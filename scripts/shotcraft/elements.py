"""Elements: the characters, places, props and style frames of a production, each built and locked on its own
before any shot is generated. Shots are then composed from the locked elements.

An element (E01, E02 ...) lives in project.json under "elements". Each element has one or more views (a
character's turnaround and expression sheet, a place's empty plate, a prop's product shot). Each view is a
prompt card, 04_elements/cards/E01A.md, E01B.md ..., scaffolded from rules/element_recipes.json and generated
on the `element` tier while the elements stage is open. When the user approves a take of every view, `lock`
turns those takes into the element's reference assets (labelled @Label) and the element can be used in shots.

The written sheet (model sheet, wardrobe, environment description) lives beside it in
04_elements/<category>s/<slug>.md, written by the designers.

API:
    recipes(project=None) -> dict                     rules/element_recipes.json "categories"
    list_elements(project) -> [element dicts]
    get(project, element_id_or_label) -> element
    add(project, name, category, label=None, views=None, anchor=None, use_case=None) -> element (cards written)
    add_view(project, element_id, view) -> card path
    lock(project, element_id, user_said, gens=None) -> element
    unlock(project, element_id, user_said) -> element
    link(project, element_id, hf_element_id, hf_name=None) -> element   the Higgsfield Element it was saved as
    shot_elements(project) -> {shot id: [element labels]}   from the shot list (shot cell, else its scene's cell)
    attach_plan(project, shots=None) -> [{"shot", "asset", "as", "label"}]
    attach(project, shots, user_said) -> [added inputs]  puts each shot's locked elements on its card as inputs
    cli_element_add / list / show / view / lock / unlock / link / attach (args)

Stdlib only.
"""
import json
import os
import re

from . import Refused, ShotcraftError, jsonio, manifest, paths, rules, stages

CARD_DIR = "04_elements/cards"
TAKES_DIR = "06_generations/elements"
ELEMENT_RE = re.compile(r"^E\d{2,3}$")
CARD_RE = re.compile(r"^E\d{2,3}[A-Z]$")
LABEL_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{0,23}$")
SHEET_DIR = {"character": "characters", "environment": "environments", "prop": "props", "style": "style"}


# ---------------------------------------------------------------- rules and records

def recipes(project=None):
    data = rules.load("element_recipes", project)
    cats = data.get("categories") or {}
    if not cats:
        raise ShotcraftError("rules/element_recipes.json has no categories.")
    return cats


def _recipe(project, category):
    cats = recipes(project)
    if category not in cats:
        raise Refused("Category must be one of: %s." % ", ".join(cats))
    return cats[category]


def list_elements(project):
    return list(manifest.load(project).get("elements") or [])


def get(project, ref):
    ref = str(ref or "").strip().lstrip("@")
    for e in list_elements(project):
        if e["id"] == ref or e["label"].lower() == ref.lower():
            return e
    raise Refused("No element %s in this project (sc.py element list)." % ref)


def _save_element(project, el):
    data = manifest.load(project)
    els = data.setdefault("elements", [])
    for i, e in enumerate(els):
        if e["id"] == el["id"]:
            els[i] = el
            break
    else:
        els.append(el)
    manifest.save(project, data)
    return el


def _slug(text):
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "element"


def _label_from(name):
    words = re.findall(r"[A-Za-z0-9]+", name)
    lab = "".join(w[:1].upper() + w[1:] for w in words)[:24]
    if not lab or not lab[0].isalpha():
        lab = "E" + lab
    return lab[:24]


def _elements_open(project):
    st = stages.load_state(project)
    if st.get("track") != "full":
        raise Refused("Elements belong to the full track.")
    if st["stages"].get("elements", {}).get("status") != "open":
        raise Refused("The elements stage is not open. Start it first: sc.py stage start elements")


def _fill(value, anchor):
    if isinstance(value, str):
        return value.replace("{anchor}", anchor or "<the element's anchor sentence>")
    if isinstance(value, dict):
        return {k: _fill(v, anchor) for k, v in value.items()}
    if isinstance(value, list):
        return [_fill(v, anchor) for v in value]
    return value


# ---------------------------------------------------------------- cards

