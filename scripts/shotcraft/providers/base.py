"""The provider interface (SPEC section 9). Every generator adapter (Higgsfield, the test fake, later Artlist, fal,
Runway ...) subclasses Provider and implements the abstract methods.

Generic params (what the compiler and routing produce, before a provider maps them to its own flags):
    aspect_ratio, resolution, duration, audio (bool), plus model extras such as mode, quality, model_type,
    output_format. Media never travels in params; it goes in `inputs`.
Inputs (local file paths or provider upload ids):
    {"start_image": x, "end_image": x, "image_references": [..], "video_references": [..], "audio_references": [..]}

API:
    STATUSES, TERMINAL, ACTIVE            job statuses (queued, in_progress, completed, failed, nsfw, canceled,
                                          ip_detected) and the terminal / still-running subsets
    normalize_status(raw) -> str          maps provider spellings ("succeeded", "processing" ...) to STATUSES
    MEDIA_ROLES                           the five media input roles above
    ProviderError(ShotcraftError)         a provider call failed (exit 1)
    ProviderAuthError(ProviderError)      not signed in / session expired
    class Provider:
        name, profile_provider
        available() -> bool
        auth_status() -> {"ok": bool|None, "note": str, ...}
        list_models() -> [{"id", "name", "kind"}]
        get_model(model_id) -> dict
        estimate(model, params, inputs=None, prompt=None) -> float credits
        submit(model, prompt, params, inputs=None) -> job_id
        status(job_id) -> {"job_id", "status", "result_urls": [..], "error", "cost", "raw"}
        wait(job_id, timeout=600) -> status dict (status may still be active when the timeout hits)
        download(job_id, dest_dir, names=None) -> [paths]   names: base names (no extension) used in order
        upload(path) -> upload id (or URL)
        help_text() -> str                    top-level CLI help, for spotting new surfaces (Canvas)
        has_command(name) -> bool             whether the provider exposes a command group (e.g. "canvas")
        profile(model_id) -> dict             the model's profile from rules/models.json ({} when unknown)
        prepare(model, prompt, params, inputs=None) -> {"model", "prompt", "params", "media", "notes"}
            maps generic params to the model's own flags using its profile (param_map, resolution_via,
            audio_flag/audio_values, media_mode, defaults) and drops flags the model does not accept,
            explaining each change in "notes".
"""
from .. import ShotcraftError

STATUSES = ("queued", "in_progress", "completed", "failed", "nsfw", "canceled", "ip_detected")
TERMINAL = ("completed", "failed", "nsfw", "canceled", "ip_detected")
ACTIVE = ("queued", "in_progress")
MEDIA_ROLES = ("start_image", "end_image", "image_references", "video_references", "audio_references")

_STATUS_ALIASES = {
    "queued": "queued", "pending": "queued", "waiting": "queued", "created": "queued", "submitted": "queued",
    "in_progress": "in_progress", "in-progress": "in_progress", "processing": "in_progress",
    "running": "in_progress", "started": "in_progress", "generating": "in_progress",
    "completed": "completed", "complete": "completed", "succeeded": "completed", "success": "completed",
    "done": "completed", "finished": "completed",
    "failed": "failed", "error": "failed", "errored": "failed", "failure": "failed",
    "nsfw": "nsfw", "canceled": "canceled", "cancelled": "canceled", "ip_detected": "ip_detected",
    "ip-detected": "ip_detected",
}

STATUS_HELP = {
    "failed": "The provider could not make it. Often the prompt content; rephrase and try again.",
    "nsfw": "Blocked by the content filter. Rephrase the prompt (no nudity, gore or real public figures).",
    "ip_detected": "Blocked as protected content (a trademark, brand or known character). Rephrase.",
    "canceled": "The job was canceled.",
}


class ProviderError(ShotcraftError):
    """A provider call failed."""


class ProviderAuthError(ProviderError):
    """The provider needs the user to sign in."""


def normalize_status(raw):
    s = str(raw or "").strip().lower().replace(" ", "_")
    return _STATUS_ALIASES.get(s, s or "queued")


def _has_media(inputs):
    for role in MEDIA_ROLES:
        v = (inputs or {}).get(role)
        if v:
            return True
    return False


