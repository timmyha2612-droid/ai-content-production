"""Model routing: use case + tier -> ordered model candidates, plus duration and resolution fitting and the
image-first rule (SPEC sections 0.3 and 6). Reads rules/routing.json, rules/models.json and rules/presets.json
through rules.load (plugin < personal < project layers).

API:
    TIERS
    resolve_need(use_case_or_need, project=None) -> (need, preset_id|None, preset|None)
        a preset id (social-vertical) maps to its "need" (video-general); a need is taken as is.
    route(use_case_or_need, tier, kind=None, duration=None, needs=None, project=None, handles=None)
        -> {"need", "use_case", "tier", "kind", "candidates": [...], "best": candidate|None, "notes": [...]}
        candidate: {"model", "name", "kind", "params", "why", "fits", "problems", "notes", "duration",
                    "unconfirmed"}; rows that fit come first, otherwise the routing.json order is kept.
        needs: list or comma text from audio, refs, video_refs, audio_refs, start_frame, end_frame, soul_id, 4k,
               svg, vector, loop, multishot.
    tier_row(need, tier, model_id, project=None) -> the routing.json row for that model, or None
    fit_duration(model, target, handles=0, shortest=True, project=None)
        -> {"target_s", "handles_s", "requested_s", "chosen_s", "trim_s", "trim_plan", "fits", "chain", "reason"}
        model: a profile dict or a model id. Picks the shortest allowed length that covers the shot plus its
        handles; when one take is too short, "chain" holds a plan to cover the shot in several takes.
    fit_resolution(preset, tier, model=None, project=None) -> {"resolution", "wanted", "reason"}
        the preset's size for the tier (board uses the draft size, upscale the delivery size), fitted to the
        model's sizes when a model is given (the smallest size that still covers it).
    image_first_reasons(card, rules_data=None, project=None) -> [plain-English reasons]
        rules_data: the routing.json dict (default: loaded); only its "image_first" block is used.
    image_first(card, rules_data=None, project=None) -> bool
    stale_rows(days=30, today=None, project=None) -> [{"use_case", "checked_at", "age_days"}]
    cli_route(args) -> exit code   (sc.py route --use-case U --tier T [--kind] [--duration] [--needs])
"""
import datetime
import json
import math
import re

from . import Refused, rules

TIERS = ("board", "draft", "final", "upscale")
NEED_WORDS = ("audio", "refs", "video_refs", "audio_refs", "start_frame", "end_frame", "soul_id", "4k", "svg",
              "vector", "loop", "multishot")


# ---------------------------------------------------------------- loading

def _routing(project=None):
    return rules.load("routing", project)


def _models(project=None, provider="higgsfield"):
    data = rules.load("models", project)
    return ((data.get("providers") or {}).get(provider) or {}).get("models") or {}


def _presets(project=None):
    data = rules.load("presets", project)
    table = data.get("presets", data)
    return table if isinstance(table, dict) else {}


def _profile(model, project=None):
    if isinstance(model, dict):
        return model
    prof = dict(_models(project).get(model) or {})
    if prof:
        prof.setdefault("id", model)
    return prof


def resolve_need(use_case_or_need, project=None):
    key = (use_case_or_need or "").strip()
    if not key:
        raise Refused("Name a use case (a preset such as social-vertical) or a need (such as video-general).")
    use_cases = _routing(project).get("use_cases") or {}
    presets = _presets(project)
    if key in presets:
        need = presets[key].get("need")
        if need not in use_cases:
            raise Refused("Preset %s points to need %r, which is not in routing.json." % (key, need))
        return need, key, presets[key]
    if key in use_cases:
        return key, None, None
    raise Refused("Unknown use case or need %r. Presets: %s. Needs: %s." % (
        key, ", ".join(sorted(presets)), ", ".join(sorted(use_cases))))


def tier_row(need, tier, model_id, project=None):
    uc = (_routing(project).get("use_cases") or {}).get(need) or {}
    for row in _tier_rows(uc, tier):
        if row.get("model") == model_id:
            return row
    return None


def _tier_rows(uc, tier):
    rows = uc.get(tier)
    if tier == "board" and not rows:
        rows = uc.get("draft")
    return [r for r in (rows or []) if isinstance(r, dict) and r.get("model")]


# ---------------------------------------------------------------- fitting

def _num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _clean(x):
    if x is None:
        return None
    x = round(float(x), 3)
    return int(x) if x.is_integer() else x


