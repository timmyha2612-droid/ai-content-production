"""The animatic (a string-out of the shots in shot-list order), built with ffmpeg.

For each planned shot the best available picture is used:
    an approved upscale or final > any completed final > an approved draft > any completed draft
    > an approved board > any completed board > a black slate.
Video sources are trimmed: the cut skips the handles (card handles_s) at the head and plays the shot's planned
length (card settings.duration_s, else the shot list's duration, else the clip length). A still is held for the
planned length. Every segment is scaled and padded to the delivery frame (never stretched), at the delivery frame
rate. An optional audio file is laid under the whole cut (padded with silence or cut to length). Shot ids can be
burned in (top left) with --burn-ids.

Writes 09_assembly/animatic.mp4 and 09_assembly/shots.csv (an EDL-like list: order, shot, source, in/out points
and record in/out).

API:
    TIER_PREFERENCE
    frame_for(project) -> (width, height, fps)
    pick_source(project, shot, gens) -> {"tier", "generation", "path", "kind", "approved"} | None
    plan(project) -> [segment dicts]
    build(project, audio=None, burn_ids=False, out=None) -> {"path", "csv", "duration_s", "segments", "notes"}
    cli_assembly_animatic(args) -> int    sc.py assembly animatic [--audio FILE] [--burn-ids]
"""
import csv
import json
import os
import shutil
import tempfile

from . import Refused, ShotcraftError, manifest
from .delivery import parse_wh, probe, ratio_of, run

OUT = "09_assembly/animatic.mp4"
CSV = "09_assembly/shots.csv"
DEFAULT_STILL_S = 3.0
TIER_PREFERENCE = (("upscale", True), ("final", True), ("final", None), ("draft", True), ("draft", None),
                   ("board", True), ("board", None))


