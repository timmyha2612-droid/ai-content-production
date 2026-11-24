"""Reference downloads and the rights check (SPEC sections 0.6 and 7).

Every downloaded reference keeps its source URL and is tagged `reference-only`. It is never sent to a model as
an input unless the user marks it `owned` or `licensed` (sc.py asset mark ID --rights owned --user-said "...").

How a link is fetched:
  - Video platforms (YouTube, Instagram, TikTok, Vimeo, Facebook, X, ...): yt-dlp when it is installed. It
    prefers H.264/AAC, merges to .mp4 and writes the site's info JSON next to the video. If the file is not
    H.264 .mp4 and ffmpeg is installed, it is converted, so it opens in any editor.
  - Anything else (a direct image or video link, file://): a plain download with urllib. A web page (HTML) is
    handed to yt-dlp when it is installed, else refused with a hint.
Files land in <project>/01_research/refs/<slug>/ with a source.json (url, when, how, title) and each media file
is registered as an asset: rights reference-only, role reference, source_url set.

API:
    VIDEO_HOSTS                                 host suffixes that go to yt-dlp
    is_video_platform(url) -> bool
    slug_for(url, title=None) -> str
    fetch(project, url, note=None, shot=None, cookies_from_browser=None, use_ytdlp=None, timeout=60)
        -> {"url", "folder", "method", "assets": [asset dicts], "files": [rel paths], "notes": [..]}
    rights_check(project_or_manifest, asset_ids) -> {"ok", "blocked": [..], "missing": [..], "allowed": [..],
                                                     "reason"}
    require_rights(project, asset_ids)          raises Refused when any input is reference-only or unknown
    cli_refs_fetch(args) -> int                 sc.py refs fetch URL [--note] [--shot] [--cookies-from-browser B]
"""
import json
import os
import re
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request

from . import Refused, ShotcraftError, VERSION, jsonio, manifest

VIDEO_HOSTS = ("youtube.com", "youtu.be", "instagram.com", "tiktok.com", "vimeo.com", "facebook.com",
               "fb.watch", "x.com", "twitter.com", "twitch.tv", "dailymotion.com", "reddit.com",
               "threads.net", "pinterest.com", "linkedin.com", "loom.com", "bilibili.com")
MAX_BYTES = 1024 * 1024 * 1024          # 1 GB cap for a plain download
USER_AGENT = "shotcraft/%s (reference fetch)" % VERSION
ALLOWED_RIGHTS = ("owned", "licensed", "generated")

_CT_EXT = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif", "image/avif": ".avif",
    "image/svg+xml": ".svg", "image/tiff": ".tif", "image/heic": ".heic", "video/mp4": ".mp4",
    "video/quicktime": ".mov", "video/webm": ".webm", "audio/mpeg": ".mp3", "audio/wav": ".wav",
    "audio/x-wav": ".wav", "audio/mp4": ".m4a", "application/pdf": ".pdf",
}


# ---------------------------------------------------------------- helpers

def _host(url):
    try:
        return (urllib.parse.urlparse(url).hostname or "").lower()
    except ValueError:
        return ""


def is_video_platform(url):
    h = _host(url)
    return any(h == d or h.endswith("." + d) for d in VIDEO_HOSTS)


def slug_for(url, title=None):
    if title:
        base = title
    else:
        u = urllib.parse.urlparse(url)
        host = (u.hostname or "").replace("www.", "")
        tail = [p for p in u.path.split("/") if p][-2:]
        if u.scheme == "file":
            host = "local"
        base = "-".join([host.split(".")[0]] + tail) if host else "-".join(tail)
    s = re.sub(r"\.[A-Za-z0-9]{2,5}$", "", base or "")
    s = re.sub(r"[^A-Za-z0-9]+", "-", s).strip("-").lower()
    return (s[:60].strip("-")) or "reference"


def _unique_dir(parent, name):
    d, k = os.path.join(parent, name), 2
    while os.path.exists(d):
        d = os.path.join(parent, "%s-%d" % (name, k))
        k += 1
    os.makedirs(d)
    return d


def _run(cmd, timeout=None):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def _safe_name(name, fallback="reference"):
    name = os.path.basename(urllib.parse.unquote(name or ""))
    base, ext = os.path.splitext(name)
    base = re.sub(r"[^A-Za-z0-9._-]+", "-", base).strip("-.")[:80] or fallback
    ext = re.sub(r"[^A-Za-z0-9.]", "", ext)[:6]
    return base + ext.lower()


# ---------------------------------------------------------------- yt-dlp route

