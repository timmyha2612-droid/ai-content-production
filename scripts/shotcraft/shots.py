"""Per-shot progress: after the whole board is approved, shots move from draft to final to locked one batch at
a time (SPEC section 13).

The user picks the batch: one shot, a few, a range, whole scenes or every shot. A shot in progress may make
drafts and finals while the drafts and finals stages are still closed; a locked shot makes nothing until the
user unlocks it. Every start, pause, lock and unlock carries the user's own words.

State lives in <project>/.shotcraft/shots.json, written only by sc.py (the guard blocks Edit/Write there).

API:
    known_shots(project) -> [shot ids in order]
    scene_of(project) -> {shot id: scene}
    select(project, items=(), all_shots=False, scenes=()) -> [shot ids]   items: S010, S010-S040
    start(project, ids, user_said) -> {"started", "already", "locked"}
    pause(project, ids, user_said) -> [ids]
    lock(project, shot, user_said) -> record     needs an approved final of the shot
    unlock(project, shot, user_said) -> record
    progress(project) -> {shot id: {"state", "label", "in_progress", "locked", "scene", ...}}
    gen_allowed(project, tier, shot) -> (ok, why)   used by gen.gates in place of stages.gen_allowed
    cli_shots_status / start / pause / lock / unlock
"""
import json
import os
import re

from . import Refused, ShotcraftError, jsonio, manifest, paths, stages

PER_SHOT_TIERS = ("draft", "final", "upscale")
RUNNING = ("estimated", "submitted", "queued", "in_progress")
STATE_LABELS = {
    "waiting": "Waiting for the board",
    "ready": "Board approved, not started",
    "paused": "Paused",
    "in_progress": "In progress, no takes yet",
    "draft_running": "Draft generating",
    "draft_review": "Draft to review",
    "draft_approved": "Draft approved",
    "final_running": "Final generating",
    "final_review": "Final to review",
    "final_approved": "Final approved, ready to lock",
    "locked": "Locked",
}


def _file(project):
    return os.path.join(paths.project_meta_dir(project), "shots.json")


def _load(project):
    data = jsonio.read_json(_file(project))
    if not isinstance(data, dict):
        data = {}
    data.setdefault("shots", {})
    return data


def _save(project, data):
    jsonio.write_json(_file(project), data)


def _said(s):
    return bool((s or "").strip())


def _need_said(user_said, what):
    if not _said(user_said):
        raise Refused("%s needs the user's own words (--user-said)." % what)


def known_shots(project):
    ids = list(stages.planned_shots(project))
    for c in stages.card_ids(project):
        if c not in ids:
            ids.append(c)
    return ids


def scene_of(project):
    out = {}
    for r in stages.parse_shotlist(project):
        if r.get("id") and str(r.get("scene") or "").strip():
            out[r["id"]] = str(r["scene"]).strip()
    try:
        from . import board
        for s in board.load_board(project).get("shots") or []:
            if isinstance(s, dict) and s.get("card") and s.get("scene") not in (None, "") and s["card"] not in out:
                out[s["card"]] = str(s["scene"]).strip()
    except ShotcraftError:
        pass
    return out


def _board_ready(project):
    st = stages.load_state(project)
    rec = st["stages"].get("boards")
    if rec is None:  # a track without boards (the default now): the prompts stage is the last gate
        rec = st["stages"].get("prompts")
    return bool(rec) and rec["status"] in ("done", "skipped")


