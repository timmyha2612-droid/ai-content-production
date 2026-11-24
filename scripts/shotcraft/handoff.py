"""The Higgsfield hand-off (SPEC sections 4, 9 and 10): the project's approved work, uploaded to Higgsfield, plus a
Canvas build sheet that says, shot by shot, which nodes to add, what to paste and how to connect them.

Higgsfield Canvas has no API yet (Nov 2026). Until it does, the build sheet is the hand-off, and the handoff skill
can offer a browser-assisted build. The same node plan is written as data in upload-list.json ("canvas") so a
browser helper, or a future build_canvas(), can follow it without reading markdown.

What goes on the upload list:
  - approved finals and upscales (their output files),
  - the inputs those shots use (start/end frames, references) and the bible (character, environment, prop,
    moodboard assets),
  but never an asset tagged reference-only: those are listed under "skipped" with the reason.
Uploads are remembered in project.json handoff.uploaded ({path, upload_id, at, size}); a file whose size changed
since its upload counts as not uploaded.

API:
    MEDIA_PARAMS                      param keys that carry asset ids (start_image, end_image, image_references ...)
    upload_items(project) -> {"items": [...], "skipped": [...]}
    shot_plans(project, items=None) -> [per-shot canvas plan]
    build(project) -> {"sheet", "upload_list", "items", "skipped", "shots", "uploaded", "pending", "canvas_api"}
    upload(project, dry_run=False, provider=None) -> {"uploaded": [...], "would_upload": [...], "failed": [...],
                                                     "already": n, "build": build result}
    canvas_api_available(provider=None, project=None) -> bool   true once the provider has a "canvas" command
    cli_handoff_build(args) -> int    sc.py handoff build
    cli_handoff_upload(args) -> int   sc.py handoff upload [--dry-run]
"""
import json
import os
import re

from . import ShotcraftError, jsonio, manifest, paths

SHEET = "11_handoff/canvas-build-sheet.md"
UPLOAD_LIST = "11_handoff/upload-list.json"
MEDIA_PARAMS = ("start_image", "end_image", "image_references", "video_references", "audio_references")
PORT_FOR_AS = {"start_frame": "start_image", "end_frame": "end_image", "reference": "image_references",
               "character": "image_references", "style": "image_references"}
PORT_LABEL = {"start_image": "start frame", "end_image": "end frame", "image_references": "image reference",
              "video_references": "video reference", "audio_references": "audio reference"}
BIBLE_ROLES = ("character", "environment", "prop", "moodboard")
ALLOWED = ("owned", "licensed", "generated")


# ---------------------------------------------------------------- helpers

def _model_profiles(project):
    try:
        from . import rules
        data = rules.load("models", project)
        out = {}
        for prov in (data.get("providers") or {}).values():
            out.update(prov.get("models") or {})
        return out
    except Exception:
        return {}


def _card(project, shot):
    path = os.path.join(project, "05_prompts", "%s.md" % shot)
    try:
        from . import cards
        return cards.read(path)
    except Exception:
        from . import stages
        return (stages.read_card_meta(path) or {}), ""


def _card_prompt(body):
    """The text under the card's '## Prompt' heading (without code fences), or None."""
    m = re.search(r"^## Prompt[^\n]*\n(.*?)(?=^## |\Z)", body or "", re.M | re.S)
    if not m:
        return None
    text = re.sub(r"^```[a-z]*\s*$", "", m.group(1), flags=re.M).strip()
    if not text or text.startswith("(run:"):
        return None
    return text


def _size(project, rel):
    try:
        return os.path.getsize(os.path.join(project, rel))
    except OSError:
        return None


def _uploaded_map(project, data):
    out = {}
    for u in (data.get("handoff") or {}).get("uploaded") or []:
        if not isinstance(u, dict) or not u.get("path"):
            continue
        if u.get("size") is not None and _size(project, u["path"]) not in (None, u.get("size")):
            continue  # the file changed after its upload
        out[u["path"]] = u
    return out


def _latest(gens, **want):
    hits = []
    for g in gens:
        ok = True
        for k, v in want.items():
            if isinstance(v, tuple):
                if g.get(k) not in v:
                    ok = False
            elif g.get(k) != v:
                ok = False
        if ok:
            hits.append(g)
    return hits[-1] if hits else None


def _base_gen(gens, shot):
    mine = [g for g in gens if g.get("shot") == shot and g.get("status") == "completed"]
    return (_latest(mine, tier="final", approved=True) or _latest(mine, tier="final")
            or _latest(mine, tier="draft", approved=True))


