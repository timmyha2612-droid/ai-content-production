"""Compile a prompt card into provider-ready text and params for one model (SPEC section 5).

    compile(card, model_profile, rules) -> {
        "prompt": str,
        "negative_prompt": str | None,
        "params": {aspect_ratio, resolution, duration, audio, start_image, end_image, image_references},
        "adjustments": [{"param", "from", "to", "reason"}],
        "unguarded": [avoid terms with no positive rewrite (or trimmed away)],
        "dropped_fields": [{"field": "light_look.texture", "reason": "..."}],
        "word_count": int,
        "max_prompt_words": int, "model": id, "motion_only": bool, "warnings": [str],
        "requested_duration_s": float | None,
    }

`card` is the card meta dict (front matter). `model_profile` is one entry of rules/models.json
(it may carry "id"). `rules` is a dict with optional keys "taxonomy", "positive_rewrites",
"negatives", "presets" (see rules.compiler_rules()). "presets" gives the card's finish value
(natural | true_to_life | clean) from its use_case; without it the finish is unknown. Missing pieces fall back to safe defaults:
max_prompt_words=120, negative_prompt=false.

Params use the Higgsfield CLI flag names (aspect_ratio, resolution, duration, start_image,
end_image, image_references); media values are asset ids from project.json for the provider
adapter to resolve. "audio" is a generic boolean the adapter maps to the model's own flag.

Stdlib only.
"""

import math
import re

DEFAULT_MAX_WORDS = 120
DEFAULT_PROTECT = 90
MIN_GUARDS = 2
DEFAULT_GUARD_PRIORITY = 45

# Prompt order: subject+action -> world -> depth planes -> camera -> light & look -> time/beats -> style.
# The depth group is the frame built like a multiplane cel set-up: far background, near background, the
# subject's place in the midground, then the foreground, then how the planes move against each other.
ORDER = [
    ("subject", ["subject", "action", "interaction", "wardrobe_props", "elements", "consistency"]),
    ("world", ["environment", "era", "time_of_day", "weather_season", "atmosphere"]),
    ("depth", ["background_far", "background_near", "placement", "foreground", "parallax"]),
    ("camera", ["shot_size", "angle", "lens", "dof", "composition", "movement", "movement_speed",
                "camera_look"]),
    ("light_look", ["setup", "quality", "direction", "color_temp", "practicals", "palette_grade",
                    "texture", "finish", "mood"]),
    ("time_output", ["beats", "pacing", "loop", "transition_in", "transition_out", "audio",
                     "on_screen_text"]),
    ("style", ["style_ref"]),
]
# Fields that print in a group other than their own card layer.
FIELD_LAYER = {"style_ref": "light_look", "background_far": "world", "background_near": "world",
               "foreground": "world", "parallax": "world", "placement": "subject"}
# How fragments inside one group are joined (default ", ").
GROUP_JOIN = {"depth": "; "}
DEPTH_FIELDS = ("world.background_far", "world.background_near", "world.foreground")

# Fallback priorities (higher = more important). texture, practicals, era, camera_look go first.
DEFAULT_PRIORITY = {
    "subject.subject": 100, "subject.action": 98, "camera.movement": 94,
    "camera.movement_speed": 92, "camera.shot_size": 90, "world.environment": 88,
    "time_output.on_screen_text": 85, "time_output.beats": 84, "world.time_of_day": 82,
    "light_look.setup": 80, "camera.angle": 78, "light_look.mood": 76, "subject.placement": 75,
    "camera.lens": 74, "subject.interaction": 73,
    "camera.composition": 72, "light_look.style_ref": 70, "time_output.loop": 70,
    "time_output.audio": 68, "world.foreground": 67, "subject.elements": 66, "time_output.pacing": 64,
    "world.atmosphere": 62, "world.background_near": 61, "light_look.palette_grade": 60, "camera.dof": 58,
    "light_look.color_temp": 56, "light_look.direction": 54,
    "world.background_far": 53, "light_look.quality": 52,
    "world.weather_season": 50, "world.parallax": 49, "subject.consistency": 48, "light_look.finish": 47,
    "subject.wardrobe_props": 46,
    "time_output.transition_in": 44, "time_output.transition_out": 42,
    "camera.camera_look": 40, "world.era": 30, "light_look.practicals": 20,
    "light_look.texture": 10,
}

