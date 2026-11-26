"""The storyboard: a local web app over a project's script, cards and references (SPEC section 12).

The board is a view. Its text lives in <project>/board/board.json (written by Claude from the script, the shot
list and the bible); the Higgsfield side of each shot is read live from its prompt card in 05_prompts/; every
reference the user adds on the board is a normal project asset in project.json, filed in 00_inputs/board/.

Rights first: a reference added on the board starts as reference-only and is never sent to a model. Only
owned, licensed or generated assets become card inputs, and only through `sc.py card set-input` with the user's
words. The board proposes those commands (`sc.py board inputs`); it never runs them.

API:
    board_file(project) -> path
    load_board(project) -> dict              raises ShotcraftError when the file is missing or not JSON
    validate(data) -> [error strings]
    input_role(attr) -> "start_frame|character|reference|style" | None   the card input an attribute feeds
    asset_role(attr) -> manifest role                                    the project.json role it is filed as
    refs(project) -> [asset dicts with a "board" key]
    add_ref(project, data_bytes, filename, shot, attr) -> asset
    set_rights(project, asset_id, rights) -> asset
    set_label(project, asset_id, label) -> asset   a short name a prompt can mention as @Label
    resolve_mentions(project, card_id, prompt, model_id) -> {"prompt", "slots", "warnings"}
    remove_ref(project, asset_id)            refuses when a card or a generation uses the asset
    shot_hf(project, card_id) -> dict|None   models per tier, length, compiled prompt (dry run, no writes)
    inputs_plan(project, data=None) -> [{"shot", "card", "asset", "as", "attr", "command"}]
    takes(project) -> {shot id: [generation summaries, newest first]}
    view(project) -> dict                    everything the app shows: board, hf per shot, refs, plan, progress, takes
    cli_board_check / cli_board_inputs / cli_board_serve / cli_board_init

Stdlib only.
"""
import json
import os
import re
import uuid

from . import Refused, ShotcraftError, jsonio, manifest, paths

BOARD_DIR = "board"
REFS_DIR = "00_inputs/board"
SENDABLE = ("owned", "licensed", "generated")
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}
MAX_BYTES = 20 * 1024 * 1024
LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,23}$")
MENTION_RE = re.compile(r"@([A-Za-z][A-Za-z0-9_-]{0,23})")
# How a model's prompt points at its image references, by model id prefix. Seedance on Higgsfield numbers
# reference images in upload order (@Image1, @Image2 ...). A model with no entry gets the label as plain
# words; its references are still attached, in the same order.
MENTION_STYLE = {"seedance": "@Image{n}"}
# Reference slots are filled in this order: who, then what, then how it looks.
_SLOT_ORDER = {"character": 0, "reference": 1, "style": 2}

# Board attribute -> card input role ("as" in sc.py card set-input). None: never sent, a note for the edit.
_INPUT = {
    "frame": "start_frame",
    "character": "character",
    "wardrobe": "reference", "props": "reference", "environment": "reference",
    "lighting": "style", "mood": "style", "camera": "style",
    "palette": "style", "visual worlds": "style", "light and texture": "style", "moodboard": "style",
}
# Board attribute -> project.json asset role.
_ROLE = {
    "frame": "board", "character": "character", "wardrobe": "prop", "props": "prop",
    "environment": "environment",
}

BOARD_TEMPLATE = {
    "title": "A neighbourhood bakery at dawn",
    "summary": "15 second vertical reel. Sample board: replace every value with the project's own.",
    "facts": [{"value": "15 s", "label": "Length"}, {"value": "9:16", "label": "Vertical social"}],
    "worlds": [{"id": "dawn", "label": "Dawn", "color": "#e9d7b8"}],
    "look": [
        {"attr": "Visual worlds", "text": "One world: a small bakery before opening, warm and quiet."},
        {"attr": "Palette", "text": "Flour white #F4EFE6, crust brown #8A5A2B, window blue #3A6EA5."},
        {"attr": "Light and texture", "text": "One window as the key light. Natural grain, real flour dust."},
        {"attr": "Keep out", "text": "No logos, no readable text in generated frames."},
        {"attr": "Moodboard", "text": "General references for the whole film."},
    ],
    "shots": [
        {"n": 1, "card": "S010", "time": "0.0-3.0", "dur": 3.0, "world": "dawn", "name": "First light",
         "size": "MS", "picture": "A baker dusts flour off her hands as the oven light comes on.",
         "vo": "", "text": "Open at 6", "sound": "Oven hum.",
         "layers": {"Character": "A baker in her 40s.", "Wardrobe": "Linen apron.",
                    "Environment": "Small bakery counter.", "Camera": "MS, eye level, locked-off.",
                    "Lighting": "Cool window key from frame left.", "Mood": "Calm."}},
    ],
    "notes": [{"title": "Before generating", "items": ["Make each shot as a still first."]}],
}


