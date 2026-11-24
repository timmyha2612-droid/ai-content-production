"""Generation providers (SPEC section 9). Each provider follows providers/base.py.

API:
    PROVIDERS                         name -> "module:Class"
    get_provider(name=None, project=None, **kw) -> Provider
        name None: $SHOTCRAFT_PROVIDER, else the project's provider (project.json), else the user's config,
        else "higgsfield". $SHOTCRAFT_PROVIDER=fake always wins (tests, dry runs).
    provider_name(project=None) -> str     the name get_provider(None, project) would pick
"""
import importlib
import os

from .. import ShotcraftError

PROVIDERS = {
    "higgsfield": "higgsfield:HiggsfieldProvider",
    "fake": "fake:FakeProvider",
}


def provider_name(project=None):
    env = (os.environ.get("SHOTCRAFT_PROVIDER") or "").strip()
    if env:
        return env
    if project:
        try:
            from .. import manifest
            name = manifest.load(project).get("provider")
            if name:
                return name
        except Exception:
            pass
    try:
        from .. import config
        name = config.load().get("provider")
        if name:
            return name
    except Exception:
        pass
    return "higgsfield"


def get_provider(name=None, project=None, **kw):
    env = (os.environ.get("SHOTCRAFT_PROVIDER") or "").strip()
    if env == "fake":
        name = "fake"
    name = name or provider_name(project)
    spec = PROVIDERS.get(name)
    if not spec:
        raise ShotcraftError("Unknown provider %r. Known: %s." % (name, ", ".join(sorted(PROVIDERS))))
    mod_name, cls_name = spec.split(":")
    mod = importlib.import_module("%s.%s" % (__name__, mod_name))
    return getattr(mod, cls_name)(project=project, **kw)