def _float(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _even(n):
    n = int(round(n))
    return n if n % 2 == 0 else n + 1


def frame_for(project):
    data = manifest.load(project)
    d = data.get("delivery") or {}
    preset = None
    try:
        from . import rules
        preset = rules.preset(data.get("use_case"), project) if data.get("use_case") else None
    except Exception:
        preset = None
    preset = preset or {}
    wh = parse_wh(d.get("resolution"))
    if not wh:
        res = preset.get("resolution")
        wh = parse_wh(res.get("delivery") if isinstance(res, dict) else res)
    if not wh:
        r = ratio_of(d.get("aspect") or preset.get("aspect")) or 16 / 9.0
        wh = (1920, _even(1920 / r)) if r >= 1 else (_even(1920 * r), 1920)
    w, h = wh
    if max(w, h) > 1920:  # an animatic never needs more than HD
        s = 1920.0 / max(w, h)
        w, h = _even(w * s), _even(h * s)
    fps = _float(d.get("fps")) or _float(preset.get("fps")) or 24.0
    return _even(w), _even(h), fps


def _exists(project, rel):
    return bool(rel) and os.path.isfile(os.path.join(project, rel))


def pick_source(project, shot, gens):
    mine = [g for g in gens if g.get("shot") == shot and g.get("status") == "completed"]
    for tier, need in TIER_PREFERENCE:
        cands = [g for g in mine if g.get("tier") == tier and (need is None or g.get("approved") is need)
                 and g.get("approved") is not False]
        for g in reversed(cands):  # newest first
            for o in g.get("outputs") or []:
                if _exists(project, o):
                    return {"tier": tier, "generation": g.get("id"), "path": o,
                            "kind": manifest.guess_kind(o), "approved": g.get("approved"),
                            "model": g.get("model")}
    return None


def plan(project):
    from . import stages
    data = manifest.load(project)
    gens = data.get("generations", [])
    rows = {}
    try:
        rows = {r["id"]: r for r in stages.parse_shotlist(project) if r.get("id")}
    except Exception:
        rows = {}
    shots = stages.planned_shots(project)
    if not shots:
        shots = []
        for g in gens:
            if g.get("shot") and g["shot"] not in shots:
                shots.append(g["shot"])
    segs = []
    for sid in shots:
        meta = stages.read_card_meta(os.path.join(project, "05_prompts", "%s.md" % sid)) or {}
        settings = meta.get("settings") or {}
        dur = _float(settings.get("duration_s")) or _float((rows.get(sid) or {}).get("duration_value"))
        handles = _float(meta.get("handles_s")) or 0.0
        src = pick_source(project, sid, gens)
        seg = {"shot": sid, "title": meta.get("title") or (rows.get(sid) or {}).get("purpose") or "",
               "planned_s": dur, "handles_s": handles, "source": src, "note": None}
        segs.append(seg)
    return segs


def _drawtext_ok():
    r = run(["ffmpeg", "-hide_banner", "-filters"], timeout=20)
    return "drawtext" in (r.stdout or "")


def _render_segment(seg, src_abs, dest, w, h, fps, burn, notes):
    """Render one segment to an H.264 file with no audio. Returns its real length in seconds."""
    vf = ("scale=%d:%d:force_original_aspect_ratio=decrease,pad=%d:%d:(ow-iw)/2:(oh-ih)/2:color=black,"
          "setsar=1,fps=%s,format=yuv420p" % (w, h, w, h, fps))
    dur = seg["out_s"]
    if burn:
        label = seg["shot"].replace(":", r"\:").replace("'", "")
        vf += (",drawtext=text='%s':x=24:y=24:fontsize=%d:fontcolor=white:box=1:boxcolor=black@0.55:boxborderw=8"
               % (label, max(18, h // 30)))
    enc = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-an",
           "-video_track_timescale", "90000"]
    if src_abs is None:
        cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=%dx%d:r=%s:d=%.3f"
               % (w, h, fps, dur), "-vf", vf, "-t", "%.3f" % dur] + enc + [dest]
    elif seg["source"]["kind"] == "image":
        cmd = ["ffmpeg", "-y", "-v", "error", "-loop", "1", "-framerate", str(fps), "-i", src_abs,
               "-vf", vf, "-t", "%.3f" % dur] + enc + [dest]
    else:
        pad = seg.get("pad_s") or 0
        vf2 = vf + ((",tpad=stop_mode=clone:stop_duration=%.3f" % pad) if pad > 0 else "")
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % seg["in_s"], "-i", src_abs, "-vf", vf2,
               "-t", "%.3f" % dur] + enc + [dest]
    r = run(cmd, timeout=600)
    if r.returncode != 0 or not os.path.isfile(dest):
        raise ShotcraftError("ffmpeg could not render shot %s: %s" % (seg["shot"], (r.stderr or "").strip()[:300]))
    return dur


def _tc(seconds, fps):
    fr = int(round(seconds * fps))
    f = int(round(fps))
    return "%02d:%02d:%02d:%02d" % (fr // (3600 * f), (fr // (60 * f)) % 60, (fr // f) % 60, fr % f)


def build(project, audio=None, burn_ids=False, out=None):
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        raise ShotcraftError("The animatic needs ffmpeg and ffprobe. Install ffmpeg (brew install ffmpeg / "
                             "apt install ffmpeg).")
    segs = plan(project)
    if not segs:
        raise Refused("There are no shots to assemble yet (no shot list, cards or generations).")
    w, h, fps = frame_for(project)
    notes = []
    if burn_ids and not _drawtext_ok():
        notes.append("This ffmpeg has no drawtext filter, so shot ids are not burned in.")
        burn_ids = False
    audio_abs = None
    if audio:
        audio_abs = audio if os.path.isabs(audio) else os.path.join(project, audio)
        if not os.path.isfile(audio_abs):
            audio_abs = os.path.abspath(os.path.expanduser(audio))
        if not os.path.isfile(audio_abs):
            raise ShotcraftError("No audio file at %s." % audio)
    # in/out points
    for seg in segs:
        src = seg["source"]
        seg["in_s"], seg["pad_s"] = 0.0, 0.0
        if src is None:
            seg["out_s"] = seg["planned_s"] or DEFAULT_STILL_S
            notes.append("%s has no picture yet; a black slate holds its place." % seg["shot"])
            continue
        if src["kind"] == "image":
            seg["out_s"] = seg["planned_s"] or DEFAULT_STILL_S
            continue
        clip = probe(os.path.join(project, src["path"]))["duration"] or 0.0
        want = seg["planned_s"] or max(0.1, clip - 2 * seg["handles_s"]) or DEFAULT_STILL_S
        hd = seg["handles_s"]
        if clip >= want + hd - 0.01:
            seg["in_s"] = hd if clip >= want + 2 * hd - 0.05 else max(0.0, (clip - want) / 2.0)
        elif clip >= want - 0.01:
            seg["in_s"] = max(0.0, (clip - want) / 2.0)
        else:
            seg["pad_s"] = want - clip
            notes.append("%s: the clip is %.2f s but the shot plays %.2f s; the last frame is held."
                         % (seg["shot"], clip, want))
        seg["out_s"] = round(want, 3)
    out_abs = os.path.join(project, out or OUT)
    os.makedirs(os.path.dirname(out_abs), exist_ok=True)
    tmpdir = tempfile.mkdtemp(prefix="sc-animatic-")
    try:
        parts = []
        for i, seg in enumerate(segs):
            dest = os.path.join(tmpdir, "seg%03d.mp4" % i)
            src_abs = os.path.join(project, seg["source"]["path"]) if seg["source"] else None
            _render_segment(seg, src_abs, dest, w, h, fps, burn_ids, notes)
            parts.append(dest)
        lst = os.path.join(tmpdir, "list.txt")
        with open(lst, "w", encoding="utf-8") as fh:
            for p in parts:
                fh.write("file '%s'\n" % p.replace("'", "'\\''"))
        total = round(sum(s["out_s"] for s in segs), 3)
        joined = os.path.join(tmpdir, "joined.mp4")
        r = run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy",
                 "-movflags", "+faststart", joined], timeout=600)
        if r.returncode != 0:
            raise ShotcraftError("ffmpeg could not join the shots: %s" % (r.stderr or "").strip()[:300])
        tmp_out = os.path.join(tmpdir, "final.mp4")
        if audio_abs:
            r = run(["ffmpeg", "-y", "-v", "error", "-i", joined, "-i", audio_abs, "-map", "0:v:0", "-map", "1:a:0",
                     "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-af", "apad", "-t", "%.3f" % total,
                     "-movflags", "+faststart", tmp_out], timeout=600)
            if r.returncode != 0:
                raise ShotcraftError("ffmpeg could not add the audio: %s" % (r.stderr or "").strip()[:300])
        else:
            tmp_out = joined
        shutil.move(tmp_out, out_abs)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
    # EDL-like CSV
    csv_abs = os.path.join(project, CSV)
    rec = 0.0
    rows = []
    for i, seg in enumerate(segs, 1):
        src = seg["source"] or {}
        row = {"order": i, "shot": seg["shot"], "title": seg["title"], "source_tier": src.get("tier") or "slate",
               "generation": src.get("generation") or "", "source_file": src.get("path") or "",
               "source_kind": src.get("kind") or "", "approved": {True: "yes", False: "no"}.get(src.get("approved"),
                                                                                               ""),
               "src_in_s": "%.3f" % seg["in_s"], "src_out_s": "%.3f" % (seg["in_s"] + seg["out_s"] - seg["pad_s"]),
               "duration_s": "%.3f" % seg["out_s"], "handles_s": "%.3f" % seg["handles_s"],
               "rec_in_s": "%.3f" % rec, "rec_out_s": "%.3f" % (rec + seg["out_s"]),
               "rec_in_tc": _tc(rec, fps), "rec_out_tc": _tc(rec + seg["out_s"], fps)}
        rec += seg["out_s"]
        rows.append(row)
    with open(csv_abs, "w", encoding="utf-8", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        wr.writeheader()
        wr.writerows(rows)
    return {"path": os.path.relpath(out_abs, project).replace(os.sep, "/"), "csv": CSV,
            "duration_s": round(rec, 3), "frame": "%dx%d" % (w, h), "fps": fps, "audio": bool(audio_abs),
            "segments": rows, "notes": notes}


def cli_assembly_animatic(args):
    from . import project as _project
    proj = _project.resolve(getattr(args, "project", None), getattr(args, "session_id", None))
    res = build(proj, audio=getattr(args, "audio", None), burn_ids=getattr(args, "burn_ids", False))
    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        lines = ["Animatic: %s (%.2f s, %s at %s fps%s). Shot list: %s"
                 % (res["path"], res["duration_s"], res["frame"], res["fps"], ", with audio" if res["audio"] else "",
                    res["csv"])]
        for s in res["segments"]:
            lines.append("  %s  %-6s %6ss  %s" % (s["shot"], s["source_tier"], s["duration_s"],
                                                  s["source_file"] or "black slate"))
        lines += ["  note: " + n for n in res["notes"]]
        print("\n".join(lines))
    return 0
