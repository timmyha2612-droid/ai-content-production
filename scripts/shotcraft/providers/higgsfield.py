"""Higgsfield through its official CLI (`higgsfield`, npm @higgsfield/cli). SPEC section 9.

Commands used (from docs/research/higgsfield-cli/README.md and MODELS.md):
    higgsfield account status --json                      signed in? (fallback: higgsfield auth status)
    higgsfield model list --json                          live catalog
    higgsfield model get <job_set_type> --json            one model's schema
    higgsfield generate cost <job_set_type> [flags] --json     credit estimate, no job
    higgsfield generate create <job_set_type> --prompt .. [flags] --json   submit (no --wait: returns job ids)
    higgsfield generate get <job_id> --json               job status and result URLs
    higgsfield generate wait <job_id> --json --wait-timeout <N>s --wait-interval 3s
    higgsfield upload create <path> --json                upload a file, returns an upload id
Flags: --aspect_ratio, --resolution, --duration, --mode ... (underscore spelling, as in MODELS.md); media flags
--start-image, --end-image, --image-references, --video-references, --audio-references (repeated for several).

Behaviour: retries on HTTP 429 and captcha/anti-bot HTML (wait 30 s, at most 3 tries); "Session expired" /
"Not authenticated" raise ProviderAuthError with the fix; outputs are downloaded right away (URLs expire).
The REST API (api.higgsfield.ai, separate USD billing) is a possible later mode and is not built.

API: class HiggsfieldProvider(Provider) plus build_argv(prepared, action) for tests.
"""
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request

from .base import (ACTIVE, TERMINAL, Provider, ProviderAuthError, ProviderError, normalize_status, output_ext)

CLI = "higgsfield"
_RETRY_RX = re.compile(r"(HTTP\s*429|\b429\b|rate.?limit|too many requests|captcha|datadome|<html)", re.I)
_AUTH_RX = re.compile(r"(session expired|not authenticated|stored credentials are for|please log ?in|"
                      r"unauthori[sz]ed|\b401\b)", re.I)
_UNKNOWN_MODEL_RX = re.compile(r"unknown model", re.I)
_URL_KEYS = ("result_url", "result_urls", "url", "urls", "output", "outputs", "result", "results", "media",
             "medias", "file", "files", "video", "image", "audio", "download_url", "raw_url")


def _flag(key):
    """MODELS.md spells value flags with underscores and media flags with dashes."""
    if key in ("start_image", "end_image", "image_references", "video_references", "audio_references", "soul_id"):
        return "--" + key.replace("_", "-")
    return "--" + key


def _value(v):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    if isinstance(v, (list, dict)):
        return json.dumps(v, separators=(",", ":"))
    return str(v)


def build_argv(prepared, action="create"):
    """argv after `higgsfield generate <action>` for a prepared request (see Provider.prepare)."""
    argv = [prepared["model"]]
    if prepared.get("prompt"):
        argv += ["--prompt", prepared["prompt"]]
    for k in sorted(prepared.get("params") or {}):
        argv += [_flag(k), _value(prepared["params"][k])]
    for role in ("start_image", "end_image", "image_references", "video_references", "audio_references"):
        for v in (prepared.get("media") or {}).get(role, []):
            argv += [_flag(role), str(v)]
    return argv


def _parse_json(text):
    text = (text or "").strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except ValueError:
        pass
    # some commands print a note before the JSON; take the first {...} or [...] block
    for opener in ("[", "{"):
        i = text.find(opener)
        if i >= 0:
            try:
                return json.loads(text[i:])
            except ValueError:
                continue
    return None


def _jobs(data):
    if isinstance(data, list):
        return [d for d in data if isinstance(d, dict)] or [{"id": d} for d in data if isinstance(d, str)]
    if isinstance(data, dict):
        for k in ("jobs", "data", "items", "results", "job_ids", "ids"):
            v = data.get(k)
            if isinstance(v, list) and v:
                return _jobs(v)
        for k in ("job", "result"):
            if isinstance(data.get(k), dict):
                return [data[k]]
        return [data]
    if isinstance(data, str):
        return [{"id": data}]
    return []


def _job_id(job):
    for k in ("id", "job_id", "jobId", "request_id", "uuid"):
        if job.get(k):
            return str(job[k])
    return None


def _urls(obj, key_ok=False, out=None):
    out = [] if out is None else out
    if isinstance(obj, str):
        if key_ok and re.match(r"^https?://", obj) and obj not in out:
            out.append(obj)
    elif isinstance(obj, list):
        for v in obj:
            _urls(v, key_ok, out)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            ok = key_ok or str(k).lower() in _URL_KEYS
            if str(k).lower() in ("params", "input", "inputs", "request", "prompt"):
                continue  # the job's own inputs are not outputs
            _urls(v, ok, out)
    return out