def _ensure_h264(path, notes):
    """Convert to H.264/AAC .mp4 when it is not one already (needs ffmpeg/ffprobe)."""
    if not (shutil.which("ffprobe") and shutil.which("ffmpeg")):
        return path
    r = _run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name", "-of", "json", path])
    try:
        streams = json.loads(r.stdout or "{}").get("streams", [])
    except ValueError:
        return path
    v = next((s.get("codec_name") for s in streams if s.get("codec_type") == "video"), None)
    a = next((s.get("codec_name") for s in streams if s.get("codec_type") == "audio"), None)
    if v is None:
        return path
    if v == "h264" and a in (None, "aac") and path.lower().endswith(".mp4"):
        return path
    base = os.path.splitext(path)[0]
    tmp = base + ".h264-tmp.mp4"
    vargs = ["-c:v", "copy"] if v == "h264" else ["-c:v", "libx264", "-preset", "medium", "-crf", "18",
                                                    "-pix_fmt", "yuv420p"]
    aargs = ["-c:a", "copy"] if a == "aac" else ["-c:a", "aac", "-b:a", "192k"]
    r = _run(["ffmpeg", "-y", "-v", "error", "-i", path, "-map", "0:v:0", "-map", "0:a?"] + vargs + aargs
             + ["-movflags", "+faststart", tmp])
    if r.returncode != 0 or not os.path.isfile(tmp):
        if os.path.exists(tmp):
            os.unlink(tmp)
        notes.append("Could not convert %s to H.264; kept the %s file." % (os.path.basename(path), v))
        return path
    dst = base + ".mp4"
    if os.path.abspath(dst) != os.path.abspath(path):
        os.unlink(path)
    os.replace(tmp, dst)
    notes.append("Converted %s from %s to H.264." % (os.path.basename(dst), v))
    return dst


def _ytdlp(url, folder, notes, cookies_from_browser=None, timeout=900):
    cmd = ["yt-dlp", "--ignore-config", "--no-mtime", "--no-overwrites", "--no-progress",
           "-S", "res,fps,vcodec:h264,acodec:aac", "--merge-output-format", "mp4",
           "--playlist-items", "1:10", "--write-info-json",
           "-o", os.path.join(folder, "%(title).60B-%(id)s.%(ext)s"),
           "--print", "after_move:filepath"]
    if cookies_from_browser:
        cmd += ["--cookies-from-browser", cookies_from_browser]
    try:
        r = _run(cmd + [url], timeout=timeout)
    except subprocess.TimeoutExpired:
        raise ShotcraftError("yt-dlp took longer than %d s for %s." % (timeout, url))
    if r.returncode != 0:
        err = (r.stderr or "").strip().splitlines()
        msg = next((l for l in reversed(err) if "ERROR" in l), err[-1] if err else "unknown error")
        if re.search(r"login|log in|rate-limit|cookies|private", msg, re.I):
            msg += (" This site wants a signed-in browser for this link. With the user's OK, run again with "
                    "--cookies-from-browser <browser> (the browser they are signed in with).")
        raise ShotcraftError("yt-dlp could not download %s: %s" % (url, msg))
    out = []
    for line in (r.stdout or "").splitlines():
        p = line.strip()
        if p and os.path.isfile(p):
            out.append(_ensure_h264(p, notes))
    info = None
    for f in sorted(os.listdir(folder)):
        if f.endswith(".info.json"):
            try:
                with open(os.path.join(folder, f), "r", encoding="utf-8") as fh:
                    info = json.load(fh)
            except (OSError, ValueError):
                info = None
            break
    return out, info


# ---------------------------------------------------------------- plain download

