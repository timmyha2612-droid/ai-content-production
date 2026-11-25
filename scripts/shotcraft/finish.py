"""The natural-finish pass in post: matched film grain (and an optional mild vignette) on pictures, and a
room-tone safety floor under sound, so a piece never looks sterile-perfect or drops to digital silence.

This is a craft pass for a natural look, not a way to hide that a piece is AI-made or to beat AI detectors. It
never crops or covers a watermark. Like any edit, an ffmpeg re-encode or remux does not carry Content
Credentials (C2PA) over, so realistic AI content needs the platform's AI label when it is posted.

Where files go. Paths are relative to the current directory. When --out is not given the result lands next to
the source as <name>-texture.<ext> / <name>-roomtone.<ext>; inside a 09_delivery folder that would leave a work
file among the deliverables (which fails the delivery check), so finish refuses there. Chain instead:
    sc.py finish texture  08_assembly/reel.mp4 --out 08_assembly/reel-texture.mp4
    sc.py finish roomtone 08_assembly/reel-texture.mp4 --out 09_delivery/reel.mp4

    texture: ffmpeg's noise filter (temporal + uniform, so the grain moves like film rather than sitting on the
             frame like a screen door) at a fixed strength, plus vignette when asked. One setting per job
             (decided at intake, "Grain:" on the job card): every shot gets the same grain so the cut matches.
             The noise and vignette filters work in 8-bit, so a source deeper than 8 bits goes through an
             8-bit filter stage and is written back at its delivery depth (10-bit ProRes stays 10-bit, but the
             grain itself is 8-bit). Alpha is split off before the filters and merged back untouched, so
             ProRes 4444 with alpha stays 4444 with alpha. Audio is copied untouched when the destination
             container can hold it, else re-encoded (said in the result). The source frame rate is kept exactly
             (no -r, so 23.976 / 29.97 stay rational). Stills: PNG lossless, JPEG -q:v 2, WebP quality 95.
    roomtone: one bed laid under the existing audio at a very low level (dBFS), looped to length: the given
             recording (one neutral room tone, preferred), or else generated pink noise, low-passed so it reads
             as air rather than hiss. This is a single-bed safety floor for a deliverable that still fails the
             digital-silence check; per-scene ambience beds belong to the sound stage's mix. The source channel
             layout is kept; a file with more than one audio track is refused. When the audio ends before the
             picture it is padded to the picture's length first, so the bed covers the tail. The picture is
             copied untouched. The result is checked for digital silence afterwards.

Codecs by destination container (combinations that cannot work are refused before ffmpeg runs):
    video  .mp4 .m4v .mov -> H.264 CRF 14 (ProRes 422 HQ, or 4444 with alpha, when a .mov source is ProRes or
                             deeper than 8 bits); .webm -> VP9 + Opus
    audio  .mp3 -> libmp3lame; .flac -> flac; .wav .aif .aiff -> 24-bit PCM (or the source PCM depth);
           .m4a / .mp4 -> AAC; .mov -> AAC, or PCM kept when the source audio (.mov/.mxf) is PCM;
           .ogg .opus -> Opus; .webm -> Opus
    stills .png .jpg .jpeg .webp .tif .tiff

API:
    GRAIN = {"off": 0, "subtle": 6, "film": 12}       ffmpeg noise strength per setting
    texture(src, grain="subtle", vignette=False, out=None) -> {"path", "grain", "vignette", "codec", "notes"}
    roomtone(src, bed=None, level=-60.0, out=None) -> {"path", "bed", "level_dbfs", "codec", "padded_to_s",
                                                       "digital_silence", "notes"}
    cli_finish_texture(args) -> int     sc.py finish texture <file> [--grain off|subtle|film] [--vignette] [--out P]
    cli_finish_roomtone(args) -> int    sc.py finish roomtone <file> [--bed FILE] [--level -60] [--out P]
"""
import json
import os
import re
import shutil
import subprocess

from . import Refused, ShotcraftError
from .delivery import digital_silence, probe, run

GRAIN = {"off": 0, "subtle": 6, "film": 12}
VIGNETTE_ANGLE = 0.45          # radians; ffmpeg's default (PI/5, about 0.63) is heavier than a real lens
LEVEL_MIN, LEVEL_MAX = -80.0, -40.0
BED_LOWPASS_HZ = 6000
DELIVERY_DIR = "09_delivery"

