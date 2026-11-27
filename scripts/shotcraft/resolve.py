"""The DaVinci hand-off: the approved finals laid out for DaVinci Resolve (SPEC: handoff stage, on request).

`sc.py handoff resolve` writes, under 10_handoff/resolve/:
    SC01/SC01_S010_v1.mp4 ...   the approved take of every shot (upscale over final), filed by scene
    timeline.fcpxml             one timeline with every shot in shot-list order at its planned cut length,
                                trimmed past the handles. In Resolve: File > Import > Timeline.
    shots.csv                   scene, place, time, shot, length, purpose, elements, file, take, model, prompt
and records the package in project.json ("resolve_package", with sha256 per file) for the stage check.

API:
    plan(project) -> {"fps", "width", "height", "clips": [...], "problems": [...]}
    build(project) -> record
    fcpxml(clips, fps, width, height, name) -> str
    cli_handoff_resolve(args)

Stdlib only (ffprobe when present, for each clip's real length).
"""
import csv
import json
import os
import re
import shutil
from fractions import Fraction
from urllib.parse import quote
from xml.sax.saxutils import escape, quoteattr

from . import Refused, ShotcraftError, jsonio, manifest, paths, stages

OUT_DIR = "10_handoff/resolve"
_NTSC = {23.976: (1001, 24000), 29.97: (1001, 30000), 59.94: (1001, 60000)}


def frame_duration(fps):
    """Rational seconds per frame: (num, den)."""
    f = float(fps)
    for k, v in _NTSC.items():
        if abs(f - k) < 0.01:
            return v
    return (1, int(round(f)))


def _t(frames, fd):
    fr = Fraction(frames * fd[0], fd[1])
    if fr.denominator == 1:
        return "%ds" % fr.numerator
    return "%d/%ds" % (fr.numerator, fr.denominator)


def _frames(seconds, fd):
    return int(round(float(seconds) * fd[1] / fd[0]))


def _probe(path):
    from . import delivery
    try:
        if delivery.have_tools():
            return delivery.probe(path)
    except ShotcraftError:
        pass
    return {}


def _chosen_take(gens, shot):
    for tiers in (("upscale",), ("final",)):
        ok = [g for g in gens if g.get("shot") == shot and g.get("tier") in tiers and g.get("approved") is True
              and g.get("status") == "completed" and g.get("outputs")]
        if ok:
            g = ok[-1]
            all_ = [x for x in gens if x.get("shot") == shot and x.get("tier") in tiers and x.get("status") == "completed"]
            return g, all_.index(g) + 1
    return None, None


def _wh(text):
    m = re.match(r"^\s*(\d+)\s*[x×]\s*(\d+)\s*$", str(text or ""))
    return (int(m.group(1)), int(m.group(2))) if m else (None, None)


def plan(project):
    data = manifest.load(project)
    gens = data.get("generations", [])
    rows = stages.parse_shotlist(project)
    if not rows:
        raise Refused("No shot list to lay the timeline out from (03_script/shotlist.md).")
    scenes = {s["scene"]: s for s in stages.parse_scenes(project)}
    inputs = stages.input_shots(project)
    clips, problems = [], []
    for r in rows:
        sid = r["id"]
        scn = str(r.get("scene") or "").strip() or "SC00"
        if sid in inputs:
            src, take, version, model, prompt = inputs[sid], None, 1, "user's own file", ""
        else:
            g, version = _chosen_take(gens, sid)
            if g is None:
                problems.append("%s has no approved final" % sid)
                continue
            src, take, model, prompt = g["outputs"][0], g["id"], g.get("model"), g.get("prompt") or ""
        card = stages.read_card_meta(os.path.join(project, "05_prompts", sid + ".md")) or {}
        ext = os.path.splitext(src)[1] or ".mp4"
        name = "%s_%s_v%d" % (scn, sid, version)
        clips.append({"shot": sid, "scene": scn, "src": src, "take": take, "model": model, "prompt": prompt,
                      "dest": "%s/%s/%s%s" % (OUT_DIR, scn, name, ext), "name": name,
                      "duration_s": r.get("duration_value") or (card.get("settings") or {}).get("duration_s") or 5,
                      "handles_s": card.get("handles_s") or 0, "purpose": r.get("purpose") or "",
                      "elements": r.get("elements") or (scenes.get(scn) or {}).get("elements") or "",
                      "place": (scenes.get(scn) or {}).get("place") or "",
                      "time": (scenes.get(scn) or {}).get("time") or ""})
    d = data.get("delivery") or {}
    fps = d.get("fps")
    width, height = _wh(d.get("resolution"))
    return {"fps": fps, "width": width, "height": height, "clips": clips, "problems": problems}


