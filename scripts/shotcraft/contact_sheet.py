"""Contact sheets for boards, drafts and finals: one self-contained HTML page per build, saved as
06_generations/contact-sheets/<tier>-<YYYYMMDD-HHMMSS>.html (the boards/drafts stage evidence checks the sheet
recorded in project.json: built here, unchanged, and showing every completed take). Estimate-only records are
left out: they are not takes and cost nothing.

The page has a row per shot (shot-list order), with every take of that tier side by side: the picture (<img>) or
clip (<video controls loop muted>), the model, cost, status, approval and the user's words, and the compiled
prompt. Media paths are relative to the sheet, so the project folder can move. Light and dark themes follow the
system setting. No scripts, no network.

API:
    TIER_GENS                       sheet tier -> generation tiers shown
    collect(project, tier) -> {"project", "name", "tier", "shots": [{"shot", "title", "purpose", "duration_s",
                                "takes": [...]}], "totals": {...}}
    render(data, sheet_dir, project) -> html str
    build(project, tier, stamp=None) -> {"path", "rel", "shots", "takes", "missing"}   (recorded in project.json
                                    "sheets" with its sha256 and the completed generations it shows)
    record_sheet(project, tier, rel, sha256, gen_ids)
    open_file(path) -> bool         opens with the OS viewer when one exists (open / xdg-open / startfile)
    cli_sheet_build(args) -> int    sc.py sheet build --tier board|draft|final [--open]
"""
import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys

from . import Refused, jsonio, manifest

TIER_GENS = {"element": ("element",), "board": ("board",), "draft": ("draft",), "final": ("final", "upscale")}
SPENDING = ("submitted", "queued", "in_progress", "completed")
TIER_LABEL = {"element": "Elements", "board": "Boards", "draft": "Drafts", "final": "Finals"}
SHEET_DIR = "06_generations/contact-sheets"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".webm", ".mkv"}
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif", ".svg", ".bmp"}

_STATUS_HELP = {
    "failed": "The provider could not make it. Often the prompt content; rephrase and try again.",
    "nsfw": "Blocked by the content filter. Rephrase the prompt.",
    "ip_detected": "Blocked as protected content (a brand or known character). Rephrase.",
    "canceled": "The job was canceled.",
    "estimated": "Only estimated; not generated yet.",
    "submitted": "Still generating.", "queued": "Still generating.", "in_progress": "Still generating.",
}


def _model_names(project):
    try:
        from . import rules
        data = rules.load("models", project)
        out = {}
        for prov in (data.get("providers") or {}).values():
            for mid, prof in (prov.get("models") or {}).items():
                out[mid] = prof.get("name") or mid
        return out
    except Exception:
        return {}


def _shot_info(project):
    from . import stages
    rows = {}
    try:
        for r in stages.parse_shotlist(project):
            if r.get("id"):
                rows[r["id"]] = r
    except Exception:
        pass
    try:
        order = stages.planned_shots(project)
    except Exception:
        order = list(rows)
    return order, rows


def _card(project, shot):
    from . import stages
    folder = ("04_elements", "cards") if re.match(r"^E\d{2,3}[A-Z]$", str(shot)) else ("05_prompts",)
    return stages.read_card_meta(os.path.join(project, *(folder + ("%s.md" % shot,)))) or {}


