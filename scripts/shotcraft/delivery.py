"""Delivery checks (SPEC section 4, delivery stage): every file in 10_delivery/ is measured with ffprobe (and
ffmpeg's ebur128 filter for loudness) against the delivery spec, and the result goes to
10_delivery/delivery-report.json. The delivery stage closes only when every check there is PASS.

The spec comes from, lowest to highest: the preset (rules/presets.json, the project's use case or --spec), then
project.json "delivery", then command-line overrides. What is checked per file:
  video: resolution, aspect, frame rate, codec, duration (within a tolerance), audio presence (when the preset
         says audio is required or none), loudness and true peak (when there is audio), file size
  image: resolution, aspect, format, file size
The expected duration of a file: --duration, else the planned length of the shot named in the file name
(S010...), else (when there is a single video) the planned total of the shot list, else the preset's min-max.

Only PASS/FAIL items go in "checks"; anything informational goes in "notes".

API:
    have_tools() -> bool                                ffprobe found
    run(cmd, timeout=None) -> CompletedProcess          text output, never raises on a non-zero exit
    probe(path) -> dict                                 kind, width, height, fps, vcodec, pix_fmt, acodec, channels,
                                                        sample_rate, duration, size_bytes, format_name, has_audio
    loudness(path) -> {"integrated_lufs", "true_peak_dbtp", "lra"} or None
    parse_wh(text) -> (w, h) | None                     the first "1080x1920" in a string
    ratio_of(aspect) -> float | None                    "9:16" -> 0.5625
    aspect_name(w, h) -> str
    spec_for(project, preset_id=None, overrides=None) -> dict
    check(project, preset_id=None, duration=None, tolerance=None, lufs=None, write=True) -> report dict
    cli_delivery_check(args) -> int     sc.py delivery check [--spec P] [--duration S] [--tolerance S] [--lufs L]
                                        exit 0 when every check passes, 2 when any fails
"""
import json
import os
import re
import shutil
import subprocess

from . import Refused, ShotcraftError, jsonio, manifest

REPORT = "10_delivery/delivery-report.json"
SKIP_EXT = {".json", ".md", ".txt", ".csv", ".srt", ".vtt", ".pdf", ".edl", ".xml", ".fcpxml", ".html"}
DEFAULT_LUFS = -14.0
LUFS_TOL = 1.0
MAX_TRUE_PEAK = -1.0
DEFAULT_DUR_TOL = 0.5
KNOWN_ASPECTS = (("9:16", 9 / 16.0), ("4:5", 4 / 5.0), ("2:3", 2 / 3.0), ("3:4", 3 / 4.0), ("1:1", 1.0),
                 ("4:3", 4 / 3.0), ("3:2", 3 / 2.0), ("16:9", 16 / 9.0), ("1.85:1", 1.85), ("2:1", 2.0),
                 ("21:9", 21 / 9.0), ("2.39:1", 2.39))


# ---------------------------------------------------------------- tools

def have_tools():
    return bool(shutil.which("ffprobe"))


def run(cmd, timeout=None):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True,
                          encoding="utf-8", errors="replace", timeout=timeout)


def _rate(text):
    try:
        num, _, den = str(text or "0/1").partition("/")
        den = float(den or 1)
        return round(float(num) / den, 3) if den else None
    except ValueError:
        return None