def _write_view_card(project, el, view, letter):
    from . import cards
    rec = _recipe(project, el["category"])
    vr = (rec.get("views") or {}).get(view)
    if vr is None:
        raise Refused("A %s has no %r view. Views: %s." % (el["category"], view, ", ".join(rec.get("views") or {})))
    try:
        presets = rules.load("presets", project)
        taxonomy = rules.load("taxonomy", project)
        negatives = rules.load("negatives", project)
        version = rules.rules_version(project)
    except Exception as exc:
        raise ShotcraftError("Could not read the rule files: %s" % exc)
    card_id = el["id"] + letter
    meta = cards.new_card(card_id, kind="image", use_case=el.get("use_case") or None, presets=presets,
                          taxonomy=taxonomy, negatives=negatives, rules_version=version,
                          title="%s: %s" % (el["name"], vr.get("label") or view))
    meta["tier_plan"] = ["element"]
    meta["model"] = {"element": None}
    meta["settings"]["aspect"] = vr.get("aspect") or meta["settings"].get("aspect") or "1:1"
    meta["settings"]["variants"] = 2
    for layer, fields in (vr.get("layers") or {}).items():
        meta["layers"].setdefault(layer, {})
        for f, v in _fill(fields, el.get("anchor")).items():
            meta["layers"][layer][f] = v
    if vr.get("finish"):
        meta["finish"] = vr["finish"]
        meta["layers"]["light_look"]["finish"] = ""
    meta["layers"]["intent"]["use"] = "element %s (@%s), %s view: %s" % (
        el["id"], el["label"], view, vr.get("why") or "")
    avoid = list(meta.get("avoid") or [])
    for a in vr.get("avoid") or []:
        if a not in avoid:
            avoid.append(a)
    meta["avoid"] = avoid
    meta["element"] = {"id": el["id"], "view": view, "category": el["category"], "label": el["label"]}
    meta["rationale"]["model"] = "Element sheet: a still that takes references (rules/routing.json element_policy)."
    os.makedirs(os.path.join(project, CARD_DIR), exist_ok=True)
    path = os.path.join(project, CARD_DIR, card_id + ".md")
    if os.path.exists(path):
        raise Refused("%s already exists." % paths.rel_to(project, path))
    cards.write(path, meta, cards.render_body(meta))
    return path


def add(project, name, category, label=None, views=None, anchor=None, use_case=None):
    _elements_open(project)
    rec = _recipe(project, category)
    label = (label or _label_from(name)).lstrip("@")
    if not LABEL_RE.match(label):
        raise Refused("A label is a letter then up to 23 letters, digits, - or _ (got %r)." % label)
    els = list_elements(project)
    if any(e["label"].lower() == label.lower() for e in els):
        raise Refused("@%s is taken. Pick another --label." % label)
    views = views or list(rec.get("default_views") or [])
    bad = [v for v in views if v not in (rec.get("views") or {})]
    if bad:
        raise Refused("Unknown view(s) for a %s: %s. Views: %s." % (category, ", ".join(bad),
                                                                    ", ".join(rec.get("views") or {})))
    n = max([int(e["id"][1:]) for e in els] or [0]) + 1
    el = {"id": "E%02d" % n, "name": name, "label": label, "category": category,
          "anchor": (anchor or "").strip(), "use_case": use_case or manifest.load(project).get("use_case"),
          "sheet": "04_elements/%s/%s.md" % (SHEET_DIR[category], _slug(name)),
          "views": {}, "status": "draft", "assets": [], "hf_element_id": None, "hf_name": None,
          "added": jsonio.now_iso()}
    for i, v in enumerate(views):
        letter = chr(ord("A") + i)
        _write_view_card(project, el, v, letter)
        el["views"][v] = el["id"] + letter
    return _save_element(project, el)


def add_view(project, element_id, view):
    _elements_open(project)
    el = get(project, element_id)
    if el.get("status") == "locked":
        raise Refused("%s is locked. Unlock it first to add a view." % el["id"])
    if view in el["views"]:
        raise Refused("%s already has a %s view (%s)." % (el["id"], view, el["views"][view]))
    letter = chr(ord("A") + len(el["views"]))
    path = _write_view_card(project, el, view, letter)
    el["views"][view] = el["id"] + letter
    _save_element(project, el)
    return path


# ---------------------------------------------------------------- lock

def _approved_take(gens, card_id):
    ok = [g for g in gens if g.get("shot") == card_id and g.get("tier") == "element"
          and g.get("status") == "completed" and g.get("approved") is True and g.get("outputs")]
    return ok[-1] if ok else None


