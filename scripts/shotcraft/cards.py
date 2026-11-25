"""Prompt cards: parse, write, scaffold and validate (SPEC section 5).

A card is a markdown file that starts with a JSON front matter block between two lines that
hold only '---', followed by a markdown body.

Public functions:
    parse_text(text) -> (meta, body)          raises CardError on bad front matter
    read(path) -> (meta, body)
    dump(meta, body) -> text
    write(path, meta, body)                    atomic
    new_card(shot, kind, use_case, from_text, presets=None, taxonomy=None, negatives=None) -> meta
    render_body(meta, compiled=None, model=None) -> body
    update_body_sections(body, sections) -> body
    validate(meta, presets=None, taxonomy=None) -> [error strings]   (empty list = valid)
    card_hash(meta) -> sha256 of the front matter minus status/approved_said/approved_hash
    resolve_card_path(value, project=None) -> Path   (absolute, cwd-relative, project-relative or a shot id)
    approve(project, path, user_said) -> meta         records the approval (hash + words) in project.json
    set_input(project, path, asset_id, role, user_said) -> meta
CLI (sc.py card ...): cli_card_new, cli_card_validate, cli_card_compile, cli_card_approve, cli_card_set_input,
cli_refine_save.

Stdlib only.
"""

import copy
import json
import os
import re
import tempfile
from pathlib import Path

FENCE = "---"

LAYER_FIELDS = {
    "intent": ["use", "platform", "audience", "brand"],
    "subject": ["subject", "action", "placement", "interaction", "wardrobe_props", "elements",
                "consistency"],
    "world": ["environment", "background_far", "background_near", "foreground", "parallax", "era",
              "time_of_day", "weather_season", "atmosphere"],
    "camera": ["shot_size", "angle", "lens", "dof", "composition", "movement", "movement_speed",
               "camera_look"],
    "light_look": ["setup", "quality", "direction", "color_temp", "practicals", "palette_grade",
                   "texture", "finish", "style_ref", "mood"],
    "time_output": ["beats", "pacing", "loop", "transition_in", "transition_out", "audio",
                    "on_screen_text"],
}

KINDS = ("video", "image")
TIERS = ("board", "draft", "final", "upscale")
INPUT_ROLES = ("start_frame", "end_frame", "reference", "character", "style")
STATUSES = ("draft", "approved", "generated", "final")
SHOT_RE = re.compile(r"^S\d{3,4}[A-Z]?$")
ASSET_RE = re.compile(r"^A\d{3,}$")
ASPECT_RE = re.compile(r"^(auto|\d+(\.\d+)?:\d+(\.\d+)?)$")
BEAT_T_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*s?\s*$")

# Body section headings (order matters for render_body).
SEC_PROMPT = "Prompt"
SEC_AVOID = "Avoid (guarded against)"
SEC_BEATS = "Beats"
SEC_WHY = "Why these settings"
SEC_SOURCE = "Source text"


class CardError(Exception):
    pass


# --------------------------------------------------------------------------- parse / dump

def parse_text(text):
    """Split card text into (meta dict, body str)."""
    if text.startswith("﻿"):
        text = text[1:]
    lines = text.splitlines(True)
    i = 0
    while i < len(lines) and not lines[i].strip():
        i += 1
    if i >= len(lines) or lines[i].strip() != FENCE:
        raise CardError("The card must start with a '---' line, then JSON front matter, then '---'.")
    start = i + 1
    end = None
    for j in range(start, len(lines)):
        if lines[j].strip() == FENCE:
            end = j
            break
    if end is None:
        raise CardError("The front matter has no closing '---' line.")
    raw = "".join(lines[start:end])
    try:
        meta = json.loads(raw)
    except ValueError as exc:
        raise CardError("The front matter is not valid JSON: {}".format(exc))
    if not isinstance(meta, dict):
        raise CardError("The front matter must be a JSON object.")
    body = "".join(lines[end + 1:])
    if body.startswith("\n"):
        body = body[1:]
    return meta, body


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return parse_text(fh.read())


def dump(meta, body=""):
    text = FENCE + "\n" + json.dumps(meta, indent=2, ensure_ascii=False) + "\n" + FENCE + "\n"
    if body:
        text += "\n" + body.lstrip("\n")
        if not text.endswith("\n"):
            text += "\n"
    return text


def _atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
        os.replace(tmp, str(path))
    except Exception:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write(path, meta, body=None):
    if body is None:
        body = render_body(meta)
    _atomic_write(path, dump(meta, body))


# --------------------------------------------------------------------------- body sections

def split_sections(body):
    """Return [(heading or None, text)] for '## ' headings."""
    out = []
    head, buf = None, []
    for line in body.splitlines(True):
        if line.startswith("## "):
            if head is not None or "".join(buf).strip():
                out.append((head, "".join(buf)))
            head, buf = line[3:].strip(), []
        else:
            buf.append(line)
    if head is not None or "".join(buf).strip():
        out.append((head, "".join(buf)))
    return out


def _sec_key(heading):
    h = (heading or "").lower()
    if h.startswith("prompt"):
        return SEC_PROMPT
    if h.startswith("avoid"):
        return SEC_AVOID
    if h.startswith("beats"):
        return SEC_BEATS
    if h.startswith("why"):
        return SEC_WHY
    if h.startswith("source"):
        return SEC_SOURCE
    return heading