def _key(attr):
    return re.sub(r"\s+", " ", str(attr or "")).strip().lower()


def input_role(attr):
    return _INPUT.get(_key(attr))


def asset_role(attr):
    k = _key(attr)
    if k in _ROLE:
        return _ROLE[k]
    return "moodboard" if k in _INPUT else "reference"


def board_file(project):
    return os.path.join(project, BOARD_DIR, "board.json")


def load_board(project):
    path = board_file(project)
    if not os.path.isfile(path):
        raise ShotcraftError("No board yet: %s is missing. Write it from the script and shot list, or start from "
                             "the sample with: sc.py board init" % path)
    try:
        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)
    except ValueError as exc:
        raise ShotcraftError("%s is not valid JSON: %s" % (path, exc))
    return data


def validate(data):
    errs = []
    if not isinstance(data, dict):
        return ["The board must be a JSON object."]
    if not str(data.get("title") or "").strip():
        errs.append("title is missing.")
    worlds = {w.get("id") for w in data.get("worlds") or [] if isinstance(w, dict)}
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        errs.append("shots must be a non-empty list.")
        shots = []
    seen = set()
    for i, s in enumerate(shots):
        where = "shots[%d]" % i
        if not isinstance(s, dict):
            errs.append(where + " must be an object.")
            continue
        n = s.get("n")
        if not isinstance(n, int) or n < 1:
            errs.append(where + ".n must be a whole number from 1.")
        elif n in seen:
            errs.append("shot %d appears twice." % n)
        seen.add(n)
        for f in ("name", "picture", "time"):
            if not str(s.get(f) or "").strip():
                errs.append("%s.%s is missing." % (where, f))
        if not isinstance(s.get("dur"), (int, float)) or s.get("dur") <= 0:
            errs.append(where + ".dur must be the cut length in seconds.")
        if s.get("world") and worlds and s.get("world") not in worlds and s.get("world") != "mix":
            errs.append("%s.world %r is not in worlds." % (where, s.get("world")))
        card = s.get("card")
        if card is not None and not re.match(r"^S\d{3}[A-Z]?$", str(card)):
            errs.append("%s.card %r should be a shot id like S010 (or null for an edit-only shot)." % (where, card))
        if s.get("layers") is not None and not isinstance(s.get("layers"), dict):
            errs.append(where + ".layers must be an object of attribute: text.")
    for i, row in enumerate(data.get("look") or []):
        if not isinstance(row, dict) or not row.get("attr"):
            errs.append("look[%d] needs attr and text." % i)
    return errs


def refs(project):
    return [a for a in manifest.load(project).get("assets", []) if isinstance(a.get("board"), dict)]


def _shot_card(project, shot):
    if not shot:
        return None
    try:
        for s in load_board(project).get("shots") or []:
            if s.get("n") == shot:
                return s.get("card")
    except ShotcraftError:
        pass
    return None


