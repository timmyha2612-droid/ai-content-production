"""Tracks and the stage state machine (SPEC §4). The order and the stage table come from rules/tracks.json and
rules/stages.json (plugin layer only: gates are not something a personal rule file can loosen).

State lives in <project>/.shotcraft/stages.json:
    {"schema": 1, "track": "full", "order": [...], "stages": {name: {"status": "pending|open|done|skipped",
     "opened_at", "done_at", "evidence", "user_said", "note", "qa_rounds": [...], "qa_override", "history": [...]}}}
QA rounds live in <project>/.shotcraft/qa/<stage>/round-N.json (older cycles under history/cycle-K/).

API:
    load_tracks() -> dict          load_stage_defs() -> dict (name -> definition)
    track_stages(track) -> [names]  is_optional(stage) -> bool   parallel_ok(a, b) -> bool
    init_state(project, track) -> state      load_state(project) -> state      save_state(project, state)
    status(project) -> {"track", "order", "open": [..], "next": name|None, "stages": [ {name, status, ...} ]}
    start(project, stage, note=None) -> record
    done(project, stage, user_said=None, note=None) -> record         (checks the evidence itself)
    skip(project, stage, user_said, note=None) -> record
    reopen(project, stage, note=None, user_said=None) -> {"reopened": stage, "reset": [later stages]}
    check_evidence(project, stage) -> (ok, found: [str], problems: [str])
    qa_record(project, stage, round_n, verdict, findings=None, note=None, by=None) -> round record
        findings: the reviewer's findings list, or its whole return object with a "findings" key; by: who ran it
        (qa-supervisor | script-supervisor; continuity gates need script-supervisor)
    gates_for(project, stage) -> [gates]                       (stages.json gate, or gate_by_track[track])
    qa_status(project, stage) -> {"rounds", "latest", "passed", "escalate", "next_round", "max_rounds", "message"}
    stage_open(project, stage) -> bool
    stage_for_path(project, relpath) -> stage name | None     (folder -> stage map, for the guard)
    path_writable(project, relpath) -> (bool, reason)          (the guard's whole write rule in one call)
    gen_stage_for_tier(tier) -> stage name
    gen_allowed(project, tier) -> (bool, reason)               (refine track never; the tier's stage must be open)
    parse_shotlist(project) -> [ {"id", "duration_s", "purpose", "kind", "image_first", ...} ]
    planned_shots(project) -> [shot ids]                       (shot list on full track, else the cards)
    generated_shots(project) -> [shot ids]   the planned shots that are generated (no `source: 00_inputs/...`)
    input_shots(project) -> {shot id: source path}   shots covered by the user's own files in 00_inputs/
    card_ids(project) -> [ids]     read_card_meta(path) -> dict|None    validate_card(path) -> [errors]
"""
import fnmatch
import glob
import json
import os
import re
import shutil
import sys

from . import Refused, ShotcraftError, jsonio, manifest, paths

STATUSES = ("pending", "open", "done", "skipped")
VERDICTS = ("PASS", "FAIL")


# ---------------------------------------------------------------- rule files

def _rules(name):
    path = os.path.join(paths.rules_dir(), name)
    data = jsonio.read_json(path, default=None)
    if not isinstance(data, dict):
        raise ShotcraftError("Missing or empty rule file: %s" % path)
    return data


def load_tracks():
    data = _rules("tracks.json")
    data.setdefault("optional", [])
    data.setdefault("parallel", [])
    data.setdefault("qa_max_rounds", 3)
    data.setdefault("gen_tier_stage", {"board": "boards", "draft": "drafts", "final": "finals",
                                       "upscale": "finals"})
    return data


def load_stage_defs():
    return _rules("stages.json").get("stages", {})


def track_stages(track):
    tracks = load_tracks()["tracks"]
    if track not in tracks:
        raise Refused("Unknown track %r. Tracks: %s." % (track, ", ".join(tracks)))
    return list(tracks[track]["stages"])


def is_optional(stage):
    defs = load_stage_defs()
    if stage in defs and "optional" in defs[stage]:
        return bool(defs[stage]["optional"])
    return stage in load_tracks()["optional"]


def parallel_ok(a, b):
    for group in load_tracks()["parallel"]:
        if a in group and b in group and a != b:
            return True
    return False


def max_rounds():
    return int(load_tracks()["qa_max_rounds"])


# ---------------------------------------------------------------- state

def _blank():
    return {"status": "pending", "opened_at": None, "done_at": None, "evidence": None, "user_said": None,
            "note": None, "qa_rounds": [], "qa_override": None, "history": []}


def init_state(project, track):
    order = track_stages(track)
    state = {"schema": 1, "track": track, "order": order, "stages": {s: _blank() for s in order}}
    save_state(project, state)
    return state


def load_state(project):
    state = jsonio.read_json(paths.stages_file(project), default=None)
    if not isinstance(state, dict):
        data = manifest.load(project)
        return init_state(project, data.get("track") or "full")
    for s in state.get("order", []):
        rec = state["stages"].setdefault(s, _blank())
        for k, v in _blank().items():
            rec.setdefault(k, v)
    return state