def _gen_inputs(gen, meta):
    """[(asset_id, port)] from the generation's params, else its inputs, else the card's inputs."""
    out = []
    params = (gen or {}).get("params") or {}
    for port in MEDIA_PARAMS:
        v = params.get(port)
        for aid in (v if isinstance(v, (list, tuple)) else [v] if v else []):
            if isinstance(aid, str) and re.match(r"^A\d+$", aid):
                out.append((aid, port))
    if not out:
        as_map = {}
        for i in meta.get("inputs") or []:
            if isinstance(i, dict) and i.get("asset"):
                as_map[i["asset"]] = PORT_FOR_AS.get(i.get("as"), "image_references")
        ids = [i for i in ((gen or {}).get("inputs") or []) if isinstance(i, str)] or list(as_map)
        for aid in ids:
            out.append((aid, as_map.get(aid, "image_references")))
    seen, uniq = set(), []
    for aid, port in out:
        if aid not in seen:
            seen.add(aid)
            uniq.append((aid, port))
    return uniq


def _shots(project, data):
    from . import stages
    try:
        order = list(stages.planned_shots(project))
    except Exception:
        order = []
    for g in data.get("generations", []):
        if g.get("shot") and g["shot"] not in order and g.get("approved") is True:
            order.append(g["shot"])
    return order


# ---------------------------------------------------------------- upload list

def upload_items(project):
    data = manifest.load(project)
    gens = data.get("generations", [])
    uploaded = _uploaded_map(project, data)
    items, skipped, seen = [], [], set()

    def add(path, why, kind=None, role=None, shot=None, asset=None, gen=None, rights="generated"):
        if not path or path in seen:
            return
        seen.add(path)
        if rights not in ALLOWED:
            skipped.append({"path": path, "asset": asset, "rights": rights, "shot": shot,
                            "reason": "reference-only: for looking at, never uploaded or sent to a model. If the "
                                      "user owns or licenses it, mark it first (sc.py asset mark)."})
            return
        if not os.path.isfile(os.path.join(project, path)):
            skipped.append({"path": path, "asset": asset, "rights": rights, "shot": shot,
                            "reason": "file not found in the project (run sc.py gen fetch?)"})
            return
        u = uploaded.get(path) or {}
        items.append({"path": path, "kind": kind or manifest.guess_kind(path), "role": role, "shot": shot,
                      "asset": asset, "generation": gen, "rights": rights, "why": why,
                      "upload_id": u.get("upload_id"), "uploaded_at": u.get("at")})

    # approved finals and upscales, plus the inputs they used
    for sid in _shots(project, data):
        meta, _ = _card(project, sid)
        base = _base_gen(gens, sid)
        for g in gens:
            if g.get("shot") == sid and g.get("tier") in ("final", "upscale") and g.get("approved") is True:
                for o in g.get("outputs") or []:
                    add(o, "approved %s for %s" % (g["tier"], sid), role=g["tier"] if g["tier"] == "final"
                        else "upscaled", shot=sid, gen=g.get("id"))
        for aid, port in _gen_inputs(base, meta):
            a = manifest.find_asset(data, aid)
            if a is None:
                continue
            add(a.get("path"), "%s for %s" % (PORT_LABEL.get(port, port), sid), kind=a.get("kind"),
                role=a.get("role"), shot=sid, asset=aid, rights=a.get("rights"))
    # the bible
    for a in data.get("assets", []):
        if a.get("role") in BIBLE_ROLES:
            add(a.get("path"), "bible: %s" % a["role"], kind=a.get("kind"), role=a.get("role"), shot=a.get("shot"),
                asset=a.get("id"), rights=a.get("rights"))
    return {"items": items, "skipped": skipped}


# ---------------------------------------------------------------- canvas plan

