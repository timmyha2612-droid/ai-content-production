"""Credit budget for a project (project.json "budget"): status, the spend check, and a small ledger.

Rules (SPEC §0.3, §7): one job over `threshold_single_job`, or over what is left of the budget, needs the
user's own words (--user-said). With no total budget set, only the single-job threshold applies.
Every change is also appended to <project>/.shotcraft/ledger.jsonl.

API:
    status(project) -> {"credits", "threshold_single_job", "spent", "reserved", "remaining"}
                       (remaining = credits - spent - reserved, or None with no total budget)
    check(project, credits, user_said=None) -> {"ok": bool, "needs_user_said": bool, "reason": str, ...status}
                       ok is True when within limits, or when over them and user_said was given
    require(project, credits, user_said=None) -> dict     like check, raises Refused when not ok
    reserve(project, credits, gen_id=None, note=None) -> status    hold credits for a submitted job
    commit(project, reserved, actual, gen_id=None) -> status       release the hold, add the actual spend
    release(project, credits, gen_id=None, note=None) -> status    give back a hold (failed/canceled job)
    ledger(project) -> list
    set_budget(project, credits=None, threshold=None, user_said=None) -> status   the total and the single-job
                       threshold settled at intake; needs the user's words, records a decision
"""
from . import Refused, jsonio, manifest, paths


def _num(v, default=0):
    try:
        return float(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _clean(x):
    if x is None:
        return None
    return int(x) if float(x).is_integer() else round(x, 3)


def _budget(data):
    b = data.setdefault("budget", {})
    b.setdefault("credits", None)
    b.setdefault("threshold_single_job", 50)
    b.setdefault("spent", 0)
    b.setdefault("reserved", 0)
    return b


def _status_of(b):
    total = b.get("credits")
    spent, reserved = _num(b.get("spent")), _num(b.get("reserved"))
    remaining = None if total is None else _num(total) - spent - reserved
    return {"credits": total, "threshold_single_job": b.get("threshold_single_job"), "spent": _clean(spent),
            "reserved": _clean(reserved), "remaining": _clean(remaining)}


def status(project):
    return _status_of(_budget(manifest.load(project)))


def check(project, credits, user_said=None, generation=False):
    """generation=True for a submit: with confirm_every_generation on (the default), any job that costs
    credits needs the user's yes to its price, not only jobs over the threshold."""
    st = status(project)
    cost = _num(credits, None)
    if cost is None or cost < 0:
        raise Refused("Credits must be a number of 0 or more.")
    reasons = []
    if generation and cost > 0:
        from . import config
        if config.load().get("confirm_every_generation", True):
            reasons.append("every generation is priced first and needs the user's yes (about %s credits)"
                           % _clean(cost))
    thr = st.get("threshold_single_job")
    if thr is not None and cost > _num(thr):
        reasons.append("%s credits is over the single-job threshold of %s" % (_clean(cost), thr))
    if st["remaining"] is not None and cost > st["remaining"]:
        reasons.append("%s credits is more than the %s left in the budget" % (_clean(cost), st["remaining"]))
    said = bool((user_said or "").strip())
    out = dict(st)
    out["cost"] = _clean(cost)
    if not reasons:
        out.update({"ok": True, "needs_user_said": False, "reason": "within budget"})
    else:
        reason = "; ".join(reasons)
        out.update({"ok": said, "needs_user_said": True,
                    "reason": reason + (" (the user agreed)" if said else ". Ask the user and pass their words "
                                        "with --user-said.")})
    return out


def require(project, credits, user_said=None):
    res = check(project, credits, user_said)
    if not res["ok"]:
        raise Refused(res["reason"])
    return res


def _change(project, field_deltas, entry):
    data = manifest.load(project)
    b = _budget(data)
    for field, delta in field_deltas.items():
        b[field] = _clean(max(0.0, _num(b.get(field)) + delta))
    manifest.save(project, data)
    entry["at"] = jsonio.now_iso()
    jsonio.append_jsonl(paths.ledger_file(project), entry)
    return _status_of(b)


def reserve(project, credits, gen_id=None, note=None):
    c = _num(credits)
    return _change(project, {"reserved": c}, {"op": "reserve", "credits": _clean(c), "gen": gen_id, "note": note})


def commit(project, reserved, actual, gen_id=None):
    r, a = _num(reserved), _num(actual)
    return _change(project, {"reserved": -r, "spent": a},
                   {"op": "commit", "released": _clean(r), "credits": _clean(a), "gen": gen_id})


def release(project, credits, gen_id=None, note=None):
    c = _num(credits)
    return _change(project, {"reserved": -c}, {"op": "release", "credits": _clean(c), "gen": gen_id, "note": note})


def ledger(project):
    return jsonio.read_jsonl(paths.ledger_file(project))


def set_budget(project, credits=None, threshold=None, user_said=None):
    if not (user_said or "").strip():
        raise Refused("Setting the budget needs the user's own words (--user-said).")
    if credits is None and threshold is None:
        raise Refused("Give --credits, --threshold or both.")
    for name, v in (("credits", credits), ("threshold", threshold)):
        if v is not None and (_num(v, None) is None or _num(v) < 0):
            raise Refused("--%s must be a number of 0 or more." % name)
    data = manifest.load(project)
    b = _budget(data)
    old = (b.get("credits"), b.get("threshold_single_job"))
    if credits is not None:
        b["credits"] = _clean(_num(credits))
    if threshold is not None:
        b["threshold_single_job"] = _clean(_num(threshold))
    data["decisions"].append({"at": jsonio.now_iso(), "stage": None,
                              "text": "Budget set: %s credits total, single-job threshold %s (was %s / %s)"
                                      % (b["credits"], b["threshold_single_job"], old[0], old[1]),
                              "user_said": user_said.strip()})
    manifest.save(project, data)
    jsonio.append_jsonl(paths.ledger_file(project), {"op": "set", "credits": b["credits"],
                                                     "threshold": b["threshold_single_job"], "at": jsonio.now_iso()})
    return _status_of(b)
