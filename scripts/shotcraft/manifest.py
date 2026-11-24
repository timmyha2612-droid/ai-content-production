"""project.json (schema 1, SPEC §3): the project's manifest. Only sc.py writes it (the guard blocks Edit/Write).

Every function takes the project folder (absolute path) and does load -> change -> atomic save.

API:
    SCHEMA, RIGHTS, ROLES, KINDS, TIERS, GEN_STATUSES
    new_manifest(name, slug, track, use_case=None, delivery=None, budget=None, stages_included=None,
                 provider="higgsfield") -> dict
    load(project) -> dict                         raises ShotcraftError when there is no project.json
    save(project, data)                           atomic write
    guess_kind(path) -> "image|video|audio|3d|doc"
    add_asset(project, path, rights, role, kind=None, source_url=None, note=None, shot=None) -> asset dict
                                                  id A001, A002 ...; path stored relative to the project
    find_asset(project_or_manifest, asset_id) -> dict|None
    list_assets(project, role=None, shot=None, rights=None) -> list
    mark_asset(project, asset_id, rights, user_said) -> asset (also records a decision)
    add_generation(project, **fields) -> gen dict  id G0001 ...; defaults fill the schema
    update_generation(project, gen_id, **fields) -> gen dict
    find_generation(project_or_manifest, gen_id) -> dict|None
    list_generations(project, shot=None, tier=None, status=None) -> list
    add_decision(project, stage, text, user_said=None) -> decision dict
    set_card_approval(project, shot, card_hash, user_said, card_rel) -> record   (data["card_approvals"][shot])
    card_approval(project_or_manifest, shot) -> record|None
    file_sha256(path) -> hex digest
"""
import hashlib
import os

from . import Refused, ShotcraftError, jsonio, paths

SCHEMA = 1
RIGHTS = ("reference-only", "owned", "licensed", "generated")
ROLES = ("reference", "character", "environment", "prop", "moodboard", "input", "board", "draft", "final",
         "upscaled")
KINDS = ("image", "video", "audio", "3d", "doc")
TIERS = ("board", "draft", "final", "upscale")
GEN_STATUSES = ("estimated", "submitted", "queued", "in_progress", "completed", "failed", "nsfw", "canceled",
                "ip_detected")

