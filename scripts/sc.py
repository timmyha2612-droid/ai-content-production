#!/usr/bin/env python3
"""shotcraft's one CLI: python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py" <group> <cmd> [options]

Every command takes --json (machine-readable output), --project PATH (else the session's active project) and
--session-id ID (else $CLAUDE_SESSION_ID or $CLAUDE_CODE_SESSION_ID). Exit codes: 0 = ok, 2 = refused by a rule or gate, 1 = error.

Groups handled here (core engine): setup, doctor, project, brief, stage, qa, budget, asset, lessons.

Groups owned by other modules (delegation convention):
    sc.py parses the arguments, then lazily imports the owning module and calls
        cli_<group>_<cmd>(args) -> int          (dashes in names become underscores)
    e.g. `sc.py gen submit ...` -> shotcraft.gen.cli_gen_submit(args). The single-command group `route` calls
    cli_route(args) (cli_route_route also accepted). The module prints its own output and returns the exit code;
    it may raise shotcraft.Refused (exit 2) or shotcraft.ShotcraftError (exit 1). `args` always carries
    .json, .project and .session_id; resolve the project with shotcraft.project.resolve(args.project, args.session_id).
        card new|validate|approve|set-input  shotcraft.cards      card compile   shotcraft.compiler (then cards)
        refine save              shotcraft.cards (then compiler)
        route                    shotcraft.routing
        gen estimate|submit|status|fetch|approve|reject   shotcraft.gen
        refs fetch               shotcraft.refs          sheet build      shotcraft.contact_sheet
        delivery check           shotcraft.delivery      assembly animatic shotcraft.assembly
        finish texture|roomtone  shotcraft.finish
        scout check|report       shotcraft.scout         handoff build|upload shotcraft.handoff
    If the module is not installed, sc.py prints a clear message and exits 1.
"""
import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from shotcraft import VERSION, Refused, ShotcraftError  # noqa: E402
from shotcraft import budget, config, jsonio, lessons, manifest, paths, project, stages  # noqa: E402


# ---------------------------------------------------------------- output helpers

def emit(args, data, text=None):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        print(text if text is not None else json.dumps(data, indent=2, ensure_ascii=False, default=str))


def _proj(args):
    return project.resolve(getattr(args, "project", None), getattr(args, "session_id", None))


# ---------------------------------------------------------------- setup / doctor

def _run(cmd, timeout=15):
    try:
        p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                           universal_newlines=True)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except (OSError, subprocess.SubprocessError) as exc:
        return None, "", str(exc)


def doctor_report():
    tools = {}
    probes = {"higgsfield": ["higgsfield", "version"], "ffmpeg": ["ffmpeg", "-version"],
              "ffprobe": ["ffprobe", "-version"], "yt-dlp": ["yt-dlp", "--version"], "node": ["node", "--version"]}
    for name, cmd in probes.items():
        where = shutil.which(name)
        info = {"found": bool(where), "path": where, "version": None}
        if where:
            rc, out, err = _run(cmd, timeout=10)
            first = (out or err).splitlines()[0] if (out or err) else None
            info["version"] = first if rc == 0 else None
        tools[name] = info
    auth = {"checked": False, "ok": None, "note": "higgsfield CLI not installed"}
    if tools["higgsfield"]["found"]:
        rc, out, err = _run(["higgsfield", "account", "status", "--json"], timeout=15)
        auth = {"checked": True, "ok": rc == 0,
                "note": "signed in" if rc == 0 else ("not signed in; run: higgsfield auth login" if rc is not None
                                                     else "could not run the CLI: %s" % err)}
    cfg = config.load()
    root = config.projects_root(cfg)
    cfg_info = {"file": paths.config_file(), "exists": config.exists(), "projects_root": root,
                "projects_root_ok": bool(root and os.path.isdir(root) and os.access(root, os.W_OK)),
                "first_run_done": bool(cfg.get("first_run_done"))}
    want = ["taxonomy.json", "negatives.json", "positive_rewrites.json", "models.json", "routing.json",
            "presets.json", "tracks.json", "stages.json"]
    missing = [f for f in want if not os.path.isfile(os.path.join(paths.rules_dir(), f))]
    problems = []
    if not cfg_info["exists"]:
        problems.append("No config yet: run sc.py setup --projects-root DIR")
    elif not cfg_info["projects_root_ok"]:
        problems.append("The projects folder is missing or not writable: %s" % root)
    if missing:
        problems.append("Plugin rule files missing: %s" % ", ".join(missing))
    if not tools["higgsfield"]["found"]:
        problems.append("Higgsfield CLI not found (npm install -g @higgsfield/cli). Generation is off until then.")
    elif auth["ok"] is False:
        problems.append("Higgsfield CLI is not signed in: higgsfield auth login")
    if not tools["ffprobe"]["found"]:
        problems.append("ffprobe not found: delivery checks and the animatic need ffmpeg/ffprobe.")
    return {"version": VERSION, "python": sys.version.split()[0], "plugin_root": paths.plugin_root(),
            "user_dir": paths.user_dir(), "tools": tools, "higgsfield_auth": auth, "config": cfg_info,
            "rules_missing": missing, "active_project": project.active_project(), "problems": problems,
            "ok": not problems}


