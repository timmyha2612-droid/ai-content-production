"""User config at ~/.shotcraft/config.json (SPEC §2).

API:
    DEFAULTS                            the default config dict
    load() -> dict                      config merged over DEFAULTS (never fails on a missing file)
    save(cfg)                           atomic write
    exists() -> bool                    has the first run happened (config file present)
    projects_root(cfg=None) -> str|None the folder new projects go in (absolute), or None
    setup(projects_root=None) -> dict   first-run: set projects_root, make folders, first_run_done=True
"""
import copy
import os

from . import Refused, jsonio, paths

DEFAULTS = {
    "projects_root": None,
    "provider": "higgsfield",
    "default_threshold_credits": 50,
    # Every generation shows its live price and waits for the user's yes, whatever its size. Set to false to
    # let jobs under the single-job threshold go without asking.
    "confirm_every_generation": True,
    "currency_note": None,
    "first_run_done": False,
}


def load():
    cfg = copy.deepcopy(DEFAULTS)
    data = jsonio.read_json(paths.config_file(), default={}) or {}
    if isinstance(data, dict):
        cfg.update(data)
    return cfg


def save(cfg):
    jsonio.write_json(paths.config_file(), cfg)


def exists():
    return os.path.isfile(paths.config_file())


def projects_root(cfg=None):
    cfg = cfg if cfg is not None else load()
    root = cfg.get("projects_root")
    if not root:
        return None
    return os.path.abspath(os.path.expanduser(root))


def setup(projects_root=None):
    """Create or update the config. projects_root is required unless one is already set."""
    cfg = load()
    if projects_root:
        cfg["projects_root"] = os.path.abspath(os.path.expanduser(projects_root))
    if not cfg.get("projects_root"):
        raise Refused("No projects folder set yet. Ask the user where projects should live, then run: "
                      "sc.py setup --projects-root DIR")
    for d in (paths.user_dir(), paths.user_rules_dir(), paths.sessions_dir(), paths.scout_dir(),
              cfg["projects_root"]):
        os.makedirs(d, exist_ok=True)
    cfg["first_run_done"] = True
    save(cfg)
    return cfg