def shot_plans(project, items=None):
    data = manifest.load(project)
    gens = data.get("generations", [])
    profiles = _model_profiles(project)
    items = items if items is not None else upload_items(project)["items"]
    by_path = {i["path"]: i for i in items}
    plans = []
    for sid in _shots(project, data):
        meta, body = _card(project, sid)
        base = _base_gen(gens, sid)
        ups = [g for g in gens if g.get("shot") == sid and g.get("tier") == "upscale" and g.get("approved") is True]
        upscale = ups[-1] if ups else None
        model = (base or {}).get("model") or ((meta.get("model") or {}).get("final")
                                              if isinstance(meta.get("model"), dict) else meta.get("model"))
        prompt = (base or {}).get("prompt") or _card_prompt(body)
        settings = {}
        if base and base.get("params"):
            settings = {k: v for k, v in base["params"].items() if k not in MEDIA_PARAMS and v not in (None, "")}
        else:
            s = meta.get("settings") or {}
            for src, dst in (("aspect", "aspect_ratio"), ("resolution", "resolution"), ("duration_s", "duration"),
                             ("audio", "audio")):
                if s.get(src) is not None:
                    settings[dst] = s[src]
        nodes, edges = [], []
        for n, (aid, port) in enumerate(_gen_inputs(base, meta), 1):
            a = manifest.find_asset(data, aid) or {}
            item = by_path.get(a.get("path")) or {}
            nid = "%s-in%d" % (sid, n)
            blocked = a.get("rights") not in ALLOWED
            nodes.append({"id": nid, "type": "input", "media": a.get("kind") or "image", "asset": aid,
                          "path": a.get("path"), "upload_id": item.get("upload_id"), "port": port,
                          "blocked": blocked, "note": "reference-only: do not connect" if blocked else None})
            if not blocked:
                edges.append({"from": nid, "to": "%s-model" % sid, "port": port})
        if prompt:
            nodes.append({"id": "%s-prompt" % sid, "type": "prompt", "text": prompt})
            edges.append({"from": "%s-prompt" % sid, "to": "%s-model" % sid, "port": "prompt"})
        prof = profiles.get(model) or {}
        nodes.append({"id": "%s-model" % sid, "type": "model", "model": model,
                      "model_name": prof.get("name") or model, "settings": settings})
        outputs = []
        if base:
            for o in base.get("outputs") or []:
                outputs.append({"path": o, "generation": base.get("id"), "tier": base.get("tier"),
                                "approved": base.get("approved"), "approval_said": base.get("approval_said"),
                                "upload_id": (by_path.get(o) or {}).get("upload_id")})
        if upscale:
            up_model = upscale.get("model")
            nodes.append({"id": "%s-upscale" % sid, "type": "model", "model": up_model,
                          "model_name": (profiles.get(up_model) or {}).get("name") or up_model,
                          "settings": {k: v for k, v in (upscale.get("params") or {}).items()
                                       if k not in MEDIA_PARAMS and v not in (None, "")}})
            edges.append({"from": "%s-model" % sid, "to": "%s-upscale" % sid, "port": "input"})
            for o in upscale.get("outputs") or []:
                outputs.append({"path": o, "generation": upscale.get("id"), "tier": "upscale",
                                "approved": True, "approval_said": upscale.get("approval_said"),
                                "upload_id": (by_path.get(o) or {}).get("upload_id")})
        plans.append({"shot": sid, "title": meta.get("title") or "", "kind": meta.get("kind"),
                      "duration_s": (meta.get("settings") or {}).get("duration_s"),
                      "status": "approved" if base and base.get("approved") is True else
                      ("not approved yet" if base else "not generated yet"),
                      "nodes": nodes, "edges": edges, "outputs": outputs})
    return plans


def _settings_text(settings):
    parts = []
    for k, v in settings.items():
        if k == "audio":
            v = "on" if v else "off"
        elif k == "duration":
            v = "%s s" % v
        parts.append("%s: %s" % (k.replace("_ratio", "").replace("_", " "), v))
    return ", ".join(parts) or "defaults"