def update_body_sections(body, sections):
    """Replace (or append) sections. `sections` maps a canonical key to (heading, text)."""
    parts = split_sections(body or "")
    done = set()
    out = []
    for head, text in parts:
        key = _sec_key(head)
        if key in sections:
            new_head, new_text = sections[key]
            out.append((new_head, new_text))
            done.add(key)
        else:
            out.append((head, text))
    for key, (new_head, new_text) in sections.items():
        if key not in done:
            out.append((new_head, new_text))
    chunks = []
    for head, text in out:
        text = text.strip("\n")
        if head is None:
            chunks.append(text + "\n")
        else:
            chunks.append("## " + head + "\n" + (text + "\n" if text else ""))
    return "\n".join(chunks)


def _beats_text(meta):
    beats = (((meta.get("layers") or {}).get("time_output") or {}).get("beats")) or []
    lines = []
    for b in beats:
        if isinstance(b, dict) and (b.get("what") or "").strip():
            lines.append("- {}s: {}".format(b.get("t", "?"), b.get("what")))
    return "\n".join(lines) or "(none yet)"


def _why_text(meta):
    rat = meta.get("rationale") or {}
    lines = ["- {}: {}".format(k, v) for k, v in rat.items() if v and k != "source_text"]
    return "\n".join(lines) or "(fill in why this model, resolution and duration)"


def render_body(meta, compiled=None, model=None):
    """Build the standard markdown body from the card (and a compile result if given)."""
    model = model or (compiled or {}).get("model") or "(not compiled yet)"
    if compiled:
        prompt = compiled.get("prompt") or ""
        if compiled.get("negative_prompt"):
            prompt += "\n\nNegative prompt: " + compiled["negative_prompt"]
    else:
        prompt = "(run: sc.py card compile <this file> --model <model id>)"
    avoid = meta.get("avoid") or []
    avoid_lines = []
    unguarded = set((compiled or {}).get("unguarded") or [])
    for a in avoid:
        avoid_lines.append("- {}{}".format(a, " (unguarded: no positive rewrite)" if a in unguarded else ""))
    sections = [
        ("## {} (compiled for {})".format(SEC_PROMPT, model), prompt),
        ("## " + SEC_AVOID, "\n".join(avoid_lines) or "(nothing listed)"),
        ("## " + SEC_BEATS, _beats_text(meta)),
        ("## " + SEC_WHY, _why_text(meta)),
    ]
    src = (meta.get("rationale") or {}).get("source_text")
    if src:
        sections.append(("## " + SEC_SOURCE, src))
    return "\n\n".join(h + "\n" + t.strip("\n") for h, t in sections) + "\n"


def body_with_compile(body, meta, compiled):
    """Refresh the Prompt and Avoid sections of an existing body from a compile result."""
    fresh = split_sections(render_body(meta, compiled))
    wanted = {}
    for head, text in fresh:
        key = _sec_key(head)
        if key in (SEC_PROMPT, SEC_AVOID):
            wanted[key] = (head, text)
    if not (body or "").strip():
        return render_body(meta, compiled)
    return update_body_sections(body, wanted)


# --------------------------------------------------------------------------- scaffold

def empty_layers():
    layers = {}
    for layer, fields in LAYER_FIELDS.items():
        layers[layer] = {}
        for f in fields:
            if f == "beats":
                layers[layer][f] = []
            elif f == "loop":
                layers[layer][f] = False
            else:
                layers[layer][f] = ""
    return layers


def _preset_table(presets):
    if not presets:
        return {}
    return presets.get("presets", presets) if isinstance(presets, dict) else {}


def _vocab_index(taxonomy):
    """[(term_lower, layer, field, term)] longest first, for matching free text."""
    idx = []
    for layer, ldef in ((taxonomy or {}).get("layers") or {}).items():
        if layer == "intent":
            continue
        for field, fdef in (ldef.get("fields") or {}).items():
            if field in ("beats", "loop"):
                continue
            for v in fdef.get("vocab") or []:
                term = v.get("term") if isinstance(v, dict) else None
                if not term:
                    continue
                clean = re.sub(r"\s*\([^)]*\)", "", term).strip()
                for t in {term, clean}:
                    if len(t) >= 3 and "|" not in t and "S010" not in t:
                        idx.append((t.lower(), layer, field, t))
    idx.sort(key=lambda x: -len(x[0]))
    return idx


STOPWORDS = {"a", "an", "the", "and", "with", "in", "at", "on", "of", "over", "under", "into",
             "from", "to", "by", "for", "through", "during", "shot", "shots", "look", "style",
             "lighting", "light", "camera", "lens", "very", "some", "lots", "very", "plus", "using"}