def save_state(project, state):
    jsonio.write_json(paths.stages_file(project), state)


def _need_stage(state, stage):
    if stage not in state["order"]:
        raise Refused("Stage %r is not part of the %s track. Stages: %s."
                      % (stage, state["track"], ", ".join(state["order"])))
    return state["stages"][stage]


def _sync_included(project, state):
    data = manifest.load(project)
    data["stages_included"] = [s for s in state["order"] if state["stages"][s]["status"] != "skipped"]
    manifest.save(project, data)


def _snapshot(rec, reason):
    snap = {k: v for k, v in rec.items() if k != "history"}
    snap["reset_at"] = jsonio.now_iso()
    snap["reason"] = reason
    return snap


def status(project):
    state = load_state(project)
    defs = load_stage_defs()
    rows, open_now, nxt = [], [], None
    for s in state["order"]:
        rec = state["stages"][s]
        d = defs.get(s, {})
        if rec["status"] == "open":
            open_now.append(s)
        if nxt is None and rec["status"] == "pending":
            nxt = s
        rows.append({"stage": s, "status": rec["status"], "owner": d.get("owner"), "gate": d.get("gate", []),
                     "optional": is_optional(s), "outputs": d.get("outputs"), "opened_at": rec["opened_at"],
                     "done_at": rec["done_at"], "user_said": rec["user_said"],
                     "qa_rounds": len(rec.get("qa_rounds") or [])})
    return {"track": state["track"], "order": state["order"], "open": open_now, "next": nxt, "stages": rows}


def stage_open(project, stage):
    try:
        state = load_state(project)
    except ShotcraftError:
        return False
    rec = state["stages"].get(stage)
    return bool(rec) and stage in state["order"] and rec["status"] == "open"


# ---------------------------------------------------------------- transitions

def start(project, stage, note=None):
    state = load_state(project)
    rec = _need_stage(state, stage)
    if rec["status"] == "open":
        return rec
    if rec["status"] == "done":
        raise Refused("Stage %s is already done. To work on it again: sc.py stage reopen %s" % (stage, stage))
    if rec["status"] == "skipped":
        raise Refused("Stage %s was skipped. To bring it back: sc.py stage reopen %s" % (stage, stage))
    idx = state["order"].index(stage)
    waiting = []
    for s in state["order"][:idx]:
        st = state["stages"][s]["status"]
        if st in ("done", "skipped"):
            continue
        if st == "open" and parallel_ok(s, stage):
            continue
        waiting.append("%s (%s)" % (s, st))
    if waiting:
        raise Refused("Can't start %s yet. Earlier stages not finished: %s." % (stage, ", ".join(waiting)))
    others = [s for s in state["order"] if s != stage and state["stages"][s]["status"] == "open"
              and not parallel_ok(s, stage)]
    if others:
        raise Refused("Only one stage can be open at a time. Open now: %s." % ", ".join(others))
    rec.update({"status": "open", "opened_at": jsonio.now_iso(), "done_at": None, "evidence": None,
                "user_said": None, "note": note, "qa_override": None})
    save_state(project, state)
    return rec


def skip(project, stage, user_said, note=None):
    if not (user_said or "").strip():
        raise Refused("Skipping a stage needs the user's own words (--user-said).")
    state = load_state(project)
    rec = _need_stage(state, stage)
    if rec["status"] == "done":
        raise Refused("Stage %s is done; it can't be skipped. Reopen it first if it must change." % stage)
    if rec["status"] == "skipped":
        return rec
    if not is_optional(stage) and stage.lower() not in user_said.lower():
        raise Refused("Stage %s is not optional. It can only be dropped when the user's words name it." % stage)
    if rec["status"] == "open" or rec["opened_at"]:
        rec["history"].append(_snapshot(rec, "skipped"))
    rec.update({"status": "skipped", "done_at": jsonio.now_iso(), "user_said": user_said, "note": note,
                "evidence": None})
    save_state(project, state)
    _sync_included(project, state)
    manifest.add_decision(project, stage, "Stage %s skipped" % stage, user_said)
    return rec


def _archive_qa(project, stage):
    d = paths.qa_dir(project, stage)
    files = sorted(glob.glob(os.path.join(d, "round-*.json")))
    if not files:
        return None
    hist = os.path.join(d, "history")
    k = 1
    while os.path.exists(os.path.join(hist, "cycle-%d" % k)):
        k += 1
    dest = os.path.join(hist, "cycle-%d" % k)
    os.makedirs(dest, exist_ok=True)
    for f in files:
        shutil.move(f, os.path.join(dest, os.path.basename(f)))
    return dest