def _doctor_text(r):
    lines = ["shotcraft %s (Python %s)" % (r["version"], r["python"])]
    for name, t in r["tools"].items():
        lines.append("  %-10s %s" % (name, (t["version"] or "found") if t["found"] else "not found"))
    lines.append("  higgsfield sign-in: %s" % r["higgsfield_auth"]["note"])
    lines.append("  projects folder: %s" % (r["config"]["projects_root"] or "not set"))
    if r["active_project"]:
        lines.append("  active project: %s" % r["active_project"])
    if r["problems"]:
        lines.append("To fix:")
        lines += ["  - " + p for p in r["problems"]]
    else:
        lines.append("All good.")
    return "\n".join(lines)


def cmd_setup(args):
    cfg = config.setup(args.projects_root)
    rep = doctor_report()
    emit(args, {"config": cfg, "doctor": rep},
         "Config saved. Projects go in %s.\n%s" % (cfg["projects_root"], _doctor_text(rep)))
    return 0


def cmd_doctor(args):
    rep = doctor_report()
    emit(args, rep, _doctor_text(rep))
    return 0


# ---------------------------------------------------------------- project

def cmd_project_init(args):
    proj = project.init_project(args.name, args.track, use_case=args.use_case, budget=args.budget,
                                threshold=args.threshold, root=args.root)
    opened = project.open_project(proj, args.session_id)
    emit(args, {"project": proj, "track": args.track, "opened": opened},
         "Project created at %s (track: %s). It is now the active project.\nNext: sc.py stage start %s"
         % (proj, args.track, stages.track_stages(args.track)[0]))
    return 0


def cmd_project_open(args):
    rec = project.open_project(args.path, args.session_id)
    emit(args, rec, "Active project: %s" % rec["project"])
    return 0


def _status_text(st):
    lines = ["%s  (track: %s, use case: %s)" % (st["name"], st["track"], st["use_case"] or "not set"),
             "  %s" % st["project"]]
    for row in st["stages"]:
        mark = {"done": "[x]", "open": "[>]", "skipped": "[-]", "pending": "[ ]"}[row["status"]]
        lines.append("  %s %-9s %s" % (mark, row["stage"], row["status"]))
    b = st["budget"]
    lines.append("  budget: %s spent, %s reserved, %s left (single-job threshold %s)"
                 % (b["spent"], b["reserved"], "no limit" if b["remaining"] is None else b["remaining"],
                    b["threshold_single_job"]))
    c = st["counts"]
    lines.append("  %d assets, %d generations (%d completed, %d approved)"
                 % (c["assets"], c["generations"], c["completed"], c["approved"]))
    return "\n".join(lines)


def cmd_project_status(args):
    st = project.status(_proj(args))
    emit(args, st, _status_text(st))
    return 0


# ---------------------------------------------------------------- stage

def _stage_status_text(st):
    lines = ["Track: %s" % st["track"]]
    for row in st["stages"]:
        mark = {"done": "[x]", "open": "[>]", "skipped": "[-]", "pending": "[ ]"}[row["status"]]
        extra = " (optional)" if row["optional"] and row["status"] == "pending" else ""
        lines.append("  %s %-9s %-8s %s%s" % (mark, row["stage"], row["status"], row["owner"] or "", extra))
    lines.append("Open: %s. Next: %s." % (", ".join(st["open"]) or "none", st["next"] or "none"))
    return "\n".join(lines)


def cmd_stage(args):
    proj = _proj(args)
    action = args.stage_cmd
    if action == "status":
        st = stages.status(proj)
        if args.stage:
            row = next((r for r in st["stages"] if r["stage"] == args.stage), None)
            if row is None:
                raise Refused("Stage %r is not on this track." % args.stage)
            emit(args, row, "%s: %s" % (row["stage"], row["status"]))
        else:
            emit(args, st, _stage_status_text(st))
        return 0
    if not args.stage:
        raise Refused("Name the stage: sc.py stage %s STAGE" % action)
    if action == "start":
        rec = stages.start(proj, args.stage, note=args.note)
        out = {"stage": args.stage, "status": rec["status"]}
        d = stages.load_stage_defs().get(args.stage, {})
        emit(args, out, "Stage %s is open. Owner: %s. Needs: %s. Gate: %s."
             % (args.stage, d.get("owner"), d.get("outputs"), ", ".join(d.get("gate", []))))
    elif action == "done":
        rec = stages.done(proj, args.stage, user_said=args.user_said, note=args.note)
        nxt = stages.status(proj)["next"]
        emit(args, {"stage": args.stage, "status": rec["status"], "evidence": rec["evidence"],
                    "qa_override": rec.get("qa_override"), "next": nxt},
             "Stage %s done.\n- %s\nNext: %s" % (args.stage, "\n- ".join(rec["evidence"] or []), nxt or "none"))
    elif action == "skip":
        rec = stages.skip(proj, args.stage, args.user_said, note=args.note)
        emit(args, {"stage": args.stage, "status": rec["status"]}, "Stage %s skipped." % args.stage)
    elif action == "reopen":
        res = stages.reopen(proj, args.stage, note=args.note, user_said=args.user_said)
        emit(args, res, "Stage %s is open again.%s" % (
            args.stage, (" Set back to pending: %s." % ", ".join(res["reset"])) if res["reset"] else ""))
    return 0


