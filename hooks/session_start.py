#!/usr/bin/env python3
"""shotcraft SessionStart hook (SPEC section 7).

  - If `higgsfield` is installed and ~/.shotcraft/scout/last.json is missing or older than 20 hours, run
    `sc.py scout check --json` (12 s timeout).
  - Print one line when the last check found new, removed or changed models:
    "N new Higgsfield models since <date> — say 'run model-scout' to review".
  - Flag routing rows whose checked_at is older than 30 days (rules/routing.json, falling back to the
    checked_at of the model a row names in rules/models.json).
  - Print the active project and its open stage.
Silent on any failure: it never prints a traceback and always exits 0.
"""
import datetime
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(PLUGIN_ROOT, "scripts")
SC = os.path.join(SCRIPTS, "sc.py")

SCOUT_MAX_AGE_H = 20
SCOUT_TIMEOUT_S = 12
ROUTING_MAX_AGE_D = 30


def _core():
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    from shotcraft import paths, project
    return paths, project


def _parse_date(value):
    if not value or not isinstance(value, str):
        return None
    v = value.strip().replace("Z", "+00:00")
    for fn in (lambda s: datetime.datetime.fromisoformat(s),
               lambda s: datetime.datetime.strptime(s[:10], "%Y-%m-%d")):
        try:
            d = fn(v)
            if d.tzinfo is not None:
                d = d.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            return d
        except Exception:
            continue
    return None


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _scout_age_hours(path, data):
    when = None
    if isinstance(data, dict):
        for k in ("timestamp", "checked_at", "at", "time"):
            when = _parse_date(data.get(k))
            if when:
                break
    if when is None:
        try:
            when = datetime.datetime.fromtimestamp(os.path.getmtime(path), datetime.timezone.utc).replace(tzinfo=None)
        except Exception:
            return None
    return (datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None) - when).total_seconds() / 3600.0


def _count(v):
    if isinstance(v, (list, tuple, dict)):
        return len(v)
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        return int(v)
    return 0


def scout_lines(paths):
    lines = []
    last = os.path.join(paths.scout_dir(), "last.json")
    data = _read_json(last)
    if shutil.which("higgsfield"):
        age = _scout_age_hours(last, data) if os.path.exists(last) else None
        if age is None or age > SCOUT_MAX_AGE_H:
            try:
                subprocess.run([sys.executable, SC, "scout", "check", "--json"], stdin=subprocess.DEVNULL,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=SCOUT_TIMEOUT_S)
            except Exception:
                pass
            data = _read_json(last)
    if not isinstance(data, dict) or data.get("reviewed") or data.get("acknowledged"):
        return lines
    new, removed, changed = (_count(data.get(k)) for k in ("new", "removed", "changed"))
    if new or removed or changed:
        since = data.get("since") or data.get("previous") or data.get("timestamp") or data.get("checked_at")
        d = _parse_date(since) if isinstance(since, str) else None
        when = d.strftime("%Y-%m-%d") if d else "the last check"
        parts = []
        if new:
            parts.append("%d new" % new)
        if removed:
            parts.append("%d removed" % removed)
        if changed:
            parts.append("%d changed" % changed)
        lines.append("shotcraft: %s Higgsfield models since %s — say 'run model-scout' to review."
                     % (", ".join(parts), when))
    return lines


def _load_rules(name):
    try:
        if SCRIPTS not in sys.path:
            sys.path.insert(0, SCRIPTS)
        from shotcraft import rules
        return rules.load(name)
    except Exception:
        return _read_json(os.path.join(PLUGIN_ROOT, "rules", name if name.endswith(".json") else name + ".json"))


def _model_dates(models):
    out = {}
    try:
        for prov in (models or {}).get("providers", {}).values():
            for mid, m in (prov.get("models") or {}).items():
                if isinstance(m, dict) and m.get("checked_at"):
                    out[mid] = m["checked_at"]
    except Exception:
        pass
    return out


def routing_lines():
    routing = _load_rules("routing")
    if not isinstance(routing, dict):
        return []
    model_dates = _model_dates(_load_rules("models"))
    now = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    stale, oldest = set(), None
    for need, row in (routing.get("use_cases") or {}).items():
        if not isinstance(row, dict):
            continue
        dates = []
        if row.get("checked_at"):
            dates.append(row["checked_at"])
        for tier in ("draft", "final", "upscale"):
            for entry in row.get(tier) or []:
                if isinstance(entry, dict):
                    mid = entry.get("model") or entry.get("id")
                    if entry.get("checked_at"):
                        dates.append(entry["checked_at"])
                    elif mid in model_dates:
                        dates.append(model_dates[mid])
                elif isinstance(entry, str) and entry in model_dates:
                    dates.append(model_dates[entry])
        for ds in dates:
            d = _parse_date(ds)
            if d and (now - d).days > ROUTING_MAX_AGE_D:
                stale.add(need)
                if oldest is None or d < oldest:
                    oldest = d
    if not stale:
        return []
    return ["shotcraft: %d routing row%s last checked more than %d days ago (oldest %s) — say 'run model-scout' "
            "to refresh." % (len(stale), "" if len(stale) == 1 else "s", ROUTING_MAX_AGE_D,
                             oldest.strftime("%Y-%m-%d"))]


def project_lines(paths, project, session_id):
    sid = session_id or os.environ.get("CLAUDE_SESSION_ID") or os.environ.get("CLAUDE_CODE_SESSION_ID") or None
    from_session = bool(sid) and os.path.isfile(paths.session_file(sid))
    proj = project.active_project(sid)
    if not proj:
        return []
    try:
        st = project.status(proj)
        name = st.get("name") or os.path.basename(proj)
        opened = ", ".join(st.get("open") or [])
        stage = ("open stage: %s" % opened) if opened else (
            "no stage open, next: %s" % st["next"] if st.get("next") else "every stage is closed")
        track = st.get("track") or "?"
    except Exception:
        name, stage, track = os.path.basename(proj), "stage state unreadable", "?"
    where = "active project" if from_session else "last opened project"
    return ["shotcraft: %s \"%s\" (%s track, %s) at %s." % (where, name, track, stage, proj)]


def export_session_id(session_id):
    """Give later Bash calls the same session id the hooks see, so sc.py and the hooks agree on the
    active project. Claude Code offers $CLAUDE_ENV_FILE to SessionStart hooks for this."""
    env_file = os.environ.get("CLAUDE_ENV_FILE")
    if not env_file or not session_id or not re.match(r"^[\w.-]+$", str(session_id)):
        return
    try:
        with open(env_file, "a", encoding="utf-8") as fh:
            fh.write("export CLAUDE_SESSION_ID=%s\n" % session_id)
    except Exception:
        pass


def main():
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    out = []
    try:
        paths, project = _core()
    except Exception:
        return 0
    export_session_id(data.get("session_id"))
    for fn in (lambda: scout_lines(paths), routing_lines,
               lambda: project_lines(paths, project, data.get("session_id"))):
        try:
            out.extend(fn())
        except Exception:
            pass
    if out:
        try:
            sys.stdout.write("\n".join(out) + "\n")
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        pass
    sys.exit(0)