def reopen(project, stage, note=None, user_said=None):
    state = load_state(project)
    rec = _need_stage(state, stage)
    if rec["status"] == "pending":
        raise Refused("Stage %s has not started; use: sc.py stage start %s" % (stage, stage))
    idx = state["order"].index(stage)
    undoes = [s for s in state["order"][idx:] if state["stages"][s]["status"] == "done"]
    if undoes and not (user_said or "").strip():
        later = [s for s in state["order"][idx + 1:] if state["stages"][s]["status"] in ("open", "done")]
        raise Refused("Reopening %s undoes what the user closed (%s)%s. It needs the user's words "
                      "(--user-said \"...\")." % (stage, ", ".join(undoes),
                                                    (" and sets back to pending: %s" % ", ".join(later)) if later else ""))
    reset = []
    for s in state["order"][idx + 1:]:
        r = state["stages"][s]
        if r["status"] in ("open", "done"):
            r["history"].append(_snapshot(r, "reopened %s" % stage))
            r.update({k: v for k, v in _blank().items() if k != "history"})
            _archive_qa(project, s)
            reset.append(s)
    was = rec["status"]
    if was != "open":
        rec["history"].append(_snapshot(rec, "reopened"))
        _archive_qa(project, stage)
        rec.update({"status": "open", "opened_at": jsonio.now_iso(), "done_at": None, "evidence": None,
                    "user_said": None, "note": note, "qa_rounds": [], "qa_override": None})
    save_state(project, state)
    if was == "skipped":
        _sync_included(project, state)
    manifest.add_decision(project, stage, "Stage %s reopened%s" % (stage, (": " + note) if note else ""),
                          user_said)
    return {"reopened": stage, "was": was, "reset": reset}


def gates_for(project, stage, state=None):
    """The stage's gate list. stages.json may give a gate per track (gate_by_track), e.g. single-track drafts
    have no other shots and no bible to check continuity against."""
    d = load_stage_defs().get(stage, {})
    if state is None:
        try:
            state = load_state(project)
        except ShotcraftError:
            state = {}
    by_track = d.get("gate_by_track") or {}
    track = (state or {}).get("track")
    if track in by_track:
        return list(by_track[track])
    return list(d.get("gate", []))


def done(project, stage, user_said=None, note=None):
    state = load_state(project)
    rec = _need_stage(state, stage)
    if rec["status"] != "open":
        raise Refused("Stage %s is %s, not open. Start it first: sc.py stage start %s"
                      % (stage, rec["status"], stage))
    gates = gates_for(project, stage, state)
    ok, found, problems = check_evidence(project, stage)
    if not ok:
        raise Refused("Stage %s can't close yet. Missing evidence:\n- %s" % (stage, "\n- ".join(problems)))
    said = (user_said or "").strip() or None
    override = None
    if "qa_pass" in gates or "continuity_qa_pass" in gates:
        qa = qa_status(project, stage)
        if qa["passed"] and "continuity_qa_pass" in gates and qa["latest"].get("by") != "script-supervisor":
            raise Refused("Stage %s needs a continuity QA PASS from the script-supervisor; the passing round was "
                          "recorded by %s. Run the script-supervisor and record its round with --by "
                          "script-supervisor." % (stage, qa["latest"].get("by") or "an unnamed reviewer"))
        if not qa["passed"]:
            if qa["escalate"] and said:
                override = "QA failed %d rounds; closed on the user's words" % len(qa["rounds"])
            else:
                kind = "Continuity QA" if "continuity_qa_pass" in gates else "QA"
                raise Refused("Stage %s needs a %s PASS. %s" % (stage, kind, qa["message"]))
        found.append("QA: %s" % ("PASS round %d" % qa["latest"]["round"] if qa["passed"] else "override"))
    if ("user_said" in gates or override) and not said:
        raise Refused("Stage %s closes only on the user's own words (--user-said \"...\")." % stage)
    rec.update({"status": "done", "done_at": jsonio.now_iso(), "evidence": found, "user_said": said,
                "qa_override": override})
    if note:
        rec["note"] = note
    save_state(project, state)
    if said:
        manifest.add_decision(project, stage, "Stage %s closed%s" % (stage, " (QA override)" if override else ""),
                              said)
    return rec


# ---------------------------------------------------------------- QA rounds

def _round_file(project, stage, n):
    return os.path.join(paths.qa_dir(project, stage), "round-%d.json" % n)


def qa_status(project, stage):
    state = load_state(project)
    rec = _need_stage(state, stage)
    rounds = list(rec.get("qa_rounds") or [])
    latest = rounds[-1] if rounds else None
    passed = bool(latest and latest["verdict"] == "PASS")
    mx = max_rounds()
    escalate = bool(latest and not passed and len(rounds) >= mx)
    if passed:
        msg, nxt = "QA passed in round %d." % latest["round"], None
    elif escalate:
        msg, nxt = ("QA failed %d rounds. Escalate to the user: their words can close the stage "
                    "(sc.py stage done %s --user-said \"...\")." % (len(rounds), stage)), None
    elif latest:
        msg, nxt = "Round %d failed. Fix the findings, then run QA round %d." % (latest["round"],
                                                                               latest["round"] + 1), latest["round"] + 1
    else:
        msg, nxt = "No QA round recorded yet. Run QA round 1.", 1
    return {"stage": stage, "rounds": rounds, "latest": latest, "passed": passed, "escalate": escalate,
            "next_round": nxt, "max_rounds": mx, "message": msg}