# ---------------------------------------------------------------- qa

def cmd_qa_record(args):
    proj = _proj(args)
    findings = None
    if args.findings:
        findings = jsonio.read_json(args.findings, default=None)
        if findings is None:
            raise ShotcraftError("Findings file %s is missing or empty." % args.findings)
    rec = stages.qa_record(proj, args.stage, args.round, args.verdict, findings=findings, note=args.note,
                           by=getattr(args, "by", None))
    for w in rec.get("warnings") or []:
        print("Note: %s" % w, file=sys.stderr)
    qa = stages.qa_status(proj, args.stage)
    emit(args, {"recorded": rec, "status": qa}, "QA %s round %d: %s. %s"
         % (args.stage, rec["round"], rec["verdict"], qa["message"]))
    return 0


def cmd_qa_status(args):
    qa = stages.qa_status(_proj(args), args.stage)
    emit(args, qa, "QA %s: %d round(s). %s" % (args.stage, len(qa["rounds"]), qa["message"]))
    return 0


# ---------------------------------------------------------------- budget

def cmd_budget_status(args):
    st = budget.status(_proj(args))
    emit(args, st, "Budget: %s credits total, %s spent, %s reserved, %s left. Single-job threshold: %s."
         % (st["credits"] if st["credits"] is not None else "no limit", st["spent"], st["reserved"],
            st["remaining"] if st["remaining"] is not None else "no limit", st["threshold_single_job"]))
    return 0


def cmd_budget_check(args):
    res = budget.check(_proj(args), args.credits, user_said=args.user_said)
    emit(args, res, ("OK: " if res["ok"] else "Needs the user's yes: ") + res["reason"])
    return 0 if res["ok"] else 2


def cmd_budget_set(args):
    st = budget.set_budget(_proj(args), credits=args.credits, threshold=args.threshold, user_said=args.user_said)
    emit(args, st, "Budget set: %s credits total, single-job threshold %s."
         % (st["credits"] if st["credits"] is not None else "no limit", st["threshold_single_job"]))
    return 0


def cmd_project_set(args):
    res = project.set_project(_proj(args), use_case=args.use_case, delivery_duration=args.delivery_duration,
                              user_said=args.user_said)
    emit(args, res, "Project updated: %s." % "; ".join(res["changes"]))
    return 0


# ---------------------------------------------------------------- brief (late intake answers)

ADDED_HEAD = "## Added after intake"


def _append_section(path, title, block):
    text = ""
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as fh:
            text = fh.read()
    if ADDED_HEAD not in text:
        text = text.rstrip("\n") + ("\n\n" if text.strip() else "# %s\n\n" % title) + ADDED_HEAD + "\n"
    text = text.rstrip("\n") + "\n\n" + block.strip("\n") + "\n"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)


def cmd_brief_add(args):
    """A question the intake missed, asked later: appended to grilling.md and job-card.md under
    '## Added after intake' (whatever the intake stage's lock) and recorded as a decision."""
    proj = _proj(args)
    q, a = (args.question or "").strip(), (args.answer or "").strip()
    if not q or not a:
        raise Refused("Give the question (--question) and the user's answer in their words (--answer).")
    stamp = jsonio.now_iso()
    _append_section(os.path.join(proj, "00_brief", "grilling.md"), "Grilling",
                    "Q (%s): %s\nA: %s" % (stamp[:10], q, a))
    _append_section(os.path.join(proj, "00_brief", "job-card.md"), "Job card",
                    "- %s: %s%s" % (args.line or q, a, ("  (%s)" % args.note) if args.note else ""))
    manifest.add_decision(proj, "intake", "Added after intake: %s" % q, a)
    emit(args, {"ok": True, "question": q, "answer": a},
         "Added to 00_brief/grilling.md and 00_brief/job-card.md under '%s'." % ADDED_HEAD)
    return 0


# ---------------------------------------------------------------- asset

def _unique_dest(folder, name):
    base, ext = os.path.splitext(name)
    dest, k = os.path.join(folder, name), 2
    while os.path.exists(dest):
        dest = os.path.join(folder, "%s-%d%s" % (base, k, ext))
        k += 1
    return dest