def _shot_md(plan):
    lines = ["### %s%s" % (plan["shot"], (" - " + plan["title"]) if plan["title"] else "")]
    bits = [b for b in (plan["kind"], ("%s s" % plan["duration_s"]) if plan["duration_s"] else None,
                        plan["status"]) if b]
    lines.append("_%s_" % " · ".join(bits))
    lines.append("")
    inputs = [n for n in plan["nodes"] if n["type"] == "input"]
    lines.append("**Input nodes**")
    if not inputs:
        lines.append("- none (text only)")
    for n in inputs:
        if n["blocked"]:
            lines.append("- %s (%s): reference-only, leave it off the board as an input." % (n["path"], n["asset"]))
            continue
        up = ("upload id `%s`" % n["upload_id"]) if n["upload_id"] else "not uploaded yet (sc.py handoff upload)"
        lines.append("- `%s`: %s %s, %s -> model port **%s**" % (n["id"], n["media"], n["path"], up,
                                                                 PORT_LABEL.get(n["port"], n["port"])))
    lines.append("")
    prompt = next((n for n in plan["nodes"] if n["type"] == "prompt"), None)
    lines.append("**Prompt node** `%s-prompt`" % plan["shot"])
    if prompt:
        lines += ["", "```text", prompt["text"], "```"]
    else:
        lines.append("- no compiled prompt yet (sc.py card compile)")
    lines.append("")
    lines.append("**Model node**")
    for n in plan["nodes"]:
        if n["type"] == "model":
            lines.append("- `%s`: %s (`%s`). Settings: %s" % (n["id"], n["model_name"] or "model not set",
                                                             n["model"] or "-", _settings_text(n["settings"])))
    lines.append("")
    lines.append("**Edges**")
    for e in plan["edges"]:
        lines.append("- `%s` -> `%s` (%s)" % (e["from"], e["to"], PORT_LABEL.get(e["port"], e["port"])))
    if not plan["edges"]:
        lines.append("- none")
    lines.append("")
    lines.append("**Final output**")
    if not plan["outputs"]:
        lines.append("- nothing approved yet")
    for o in plan["outputs"]:
        said = (' - approved: "%s"' % o["approval_said"]) if o.get("approval_said") else ""
        up = (", upload id `%s`" % o["upload_id"]) if o.get("upload_id") else ""
        lines.append("- %s (%s)%s%s" % (o["path"], o["tier"], up, said))
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------- build

def canvas_api_available(provider=None, project=None):
    try:
        if provider is None:
            from .providers import get_provider
            provider = get_provider(None, project)
        return bool(provider.has_command("canvas"))
    except Exception:
        return False