VIDEO_EXT = (".mp4", ".m4v", ".mov", ".webm")
AUDIO_EXT = (".mp3", ".flac", ".wav", ".aif", ".aiff", ".m4a", ".ogg", ".opus")
IMAGE_EXT = (".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff")
# video codecs each container can carry when the picture is stream-copied (roomtone)
VIDEO_COPY_OK = {
    ".mp4": {"h264", "hevc", "av1", "mpeg4", "vp9"},
    ".m4v": {"h264", "hevc", "av1", "mpeg4"},
    ".mov": {"h264", "hevc", "av1", "mpeg4", "prores", "dnxhd", "mjpeg", "png", "qtrle", "hap"},
    ".webm": {"vp8", "vp9", "av1"},
}
# audio codecs each container can carry when the sound is stream-copied (texture)
AUDIO_COPY_OK = {
    ".mp4": {"aac", "mp3", "alac", "ac3", "eac3", "opus", "flac"},
    ".m4v": {"aac", "mp3", "alac", "ac3", "eac3"},
    ".mov": {"aac", "mp3", "alac", "ac3", "eac3"},  # plus any pcm_* (see _audio_copy_ok)
    ".webm": {"opus", "vorbis"},
}
SRC_PCM_KEEP = (".mov", ".mxf")


def _need_ffmpeg():
    if not (shutil.which("ffmpeg") and shutil.which("ffprobe")):
        raise ShotcraftError("ffmpeg is not installed, so the finish pass cannot run. "
                             "Install it (brew install ffmpeg / apt install ffmpeg).")


def _in_delivery(path):
    parts = os.path.normpath(os.path.abspath(path)).split(os.sep)
    return DELIVERY_DIR in parts[:-1]


def _out_path(src, out, tag):
    if out:
        dest = os.path.abspath(out)
    else:
        if _in_delivery(src):
            raise Refused(
                "%s is inside %s/ and no --out was given, so the result would land there as a work file "
                "(work files left in %s/ fail the delivery check). Write the work file to 08_assembly/ and the "
                "final file to %s/, e.g.: sc.py finish texture <file> --out 08_assembly/<name>-texture.mp4, "
                "then sc.py finish roomtone 08_assembly/<name>-texture.mp4 --out %s/<name>.mp4 (paths are "
                "relative to the current directory)." % (os.path.basename(src), DELIVERY_DIR, DELIVERY_DIR,
                                                          DELIVERY_DIR, DELIVERY_DIR))
        stem, ext = os.path.splitext(src)
        dest = "%s-%s%s" % (stem, tag, ext)
    if os.path.abspath(src) == dest:
        raise Refused("The output would overwrite the source. Pick another --out; the original is kept.")
    return dest


_ENCODERS = None


def _need_encoder(name, why):
    """Refuse up front when this ffmpeg build lacks an encoder the destination needs."""
    global _ENCODERS
    if _ENCODERS is None:
        r = run(["ffmpeg", "-hide_banner", "-encoders"], timeout=60)
        _ENCODERS = set(re.findall(r"^\s*[VAS][.A-Z]{5}\s+(\S+)", r.stdout or "", re.M))
    if _ENCODERS and name not in _ENCODERS:
        raise Refused("This ffmpeg has no %s encoder, so it cannot write %s. Pick another format, or install "
                      "an ffmpeg build with %s." % (name, why, name))


def _root_cause(stderr):
    """The first meaningful lines of ffmpeg's stderr: the root cause comes first, the fallout after it."""
    lines = []
    for line in (stderr or "").splitlines():
        line = re.sub(r"^\[[^\]]*@ 0x[0-9a-f]+\]\s*", "", line.strip())
        if not line or line.startswith(("Press [q]", "frame=", "size=")):
            continue
        if line not in lines:
            lines.append(line[:240])
        if len(lines) == 3:
            break
    return " | ".join(lines) or "no error output"


def _ffmpeg(args, dest, what):
    d = os.path.dirname(dest)
    if d:
        os.makedirs(d, exist_ok=True)
    cmd = ["ffmpeg", "-y", "-hide_banner", "-nostdin", "-loglevel", "error"] + args + [dest]
    try:
        r = run(cmd, timeout=3600)
    except subprocess.TimeoutExpired:
        _remove(dest)
        raise ShotcraftError("ffmpeg timed out trying to %s; the partial output was removed." % what)
    if r.returncode != 0:
        _remove(dest)
        raise ShotcraftError("ffmpeg could not %s (partial output removed): %s" % (what, _root_cause(r.stderr)))


