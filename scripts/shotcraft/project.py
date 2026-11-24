"""Projects: create the folder layout, register the active project for a Claude session, report status.

API:
    FOLDERS                                  every folder made by init (SPEC §2)
    slugify(text) -> str                     "Sydney Dawn Reel!" -> "sydney-dawn-reel"
    session_id_from(explicit=None) -> str|None   --session-id, else $CLAUDE_SESSION_ID or $CLAUDE_CODE_SESSION_ID
    init_project(name, track, use_case=None, budget=None, threshold=None, root=None) -> abs path
    is_project(path) -> bool
    find_project_root(path) -> str|None      walks up from a file or folder to the folder holding project.json
    open_project(path, session_id=None) -> dict   writes sessions/<id>.json (when there is an id) and active.json
    active_project(session_id=None) -> str|None    session file first, then active.json; None if gone
    resolve(explicit=None, session_id=None) -> str  --project, else the active project; raises Refused if none
    load_preset(use_case) -> dict|None       a preset from rules/presets.json (personal layer over plugin)
    status(project) -> dict                  name, track, stages, budget, counts, open stage
    set_project(project, use_case=None, delivery_duration=None, user_said=None) -> dict
                                             change the use case (re-applies the preset's delivery block) or the
                                             delivery length after intake; needs the user's words
"""
import os
import re
import unicodedata

from . import Refused, ShotcraftError, config, jsonio, manifest, paths

FOLDERS = [
    "00_brief", "00_inputs",
    "01_research", "01_research/refs",
    "02_concept", "03_script",
    "04_bible", "04_bible/characters", "04_bible/environments", "04_bible/props", "04_bible/moodboard",
    "05_prompts",
    "06_generations", "06_generations/boards", "06_generations/drafts", "06_generations/finals",
    "06_generations/upscaled", "06_generations/contact-sheets",
    "07_mograph", "07_mograph/ae", "07_mograph/code",
    "08_sound", "09_assembly", "10_delivery", "11_handoff",
    ".shotcraft", ".shotcraft/qa", ".shotcraft/rules",
]