IMAGE_SKIP = {"camera.movement", "camera.movement_speed", "time_output.beats", "time_output.pacing",
              "time_output.loop", "time_output.transition_in", "time_output.transition_out",
              "time_output.audio", "world.parallax"}
# With a start frame the planes are already drawn; what still has to be said is how they move and how the
# subject and the place act on each other over time (splashes, hair in the wind, light sweeping across).
# A card with a `source` input edits that video (a relight, a sky change, a restyle): the source already sets
# the framing, the camera move and the timing, so those fields are left out and the words go to what changes.
EDIT_SKIP = {"camera.shot_size", "camera.angle", "camera.lens", "camera.dof", "camera.composition",
             "camera.movement", "camera.movement_speed", "camera.camera_look", "time_output.beats",
             "time_output.pacing", "time_output.transition_in", "time_output.transition_out",
             "subject.placement", "subject.interaction"}

MOTION_KEEP = {"subject.action", "subject.interaction", "world.parallax", "camera.movement",
               "camera.movement_speed", "time_output.beats",
               "time_output.pacing", "time_output.loop", "time_output.transition_in",
               "time_output.transition_out", "time_output.audio"}

# Depth labels: a plane is named so the model places it, unless the text already names it.
DEPTH_LABEL = {
    "world.background_far": ("far background", ("far background", "distance", "distant", "horizon")),
    "world.background_near": ("background", ("background",)),
    "subject.placement": ("midground", ("midground", "middle ground", "mid-ground", "foreground",
                                        "background", "close to lens", "close to the lens")),
    "world.foreground": ("foreground", ("foreground",)),
    "world.parallax": ("depth motion", ("parallax", "moves", "drift", "streak", "slower", "faster")),
}
# A look that asks for grain: these words, plus taxonomy texture terms whose "means" mentions grain.
GRAIN_WORDS = ("grain", "film stock", "35mm", "16mm", "super 8", "halation", "portra", "vision3", "500t",
               "800t", "cinestill", "hp5", "ilford", "ektachrome", "kodak")
# Negated grain wording is removed before matching ("clean digital, no grain" asks for no grain).
GRAIN_NEGATED = re.compile(r"\b(?:no|without|zero|free of|minus)\s+(?:\w+\s+)?grain\b|\bgrain[- ]?(?:free|less)\b|"
                           r"\bclean(?:\s+digital)?\b")
# An avoid guard fights grain when it names grain or noise.
GRAIN_GUARD_WORDS = ("grain", "noise")

NATURAL_FINISHES = ("natural", "true_to_life")
SHALLOW_WORDS = ("shallow", "out of focus", "out-of-focus", "bokeh", "blurred", "blurry", "soft")
SHALLOW_FIELDS = (("camera", "dof"), ("world", "foreground"), ("world", "background_near"),
                  ("world", "background_far"))
SYMMETRY_RE = re.compile(r"(?<!a)symmetr|(?<!off-)(?<!off )\bcent(?:red|ered)\b|cent(?:re|er)[- ]punch|"
                         r"one[- ]point")

RES_RANK = {"360p": 360, "480p": 480, "540p": 540, "576p": 576, "720p": 720, "768": 768,
            "1080p": 1080, "1440p": 1440, "2160p": 2160, "4k": 2160, "1k": 1024, "2k": 2048,
            "512": 512, "1080": 1080, "8k": 4320}


# --------------------------------------------------------------------------- helpers

def _norm(s):
    return re.sub(r"\s+", " ", str(s or "")).strip().lower()