def fit_duration(model, target, handles=0, shortest=True, project=None):
    prof = _profile(model, project)
    spec = prof.get("durations")
    t = _num(target)
    h = _num(handles) or 0.0
    out = {"target_s": _clean(t), "handles_s": _clean(h), "requested_s": None, "chosen_s": None, "trim_s": 0,
           "trim_plan": None, "fits": True, "chain": None, "reason": None}
    if t is None:
        out["reason"] = "no duration asked for"
        return out
    req = t + 2 * h
    out["requested_s"] = _clean(req)
    name = prof.get("name") or prof.get("id") or "this model"
    if not spec:
        out["reason"] = "%s has no duration setting; check the clip length after generation" % name
        return out
    if isinstance(spec, dict):
        lo, hi = _num(spec.get("min")), _num(spec.get("max"))
        allowed = None
    else:
        allowed = sorted(x for x in (_num(v) for v in spec) if x is not None)
        lo, hi = (allowed[0], allowed[-1]) if allowed else (None, None)

    def pick(need):
        if allowed is not None:
            above = [a for a in allowed if a >= need - 1e-9]
            if shortest:
                return above[0] if above else None
            return min(allowed, key=lambda a: (abs(a - need), -a))
        v = float(math.ceil(need - 1e-9))
        if lo is not None and v < lo:
            v = lo
        if hi is not None and v > hi:
            return None
        return v

    chosen = pick(req)
    if chosen is None:
        # one take is too short: plan a chain of takes
        takes = int(math.ceil(req / hi)) if hi else 2
        each = None
        while each is None and takes < 50:
            each = pick(req / takes)
            if each is None:
                takes += 1
        chain_ok = bool(prof.get("start_frame"))
        plan = ("Cover %s s in %d takes of %s s. %s" % (
            _clean(req), takes, _clean(each), "Use the last frame of each take as the start frame of the next, "
            "then cut on matching action." if chain_ok else
            "%s has no start frame, so cut between takes (a cutaway or a change of angle)." % name))
        out.update({"chosen_s": _clean(hi), "fits": False,
                    "chain": {"takes": takes, "each_s": _clean(each), "total_s": _clean(each * takes),
                              "trim_s": _clean(each * takes - req), "start_frame_chaining": chain_ok,
                              "plan": plan},
                    "reason": "%s makes at most %s s per take; the shot needs %s s." % (name, _clean(hi),
                                                                                        _clean(req))})
        return out
    out["chosen_s"] = _clean(chosen)
    trim = chosen - req
    out["trim_s"] = _clean(trim if trim > 0 else 0)
    if trim > 1e-9:
        out["trim_plan"] = "Trim %s s in the edit (from the tail, or split between head and tail)." % _clean(trim)
        out["reason"] = "%s s is the shortest length %s offers that covers %s s." % (_clean(chosen), name,
                                                                                    _clean(req))
    elif trim < -1e-9:
        out["fits"] = False
        out["reason"] = "%s s is %s s shorter than planned." % (_clean(chosen), _clean(-trim))
    else:
        out["reason"] = "exact length"
    return out


def fit_resolution(preset, tier, model=None, project=None):
    preset = preset or {}
    res = preset.get("resolution") or {}
    if not isinstance(res, dict):
        res = {"draft": res, "final": res, "delivery": res}
    key = {"board": "draft", "draft": "draft", "final": "final", "upscale": "delivery"}.get(tier, "final")
    wanted = res.get(key) or res.get("final")
    out = {"resolution": wanted, "wanted": wanted, "reason": "preset size for %s" % tier}
    if model is not None and wanted:
        prof = _profile(model, project)
        allowed = prof.get("resolutions")
        if allowed:
            from . import compiler
            val, why = compiler._fit_resolution(wanted, allowed)
            out["resolution"] = val
            if why:
                out["reason"] = why
    return out


# ---------------------------------------------------------------- image first

def _text_of(card, *keys):
    layers = card.get("layers") or {}
    parts = []
    for key in keys:
        layer, field = key.split(".")
        v = (layers.get(layer) or {}).get(field)
        if isinstance(v, list):
            v = " ".join(str(b.get("what", "")) if isinstance(b, dict) else str(b) for b in v)
        if v:
            parts.append(str(v))
    return " ".join(parts).lower()


def _has_word(text, words):
    for w in words or []:
        if re.search(r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(w.lower()), text):
            return w
    return None