def _number(obj, keys=("credits", "cost", "total_credits", "credit_cost", "price", "amount", "total")):
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        return float(obj)
    if isinstance(obj, dict):
        for k in keys:
            v = obj.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                return float(v)
            if isinstance(v, str) and re.match(r"^\d+(\.\d+)?$", v.strip()):
                return float(v)
        for v in obj.values():
            if isinstance(v, (dict, list)):
                n = _number(v, keys)
                if n is not None:
                    return n
    if isinstance(obj, list):
        for v in obj:
            n = _number(v, keys)
            if n is not None:
                return n
    return None


class HiggsfieldProvider(Provider):
    name = "higgsfield"
    profile_provider = "higgsfield"
    backoff_s = 30
    max_tries = 3
    call_timeout = 120

    def __init__(self, project=None, cli=None, runner=None, sleeper=None, **kw):
        Provider.__init__(self, project=project)
        self.cli = cli or os.environ.get("SHOTCRAFT_HIGGSFIELD_BIN") or CLI
        self._runner = runner or self._subprocess
        self._sleep = sleeper or time.sleep

    # ------------------------------------------------------------ running the CLI
    def _subprocess(self, argv, timeout):
        try:
            p = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout,
                               universal_newlines=True)
            return p.returncode, p.stdout or "", p.stderr or ""
        except subprocess.TimeoutExpired:
            return None, "", "timed out after %d s" % timeout
        except OSError as exc:
            return None, "", str(exc)

    def _run(self, args, timeout=None, check=True):
        argv = [self.cli] + list(args)
        last = ""
        for attempt in range(1, self.max_tries + 1):
            rc, out, err = self._runner(argv, timeout or self.call_timeout)
            both = (out or "") + "\n" + (err or "")
            if rc == 0:
                return out, err
            last = (err or out or "").strip()
            if _AUTH_RX.search(both):
                raise ProviderAuthError("Higgsfield needs you to sign in again. Run: higgsfield auth login "
                                        "(then try again). CLI said: %s" % last[:300])
            if rc is not None and _RETRY_RX.search(both) and attempt < self.max_tries:
                self._sleep(self.backoff_s)
                continue
            break
        if not check:
            return None, last
        if _UNKNOWN_MODEL_RX.search(last):
            raise ProviderError("Higgsfield does not know that model. Run: higgsfield model list (or sc.py scout "
                                "check). CLI said: %s" % last[:300])
        raise ProviderError("higgsfield %s failed: %s" % (" ".join(args[:2]), last[:500] or "no output"))

    def _json(self, args, timeout=None):
        out, err = self._run(list(args) + ["--json"], timeout=timeout)
        data = _parse_json(out)
        if data is None:
            data = _parse_json(err)
        return data, out

    # ------------------------------------------------------------ interface
    def available(self):
        return bool(shutil.which(self.cli))

    def auth_status(self):
        if not self.available():
            return {"ok": None, "note": "Higgsfield CLI not installed (npm install -g @higgsfield/cli)."}
        for args in (["account", "status", "--json"], ["auth", "status"]):
            rc, out, err = self._runner([self.cli] + args, 20)
            if rc == 0:
                data = _parse_json(out)
                return {"ok": True, "note": "signed in", "credits": _number(data) if data is not None else None,
                        "raw": data if data is not None else out.strip()[:500]}
            if _AUTH_RX.search((out or "") + (err or "")):
                return {"ok": False, "note": "not signed in: run higgsfield auth login"}
        return {"ok": False, "note": "could not check sign-in: %s" % ((err or out or "").strip()[:200])}

    def list_models(self):
        data, _ = self._json(["model", "list"], timeout=60)
        items = data if isinstance(data, list) else (
            (data or {}).get("models") or (data or {}).get("data") or (data or {}).get("items") or [])
        out = []
        for it in items:
            if isinstance(it, str):
                out.append({"id": it, "name": None, "kind": None})
                continue
            if not isinstance(it, dict):
                continue
            mid = it.get("job_set_type") or it.get("id") or it.get("model") or it.get("slug")
            if not mid:
                continue
            out.append({"id": str(mid),
                        "name": it.get("name") or it.get("display_name") or it.get("title"),
                        "kind": it.get("type") or it.get("kind") or it.get("category") or it.get("media_type"),
                        "raw": it})
        return out

    def get_model(self, model_id):
        data, out = self._json(["model", "get", model_id], timeout=60)
        return data if data is not None else {"text": out}

    def estimate(self, model, params, inputs=None, prompt=None):
        prep = self.prepare(model, prompt or "cost estimate", params, None)
        data, out = self._json(["generate", "cost"] + build_argv(prep, "cost"), timeout=60)
        n = _number(data) if data is not None else None
        if n is None:
            m = re.search(r"(\d+(?:\.\d+)?)\s*credit", out or "", re.I) or re.search(r"(\d+(?:\.\d+)?)", out or "")
            n = float(m.group(1)) if m else None
        if n is None:
            raise ProviderError("Could not read a credit cost from: higgsfield generate cost %s" % model)
        return n

    def submit(self, model, prompt, params, inputs=None):
        prep = self.prepare(model, prompt, params, inputs)
        data, out = self._json(["generate", "create"] + build_argv(prep, "create"), timeout=180)
        ids = [i for i in (_job_id(j) for j in _jobs(data)) if i]
        if not ids:
            m = re.search(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", out or "")
            if m:
                ids = [m.group(1)]
        if not ids:
            raise ProviderError("Higgsfield did not return a job id. Output: %s" % (out or "")[:300])
        return ids[0]

    def _status_from(self, job_id, data):
        jobs = _jobs(data)
        job = next((j for j in jobs if _job_id(j) == job_id), jobs[0] if jobs else {})
        st = normalize_status(job.get("status") or job.get("state"))
        err = job.get("error") or job.get("message") or job.get("failure_reason")
        return {"job_id": job_id, "status": st, "result_urls": _urls(job) if st == "completed" else [],
                "error": str(err) if err and st != "completed" else None, "cost": _number(job), "raw": job}

    def status(self, job_id):
        data, _ = self._json(["generate", "get", job_id], timeout=60)
        return self._status_from(job_id, data)

    def wait(self, job_id, timeout=600):
        args = ["generate", "wait", job_id, "--wait-timeout", "%ds" % int(timeout), "--wait-interval", "3s"]
        out, err = self._run(args + ["--json"], timeout=int(timeout) + 60, check=False)
        if out is not None:
            data = _parse_json(out)
            if data is not None:
                st = self._status_from(job_id, data)
                if st["status"] in TERMINAL:
                    return st
        # a timeout or an unreadable answer: ask for the current state
        st = self.status(job_id)
        if st["status"] in ACTIVE:
            st["timed_out"] = True
        return st

    def download(self, job_id, dest_dir, names=None):
        st = self.status(job_id)
        if st["status"] != "completed":
            raise ProviderError("Job %s is %s; nothing to download yet." % (job_id, st["status"]))
        if not st["result_urls"]:
            raise ProviderError("Job %s finished but returned no file URL." % job_id)
        os.makedirs(dest_dir, exist_ok=True)
        names = list(names or [])
        paths = []
        for i, url in enumerate(st["result_urls"]):
            base = names[i] if i < len(names) else "%s-%d" % (names[-1] if names else job_id, i + 1)
            ext = output_ext(None, None, url)
            if ext == ".bin":
                ext = ""
            tmp = os.path.join(dest_dir, ".part-" + base)
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "shotcraft"})
                with urllib.request.urlopen(req, timeout=300) as resp, open(tmp, "wb") as fh:
                    if not ext:
                        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip()
                        ext = {"image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
                               "image/svg+xml": ".svg", "image/gif": ".gif", "video/mp4": ".mp4",
                               "video/quicktime": ".mov", "audio/wav": ".wav", "audio/x-wav": ".wav",
                               "audio/mpeg": ".mp3", "model/gltf-binary": ".glb"}.get(ctype, ".bin")
                    shutil.copyfileobj(resp, fh)
            except Exception as exc:
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
                raise ProviderError("Could not download %s: %s" % (url, exc))
            dest = os.path.join(dest_dir, base + ext)
            os.replace(tmp, dest)
            paths.append(dest)
        return paths

    def upload(self, path):
        data, out = self._json(["upload", "create", path], timeout=300)
        for j in _jobs(data):
            for k in ("id", "upload_id", "uuid", "media_id"):
                if j.get(k):
                    return str(j[k])
            urls = _urls(j, key_ok=True)
            if urls:
                return urls[0]
        m = re.search(r"\b([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", out or "")
        if m:
            return m.group(1)
        raise ProviderError("Higgsfield did not return an upload id for %s." % path)

    def help_text(self):
        if not self.available():
            return ""
        rc, out, err = self._runner([self.cli, "--help"], 20)
        return (out or "") + (err or "")

    def has_command(self, name):
        if not self.available():
            return False
        rc, out, err = self._runner([self.cli, name, "--help"], 20)
        text = (out or "") + (err or "")
        return rc == 0 and not re.search(r"unknown (command|subcommand)", text, re.I)
