"""Layered rules loader.

Rule files are JSON. They are read from up to three layers, later layers winning:

    1. plugin defaults   <plugin root>/rules/<name>.json
    2. personal rules    ~/.shotcraft/rules/<name>.json
    3. project rules     <project>/.shotcraft/rules/<name>.json

Merging (deep_merge):
    - dicts merge key by key, recursively;
    - any other value (lists included) replaces the value below it;
    - a key ending in "+" appends: {"universal+": ["x"]} adds "x" to the list "universal"
      below it instead of replacing it (duplicates are skipped).

Stdlib only.
"""

import copy
import json
import os
from pathlib import Path

try:  # paths.py is written alongside this module; import defensively.
    from shotcraft import paths as _paths  # type: ignore
except Exception:  # pragma: no cover - depends on the rest of the package
    _paths = None


RULE_NAMES = ("taxonomy", "negatives", "positive_rewrites", "models", "routing",
              "presets", "tracks", "stages")


class RulesError(Exception):
    """A rule file exists but cannot be read as JSON."""


# --------------------------------------------------------------------------- locations

def plugin_root():
    """The plugin's root folder (the one holding rules/ and scripts/)."""
    if _paths is not None and hasattr(_paths, "plugin_root"):
        try:
            return Path(_paths.plugin_root())
        except Exception:
            pass
    env = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if env and (Path(env) / "rules").is_dir():
        return Path(env)
    # scripts/shotcraft/rules.py -> plugin root is two folders above scripts/
    return Path(__file__).resolve().parents[2]


def user_home():
    """~/.shotcraft, or $SHOTCRAFT_HOME (paths.user_dir() when available)."""
    for fn in ("user_dir", "user_home"):
        f = getattr(_paths, fn, None) if _paths is not None else None
        if callable(f):
            try:
                return Path(f())
            except Exception:
                pass
    env = os.environ.get("SHOTCRAFT_HOME")
    if env:
        return Path(env).expanduser()
    return Path.home() / ".shotcraft"


def plugin_rules_dir():
    return plugin_root() / "rules"


def user_rules_dir():
    return user_home() / "rules"


def project_rules_dir(project):
    return Path(project) / ".shotcraft" / "rules"


def rule_dirs(project=None):
    """The rule folders in merge order (lowest first)."""
    dirs = [plugin_rules_dir(), user_rules_dir()]
    if project:
        dirs.append(project_rules_dir(project))
    return dirs


# --------------------------------------------------------------------------- merge

def deep_merge(base, over):
    """Return a new value: `over` merged onto `base` (see module docstring)."""
    if not isinstance(base, dict) or not isinstance(over, dict):
        return copy.deepcopy(over)
    out = copy.deepcopy(base)
    for key, val in over.items():
        if isinstance(key, str) and key.endswith("+") and len(key) > 1:
            real = key[:-1]
            cur = out.get(real)
            add = val if isinstance(val, list) else [val]
            if isinstance(cur, list):
                merged = list(cur)
                for item in add:
                    if item not in merged:
                        merged.append(copy.deepcopy(item))
                out[real] = merged
            elif isinstance(cur, dict) and isinstance(val, dict):
                out[real] = deep_merge(cur, val)
            else:
                out[real] = copy.deepcopy(add)
            continue
        if key in out and isinstance(out[key], dict) and isinstance(val, dict):
            out[key] = deep_merge(out[key], val)
        else:
            out[key] = copy.deepcopy(val)
    return out


def _read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as exc:
        raise RulesError("{} is not valid JSON: {}".format(path, exc))


def _strip_plus_keys(value):
    """Turn leftover 'key+' entries (nothing below to append to) into plain keys."""
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if isinstance(k, str) and k.endswith("+") and len(k) > 1 and k[:-1] not in value:
                out[k[:-1]] = _strip_plus_keys(v)
            else:
                out[k] = _strip_plus_keys(v)
        return out
    if isinstance(value, list):
        return [_strip_plus_keys(v) for v in value]
    return value


def load_from_dirs(name, dirs):
    """Merge <dir>/<name>.json across `dirs` in order. Missing files are skipped."""
    fname = name if name.endswith(".json") else name + ".json"
    result = {}
    for d in dirs:
        if d is None:
            continue
        p = Path(d) / fname
        if p.is_file():
            result = deep_merge(result, _read_json(p))
    return _strip_plus_keys(result)


def sources(name, project=None):
    """Which files contributed to `name`, lowest layer first."""
    fname = name if name.endswith(".json") else name + ".json"
    return [str(Path(d) / fname) for d in rule_dirs(project) if (Path(d) / fname).is_file()]


def load(name, project=None):
    """Load one rule file merged across plugin < personal < project layers."""
    return load_from_dirs(name, rule_dirs(project))


def load_all(project=None, names=RULE_NAMES):
    return {n: load(n, project) for n in names}


def compiler_rules(project=None):
    """The rule bundle compiler.compile() expects."""
    return {
        "taxonomy": load("taxonomy", project),
        "negatives": load("negatives", project),
        "positive_rewrites": load("positive_rewrites", project),
    }


def rules_version(project=None):
    """Version stamp used in cards (checked_rules_version)."""
    for name in ("models", "taxonomy"):
        try:
            data = load(name, project)
        except RulesError:
            continue
        v = data.get("rules_version") or data.get("version")
        if v:
            return str(v)
    return "0.0.0"


# --------------------------------------------------------------------------- helpers

def model_profile(model_id, provider="higgsfield", project=None, models=None):
    """Return (profile dict with 'id' added, error message or None)."""
    data = models if models is not None else load("models", project)
    prov = (data.get("providers") or {}).get(provider)
    if not prov:
        return None, "No provider '{}' in models.json.".format(provider)
    table = prov.get("models") or {}
    if model_id not in table:
        known = ", ".join(sorted(table)) or "none"
        return None, "Model '{}' is not in models.json for {}. Known: {}".format(model_id, provider, known)
    prof = dict(table[model_id])
    prof.setdefault("id", model_id)
    return prof, None


def preset(use_case, project=None, presets=None):
    data = presets if presets is not None else load("presets", project)
    table = data.get("presets", data)
    return table.get(use_case) if isinstance(table, dict) else None


def field_meta(taxonomy, layer, field):
    try:
        return taxonomy["layers"][layer]["fields"][field]
    except (KeyError, TypeError):
        return None
