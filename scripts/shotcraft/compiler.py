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
"negatives" (see rules.compiler_rules()). Missing pieces fall back to safe defaults:
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
DEFAULT_GUARD_PRIORITY = 45

# Prompt order: subject+action -> world -> camera -> light & look -> time/beats -> style.
ORDER = [
    ("subject", ["subject", "action", "wardrobe_props", "elements", "consistency"]),
    ("world", ["environment", "era", "time_of_day", "weather_season", "atmosphere"]),
    ("camera", ["shot_size", "angle", "lens", "dof", "composition", "movement", "movement_speed",
                "camera_look"]),
    ("light_look", ["setup", "quality", "direction", "color_temp", "practicals", "palette_grade",
                    "texture", "mood"]),
    ("time_output", ["beats", "pacing", "loop", "transition_in", "transition_out", "audio",
                     "on_screen_text"]),
    ("style", ["style_ref"]),
]
# style_ref lives in the light_look layer of the card but prints last.
FIELD_LAYER = {"style_ref": "light_look"}

# Fallback priorities (higher = more important). texture, practicals, era, camera_look go first.
DEFAULT_PRIORITY = {
    "subject.subject": 100, "subject.action": 98, "camera.movement": 94,
    "camera.movement_speed": 92, "camera.shot_size": 90, "world.environment": 88,
    "time_output.on_screen_text": 85, "time_output.beats": 84, "world.time_of_day": 82,
    "light_look.setup": 80, "camera.angle": 78, "light_look.mood": 76, "camera.lens": 74,
    "camera.composition": 72, "light_look.style_ref": 70, "time_output.loop": 70,
    "time_output.audio": 68, "subject.elements": 66, "time_output.pacing": 64,
    "world.atmosphere": 62, "light_look.palette_grade": 60, "camera.dof": 58,
    "light_look.color_temp": 56, "light_look.direction": 54, "light_look.quality": 52,
    "world.weather_season": 50, "subject.consistency": 48, "subject.wardrobe_props": 46,
    "time_output.transition_in": 44, "time_output.transition_out": 42,
    "camera.camera_look": 40, "world.era": 30, "light_look.practicals": 20,
    "light_look.texture": 10,
}

IMAGE_SKIP = {"camera.movement", "camera.movement_speed", "time_output.beats", "time_output.pacing",
              "time_output.loop", "time_output.transition_in", "time_output.transition_out",
              "time_output.audio"}
MOTION_KEEP = {"subject.action", "camera.movement", "camera.movement_speed", "time_output.beats",
               "time_output.pacing", "time_output.loop", "time_output.transition_in",
               "time_output.transition_out", "time_output.audio"}

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
                parts.append("{}s: {}".format(t, what) if t else what)
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
        if '"' in v or "“" in v or "text" in v.lower():
            return v
        return 'on-screen text reads "{}"'.format(v)
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
            sentences.append(", ".join(cur))
            cur = []
        cur_group = it["group"]
        cur.append(it["text"])
    if cur:
        sentences.append(", ".join(cur))
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

def _rewrite_lookup(rewrites):
    return {_norm(k): v for k, v in (rewrites or {}).items()
            if isinstance(v, str) and not str(k).startswith("_")}


STATIC_WORDS = ("static", "locked", "tripod", "no camera move", "still camera")


def _camera_moves(layers):
    mv = _norm(((layers.get("camera") or {}).get("movement")))
    return bool(mv) and not any(w in mv for w in STATIC_WORDS)


def _gather_avoid(card, profile, rules):
    avoid = [a for a in (card.get("avoid") or []) if isinstance(a, str) and a.strip()]
    neg = (rules or {}).get("negatives") or {}
    mid = (profile or {}).get("id")
    if mid:
        extra = ((neg.get("by_model") or {}).get(mid)) or []
        for a in extra:
            if isinstance(a, str) and _norm(a) not in {_norm(x) for x in avoid}:
                avoid.append(a)
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
    start = end = None
    for inp in inputs:
        role, asset = inp.get("as"), inp.get("asset")
        if role == "start_frame":
            start = asset
        elif role == "end_frame":
            end = asset
        else:
            refs.append(asset)
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
            if motion_only and key not in MOTION_KEEP:
                dropped.append({"field": key, "reason": "the start frame already shows this"})
                continue
            if key == "time_output.audio" and not params.get("audio"):
                dropped.append({"field": key, "reason": "no native audio for this shot; sound is added in post"})
                continue
            items.append({"key": key, "group": group, "text": text,
                          "priority": _priority(taxonomy, key), "idx": idx})
            idx += 1

    # ---------------- avoid
    avoid = _gather_avoid(card, profile, rules)
    unguarded = []
    negative_prompt = None
    if has_negative:
        negative_prompt = ", ".join(avoid) if avoid else None
    else:
        lookup = _rewrite_lookup(rules.get("positive_rewrites"))
        moving = kind == "video" and _camera_moves(layers)
        used = set()
        for term in avoid:
            pos = None
            if moving:
                pos = lookup.get(_norm(term) + " (moving camera)")
            pos = pos or lookup.get(_norm(term))
            if not pos:
                unguarded.append(term)
                continue
            if _norm(pos) in used:
                continue
            used.add(_norm(pos))
            items.append({"key": "avoid:" + term, "group": "guard", "text": pos,
                          "priority": guard_pri, "idx": idx, "term": term})
            idx += 1

    # ---------------- trim
    def build():
        return _assemble(items)

    prompt = build()
    while _words(prompt) > max_words:
        cands = [it for it in items if it["priority"] < protect]
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
        "warnings": warnings,
        "requested_duration_s": requested,
    }


compile_card = compile


def __getattr__(name):  # re-export the CLI functions that live in cards.py (lazy, no cycle)
    if name in ("cli_card_new", "cli_card_validate", "cli_card_compile", "cli_refine_save"):
        from shotcraft import cards
        return getattr(cards, name)
    raise AttributeError(name)