def _http_get(url, folder, timeout=60):
    """Download one URL (http, https or file) into folder. Returns (path, content_type)."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        resp = urllib.request.urlopen(req, timeout=timeout)
    except urllib.error.HTTPError as exc:
        raise ShotcraftError("The server answered %s for %s." % (exc.code, url))
    except (urllib.error.URLError, OSError, ValueError) as exc:
        raise ShotcraftError("Could not download %s: %s" % (url, getattr(exc, "reason", exc)))
    with resp:
        ctype = (resp.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ctype in ("text/html", "application/xhtml+xml"):
            return None, ctype
        name = None
        cd = resp.headers.get("Content-Disposition") or ""
        m = re.search(r"filename\*?=(?:UTF-8'')?\"?([^\";]+)", cd, re.I)
        if m:
            name = m.group(1)
        if not name:
            name = urllib.parse.urlparse(resp.geturl() or url).path
        name = _safe_name(name)
        if not os.path.splitext(name)[1] and ctype in _CT_EXT:
            name += _CT_EXT[ctype]
        dest = os.path.join(folder, name)
        total = 0
        with open(dest, "wb") as fh:
            while True:
                chunk = resp.read(1024 * 256)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_BYTES:
                    fh.close()
                    os.unlink(dest)
                    raise ShotcraftError("%s is larger than 1 GB; download it yourself and add it with "
                                         "sc.py asset add." % url)
                fh.write(chunk)
    if total == 0:
        os.unlink(dest)
        raise ShotcraftError("%s gave an empty file." % url)
    return dest, ctype


# ---------------------------------------------------------------- fetch

def fetch(project, url, note=None, shot=None, cookies_from_browser=None, use_ytdlp=None, timeout=60):
    """Download a reference into 01_research/refs/<slug>/ and register each file as reference-only."""
    url = (url or "").strip()
    scheme = urllib.parse.urlparse(url).scheme.lower()
    if scheme not in ("http", "https", "file"):
        raise Refused("Give a web link (http/https). For a file on this computer use: sc.py asset add PATH "
                      "--rights reference-only --role reference")
    have_ytdlp = bool(shutil.which("yt-dlp"))
    if use_ytdlp is None:
        use_ytdlp = is_video_platform(url)
    refs_root = os.path.join(project, "01_research", "refs")
    os.makedirs(refs_root, exist_ok=True)
    notes, files, info, method = [], [], None, None

    if use_ytdlp:
        if not have_ytdlp:
            raise ShotcraftError("This link is a video page (%s). Downloading it needs yt-dlp, which is not "
                                 "installed. Install it (brew install yt-dlp, or pipx install yt-dlp) and try "
                                 "again." % (_host(url) or url))
        folder = _unique_dir(refs_root, slug_for(url))
        try:
            files, info = _ytdlp(url, folder, notes, cookies_from_browser)
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        method = "yt-dlp"
    else:
        folder = _unique_dir(refs_root, slug_for(url))
        try:
            path, ctype = _http_get(url, folder, timeout=timeout)
            if path is None:  # a web page, not a media file
                if not have_ytdlp:
                    raise Refused("That link is a web page, not an image or video file. Give a direct media "
                                  "link, or install yt-dlp so shotcraft can pull the video from the page.")
                files, info = _ytdlp(url, folder, notes, cookies_from_browser)
                method = "yt-dlp"
            else:
                files, method = [path], "download"
                if manifest.guess_kind(path) == "video":
                    files = [_ensure_h264(path, notes)]
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
    if not files:
        shutil.rmtree(folder, ignore_errors=True)
        raise ShotcraftError("Nothing was downloaded from %s." % url)

    title = (info or {}).get("title")
    source = {"url": url, "fetched_at": jsonio.now_iso(), "method": method, "title": title,
              "uploader": (info or {}).get("uploader") or (info or {}).get("channel"),
              "webpage_url": (info or {}).get("webpage_url"), "duration": (info or {}).get("duration"),
              "rights": "reference-only", "note": note,
              "files": [os.path.basename(f) for f in files]}
    jsonio.write_json(os.path.join(folder, "source.json"), source)

    assets = []
    for f in files:
        a_note = note
        if title:
            a_note = ((note + " | ") if note else "") + "title: %s" % title
        assets.append(manifest.add_asset(project, f, "reference-only", "reference", source_url=url,
                                         note=a_note, shot=shot))
    rel_folder = os.path.relpath(folder, project).replace(os.sep, "/")
    return {"url": url, "folder": rel_folder, "method": method, "title": title, "assets": assets,
            "files": [a["path"] for a in assets], "notes": notes}


# ---------------------------------------------------------------- rights

def rights_check(project_or_manifest, asset_ids):
    """Inputs may go to a model only when their rights are owned, licensed or generated."""
    data = project_or_manifest if isinstance(project_or_manifest, dict) else manifest.load(project_or_manifest)
    blocked, missing, allowed = [], [], []
    for aid in asset_ids or []:
        if isinstance(aid, dict):
            aid = aid.get("asset") or aid.get("id")
        a = manifest.find_asset(data, aid)
        if a is None:
            missing.append(aid)
            continue
        if a.get("rights") in ALLOWED_RIGHTS:
            allowed.append(aid)
        else:
            blocked.append({"id": aid, "path": a.get("path"), "rights": a.get("rights"),
                            "source_url": a.get("source_url")})
    reasons = []
    if blocked:
        reasons.append("%s %s reference-only, so it cannot go to a model. If the user owns it or has a licence, "
                       "record their words: sc.py asset mark ID --rights owned|licensed --user-said \"...\""
                       % (", ".join("%s (%s)" % (b["id"], b["path"]) for b in blocked),
                          "is" if len(blocked) == 1 else "are"))
    if missing:
        reasons.append("Unknown asset id(s): %s." % ", ".join(str(m) for m in missing))
    return {"ok": not blocked and not missing, "blocked": blocked, "missing": missing, "allowed": allowed,
            "reason": " ".join(reasons) or "All inputs may be sent to a model."}


def require_rights(project, asset_ids):
    res = rights_check(project, asset_ids)
    if not res["ok"]:
        raise Refused(res["reason"])
    return res


# ---------------------------------------------------------------- CLI

def cli_refs_fetch(args):
    from . import project as _project
    proj = _project.resolve(getattr(args, "project", None), getattr(args, "session_id", None))
    res = fetch(proj, args.url, note=getattr(args, "note", None), shot=getattr(args, "shot", None),
                cookies_from_browser=getattr(args, "cookies_from_browser", None))
    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        lines = ["Saved %d file(s) to %s (%s), tagged reference-only:" % (len(res["assets"]), res["folder"],
                                                                         res["method"])]
        for a in res["assets"]:
            lines.append("  %s  %s" % (a["id"], a["path"]))
        lines += ["  " + n for n in res["notes"]]
        lines.append("These are for looking at only. They go to a model only if the user says they own or "
                     "license them.")
        print("\n".join(lines))
    return 0