def cmd_asset_add(args):
    proj = _proj(args)
    src = os.path.abspath(os.path.expanduser(args.path))
    if not os.path.exists(src):
        alt = os.path.join(proj, args.path)
        if os.path.exists(alt):
            src = alt
        else:
            raise ShotcraftError("No file at %s." % args.path)
    copied = None
    if paths.rel_to(proj, src) is None:
        dest = _unique_dest(os.path.join(proj, "00_inputs"), os.path.basename(src))
        if os.path.isdir(src):
            shutil.copytree(src, dest)
        else:
            shutil.copy2(src, dest)
        copied, src = src, dest
    rel = paths.rel_to(proj, src)
    said = (args.user_said or "").strip()
    if args.rights == "generated" and not rel.startswith("06_generations/"):
        raise Refused("Only shotcraft's own generations are 'generated' (sc.py gen adds them from 06_generations/). "
                      "Register %s as owned, licensed or reference-only." % rel)
    known = manifest.load(proj).get("assets", [])
    same_path = [a for a in known if a.get("path") == rel and a.get("rights") == "reference-only"]
    if same_path:
        raise Refused("%s is already registered as %s (reference-only). To change its rights, use: sc.py asset mark "
                      "%s --rights owned|licensed --user-said \"...\"" % (rel, same_path[0]["id"], same_path[0]["id"]))
    ref_only = [a for a in known if a.get("rights") == "reference-only"]
    if ref_only and args.rights != "reference-only" and os.path.isfile(src):
        digest = manifest.file_sha256(src)
        twin = None
        for a in ref_only:
            try:
                if manifest.file_sha256(os.path.join(proj, a["path"])) == digest:
                    twin = a
                    break
            except (OSError, KeyError):
                continue
        if twin and not said:
            raise Refused("%s is the same file as %s (%s), a reference-only download. It can be %s only on the "
                          "user's own words (--user-said), or mark the reference itself: sc.py asset mark %s "
                          "--rights owned --user-said \"...\"" % (rel, twin["id"], twin["path"], args.rights, twin["id"]))
        if twin:
            args.note = ((args.note + " | ") if args.note else "") + "same file as reference-only %s" % twin["id"]
    if args.rights in ("owned", "licensed") and not rel.startswith("00_inputs/") \
            and not said:
        raise Refused("Only files in 00_inputs/ are taken as %s by default. Marking %s as %s needs the user's "
                      "own words (--user-said)." % (args.rights, rel, args.rights))
    note = args.note
    if copied:
        note = ((note + " | ") if note else "") + "copied from %s" % copied
    asset = manifest.add_asset(proj, src, args.rights, args.role, kind=args.kind, source_url=args.source_url,
                               note=note, shot=args.shot)
    if (args.user_said or "").strip():
        manifest.add_decision(proj, None, "Asset %s added as %s" % (asset["id"], args.rights), args.user_said)
    emit(args, asset, "Added %s: %s (%s, %s)%s" % (asset["id"], asset["path"], asset["role"], asset["rights"],
                                                    " - copied into 00_inputs/" if copied else ""))
    return 0


def cmd_asset_list(args):
    items = manifest.list_assets(_proj(args), role=args.role, shot=args.shot, rights=args.rights)
    text = "\n".join("%s  %-14s %-10s %-6s %s%s" % (a["id"], a["rights"], a["role"], a["kind"], a["path"],
                                                     ("  [%s]" % a["shot"]) if a.get("shot") else "")
                     for a in items) or "No assets."
    emit(args, items, text)
    return 0


def cmd_asset_mark(args):
    a = manifest.mark_asset(_proj(args), args.id, args.rights, args.user_said)
    emit(args, a, "%s is now %s." % (a["id"], a["rights"]))
    return 0


# ---------------------------------------------------------------- lessons

def _lessons_project(args):
    if getattr(args, "personal", False):
        return None
    if args.project:
        return project.resolve(args.project, args.session_id)
    return project.active_project(args.session_id)


def cmd_lessons_add(args):
    proj = _lessons_project(args)
    item = lessons.add(args.text, kind=args.kind, project=proj)
    emit(args, dict(item, inbox=lessons.inbox_path(proj)), "Logged lesson #%d (%s)." % (item["n"], item["kind"]))
    return 0


def cmd_lessons_list(args):
    proj = _lessons_project(args)
    items = lessons.list_lessons(proj, status=args.status)
    text = "\n".join("#%d [%s] %s — %s%s" % (l["n"], l["kind"], l["status"], l["text"],
                                             (' ("%s")' % l["user_said"]) if l["user_said"] else "")
                     for l in items) or "No lessons."
    emit(args, items, text)
    return 0


def cmd_lessons_decide(args):
    item = lessons.decide(args.n, args.decision, args.user_said, project=_lessons_project(args))
    emit(args, item, "Lesson #%d %s." % (item["n"], item["status"]))
    return 0


# ---------------------------------------------------------------- delegation