def extract_from_text(text, taxonomy):
    """Sort free text into layer fields.

    The text is split into clauses (commas, semicolons, full stops). A clause made only of
    taxonomy terms (plus small linking words) is moved into those fields. Any other clause is
    kept word for word as part of the subject, so the user's description is never mangled.
    Returns (fills {layer: {field: "a, b"}}, leftover text)."""
    fills = {}
    text = (text or "").strip()
    if not text or not taxonomy:
        return fills, text
    index = _vocab_index(taxonomy)
    keep = []
    for clause in re.split(r"\s*[,;]\s*|\.\s+|\s+\+\s+", text):
        clause = clause.strip().rstrip(".")
        if not clause:
            continue
        remaining = clause
        found = []
        for term_l, layer, field, term in index:
            pat = re.compile(r"(?<![\w-])" + re.escape(term_l) + r"(?![\w-])", re.I)
            m = pat.search(remaining)
            if not m:
                continue
            found.append((layer, field, m.group(0)))
            remaining = remaining[:m.start()] + " | " + remaining[m.end():]
        rest = [w for w in re.findall(r"[\w'-]+", remaining.lower()) if w not in STOPWORDS]
        if found and not rest:
            for layer, field, val in found:
                cur = fills.setdefault(layer, {}).get(field)
                if not cur:
                    fills[layer][field] = val
                elif val.lower() not in cur.lower():
                    fills[layer][field] = cur + ", " + val
        else:
            keep.append(clause)
    return fills, ", ".join(keep)


from shotcraft.compiler import MIN_GUARDS  # noqa: E402 - guards the trimmer keeps (no import cycle)
NATURAL_FINISHES = ("natural", "true_to_life")


def _finish_guards(negatives, finish):
    """Avoid guards for a preset's finish: negatives.json by_finish, else the first two too_perfect ones."""
    if finish not in NATURAL_FINISHES:
        return []
    by_finish = (negatives or {}).get("by_finish") or {}
    lst = by_finish.get(finish)
    if not isinstance(lst, list):
        lst = ((negatives or {}).get("by_category") or {}).get("too_perfect", [])[:2]
    return [a for a in lst if isinstance(a, str) and a.strip()]


def _finish_default(taxonomy, finish):
    """The light_look.finish default for a finish value (taxonomy 'defaults'), or None. A single legacy
    'default' string still applies to the natural looks."""
    if finish not in NATURAL_FINISHES or not taxonomy:
        return None
    fdef = (((taxonomy.get("layers") or {}).get("light_look") or {}).get("fields") or {}).get("finish") or {}
    defaults = fdef.get("defaults")
    if isinstance(defaults, dict):
        v = defaults.get(finish)
        return v if isinstance(v, str) and v.strip() else None
    v = fdef.get("default")
    return v if isinstance(v, str) and v.strip() else None


def _norm_text(v):
    return re.sub(r"\s+", " ", str(v or "")).strip().lower()


def new_card(shot, kind=None, use_case=None, from_text=None, presets=None, taxonomy=None,
             negatives=None, title=None, rules_version="0.0.0"):
    """Return a scaffolded card meta dict. Pass rule dicts to fill settings from the preset,
    split from_text into layer fields, and start the avoid list from negatives.json."""
    preset = (_preset_table(presets).get(use_case) if use_case else None) or {}
    finish = preset.get("finish") if isinstance(preset.get("finish"), str) else None
    if not kind:
        kind = preset.get("kind") if preset.get("kind") in KINDS else "video"
    res = preset.get("resolution") or {}
    dur = preset.get("shot_duration") or preset.get("duration") or {}
    settings = {
        "aspect": preset.get("aspect") if ASPECT_RE.match(str(preset.get("aspect") or "")) else
        ("16:9" if kind == "video" else "1:1"),
        "resolution": res.get("final") or ("1080p" if kind == "video" else "2k"),
        "variants": 2,
    }
    if kind == "video":
        typical = dur.get("typical") if isinstance(dur, dict) else None
        settings["duration_s"] = typical if isinstance(typical, (int, float)) else 5
        # Native audio only when the preset asks for it; "optional"/"post" means sound in post.
        settings["audio"] = preset.get("audio") in (True, "native")
    layers = empty_layers()
    rationale = {"model": "", "resolution": "", "duration": ""}
    if preset:
        rationale["resolution"] = "Preset {}: generate at {} (delivery {}).".format(
            use_case, settings["resolution"], res.get("delivery", "n/a"))
        if kind == "video":
            rationale["duration"] = "Preset {}: typical shot length {} s.".format(use_case, settings["duration_s"])
        layers["intent"]["platform"] = preset.get("label", "")
    if from_text:
        fills, leftover = extract_from_text(from_text, taxonomy)
        for layer, fields in fills.items():
            for f, v in fields.items():
                layers[layer][f] = v
        # Whatever was not sorted into a field stays as the subject, word for word. If every
        # clause was sorted, the subject is left empty for the user (validate will say so).
        layers["subject"]["subject"] = leftover
        rationale["source_text"] = from_text.strip()
    avoid = []
    if negatives:
        uni = negatives.get("universal", [])
        avoid.extend([a for a in ("blurry", "watermark") if a in uni] or uni[:2])
        cats = negatives.get("by_category") or {}
        if kind == "video":
            mv = _norm_text(layers["camera"].get("movement"))
            if not mv or any(w in mv for w in ("static", "locked", "tripod")):
                avoid.append("camera shake")
            avoid.extend([a for a in ("flicker", "morphing") if a in cats.get("motion", [])])
        if use_case == "icon-ui":
            avoid.extend(cats.get("icon", []))
        if use_case in ("product-shot",):
            avoid.extend(cats.get("product", [])[:4])
        if use_case in ("thumbnail", "banner-ad"):
            avoid.extend(cats.get("text", [])[:3])
        # Live-action looks: guard against the over-perfect "AI" finish. The first finish guard goes inside
        # the first MIN_GUARDS so the trimmer never drops it before the generic ones.
        finish_guards = _finish_guards(negatives, finish)
        if finish_guards:
            avoid.insert(min(MIN_GUARDS - 1, len(avoid)), finish_guards[0])
            avoid.extend(finish_guards[1:])
    default = _finish_default(taxonomy, finish)
    if default and not layers["light_look"].get("finish"):
        layers["light_look"]["finish"] = default
    seen = []
    for a in avoid:
        if a not in seen:
            seen.append(a)
    tier_plan = ["draft", "final"]
    meta = {
        "id": shot,
        "title": title or (from_text.strip()[:60] if from_text else ""),
        "kind": kind,
        "use_case": use_case or "",
        "tier_plan": tier_plan,
        "model": {"draft": None, "final": None, "upscale": None},
        "settings": settings,
        "handles_s": preset.get("handles_s", 0) if kind == "video" else 0,
        "inputs": [],
        "layers": layers,
        "avoid": seen,
        "status": "draft",
        "approved_said": None,
        "rationale": rationale,
        "checked_rules_version": rules_version,
    }
    return meta