QA_BY = ("qa-supervisor", "script-supervisor")


def normalise_findings(findings):
    """-> (list, warnings). Takes the reviewer's findings list or its whole return object ({"agent", "verdict",
    "findings": [...]})."""
    warnings = []
    if findings is None:
        return [], warnings
    if isinstance(findings, dict):
        if isinstance(findings.get("findings"), list):
            findings = findings["findings"]
        else:
            raise Refused("The findings file must hold the reviewer's findings list, or an object with a "
                          "\"findings\" list.")
    if not isinstance(findings, list):
        raise Refused("The findings file must hold a JSON list of findings.")
    for n, f in enumerate(findings):
        if not isinstance(f, dict):
            warnings.append("finding %d is not an object" % (n + 1))
            continue
        lacks = [k for k in ("id", "severity", "kind") if not f.get(k)]
        if lacks:
            warnings.append("finding %s lacks %s (see producer/references/qa-loop.md)"
                            % (f.get("id") or n + 1, ", ".join(lacks)))
    return findings, warnings


def qa_record(project, stage, round_n, verdict, findings=None, note=None, by=None):
    verdict = str(verdict or "").upper()
    if by is not None and by not in QA_BY:
        raise Refused("--by must be one of: %s." % ", ".join(QA_BY))
    findings, warnings = normalise_findings(findings)
    if verdict not in VERDICTS:
        raise Refused("Verdict must be PASS or FAIL.")
    state = load_state(project)
    rec = _need_stage(state, stage)
    if rec["status"] != "open":
        raise Refused("QA is recorded on an open stage; %s is %s." % (stage, rec["status"]))
    qa = qa_status(project, stage)
    if qa["passed"]:
        raise Refused("QA for %s already passed in round %d." % (stage, qa["latest"]["round"]))
    if qa["escalate"]:
        raise Refused("QA for %s has used all %d rounds. Escalate to the user." % (stage, qa["max_rounds"]))
    try:
        round_n = int(round_n)
    except (TypeError, ValueError):
        raise Refused("Round must be a number.")
    if round_n != qa["next_round"]:
        raise Refused("The next QA round for %s is %d, not %d." % (stage, qa["next_round"], round_n))
    if verdict == "FAIL" and not findings:
        raise Refused("A FAIL round needs its findings (--findings FILE.json).")
    record = {"stage": stage, "round": round_n, "verdict": verdict, "by": by, "findings": findings or [],
              "note": note, "at": jsonio.now_iso(), "warnings": warnings}
    path = _round_file(project, stage, round_n)
    jsonio.write_json(path, record)
    rec["qa_rounds"].append({"round": round_n, "verdict": verdict, "by": by, "at": record["at"],
                             "file": paths.rel_to(project, path)})
    save_state(project, state)
    return record


# ---------------------------------------------------------------- folders (guard helpers)

CASE_INSENSITIVE_FS = sys.platform in ("darwin", "win32")


def _fold(text):
    """Case-fold paths where the file system ignores case (macOS and Windows by default), so 05_PROMPTS/ and
    Project.json hit the same rules as 05_prompts/ and project.json."""
    return text.lower() if CASE_INSENSITIVE_FS else text


def _norm_rel(relpath):
    rel = str(relpath).replace("\\", "/")
    while rel.startswith("./"):
        rel = rel[2:]
    while "//" in rel:
        rel = rel.replace("//", "/")
    return _fold(rel.lstrip("/"))


def stage_for_path(project, relpath):
    rel = _norm_rel(relpath)
    defs = load_stage_defs()
    try:
        order = load_state(project)["order"]
    except ShotcraftError:
        order = list(defs)
    for s in order:
        for pat in defs.get(s, {}).get("folders", []):
            pat = _fold(pat)
            if fnmatch.fnmatchcase(rel, pat) or rel == pat.rstrip("/*"):
                return s
    return None


# 00_brief/ files that take late intake answers: written through `sc.py brief add`, which appends under
# '## Added after intake'. They stay locked to Write/Edit once intake is done, so the user's confirmed card
# can't be rewritten silently.
ALWAYS_WRITABLE = ("00_inputs/", ".shotcraft/lessons.md")


def path_writable(project, relpath):
    rel = _norm_rel(relpath)
    if rel == "project.json":
        return False, "project.json changes only through sc.py."
    if rel == ".shotcraft" or rel == ".shotcraft/stages.json" or rel.startswith(".shotcraft/qa/") \
            or rel == ".shotcraft/qa":
        return False, "Stage and QA records change only through sc.py (sc.py stage / sc.py qa)."
    if rel.startswith("00_inputs/") or rel == ".shotcraft/lessons.md":
        return True, "always allowed"
    stage = stage_for_path(project, rel)
    if stage is None:
        return True, "not a stage folder"
    st = load_state(project)["stages"][stage]["status"]
    if st == "open":
        return True, "stage %s is open" % stage
    if st == "done":
        hint = ""
        if stage == "prompts":
            hint = (" To approve a card or set its start frame without reopening: sc.py card approve / "
                    "sc.py card set-input (while boards, drafts or finals is open).")
        elif stage == "intake":
            hint = " To add a late answer without reopening: sc.py brief add --question \"...\" --answer \"...\"."
        return False, ("Stage %s is done. Reopen it to change its files: sc.py stage reopen %s --user-said "
                       "\"<their words>\" (this sets every later stage back to pending).%s" % (stage, stage, hint))
    if st == "skipped":
        return False, "Stage %s was skipped. Reopen it first: sc.py stage reopen %s" % (stage, stage)
    return False, "Stage %s is not open yet. Start it first: sc.py stage start %s" % (stage, stage)