def delegate(group, cmd, modules):
    names = ["cli_%s_%s" % (group.replace("-", "_"), cmd.replace("-", "_"))] if cmd else []
    if not cmd or cmd == group:
        names += ["cli_%s" % group, "cli_%s_%s" % (group, group)]

    def run(args):
        tried = []
        for mod in modules:
            full = "shotcraft." + mod
            try:
                m = importlib.import_module(full)
            except ModuleNotFoundError as exc:
                if exc.name == full:
                    tried.append("scripts/shotcraft/%s.py (missing)" % mod)
                    continue
                raise
            for n in names:
                fn = getattr(m, n, None)
                if callable(fn):
                    rc = fn(args)
                    return 0 if rc is None else int(rc)
            tried.append("scripts/shotcraft/%s.py (no %s)" % (mod, " or ".join(names)))
        msg = ("'sc.py %s%s' is not available in this install. Looked for: %s."
               % (group, (" " + cmd) if cmd else "", "; ".join(tried)))
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": msg}))
        else:
            print(msg, file=sys.stderr)
        return 1
    return run


# ---------------------------------------------------------------- parser

def build_parser():
    def common_parser(suppress):
        c = argparse.ArgumentParser(add_help=False)
        kw = {"default": argparse.SUPPRESS} if suppress else {}
        c.add_argument("--json", action="store_true", help="print JSON", **kw)
        c.add_argument("--project", help="project folder (default: the active project for this session)", **kw)
        c.add_argument("--session-id", dest="session_id", help="Claude session id (default: $CLAUDE_SESSION_ID, else $CLAUDE_CODE_SESSION_ID)",
                       **kw)
        return c

    # The options work before or after the command; leaf copies use SUPPRESS so they never undo the top level.
    common = common_parser(True)
    p = argparse.ArgumentParser(prog="sc.py", description="shotcraft: an AI content production crew.",
                                parents=[common_parser(False)])
    p.add_argument("--version", action="version", version="shotcraft %s" % VERSION)
    g = p.add_subparsers(dest="group", metavar="GROUP")
    g.required = True

    def leaf(sub, name, func, **kw):
        sp = sub.add_parser(name, parents=[common], **kw)
        sp.set_defaults(func=func)
        return sp

    def group(name, help_):
        gp = g.add_parser(name, help=help_)
        s = gp.add_subparsers(dest="cmd", metavar="CMD")
        s.required = True
        return s

    sp = leaf(g, "setup", cmd_setup, help="first-run config, then doctor")
    sp.add_argument("--projects-root", dest="projects_root")
    leaf(g, "doctor", cmd_doctor, help="which tools exist, sign-in, config sanity")

    s = group("project", "create, open and inspect projects")
    sp = leaf(s, "init", cmd_project_init)
    sp.add_argument("--name", required=True)
    sp.add_argument("--track", required=True, choices=["full", "single", "quick", "refine"])
    sp.add_argument("--use-case", dest="use_case")
    sp.add_argument("--budget", type=float)
    sp.add_argument("--threshold", type=float)
    sp.add_argument("--root")
    sp = leaf(s, "open", cmd_project_open)
    sp.add_argument("path")
    leaf(s, "status", cmd_project_status)
    sp = leaf(s, "set", cmd_project_set, help="change the use case or delivery length after intake")
    sp.add_argument("--use-case", dest="use_case")
    sp.add_argument("--delivery-duration", dest="delivery_duration", type=float)
    sp.add_argument("--user-said", dest="user_said", required=True)

    s = group("brief", "late intake answers")
    sp = leaf(s, "add", cmd_brief_add, help="add a question the intake missed, with the user's answer")
    sp.add_argument("--question", required=True)
    sp.add_argument("--answer", required=True, help="the user's answer, in their words")
    sp.add_argument("--line", help="the job-card line it belongs to (default: the question)")
    sp.add_argument("--note")

    s = group("stage", "stage gates: status, start, done, skip, reopen")
    for name in ("status", "start", "done", "skip", "reopen"):
        sp = leaf(s, name, cmd_stage)
        sp.set_defaults(stage_cmd=name)
        sp.add_argument("stage", nargs="?" if name == "status" else None)
        sp.add_argument("--user-said", dest="user_said")
        sp.add_argument("--note")

    s = group("qa", "QA rounds")
    sp = leaf(s, "record", cmd_qa_record)
    sp.add_argument("--stage", required=True)
    sp.add_argument("--round", required=True, type=int)
    sp.add_argument("--verdict", required=True, type=str.upper, choices=["PASS", "FAIL"])
    sp.add_argument("--findings", help="JSON file with the round's findings (required for FAIL): the reviewer's "
                                       "findings array, or its whole return object with a findings key")
    sp.add_argument("--by", choices=["qa-supervisor", "script-supervisor"],
                    help="who ran the round (continuity gates need script-supervisor)")
    sp.add_argument("--note")
    sp = leaf(s, "status", cmd_qa_status)
    sp.add_argument("--stage", required=True)

    s = group("budget", "credit budget")
    leaf(s, "status", cmd_budget_status)
    sp = leaf(s, "check", cmd_budget_check)
    sp.add_argument("--credits", required=True, type=float)
    sp.add_argument("--user-said", dest="user_said")
    sp = leaf(s, "set", cmd_budget_set, help="record the budget settled at intake")
    sp.add_argument("--credits", type=float)
    sp.add_argument("--threshold", type=float)
    sp.add_argument("--user-said", dest="user_said", required=True)

    s = group("asset", "project assets and their rights")
    sp = leaf(s, "add", cmd_asset_add)
    sp.add_argument("path")
    sp.add_argument("--rights", required=True, choices=list(manifest.RIGHTS))
    sp.add_argument("--role", required=True, choices=list(manifest.ROLES))
    sp.add_argument("--kind", choices=list(manifest.KINDS))
    sp.add_argument("--source-url", dest="source_url")
    sp.add_argument("--shot")
    sp.add_argument("--note")
    sp.add_argument("--user-said", dest="user_said")
    sp = leaf(s, "list", cmd_asset_list)
    sp.add_argument("--role")
    sp.add_argument("--shot")
    sp.add_argument("--rights")
    sp = leaf(s, "mark", cmd_asset_mark)
    sp.add_argument("id")
    sp.add_argument("--rights", required=True, choices=list(manifest.RIGHTS))
    sp.add_argument("--user-said", dest="user_said", required=True)

    s = group("lessons", "the lessons inbox")
    sp = leaf(s, "add", cmd_lessons_add)
    sp.add_argument("text")
    sp.add_argument("--kind", default="general", choices=list(lessons.KINDS))
    sp.add_argument("--personal", action="store_true", help="log to ~/.shotcraft/lessons.md even with a project")
    sp = leaf(s, "list", cmd_lessons_list)
    sp.add_argument("--status", choices=["open", "accepted", "rejected"])
    sp.add_argument("--personal", action="store_true")
    sp = leaf(s, "decide", cmd_lessons_decide)
    sp.add_argument("n", type=int)
    sp.add_argument("decision", choices=["accept", "reject"])
    sp.add_argument("--user-said", dest="user_said", required=True)
    sp.add_argument("--personal", action="store_true")

    # ---- delegated groups
    s = group("card", "prompt cards")
    sp = leaf(s, "new", delegate("card", "new", ["cards"]))
    sp.add_argument("--shot", required=True)
    sp.add_argument("--kind", choices=["image", "video"])
    sp.add_argument("--use-case", dest="use_case")
    sp.add_argument("--from-text", dest="from_text")
    sp.add_argument("--force", action="store_true", help="overwrite an existing card")
    sp = leaf(s, "validate", delegate("card", "validate", ["cards"]))
    sp.add_argument("path")
    sp = leaf(s, "compile", delegate("card", "compile", ["compiler", "cards"]))
    sp.add_argument("path")
    sp.add_argument("--model", required=True)
    sp.add_argument("--provider")
    sp.add_argument("--dry-run", dest="dry_run", action="store_true", help="print only; leave the card as it is")
    sp = leaf(s, "approve", delegate("card", "approve", ["cards"]))
    sp.add_argument("path")
    sp.add_argument("--user-said", dest="user_said", required=True)
    sp = leaf(s, "set-input", delegate("card", "set-input", ["cards"]))
    sp.add_argument("path")
    sp.add_argument("--asset", required=True)
    sp.add_argument("--as", dest="as_role", required=True,
                    choices=["start_frame", "end_frame", "reference", "character", "style", "source"])
    sp.add_argument("--user-said", dest="user_said", required=True)

    s = group("refine", "refine track")
    sp = leaf(s, "save", delegate("refine", "save", ["cards", "compiler"]))
    sp.add_argument("card_text_file")

    s = group("quick", "quick track: one shot, one price, one yes")
    sp = leaf(s, "plan", delegate("quick", "plan", ["quick"]),
              help="set up a quick project from a card and get the live price (spends nothing)")
    sp.add_argument("card", help="the prompt card (for example a refine card)")
    sp.add_argument("--name", help="project name (default: the card's title); a date stamp is added")
    sp.add_argument("--input", action="append", help="an input file (repeat for several)")
    sp.add_argument("--as", dest="as_role", action="append",
                    choices=["source", "start_frame", "end_frame", "reference", "character", "style"],
                    help="its role, one per --input: source = the video to edit (relight, sky, restyle)")
    sp.add_argument("--rights", choices=["owned", "licensed", "reference-only"],
                    help="whose the inputs are (needed with --input)")
    sp.add_argument("--trim", help="START-END seconds to cut from a video input, for example 22-26")
    sp.add_argument("--crop", help="ffmpeg crop W:H:X:Y for a video input, for example 1215:2160:1400:0")
    sp.add_argument("--scale", help="ffmpeg scale after the crop, for example 1080:1920")
    sp.add_argument("--tier", choices=["draft", "final"], help="default final (on --update: the tier priced before)")
    sp.add_argument("--model")
    sp.add_argument("--variants", type=int)
    sp.add_argument("--budget", type=float)
    sp.add_argument("--threshold", type=float)
    sp.add_argument("--root")
    sp.add_argument("--update", action="store_true", help="re-price the active quick project with a changed card")
    sp.add_argument("--recipe", help="relight, sky, cleanup, background, animate, extend (sc.py quick recipes)")
    sp = leaf(s, "recipes", delegate("quick", "recipes", ["quick"]),
              help="which recipe fits the user's words and file (relight, sky, cleanup, background, ...)")
    sp.add_argument("--say", help="the user's words")
    sp.add_argument("--file", help="the file they gave")
    sp = leaf(s, "go", delegate("quick", "go", ["quick"]),
              help="the user's yes to the shown prompt and price: approve, generate, wait, download")
    sp.add_argument("--user-said", dest="user_said", required=True)
    sp.add_argument("--timeout", type=int, help="seconds to wait (default 1800)")
    sp.add_argument("--no-wait", dest="no_wait", action="store_true")
    sp = leaf(s, "keep", delegate("quick", "keep", ["quick"]), help="the user keeps the result; closes the project")
    sp.add_argument("--user-said", dest="user_said", required=True)
    sp.add_argument("--gen-id", dest="gen_id")
    sp.add_argument("--note")
    sp = leaf(s, "redo", delegate("quick", "redo", ["quick"]), help="reject the result with what to change")
    sp.add_argument("--user-said", dest="user_said", required=True)
    sp.add_argument("--note", required=True)
    sp.add_argument("--gen-id", dest="gen_id")

    sp = leaf(g, "route", delegate("route", None, ["routing"]), help="pick a model for a use case and tier")
    sp.add_argument("--use-case", dest="use_case", required=True)
    sp.add_argument("--tier", required=True, choices=["board", "draft", "final", "upscale"])
    sp.add_argument("--kind", choices=["image", "video"])
    sp.add_argument("--duration", type=float)
    sp.add_argument("--needs", help="comma list: audio,refs,end_frame,...")

    s = group("gen", "generation (the only way to generate)")
    for name in ("estimate", "submit"):
        sp = leaf(s, name, delegate("gen", name, ["gen"]))
        sp.add_argument("card")
        sp.add_argument("--tier", required=True, choices=["board", "draft", "final", "upscale"])
        sp.add_argument("--model")
        sp.add_argument("--variants", type=int, help="how many takes (default: the card's settings.variants)")
        if name == "submit":
            sp.add_argument("--user-said", dest="user_said", help="the user's yes to the cost (budget)")
            sp.add_argument("--skip-draft-said", dest="skip_draft_said",
                            help="the user's yes to a final with no approved draft (or an upscale with no "
                                 "approved final)")
            sp.add_argument("--wait", action="store_true")
            sp.add_argument("--timeout", type=int, help="seconds to wait with --wait (default 600)")
    for name in ("status", "fetch"):
        sp = leaf(s, name, delegate("gen", name, ["gen"]))
        sp.add_argument("gen_id")
        if name == "fetch":
            sp.add_argument("--timeout", type=int, help="seconds to wait for a running job (default 600)")
    for name in ("approve", "reject"):
        sp = leaf(s, name, delegate("gen", name, ["gen"]))
        sp.add_argument("gen_id")
        sp.add_argument("--user-said", dest="user_said", required=True)
        sp.add_argument("--note")

    s = group("refs", "reference downloads")
    sp = leaf(s, "fetch", delegate("refs", "fetch", ["refs"]))
    sp.add_argument("url")
    sp.add_argument("--note")
    sp.add_argument("--shot")
    sp.add_argument("--cookies-from-browser", dest="cookies_from_browser",
                    help="browser to borrow sign-in cookies from (only with the user's OK)")

    s = group("sheet", "contact sheets")
    sp = leaf(s, "build", delegate("sheet", "build", ["contact_sheet"]))
    sp.add_argument("--tier", required=True, choices=["board", "draft", "final"])
    sp.add_argument("--open", action="store_true")

    s = group("delivery", "delivery checks")
    sp = leaf(s, "check", delegate("delivery", "check", ["delivery"]))
    sp.add_argument("--spec", help="preset id (default: the project's use case)")
    sp.add_argument("--duration", type=float, help="expected length of each video in seconds")
    sp.add_argument("--tolerance", type=float, help="duration tolerance in seconds (default 0.5)")
    sp.add_argument("--lufs", type=float, help="loudness target in LUFS (default: the preset, else -14)")

    s = group("assembly", "animatic / string-out")
    sp = leaf(s, "animatic", delegate("assembly", "animatic", ["assembly"]))
    sp.add_argument("--audio")
    sp.add_argument("--burn-ids", dest="burn_ids", action="store_true", help="burn shot ids into the picture")

    s = group("finish", "natural-finish pass: matched grain, room tone")
    sp = leaf(s, "texture", delegate("finish", "texture", ["finish"]),
              help="add matched film grain (and an optional mild vignette) to a clip or still")
    sp.add_argument("file")
    sp.add_argument("--grain", choices=["off", "subtle", "film"], default="subtle")
    sp.add_argument("--vignette", action="store_true")
    sp.add_argument("--out", help="output file, relative to the current directory (default: <name>-texture "
                                  "next to the source; required for a source inside 09_delivery/)")
    sp = leaf(s, "roomtone", delegate("finish", "roomtone", ["finish"]),
              help="safety floor: lay one room-tone bed under the audio so it never drops to digital silence")
    sp.add_argument("file")
    sp.add_argument("--bed", help="a recorded room tone or ambience to loop (preferred over the generated floor)")
    sp.add_argument("--level", type=float, default=-60.0, help="bed level in dBFS (-80 to -40, default -60)")
    sp.add_argument("--out", help="output file, relative to the current directory (default: <name>-roomtone "
                                  "next to the source; required for a source inside 09_delivery/)")

    s = group("scout", "model check")
    leaf(s, "check", delegate("scout", "check", ["scout"]))
    leaf(s, "report", delegate("scout", "report", ["scout"]))
    leaf(s, "ack", delegate("scout", "ack", ["scout"]), help="the user has decided every proposal")

    s = group("shots", "per-shot progress: start a batch, lock approved shots")
    leaf(s, "status", delegate("shots", "status", ["shots"]))
    for name, helptext in (("start", "put shots in progress (after the whole board is approved)"),
                           ("pause", "take shots out of progress")):
        sp = leaf(s, name, delegate("shots", name, ["shots"]), help=helptext)
        sp.add_argument("shots", nargs="*", help="S010, S010-S040 or a comma list")
        sp.add_argument("--all", action="store_true")
        sp.add_argument("--scene", action="append", help="every shot in this scene (repeat for more)")
        sp.add_argument("--user-said", dest="user_said", required=True)
    for name in ("lock", "unlock"):
        sp = leaf(s, name, delegate("shots", name, ["shots"]))
        sp.add_argument("shot")
        sp.add_argument("--user-said", dest="user_said", required=True)

    s = group("board", "storyboard app: script, look book, references and the Higgsfield mapping")
    sp = leaf(s, "init", delegate("board", "init", ["board"]), help="write a sample board/board.json")
    sp.add_argument("--force", action="store_true", help="replace an existing board.json")
    leaf(s, "check", delegate("board", "check", ["board"]), help="validate the board and show each shot's cards")
    sp = leaf(s, "add", delegate("board", "add", ["board"]), help="put an image from disk on the board")
    sp.add_argument("path")
    sp.add_argument("--shot", required=True, help="the board's shot number, 0 for the look book")
    sp.add_argument("--attr", required=True, help="Character, Wardrobe, Props, Environment, Camera, Lighting, "
                                                   "Mood, Frame, or a look book row")
    sp.add_argument("--label", help="the name prompts mention as @Label")
    sp.add_argument("--rights", choices=["reference-only", "owned", "licensed", "generated"])
    sp.add_argument("--user-said", dest="user_said")
    leaf(s, "inputs", delegate("board", "inputs", ["board"]),
         help="card inputs the board's sendable references call for (proposals only)")
    sp = leaf(s, "serve", delegate("board", "serve", ["board"]), help="open the storyboard on 127.0.0.1")
    sp.add_argument("--port", type=int, default=8765)
    sp.add_argument("--no-open", dest="no_open", action="store_true", help="print the link, don't open a browser")

    s = group("handoff", "Higgsfield hand-off")
    leaf(s, "build", delegate("handoff", "build", ["handoff"]))
    sp = leaf(s, "upload", delegate("handoff", "upload", ["handoff"]))
    sp.add_argument("--dry-run", dest="dry_run", action="store_true")
    sp.add_argument("--user-said", dest="user_said", help="the user's yes to uploading (needed unless --dry-run)")

    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "session_id", None):
        args.session_id = project.session_id_from(None)
    try:
        return args.func(args)
    except Refused as exc:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "refused": True, "reason": str(exc)}, ensure_ascii=False))
        else:
            print("Refused: %s" % exc, file=sys.stderr)
        return 2
    except ShotcraftError as exc:
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        else:
            print("Error: %s" % exc, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 1
    except Exception as exc:  # last resort: never a bare traceback for the user
        if os.environ.get("SHOTCRAFT_DEBUG"):
            raise
        msg = "Unexpected error: %s: %s (set SHOTCRAFT_DEBUG=1 for details)" % (type(exc).__name__, exc)
        if getattr(args, "json", False):
            print(json.dumps({"ok": False, "error": msg}))
        else:
            print(msg, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