def collect(project, tier):
    if tier not in TIER_GENS:
        raise Refused("Tier must be element, board, draft or final.")
    data = manifest.load(project)
    names = _model_names(project)
    # estimate-only records are not takes: they cost nothing and can't be approved or rejected
    gens = [g for g in data.get("generations", []) if g.get("tier") in TIER_GENS[tier]
            and g.get("status") != "estimated"]
    order, rows = _shot_info(project)
    if tier == "element":  # one row per element view card, not per shot
        order = []
        for el in data.get("elements") or []:
            order += list((el.get("views") or {}).values())
    for g in gens:
        if g.get("shot") and g["shot"] not in order:
            order.append(g["shot"])
    if any(not g.get("shot") for g in gens):
        order.append(None)
    shots, total_cost, n_takes, missing = [], 0.0, 0, []
    for sid in order:
        mine = [g for g in gens if g.get("shot") == sid]
        meta = _card(project, sid) if sid else {}
        row = rows.get(sid, {})
        takes = []
        for g in mine:
            cost = g.get("cost_actual")
            if cost is None and g.get("status") in SPENDING:
                cost = g.get("cost_estimate")
            if isinstance(cost, (int, float)):
                total_cost += cost
            outs = list(g.get("outputs") or [])
            files = []
            for o in outs:
                exists = os.path.isfile(os.path.join(project, o))
                if not exists:
                    missing.append(o)
                files.append({"path": o, "exists": exists})
            n_takes += max(1, len(files))
            takes.append({
                "id": g.get("id"), "tier": g.get("tier"), "model": g.get("model"),
                "model_name": names.get(g.get("model"), g.get("model")),
                "cost": cost, "cost_is_estimate": g.get("cost_actual") is None and cost is not None,
                "status": g.get("status"), "approved": g.get("approved"), "approval_said": g.get("approval_said"),
                "note": g.get("note") or g.get("reject_note"), "prompt": g.get("prompt"),
                "params": g.get("params") or {}, "files": files, "inputs": g.get("inputs") or [],
                "created": g.get("created"),
            })
        settings = meta.get("settings") or {}
        shots.append({
            "shot": sid, "title": meta.get("title") or row.get("purpose") or "",
            "purpose": row.get("purpose") or "", "kind": meta.get("kind") or row.get("kind") or "",
            "duration_s": settings.get("duration_s") or row.get("duration_value"),
            "takes": takes,
        })
    approved = sum(1 for g in gens if g.get("approved") is True)
    rejected = sum(1 for g in gens if g.get("approved") is False)
    undecided = sum(1 for g in gens if g.get("status") == "completed" and g.get("approved") is None)
    return {"project": project, "name": data.get("name"), "use_case": data.get("use_case"), "tier": tier,
            "built": jsonio.now_iso(), "shots": shots, "missing": missing,
            "totals": {"generations": len(gens), "takes": n_takes, "cost": round(total_cost, 2),
                       "approved": approved, "rejected": rejected,
                       "undecided": undecided},
            "gen_ids": [g.get("id") for g in gens if g.get("status") == "completed"]}


# ---------------------------------------------------------------- HTML

CSS = """
:root { --bg:#f6f5f2; --card:#ffffff; --ink:#1c1c1e; --muted:#6b6b70; --line:#e2e0db; --accent:#2f6fde;
  --ok:#1f8a4c; --bad:#c0392b; --wait:#b7791f; --code:#f0eee9; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#141416; --card:#1e1e21; --ink:#ececef; --muted:#9a9aa1; --line:#2e2e33; --accent:#6ea0ff;
    --ok:#4cc38a; --bad:#ff6b5e; --wait:#e0a84a; --code:#26262a; }
}
* { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--ink);
  font:15px/1.45 -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }
header { padding:24px 16px 8px; max-width:1400px; margin:0 auto; }
h1 { font-size:22px; margin:0 0 4px; }
.sub { color:var(--muted); font-size:13px; }
.totals { display:flex; flex-wrap:wrap; gap:8px; margin:12px 0 0; }
.pill { border:1px solid var(--line); background:var(--card); border-radius:999px; padding:3px 10px; font-size:13px; }
main { max-width:1400px; margin:0 auto; padding:8px 16px 48px; }
section.shot { border-top:1px solid var(--line); padding:18px 0; }
section.shot h2 { font-size:17px; margin:0 0 2px; }
section.shot .meta { color:var(--muted); font-size:13px; margin-bottom:10px; }
.grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(260px, 1fr)); gap:14px; }
.take { background:var(--card); border:1px solid var(--line); border-radius:10px; overflow:hidden;
  display:flex; flex-direction:column; }
.take.approved { border-color:var(--ok); box-shadow:0 0 0 1px var(--ok); }
.take.rejected { opacity:.6; }
.media { background:#000; display:flex; align-items:center; justify-content:center; min-height:140px; }
.media img, .media video { width:100%; height:auto; max-height:420px; object-fit:contain; display:block; }
.media .none { color:#aaa; font-size:13px; padding:24px; text-align:center; }
.body { padding:10px 12px 12px; font-size:13px; }
.row { display:flex; justify-content:space-between; gap:8px; flex-wrap:wrap; }
.tag { font-weight:600; }
.status-completed { color:var(--ok); } .status-failed, .status-nsfw, .status-ip_detected, .status-canceled { color:var(--bad); }
.status-queued, .status-in_progress, .status-submitted, .status-estimated { color:var(--wait); }
.ok { color:var(--ok); font-weight:600; } .bad { color:var(--bad); font-weight:600; } .muted { color:var(--muted); }
details { margin-top:8px; } summary { cursor:pointer; color:var(--accent); }
pre { white-space:pre-wrap; word-wrap:break-word; background:var(--code); padding:8px; border-radius:6px;
  font:12px/1.4 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; margin:6px 0 0; }
.said { font-style:italic; }
.empty { color:var(--muted); font-size:13px; }
footer { color:var(--muted); font-size:12px; max-width:1400px; margin:0 auto; padding:0 16px 32px; }
"""


