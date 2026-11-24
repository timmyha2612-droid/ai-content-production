"""Lessons inbox: corrections and preferences the user gives during a job, decided at the learn stage.

The inbox is plain markdown so people (and Claude) can read it; the guard always lets it be written.
With a project it is <project>/.shotcraft/lessons.md; with none, ~/.shotcraft/lessons.md. One lesson per line:
    - [ ] #3 [general] 2026-11-24 — Keep hooks under 2 seconds
    - [x] #3 [general] 2026-11-24 — Keep hooks under 2 seconds → accepted 2026-11-25: "yes, always"

API:
    KINDS = ("general", "project", "model")
    inbox_path(project=None) -> str
    add(text, kind="general", project=None) -> lesson
    list_lessons(project=None, status=None) -> [ {"n", "kind", "date", "text", "status", "decided_at", "user_said"} ]
    decide(n, decision, user_said, project=None) -> lesson       decision: accept|reject
    open_count(project=None) -> int
"""
import os
import re

from . import Refused, ShotcraftError, jsonio, paths

KINDS = ("general", "project", "model")
_LINE = re.compile(r"^- \[(?P<x>[ xX])\] #(?P<n>\d+) \[(?P<kind>[a-z]+)\] (?P<date>\S+) — (?P<rest>.*)$")
_DECIDED = re.compile(r"^(?P<text>.*) → (?P<status>accepted|rejected) (?P<at>\S+): \"(?P<said>.*)\"$")


def inbox_path(project=None):
    return paths.project_lessons_file(project) if project else paths.user_lessons_file()


def _read(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read().splitlines()
    except FileNotFoundError:
        return ["# Lessons inbox", ""]


def _write(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines).rstrip("\n") + "\n")
    os.replace(tmp, path)


def _parse(line):
    m = _LINE.match(line)
    if not m:
        return None
    rest = m.group("rest")
    item = {"n": int(m.group("n")), "kind": m.group("kind"), "date": m.group("date"), "text": rest,
            "status": "open", "decided_at": None, "user_said": None}
    d = _DECIDED.match(rest)
    if d:
        item.update({"text": d.group("text"), "status": d.group("status"), "decided_at": d.group("at"),
                     "user_said": d.group("said").replace('\\"', '"')})
    return item


def _fmt(item):
    box = " " if item["status"] == "open" else "x"
    line = "- [%s] #%d [%s] %s — %s" % (box, item["n"], item["kind"], item["date"], item["text"])
    if item["status"] != "open":
        line += ' → %s %s: "%s"' % (item["status"], item["decided_at"], item["user_said"].replace('"', '\\"'))
    return line


def list_lessons(project=None, status=None):
    out = []
    for line in _read(inbox_path(project)):
        item = _parse(line)
        if item and (status is None or item["status"] == status):
            out.append(item)
    return out


def add(text, kind="general", project=None):
    text = " ".join(str(text or "").split())
    if not text:
        raise Refused("A lesson needs some text.")
    if kind not in KINDS:
        raise Refused("Kind must be one of: %s." % ", ".join(KINDS))
    path = inbox_path(project)
    lines = _read(path)
    n = max([l["n"] for l in (_parse(x) for x in lines) if l] or [0]) + 1
    item = {"n": n, "kind": kind, "date": jsonio.today(), "text": text, "status": "open", "decided_at": None,
            "user_said": None}
    lines.append(_fmt(item))
    _write(path, lines)
    return item


def decide(n, decision, user_said, project=None):
    decision = {"accept": "accepted", "accepted": "accepted", "reject": "rejected",
                "rejected": "rejected"}.get(str(decision).lower())
    if not decision:
        raise Refused("Decide with accept or reject.")
    said = " ".join(str(user_said or "").split())
    if not said:
        raise Refused("Deciding a lesson needs the user's own words (--user-said).")
    path = inbox_path(project)
    lines = _read(path)
    for i, line in enumerate(lines):
        item = _parse(line)
        if item and item["n"] == int(n):
            item.update({"status": decision, "decided_at": jsonio.today(), "user_said": said})
            lines[i] = _fmt(item)
            _write(path, lines)
            return item
    raise ShotcraftError("No lesson #%s in %s." % (n, path))


def open_count(project=None):
    return len(list_lessons(project, status="open"))
