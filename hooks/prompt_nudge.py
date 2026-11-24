#!/usr/bin/env python3
"""shotcraft UserPromptSubmit hook (SPEC section 7): while a project is active, remind Claude to log the
user's corrections and preferences in the lessons inbox. The reminder stays under 200 characters.
Silent when no project is active or on any failure; always exits 0."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.join(os.path.dirname(HERE), "scripts")

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
        from shotcraft import project
        if project.active_project(data.get("session_id") or None):
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
