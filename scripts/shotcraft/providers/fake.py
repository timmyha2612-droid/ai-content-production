"""A deterministic stand-in for a generation provider: no network, no CLI. Used by the tests and for dry runs
(SHOTCRAFT_PROVIDER=fake). It describes its models with the Higgsfield profiles from rules/models.json.

Jobs live in <SHOTCRAFT_HOME>/fake_provider/jobs.json, so a job submitted by one sc.py process can be checked
by the next. Outputs are tiny placeholder files with the right extension.

Cost (credits), deterministic:
    image: 2 x size factor           video: 2 x seconds x size factor        upscale: 4 (image) / 1 per s (video)
    size factor: 480p/512 0.5, 720p/768/1k 1, 1.5k 1.5, 1080p/1080/2k 2, 4k 4 (anything else 1); rounded up.

Knobs (constructor args, or environment variables for CLI runs):
    final_status / SHOTCRAFT_FAKE_STATUS     status every job ends in (default completed): failed, nsfw ...
    outputs / SHOTCRAFT_FAKE_OUTPUTS         files per job (default 1)
    models / SHOTCRAFT_FAKE_MODELS           the live model list: a list of {"id","name","kind"} (or a path to a
                                             JSON file holding one); default = every model in models.json whose
                                             in_model_list is true
    help / SHOTCRAFT_FAKE_HELP               text returned by help_text() (e.g. to simulate a 'canvas' command)

API: class FakeProvider(Provider), cost_for(profile, params) -> int.
"""
import hashlib
import json
import math
import os

from .. import jsonio, paths
from .base import Provider, ProviderError, normalize_status, output_ext

SIZE_FACTOR = {"480p": 0.5, "512": 0.5, "720p": 1, "768": 1, "1k": 1, "1.5k": 1.5, "1080p": 2, "1080": 2,
               "2k": 2, "4k": 4}

# smallest valid files of each type, so tools that sniff headers are not confused
_PNG = bytes.fromhex("89504e470d0a1a0a0000000d4948445200000001000000010806000000"
                     "1f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")
_MP4 = b"\x00\x00\x00\x18ftypisom\x00\x00\x02\x00isommp42" + b"\x00\x00\x00\x08free"
_WAV = (b"RIFF" + (36).to_bytes(4, "little") + b"WAVEfmt " + (16).to_bytes(4, "little") +
        (1).to_bytes(2, "little") + (1).to_bytes(2, "little") + (8000).to_bytes(4, "little") +
        (8000).to_bytes(4, "little") + (1).to_bytes(2, "little") + (8).to_bytes(2, "little") + b"data" +
        (0).to_bytes(4, "little"))
_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16"><rect width="16" height="16"/></svg>\n'


def cost_for(profile, params):
    params = params or {}
    kind = (profile or {}).get("kind") or "image"
    size = str(params.get("resolution") or params.get("quality") or "").lower()
    factor = SIZE_FACTOR.get(size, 1)
    if kind == "upscale":
        if (profile or {}).get("upscales") == "video":
            return int(math.ceil(float(params.get("duration") or 5)))
        return 4
    if kind == "video":
        secs = float(params.get("duration") or 5)
        return int(math.ceil(2 * secs * factor))
    return int(math.ceil(2 * factor))