def _words(text):
    return len(text.split())


def _priority(taxonomy, key):
    layer, field = key.split(".", 1)
    try:
        p = taxonomy["layers"][layer]["fields"][field]["priority"]
        if isinstance(p, (int, float)):
            return p
    except (KeyError, TypeError):
        pass
    return DEFAULT_PRIORITY.get(key, 50)


def _fragment(key, value):
    """Turn one field value into prompt text, or '' if empty."""
    if key == "time_output.beats":
        parts = []
        for b in value or []:
            if isinstance(b, dict) and str(b.get("what") or "").strip():
                t = str(b.get("t") or "").strip()
                what = str(b["what"]).strip().rstrip(".")
                t = str(t).strip() if t is not None else ""
                if t and not re.search(r"[a-z]\s*$", t, re.I):
                    t += " s"  # "0-4" -> "0-4 s"; "0-4 s" and "0-4s" stay as they are
                parts.append("{}: {}".format(t, what) if t else what)
        return "; ".join(parts)
    if key == "time_output.loop":
        return "seamless loop, the last frame matches the first" if value is True else ""
    if not isinstance(value, str):
        return ""
    v = value.strip().rstrip(".")
    if not v:
        return ""
    if key == "time_output.transition_in":
        return "opens with " + v
    if key == "time_output.transition_out":
        return "ends with " + v
    if key == "time_output.audio":
        return v if v.lower().startswith(("audio", "sound", "no audio", "silent")) else "audio: " + v
    if key == "time_output.on_screen_text":
        if str(v).strip().lower() in ("none", "no", "no text", "n/a", "-", "nothing"):
            return ""
        if '"' in v or "“" in v or "text" in v.lower():
            return v
        return 'on-screen text reads "{}"'.format(v)
    if key in DEPTH_LABEL:
        label, names = DEPTH_LABEL[key]
        return v if any(n in v.lower() for n in names) else "{}: {}".format(label, v)
    if key == "light_look.mood":
        return v if "mood" in v.lower() or "feel" in v.lower() else v + " mood"
    if key == "camera.movement_speed":
        return v if "speed" in v.lower() or "motion" in v.lower() or "ease" in v.lower() else v + " camera move"
    return v


def _cap(s):
    return s[:1].upper() + s[1:] if s else s


def _assemble(items):
    """items: ordered list of dicts with 'group' and 'text'. Join into sentences per group."""
    sentences = []
    cur_group, cur = None, []
    for it in items:
        if it["group"] != cur_group and cur:
            sentences.append(GROUP_JOIN.get(cur_group, ", ").join(cur))
            cur = []
        cur_group = it["group"]
        cur.append(it["text"])
    if cur:
        sentences.append(GROUP_JOIN.get(cur_group, ", ").join(cur))
    return " ".join(_cap(s) + "." for s in sentences if s)


def _ratio(a):
    try:
        w, h = str(a).split(":")
        return float(w) / float(h)
    except (ValueError, ZeroDivisionError):
        return None


def _res_rank(r):
    s = str(r).strip().lower()
    if s in RES_RANK:
        return RES_RANK[s]
    m = re.match(r"^(\d+)\s*p?$", s)
    if m:
        return int(m.group(1))
    m = re.match(r"^(\d+)\s*x\s*(\d+)$", s)
    if m:
        return min(int(m.group(1)), int(m.group(2)))
    m = re.match(r"^(\d+(?:\.\d+)?)k$", s)
    if m:
        return int(float(m.group(1)) * 1024)
    return None


def _fit_aspect(want, allowed):
    if not allowed or want in allowed:
        return want, None
    wr = _ratio(want)
    numeric = [(a, _ratio(a)) for a in allowed if _ratio(a)]
    if wr is None or not numeric:
        return (allowed[0], "Not offered by this model; using its first option.")
    best = min(numeric, key=lambda x: abs(math.log(x[1] / wr)))[0]
    return best, "This model does not offer {}. {} is the closest; crop to {} in post.".format(want, best, want)