def slugify(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    text = re.sub(r"-{2,}", "-", text)
    return text[:60].strip("-") or "project"


def session_id_from(explicit=None):
    sid = explicit or os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("CLAUDE_CODE_SESSION_ID") or None
    return str(sid) if sid else None


def _load_rules_file(name):
    """Plugin rules/<name> with the personal layer shallow-merged on top (for presets)."""
    base = jsonio.read_json(os.path.join(paths.rules_dir(), name), default=None)
    mine = jsonio.read_json(os.path.join(paths.user_rules_dir(), name), default=None)
    if base is None and mine is None:
        return None
    out = dict(base or {})
    for k, v in (mine or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            merged = dict(out[k])
            merged.update(v)
            out[k] = merged
        else:
            out[k] = v
    return out


def _presets_table():
    data = _load_rules_file("presets.json")
    if data is None:
        return None
    if isinstance(data.get("presets"), dict):
        return data["presets"]
    return {k: v for k, v in data.items() if isinstance(v, dict)}


def load_preset(use_case):
    table = _presets_table()
    if not table or not use_case:
        return None
    return table.get(use_case)


def _delivery_from_preset(preset):
    if not preset:
        return {}
    res = preset.get("resolution")
    if isinstance(res, dict):
        res = res.get("delivery") or res.get("final") or res.get("draft")
    dur = preset.get("duration")
    if isinstance(dur, dict):
        dur = dur.get("typical")
    fmts = preset.get("delivery_formats") or preset.get("formats") or []
    return {"aspect": preset.get("aspect"), "resolution": res, "fps": preset.get("fps"), "duration_s": dur,
            "formats": list(fmts) if isinstance(fmts, (list, tuple)) else [fmts]}


def init_project(name, track, use_case=None, budget=None, threshold=None, root=None):
    from . import stages  # local import: stages imports project helpers

    if not (name or "").strip():
        raise Refused("A project needs a name (--name).")
    tracks = stages.load_tracks()
    if track not in tracks["tracks"]:
        raise Refused("Unknown track %r. Tracks: %s." % (track, ", ".join(tracks["tracks"])))
    cfg = config.load()
    base = os.path.abspath(os.path.expanduser(root)) if root else config.projects_root(cfg)
    if not base:
        raise Refused("No projects folder set. Run: sc.py setup --projects-root DIR (or pass --root DIR).")
    preset = None
    if use_case:
        table = _presets_table()
        if table is not None:
            preset = table.get(use_case)
            if preset is None:
                raise Refused("Unknown use case %r. Known: %s." % (use_case, ", ".join(sorted(table))))
    slug = slugify(name)
    proj = os.path.join(base, slug)
    if os.path.exists(paths.manifest_file(proj)):
        raise Refused("A project already exists at %s. Open it with: sc.py project open %s" % (proj, proj))
    for d in FOLDERS:
        os.makedirs(os.path.join(proj, d), exist_ok=True)
    thr = threshold if threshold is not None else cfg.get("default_threshold_credits", 50)
    included = stages.track_stages(track)
    data = manifest.new_manifest(
        name=name.strip(), slug=slug, track=track, use_case=use_case,
        delivery=_delivery_from_preset(preset),
        budget={"credits": budget, "threshold_single_job": thr, "spent": 0, "reserved": 0},
        stages_included=included, provider=cfg.get("provider") or "higgsfield")
    manifest.save(proj, data)
    stages.init_state(proj, track)
    lessons = paths.project_lessons_file(proj)
    if not os.path.exists(lessons):
        with open(lessons, "w", encoding="utf-8") as fh:
            fh.write("# Lessons inbox\n\n")
    return proj


def is_project(path):
    return bool(path) and os.path.isfile(paths.manifest_file(path))


def find_project_root(path):
    cur = os.path.abspath(path)
    if os.path.isfile(cur) or not os.path.exists(cur):
        cur = os.path.dirname(cur)
    while True:
        if is_project(cur):
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def open_project(path, session_id=None):
    proj = os.path.abspath(os.path.expanduser(path))
    if not is_project(proj):
        found = find_project_root(proj)
        if not found:
            raise ShotcraftError("No shotcraft project at %s (no project.json)." % proj)
        proj = found
    record = {"project": proj, "opened_at": jsonio.now_iso()}
    sid = session_id_from(session_id)
    if sid:
        jsonio.write_json(paths.session_file(sid), record)
    jsonio.write_json(paths.active_file(), record)
    return {"project": proj, "session_id": sid, "opened_at": record["opened_at"]}


def active_project(session_id=None):
    sid = session_id_from(session_id)
    candidates = []
    if sid:
        candidates.append(paths.session_file(sid))
    candidates.append(paths.active_file())
    for f in candidates:
        try:
            rec = jsonio.read_json(f, default=None)
        except ShotcraftError:
            rec = None
        if isinstance(rec, dict) and is_project(rec.get("project")):
            return rec["project"]
    return None


def resolve(explicit=None, session_id=None):
    if explicit:
        proj = os.path.abspath(os.path.expanduser(explicit))
        if is_project(proj):
            return proj
        found = find_project_root(proj)
        if found:
            return found
        raise Refused("No shotcraft project at %s." % proj)
    proj = active_project(session_id)
    if not proj:
        raise Refused("No active project. Open one with: sc.py project open PATH (or pass --project PATH).")
    return proj


def status(project):
    from . import budget, stages

    data = manifest.load(project)
    st = stages.status(project)
    gens = data.get("generations", [])
    return {
        "project": project,
        "name": data.get("name"),
        "slug": data.get("slug"),
        "track": data.get("track"),
        "use_case": data.get("use_case"),
        "delivery": data.get("delivery"),
        "open": st["open"],
        "next": st["next"],
        "stages": st["stages"],
        "budget": budget.status(project),
        "counts": {
            "assets": len(data.get("assets", [])),
            "generations": len(gens),
            "completed": sum(1 for g in gens if g.get("status") == "completed"),
            "approved": sum(1 for g in gens if g.get("approved") is True),
            "decisions": len(data.get("decisions", [])),
        },
    }


def set_project(project, use_case=None, delivery_duration=None, user_said=None):
    if not (user_said or "").strip():
        raise Refused("Changing the project's use case or delivery needs the user's own words (--user-said).")
    if use_case is None and delivery_duration is None:
        raise Refused("Give --use-case, --delivery-duration or both.")
    data = manifest.load(project)
    changes = []
    if use_case is not None:
        table = _presets_table()
        preset = (table or {}).get(use_case)
        if table is not None and preset is None:
            raise Refused("Unknown use case %r. Known: %s." % (use_case, ", ".join(sorted(table))))
        changes.append("use case %s -> %s" % (data.get("use_case"), use_case))
        data["use_case"] = use_case
        data["delivery"] = _delivery_from_preset(preset)
    if delivery_duration is not None:
        try:
            d = float(delivery_duration)
        except (TypeError, ValueError):
            raise Refused("--delivery-duration must be a number of seconds.")
        if d <= 0:
            raise Refused("--delivery-duration must be more than 0 seconds.")
        d = int(d) if d.is_integer() else d
        data.setdefault("delivery", {})
        changes.append("delivery length %s -> %s s" % (data["delivery"].get("duration_s"), d))
        data["delivery"]["duration_s"] = d
    data["decisions"].append({"at": jsonio.now_iso(), "stage": None, "text": "Project changed: " + "; ".join(changes),
                              "user_said": user_said.strip()})
    manifest.save(project, data)
    return {"use_case": data.get("use_case"), "delivery": data.get("delivery"), "changes": changes}