class FakeProvider(Provider):
    name = "fake"
    profile_provider = "higgsfield"

    def __init__(self, project=None, final_status=None, outputs=None, models=None, help=None, **kw):
        Provider.__init__(self, project=project)
        self.final_status = normalize_status(final_status or os.environ.get("SHOTCRAFT_FAKE_STATUS") or "completed")
        self.outputs = int(outputs or os.environ.get("SHOTCRAFT_FAKE_OUTPUTS") or 1)
        self._live = models
        self._help = help if help is not None else os.environ.get("SHOTCRAFT_FAKE_HELP", "")

    # ------------------------------------------------------------ store
    def _store_path(self):
        return os.path.join(paths.user_dir(), "fake_provider", "jobs.json")

    def _load(self):
        data = jsonio.read_json(self._store_path(), default=None) or {}
        data.setdefault("jobs", {})
        data.setdefault("uploads", {})
        data.setdefault("calls", [])
        return data

    def _save(self, data):
        jsonio.write_json(self._store_path(), data)

    def _log(self, data, what, **info):
        info["call"] = what
        data["calls"].append(info)

    # ------------------------------------------------------------ interface
    def available(self):
        return True

    def auth_status(self):
        return {"ok": True, "note": "fake provider (no sign-in needed)"}

    def list_models(self):
        live = self._live
        if live is None:
            env = os.environ.get("SHOTCRAFT_FAKE_MODELS")
            if env:
                live = jsonio.read_json(env, default=None) if os.path.isfile(env) else json.loads(env)
        if live is not None:
            return [dict(m) if isinstance(m, dict) else {"id": str(m), "name": None, "kind": None} for m in live]
        out = []
        for mid, prof in sorted(self._models_table().items()):
            if prof.get("in_model_list") is True:
                out.append({"id": mid, "name": prof.get("name"), "kind": prof.get("kind")})
        return out

    def get_model(self, model_id):
        prof = self.profile(model_id)
        if not prof:
            raise ProviderError("Unknown model %r (fake provider)." % model_id)
        return prof

    def estimate(self, model, params, inputs=None, prompt=None):
        prof = self.profile(model)
        if not prof:
            raise ProviderError("Unknown model %r (fake provider)." % model)
        prep = self.prepare(model, prompt, params, inputs)
        merged = dict(params or {})
        merged.update(prep["params"])
        return float(cost_for(prof, merged))

    def submit(self, model, prompt, params, inputs=None):
        prof = self.profile(model)
        if not prof:
            raise ProviderError("Unknown model %r (fake provider)." % model)
        prep = self.prepare(model, prompt, params, inputs)
        data = self._load()
        n = len(data["jobs"]) + 1
        key = json.dumps([model, prompt, prep["params"], prep["media"], n], sort_keys=True, default=str)
        job_id = "fake-%s" % hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        merged = dict(params or {})
        merged.update(prep["params"])
        data["jobs"][job_id] = {"model": model, "prompt": prompt, "params": prep["params"], "media": prep["media"],
                                "notes": prep["notes"], "status": self.final_status, "n": n,
                                "cost": cost_for(prof, merged), "outputs": self.outputs,
                                "ext": output_ext(prof, merged)}
        self._log(data, "submit", job_id=job_id, model=model)
        self._save(data)
        return job_id

    def _job(self, job_id):
        job = self._load()["jobs"].get(job_id)
        if job is None:
            raise ProviderError("No job %s (fake provider)." % job_id)
        return job

    def status(self, job_id):
        job = self._job(job_id)
        st = job["status"]
        urls = (["fake://%s/%d%s" % (job_id, i, job["ext"]) for i in range(job["outputs"])]
                if st == "completed" else [])
        return {"job_id": job_id, "status": st, "result_urls": urls,
                "error": None if st == "completed" else "fake provider ended the job as %s" % st,
                "cost": job["cost"], "raw": job}

    def wait(self, job_id, timeout=600):
        return self.status(job_id)

    def download(self, job_id, dest_dir, names=None):
        st = self.status(job_id)
        if st["status"] != "completed":
            raise ProviderError("Job %s is %s; nothing to download." % (job_id, st["status"]))
        os.makedirs(dest_dir, exist_ok=True)
        names = list(names or [])
        out = []
        for i, url in enumerate(st["result_urls"]):
            base = names[i] if i < len(names) else "%s-%d" % (names[-1] if names else job_id, i + 1)
            ext = os.path.splitext(url)[1] or ".bin"
            body = {".png": _PNG, ".mp4": _MP4, ".wav": _WAV, ".svg": _SVG}.get(
                ext, ("fake output of %s\n" % job_id).encode("utf-8"))
            dest = os.path.join(dest_dir, base + ext)
            with open(dest, "wb") as fh:
                fh.write(body)
            out.append(dest)
        return out

    def upload(self, path):
        if not os.path.exists(path):
            raise ProviderError("No file to upload at %s." % path)
        key = "%s:%d" % (os.path.abspath(path), os.path.getsize(path))
        uid = "fake-upload-%s" % hashlib.sha1(key.encode("utf-8")).hexdigest()[:12]
        data = self._load()
        data["uploads"][uid] = os.path.abspath(path)
        self._log(data, "upload", upload_id=uid, path=os.path.abspath(path))
        self._save(data)
        return uid

    def help_text(self):
        return self._help or "fake provider: generate, model, upload"

    def has_command(self, name):
        return name.lower() in (self._help or "").lower()

    # ------------------------------------------------------------ for tests
    def calls(self):
        return list(self._load()["calls"])
