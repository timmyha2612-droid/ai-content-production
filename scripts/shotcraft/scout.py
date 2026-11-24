"""Model scout: compare the provider's live model list with rules/models.json (SPEC sections 2, 7 and 8).

check() asks the provider for its live catalog and writes ~/.shotcraft/scout/last.json:
    {"timestamp", "since", "provider", "ok", "error", "live_count", "known_count",
     "new": [{"id", "name", "kind"}], "removed": [{"id", "name"}], "changed": [{"id", "field", "known", "live"}],
     "stale_models": [{"id", "checked_at", "age_days"}], "stale_routing": [{"use_case", "checked_at", "age_days"}],
     "canvas_api_detected": bool, "canvas_evidence": [str], "summary": str}
    new      live ids that models.json does not know
    removed  known ids marked in_model_list: true that the live list no longer has (ids known to be missing from
             `higgsfield model list`, such as the Cinematic Studio ones, are never reported as removed)
    changed  a different display name, or a different kind when both sides say image/video/audio/3d
    stale    model profiles and routing rows whose checked_at is older than 30 days
    canvas   whether a Canvas API seems to exist now (a model or command named canvas). Higgsfield's Canvas had
             no API as of Nov 2026; when this flips, the handoff skill can build boards directly.
The session-start hook reads last.json; the model-scout agent and skill turn it into proposals for the user.

API:
    STALE_DAYS
    last_path() -> str
    load_last() -> dict|None
    check(provider=None, project=None, today=None, write=True, stale_days=STALE_DAYS) -> report
    diff(known, live) -> {"new", "removed", "changed"}
    report(data=None) -> str          plain-English summary of a report (default: last.json)
    cli_scout_check(args) -> exit code    sc.py scout check   (0 even when there are differences; 1 if the
                                                              provider could not be asked)
    cli_scout_report(args) -> exit code   sc.py scout report
"""
import datetime
import json
import os
import re

from . import jsonio, paths, rules

STALE_DAYS = 30
_KINDS = ("image", "video", "audio", "3d")


def last_path():
    return os.path.join(paths.scout_dir(), "last.json")


def load_last():
    try:
        data = jsonio.read_json(last_path(), default=None)
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _norm_kind(k):
    k = str(k or "").strip().lower()
    if not k:
        return None
    for want in _KINDS:
        if want in k:
            return want
    if "speech" in k or "music" in k or "sound" in k:
        return "audio"
    return k


def _norm_name(n):
    return re.sub(r"\s+", " ", str(n or "")).strip().lower()


def diff(known, live):
    """known: {id: profile}; live: [{"id", "name", "kind"}]"""
    live_by = {}
    for m in live or []:
        if isinstance(m, dict) and m.get("id"):
            live_by[str(m["id"])] = m
    new = [{"id": mid, "name": m.get("name"), "kind": _norm_kind(m.get("kind"))}
           for mid, m in sorted(live_by.items()) if mid not in known]
    removed = [{"id": mid, "name": p.get("name")} for mid, p in sorted(known.items())
               if p.get("in_model_list") is True and mid not in live_by]
    changed = []
    for mid, m in sorted(live_by.items()):
        p = known.get(mid)
        if not p:
            continue
        if m.get("name") and p.get("name") and _norm_name(m["name"]) != _norm_name(p["name"]):
            changed.append({"id": mid, "field": "name", "known": p["name"], "live": m["name"]})
        lk, kk = _norm_kind(m.get("kind")), p.get("kind")
        if lk in _KINDS and kk in _KINDS and lk != kk:
            changed.append({"id": mid, "field": "kind", "known": kk, "live": lk})
        if p.get("in_model_list") is False:
            changed.append({"id": mid, "field": "in_model_list", "known": False, "live": True})
    return {"new": new, "removed": removed, "changed": changed}


def _age(checked_at, today):
    try:
        d = datetime.date.fromisoformat(str(checked_at)[:10])
    except ValueError:
        return None
    return (today - d).days


def _today(today):
    if today is None:
        return datetime.date.today()
    if isinstance(today, str):
        return datetime.date.fromisoformat(today[:10])
    return today


def _summary(rep):
    if not rep.get("ok"):
        return "Model check failed: %s" % (rep.get("error") or "unknown error")
    parts = []
    if rep["new"]:
        parts.append("%d new" % len(rep["new"]))
    if rep["removed"]:
        parts.append("%d removed" % len(rep["removed"]))
    if rep["changed"]:
        parts.append("%d changed" % len(rep["changed"]))
    head = ("%s Higgsfield model%s since %s" % (", ".join(parts), "" if (len(rep["new"]) + len(rep["removed"]) +
                                                                         len(rep["changed"])) == 1 else "s",
                                                (rep.get("since") or "the plugin's model list")[:10])
            if parts else "No model changes")
    extra = []
    if rep.get("stale_routing"):
        extra.append("%d routing row(s) not checked for %d+ days" % (len(rep["stale_routing"]), STALE_DAYS))
    if rep.get("stale_models"):
        extra.append("%d model profile(s) not checked for %d+ days" % (len(rep["stale_models"]), STALE_DAYS))
    if rep.get("canvas_api_detected"):
        extra.append("a Canvas API may now exist")
    s = head + (" — say 'run model-scout' to review" if parts or extra else "")
    if extra:
        s += ". Also: " + "; ".join(extra) + "."
    return s