def _e(x):
    return html.escape("" if x is None else str(x), quote=True)


def _rel_url(project, rel, sheet_dir):
    full = os.path.join(project, rel)
    r = os.path.relpath(full, sheet_dir).replace(os.sep, "/")
    from urllib.parse import quote
    return quote(r, safe="/._-~")


def _media(project, f, sheet_dir):
    if not f["exists"]:
        return '<div class="none">File not found:<br>%s</div>' % _e(f["path"])
    ext = os.path.splitext(f["path"])[1].lower()
    url = _rel_url(project, f["path"], sheet_dir)
    if ext in VIDEO_EXT:
        return '<video src="%s" controls loop muted playsinline preload="metadata"></video>' % url
    if ext in IMAGE_EXT:
        return '<img src="%s" alt="%s" loading="lazy">' % (url, _e(os.path.basename(f["path"])))
    return '<div class="none"><a href="%s">%s</a></div>' % (url, _e(os.path.basename(f["path"])))


def _params_text(p):
    keep = []
    for k in ("aspect_ratio", "resolution", "duration", "audio", "mode", "quality"):
        if k in p and p[k] not in (None, ""):
            v = p[k]
            if k == "duration":
                v = "%s s" % v
            elif k == "audio":
                v = "on" if v else "off"
            keep.append("%s %s" % (k.replace("_ratio", "").replace("_", " "), v))
    return ", ".join(keep)


def _take_html(project, shot, t, n, sheet_dir):
    cls = "take" + (" approved" if t["approved"] is True else (" rejected" if t["approved"] is False else ""))
    files = t["files"] or [None]
    out = []
    for k, f in enumerate(files):
        label = "Take %d" % n if len(files) == 1 else "Take %d.%d" % (n, k + 1)
        media = _media(project, f, sheet_dir) if f else '<div class="none">%s</div>' % _e(
            _STATUS_HELP.get(t["status"], "No output yet."))
        if t["approved"] is True:
            appr = '<span class="ok">Approved</span>'
        elif t["approved"] is False:
            appr = '<span class="bad">Rejected</span>'
        else:
            appr = '<span class="muted">Not decided</span>'
        cost = "" if t["cost"] is None else ("%s credits%s" % (t["cost"], " (estimate)" if t["cost_is_estimate"]
                                                              else ""))
        parts = [
            '<div class="%s">' % cls,
            '<div class="media">%s</div>' % media,
            '<div class="body">',
            '<div class="row"><span class="tag">%s</span><span class="muted">%s</span></div>' % (
                _e(label), _e(t["id"])),
            '<div class="row"><span>%s</span><span>%s</span></div>' % (_e(t["model_name"] or "model not set"),
                                                                      _e(cost)),
            '<div class="row"><span class="status-%s">%s</span>%s</div>' % (
                _e(t["status"]), _e((t["status"] or "").replace("_", " ")), appr),
        ]
        if t["status"] in ("failed", "nsfw", "ip_detected", "canceled"):
            parts.append('<div class="bad">%s</div>' % _e(_STATUS_HELP[t["status"]]))
        if t["approval_said"]:
            parts.append('<div class="said">"%s"</div>' % _e(t["approval_said"]))
        if t["note"]:
            parts.append('<div class="muted">Note: %s</div>' % _e(t["note"]))
        ptxt = _params_text(t["params"])
        if ptxt:
            parts.append('<div class="muted">%s</div>' % _e(ptxt))
        if t["inputs"]:
            parts.append('<div class="muted">Inputs: %s</div>' % _e(", ".join(str(i) for i in t["inputs"])))
        if t["prompt"]:
            parts.append('<details><summary>Prompt</summary><pre>%s</pre></details>' % _e(t["prompt"]))
        if f:
            parts.append('<div class="muted" style="margin-top:6px">%s</div>' % _e(f["path"]))
        parts.append("</div></div>")
        out.append("\n".join(parts))
    return "\n".join(out)