# --------------------------------------------------------------------------- validate

def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def validate(meta, presets=None, taxonomy=None):
    """Return a list of plain-English errors. Empty list means the card is valid."""
    errs = []
    if not isinstance(meta, dict):
        return ["The front matter must be a JSON object."]

    sid = meta.get("id")
    if not isinstance(sid, str) or not SHOT_RE.match(sid):
        errs.append("id must be a shot id like S010 (got {!r}).".format(sid))
    kind = meta.get("kind")
    if kind not in KINDS:
        errs.append("kind must be 'video' or 'image' (got {!r}).".format(kind))
    uc = meta.get("use_case")
    if not isinstance(uc, str) or not uc:
        errs.append("use_case is missing (a preset id such as social-vertical).")
    else:
        table = _preset_table(presets)
        if table and uc not in table:
            errs.append("use_case '{}' is not a known preset. Known: {}.".format(uc, ", ".join(sorted(table))))

    tp = meta.get("tier_plan")
    if not isinstance(tp, list) or not tp:
        errs.append("tier_plan must be a non-empty list (board, draft, final, upscale).")
    else:
        bad = [t for t in tp if t not in TIERS]
        if bad:
            errs.append("tier_plan has unknown tiers: {}.".format(", ".join(map(str, bad))))

    model = meta.get("model")
    if model is not None and not isinstance(model, dict):
        errs.append("model must be an object like {\"draft\": id, \"final\": id, \"upscale\": null}.")
    elif isinstance(model, dict):
        for k, v in model.items():
            if k not in TIERS:
                errs.append("model has an unknown tier '{}'.".format(k))
            if v is not None and not isinstance(v, str):
                errs.append("model.{} must be a model id or null.".format(k))

    settings = meta.get("settings")
    dur = None
    if not isinstance(settings, dict):
        errs.append("settings must be an object.")
    else:
        asp = settings.get("aspect")
        if not isinstance(asp, str) or not ASPECT_RE.match(asp):
            errs.append("settings.aspect must look like '9:16' (got {!r}).".format(asp))
        if "resolution" in settings and not isinstance(settings.get("resolution"), str):
            errs.append("settings.resolution must be text such as '1080p' or '2k'.")
        v = settings.get("variants", 1)
        if not isinstance(v, int) or isinstance(v, bool) or v < 1 or v > 8:
            errs.append("settings.variants must be a whole number from 1 to 8.")
        if kind == "video":
            dur = settings.get("duration_s")
            if not _num(dur) or dur <= 0:
                errs.append("settings.duration_s must be a positive number of seconds for a video card.")
                dur = None
            if "audio" in settings and not isinstance(settings["audio"], bool):
                errs.append("settings.audio must be true or false.")
        elif kind == "image" and settings.get("duration_s"):
            errs.append("An image card cannot have settings.duration_s.")

    hs = meta.get("handles_s", 0)
    if hs is not None and (not _num(hs) or hs < 0 or hs > 5):
        errs.append("handles_s must be a number from 0 to 5.")

    inputs = meta.get("inputs", [])
    if not isinstance(inputs, list):
        errs.append("inputs must be a list.")
    else:
        roles = []
        for n, inp in enumerate(inputs):
            if not isinstance(inp, dict):
                errs.append("inputs[{}] must be an object {{\"asset\": \"A003\", \"as\": \"start_frame\"}}.".format(n))
                continue
            a = inp.get("asset")
            if not isinstance(a, str) or not ASSET_RE.match(a):
                errs.append("inputs[{}].asset must be an asset id like A003 (got {!r}).".format(n, a))
            r = inp.get("as")
            if r not in INPUT_ROLES:
                errs.append("inputs[{}].as must be one of {} (got {!r}).".format(n, ", ".join(INPUT_ROLES), r))
            roles.append(r)
        for r in ("start_frame", "end_frame"):
            if roles.count(r) > 1:
                errs.append("Only one input can be the {}.".format(r.replace("_", " ")))
        if kind == "image" and ("start_frame" in roles or "end_frame" in roles):
            errs.append("An image card cannot have start or end frames; use 'reference' instead.")

    layers = meta.get("layers")
    if not isinstance(layers, dict):
        errs.append("layers must be an object with the 6 layers.")
    else:
        for lname, lval in layers.items():
            if lname not in LAYER_FIELDS:
                errs.append("Unknown layer '{}'. Layers: {}.".format(lname, ", ".join(LAYER_FIELDS)))
                continue
            if not isinstance(lval, dict):
                errs.append("layers.{} must be an object.".format(lname))
                continue
            for f, v in lval.items():
                if f not in LAYER_FIELDS[lname]:
                    errs.append("Unknown field layers.{}.{}.".format(lname, f))
                    continue
                if f == "beats":
                    if not isinstance(v, list):
                        errs.append("layers.time_output.beats must be a list of {\"t\": \"0-2\", \"what\": \"...\"}.")
                        continue
                    last_end = 0.0
                    for n, b in enumerate(v):
                        if not isinstance(b, dict) or not isinstance(b.get("what"), str):
                            errs.append("beats[{}] needs 't' and 'what'.".format(n))
                            continue
                        m = BEAT_T_RE.match(str(b.get("t", "")))
                        if not m:
                            errs.append("beats[{}].t must be a range in seconds like '0-2' (got {!r}).".format(n, b.get("t")))
                            continue
                        a0, a1 = float(m.group(1)), float(m.group(2))
                        if a1 <= a0:
                            errs.append("beats[{}] ends before it starts ({}).".format(n, b.get("t")))
                        if a0 < last_end - 1e-9:
                            errs.append("beats[{}] overlaps the beat before it.".format(n))
                        last_end = max(last_end, a1)
                        if dur is not None and a1 > dur + 1e-9:
                            errs.append("beats[{}] runs to {} s, past the shot length of {} s.".format(n, m.group(2), dur))
                elif f == "loop":
                    if not isinstance(v, bool):
                        errs.append("layers.time_output.loop must be true or false.")
                elif not isinstance(v, str):
                    errs.append("layers.{}.{} must be text.".format(lname, f))
        subj = layers.get("subject") if isinstance(layers.get("subject"), dict) else {}
        if not str(subj.get("subject") or "").strip() and not str(subj.get("action") or "").strip():
            errs.append("Describe at least the subject or the action (layers.subject).")
        if kind == "image" and isinstance(layers.get("time_output"), dict):
            to = layers["time_output"]
            if to.get("beats"):
                errs.append("An image card cannot have beats.")

    avoid = meta.get("avoid", [])
    if not isinstance(avoid, list) or not all(isinstance(a, str) and a.strip() for a in avoid):
        errs.append("avoid must be a list of short phrases.")

    status = meta.get("status")
    if status not in STATUSES:
        errs.append("status must be one of {} (got {!r}).".format(", ".join(STATUSES), status))
    elif status in ("approved", "generated", "final"):
        said = meta.get("approved_said")
        if not isinstance(said, str) or not said.strip():
            errs.append("A card with status '{}' needs approved_said (the user's own words).".format(status))

    rat = meta.get("rationale", {})
    if rat is not None and not isinstance(rat, dict):
        errs.append("rationale must be an object.")
    return errs