def _remove(path):
    try:
        os.remove(path)
    except OSError:
        pass


def _src(path):
    src = os.path.abspath(path)
    if not os.path.isfile(src):
        raise ShotcraftError("No such file: %s" % path)
    return src


def _streams(path):
    r = run(["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path], timeout=60)
    if r.returncode != 0:
        raise ShotcraftError("ffprobe could not read %s: %s" % (path, _root_cause(r.stderr)))
    data = json.loads(r.stdout or "{}")
    streams = data.get("streams") or []
    v = [s for s in streams if s.get("codec_type") == "video"
         and not (s.get("disposition") or {}).get("attached_pic")]
    a = [s for s in streams if s.get("codec_type") == "audio"]
    return v, a, data.get("format") or {}


def _bit_depth(vstream):
    pf = vstream.get("pix_fmt") or ""
    m = re.search(r"p(9|10|12|14|16)(le|be)?$", pf) or re.search(r"(10|12|16)(le|be)$", pf)
    if m:
        return int(m.group(1))
    raw = vstream.get("bits_per_raw_sample")
    try:
        return int(raw) if raw else 8
    except ValueError:
        return 8


def _has_alpha(vstream):
    pf = vstream.get("pix_fmt") or ""
    return pf.startswith(("yuva", "rgba", "bgra", "argb", "abgr", "gbrap", "ya")) or pf in ("pal8",)


def _audio_copy_ok(ext, acodec):
    if not acodec:
        return False
    if ext == ".mov" and acodec.startswith("pcm_"):
        return True
    return acodec in AUDIO_COPY_OK.get(ext, set())


def _pcm_codec(src_acodec, big_endian):
    """24-bit PCM, or the source PCM depth when the source is PCM, in the endianness the container needs."""
    m = re.match(r"pcm_(s|f|u)(8|16|24|32|64)(le|be)?$", src_acodec or "")
    kind, bits = (m.group(1), m.group(2)) if m else ("s", "24")
    if bits == "8":
        return "pcm_u8" if not big_endian else "pcm_s8"
    if kind == "u":
        kind = "s"
    return "pcm_%s%s%s" % (kind, bits, "be" if big_endian else "le")


def _audio_encoder(dest_ext, src_ext, src_acodec, channels):
    """ffmpeg -c:a args and a label for re-encoded audio in `dest_ext`."""
    if dest_ext == ".mp3":
        if channels and channels > 2:
            raise Refused("MP3 holds at most 2 channels and the source has %d. Use .wav, .flac or .m4a." % channels)
        _need_encoder("libmp3lame", "MP3 audio")
        return ["-c:a", "libmp3lame", "-q:a", "0"], "mp3 (VBR V0)"
    if dest_ext == ".flac":
        return ["-c:a", "flac"], "flac"
    if dest_ext in (".wav", ".aif", ".aiff"):
        c = _pcm_codec(src_acodec, dest_ext != ".wav")
        return ["-c:a", c], c
    if dest_ext in (".ogg", ".opus", ".webm"):
        _need_encoder("libopus", "Opus audio")
        return ["-c:a", "libopus", "-b:a", "192k"], "opus 192k"
    if dest_ext == ".mov" and (src_acodec or "").startswith("pcm_") and src_ext in SRC_PCM_KEEP:
        return ["-c:a", _pcm_codec(src_acodec, False)], _pcm_codec(src_acodec, False)
    if dest_ext in (".m4a", ".mp4", ".m4v", ".mov"):
        return ["-c:a", "aac", "-b:a", "320k"], "aac 320k"
    raise Refused("finish cannot write audio to %s files. Use one of: %s." % (dest_ext, ", ".join(AUDIO_EXT)))


# ---------------------------------------------------------------- texture

def texture(src, grain="subtle", vignette=False, out=None):
    _need_ffmpeg()
    src = _src(src)
    if grain not in GRAIN:
        raise ShotcraftError("--grain must be one of %s." % ", ".join(GRAIN))
    if not GRAIN[grain] and not vignette:
        raise Refused("Nothing to do: grain is off and no vignette was asked for (texture is skipped).")
    p = probe(src)
    if p["kind"] not in ("video", "image"):
        raise ShotcraftError("%s has no picture to texture." % os.path.basename(src))
    dest = _out_path(src, out, "texture")
    src_ext = os.path.splitext(src)[1].lower()
    ext = os.path.splitext(dest)[1].lower()
    vstreams, astreams, _ = _streams(src)
    if not vstreams:
        raise ShotcraftError("%s has no picture to texture." % os.path.basename(src))
    vs = vstreams[0]
    depth, alpha = _bit_depth(vs), _has_alpha(vs)
    notes = []

    if p["kind"] == "image":
        if ext not in IMAGE_EXT:
            raise Refused("A still must be written as a still (%s), not %s." % (", ".join(IMAGE_EXT), ext or
                                                                                 "no extension"))
    elif ext not in VIDEO_EXT:
        raise Refused("A video must be written to a video container (%s), not %s." % (", ".join(VIDEO_EXT), ext or
                                                                                       "no extension"))

    # picture codec for the destination
    enc, codec, out_fmt = [], None, None
    if p["kind"] == "image":
        if ext in (".jpg", ".jpeg"):
            enc, out_fmt = ["-q:v", "2"], "yuvj444p"
            if alpha:
                notes.append("JPEG has no alpha; the alpha channel was dropped.")
                alpha = False
        elif ext == ".webp":
            _need_encoder("libwebp", "WebP stills")
            enc = ["-c:v", "libwebp", "-quality", "95"]
        enc += ["-frames:v", "1", "-update", "1"]
    elif ext == ".webm":
        _need_encoder("libvpx-vp9", "WebM video")
        enc = ["-c:v", "libvpx-vp9", "-crf", "18", "-b:v", "0", "-row-mt", "1", "-deadline", "good"]
        out_fmt = "yuva420p" if alpha else "yuv420p"
        codec = "vp9 (CRF 18)"
    elif ext == ".mov" and (p["vcodec"] == "prores" or depth > 8):
        if alpha:
            enc, out_fmt, codec = ["-c:v", "prores_ks", "-profile:v", "4"], "yuva444p10le", "prores (4444, alpha)"
        else:
            enc, out_fmt, codec = ["-c:v", "prores_ks", "-profile:v", "3"], "yuv422p10le", "prores (422 HQ)"
    else:
        _need_encoder("libx264", "H.264 video")
        enc = ["-c:v", "libx264", "-crf", "14", "-preset", "slow"]
        out_fmt, codec = "yuv420p", "h264 (CRF 14)"
        if alpha:
            notes.append("H.264 has no alpha; the alpha channel was dropped (write a .mov to keep ProRes 4444).")
            alpha = False
        if depth > 8:
            notes.append("The %d-bit source was written as 8-bit H.264 (write a .mov for 10-bit ProRes)." % depth)
    if ext in (".mp4", ".m4v", ".mov") and p["kind"] == "video":
        enc += ["-movflags", "+faststart"]

    # filters: 8-bit stage (noise and vignette are 8-bit only); alpha split off and merged back untouched
    look = []
    if vignette:
        look.append("vignette=angle=%s" % VIGNETTE_ANGLE)
    if GRAIN[grain]:
        look.append("noise=alls=%d:allf=t+u" % GRAIN[grain])
    work = "yuv444p" if (alpha or depth > 8 or p["kind"] == "image") else None
    if depth > 8:
        notes.append("Grain and vignette are applied in an 8-bit filter stage; the %d-bit source is written "
                     "back at %s." % (depth, out_fmt or "its own depth"))
    back = ",format=%s" % out_fmt if out_fmt else ""
    pre = "format=%s," % work if work else ""
    if alpha:
        a_fmt = "gray10le" if depth > 8 else "gray"
        graph = ("[0:v:0]split[m][a];[a]alphaextract,format=%s[al];[m]%s%s,format=%s[c];"
                 "[c][al]alphamerge%s[v]" % (a_fmt, pre, ",".join(look),
                                             "yuv444p10le" if depth > 8 else "yuv444p", back))
    else:
        graph = "[0:v:0]%s%s%s[v]" % (pre, ",".join(look), back)
    args = ["-i", src, "-filter_complex", graph, "-map", "[v]"] + enc

    if p["kind"] == "video" and astreams:
        args += ["-map", "0:a"]
        if all(_audio_copy_ok(ext, a.get("codec_name")) for a in astreams):
            args += ["-c:a", "copy"]
        else:
            a_args, a_label = _audio_encoder(ext, src_ext, astreams[0].get("codec_name"),
                                             max(a.get("channels") or 0 for a in astreams))
            args += a_args
            notes.append("The audio (%s) cannot go into %s as it is, so it was re-encoded to %s."
                         % (astreams[0].get("codec_name"), ext, a_label))
    if p["kind"] == "video":
        args += ["-map_metadata", "0"]
    _ffmpeg(args, dest, "add the texture")
    return {"path": dest, "grain": grain, "vignette": bool(vignette), "codec": codec, "notes": notes}


# ---------------------------------------------------------------- room tone

def _stream_end(s, fmt):
    for val in (s.get("duration"), (s.get("tags") or {}).get("DURATION"), fmt.get("duration")):
        if not val:
            continue
        m = re.match(r"(\d+):(\d+):([\d.]+)$", str(val))
        try:
            secs = (int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))) if m else float(val)
        except ValueError:
            continue
        try:
            start = float(s.get("start_time") or 0)
        except ValueError:
            start = 0.0
        return max(0.0, secs + start)
    return None


