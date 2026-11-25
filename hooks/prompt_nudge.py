#!/usr/bin/env python3
"""shotcraft UserPromptSubmit hook (SPEC section 7): in a session bound to a shotcraft project, when the
prompt reads like a correction or a preference, remind Claude to log it in the lessons inbox (under 200
characters). Silent otherwise (other sessions pay nothing) and on any failure; always exits 0."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")

# Only prompts that sound like a correction or a stated preference get the reminder.
CORRECTION = re.compile(r"\b(no|nope|nah|not|don'?t|do not|never|always|instead|actually|wrong|should(n'?t)?|"
                        r"prefer|rather|avoid|stop|hate|too \w+|less \w+|looks? (off|wrong|bad|fake)|"
                        r"remember|next time|from now on|i (don'?t|do not) (want|like))\b", re.I)

NUDGE = ("shotcraft: if the user just corrected you or explained a preference, log it: "
         "sc.py lessons add \"<what they said>\" (--kind general|project|model).")


def main():
    try:
        raw = sys.stdin.read() if not sys.stdin.isatty() else ""
        data = json.loads(raw) if raw.strip() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}
    try:
        if SCRIPTS not in sys.path:
            sys.path.insert(0, SCRIPTS)
        from shotcraft import paths, project
        sid = data.get("session_id") or None
        # only in a session bound to a shotcraft project (no global fallback: other sessions stay quiet), and
        # only when the prompt reads like a correction or a preference
        if not sid or not os.path.isfile(paths.session_file(sid)):
            return 0
        if not CORRECTION.search(str(data.get("prompt") or "").replace("\u2019", "'")):
            return 0
        if project.active_project(sid):
            sys.stdout.write(NUDGE[:199] + "\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        pass
    sys.exit(0)