def gen_stage_for_tier(tier):
    table = load_tracks()["gen_tier_stage"]
    if tier not in table:
        raise Refused("Unknown tier %r. Tiers: %s." % (tier, ", ".join(table)))
    return table[tier]


def gen_allowed(project, tier):
    state = load_state(project)
    track = load_tracks()["tracks"].get(state["track"], {})
    if not track.get("generation_allowed", True):
        return False, "The %s track never generates. Start a single or full project to generate." % state["track"]
    stage = gen_stage_for_tier(tier)
    if stage not in state["order"]:
        return False, "Tier %s needs the %s stage, which is not on the %s track." % (tier, stage, state["track"])
    st = state["stages"][stage]["status"]
    if st != "open":
        return False, "Tier %s generates only while the %s stage is open (it is %s)." % (tier, stage, st)
    return True, "stage %s is open" % stage


# ---------------------------------------------------------------- shot list and cards

_TRUE = {"y", "yes", "true", "x", "1", "✓", "✔", "image-first", "image first", "board", "boards"}
_HEAD_ALIASES = {
    "id": ("id", "shot", "shot_id", "shot_no", "shot_number"),
    "duration_s": ("duration_s", "duration", "dur", "seconds", "duration_sec", "secs", "length_s", "len_s"),
    "purpose": ("purpose", "why", "intent"),
    "kind": ("kind", "type", "media"),
    "image_first": ("image_first", "imagefirst", "board", "boards", "image_first_"),
}


def _norm_head(h):
    h = re.sub(r"[*`_]+", " ", h).strip().lower()
    h = re.sub(r"\(s\)|\(sec\)|\(seconds\)", " s", h)
    return re.sub(r"[^a-z0-9]+", "_", h).strip("_")


def _cells(line):
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def parse_shotlist_text(text):
    rows, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        if lines[i].strip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-{2,}", lines[i + 1]):
            heads = [_norm_head(h) for h in _cells(lines[i])]
            colmap = {}
            for j, h in enumerate(heads):
                for key, aliases in _HEAD_ALIASES.items():
                    if h in aliases and key not in colmap:
                        colmap[key] = j
            i += 2
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = _cells(lines[i])
                if "id" in colmap:
                    row = {heads[j] or "col%d" % j: (cells[j] if j < len(cells) else "") for j in range(len(heads))}
                    for key, j in colmap.items():
                        row[key] = cells[j] if j < len(cells) else ""
                    row["id"] = re.sub(r"[*`]", "", row["id"]).strip()
                    ftxt = str(row.get("image_first", "")).strip().lower()
                    row["image_first"] = ftxt in _TRUE
                    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds)?\s*$", str(row.get("duration_s", "")))
                    row["duration_value"] = float(m.group(1)) if m else None
                    rows.append(row)
                i += 1
            continue
        i += 1
    return rows


def parse_shotlist(project):
    path = os.path.join(project, "03_script", "shotlist.md")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return parse_shotlist_text(fh.read())
    except FileNotFoundError:
        return []