def roomtone(src, bed=None, level=-60.0, out=None):
    _need_ffmpeg()
    src = _src(src)
    level = float(level)
    if not LEVEL_MIN <= level <= LEVEL_MAX:
        raise ShotcraftError("--level must be between %d and %d dBFS (room tone sits well under the mix)."
                             % (LEVEL_MIN, LEVEL_MAX))
    p = probe(src)
    vstreams, astreams, fmt = _streams(src)
    if not astreams:
        raise Refused("%s has no audio track to lay room tone under. Add the sound mix first."
                      % os.path.basename(src))
    if len(astreams) > 1:
        raise Refused("%s has %d audio tracks; roomtone lays one bed under one mix. Mix down to a single "
                      "track (or split the tracks) first, then run roomtone on it."
                      % (os.path.basename(src), len(astreams)))
    dest = _out_path(src, out, "roomtone")
    src_ext = os.path.splitext(src)[1].lower()
    ext = os.path.splitext(dest)[1].lower()
    a = astreams[0]
    has_video = p["kind"] == "video" and bool(vstreams)
    notes = []

    # what the destination can hold, decided before ffmpeg runs
    if ext in VIDEO_EXT and has_video:
        vcodec = vstreams[0].get("codec_name")
        if vcodec not in VIDEO_COPY_OK[ext]:
            raise Refused("The picture (%s) cannot be copied into a %s file untouched. Write a %s instead."
                          % (vcodec, ext, " or ".join(e for e, ok in VIDEO_COPY_OK.items() if vcodec in ok)
                             or "file in the source's own container (%s)" % src_ext))
    elif ext in VIDEO_EXT and not has_video:
        if ext == ".mov" or ext == ".webm":
            raise Refused("%s has no picture; write the audio to an audio file (%s)."
                          % (os.path.basename(src), ", ".join(AUDIO_EXT)))
    elif ext in AUDIO_EXT:
        if has_video:
            notes.append("The destination is audio only, so the picture was left out.")
    else:
        raise Refused("finish roomtone cannot write %s files. Use a video container (%s) or an audio file (%s)."
                      % (ext or "extension-less", ", ".join(VIDEO_EXT), ", ".join(AUDIO_EXT)))
    a_args, a_label = _audio_encoder(ext, src_ext, a.get("codec_name"), a.get("channels"))

    channels = a.get("channels") or 2
    layout = a.get("channel_layout") or ("mono" if channels == 1 else "stereo" if channels == 2
                                         else "%dc" % channels)
    rate = int(a.get("sample_rate") or 48000)
    if ext in (".ogg", ".opus", ".webm") and rate not in (8000, 12000, 16000, 24000, 48000):
        rate = 48000
    fmt_chain = "aformat=sample_rates=%d:channel_layouts=%s" % (rate, layout)

    args = ["-i", src]
    if bed:
        bed_abs = _src(bed)
        if not probe(bed_abs)["has_audio"]:
            raise ShotcraftError("The bed %s has no audio." % os.path.basename(bed_abs))
        # level the bed as it will sound in the output layout
        mean = _mean_volume_chain(["-t", "30", "-i", bed_abs], fmt_chain)
        if mean is None:
            raise ShotcraftError("The bed %s is silent." % os.path.basename(bed_abs))
        args += ["-stream_loop", "-1", "-i", bed_abs]
        bed_chain = "[1:a]%s,volume=%.2fdB" % (fmt_chain, level - mean)
        bed_name = os.path.basename(bed_abs)
    else:
        # The noise source's amplitude is a peak value; measure a fixed-seed sample of the shaped noise in the
        # output layout so the bed's average level lands on --level, the same way a recorded bed is levelled.
        noise = "anoisesrc=color=pink:sample_rate=%d:amplitude=0.5:seed=7" % rate
        shaped = "lowpass=f=%d,%s" % (BED_LOWPASS_HZ, fmt_chain)
        mean = _mean_volume_chain(["-f", "lavfi", "-i", "%s:duration=5" % noise], shaped)
        if mean is None:
            raise ShotcraftError("Could not measure the generated room tone (ffmpeg anoisesrc).")
        args += ["-f", "lavfi", "-i", noise]
        bed_chain = "[1:a]%s,volume=%.2fdB" % (shaped, level - mean)
        bed_name = None

    # pad the main audio to the picture's length so the bed also covers a tail where the audio ran out
    pad, padded_to = "", None
    if has_video:
        v_end = _stream_end(vstreams[0], fmt)
        a_end = _stream_end(a, fmt)
        if v_end and (a_end is None or a_end < v_end - 0.01):
            pad, padded_to = ",apad=whole_dur=%.3f" % v_end, round(v_end, 3)
            if a_end is not None and v_end - a_end >= 0.5:
                notes.append("The audio ended %.2f s before the picture; it was padded to %.2f s and the bed "
                             "covers the tail." % (v_end - a_end, v_end))
    graph = ("[0:a]%s%s[main];%s[bed];[main][bed]amix=inputs=2:duration=first:dropout_transition=0:"
             "normalize=0[aout]" % (fmt_chain, pad, bed_chain))
    args += ["-filter_complex", graph]
    if ext in VIDEO_EXT and has_video:
        args += ["-map", "0:v:0", "-c:v", "copy"]
        if ext in (".mp4", ".m4v", ".mov"):
            args += ["-movflags", "+faststart"]
    args += ["-map", "[aout]"] + a_args + ["-map_metadata", "0"]
    _ffmpeg(args, dest, "lay the room tone")
    return {"path": dest, "bed": bed_name or "generated pink noise (fallback)", "level_dbfs": level,
            "codec": a_label, "layout": layout, "padded_to_s": padded_to, "notes": notes,
            "digital_silence": digital_silence(dest)}