def _template():
    p = os.path.join(paths.plugin_root(), "templates", "canvas-build-sheet.md")
    try:
        with open(p, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ("# Canvas build sheet: {{project_name}}\n\nBuilt {{built}}. Use case: {{use_case}}. Delivery: "
                "{{delivery}}.\n\n{{canvas_api_note}}\n\n## Uploads\n\n{{upload_summary}}\n\n{{upload_table}}\n\n"
                "{{skipped}}\n\n## Shots\n\n{{shots}}\n")


def _delivery_text(d):
    d = d or {}
    bits = [str(d[k]) for k in ("aspect", "resolution") if d.get(k)]
    if d.get("fps"):
        bits.append("%s fps" % d["fps"])
    if d.get("duration_s"):
        bits.append("%s s" % d["duration_s"])
    return ", ".join(bits) or "not set"


def build(project, check_canvas=False):
    data = manifest.load(project)
    ul = upload_items(project)
    items, skipped = ul["items"], ul["skipped"]
    plans = shot_plans(project, items)
    api = canvas_api_available(project=project) if check_canvas else False
    done = [i for i in items if i["upload_id"]]
    pending = [i for i in items if not i["upload_id"]]
    rows = ["| File | What | Shot | Upload id |", "|---|---|---|---|"]
    for i in items:
        rows.append("| %s | %s | %s | %s |" % (i["path"], i["why"], i["shot"] or "-",
                                               ("`%s`" % i["upload_id"]) if i["upload_id"] else "not yet"))
    skipped_md = ""
    if skipped:
        skipped_md = "Left out:\n\n" + "\n".join("- %s: %s" % (s["path"], s["reason"]) for s in skipped)
    note = ("Higgsfield now shows a Canvas command in its CLI. shotcraft cannot build the board through it yet; "
            "tell Claude so the hand-off can be updated." if api else
            "Higgsfield Canvas has no API yet, so the board is built by hand (or with browser help) from this "
            "sheet.")
    values = {
        "project_name": data.get("name") or os.path.basename(project),
        "built": jsonio.now_iso(),
        "use_case": data.get("use_case") or "not set",
        "delivery": _delivery_text(data.get("delivery")),
        "canvas_api_note": note,
        "upload_summary": "%d file(s) to hand off: %d uploaded, %d not uploaded yet%s." % (
            len(items), len(done), len(pending), (" (run: sc.py handoff upload)" if pending else "")),
        "upload_table": "\n".join(rows) if items else "Nothing to upload yet (no approved finals or bible files).",
        "skipped": skipped_md,
        "shots": "\n".join(_shot_md(p) for p in plans) if plans else "No shots yet.",
    }
    text = _template()
    for k, v in values.items():
        text = text.replace("{{%s}}" % k, v)
    text = re.sub(r"\n{3,}", "\n\n", text)
    sheet_abs = os.path.join(project, SHEET)
    os.makedirs(os.path.dirname(sheet_abs), exist_ok=True)
    tmp = sheet_abs + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write(text)
    os.replace(tmp, sheet_abs)
    jsonio.write_json(os.path.join(project, UPLOAD_LIST), {
        "schema": 1, "built": values["built"], "project": data.get("name"), "provider": data.get("provider"),
        "items": items, "skipped": skipped, "canvas": {"api": api, "shots": plans}})
    data = manifest.load(project)
    h = data.setdefault("handoff", {})
    h.setdefault("uploaded", [])
    if h.get("canvas_sheet") != SHEET or h.get("upload_list") != UPLOAD_LIST:
        h["canvas_sheet"] = SHEET
        h["upload_list"] = UPLOAD_LIST
        manifest.save(project, data)
    return {"sheet": SHEET, "upload_list": UPLOAD_LIST, "items": len(items), "skipped": len(skipped),
            "shots": len(plans), "uploaded": len(done), "pending": len(pending), "canvas_api": api}


def upload(project, dry_run=False, provider=None):
    from . import refs
    ul = upload_items(project)
    todo = [i for i in ul["items"] if not i["upload_id"]]
    already = len(ul["items"]) - len(todo)
    # re-check rights at the moment of upload
    ids = [i["asset"] for i in todo if i.get("asset")]
    rc = refs.rights_check(project, ids)
    blocked = set(b["id"] for b in rc["blocked"]) | set(rc["missing"])
    todo = [i for i in todo if not (i.get("asset") in blocked)]
    if dry_run:
        return {"dry_run": True, "would_upload": [i["path"] for i in todo], "already": already,
                "skipped": ul["skipped"], "uploaded": [], "failed": []}
    if provider is None:
        from .providers import get_provider
        provider = get_provider(None, project)
    if todo and not provider.available():
        raise ShotcraftError("The %s CLI is not installed, so nothing can be uploaded." % provider.name)
    done, failed = [], []
    for i in todo:
        full = os.path.join(project, i["path"])
        try:
            uid = provider.upload(full)
        except ShotcraftError as exc:
            failed.append({"path": i["path"], "error": str(exc)})
            continue
        rec = {"path": i["path"], "upload_id": uid, "at": jsonio.now_iso(), "size": _size(project, i["path"]),
               "provider": getattr(provider, "name", None)}
        data = manifest.load(project)
        h = data.setdefault("handoff", {})
        lst = [u for u in h.get("uploaded") or [] if not (isinstance(u, dict) and u.get("path") == i["path"])]
        lst.append(rec)
        h["uploaded"] = lst
        manifest.save(project, data)
        done.append(rec)
    res = build(project)
    return {"dry_run": False, "uploaded": done, "failed": failed, "already": already, "would_upload": [],
            "skipped": ul["skipped"], "build": res}


# ---------------------------------------------------------------- CLI

def _proj(args):
    from . import project as _project
    return _project.resolve(getattr(args, "project", None), getattr(args, "session_id", None))


def cli_handoff_build(args):
    proj = _proj(args)
    res = build(proj, check_canvas=True)
    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print("Canvas build sheet: %s (%d shots). Upload list: %s (%d files: %d uploaded, %d not yet; %d left out)."
              % (res["sheet"], res["shots"], res["upload_list"], res["items"], res["uploaded"], res["pending"],
                 res["skipped"]))
    return 0


def cli_handoff_upload(args):
    proj = _proj(args)
    res = upload(proj, dry_run=getattr(args, "dry_run", False))
    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
    elif res["dry_run"]:
        lines = ["Would upload %d file(s) (%d already uploaded):" % (len(res["would_upload"]), res["already"])]
        lines += ["  " + p for p in res["would_upload"]]
        lines += ["  left out: %s (%s)" % (s["path"], s["reason"]) for s in res["skipped"]]
        print("\n".join(lines))
    else:
        lines = ["Uploaded %d file(s); %d were already uploaded." % (len(res["uploaded"]), res["already"])]
        lines += ["  failed: %s (%s)" % (f["path"], f["error"]) for f in res["failed"]]
        lines.append("The build sheet now shows the upload ids: %s" % res["build"]["sheet"])
        print("\n".join(lines))
    return 1 if res.get("failed") else 0