def check(provider=None, project=None, today=None, write=True, stale_days=STALE_DAYS):
    today = _today(today)
    prev = load_last() or {}
    data = rules.load("models", project)
    prov_name = getattr(provider, "name", None) or "higgsfield"
    section = (data.get("providers") or {}).get(getattr(provider, "profile_provider", None) or "higgsfield") or {}
    known = section.get("models") or {}
    rep = {"timestamp": jsonio.now_iso(), "since": prev.get("timestamp"), "provider": prov_name, "ok": True,
           "error": None, "live_count": 0, "known_count": len(known), "new": [], "removed": [], "changed": [],
           "stale_models": [], "stale_routing": [], "canvas_api_detected": False, "canvas_evidence": []}
    if provider is None:
        from .providers import get_provider
        try:
            provider = get_provider(None, project=project)
            rep["provider"] = provider.name
        except Exception as exc:
            rep.update({"ok": False, "error": str(exc)})
    live = None
    if provider is not None:
        if not provider.available():
            rep.update({"ok": False, "error": "the %s CLI is not installed" % provider.name})
        else:
            try:
                live = provider.list_models()
            except Exception as exc:
                rep.update({"ok": False, "error": str(exc)[:500]})
    if live is not None:
        rep["live_count"] = len(live)
        rep.update(diff(known, live))
        for m in live:
            blob = "%s %s" % (m.get("id") or "", m.get("name") or "")
            if "canvas" in blob.lower():
                rep["canvas_evidence"].append("model %s" % (m.get("id") or m.get("name")))
        try:
            help_text = provider.help_text() or ""
        except Exception:
            help_text = ""
        if re.search(r"(?im)^\s*canvas\b", help_text) or re.search(r"\bcanvas\s+(api|board|build|create)",
                                                                   help_text, re.I):
            rep["canvas_evidence"].append("'canvas' in the CLI help")
        try:
            if provider.has_command("canvas"):
                rep["canvas_evidence"].append("a 'canvas' command answers --help")
        except Exception:
            pass
        rep["canvas_api_detected"] = bool(rep["canvas_evidence"])
    for mid, p in sorted(known.items()):
        age = _age(p.get("checked_at") or data.get("checked_at") or "", today)
        if age is None or age > stale_days:
            rep["stale_models"].append({"id": mid, "checked_at": p.get("checked_at"), "age_days": age})
    try:
        from . import routing
        rep["stale_routing"] = routing.stale_rows(stale_days, today=today, project=project)
    except Exception as exc:
        rep["stale_routing"] = []
        rep.setdefault("warnings", []).append("could not read routing.json: %s" % exc)
    rep["summary"] = _summary(rep)
    if write:
        jsonio.write_json(last_path(), rep)
    return rep


def report(data=None):
    data = data if data is not None else load_last()
    if not data:
        return "No model check yet. Run: sc.py scout check"
    lines = ["Model check of %s (%s): %s" % (data.get("timestamp", "?")[:16].replace("T", " "),
                                             data.get("provider"), data.get("summary") or _summary(data))]
    if data.get("new"):
        lines.append("New on the provider (not in shotcraft's models.json):")
        lines += ["  - %s%s%s" % (m["id"], (" (%s)" % m["name"]) if m.get("name") else "",
                                  (", %s" % m["kind"]) if m.get("kind") else "") for m in data["new"]]
    if data.get("removed"):
        lines.append("Gone from the provider's list:")
        lines += ["  - %s (%s)" % (m["id"], m.get("name")) for m in data["removed"]]
    if data.get("changed"):
        lines.append("Changed:")
        lines += ["  - %s %s: %s -> %s" % (c["id"], c["field"], c["known"], c["live"]) for c in data["changed"]]
    if data.get("stale_routing"):
        lines.append("Routing rows to re-check (older than %d days): %s" % (
            STALE_DAYS, ", ".join(r["use_case"] for r in data["stale_routing"])))
    if data.get("stale_models"):
        ids = [m["id"] for m in data["stale_models"]]
        lines.append("Model profiles to re-check: %d (%s%s)" % (len(ids), ", ".join(ids[:8]),
                                                               " ..." if len(ids) > 8 else ""))
    lines.append("Canvas API: %s" % ("may exist now: %s" % "; ".join(data.get("canvas_evidence") or [])
                                     if data.get("canvas_api_detected") else "not seen"))
    if data.get("new") or data.get("removed") or data.get("changed"):
        lines.append("Next: say 'run model-scout' to review and propose updates (personal rules or a PR).")
    return "\n".join(lines)


def _project(args):
    try:
        from . import project
        if getattr(args, "project", None):
            return project.resolve(args.project, getattr(args, "session_id", None))
        return project.active_project(getattr(args, "session_id", None))
    except Exception:
        return None


def cli_scout_check(args):
    rep = check(project=_project(args))
    if getattr(args, "json", False):
        print(json.dumps(rep, indent=2, ensure_ascii=False, default=str))
    else:
        print(report(rep))
    return 0 if rep.get("ok") else 1


def cli_scout_report(args):
    data = load_last()
    if getattr(args, "json", False):
        print(json.dumps(data or {"ok": False, "error": "no model check yet"}, indent=2, ensure_ascii=False))
    else:
        print(report(data))
    return 0 if data else 1