def add_ref(project, data, filename, shot, attr):
    """File an uploaded image under 00_inputs/board/ and record it in project.json as reference-only
    (a frame still as generated: it came out of a generation)."""
    attr = re.sub(r"\s+", " ", str(attr or "")).strip()
    if not attr or len(attr) > 60:
        raise Refused("Say which attribute the reference is for.")
    try:
        shot = int(shot)
    except (TypeError, ValueError):
        raise Refused("The shot must be a number (0 for the look book).")
    if shot < 0:
        raise Refused("The shot must be 0 or more.")
    ext = os.path.splitext(str(filename or ""))[1].lower()
    if ext not in IMAGE_EXT:
        raise Refused("Only images can be added to the board (%s)." % ", ".join(sorted(IMAGE_EXT)))
    if not data:
        raise Refused("The file is empty.")
    if len(data) > MAX_BYTES:
        raise Refused("The file is over 20 MB.")
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", os.path.splitext(os.path.basename(str(filename)))[0]).strip("-.")[:40]
    folder = os.path.join(project, REFS_DIR)
    os.makedirs(folder, exist_ok=True)
    dest = os.path.join(folder, "%s-%s%s" % (uuid.uuid4().hex[:8], base or "image", ext))
    with open(dest, "wb") as fh:
        fh.write(data)
    rights = "generated" if _key(attr) == "frame" else "reference-only"
    asset = manifest.add_asset(project, dest, rights, asset_role(attr), kind="image",
                               note="Added on the storyboard (%s)" % attr, shot=_shot_card(project, shot))
    m = manifest.load(project)
    a = manifest.find_asset(m, asset["id"])
    a["board"] = {"shot": shot, "attr": attr, "name": str(filename or "")[:120],
                  "label": _free_label(m, re.sub(r"[^A-Za-z0-9]", "", attr.title()) or "Ref")}
    manifest.save(project, m)
    return a


def _labels(m, skip=None):
    return {str((a.get("board") or {}).get("label", "")).lower() for a in m.get("assets", [])
            if isinstance(a.get("board"), dict) and a.get("id") != skip}


def _free_label(m, base, skip=None):
    base = (base if LABEL_RE.match(base or "") else "Ref")[:20]
    taken = _labels(m, skip)
    n = 1
    while (base + str(n)).lower() in taken:
        n += 1
    return base + str(n)


def set_label(project, asset_id, label):
    label = str(label or "").strip().lstrip("@")
    if not LABEL_RE.match(label):
        raise Refused("A label is 1 to 24 letters, digits, - or _, starting with a letter (like Editor or "
                      "ClayDino).")
    m = manifest.load(project)
    a = manifest.find_asset(m, asset_id)
    if a is None or not isinstance(a.get("board"), dict):
        raise ShotcraftError("No board reference %s." % asset_id)
    if label.lower() in _labels(m, skip=asset_id):
        raise Refused("@%s is already used by another reference." % label)
    a["board"]["label"] = label
    manifest.save(project, m)
    return a


def set_rights(project, asset_id, rights):
    a = manifest.find_asset(project, asset_id)
    if a is None or not isinstance(a.get("board"), dict):
        raise ShotcraftError("No board reference %s." % asset_id)
    return manifest.mark_asset(project, asset_id, rights,
                               user_said="(storyboard) set to %s by the user on the board" % rights)


def _uses(project, asset_id):
    used = []
    pdir = os.path.join(project, "05_prompts")
    if os.path.isdir(pdir):
        from . import cards
        for name in sorted(os.listdir(pdir)):
            if not name.endswith(".md"):
                continue
            try:
                meta, _ = cards.read(os.path.join(pdir, name))
            except Exception:
                continue
            if any(isinstance(i, dict) and i.get("asset") == asset_id for i in meta.get("inputs") or []):
                used.append("card " + name[:-3])
    for g in manifest.load(project).get("generations", []):
        if asset_id in json.dumps(g.get("inputs") or g.get("params") or {}):
            used.append("generation " + str(g.get("id")))
    return used


def remove_ref(project, asset_id):
    m = manifest.load(project)
    a = manifest.find_asset(m, asset_id)
    if a is None or not isinstance(a.get("board"), dict):
        raise ShotcraftError("No board reference %s." % asset_id)
    used = _uses(project, asset_id)
    if used:
        raise Refused("%s is in use (%s). Take it off the card first." % (asset_id, ", ".join(used)))
    m["assets"] = [x for x in m["assets"] if x.get("id") != asset_id]
    manifest.save(project, m)
    full = os.path.join(project, a.get("path") or "")
    if paths.rel_to(project, full) and str(a.get("path", "")).startswith(REFS_DIR + "/") and os.path.isfile(full):
        os.remove(full)