def _fit_resolution(want, allowed):
    if not allowed or want is None:
        return want, None
    low = {str(a).lower(): a for a in allowed}
    if str(want).lower() in low:
        return low[str(want).lower()], None
    wr = _res_rank(want)
    ranked = sorted([(a, _res_rank(a)) for a in allowed if _res_rank(a) is not None], key=lambda x: x[1])
    if wr is None or not ranked:
        return allowed[0], "Not offered by this model; using its first option."
    above = [a for a, r in ranked if r >= wr]
    if above:
        return above[0], "{} is not offered; {} is the smallest size that still covers it.".format(want, above[0])
    top = ranked[-1][0]
    return top, "{} is not offered; {} is the largest this model makes (upscale later only if delivery needs it).".format(want, top)


def _fit_duration(want, spec):
    """spec: list of allowed seconds, or {"min": a, "max": b}. Returns (value, reason)."""
    if want is None or spec is None:
        return want, None
    if isinstance(spec, dict):
        lo, hi = spec.get("min"), spec.get("max")
        val = want
        if isinstance(val, float) and not val.is_integer():
            val = int(math.ceil(val))
        val = int(val) if float(val).is_integer() else val
        if lo is not None and val < lo:
            return lo, "{} s is below this model's minimum; using {} s.".format(want, lo)
        if hi is not None and val > hi:
            return hi, "{} s is above this model's maximum; using {} s. Split the shot if it needs more.".format(want, hi)
        if val != want:
            return val, "This model takes whole seconds; rounded {} s up to {} s.".format(want, val)
        return val, None
    allowed = sorted(x for x in spec if isinstance(x, (int, float)))
    if not allowed:
        return want, None
    if want in allowed:
        return want, None
    # nearest; on a tie take the longer one (it can be trimmed in the edit)
    best = min(allowed, key=lambda x: (abs(x - want), -x))
    if best > want:
        why = "{} s is not offered; {} s is the nearest. Trim {} s in the edit.".format(want, best, round(best - want, 2))
    else:
        why = "{} s is not offered; {} s is the nearest. The clip will be {} s shorter than planned.".format(
            want, best, round(want - best, 2))
    return best, why


# --------------------------------------------------------------------------- avoid

def _rkey(s):
    """Lookup key for an avoid term: commas are not significant ("flat, even lighting" = "flat even lighting")."""
    return _norm(str(s or "").replace(",", " "))


def _rewrite_lookup(rewrites):
    return {_rkey(k): v for k, v in (rewrites or {}).items()
            if isinstance(v, str) and not str(k).startswith("_")}


def _tokens(s):
    """Normalised words for containment checks: lower case, no punctuation, plural 's' dropped."""
    out = []
    for w in re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)*", str(s or "").lower()):
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        out.append(w)
    return " " + " ".join(out) + " "


def _contained(phrase, text):
    p = _tokens(phrase)
    return p.strip() != "" and p in _tokens(text)


def _preset_finish(card, rules):
    """The card's finish value from its preset (natural | true_to_life | clean), or None when unknown."""
    presets = (rules or {}).get("presets") or {}
    table = presets.get("presets", presets) if isinstance(presets, dict) else {}
    p = table.get(card.get("use_case")) if isinstance(table, dict) else None
    f = p.get("finish") if isinstance(p, dict) else None
    return f if isinstance(f, str) and f else None


def _grain_words(taxonomy):
    words = set(GRAIN_WORDS)
    tex = ((((taxonomy or {}).get("layers") or {}).get("light_look") or {}).get("fields") or {}).get("texture") or {}
    for v in tex.get("vocab") or []:
        if not isinstance(v, dict) or not v.get("term"):
            continue
        means = _norm(v.get("means"))
        if "grain" in means and not GRAIN_NEGATED.search(means):
            words.add(_norm(v["term"]))
    return words