def probe(path):
    if not have_tools():
        raise ShotcraftError("ffprobe is not installed. Install ffmpeg (brew install ffmpeg / apt install ffmpeg).")
    r = run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-of", "json", path], timeout=60)
    if r.returncode != 0:
        raise ShotcraftError("ffprobe could not read %s: %s" % (path, (r.stderr or "").strip()[:200]))
    data = json.loads(r.stdout or "{}")
    fmt = data.get("format") or {}
    streams = data.get("streams") or []
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), {})
    fmt_name = fmt.get("format_name") or ""
    vcodec = v.get("codec_name")
    is_image = bool(v) and (fmt_name.endswith("_pipe") or fmt_name in ("image2", "png", "webp", "gif", "svg")
                            or manifest.guess_kind(path) == "image")
    if fmt_name == "gif" and _float(fmt.get("duration")) and _float(fmt.get("duration")) > 0.2:
        is_image = False
    duration = _float(fmt.get("duration")) or _float(v.get("duration"))
    fps = _rate(v.get("avg_frame_rate")) or _rate(v.get("r_frame_rate"))
    try:
        size = os.path.getsize(path)
    except OSError:
        size = None
    return {
        "kind": "image" if is_image else ("video" if v else ("audio" if a else "other")),
        "width": v.get("width"), "height": v.get("height"),
        "fps": None if is_image else fps, "vcodec": vcodec, "pix_fmt": v.get("pix_fmt"),
        "acodec": a.get("codec_name"), "channels": a.get("channels"),
        "sample_rate": int(a["sample_rate"]) if a.get("sample_rate") else None,
        "duration": None if is_image else duration, "size_bytes": size, "format_name": fmt_name,
        "has_audio": bool(a),
    }


def _float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def loudness(path):
    """Integrated loudness (LUFS), true peak (dBTP) and loudness range via ffmpeg's ebur128 filter."""
    if not shutil.which("ffmpeg"):
        return None
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null",
             "-"], timeout=600)
    text = r.stderr or ""
    tail = text[text.rfind("Summary:"):] if "Summary:" in text else text
    i = re.search(r"I:\s*(-?[\d.]+|-inf)\s*LUFS", tail)
    lra = re.search(r"LRA:\s*(-?[\d.]+)\s*LU", tail)
    tp = re.search(r"True peak:\s*Peak:\s*(-?[\d.]+|-inf)\s*dBFS", tail, re.S)
    if not i:
        return None

    def num(m):
        if not m:
            return None
        return None if m.group(1) == "-inf" else float(m.group(1))  # None = silent
    return {"integrated_lufs": num(i), "true_peak_dbtp": num(tp), "lra": num(lra)}


# ---------------------------------------------------------------- spec

def parse_wh(text):
    m = re.search(r"(\d{2,5})\s*[x×]\s*(\d{2,5})", str(text or ""))
    return (int(m.group(1)), int(m.group(2))) if m else None


def ratio_of(aspect):
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*[:/x]\s*(\d+(?:\.\d+)?)\s*$", str(aspect or ""))
    if not m or float(m.group(2)) == 0:
        return None
    return float(m.group(1)) / float(m.group(2))


def aspect_name(w, h):
    if not w or not h:
        return "?"
    r = float(w) / float(h)
    for name, val in KNOWN_ASPECTS:
        if abs(r - val) / val < 0.01:
            return name
    return "%dx%d" % (w, h)


def _max_mb(*texts):
    for t in texts:
        for s in (t if isinstance(t, (list, tuple)) else [t]):
            m = re.search(r"under\s+(\d+(?:\.\d+)?)\s*MB", str(s or ""), re.I)
            if m:
                return float(m.group(1))
    return None


def _codecs(formats):
    text = " ".join(str(f) for f in (formats or [])).lower()
    out = []
    if "h.264" in text or "h264" in text or "avc" in text:
        out.append("h264")
    if "h.265" in text or "h265" in text or "hevc" in text:
        out.append("hevc")
    if "prores" in text:
        out.append("prores")
    if "vp9" in text or "webm" in text:
        out.append("vp9")
    if "av1" in text:
        out.append("av1")
    return out


def _image_formats(formats):
    text = " ".join(str(f) for f in (formats or [])).lower()
    out = []
    for key, codecs in (("png", ["png"]), ("jpg", ["mjpeg"]), ("jpeg", ["mjpeg"]), ("webp", ["webp"]),
                        ("avif", ["av1"]), ("svg", ["svg"]), ("gif", ["gif"])):
        if key in text:
            out += [c for c in codecs if c not in out]
    return out


def _load_preset(project, preset_id):
    try:
        from . import rules
        return rules.preset(preset_id, project)
    except Exception:
        from . import project as _p
        return _p.load_preset(preset_id)