def shot_hf(project, card_id):
    """The Higgsfield side of one shot, read from its card. Never writes the card."""
    if not card_id:
        return None
    path = os.path.join(project, "05_prompts", "%s.md" % card_id)
    if not os.path.isfile(path):
        return {"card": card_id, "missing": True}
    from . import cards, compiler, rules
    try:
        meta, _ = cards.read(path)
    except Exception as exc:
        return {"card": card_id, "error": "Card can't be read: %s" % exc}
    out = {"card": card_id, "models": {}, "settings": meta.get("settings") or {},
           "inputs": meta.get("inputs") or [], "status": meta.get("status")}
    for tier, mid in (meta.get("model") or {}).items():
        if mid:
            prof, _why = rules.model_profile(mid, "higgsfield", project)
            out["models"][tier] = {"id": mid, "name": (prof or {}).get("name") or mid}
    final = (meta.get("model") or {}).get("final") or (meta.get("model") or {}).get("draft")
    errors = cards.validate(meta)
    if errors:
        out["errors"] = errors
        return out
    if final:
        prof, why = rules.model_profile(final, "higgsfield", project)
        if prof is None:
            out["errors"] = [why]
            return out
        res = compiler.compile(meta, prof, rules.compiler_rules(project))
        out.update(prompt=res["prompt"], words=res["word_count"], max_words=res["max_prompt_words"],
                   params=res["params"], dropped=[d["field"] for d in res["dropped_fields"]],
                   motion_only=res["motion_only"], warnings=res["warnings"])
        r = resolve_mentions(project, card_id, res["prompt"], final)
        out.update(prompt_ready=r["prompt"], slots=r["slots"], mention_warnings=r["warnings"])
    return out


def inputs_plan(project, data=None):
    """Card inputs the board's sendable references call for. Proposals only: the producer runs them with the
    user's words while the boards, drafts or finals stage is open."""
    data = data or load_board(project)
    cards_by_shot = {s.get("n"): s.get("card") for s in data.get("shots") or [] if s.get("card")}
    plan = []
    for a in refs(project):
        if a.get("rights") not in SENDABLE:
            continue
        b = a["board"]
        role = input_role(b.get("attr"))
        if not role:
            continue
        targets = list(cards_by_shot.items()) if b.get("shot") == 0 else [(b.get("shot"), cards_by_shot.get(b.get("shot")))]
        for n, card in targets:
            if not card or (role == "start_frame" and b.get("shot") == 0):
                continue
            plan.append({"shot": n, "card": card, "asset": a["id"], "as": role, "attr": b.get("attr"),
                         "label": b.get("label"),
                         "command": "sc.py card set-input 05_prompts/%s.md --asset %s --as %s --user-said \"<their words>\""
                                    % (card, a["id"], role)})
    return plan


def resolve_mentions(project, card_id, prompt, model_id, plan=None):
    """Turn @Label mentions into the model's own reference pointers.

    The card's sendable board references (character, then reference, then style) fill the model's image
    slots in order; the prompt's @Label becomes that slot's pointer (@Image2 on Seedance) or, for a model
    with no pointer syntax, the label as plain words. Mentions of a reference that isn't sent are flagged."""
    plan = inputs_plan(project) if plan is None else plan
    mine = sorted([p for p in plan if p["card"] == card_id and p["as"] in _SLOT_ORDER],
                  key=lambda p: (_SLOT_ORDER[p["as"]], p["asset"]))
    style = next((v for k, v in MENTION_STYLE.items() if str(model_id or "").startswith(k)), None)
    slots, by_label = [], {}
    for i, p in enumerate(mine, 1):
        ptr = style.format(n=i) if style else None
        slots.append({"n": i, "pointer": ptr, "label": p.get("label"), "asset": p["asset"], "as": p["as"]})
        if p.get("label"):
            by_label[str(p["label"]).lower()] = slots[-1]
    known = {str((a.get("board") or {}).get("label", "")).lower(): a for a in refs(project)}
    warnings, used = [], set()

    def sub(mt):
        lab = mt.group(1)
        slot = by_label.get(lab.lower())
        if slot:
            used.add(slot["asset"])
            return slot["pointer"] or lab
        a = known.get(lab.lower())
        if a is None:
            warnings.append("No reference is called @%s." % lab)
        elif a.get("rights") not in SENDABLE:
            warnings.append("@%s is reference-only, so it isn't sent; the model only reads the word." % lab)
        else:
            warnings.append("@%s isn't an input of this shot." % lab)
        return lab

    out = MENTION_RE.sub(sub, prompt or "")
    for sl in slots:
        if sl["asset"] not in used:
            warnings.append("@%s is sent but the prompt never mentions it, so the model uses it loosely."
                            % (sl["label"] or sl["asset"]))
    if slots and not style:
        warnings.append("No @ pointer syntax on record for %s: references are attached in the order listed." % model_id)
    return {"prompt": out, "slots": slots, "warnings": warnings}