def read_card_meta(path):
    """The JSON front matter of a prompt card, or None."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    m = re.match(r"^﻿?---\s*\n(.*?)\n---\s*(\n|$)", text, re.S)
    if not m:
        return None
    try:
        data = json.loads(m.group(1))
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _interpret(result):
    if result is None or result is True:
        return []
    if result is False:
        return ["card is not valid"]
    if isinstance(result, (list, tuple)):
        if len(result) == 2 and isinstance(result[0], bool):
            return [] if result[0] else [str(e) for e in (result[1] or ["card is not valid"])]
        return [str(e) for e in result]
    if isinstance(result, dict):
        errs = result.get("errors") or []
        if result.get("ok") is False or result.get("valid") is False:
            return [str(e) for e in errs] or ["card is not valid"]
        return [str(e) for e in errs]
    return []


def validate_card(path):
    """Errors for one prompt card (empty list = valid). Uses shotcraft.cards when it is installed
    (validate_path(path) or validate_text(text) -> list of errors), else a minimal structural check."""
    try:
        from . import cards  # noqa
    except ImportError:
        cards = None
    if cards is not None:
        for name in ("validate_path", "validate_file", "validate_card_file"):
            fn = getattr(cards, name, None)
            if callable(fn):
                try:
                    return _interpret(fn(path))
                except Exception as exc:  # a broken card must not crash the gate
                    return ["card check failed: %s" % exc]
        fn = getattr(cards, "validate_text", None)
        if callable(fn):
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    return _interpret(fn(fh.read()))
            except Exception as exc:
                return ["card check failed: %s" % exc]
    meta = read_card_meta(path)
    if meta is None:
        return ["no JSON front matter between --- lines"]
    errs = []
    if not meta.get("id"):
        errs.append("no id")
    if meta.get("kind") not in ("video", "image"):
        errs.append("kind must be video or image")
    if not isinstance(meta.get("layers"), dict) or not meta.get("layers"):
        errs.append("no layers")
    return errs


def _card_files(project):
    return sorted(glob.glob(os.path.join(project, "05_prompts", "*.md")))


def card_ids(project):
    out = []
    for f in _card_files(project):
        meta = read_card_meta(f) or {}
        out.append(str(meta.get("id") or os.path.splitext(os.path.basename(f))[0]))
    return out


def planned_shots(project):
    state = load_state(project)
    if state["track"] == "full":
        ids = [r["id"] for r in parse_shotlist(project) if r.get("id")]
        if ids:
            return ids
    return card_ids(project)


def _source_of(row):
    return str(row.get("source") or "").strip().strip("`").strip()


def input_shots(project):
    """Shot-list rows covered by the user's own material: {shot id: "00_inputs/..."}."""
    out = {}
    try:
        if load_state(project)["track"] != "full":
            return out
    except ShotcraftError:
        return out
    for r in parse_shotlist(project):
        src = _source_of(r)
        if r.get("id") and src.lower().startswith("00_inputs/"):
            out[r["id"]] = src
    return out


def generated_shots(project):
    """The planned shots that shotcraft generates: rows whose source is empty or 'gen'."""
    skip = input_shots(project)
    out = []
    rows = {r["id"]: r for r in parse_shotlist(project) if r.get("id")}
    for sid in planned_shots(project):
        if sid in skip:
            continue
        src = _source_of(rows.get(sid, {})).lower()
        if src and src not in ("gen", "generated", "generate", "-", "—"):
            continue
        out.append(sid)
    return out


def _input_problems(project, sources):
    """Each input-covered shot's file exists and is an owned or licensed asset."""
    problems = []
    try:
        assets = manifest.load(project).get("assets", [])
    except ShotcraftError:
        assets = []
    for sid, src in sorted(sources.items()):
        rel = src.replace("\\", "/")
        if not os.path.exists(os.path.join(project, rel)):
            problems.append("%s uses %s, which is not there" % (sid, rel))
            continue
        a = next((x for x in assets if x.get("path") == rel), None)
        if a is None:
            problems.append("%s uses %s, which is not registered (sc.py asset add %s --rights owned --role input)"
                            % (sid, rel, rel))
        elif a.get("rights") not in ("owned", "licensed"):
            problems.append("%s uses %s, which is %s (it must be owned or licensed)" % (sid, rel, a.get("rights")))
    return problems


def _image_first_shots(project):
    rows = {r["id"]: r for r in parse_shotlist(project)}
    out = []
    for sid in generated_shots(project):
        row = rows.get(sid, {})
        meta = read_card_meta(os.path.join(project, "05_prompts", sid + ".md")) or {}
        kind = (meta.get("kind") or row.get("kind") or "").strip().lower()
        flagged = bool(row.get("image_first")) or "board" in (meta.get("tier_plan") or [])
        if flagged and kind != "image":
            out.append(sid)
    return out


# ---------------------------------------------------------------- evidence

_PLACEHOLDER = re.compile(r"^(<.*>|\.{2,}|…|tbd|tbc|todo|\?+|-+|_+|\[.*\]|none yet|n/?a)$", re.I)


def _nonempty_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return bool(fh.read().strip())
    except OSError:
        return False


def _ev_file(project, spec):
    p = os.path.join(project, spec["path"])
    if _nonempty_file(p):
        return True, "%s present" % spec["path"], None
    return False, None, "%s is missing or empty" % spec["path"]


def _ev_json(project, spec):
    p = os.path.join(project, spec["path"])
    try:
        jsonio.read_json(p, default=None)
    except ShotcraftError:
        return False, None, "%s is not valid JSON" % spec["path"]
    if not os.path.isfile(p):
        return False, None, "%s is missing" % spec["path"]
    return True, "%s present" % spec["path"], None