def spec_for(project, preset_id=None, overrides=None):
    data = manifest.load(project)
    pid = preset_id or data.get("use_case")
    preset = (_load_preset(project, pid) if pid else None) or {}
    if preset_id and not preset:
        raise Refused("Unknown delivery spec %r (a preset id from rules/presets.json)." % preset_id)
    deliv = dict(data.get("delivery") or {})
    res = preset.get("resolution")
    res_text = res.get("delivery") if isinstance(res, dict) else res
    wh = parse_wh(deliv.get("resolution")) or parse_wh(res_text)
    dur = preset.get("duration") if isinstance(preset.get("duration"), dict) else {}
    formats = deliv.get("formats") or preset.get("delivery_formats") or []
    lufs = deliv.get("loudness_lufs")
    if lufs is None:
        m = re.search(r"(-\d+(?:\.\d+)?)\s*LUFS", str(preset.get("loudness") or ""))
        lufs = float(m.group(1)) if m else DEFAULT_LUFS
    tp = deliv.get("true_peak_dbtp")
    if tp is None:
        m = re.search(r"(-\d+(?:\.\d+)?)\s*dBTP", str(preset.get("loudness") or ""))
        tp = float(m.group(1)) if m else MAX_TRUE_PEAK
    audio = deliv.get("audio", preset.get("audio"))
    if audio is True:
        audio = "required"
    elif audio is False:
        audio = "none"
    spec = {
        "preset": pid,
        "kind": deliv.get("kind") or preset.get("kind") or "video",
        "aspect": deliv.get("aspect") or preset.get("aspect"),
        "width": wh[0] if wh else None, "height": wh[1] if wh else None,
        "resolution_text": deliv.get("resolution") or res_text,
        "fps": deliv.get("fps") or preset.get("fps"),
        "duration_min": dur.get("min"), "duration_max": dur.get("max"),
        "duration_tolerance_s": deliv.get("duration_tolerance_s", DEFAULT_DUR_TOL),
        "handles_s": preset.get("handles_s") or 0,
        "codecs": deliv.get("codecs") or _codecs(formats) or ["h264", "hevc", "prores", "vp9", "av1"],
        "image_formats": deliv.get("image_formats") or _image_formats(formats) or ["png", "mjpeg", "webp"],
        "audio": audio or "optional",
        "loudness_lufs": float(lufs), "loudness_tolerance": float(deliv.get("loudness_tolerance", LUFS_TOL)),
        "max_true_peak_dbtp": float(tp),
        "max_file_mb": deliv.get("max_file_mb") or preset.get("max_file_mb")
        or _max_mb(res_text, formats, preset.get("delivery_formats")),
        "formats": list(formats),
    }
    for k, v in (overrides or {}).items():
        if v is not None:
            spec[k] = v
    return spec


# ---------------------------------------------------------------- planned durations

def _planned(project):
    """{shot: duration_s} from the shot list, falling back to each card's settings.duration_s."""
    from . import stages
    out = {}
    try:
        for row in stages.parse_shotlist(project):
            if row.get("id") and row.get("duration_value"):
                out[row["id"]] = float(row["duration_value"])
    except Exception:
        pass
    pdir = os.path.join(project, "05_prompts")
    if os.path.isdir(pdir):
        for f in sorted(os.listdir(pdir)):
            if not f.endswith(".md"):
                continue
            meta = stages.read_card_meta(os.path.join(pdir, f)) or {}
            sid = meta.get("id") or os.path.splitext(f)[0]
            d = _float((meta.get("settings") or {}).get("duration_s"))
            if sid not in out and d:
                out[sid] = d
    return out


# ---------------------------------------------------------------- checks

def _item(results, rel, name, ok, expected, actual, note=None):
    results.append({"name": "%s: %s" % (rel, name), "file": rel, "check": name,
                    "expected": expected, "actual": actual, "verdict": "PASS" if ok else "FAIL",
                    "note": note})


def _delivery_files(project):
    d = os.path.join(project, "10_delivery")
    out = []
    for root, dirs, files in os.walk(d):
        dirs[:] = [x for x in dirs if not x.startswith(".")]
        for f in sorted(files):
            if f.startswith(".") or os.path.splitext(f)[1].lower() in SKIP_EXT:
                continue
            out.append(os.path.join(root, f))
    return sorted(out)