def takes(project):
    out = {}
    for g in manifest.load(project).get("generations", []):
        if not g.get("shot") or g.get("status") == "estimated" and not g.get("job_id"):
            continue
        files = []
        for i, o in enumerate(g.get("outputs") or []):
            kind = manifest.guess_kind(o)
            if kind in ("image", "video"):
                files.append({"url": "/gen/%s/%d" % (g["id"], i), "kind": kind})
        out.setdefault(g["shot"], []).append({
            "id": g["id"], "tier": g.get("tier"), "status": g.get("status"), "approved": g.get("approved"),
            "said": g.get("approval_said"), "model": g.get("model"), "variant": g.get("variant"),
            "error": g.get("error"), "files": files, "at": g.get("updated") or g.get("created")})
    for v in out.values():
        v.sort(key=lambda t: t["id"], reverse=True)
    return out


def view(project):
    from . import shots as _shots
    data = load_board(project)
    errs = validate(data)
    hf = {}
    for s in data.get("shots") or []:
        if isinstance(s, dict) and s.get("card"):
            hf[str(s.get("n"))] = shot_hf(project, s["card"])
    out_refs = []
    for a in refs(project):
        b = a["board"]
        role = input_role(b.get("attr"))
        out_refs.append({"id": a["id"], "shot": b.get("shot"), "attr": b.get("attr"), "name": b.get("name"),
                         "label": b.get("label"),
                         "rights": a.get("rights"), "input": role,
                         "send": bool(role) and a.get("rights") in SENDABLE, "url": "/files/" + a["id"]})
    try:
        prog = _shots.progress(project)
    except ShotcraftError:
        prog = {}
    return {"board": data, "errors": errs, "hf": hf, "refs": out_refs,
            "plan": inputs_plan(project, data) if not errs else [], "progress": prog, "takes": takes(project)}


# ---------------------------------------------------------------- CLI

def _project(args):
    from . import project as _p
    return _p.resolve(getattr(args, "project", None), getattr(args, "session_id", None))


def _print(args, obj, text):
    if getattr(args, "json", False):
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    else:
        print(text)


def cli_board_init(args):
    project = _project(args)
    path = board_file(project)
    if os.path.exists(path) and not getattr(args, "force", False):
        raise Refused("%s already exists. Add --force to replace it with the sample." % path)
    jsonio.write_json(path, BOARD_TEMPLATE)
    _print(args, {"ok": True, "path": path}, "Sample board written to %s. Replace its text with the project's "
                                             "script, shot list and look book." % path)
    return 0


def cli_board_check(args):
    project = _project(args)
    v = view(project)
    lines = []
    if v["errors"]:
        lines += ["Board problems:"] + ["- " + e for e in v["errors"]]
    for n, h in sorted(v["hf"].items(), key=lambda kv: int(kv[0])):
        if not h:
            continue
        if h.get("missing"):
            lines.append("Shot %s: card %s not written yet." % (n, h["card"]))
        elif h.get("errors"):
            lines.append("Shot %s (%s): %s" % (n, h["card"], "; ".join(h["errors"])))
        else:
            models = ", ".join("%s %s" % (t, m["name"]) for t, m in h["models"].items())
            lines.append("Shot %s (%s): %s. Prompt %s of %s words%s." % (
                n, h["card"], models or "no models yet", h.get("words", "-"), h.get("max_words", "-"),
                ("; left out: " + ", ".join(h["dropped"])) if h.get("dropped") else ""))
    lines.append("%d reference(s) on the board, %d set to go to Higgsfield." % (
        len(v["refs"]), sum(1 for r in v["refs"] if r["send"])))
    _print(args, {"ok": not v["errors"], **v}, "\n".join(lines))
    return 0 if not v["errors"] else 2


def cli_board_inputs(args):
    project = _project(args)
    plan = inputs_plan(project)
    text = "\n".join(p["command"] for p in plan) or "No sendable references yet (all are reference-only)."
    _print(args, {"ok": True, "plan": plan}, text)
    return 0


def cli_board_serve(args):
    from . import board_server
    project = _project(args)
    load_board(project)
    return board_server.serve(project, port=getattr(args, "port", 0) or 8765,
                              open_browser=not getattr(args, "no_open", False))