def fcpxml(clips, fps, width, height, name):
    fd = frame_duration(fps)
    out = ['<?xml version="1.0" encoding="UTF-8"?>', '<!DOCTYPE fcpxml>', '<fcpxml version="1.10">', '  <resources>',
           '    <format id="r0" name="FFVideoFormat%dx%dp%s" frameDuration="%s" width="%d" height="%d"/>' % (
               width, height, str(fps).replace(".", ""), _t(1, fd), width, height)]
    spine, offset = [], 0
    for i, c in enumerate(clips, start=1):
        rid = "r%d" % i
        src_frames = _frames(c["src_duration_s"], fd) if c.get("src_duration_s") else None
        start = _frames(c["handles_s"], fd) if c.get("handles_s") else 0
        dur = _frames(c["duration_s"], fd)
        if src_frames is not None:
            if start + dur > src_frames:
                start = max(0, min(start, src_frames - dur))
            dur = min(dur, src_frames - start)
        asset_dur = src_frames if src_frames is not None else start + dur
        url = "file://" + quote(c["abs"])
        has_audio = "1" if c.get("has_audio") else "0"
        out.append('    <asset id="%s" name=%s start="0s" duration="%s" hasVideo="1" hasAudio="%s" format="r0">'
                   % (rid, quoteattr(c["name"]), _t(asset_dur, fd), has_audio))
        out.append('      <media-rep kind="original-media" src=%s/>' % quoteattr(url))
        out.append('    </asset>')
        note = escape("%s %s: %s" % (c["scene"], c["shot"], c.get("purpose") or ""))
        spine.append('            <asset-clip ref="%s" name=%s offset="%s" start="%s" duration="%s" format="r0"%s>'
                     % (rid, quoteattr(c["name"]), _t(offset, fd), _t(start, fd), _t(dur, fd),
                        ' audioRole="dialogue"' if c.get("has_audio") else ""))
        spine.append('              <note>%s</note>' % note)
        spine.append('            </asset-clip>')
        offset += dur
    out.append('  </resources>')
    out += ['  <library>', '    <event name=%s>' % quoteattr(name), '      <project name=%s>' % quoteattr(name),
            '        <sequence format="r0" duration="%s" tcStart="0s" tcFormat="NDF">' % _t(offset, fd),
            '          <spine>'] + spine + ['          </spine>', '        </sequence>', '      </project>',
                                            '    </event>', '  </library>', '</fcpxml>']
    return "\n".join(out) + "\n"


def build(project):
    st = stages.load_state(project)
    if st["stages"].get("handoff", {}).get("status") != "open":
        raise Refused("The hand-off runs only when the user asks for it. With their words: sc.py stage include "
                      "handoff --user-said \"...\", then sc.py stage start handoff.")
    pl = plan(project)
    if pl["problems"]:
        raise Refused("Not every shot is ready: %s." % "; ".join(pl["problems"]))
    if not pl["clips"]:
        raise Refused("No shots to hand off.")
    base = os.path.join(project, OUT_DIR)
    if os.path.isdir(base):
        shutil.rmtree(base)
    os.makedirs(base)
    for c in pl["clips"]:
        src = os.path.join(project, c["src"])
        if not os.path.exists(src):
            raise Refused("%s's file %s is missing." % (c["shot"], c["src"]))
        dest = os.path.join(project, c["dest"])
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(src, dest)
        c["abs"] = os.path.abspath(dest)
        pr = _probe(dest)
        c["src_duration_s"] = pr.get("duration")
        c["has_audio"] = pr.get("has_audio")
        if not pl["fps"] and pr.get("fps"):
            pl["fps"] = round(pr["fps"], 3)
        if not pl["width"] and pr.get("width"):
            pl["width"], pl["height"] = pr["width"], pr["height"]
    fps = pl["fps"] or 30
    width, height = pl["width"] or 1920, pl["height"] or 1080
    name = os.path.basename(os.path.abspath(project))
    tl = os.path.join(base, "timeline.fcpxml")
    with open(tl, "w", encoding="utf-8") as fh:
        fh.write(fcpxml(pl["clips"], fps, width, height, name))
    csv_path = os.path.join(base, "shots.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["scene", "place", "time", "shot", "duration_s", "purpose", "elements", "file", "take", "model",
                    "prompt"])
        for c in pl["clips"]:
            w.writerow([c["scene"], c["place"], c["time"], c["shot"], c["duration_s"], c["purpose"], c["elements"],
                        os.path.relpath(c["dest"], OUT_DIR), c["take"] or "", c["model"] or "", c["prompt"]])
    files = {}
    for p in [tl, csv_path] + [os.path.join(project, c["dest"]) for c in pl["clips"]]:
        files[paths.rel_to(project, p)] = manifest.file_sha256(p)
    rec = {"built_at": jsonio.now_iso(), "timeline": paths.rel_to(project, tl), "csv": paths.rel_to(project, csv_path),
           "clips": len(pl["clips"]), "fps": fps, "width": width, "height": height, "files": files}
    data = manifest.load(project)
    data["resolve_package"] = rec
    manifest.save(project, data)
    return rec


def cli_handoff_resolve(args):
    from . import project as _p
    proj = _p.resolve(getattr(args, "project", None), getattr(args, "session_id", None))
    if getattr(args, "dry_run", False):
        pl = plan(proj)
        text = "\n".join("%s %s -> %s (%s s)" % (c["scene"], c["shot"], c["dest"], c["duration_s"])
                         for c in pl["clips"])
        if pl["problems"]:
            text += "\nNot ready:\n- " + "\n- ".join(pl["problems"])
        print(json.dumps(pl, indent=2) if getattr(args, "json", False) else text)
        return 0
    rec = build(proj)
    if getattr(args, "json", False):
        print(json.dumps(rec, indent=2))
    else:
        print("DaVinci package: %s (%d clips, %s fps, %dx%d), %s.\nIn Resolve: File > Import > Timeline, pick "
              "timeline.fcpxml." % (os.path.dirname(rec["timeline"]), rec["clips"], rec["fps"], rec["width"],
                                    rec["height"], rec["csv"]))
    return 0