def validate_text(text, presets=None, taxonomy=None):
    try:
        meta, _ = parse_text(text)
    except CardError as exc:
        return [str(exc)]
    return validate(meta, presets=presets, taxonomy=taxonomy)


def copy_meta(meta):
    return copy.deepcopy(meta)


APPROVAL_FIELDS = ("status", "approved_said", "approved_hash")


def card_hash(meta):
    """sha256 of the card's front matter without its approval fields. When the user approves a card, sc.py
    stores this hash in project.json; gen refuses a card whose hash changed since."""
    import hashlib
    clean = {k: v for k, v in (meta or {}).items() if k not in APPROVAL_FIELDS}
    blob = json.dumps(clean, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- CLI
# Called by scripts/sc.py. Each takes the argparse Namespace and returns an exit code:
# 0 = ok, 2 = refused (invalid card, already exists), 1 = error.

import datetime as _dt  # noqa: E402
import sys as _sys  # noqa: E402


def _out(args, data, human):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(human)


def _err(args, msg, code=1, **extra):
    data = {"ok": False, "error": msg}
    data.update(extra)
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print(msg, file=_sys.stderr)
    return code


def _rules_mod():
    from shotcraft import rules as _r
    return _r


def _active_project(args_or_explicit=None):
    """The project folder: --project if given (the project that holds it, when there is one), else this
    session's active project (--session-id, $CLAUDE_SESSION_ID, then the last opened project), else None.
    Takes the argparse Namespace, or an explicit path."""
    if args_or_explicit is None or isinstance(args_or_explicit, (str, Path)):
        explicit, sid = args_or_explicit, None
    else:
        explicit = getattr(args_or_explicit, "project", None)
        sid = getattr(args_or_explicit, "session_id", None)
    try:
        from shotcraft import project as _p
    except Exception:
        _p = None
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if _p is not None:
            found = str(p) if _p.is_project(str(p)) else _p.find_project_root(str(p))
            if found:
                return Path(found)
        return p
    if _p is None:
        return None
    try:
        found = _p.active_project(sid)
    except Exception:
        return None
    return Path(found) if found else None


def _is_real_project(project):
    return bool(project) and (Path(project) / "project.json").is_file()


def _projects_root():
    r = _rules_mod()
    for modname in ("config", "paths"):
        try:
            mod = __import__("shotcraft." + modname, fromlist=[modname])
        except Exception:
            continue
        for fn in ("projects_root",):
            f = getattr(mod, fn, None)
            if callable(f):
                try:
                    p = f()
                    if p:
                        return Path(p)
                except Exception:
                    pass
    cfg = r.user_home() / "config.json"
    try:
        with open(cfg, "r", encoding="utf-8") as fh:
            root = json.load(fh).get("projects_root")
        if root:
            return Path(root).expanduser()
    except (OSError, ValueError):
        pass
    return None


def resolve_card_path(value, project=None):
    """A card path as typed: absolute, relative to the cwd, or relative to the project (05_prompts/S010.md),
    or a bare shot id (S010). Returns the first that exists, else the path as given."""
    p = Path(str(value)).expanduser()
    if p.is_absolute() or p.exists():
        return p
    if project:
        cands = [Path(project) / p]
        if SHOT_RE.match(str(value)):
            cands.insert(0, Path(project) / "05_prompts" / (str(value) + ".md"))
        for c in cands:
            if c.exists():
                return c
    return p


def _path_arg(args, project=None):
    for name in ("path", "card", "file", "card_text_file"):
        v = getattr(args, name, None)
        if v:
            if project is None and name != "card_text_file":
                project = _active_project(args)
            return resolve_card_path(v, project)
    return Path("")


def _write_lock(project, path):
    """None when the card file may be written now, else the guard's reason (05_prompts/ follows the
    prompts stage lock, the same rule the guard applies to Write/Edit)."""
    if not _is_real_project(project):
        return None
    try:
        rel = Path(path).resolve().relative_to(Path(project).resolve()).as_posix()
    except ValueError:
        return None
    from shotcraft import stages as _st
    ok, reason = _st.path_writable(str(project), rel)
    return None if ok else reason


def _slugify(text, fallback="prompt"):
    s = re.sub(r"[^a-z0-9]+", "-", str(text or "").lower()).strip("-")
    return s[:48].strip("-") or fallback


def cli_card_new(args):
    """sc.py card new --shot S010 [--kind video|image] [--use-case U] [--from-text "..."] [--project P]"""
    r = _rules_mod()
    shot = getattr(args, "shot", None)
    if not shot or not SHOT_RE.match(shot):
        return _err(args, "--shot must be a shot id like S010.", 2)
    project = _active_project(args)
    try:
        presets = r.load("presets", project)
        taxonomy = r.load("taxonomy", project)
        negatives = r.load("negatives", project)
        version = r.rules_version(project)
    except Exception as exc:
        return _err(args, "Could not read the rule files: {}".format(exc))
    use_case = getattr(args, "use_case", None)
    if not use_case and project:
        try:
            with open(project / "project.json", "r", encoding="utf-8") as fh:
                use_case = json.load(fh).get("use_case")
        except (OSError, ValueError):
            pass
    table = _preset_table(presets)
    if use_case and table and use_case not in table:
        return _err(args, "Unknown use case '{}'. Known: {}.".format(use_case, ", ".join(sorted(table))), 2)
    meta = new_card(shot, kind=getattr(args, "kind", None), use_case=use_case,
                    from_text=getattr(args, "from_text", None), presets=presets,
                    taxonomy=taxonomy, negatives=negatives, rules_version=version)
    text = dump(meta, render_body(meta))
    if project:
        dest = project / "05_prompts" / (shot + ".md")
        if dest.exists() and not getattr(args, "force", False):
            return _err(args, "{} already exists. Edit it, or pick another shot id.".format(dest), 2, path=str(dest))
        lock = _write_lock(project, dest)
        if lock:
            return _err(args, "Not writing {}: {}".format(dest, lock), 2, path=str(dest))
        _atomic_write(dest, text)
        problems = validate(meta, presets=presets)
        _out(args, {"ok": True, "path": str(dest), "card": meta, "todo": problems},
             "Wrote {}.{}".format(dest, (" Still to fill: " + "; ".join(problems)) if problems else ""))
        return 0
    if getattr(args, "json", False):
        print(json.dumps({"ok": True, "path": None, "card": meta, "text": text}, indent=2, ensure_ascii=False))
    else:
        _sys.stdout.write(text)
    return 0


def cli_card_validate(args):
    """sc.py card validate PATH"""
    r = _rules_mod()
    project = _active_project(args)
    path = _path_arg(args, project)
    try:
        meta, _ = read(path)
    except OSError as exc:
        return _err(args, "Cannot read {}: {}".format(path, exc))
    except CardError as exc:
        return _err(args, "{}: {}".format(path, exc), 2, errors=[str(exc)], path=str(path))
    project = _project_of(path) or project
    try:
        presets = r.load("presets", project)
    except Exception:
        presets = None
    errors = validate(meta, presets=presets)
    if errors:
        _out(args, {"ok": False, "path": str(path), "errors": errors},
             "{} is not valid:\n".format(path) + "\n".join("- " + e for e in errors))
        return 2
    _out(args, {"ok": True, "path": str(path), "errors": []}, "{} is valid.".format(path))
    return 0


def _project_of(path):
    """If path is inside a project (a folder holding project.json), return that folder."""
    p = Path(path).resolve()
    for parent in [p.parent] + list(p.parents):
        if (parent / "project.json").is_file():
            return parent
    return None


def cli_card_compile(args):
    """sc.py card compile PATH --model M [--provider P] [--json]

    Prints the compiled prompt and params, and refreshes the card's 'Prompt' and 'Avoid'
    body sections (skipped when args.dry_run is set)."""
    from shotcraft import compiler as _c
    r = _rules_mod()
    project = _active_project(args)
    path = _path_arg(args, project)
    try:
        meta, body = read(path)
    except OSError as exc:
        return _err(args, "Cannot read {}: {}".format(path, exc))
    except CardError as exc:
        return _err(args, "{}: {}".format(path, exc), 2)
    project = _project_of(path) or project
    if not getattr(args, "dry_run", False):
        lock = _write_lock(project, path)
        if lock:
            return _err(args, "Not rewriting {}: {} To see the compiled prompt without changing the card, add "
                              "--dry-run.".format(path, lock), 2)
    try:
        presets = r.load("presets", project)
    except Exception:
        presets = None
    errors = validate(meta, presets=presets)
    if errors:
        return _err(args, "Fix the card first:\n" + "\n".join("- " + e for e in errors), 2, errors=errors)
    model = getattr(args, "model", None)
    provider = getattr(args, "provider", None) or "higgsfield"
    if not model:
        return _err(args, "--model is required.", 2)
    try:
        profile, why = r.model_profile(model, provider, project)
    except Exception as exc:
        return _err(args, "Could not read models.json: {}".format(exc))
    if profile is None:
        return _err(args, why, 2)
    try:
        bundle = r.compiler_rules(project)
    except Exception as exc:
        return _err(args, "Could not read the rule files: {}".format(exc))
    result = _c.compile(meta, profile, bundle)
    result["model_name"] = profile.get("name") or model
    result["provider"] = provider
    result["card"] = str(path)
    if not getattr(args, "dry_run", False):
        try:
            _atomic_write(path, dump(meta, body_with_compile(body, meta, result)))
            result["card_updated"] = True
        except OSError as exc:
            result["card_updated"] = False
            result["warnings"].append("Could not update the card body: {}".format(exc))
    if getattr(args, "json", False):
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    lines = ["Prompt for {} ({} of {} words):".format(result["model_name"], result["word_count"],
                                                     result["max_prompt_words"]), "", result["prompt"], ""]
    if result["negative_prompt"]:
        lines += ["Negative prompt: " + result["negative_prompt"], ""]
    lines.append("Params: " + json.dumps(result["params"], ensure_ascii=False))
    for a in result["adjustments"]:
        lines.append("Changed {}: {} -> {}. {}".format(a["param"], a["from"], a["to"], a["reason"]))
    if result["dropped_fields"]:
        lines.append("Left out: " + ", ".join("{} ({})".format(d["field"], d["reason"]) for d in result["dropped_fields"]))
    if result["unguarded"]:
        lines.append("Not guarded (no positive wording found): " + ", ".join(result["unguarded"]))
    for w in result["warnings"]:
        lines.append("Note: " + w)
    print("\n".join(lines))
    return 0


def cli_refine_save(args):
    """sc.py refine save PATH [--slug S]

    Validates a card file and saves it to <projects_root>/_refine/<date>-<slug>.md."""
    r = _rules_mod()
    src = _path_arg(args, False)
    try:
        text = src.read_text(encoding="utf-8")
    except OSError as exc:
        return _err(args, "Cannot read {}: {}".format(src, exc))
    try:
        meta, body = parse_text(text)
    except CardError as exc:
        return _err(args, "{}: {}".format(src, exc), 2, errors=[str(exc)])
    try:
        presets = r.load("presets")
    except Exception:
        presets = None
    errors = validate(meta, presets=presets)
    if errors:
        return _err(args, "The card is not valid:\n" + "\n".join("- " + e for e in errors), 2, errors=errors)
    root = _projects_root()
    base = (root / "_refine") if root else (r.user_home() / "refine")
    slug = _slugify(getattr(args, "slug", None) or meta.get("title") or meta.get("id"))
    date = _dt.date.today().isoformat()
    dest = base / "{}-{}.md".format(date, slug)
    n = 2
    while dest.exists():
        dest = base / "{}-{}-{}.md".format(date, slug, n)
        n += 1
    _atomic_write(dest, dump(meta, body))
    note = "" if root else " (no projects_root set yet, so it went to your shotcraft folder)"
    _out(args, {"ok": True, "path": str(dest)}, "Saved {}{}.".format(dest, note))
    return 0


# --------------------------------------------------------------------------- approve / set-input
# Both write the card through sc.py whatever the 05_prompts/ lock, but only while prompts, boards, drafts or
# finals is open, so a late approval or a new start frame after boards does not need `stage reopen prompts`.

CARD_EDIT_STAGES = ("prompts", "boards", "drafts", "finals")


def _card_in_project(project, path):
    """(project str, rel path) for a card under <project>/05_prompts/, else raises Refused."""
    from shotcraft import Refused
    if not _is_real_project(project):
        raise Refused("No shotcraft project for this card. Pass --project or open the project first.")
    proj = Path(project).resolve()
    real = Path(os.path.realpath(str(path)))
    if real.parent != Path(os.path.realpath(str(proj / "05_prompts"))) or real.suffix != ".md":
        raise Refused("Only cards in 05_prompts/<shot>.md can be approved or changed this way ({}).".format(path))
    return str(proj), "05_prompts/" + real.name


def _card_edit_open(project):
    from shotcraft import Refused, stages as _st
    st = _st.load_state(project)
    if st.get("track") == "refine":
        return
    open_now = [s for s in CARD_EDIT_STAGES if st["stages"].get(s, {}).get("status") == "open"]
    if not open_now:
        raise Refused("Cards are approved or changed only while prompts, boards, drafts or finals is open.")


def approve(project, path, user_said):
    """Validate the card, set status approved + approved_said + approved_hash, and record the approval in
    project.json (the hash there is what gen checks)."""
    from shotcraft import Refused, manifest, rules as _r
    if not (user_said or "").strip():
        raise Refused("Approving a card needs the user's own words (--user-said).")
    proj, rel = _card_in_project(project, path)
    _card_edit_open(proj)
    meta, body = read(path)
    if str(meta.get("id") or "") != Path(rel).stem:
        raise Refused("The card's id ({}) does not match its file name ({}).".format(meta.get("id"), rel))
    try:
        presets = _r.load("presets", proj)
    except Exception:
        presets = None
    meta["status"] = "approved"
    meta["approved_said"] = user_said.strip()
    errors = validate(meta, presets=presets)
    if errors:
        raise Refused("The card does not validate, so it can't be approved:\n- " + "\n- ".join(errors))
    h = card_hash(meta)
    meta["approved_hash"] = h
    _atomic_write(path, dump(meta, body))
    manifest.set_card_approval(proj, meta["id"], h, user_said.strip(), rel)
    return meta


def set_input(project, path, asset_id, role, user_said):
    """Point a card input slot at an asset (an approved board as the start frame, say). start_frame and
    end_frame replace the slot; other roles add a reference. An approved card stays approved on these words."""
    from shotcraft import Refused, manifest
    if not (user_said or "").strip():
        raise Refused("Changing a card's inputs needs the user's own words (--user-said).")
    if role not in INPUT_ROLES:
        raise Refused("--as must be one of: {}.".format(", ".join(INPUT_ROLES)))
    proj, rel = _card_in_project(project, path)
    _card_edit_open(proj)
    data = manifest.load(proj)
    asset = manifest.find_asset(data, asset_id)
    if asset is None:
        raise Refused("No asset {} in this project.".format(asset_id))
    if asset.get("rights") not in ("owned", "licensed", "generated"):
        raise Refused("{} is {}; only owned, licensed or generated assets can be a model input. If the user owns "
                      "it: sc.py asset mark {} --rights owned --user-said \"...\"".format(
                          asset_id, asset.get("rights"), asset_id))
    meta, body = read(path)
    was_approved = meta.get("status") in ("approved", "generated", "final")
    inputs = [i for i in (meta.get("inputs") or []) if isinstance(i, dict)]
    if role in ("start_frame", "end_frame"):
        inputs = [i for i in inputs if i.get("as") != role]
    inputs = [i for i in inputs if not (i.get("asset") == asset_id and i.get("as") == role)]
    inputs.append({"asset": asset_id, "as": role})
    meta["inputs"] = inputs
    if was_approved:
        meta["approved_hash"] = card_hash(meta)
    _atomic_write(path, dump(meta, body))
    manifest.add_decision(proj, None, "Card {}: {} set to {}".format(meta.get("id"), role, asset_id),
                          user_said.strip())
    if was_approved:
        manifest.set_card_approval(proj, meta.get("id"), meta["approved_hash"], user_said.strip(), rel)
    return meta


def _run_refusable(args, fn):
    from shotcraft import Refused
    try:
        return fn()
    except Refused as exc:
        return _err(args, str(exc), 2)
    except (OSError, CardError) as exc:
        return _err(args, str(exc))


def cli_card_approve(args):
    """sc.py card approve PATH --user-said "..." """
    project = _active_project(args)
    path = _path_arg(args, project)
    project = _project_of(path) or project

    def go():
        meta = approve(project, path, getattr(args, "user_said", None))
        _out(args, {"ok": True, "path": str(path), "id": meta.get("id"), "status": meta["status"],
                    "approved_hash": meta["approved_hash"]},
             "{} approved on the user's words. It can be generated now; any later change to the card needs a "
             "new approval.".format(meta.get("id")))
        return 0
    return _run_refusable(args, go)


def cli_card_set_input(args):
    """sc.py card set-input PATH --asset A012 --as start_frame|end_frame|reference|character|style --user-said "..." """
    project = _active_project(args)
    path = _path_arg(args, project)
    project = _project_of(path) or project

    def go():
        meta = set_input(project, path, getattr(args, "asset", None), getattr(args, "as_role", None),
                         getattr(args, "user_said", None))
        _out(args, {"ok": True, "path": str(path), "inputs": meta.get("inputs"), "status": meta.get("status")},
             "{}: {} is now {}.".format(meta.get("id"), getattr(args, "as_role", None), getattr(args, "asset", None)))
        return 0
    return _run_refusable(args, go)