def _asks_for_grain(look, taxonomy):
    look = GRAIN_NEGATED.sub(" ", _norm(look))
    return any(w in look for w in _grain_words(taxonomy))


def _wants_shallow(layers, finish):
    if finish in NATURAL_FINISHES:
        return True
    for layer, field in SHALLOW_FIELDS:
        v = _norm((layers.get(layer) or {}).get(field))
        if v and any(w in v for w in SHALLOW_WORDS):
            return True
    return False


def _drop_asymmetry(text):
    """Remove the comma/colon pieces of a finish that ask for asymmetry."""
    parts = re.split(r"(\s*[,;:]\s*)", str(text or ""))
    keep, changed = [], False
    for i in range(0, len(parts), 2):
        piece = parts[i]
        if "asymmetr" in piece.lower():
            changed = True
            continue
        if keep:
            keep.append(parts[i - 1])
        keep.append(piece)
    out = "".join(keep).strip(" ,;:")
    return out, changed


STATIC_WORDS = ("static", "locked", "tripod", "no camera move", "still camera")


def _camera_moves(layers):
    mv = _norm(((layers.get("camera") or {}).get("movement")))
    return bool(mv) and not any(w in mv for w in STATIC_WORDS)


def _has_text(card):
    t = (((card.get("layers") or {}).get("time_output") or {}).get("on_screen_text") or "")
    t = str(t).strip().lower()
    return bool(t) and t not in ("none", "no", "n/a", "-", "no text")


def _field_text(layers, dotted):
    layer, _, field = str(dotted).partition(".")
    return _norm((layers.get(layer) or {}).get(field))


def _conditional_guards(card, neg, avoid, priorities=None):
    """Guards negatives.json 'applies_when' adds on its own (e.g. flat_light on a low-key setup).

    They go at the end of the list, so the card's own first MIN_GUARDS guards stay the protected ones. The
    trigger and exception words live in the rule file, not here. A rule's optional 'priority' is the trim
    priority of its rewrites; it is written into `priorities` (normalised term -> priority) when given."""
    layers = card.get("layers") or {}
    cats = neg.get("by_category") or {}
    have = {_norm(a) for a in avoid}
    out = []
    for group, rule in (neg.get("applies_when") or {}).items():
        if group.startswith("_") or not isinstance(rule, dict):
            continue
        text = " | ".join(_field_text(layers, f) for f in rule.get("fields") or [])
        if not any(_norm(w) in text for w in rule.get("any") or []):
            continue
        fields_unless = rule.get("unless_fields") or rule.get("fields") or []
        stop = " | ".join(_field_text(layers, f) for f in fields_unless)
        if any(_norm(w) in stop for w in rule.get("unless") or []):
            continue
        terms = cats.get(group) or []
        n = rule.get("add")
        for t in (terms[:n] if isinstance(n, int) else terms):
            if isinstance(t, str) and _norm(t) not in have:
                have.add(_norm(t))
                out.append(t)
                if priorities is not None and isinstance(rule.get("priority"), (int, float)):
                    priorities[_norm(t)] = rule["priority"]
    return out


def _gather_avoid(card, profile, rules, priorities=None):
    avoid = [a for a in (card.get("avoid") or []) if isinstance(a, str) and a.strip()]
    neg = (rules or {}).get("negatives") or {}
    mid = (profile or {}).get("id")
    if mid:
        extra = ((neg.get("by_model") or {}).get(mid)) or []
        for a in extra:
            if isinstance(a, str) and _norm(a) not in {_norm(x) for x in avoid}:
                avoid.append(a)
    # Text guards only when the shot has text: "correctly spelled text" on a shot with none invites the model
    # to add some.
    if not _has_text(card):
        text_terms = {_norm(t) for t in ((neg.get("by_category") or {}).get("text") or [])}
        avoid = [a for a in avoid if _norm(a) not in text_terms and not _norm(a).endswith(" text")]
    avoid.extend(_conditional_guards(card, neg, avoid, priorities))
    out, seen = [], set()
    for a in avoid:
        n = _norm(a)
        if n not in seen:
            seen.add(n)
            out.append(a.strip())
    return out


