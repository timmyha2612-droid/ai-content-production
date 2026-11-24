"""Where shotcraft keeps things.

API:
    plugin_root() -> str               the plugin folder (holds rules/, skills/, scripts/)
    rules_dir() -> str                 plugin default rules (rules/*.json)
    user_dir() -> str                  ~/.shotcraft, or $SHOTCRAFT_HOME (tests use a temp dir)
    user_rules_dir() -> str            ~/.shotcraft/rules   (personal overrides)
    config_file() -> str               ~/.shotcraft/config.json
    sessions_dir() -> str              ~/.shotcraft/sessions
    session_file(session_id) -> str    ~/.shotcraft/sessions/<id>.json
    active_file() -> str               ~/.shotcraft/active.json (fallback active project)
    scout_dir() -> str                 ~/.shotcraft/scout
    user_lessons_file() -> str         ~/.shotcraft/lessons.md (lessons logged with no project)
    project_meta_dir(project) -> str   <project>/.shotcraft
    project_rules_dir(project) -> str  <project>/.shotcraft/rules
    manifest_file(project) -> str      <project>/project.json
    stages_file(project) -> str        <project>/.shotcraft/stages.json
    qa_dir(project, stage) -> str      <project>/.shotcraft/qa/<stage>
    project_lessons_file(project)      <project>/.shotcraft/lessons.md
    ledger_file(project) -> str        <project>/.shotcraft/ledger.jsonl (budget history)
    rel_to(project, path) -> str|None  path relative to the project (forward slashes), None if outside
"""
import os

_HERE = os.path.dirname(os.path.abspath(__file__))


def plugin_root():
    """scripts/shotcraft/paths.py -> the plugin root two levels up."""
    env = os.environ.get("SHOTCRAFT_PLUGIN_ROOT")
    if env:
        return os.path.abspath(env)
    return os.path.normpath(os.path.join(_HERE, "..", ".."))


def rules_dir():
    return os.path.join(plugin_root(), "rules")


def user_dir():
    env = os.environ.get("SHOTCRAFT_HOME")
    if env:
        return os.path.abspath(os.path.expanduser(env))
    return os.path.join(os.path.expanduser("~"), ".shotcraft")


def user_rules_dir():
    return os.path.join(user_dir(), "rules")


def config_file():
    return os.path.join(user_dir(), "config.json")


def sessions_dir():
    return os.path.join(user_dir(), "sessions")


def _safe_id(session_id):
    keep = "".join(c for c in str(session_id) if c.isalnum() or c in "-_.")
    return keep.strip(".") or "default"


def session_file(session_id):
    return os.path.join(sessions_dir(), _safe_id(session_id) + ".json")


def active_file():
    return os.path.join(user_dir(), "active.json")


def scout_dir():
    return os.path.join(user_dir(), "scout")


def user_lessons_file():
    return os.path.join(user_dir(), "lessons.md")


def project_meta_dir(project):
    return os.path.join(project, ".shotcraft")


def project_rules_dir(project):
    return os.path.join(project_meta_dir(project), "rules")


def manifest_file(project):
    return os.path.join(project, "project.json")


def stages_file(project):
    return os.path.join(project_meta_dir(project), "stages.json")


def qa_dir(project, stage):
    return os.path.join(project_meta_dir(project), "qa", stage)


def project_lessons_file(project):
    return os.path.join(project_meta_dir(project), "lessons.md")


def ledger_file(project):
    return os.path.join(project_meta_dir(project), "ledger.jsonl")


def rel_to(project, path):
    """Path relative to the project with forward slashes, or None when it is outside the project."""
    proj = os.path.realpath(os.path.abspath(project))
    if not os.path.isabs(path):
        path = os.path.join(proj, path)
    full = os.path.realpath(os.path.abspath(path))
    if full == proj:
        return ""
    if not full.startswith(proj + os.sep):
        return None
    return os.path.relpath(full, proj).replace(os.sep, "/")