def _check_file(path, rel, spec, planned, single_video, results, notes, duration_override):
    p = probe(path)
    kind = p["kind"]
    if kind not in ("video", "image", "audio"):
        _item(results, rel, "readable media", False, "video, image or audio", p["format_name"] or "unknown")
        return p
    w, h = p["width"], p["height"]
    if kind in ("video", "image"):
        if spec["width"] and spec["height"]:
            ok = (w, h) == (spec["width"], spec["height"])
            _item(results, rel, "resolution", ok, "%dx%d" % (spec["width"], spec["height"]), "%sx%s" % (w, h))
        elif spec["resolution_text"]:
            notes.append("%s: no exact size in the spec (%s); only the aspect was checked."
                         % (rel, spec["resolution_text"]))
        want = ratio_of(spec["aspect"])
        if want and w and h:
            ok = abs(float(w) / h - want) / want < 0.01
            _item(results, rel, "aspect", ok, spec["aspect"], aspect_name(w, h))
        elif spec["aspect"] and not want:
            notes.append("%s: aspect '%s' is not a fixed ratio; not checked." % (rel, spec["aspect"]))
    if kind == "image":
        allowed = spec["image_formats"]
        if p["vcodec"] and allowed:
            _item(results, rel, "image format", p["vcodec"] in allowed, ", ".join(allowed), p["vcodec"])
    if kind == "video":
        if spec["fps"]:
            ok = p["fps"] is not None and abs(float(p["fps"]) - float(spec["fps"])) < 0.05
            _item(results, rel, "frame rate", ok, spec["fps"], p["fps"])
        _item(results, rel, "video codec", p["vcodec"] in spec["codecs"], ", ".join(spec["codecs"]), p["vcodec"])
        if p["vcodec"] == "h264" and p["pix_fmt"] and p["pix_fmt"] != "yuv420p":
            notes.append("%s: pixel format %s; most platforms and players want yuv420p." % (rel, p["pix_fmt"]))
        # duration
        tol = float(spec["duration_tolerance_s"] or DEFAULT_DUR_TOL)
        expected, why = None, None
        if duration_override:
            expected, why = float(duration_override), "--duration"
        else:
            m = re.search(r"(S\d{2,4})", os.path.basename(rel))
            if m and m.group(1) in planned:
                expected = planned[m.group(1)] + 2 * float(spec.get("handles_s") or 0)
                why = "planned length of %s%s" % (m.group(1), " plus handles" if spec.get("handles_s") else "")
            elif single_video and planned:
                expected, why = round(sum(planned.values()), 3), "planned total of the shot list"
        if expected is not None and p["duration"] is not None:
            ok = abs(p["duration"] - expected) <= tol
            _item(results, rel, "duration", ok, "%.2f s (+/- %.2f, %s)" % (expected, tol, why),
                  "%.2f s" % p["duration"])
        elif p["duration"] is not None and (spec["duration_min"] is not None or spec["duration_max"] is not None):
            lo = spec["duration_min"] if spec["duration_min"] is not None else 0
            hi = spec["duration_max"] if spec["duration_max"] is not None else float("inf")
            ok = lo - tol <= p["duration"] <= hi + tol
            _item(results, rel, "duration", ok, "%s-%s s (preset range)" % (lo, spec["duration_max"]),
                  "%.2f s" % p["duration"])
    if kind in ("video", "audio"):
        need = str(spec["audio"] or "optional").lower()
        if need in ("required", "yes", "true", "dialogue", "music"):
            _item(results, rel, "audio present", p["has_audio"], "an audio track", "audio" if p["has_audio"]
                  else "no audio")
        elif need in ("none", "no", "false", "silent"):
            _item(results, rel, "no audio", not p["has_audio"], "no audio track", "audio" if p["has_audio"]
                  else "no audio")
        elif not p["has_audio"] and kind == "video":
            notes.append("%s: no audio track (the spec says audio is %s)." % (rel, need))
        if p["has_audio"]:
            lu = loudness(path)
            p["loudness"] = lu
            if lu is None:
                notes.append("%s: could not measure loudness (ffmpeg missing or no ebur128)." % rel)
            else:
                target, ltol = spec["loudness_lufs"], spec["loudness_tolerance"]
                il = lu["integrated_lufs"]
                ok = il is not None and abs(il - target) <= ltol
                _item(results, rel, "loudness", ok, "%.1f LUFS (+/- %.1f)" % (target, ltol),
                      "%.1f LUFS" % il if il is not None else "silent",
                      None if ok else "Normalise the mix to %.1f LUFS integrated." % target)
                tp = lu["true_peak_dbtp"]
                if tp is not None:
                    ok = tp <= spec["max_true_peak_dbtp"]
                    _item(results, rel, "true peak", ok, "<= %.1f dBTP" % spec["max_true_peak_dbtp"],
                          "%.1f dBTP" % tp)
    if spec["max_file_mb"] and p["size_bytes"] is not None:
        mb = p["size_bytes"] / (1024.0 * 1024.0)
        _item(results, rel, "file size", mb <= float(spec["max_file_mb"]), "<= %s MB" % spec["max_file_mb"],
              "%.2f MB" % mb)
    return p