def select(project, items=(), all_shots=False, scenes=()):
    shots = known_shots(project)
    if not shots:
        raise Refused("No shots yet: write the shot list and cards first.")
    if all_shots:
        return shots
    chosen = []
    if scenes:
        sc = scene_of(project)
        want = {str(s).strip().lower() for s in scenes}
        hit = [s for s in shots if str(sc.get(s, "")).lower() in want]
        if not hit:
            raise Refused("No shots in scene %s. Add a scene column to the shot list (or scene to board.json)."
                          % ", ".join(sorted(want)))
        chosen += hit
    for item in items or ():
        for part in re.split(r"[,\s]+", str(item).strip()):
            if not part:
                continue
            m = re.match(r"^(S\d{3}[A-Z]?)-(S\d{3}[A-Z]?)$", part, re.I)
            if m:
                a, b = m.group(1).upper(), m.group(2).upper()
                if a not in shots or b not in shots:
                    raise Refused("Range %s: %s is not a shot in this project." % (part, a if a not in shots else b))
                i, j = sorted((shots.index(a), shots.index(b)))
                chosen += shots[i:j + 1]
            elif part.upper() in shots:
                chosen.append(part.upper())
            else:
                raise Refused("%s is not a shot in this project. Shots: %s." % (part, ", ".join(shots)))
    out = []
    for s in chosen:
        if s not in out:
            out.append(s)
    if not out:
        raise Refused("Say which shots: S010, S010-S040, --scene 2 or --all.")
    return out


def start(project, ids, user_said):
    _need_said(user_said, "Starting shots")
    if not _board_ready(project):
        raise Refused("The prompt cards aren't all approved yet. Close the prompts stage first (sc.py stage done "
                      "prompts), then start shots.")
    data = _load(project)
    res = {"started": [], "already": [], "locked": []}
    for s in ids:
        rec = data["shots"].setdefault(s, {"history": []})
        if rec.get("locked"):
            res["locked"].append(s)
            continue
        if rec.get("in_progress"):
            res["already"].append(s)
            continue
        rec["in_progress"] = True
        rec["history"].append({"at": jsonio.now_iso(), "event": "start", "user_said": user_said})
        res["started"].append(s)
    _save(project, data)
    if res["started"]:
        manifest.add_decision(project, None, "Shots in progress: %s" % ", ".join(res["started"]), user_said)
    return res


def pause(project, ids, user_said):
    _need_said(user_said, "Pausing shots")
    data = _load(project)
    out = []
    for s in ids:
        rec = data["shots"].get(s)
        if rec and rec.get("in_progress") and not rec.get("locked"):
            rec["in_progress"] = False
            rec["history"].append({"at": jsonio.now_iso(), "event": "pause", "user_said": user_said})
            out.append(s)
    _save(project, data)
    return out


def _gens(project, shot):
    return [g for g in manifest.load(project).get("generations", []) if g.get("shot") == shot]


def lock(project, shot, user_said):
    _need_said(user_said, "Locking a shot")
    finals = [g for g in _gens(project, shot) if g.get("tier") in ("final", "upscale") and g.get("approved") is True]
    if not finals:
        raise Refused("%s has no approved final. Approve one first (sc.py gen approve GEN_ID --user-said \"...\")."
                      % shot)
    data = _load(project)
    rec = data["shots"].setdefault(shot, {"history": []})
    if rec.get("locked"):
        raise Refused("%s is already locked." % shot)
    pick = sorted(finals, key=lambda g: (g.get("tier") == "upscale", g.get("decided_at") or "", g["id"]))[-1]
    rec.update(locked=True, in_progress=False, locked_gen=pick["id"], locked_at=jsonio.now_iso())
    rec["history"].append({"at": rec["locked_at"], "event": "lock", "gen": pick["id"], "user_said": user_said})
    _save(project, data)
    manifest.add_decision(project, "finals", "Locked %s on %s" % (shot, pick["id"]), user_said)
    return dict(rec, shot=shot)


def unlock(project, shot, user_said):
    _need_said(user_said, "Unlocking a shot")
    data = _load(project)
    rec = data["shots"].get(shot)
    if not rec or not rec.get("locked"):
        raise Refused("%s is not locked." % shot)
    rec.update(locked=False, in_progress=True)
    rec["history"].append({"at": jsonio.now_iso(), "event": "unlock", "user_said": user_said})
    _save(project, data)
    manifest.add_decision(project, "finals", "Unlocked %s" % shot, user_said)
    return dict(rec, shot=shot)