def _ev_card_lines(project, spec):
    p = os.path.join(project, spec["path"])
    try:
        with open(p, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return False, None, "%s is missing" % spec["path"]
    missing = []
    for label in spec.get("required_lines", []):
        lab = re.escape(label)
        pat_line = re.compile(r"^\s*(?:[-*]\s*)?(?:\*\*)?\s*%s\s*(?:\*\*)?\s*:\s*(?:\*\*)?\s*(.*)$" % lab, re.I | re.M)
        pat_row = re.compile(r"^\s*\|\s*(?:\*\*)?\s*%s\s*(?:\*\*)?\s*\|\s*(.*?)\s*\|" % lab, re.I | re.M)
        vals = [m.group(1) for m in pat_line.finditer(text)] + [m.group(1) for m in pat_row.finditer(text)]
        good = [v for v in (x.strip().strip("*").strip() for x in vals) if v and not _PLACEHOLDER.match(v)]
        if not good:
            missing.append(label)
    if missing:
        return False, None, "%s: these lines are not filled: %s" % (spec["path"], ", ".join(missing))
    return True, "%s has every required line" % spec["path"], None


def _ev_sections(project, spec):
    p = os.path.join(project, spec["path"])
    try:
        with open(p, "r", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return False, None, "%s is missing" % spec["path"]
    n = len(re.findall(spec.get("pattern", r"^##\s+\S"), text, re.M))
    need = int(spec.get("min", 1))
    what = spec.get("what", "sections")
    if n < need:
        return False, None, "%s has %d %s; needs at least %d" % (spec["path"], n, what, need)
    return True, "%s has %d %s" % (spec["path"], n, what), None


def _ev_files(project, spec):
    rx = re.compile(spec["name_regex"]) if spec.get("name_regex") else None
    count = 0
    for d in spec.get("dirs", []):
        for root, dirs, files in os.walk(os.path.join(project, d)):
            dirs[:] = [x for x in dirs if not x.startswith(".")]
            for f in files:
                if f.startswith("."):
                    continue
                if rx and not rx.search(f):
                    continue
                count += 1
    need = int(spec.get("min", 1))
    what = spec.get("what", "files")
    where = " or ".join(d + "/" for d in spec.get("dirs", []))
    if count < need:
        return False, None, "%s: %d %s; needs at least %d" % (where, count, what, need)
    return True, "%s: %d %s" % (where, count, what), None


def _ev_assets(project, spec):
    n = len(manifest.list_assets(project, role=spec.get("role")))
    need = int(spec.get("min", 1))
    if n < need:
        return False, None, "%d asset(s) with role=%s; needs at least %d" % (n, spec.get("role"), need)
    return True, "%d asset(s) with role=%s" % (n, spec.get("role")), None


def _ev_shotlist(project, spec):
    rows = parse_shotlist(project)
    if not rows:
        return False, None, ("%s has no shot table (a markdown table with id, duration_s and purpose columns)"
                             % spec["path"])
    bad, seen = [], set()
    for r in rows:
        sid = r.get("id", "")
        if not re.match(r"^S\d+[A-Za-z]?$", sid):
            bad.append("%r is not a shot id like S010" % sid)
        if sid in seen:
            bad.append("%s appears twice" % sid)
        seen.add(sid)
        if not r.get("duration_value") or r["duration_value"] <= 0:
            bad.append("%s has no duration_s" % (sid or "a row"))
        if not str(r.get("purpose", "")).strip() or _PLACEHOLDER.match(str(r.get("purpose", "")).strip()):
            bad.append("%s has no purpose" % (sid or "a row"))
    if bad:
        return False, None, "shot list: " + "; ".join(bad)
    return True, "shot list: %d shots with id, duration and purpose" % len(rows), None


def _ev_cards(project, spec):
    files = _card_files(project)
    invalid = []
    for f in files:
        errs = validate_card(f)
        if errs:
            invalid.append("%s (%s)" % (os.path.basename(f), "; ".join(errs[:3])))
    if invalid:
        return False, None, "cards that do not validate: " + ", ".join(invalid)
    ids = card_ids(project)
    state = load_state(project)
    if spec.get("per_shot") and state["track"] == "full":
        all_shots = [r["id"] for r in parse_shotlist(project)]
        if not all_shots:
            return False, None, "no shot list to check the cards against (03_script/shotlist.md)"
        inputs = input_shots(project)
        shots = generated_shots(project)
        problems = _input_problems(project, inputs)
        missing = [s for s in shots if s not in ids]
        if missing:
            problems.insert(0, "no card yet for: " + ", ".join(missing))
        if problems:
            return False, None, "; ".join(problems)
        return True, "a valid card for each of %d generated shot(s)%s" % (
            len(shots), (", %d from the user's own files" % len(inputs)) if inputs else ""), None
    if not ids:
        return False, None, "no prompt card in 05_prompts/"
    return True, "%d valid card(s)" % len(ids), None


def _ev_generations(project, spec):
    tiers = spec.get("tier") or []
    tiers = [tiers] if isinstance(tiers, str) else list(tiers)
    gens = manifest.load(project).get("generations", [])
    scope = spec.get("scope", "all_shots")
    shots = _image_first_shots(project) if scope == "image_first" else generated_shots(project)
    label = "/".join(tiers)
    if not shots:
        if scope == "image_first":
            return False, None, "no shot is flagged image-first; skip this stage instead (sc.py stage skip boards)"
        if input_shots(project):
            return True, "every shot comes from the user's own files; nothing to generate", None
        return False, None, "no shots planned (no shot list or cards)"
    need_approved = bool(spec.get("approved"))
    problems = []
    for sid in shots:
        done_ = [g for g in gens if g.get("shot") == sid and g.get("tier") in tiers and g.get("status") == "completed"]
        if not done_:
            problems.append("%s has no completed %s" % (sid, label))
        elif need_approved and not any(g.get("approved") is True for g in done_):
            problems.append("%s has no approved %s" % (sid, label))
    if need_approved:
        undecided = [g["id"] for g in gens if g.get("tier") in tiers and g.get("status") == "completed"
                     and g.get("approved") is None]
        if undecided:
            problems.append("not yet approved or rejected: " + ", ".join(undecided))
    if problems:
        return False, None, "; ".join(problems)
    return True, "%d shot(s) with a completed%s %s" % (len(shots), " approved" if need_approved else "", label), None


_SHEET_TIERS = {"board": ("board",), "draft": ("draft",), "final": ("final", "upscale")}


def _ev_contact_sheet(project, spec):
    """Only a sheet built by `sc.py sheet build` counts: recorded in project.json, unchanged since (sha256), and
    showing every completed generation of its tier."""
    tier = spec.get("tier", "")
    build = "sc.py sheet build --tier %s" % tier
    data = manifest.load(project)
    sheets = [x for x in data.get("sheets", []) if x.get("tier") == tier]
    if not sheets:
        return False, None, "no %s contact sheet built yet (%s)" % (tier, build)
    sh = sheets[-1]
    p = os.path.join(project, sh.get("path") or "")
    try:
        same = manifest.file_sha256(p) == sh.get("sha256")
    except OSError:
        return False, None, "the %s contact sheet %s is missing (%s)" % (tier, sh.get("path"), build)
    if not same:
        return False, None, "the %s contact sheet %s changed after it was built (%s)" % (tier, sh.get("path"), build)
    done_ids = {g["id"] for g in data.get("generations", [])
                if g.get("tier") in _SHEET_TIERS.get(tier, (tier,)) and g.get("status") == "completed"}
    left_out = sorted(done_ids - set(sh.get("gen_ids") or []))
    if left_out:
        return False, None, "the %s contact sheet is older than %s; build it again (%s)" % (
            tier, ", ".join(left_out), build)
    return True, "contact sheet: %s" % sh["path"], None


def _is_pass(v):
    if v is True:
        return True
    return isinstance(v, str) and v.strip().upper() in ("PASS", "OK", "PASSED")


def _ev_delivery_report(project, spec):
    """The delivery check recorded in project.json by `sc.py delivery check` (the report file in 09_delivery/ is
    for people; it is not trusted). It must have passed, and 09_delivery/ must hold exactly the files it checked,
    unchanged (sha256)."""
    from . import delivery
    rec = manifest.load(project).get("delivery_check")
    if not isinstance(rec, dict):
        return False, None, "no delivery check recorded yet (sc.py delivery check)"
    if not _is_pass(rec.get("verdict")):
        return False, None, "the last delivery check failed: %s (fix them, then sc.py delivery check)" % (
            ", ".join(rec.get("failed") or []) or "see 09_delivery/delivery-report.json")
    now = delivery.fingerprints(project)
    was = rec.get("files") or {}
    if set(now) != set(was):
        diff = sorted(set(now) ^ set(was))
        return False, None, "09_delivery/ changed since the last delivery check (%s); run sc.py delivery check " \
                            "again" % ", ".join(diff[:5])
    changed = sorted(k for k in now if now[k] != was.get(k))
    if changed:
        return False, None, "these files changed since the last delivery check: %s; run sc.py delivery check " \
                            "again" % ", ".join(changed[:5])
    eff = rec.get("effective") or {}
    return True, ("delivery check PASS: %d checks on %d file(s) (spec %s, duration %s, tolerance %s s, loudness "
                  "%s LUFS)" % (rec.get("checks") or 0, len(now), eff.get("preset"), eff.get("duration") or "planned",
                                eff.get("duration_tolerance_s"), eff.get("loudness_lufs"))), None


def _ev_lessons_decided(project, spec):
    from . import lessons
    open_ = [l for l in lessons.list_lessons(project) if l["status"] == "open"]
    if open_:
        return False, None, "lessons still undecided: " + ", ".join("#%d" % l["n"] for l in open_)
    return True, "every lesson decided", None


_CHECKS = {
    "file": _ev_file, "json": _ev_json, "card_lines": _ev_card_lines, "sections": _ev_sections,
    "files": _ev_files, "assets": _ev_assets, "shotlist": _ev_shotlist, "cards": _ev_cards,
    "generations": _ev_generations, "contact_sheet": _ev_contact_sheet, "delivery_report": _ev_delivery_report,
    "lessons_decided": _ev_lessons_decided,
}


def check_evidence(project, stage):
    found, problems = [], []
    for spec in load_stage_defs().get(stage, {}).get("evidence", []):
        fn = _CHECKS.get(spec.get("check"))
        if fn is None:
            problems.append("unknown evidence check %r in rules/stages.json" % spec.get("check"))
            continue
        ok, what, why = fn(project, spec)
        if ok:
            found.append(what)
        else:
            problems.append(why)
    return (not problems), found, problems