def render(data, sheet_dir, project):
    tier = data["tier"]
    t = data["totals"]
    head = [
        "<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        '<meta name="color-scheme" content="light dark">',
        "<title>%s - %s</title>" % (_e(TIER_LABEL[tier]), _e(data["name"])),
        "<style>%s</style>" % CSS, "</head>", "<body>", "<header>",
        "<h1>%s: %s</h1>" % (_e(data["name"]), _e(TIER_LABEL[tier])),
        '<div class="sub">Built %s%s</div>' % (_e(data["built"]), (" · use case: %s" % _e(data["use_case"]))
                                                if data.get("use_case") else ""),
        '<div class="totals">',
        '<span class="pill">%d shots</span>' % len([s for s in data["shots"] if s["shot"]]),
        '<span class="pill">%d takes</span>' % t["takes"],
        '<span class="pill">%s credits</span>' % t["cost"],
        '<span class="pill">%d approved</span>' % t["approved"],
        '<span class="pill">%d rejected</span>' % t["rejected"],
        '<span class="pill">%d not decided</span>' % t["undecided"],
        "</div>", "</header>", "<main>",
    ]
    body = []
    for s in data["shots"]:
        title = s["shot"] or "Not linked to a shot"
        meta = []
        if s["kind"]:
            meta.append(s["kind"])
        if s["duration_s"]:
            meta.append("%s s" % s["duration_s"])
        if s["purpose"] and s["purpose"] != s["title"]:
            meta.append(s["purpose"])
        body.append('<section class="shot" id="%s">' % _e(s["shot"] or "unlinked"))
        body.append("<h2>%s%s</h2>" % (_e(title), (" &mdash; " + _e(s["title"])) if s["title"] else ""))
        if meta:
            body.append('<div class="meta">%s</div>' % _e(" · ".join(str(m) for m in meta)))
        if not s["takes"]:
            body.append('<div class="empty">No %s yet for this shot.</div>' % _e(TIER_LABEL[tier].lower()))
        else:
            body.append('<div class="grid">')
            for n, take in enumerate(s["takes"], 1):
                body.append(_take_html(project, s["shot"], take, n, sheet_dir))
            body.append("</div>")
        body.append("</section>")
    foot = ["</main>",
            "<footer>Tell Claude which takes to approve or reject, and why. Approvals are recorded with your "
            "own words.</footer>", "</body>", "</html>"]
    return "\n".join(head + body + foot) + "\n"


def build(project, tier, stamp=None):
    data = collect(project, tier)
    sheet_dir = os.path.join(project, SHEET_DIR)
    os.makedirs(sheet_dir, exist_ok=True)
    stamp = stamp or datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    name = "%s-%s.html" % (tier, stamp)
    path = os.path.join(sheet_dir, name)
    k = 2
    while os.path.exists(path):
        path = os.path.join(sheet_dir, "%s-%s-%d.html" % (tier, stamp, k))
        k += 1
    text = render(data, sheet_dir, project)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, path)
    rel = os.path.relpath(path, project).replace(os.sep, "/")
    record_sheet(project, tier, rel, manifest.file_sha256(path), data["gen_ids"])
    return {"path": path, "rel": rel, "tier": tier, "shots": len([s for s in data["shots"] if s["shot"]]),
            "takes": data["totals"]["takes"], "totals": data["totals"], "missing": data["missing"]}


def record_sheet(project, tier, rel, sha256, gen_ids):
    """project.json "sheets": what each sheet covered. The boards/drafts evidence trusts only a sheet built here,
    unchanged since, that shows every completed take of its tier."""
    m = manifest.load(project)
    m.setdefault("sheets", []).append({"tier": tier, "path": rel, "sha256": sha256, "gen_ids": list(gen_ids),
                                       "built": jsonio.now_iso()})
    manifest.save(project, m)


def open_file(path):
    try:
        if sys.platform == "darwin" and shutil.which("open"):
            subprocess.Popen(["open", path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        if os.name == "nt":
            os.startfile(path)  # noqa: S606 (Windows only)
            return True
        for opener in ("xdg-open", "gio", "wslview"):
            if shutil.which(opener):
                cmd = [opener, "open", path] if opener == "gio" else [opener, path]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
    except OSError:
        return False
    return False


def cli_sheet_build(args):
    from . import project as _project
    proj = _project.resolve(getattr(args, "project", None), getattr(args, "session_id", None))
    res = build(proj, args.tier)
    opened = False
    if getattr(args, "open", False):
        opened = open_file(res["path"])
    res["opened"] = opened
    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        t = res["totals"]
        lines = ["Contact sheet: %s" % res["path"],
                 "%d shots, %d takes, %s credits. %d approved, %d rejected, %d not decided."
                 % (res["shots"], t["takes"], t["cost"], t["approved"], t["rejected"], t["undecided"])]
        if res["missing"]:
            lines.append("Missing files (run sc.py gen fetch): %s" % ", ".join(res["missing"]))
        if getattr(args, "open", False):
            lines.append("Opened it." if opened else "Could not open it here; open the file above in a browser.")
        print("\n".join(lines))
    return 0