def image_first_reasons(card, rules_data=None, project=None):
    cfg = (rules_data or _routing(project)).get("image_first") or {}
    card = card or {}
    if (card.get("kind") or "video") != "video":
        return []
    roles = [i.get("as") for i in (card.get("inputs") or []) if isinstance(i, dict)]
    if "start_frame" in roles:
        return []
    out = []
    if "board" in (card.get("tier_plan") or []):
        out.append("the card plans a board")
    if (card.get("settings") or {}).get("image_first"):
        out.append("the card is flagged image-first")
    w = _has_word(_text_of(card, "subject.subject", "subject.action", "subject.consistency", "subject.elements"),
                  cfg.get("people_words"))
    if w:
        out.append("people in frame (%s): get the face right on a still first" % w)
    w = _has_word(_text_of(card, "subject.subject", "subject.elements", "subject.wardrobe_props"),
                  cfg.get("accuracy_words"))
    if w or _text_of(card, "time_output.on_screen_text"):
        out.append("%s must look exactly right" % (w or "on-screen text"))
    w = _has_word(_text_of(card, "camera.movement"), cfg.get("complex_moves"))
    if w:
        out.append("complex camera move (%s)" % w)
    dur = _num((card.get("settings") or {}).get("duration_s"))
    lim = _num(cfg.get("min_duration_s"))
    if dur is not None and lim is not None and dur >= lim:
        out.append("long shot (%s s)" % _clean(dur))
    if "end_frame" in roles:
        out.append("it needs an end frame")
    return out


def image_first(card, rules_data=None, project=None):
    return bool(image_first_reasons(card, rules_data, project))


# ---------------------------------------------------------------- route

def _needs_list(needs):
    if not needs:
        return []
    if isinstance(needs, str):
        needs = needs.split(",")
    return [n.strip().lower().replace("-", "_") for n in needs if n and n.strip()]


def _need_problems(prof, needs, row_params):
    probs = []
    refs = prof.get("refs") or {}
    name = prof.get("name") or prof.get("id")
    for n in needs:
        if n == "audio" and not prof.get("audio"):
            probs.append("%s makes no sound" % name)
        elif n in ("refs", "image_refs") and not refs.get("image"):
            probs.append("%s takes no image references" % name)
        elif n == "video_refs" and not refs.get("video"):
            probs.append("%s takes no video references" % name)
        elif n == "audio_refs" and not refs.get("audio"):
            probs.append("%s takes no audio references" % name)
        elif n == "start_frame" and not prof.get("start_frame"):
            probs.append("%s has no start frame" % name)
        elif n in ("end_frame", "loop") and not prof.get("end_frame"):
            probs.append("%s has no end frame (needed for %s)" % (name, n.replace("_", " ")))
        elif n == "soul_id" and not prof.get("soul_id"):
            probs.append("%s does not take a Soul ID" % name)
        elif n == "4k" and "4k" not in [str(r).lower() for r in (prof.get("resolutions") or [])]:
            probs.append("%s does not make 4K" % name)
        elif n in ("svg", "vector") and not (row_params.get("model_type") == "vector"
                                             or row_params.get("output_format") == "svg"):
            probs.append("%s is not set up for vector output here" % name)
        elif n == "multishot" and "multi_shots" not in (prof.get("flags") or []) and \
                "multi-shot" not in " ".join(prof.get("strengths") or []):
            probs.append("%s does not do multi-shot in one job" % name)
    return probs