def lock(project, element_id, user_said, gens=None):
    """Lock an element: every view needs an approved take (or the one named in gens, {view: G0007}). Its outputs
    become the element's reference assets, labelled for the prompts."""
    if not (user_said or "").strip():
        raise Refused("Locking an element needs the user's own words (--user-said).")
    _elements_open(project)
    el = get(project, element_id)
    data = manifest.load(project)
    all_gens = data.get("generations", [])
    rec = _recipe(project, el["category"])
    chosen, missing = {}, []
    for view, card_id in el["views"].items():
        g = None
        if gens and gens.get(view):
            g = next((x for x in all_gens if x.get("id") == gens[view]), None)
            if g is None or g.get("shot") != card_id or g.get("approved") is not True:
                raise Refused("%s is not an approved take of %s (%s view)." % (gens[view], card_id, view))
        else:
            g = _approved_take(all_gens, card_id)
        if g is None:
            missing.append("%s (%s)" % (card_id, view))
        else:
            chosen[view] = g
    if missing:
        raise Refused("No approved take yet for: %s. Approve one first (sc.py gen approve G... --user-said "
                      "\"...\")." % ", ".join(missing))
    assets = []
    for view, g in chosen.items():
        for out in g["outputs"][:1]:
            a = manifest.add_asset(project, os.path.join(project, out), "generated", rec.get("asset_role") or "reference",
                                   note="element %s @%s, %s view (%s)" % (el["id"], el["label"], view, g["id"]))
            d = manifest.load(project)
            for x in d["assets"]:
                if x["id"] == a["id"]:
                    x["element"] = el["id"]
                    x["label"] = el["label"] if view == list(el["views"])[0] else "%s_%s" % (el["label"], view)
                    x["view"] = view
            manifest.save(project, d)
            assets.append({"asset": a["id"], "view": view, "gen": g["id"], "path": out})
    el.update({"status": "locked", "assets": assets, "locked_said": user_said.strip(), "locked_at": jsonio.now_iso()})
    _save_element(project, el)
    manifest.add_decision(project, "elements", "Element %s @%s locked" % (el["id"], el["label"]), user_said)
    return el


def unlock(project, element_id, user_said):
    if not (user_said or "").strip():
        raise Refused("Unlocking an element needs the user's own words (--user-said).")
    _elements_open(project)
    el = get(project, element_id)
    el.update({"status": "draft", "locked_said": None})
    _save_element(project, el)
    manifest.add_decision(project, "elements", "Element %s @%s unlocked" % (el["id"], el["label"]), user_said)
    return el


def link(project, element_id, hf_element_id, hf_name=None):
    el = get(project, element_id)
    if el.get("status") != "locked":
        raise Refused("Save only a locked element to Higgsfield (%s is %s)." % (el["id"], el.get("status")))
    if not re.match(r"^[0-9a-fA-F-]{36}$", str(hf_element_id or "")):
        raise Refused("--hf-element must be the Higgsfield Element id (a UUID).")
    el.update({"hf_element_id": hf_element_id, "hf_name": hf_name})
    return _save_element(project, el)


# ---------------------------------------------------------------- shots

def shot_elements(project):
    scenes = {s["scene"]: stages.element_labels(s.get("elements")) for s in stages.parse_scenes(project)}
    out = {}
    for r in stages.parse_shotlist(project):
        if not r.get("id"):
            continue
        own = stages.element_labels(r.get("elements"))
        out[r["id"]] = own or list(scenes.get(str(r.get("scene") or "").strip(), []))
    return out


def attach_plan(project, shots=None):
    rec_cache = {}
    by_label = {e["label"].lower(): e for e in list_elements(project)}
    plan, problems = [], []
    for sid, labels in shot_elements(project).items():
        if shots and sid not in shots:
            continue
        for lab in labels:
            el = by_label.get(lab.lower())
            if el is None:
                problems.append("%s names @%s, which is not an element" % (sid, lab))
                continue
            if el.get("status") != "locked":
                problems.append("%s uses @%s, which is not locked" % (sid, lab))
                continue
            if el["category"] not in rec_cache:
                rec_cache[el["category"]] = _recipe(project, el["category"])
            role = rec_cache[el["category"]].get("input_role") or "reference"
            for a in el.get("assets") or []:
                plan.append({"shot": sid, "asset": a["asset"], "as": role, "label": el["label"], "view": a["view"]})
    return plan, problems