# --------------------------------------------------------------------------- main

def compile(card, model_profile=None, rules=None):  # noqa: A001 - name fixed by the spec
    profile = dict(model_profile or {})
    rules = rules or {}
    taxonomy = rules.get("taxonomy") or {}
    trim_cfg = taxonomy.get("trim") or {}
    protect = trim_cfg.get("protect_at_or_above", DEFAULT_PROTECT)
    guard_pri = trim_cfg.get("guard_priority", DEFAULT_GUARD_PRIORITY)
    max_words = profile.get("max_prompt_words") or DEFAULT_MAX_WORDS
    has_negative = bool(profile.get("negative_prompt", False))

    kind = card.get("kind") or "video"
    settings = card.get("settings") or {}
    layers = card.get("layers") or {}
    inputs = [i for i in (card.get("inputs") or []) if isinstance(i, dict)]

    adjustments, warnings, dropped = [], [], []

    # ---------------- params
    params = {}
    model_kind = profile.get("kind")
    if model_kind and model_kind != kind and model_kind in ("video", "image"):
        warnings.append("This card is a {} but the model makes {}s.".format(kind, model_kind))

    aspect = settings.get("aspect")
    if aspect:
        val, why = _fit_aspect(aspect, profile.get("aspects"))
        if why:
            adjustments.append({"param": "aspect_ratio", "from": aspect, "to": val, "reason": why})
        params["aspect_ratio"] = val

    res = settings.get("resolution")
    if res:
        val, why = _fit_resolution(res, profile.get("resolutions"))
        if why:
            adjustments.append({"param": "resolution", "from": res, "to": val, "reason": why})
        params["resolution"] = val

    requested = None
    if kind == "video" and settings.get("duration_s") is not None:
        handles = card.get("handles_s") or 0
        requested = settings["duration_s"] + 2 * handles
        if isinstance(requested, float) and requested.is_integer():
            requested = int(requested)
        val, why = _fit_duration(requested, profile.get("durations"))
        if why:
            adjustments.append({"param": "duration", "from": requested, "to": val, "reason": why})
        params["duration"] = val

    if kind == "video" and "audio" in settings:
        want_audio = bool(settings.get("audio"))
        if want_audio and profile.get("audio") is False:
            adjustments.append({"param": "audio", "from": True, "to": False,
                                "reason": "This model has no native audio; add sound in post."})
            want_audio = False
        if profile.get("audio") or want_audio:
            params["audio"] = want_audio

    refs_cfg = profile.get("refs")
    img_limit = refs_cfg.get("image") if isinstance(refs_cfg, dict) else None
    refs = []
    start = end = source = None
    for inp in inputs:
        role, asset = inp.get("as"), inp.get("asset")
        if role == "start_frame":
            start = asset
        elif role == "end_frame":
            end = asset
        elif role == "source":
            if source is not None:
                warnings.append("Only one source video can be edited; {} is left out.".format(asset))
                continue
            source = asset
        else:
            refs.append(asset)
    if source is not None and kind != "video":
        warnings.append("A source video is for video cards; it is sent as a reference instead.")
        refs.insert(0, source)
        source = None
    if source is not None:
        params["source_video"] = source
        if start or end or refs:
            warnings.append("Editing a source video takes that one video only; the other inputs are left out.")
            start = end = None
            refs = []
    if kind == "image" and (start or end):
        for a in (start, end):
            if a:
                refs.append(a)
        start = end = None
    if start and profile.get("start_frame") is False:
        if img_limit:
            refs.insert(0, start)
            adjustments.append({"param": "start_image", "from": start, "to": None,
                                "reason": "This model has no start frame; the image is sent as a reference instead."})
        else:
            adjustments.append({"param": "start_image", "from": start, "to": None,
                                "reason": "This model takes no start frame or image reference; the input is dropped."})
        start = None
    if end and profile.get("end_frame") is False:
        adjustments.append({"param": "end_image", "from": end, "to": None,
                            "reason": "This model has no end frame; the input is dropped."})
        end = None
    if end and not start:
        warnings.append("An end frame without a start frame is refused by many models.")
    if start:
        params["start_image"] = start
    if end:
        params["end_image"] = end
    if refs:
        if img_limit is not None and len(refs) > img_limit:
            adjustments.append({"param": "image_references", "from": len(refs), "to": img_limit,
                                "reason": "This model takes at most {} image references; extra ones are dropped.".format(img_limit)})
            refs = refs[:img_limit]
        if refs:
            params["image_references"] = refs

    motion_only = bool(start) and kind == "video"
    edit_source = source is not None
    finish = _preset_finish(card, rules)
    if finish is None and str((layers.get("light_look") or {}).get("finish") or "").strip():
        finish = "natural"  # no preset table: a filled finish field means a natural look

    # A symmetrical frame asked for in the composition outranks the generic finish's asymmetry.
    symmetric = bool(SYMMETRY_RE.search(_norm((layers.get("camera") or {}).get("composition"))))
    if symmetric:
        ll0 = layers.get("light_look") or {}
        trimmed, changed = _drop_asymmetry(ll0.get("finish"))
        if changed:
            layers = dict(layers)
            layers["light_look"] = dict(ll0, finish=trimmed)
            warnings.append("The composition asks for symmetry, so the asymmetry wording was left out of the "
                            "finish.")

    # ---------------- prompt fields
    items = []
    idx = 0
    for group, fields in ORDER:
        for field in fields:
            layer = FIELD_LAYER.get(field, group)
            key = "{}.{}".format(layer, field)
            raw = (layers.get(layer) or {}).get(field)
            text = _fragment(key, raw)
            if not text:
                continue
            if kind == "image" and key in IMAGE_SKIP:
                dropped.append({"field": key, "reason": "not used for a still image"})
                continue
            if edit_source and key in EDIT_SKIP:
                dropped.append({"field": key, "reason": "the source video already sets this"})
                continue
            if motion_only and key not in MOTION_KEEP:
                dropped.append({"field": key, "reason": "the start frame already shows this"})
                continue
            if key == "time_output.audio" and not params.get("audio"):
                dropped.append({"field": key, "reason": "no native audio for this shot; sound is added in post"})
                continue
            pri = _priority(taxonomy, key)
            if edit_source and key.startswith("light_look."):
                # what changes is the point of an edit: light and look are trimmed last
                if pri < protect:  # trimmed last, but still trimmable; already-protected fields stay protected
                    pri = min(protect - 1, max(pri, 80 + pri // 5))
            items.append({"key": key, "group": group, "text": text,
                          "priority": pri, "idx": idx})
            idx += 1

    # A place with no planes reads as a flat backdrop behind a pasted-in subject. Only live-action looks
    # (or an unknown preset) need the planes; a clean graphic or product shot may be flat on purpose.
    world = layers.get("world") or {}
    if (not motion_only and not edit_source and finish in NATURAL_FINISHES + (None,) and str(world.get("environment") or "").strip()
            and not any(str(world.get(k.split(".", 1)[1]) or "").strip() for k in DEPTH_FIELDS)):
        warnings.append("No depth planes: add a foreground and a background (near or far) so the subject "
                        "sits inside the place, not in front of a flat backdrop.")

    # ---------------- avoid
    auto_pri = {}  # auto-added guards with their own (lower) trim priority
    avoid = _gather_avoid(card, profile, rules, auto_pri)
    ll = layers.get("light_look") or {}
    look = "{} {}".format(ll.get("texture") or "", ll.get("finish") or "")
    if _asks_for_grain(look, taxonomy):
        clash = [a for a in avoid if any(w in _norm(a) for w in GRAIN_GUARD_WORDS)]
        if clash:
            avoid = [a for a in avoid if a not in clash]
            warnings.append("Dropped the avoid item(s) {} because the look asks for grain; a 'noise-free' "
                            "guard would fight it.".format(", ".join(repr(a) for a in clash)))
    if symmetric:
        clash = [a for a in avoid if "symmetry" in _norm(a) and "asymmetr" not in _norm(a)]
        if clash:
            avoid = [a for a in avoid if a not in clash]
            warnings.append("Dropped the avoid item(s) {} because the composition asks for symmetry."
                            .format(", ".join(repr(a) for a in clash)))
    unguarded = []
    negative_prompt = None
    if has_negative:
        negative_prompt = ", ".join(avoid) if avoid else None
    else:
        lookup = _rewrite_lookup(rules.get("positive_rewrites"))
        moving = kind == "video" and _camera_moves(layers)
        shallow = _wants_shallow(layers, finish)
        field_text = " ".join(it["text"] for it in items)
        used = set()
        for term in avoid:
            pos = None
            if moving:
                pos = lookup.get(_rkey(term) + " (moving camera)")
            if shallow and not pos:
                pos = lookup.get(_rkey(term) + " (shallow focus)")
            pos = pos or lookup.get(_rkey(term))
            if not pos:
                unguarded.append(term)
                continue
            if _norm(pos) in used:
                continue
            if _contained(pos, field_text):
                continue  # the fields already say it (e.g. the finish carries the same wording)
            used.add(_norm(pos))
            items.append({"key": "avoid:" + term, "group": "guard", "text": pos,
                          "priority": auto_pri.get(_norm(term), guard_pri), "idx": idx, "term": term,
                          "auto": _norm(term) in auto_pri})
            idx += 1

    # ---------------- trim
    def build():
        return _assemble(items)

    prompt = build()
    while _words(prompt) > max_words:
        cands = [it for it in items if it["priority"] < protect]
        # Keep the first MIN_GUARDS avoid guards (the card's own, most important ones) while anything else
        # optional can still go: dropping every guard is how unwanted artefacts creep back in.
        # Auto-added guards with their own priority are never in that protected set.
        guards = [it for it in cands if it["key"].startswith("avoid:") and not it.get("auto")]
        keep = {id(it) for it in sorted(guards, key=lambda it: it["idx"])[:MIN_GUARDS]}
        if any(id(it) not in keep for it in cands):
            cands = [it for it in cands if id(it) not in keep]
        if not cands:
            warnings.append("The prompt is {} words, over this model's {}-word limit, even after "
                            "dropping every optional field. Shorten the subject, action or beats."
                            .format(_words(prompt), max_words))
            break
        victim = min(cands, key=lambda it: (it["priority"], -it["idx"]))
        items.remove(victim)
        if victim["key"].startswith("avoid:"):
            unguarded.append(victim["term"])
            dropped.append({"field": victim["key"], "reason": "trimmed to fit {} words".format(max_words)})
        else:
            dropped.append({"field": victim["key"], "reason": "trimmed to fit {} words".format(max_words)})
        prompt = build()

    return {
        "prompt": prompt,
        "negative_prompt": negative_prompt,
        "params": params,
        "adjustments": adjustments,
        "unguarded": unguarded,
        "dropped_fields": dropped,
        "word_count": _words(prompt),
        "max_prompt_words": max_words,
        "model": profile.get("id"),
        "motion_only": motion_only,
        "edit_source": edit_source,
        "warnings": warnings,
        "requested_duration_s": requested,
    }


compile_card = compile


def __getattr__(name):  # re-export the CLI functions that live in cards.py (lazy, no cycle)
    if name in ("cli_card_new", "cli_card_validate", "cli_card_compile", "cli_refine_save"):
        from shotcraft import cards
        return getattr(cards, name)
    raise AttributeError(name)