def _state(rec, gens, board_ready):
    if rec.get("locked"):
        return "locked"
    if not rec.get("in_progress"):
        if rec.get("history"):
            return "paused"
        return "ready" if board_ready else "waiting"

    def tier(t):
        return [g for g in gens if g.get("tier") in t]
    fin, dr = tier(("final", "upscale")), tier(("draft",))
    if any(g.get("approved") is True for g in fin):
        return "final_approved"
    if any(g.get("status") in RUNNING for g in fin):
        return "final_running"
    if any(g.get("status") == "completed" and g.get("approved") is None for g in fin):
        return "final_review"
    if any(g.get("approved") is True for g in dr):
        return "draft_approved"
    if any(g.get("status") in RUNNING for g in dr):
        return "draft_running"
    if any(g.get("status") == "completed" and g.get("approved") is None for g in dr):
        return "draft_review"
    return "in_progress"


def progress(project):
    data = _load(project)
    ready = _board_ready(project)
    scenes = scene_of(project)
    all_gens = manifest.load(project).get("generations", [])
    out = {}
    for s in known_shots(project):
        rec = data["shots"].get(s, {})
        st = _state(rec, [g for g in all_gens if g.get("shot") == s], ready)
        out[s] = {"state": st, "label": STATE_LABELS[st], "in_progress": bool(rec.get("in_progress")),
                  "locked": bool(rec.get("locked")), "locked_gen": rec.get("locked_gen"), "scene": scenes.get(s)}
    return out


def gen_allowed(project, tier, shot):
    rec = _load(project)["shots"].get(shot or "", {})
    if rec.get("locked"):
        return False, ("%s is locked on %s. To change it: sc.py shots unlock %s --user-said \"<their words>\""
                       % (shot, rec.get("locked_gen"), shot))
    if tier in PER_SHOT_TIERS and rec.get("in_progress") and _board_ready(project):
        return True, "%s is in progress" % shot
    ok, why = stages.gen_allowed(project, tier)
    if not ok and tier in PER_SHOT_TIERS and _board_ready(project):
        why += " Or work shot by shot: sc.py shots start %s --user-said \"<their words>\"." % (shot or "S010")
    return ok, why


# ---------------------------------------------------------------- CLI

def _project(args):
    from . import project as _p
    return _p.resolve(getattr(args, "project", None), getattr(args, "session_id", None))


def _out(args, obj, text):
    if getattr(args, "json", False):
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    else:
        print(text)
    return 0


def cli_shots_status(args):
    p = _project(args)
    pr = progress(p)
    lines = ["%s%s  %s" % (s, (" (scene %s)" % v["scene"]) if v["scene"] else "", v["label"]) for s, v in pr.items()]
    return _out(args, {"ok": True, "shots": pr}, "\n".join(lines) or "No shots yet.")


def _sel(args, p):
    return select(p, getattr(args, "shots", None) or (), getattr(args, "all", False), getattr(args, "scene", None) or ())


def cli_shots_start(args):
    p = _project(args)
    r = start(p, _sel(args, p), args.user_said)
    bits = []
    if r["started"]:
        bits.append("In progress: " + ", ".join(r["started"]) + ".")
    if r["already"]:
        bits.append("Already in progress: " + ", ".join(r["already"]) + ".")
    if r["locked"]:
        bits.append("Locked, left alone: " + ", ".join(r["locked"]) + ".")
    return _out(args, {"ok": True, **r}, " ".join(bits))


def cli_shots_pause(args):
    p = _project(args)
    r = pause(p, _sel(args, p), args.user_said)
    return _out(args, {"ok": True, "paused": r}, ("Paused: " + ", ".join(r)) if r else "Nothing to pause.")


def cli_shots_lock(args):
    p = _project(args)
    r = lock(p, args.shot.upper(), args.user_said)
    return _out(args, {"ok": True, **r}, "%s locked on %s." % (r["shot"], r["locked_gen"]))


def cli_shots_unlock(args):
    p = _project(args)
    r = unlock(p, args.shot.upper(), args.user_said)
    return _out(args, {"ok": True, **r}, "%s unlocked and back in progress." % r["shot"])