def _mean_volume_chain(inputs, chain):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-nostdin"] + inputs +
            ["-vn", "-af", "%s,volumedetect" % chain, "-f", "null", "-"], timeout=300)
    m = re.search(r"mean_volume:\s*(-?[\d.]+|-inf)\s*dB", r.stderr or "")
    if not m or m.group(1) == "-inf":
        return None
    return float(m.group(1))


# ---------------------------------------------------------------- CLI

def _print(args, res, human):
    if getattr(args, "json", False):
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        print(human)
        for n in res.get("notes") or []:
            print("  note: %s" % n)


def cli_finish_texture(args):
    res = texture(args.file, grain=getattr(args, "grain", None) or "subtle",
                  vignette=bool(getattr(args, "vignette", False)), out=getattr(args, "out", None))
    _print(args, res, "Texture: %s (grain %s%s%s). Use the same setting on every shot of the job."
           % (res["path"], res["grain"], ", mild vignette" if res["vignette"] else "",
              ", " + res["codec"] if res["codec"] else ""))
    return 0


def cli_finish_roomtone(args):
    level = getattr(args, "level", None)
    res = roomtone(args.file, bed=getattr(args, "bed", None), level=-60.0 if level is None else level,
                   out=getattr(args, "out", None))
    gaps = res["digital_silence"]
    tail = ("no digital silence left" if gaps == [] else
            "could not re-check (ffmpeg)" if gaps is None else
            "still silent at " + ", ".join("%.2f-%.2f s" % g for g in gaps))
    _print(args, res, "Room tone: %s (%s at %.0f dBFS, %s; %s)."
           % (res["path"], res["bed"], res["level_dbfs"], res["codec"], tail))
    return 0 if not gaps else 2