def check(project, preset_id=None, duration=None, tolerance=None, lufs=None, write=True):
    overrides = {"duration_tolerance_s": tolerance, "loudness_lufs": lufs}
    spec = spec_for(project, preset_id, overrides)
    files = _delivery_files(project)
    results, notes, probes = [], [], {}
    if not files:
        results.append({"name": "files present", "check": "files present", "file": None,
                        "expected": "at least one media file in 10_delivery/", "actual": "none",
                        "verdict": "FAIL", "note": "Export the delivery files into 10_delivery/ first."})
    else:
        if not have_tools():
            raise ShotcraftError("ffprobe is not installed, so delivery files cannot be checked. Install ffmpeg.")
        planned = _planned(project)
        videos = [f for f in files if manifest.guess_kind(f) == "video"]
        for f in files:
            rel = os.path.relpath(f, project).replace(os.sep, "/")
            try:
                probes[rel] = _check_file(f, rel, spec, planned, len(videos) == 1, results, notes, duration)
            except ShotcraftError as exc:
                _item(results, rel, "readable media", False, "a file ffprobe can read", str(exc)[:200])
    verdict = "PASS" if results and all(r["verdict"] == "PASS" for r in results) else "FAIL"
    report = {"schema": 1, "checked_at": jsonio.now_iso(), "verdict": verdict, "spec": spec,
              "files": probes, "checks": results, "notes": notes,
              "failed": [r["name"] for r in results if r["verdict"] != "PASS"]}
    if write:
        jsonio.write_json(os.path.join(project, REPORT), report)
        report["report"] = REPORT
    return report


def _fmt(rep):
    lines = ["Delivery check: %s (%d checks, %d failed). Report: %s"
             % (rep["verdict"], len(rep["checks"]), len(rep["failed"]), rep.get("report", REPORT))]
    for r in rep["checks"]:
        if r["verdict"] != "PASS":
            lines.append("  FAIL %s: wanted %s, got %s%s" % (r["name"], r["expected"], r["actual"],
                                                           (" - " + r["note"]) if r.get("note") else ""))
    for n in rep["notes"]:
        lines.append("  note: %s" % n)
    return "\n".join(lines)


def cli_delivery_check(args):
    from . import project as _project
    proj = _project.resolve(getattr(args, "project", None), getattr(args, "session_id", None))
    rep = check(proj, preset_id=getattr(args, "spec", None), duration=getattr(args, "duration", None),
                tolerance=getattr(args, "tolerance", None), lufs=getattr(args, "lufs", None))
    if getattr(args, "json", False):
        print(json.dumps(rep, indent=2, ensure_ascii=False, default=str))
    else:
        print(_fmt(rep))
    return 0 if rep["verdict"] == "PASS" else 2