def attach(project, shots, user_said):
    from . import cards
    if not (user_said or "").strip():
        raise Refused("Putting elements on the cards needs the user's own words (--user-said).")
    plan, problems = attach_plan(project, shots)
    if problems:
        raise Refused("; ".join(problems))
    done = []
    for p in plan:
        path = os.path.join(project, "05_prompts", p["shot"] + ".md")
        if not os.path.exists(path):
            raise Refused("No card yet for %s (sc.py card new --shot %s)." % (p["shot"], p["shot"]))
        meta, _ = cards.read(path)
        if any(i.get("asset") == p["asset"] for i in meta.get("inputs") or [] if isinstance(i, dict)):
            continue
        cards.set_input(project, path, p["asset"], p["as"], user_said)
        done.append(p)
    return done


# ---------------------------------------------------------------- CLI

def _proj(args):
    from . import project as _p
    return _p.resolve(getattr(args, "project", None), getattr(args, "session_id", None))


def _emit(args, data, text):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(text)
    return 0


def _line(e):
    return "%s @%s  %s, %s  views: %s%s" % (
        e["id"], e["label"], e["name"], e["category"],
        ", ".join("%s (%s)" % (v, c) for v, c in e["views"].items()), "  [%s]" % e["status"] +
        ("  Higgsfield: %s" % e["hf_element_id"] if e.get("hf_element_id") else ""))


def cli_element_add(args):
    p = _proj(args)
    views = [v.strip() for v in (getattr(args, "views", None) or "").split(",") if v.strip()] or None
    el = add(p, args.name, args.category, label=getattr(args, "label", None), views=views,
             anchor=getattr(args, "anchor", None))
    return _emit(args, el, "Added %s\nCards: %s\nWrite its sheet at %s, fill each card, then estimate and generate "
                           "on the element tier." % (_line(el), ", ".join("%s/%s.md" % (CARD_DIR, c)
                                                                         for c in el["views"].values()), el["sheet"]))


def cli_element_list(args):
    els = list_elements(_proj(args))
    return _emit(args, els, "\n".join(_line(e) for e in els) or "No elements yet.")


def cli_element_views(args):
    cats = recipes(None)
    lines = []
    for c, r in cats.items():
        lines.append("%s: %s (default: %s)" % (c, r.get("label"), ", ".join(r.get("default_views") or [])))
        for v, vr in (r.get("views") or {}).items():
            lines.append("  %s: %s. %s" % (v, vr.get("label"), vr.get("why")))
    return _emit(args, cats, "\n".join(lines))


def cli_element_view(args):
    path = add_view(_proj(args), args.element, args.view)
    return _emit(args, {"ok": True, "path": path}, "Wrote %s." % path)


def cli_element_lock(args):
    gens = {}
    for item in getattr(args, "take", None) or []:
        if "=" not in item:
            raise Refused("--take is view=G0007.")
        k, v = item.split("=", 1)
        gens[k.strip()] = v.strip()
    el = lock(_proj(args), args.element, args.user_said, gens or None)
    return _emit(args, el, "Locked %s\nAssets: %s" % (_line(el), ", ".join(
        "%s (%s)" % (a["asset"], a["view"]) for a in el["assets"])))


def cli_element_unlock(args):
    el = unlock(_proj(args), args.element, args.user_said)
    return _emit(args, el, "Unlocked %s" % _line(el))


def cli_element_link(args):
    el = link(_proj(args), args.element, args.hf_element, getattr(args, "hf_name", None))
    return _emit(args, el, "Linked %s" % _line(el))


def cli_element_attach(args):
    p = _proj(args)
    shots = [s for s in (getattr(args, "shots", None) or [])] or None
    if getattr(args, "dry_run", False) or not getattr(args, "user_said", None):
        plan, problems = attach_plan(p, shots)
        text = "\n".join("%s: %s as %s (@%s %s)" % (x["shot"], x["asset"], x["as"], x["label"], x["view"])
                         for x in plan) or "Nothing to attach."
        if problems:
            text += "\nProblems:\n- " + "\n- ".join(problems)
        return _emit(args, {"plan": plan, "problems": problems}, text)
    done = attach(p, shots, args.user_said)
    return _emit(args, done, "Attached %d input(s)." % len(done))