_EXT_KIND = {
    "image": {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tif", ".tiff", ".heic", ".svg", ".avif", ".exr"},
    "video": {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi", ".mxf", ".gifv"},
    "audio": {".wav", ".mp3", ".m4a", ".aac", ".flac", ".ogg", ".aif", ".aiff"},
    "3d": {".glb", ".gltf", ".obj", ".fbx", ".usd", ".usdz", ".blend", ".stl", ".ply"},
}


def new_manifest(name, slug, track, use_case=None, delivery=None, budget=None, stages_included=None,
                 provider="higgsfield"):
    return {
        "schema": SCHEMA,
        "name": name,
        "slug": slug,
        "created": jsonio.now_iso(),
        "track": track,
        "provider": provider,
        "use_case": use_case,
        "delivery": delivery or {},
        "budget": budget or {"credits": None, "threshold_single_job": 50, "spent": 0, "reserved": 0},
        "stages_included": list(stages_included or []),
        "assets": [],
        "generations": [],
        "decisions": [],
        "handoff": {"uploaded": [], "canvas_sheet": "11_handoff/canvas-build-sheet.md"},
    }


def load(project):
    data = jsonio.read_json(paths.manifest_file(project))
    if not isinstance(data, dict):
        raise ShotcraftError("No project.json in %s. Is this a shotcraft project?" % project)
    for key, default in (("assets", []), ("generations", []), ("decisions", [])):
        data.setdefault(key, default)
    return data


def save(project, data):
    jsonio.write_json(paths.manifest_file(project), data)


def _m(project_or_manifest):
    if isinstance(project_or_manifest, dict):
        return project_or_manifest
    return load(project_or_manifest)


def guess_kind(path):
    ext = os.path.splitext(str(path))[1].lower()
    for kind, exts in _EXT_KIND.items():
        if ext in exts:
            return kind
    return "doc"


def _next_id(items, prefix, width):
    best = 0
    for it in items:
        ident = str(it.get("id", ""))
        if ident.startswith(prefix) and ident[len(prefix):].isdigit():
            best = max(best, int(ident[len(prefix):]))
    return "%s%0*d" % (prefix, width, best + 1)


def add_asset(project, path, rights, role, kind=None, source_url=None, note=None, shot=None):
    if rights not in RIGHTS:
        raise Refused("Rights must be one of: %s." % ", ".join(RIGHTS))
    if role not in ROLES:
        raise Refused("Role must be one of: %s." % ", ".join(ROLES))
    if kind is not None and kind not in KINDS:
        raise Refused("Kind must be one of: %s." % ", ".join(KINDS))
    rel = paths.rel_to(project, path)
    if rel is None:
        raise Refused("The file %s is outside the project. Copy it into the project first (owned inputs go in "
                      "00_inputs/)." % path)
    data = load(project)
    asset = {
        "id": _next_id(data["assets"], "A", 3),
        "path": rel,
        "kind": kind or guess_kind(rel),
        "rights": rights,
        "source_url": source_url,
        "note": note,
        "role": role,
        "shot": shot,
        "added": jsonio.now_iso(),
    }
    data["assets"].append(asset)
    save(project, data)
    return asset


def find_asset(project_or_manifest, asset_id):
    for a in _m(project_or_manifest).get("assets", []):
        if a.get("id") == asset_id:
            return a
    return None


def list_assets(project, role=None, shot=None, rights=None):
    out = []
    for a in load(project).get("assets", []):
        if role and a.get("role") != role:
            continue
        if shot and a.get("shot") != shot:
            continue
        if rights and a.get("rights") != rights:
            continue
        out.append(a)
    return out


def mark_asset(project, asset_id, rights, user_said):
    if rights not in RIGHTS:
        raise Refused("Rights must be one of: %s." % ", ".join(RIGHTS))
    if not (user_said or "").strip():
        raise Refused("Changing an asset's rights needs the user's own words (--user-said).")
    data = load(project)
    asset = find_asset(data, asset_id)
    if asset is None:
        raise ShotcraftError("No asset %s in this project." % asset_id)
    old = asset.get("rights")
    asset["rights"] = rights
    asset.setdefault("rights_history", []).append(
        {"at": jsonio.now_iso(), "from": old, "to": rights, "user_said": user_said})
    data["decisions"].append({"at": jsonio.now_iso(), "stage": None,
                              "text": "Asset %s rights %s -> %s" % (asset_id, old, rights),
                              "user_said": user_said})
    save(project, data)
    return asset


def add_generation(project, **fields):
    data = load(project)
    gen = {
        "id": _next_id(data["generations"], "G", 4),
        "shot": None, "card": None, "tier": None, "provider": data.get("provider", "higgsfield"),
        "model": None, "params": {}, "prompt": None, "inputs": [], "cost_estimate": None,
        "cost_actual": None, "job_id": None, "status": "estimated", "outputs": [], "approved": None,
        "approval_said": None, "created": jsonio.now_iso(),
    }
    fields.pop("id", None)
    gen.update(fields)
    if gen.get("tier") is not None and gen["tier"] not in TIERS:
        raise Refused("Tier must be one of: %s." % ", ".join(TIERS))
    data["generations"].append(gen)
    save(project, data)
    return gen


def update_generation(project, gen_id, **fields):
    data = load(project)
    gen = find_generation(data, gen_id)
    if gen is None:
        raise ShotcraftError("No generation %s in this project." % gen_id)
    fields.pop("id", None)
    gen.update(fields)
    gen["updated"] = jsonio.now_iso()
    save(project, data)
    return gen


def find_generation(project_or_manifest, gen_id):
    for g in _m(project_or_manifest).get("generations", []):
        if g.get("id") == gen_id:
            return g
    return None


def list_generations(project, shot=None, tier=None, status=None):
    out = []
    for g in _m(project).get("generations", []):
        if shot and g.get("shot") != shot:
            continue
        if tier and g.get("tier") != tier:
            continue
        if status and g.get("status") != status:
            continue
        out.append(g)
    return out


def add_decision(project, stage, text, user_said=None):
    data = load(project)
    dec = {"at": jsonio.now_iso(), "stage": stage, "text": text, "user_said": user_said}
    data["decisions"].append(dec)
    save(project, data)
    return dec


def set_card_approval(project, shot, card_hash, user_said, card_rel=None):
    """The user approved this exact card (front matter hash). gen checks the hash before it spends."""
    data = load(project)
    rec = {"hash": card_hash, "user_said": user_said, "card": card_rel, "at": jsonio.now_iso()}
    data.setdefault("card_approvals", {})[shot] = rec
    data["decisions"].append({"at": rec["at"], "stage": None, "text": "Card %s approved" % shot,
                              "user_said": user_said})
    save(project, data)
    return rec


def card_approval(project_or_manifest, shot):
    return (_m(project_or_manifest).get("card_approvals") or {}).get(shot)


def file_sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()