def route(use_case_or_need, tier, kind=None, duration=None, needs=None, project=None, handles=None):
    if tier not in TIERS:
        raise Refused("Tier must be one of: %s." % ", ".join(TIERS))
    need, preset_id, preset = resolve_need(use_case_or_need, project)
    data = _routing(project)
    uc = (data.get("use_cases") or {}).get(need) or {}
    need_kind = uc.get("kind")
    kind = kind or (preset or {}).get("kind") or need_kind
    nl = _needs_list(needs)
    notes = []
    if kind and need_kind and kind != need_kind and tier != "board":
        notes.append("This need is usually a %s; you asked for a %s." % (need_kind, kind))
    if handles is None:
        handles = (preset or {}).get("handles_s") or 0
    policy = data.get("draft_policy") or {}
    if tier in ("board", "draft") and policy.get("handles") is False:
        handles = 0
    models = _models(project)
    rows = _tier_rows(uc, tier)
    if tier == "upscale" and not rows:
        notes.append("No upscale step for this need. %s" % (data.get("upscale_policy") or ""))
    cands = []
    for i, row in enumerate(rows):
        mid = row["model"]
        prof = dict(models.get(mid) or {})
        params = dict(row.get("params") or {})
        c = {"model": mid, "name": prof.get("name") or mid, "kind": prof.get("kind"), "params": params,
             "why": row.get("why"), "fits": True, "problems": [], "notes": [], "duration": None,
             "unconfirmed": bool(prof.get("unconfirmed")), "order": i}
        if not prof:
            c["fits"] = False
            c["problems"].append("%s is not in models.json (check: higgsfield model get %s)" % (mid, mid))
            cands.append(c)
            continue
        prof.setdefault("id", mid)
        if any("not in the CLI" in u for u in prof.get("unconfirmed") or []):
            c["notes"].append("%s is not in the CLI's model docs; confirm with: higgsfield model get %s" % (
                c["name"], mid))
        if kind and tier != "board" and prof.get("kind") in ("image", "video") and prof["kind"] != kind:
            c["fits"] = False
            c["problems"].append("%s makes %ss, not %ss" % (c["name"], prof["kind"], kind))
        c["problems"] += _need_problems(prof, nl, params)
        if prof.get("kind") == "video" and duration is not None:
            d = fit_duration(prof, duration, handles, shortest=True)
            c["duration"] = d
            if d.get("chain"):
                c["notes"].append(d["reason"] + " " + d["chain"]["plan"])
            elif d.get("trim_plan"):
                c["notes"].append(d["trim_plan"])
        if preset and "resolution" not in params and prof.get("kind") in ("image", "video"):
            fr = fit_resolution(preset, tier, prof)
            if fr["resolution"]:
                c["resolution"] = fr
        if c["problems"]:
            c["fits"] = False
        cands.append(c)
    # fitting rows first; among them, a single take before a chain; otherwise keep the routing order
    cands.sort(key=lambda c: (not c["fits"], bool(c["duration"] and c["duration"].get("chain")), c["order"]))
    for c in cands:
        c.pop("order", None)
    best = next((c for c in cands if c["fits"]), None)
    if rows and best is None:
        notes.append("No row fits every need; the closest is listed first. Relax a need or pick a model with "
                     "--model.")
    if uc.get("notes"):
        notes.append(uc["notes"])
    return {"need": need, "use_case": preset_id, "tier": tier, "kind": kind, "needs": nl,
            "handles_s": handles, "candidates": cands, "best": best, "notes": notes}


# ---------------------------------------------------------------- staleness

def _age_days(checked_at, today=None):
    try:
        d = datetime.date.fromisoformat(str(checked_at)[:10])
    except ValueError:
        return None
    today = today or datetime.date.today()
    if isinstance(today, str):
        today = datetime.date.fromisoformat(today[:10])
    return (today - d).days


def stale_rows(days=30, today=None, project=None):
    data = _routing(project)
    out = []
    default = data.get("checked_at")
    for name, uc in sorted((data.get("use_cases") or {}).items()):
        ca = uc.get("checked_at") or default
        age = _age_days(ca, today) if ca else None
        if age is None or age > days:
            out.append({"use_case": name, "checked_at": ca, "age_days": age})
    return out


# ---------------------------------------------------------------- CLI

def _fmt_params(p):
    return " ".join("%s=%s" % (k, v) for k, v in sorted((p or {}).items()))


def cli_route(args):
    res = route(args.use_case, args.tier, kind=getattr(args, "kind", None),
                duration=getattr(args, "duration", None), needs=getattr(args, "needs", None),
                project=_project_or_none(args))
    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        head = "%s%s, %s tier%s:" % (("%s -> " % res["use_case"]) if res["use_case"] else "", res["need"],
                                     res["tier"], (", %s" % res["kind"]) if res["kind"] else "")
        lines = [head]
        for i, c in enumerate(res["candidates"], 1):
            mark = "" if c["fits"] else "  (does not fit: %s)" % "; ".join(c["problems"])
            size = c.get("resolution", {}).get("resolution") if c.get("resolution") else None
            extra = _fmt_params(c["params"]) or ("resolution=%s" % size if size else "")
            lines.append("  %d. %s%s%s" % (i, c["name"], (" [%s]" % extra) if extra else "", mark))
            if c.get("why"):
                lines.append("     %s" % c["why"])
            d = c.get("duration")
            if d and d.get("chosen_s") is not None and not d.get("chain"):
                lines.append("     Length: %s s for a %s s shot%s." % (
                    d["chosen_s"], d["target_s"], (" plus %s s handles each side" % d["handles_s"])
                    if d.get("handles_s") else ""))
            for n in c["notes"]:
                lines.append("     Note: %s" % n)
        if not res["candidates"]:
            lines.append("  No model to run for this tier.")
        for n in res["notes"]:
            lines.append("Note: %s" % n)
        print("\n".join(lines))
    if res["candidates"] and res["best"] is None:
        return 2
    return 0


def _project_or_none(args):
    try:
        from . import project
        if getattr(args, "project", None):
            return project.resolve(args.project, getattr(args, "session_id", None))
        return project.active_project(getattr(args, "session_id", None))
    except Exception:
        return None


cli_route_route = cli_route