class Provider(object):
    name = "base"
    profile_provider = "higgsfield"   # which models.json section describes this provider's models

    def __init__(self, project=None, **kw):
        self.project = project
        self._profiles = None

    # ------------------------------------------------------------ profiles and param mapping
    def _models_table(self):
        if self._profiles is None:
            try:
                from .. import rules
                data = rules.load("models", self.project)
            except Exception:
                data = {}
            prov = (data.get("providers") or {}).get(self.profile_provider) or {}
            self._profiles = prov.get("models") or {}
        return self._profiles

    def profile(self, model_id):
        prof = dict(self._models_table().get(model_id) or {})
        if prof:
            prof.setdefault("id", model_id)
        return prof

    def prepare(self, model, prompt, params, inputs=None):
        prof = self.profile(model)
        notes = []
        p = dict(prof.get("defaults") or {})
        for k, v in (params or {}).items():
            if k in MEDIA_ROLES or v is None:
                continue
            p[k] = v
        # size through another flag (Kling: --mode std|pro|4k)
        via = prof.get("resolution_via") or {}
        res = p.get("resolution")
        if res is not None and str(res) in via:
            for k, v in via[str(res)].items():
                if k in p and p[k] != v and k in (params or {}):
                    continue  # an explicit choice wins
                p[k] = v
            if "resolution" not in (prof.get("flags") or []) and "resolution" not in (prof.get("param_map") or {}):
                p.pop("resolution", None)
        # generic audio -> the model's own flag
        if "audio" in p:
            want = bool(p.pop("audio"))
            flag = prof.get("audio_flag")
            if flag:
                style = prof.get("audio_values") or "bool"
                p[flag] = ("on" if want else "off") if style == "onoff" else want
            elif want and not prof.get("audio"):
                notes.append("%s makes no sound; add audio in post." % (prof.get("name") or model))
            elif not want and prof.get("audio"):
                notes.append("%s always makes sound and has no switch for it; mute it in the edit."
                             % (prof.get("name") or model))
        # rename generic params to the model's flags (Soul: resolution -> quality)
        for src, dst in (prof.get("param_map") or {}).items():
            if src in p:
                p[dst] = p.pop(src)
        media = {}
        for role in MEDIA_ROLES:
            v = (inputs or {}).get(role)
            if not v:
                continue
            media[role] = list(v) if isinstance(v, (list, tuple)) else [v]
        mm = prof.get("media_mode")
        if mm and mm.get("param"):
            cur = p.get(mm["param"])
            if media and (cur is None or cur == mm.get("without_media")):
                p[mm["param"]] = mm.get("with_media")
            elif not media and cur is None:
                p[mm["param"]] = mm.get("without_media")
        flags = prof.get("flags")
        if flags:
            for k in list(p):
                if k not in flags:
                    notes.append("%s has no --%s flag; left out (%s)." % (prof.get("name") or model, k, p[k]))
                    p.pop(k)
            for role in list(media):
                if role not in flags:
                    notes.append("%s takes no %s; that input is left out." % (prof.get("name") or model,
                                                                              role.replace("_", " ")))
                    media.pop(role)
        return {"model": model, "prompt": prompt, "params": p, "media": media, "notes": notes,
                "has_media": _has_media(media)}

    # ------------------------------------------------------------ the interface
    def available(self):
        raise NotImplementedError

    def auth_status(self):
        raise NotImplementedError

    def list_models(self):
        raise NotImplementedError

    def get_model(self, model_id):
        raise NotImplementedError

    def estimate(self, model, params, inputs=None, prompt=None):
        raise NotImplementedError

    def submit(self, model, prompt, params, inputs=None):
        raise NotImplementedError

    def status(self, job_id):
        raise NotImplementedError

    def wait(self, job_id, timeout=600):
        raise NotImplementedError

    def download(self, job_id, dest_dir, names=None):
        raise NotImplementedError

    def upload(self, path):
        raise NotImplementedError

    def help_text(self):
        return ""

    def has_command(self, name):
        return False


def output_ext(profile, params=None, url=None):
    """A file extension for a provider output, from the URL first, else the model's kind."""
    import os
    import re
    if url:
        path = re.split(r"[?#]", str(url))[0]
        ext = os.path.splitext(path)[1].lower()
        if re.match(r"^\.[a-z0-9]{2,5}$", ext):
            return ext
    params = params or {}
    if str(params.get("output_format") or "").lower() in ("svg", "gif", "png", "jpeg", "webp"):
        return "." + str(params["output_format"]).lower().replace("jpeg", "jpg")
    kind = (profile or {}).get("kind")
    if kind == "upscale":
        kind = (profile or {}).get("upscales") or "image"
    return {"image": ".png", "video": ".mp4", "audio": ".wav", "3d": ".glb"}.get(kind, ".bin")
