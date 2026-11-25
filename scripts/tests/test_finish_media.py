"""Media tests for the finish pass (sc.py finish texture / roomtone) and the delivery checks it answers.

Real ffmpeg on small synthetic clips: the grain really changes the picture, audio is untouched by texture,
codecs follow the destination container, room tone lands near --level, keeps the channel layout, pads audio
that ends before the picture, and finish refuses to drop work files into 09_delivery/. Skipped without ffmpeg.
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import sc  # noqa: E402
from shotcraft import Refused, ShotcraftError, delivery, finish, project  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-nostdin"] + list(args), check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def ffprobe_streams(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_streams", "-of", "json", path],
                       stdout=subprocess.PIPE, universal_newlines=True, check=True)
    return json.loads(r.stdout)["streams"]


def stream(path, kind):
    return next(s for s in ffprobe_streams(path) if s["codec_type"] == kind)


def audio_md5(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-nostdin", "-i", path, "-map", "0:a:0", "-f", "md5", "-"],
                       stdout=subprocess.PIPE, universal_newlines=True, check=True)
    return r.stdout.strip()


def psnr(a, b):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-i", a, "-i", b, "-lavfi",
                        "[0:v][1:v]psnr", "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                       universal_newlines=True)
    m = re.search(r"average:([\d.]+|inf)", r.stderr)
    return float("inf") if m.group(1) == "inf" else float(m.group(1))


def mean_db(path, start, length):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-ss", str(start), "-t", str(length), "-i", path,
                        "-vn", "-af", "volumedetect", "-f", "null", "-"], stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, universal_newlines=True)
    return float(re.search(r"mean_volume:\s*(-?[\d.]+)", r.stderr).group(1))


def clip(path, w=320, h=240, dur=3, tone=1, rate="30", vcodec=("libx264", "-preset", "ultrafast", "-pix_fmt",
                                                               "yuv420p"), acodec=("aac",), audio_dur=None):
    """Video with a tone for `tone` s then digital silence; audio_dur < dur makes the audio end early."""
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)
    adur = dur if audio_dur is None else audio_dur
    ff("-f", "lavfi", "-i", "testsrc=size=%dx%d:rate=%s:duration=%s" % (w, h, rate, dur),
       "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=%s,apad=whole_dur=%s" % (
           min(tone, adur), adur),
       "-c:v", *vcodec, "-c:a", *acodec, "-t", str(dur), path)
    return path


def audio_file(path, dur=3, tone=1, layout="mono", extra=()):
    ff("-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=%s,apad=whole_dur=%s,"
       "aformat=channel_layouts=%s" % (tone, dur, layout), *extra, path)
    return path


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class FinishMediaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-finish-media-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home"),
                                                "SHOTCRAFT_PROVIDER": "fake"})
        self.env.start()
        os.environ.pop("CLAUDE_SESSION_ID", None)
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def p(self, *parts):
        return os.path.join(self.tmp, *parts)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = sc.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    # ------------------------------------------------------------ texture

    def test_texture_changes_picture_and_leaves_audio_alone(self):
        src = clip(self.p("a.mp4"))
        res = finish.texture(src, grain="film")
        self.assertLess(psnr(src, res["path"]), 50)
        self.assertEqual(audio_md5(src), audio_md5(res["path"]))
        self.assertEqual(stream(res["path"], "video")["codec_name"], "h264")

    def test_texture_keeps_exact_frame_rate(self):
        src = clip(self.p("ntsc.mp4"), dur=1, rate="24000/1001")
        out = finish.texture(src, out=self.p("ntsc-t.mp4"))["path"]
        self.assertEqual(stream(out, "video")["r_frame_rate"], "24000/1001")

    def test_texture_prores_4444_alpha_stays_4444(self):
        src = self.p("alpha.mov")
        ff("-f", "lavfi", "-i", "testsrc2=s=160x120:d=1,format=yuva444p10le", "-c:v", "prores_ks", "-profile:v",
           "4", "-pix_fmt", "yuva444p10le", src)
        res = finish.texture(src, grain="film")
        v = stream(res["path"], "video")
        self.assertEqual(v["codec_name"], "prores")
        self.assertIn("4444", v.get("profile", ""))
        self.assertTrue(v["pix_fmt"].startswith("yuva"), v["pix_fmt"])
        self.assertTrue(any("8-bit" in n for n in res["notes"]), res["notes"])

    def test_texture_stills(self):
        png = self.p("still.png")
        ff("-f", "lavfi", "-i", "testsrc=s=64x64", "-frames:v", "1", png)
        for ext in (".png", ".jpg", ".webp"):
            try:
                out = finish.texture(png, out=self.p("still-t" + ext))["path"]
            except Refused as exc:  # an ffmpeg build without libwebp refuses up front, cleanly
                self.assertEqual(ext, ".webp", exc)
                self.assertIn("libwebp", str(exc))
                self.assertFalse(os.path.exists(self.p("still-t" + ext)))
                continue
            self.assertEqual(delivery.probe(out)["kind"], "image", ext)
        with self.assertRaises(Refused):
            finish.texture(png, out=self.p("still.mp4"))

    def test_texture_webm(self):
        src = clip(self.p("w.webm"), dur=1, vcodec=("libvpx-vp9", "-deadline", "realtime", "-cpu-used", "8"),
                   acodec=("libopus",))
        out = finish.texture(src, out=self.p("w-t.webm"))["path"]
        self.assertEqual((stream(out, "video")["codec_name"], stream(out, "audio")["codec_name"]),
                         ("vp9", "opus"))
        self.assertEqual(audio_md5(src), audio_md5(out))
        # an mp4 with AAC into webm: VP9 picture, audio re-encoded to Opus and said so
        mp4 = clip(self.p("m.mp4"), dur=1)
        res = finish.texture(mp4, out=self.p("m.webm"))
        self.assertEqual(stream(res["path"], "audio")["codec_name"], "opus")
        self.assertTrue(any("re-encoded" in n for n in res["notes"]))
        with self.assertRaises(Refused):
            finish.texture(mp4, out=self.p("m.mp3"))

    # ------------------------------------------------------------ room tone

    def test_roomtone_wav_and_mp3(self):
        wav = audio_file(self.p("v.wav"))
        self.assertTrue(delivery.digital_silence(wav))
        res = finish.roomtone(wav)
        self.assertEqual(res["digital_silence"], [])
        a = stream(res["path"], "audio")
        self.assertEqual((a["codec_name"], a["channels"]), ("pcm_s16le", 1))  # source depth and layout kept
        mp3 = audio_file(self.p("v.mp3"), extra=("-c:a", "libmp3lame"))
        res = finish.roomtone(mp3, out=self.p("out", "v.mp3"))
        self.assertEqual(res["digital_silence"], [])
        self.assertEqual(stream(res["path"], "audio")["codec_name"], "mp3")

    def test_roomtone_gap_level_near_target(self):
        src = clip(self.p("g.mp4"))
        out = finish.roomtone(src, level=-55)["path"]
        self.assertAlmostEqual(mean_db(out, 1.5, 1.2), -55, delta=2.5)
        bed = self.p("air.wav")
        ff("-f", "lavfi", "-i", "anoisesrc=color=brown:amplitude=0.3:duration=1", bed)
        out = finish.roomtone(src, bed=bed, level=-65, out=self.p("g-bed.mp4"))["path"]
        self.assertAlmostEqual(mean_db(out, 1.5, 1.2), -65, delta=2.5)

    def test_roomtone_keeps_channel_layout(self):
        src = audio_file(self.p("s51.wav"), layout="5.1")
        a = stream(finish.roomtone(src)["path"], "audio")
        self.assertEqual((a["channels"], a.get("channel_layout")), (6, "5.1"))

    def test_roomtone_refuses_two_audio_tracks(self):
        src = self.p("two.mov")
        ff("-f", "lavfi", "-i", "testsrc=s=160x120:d=1", "-f", "lavfi", "-i", "sine=d=1", "-f", "lavfi", "-i",
           "sine=f=220:d=1", "-map", "0", "-map", "1", "-map", "2", "-c:v", "libx264", "-preset", "ultrafast",
           "-c:a", "aac", src)
        with self.assertRaises(Refused) as cm:
            finish.roomtone(src)
        self.assertIn("2 audio tracks", str(cm.exception))

    def test_roomtone_webm(self):
        src = clip(self.p("r.webm"), vcodec=("libvpx-vp9", "-deadline", "realtime", "-cpu-used", "8"),
                   acodec=("libopus",))
        res = finish.roomtone(src)
        self.assertEqual(res["digital_silence"], [])
        self.assertEqual(stream(res["path"], "audio")["codec_name"], "opus")
        # H.264 cannot be copied into WebM: refused before ffmpeg runs, nothing written
        mp4 = clip(self.p("r.mp4"), dur=1)
        with self.assertRaises(Refused):
            finish.roomtone(mp4, out=self.p("r2.webm"))
        self.assertFalse(os.path.exists(self.p("r2.webm")))

    # ------------------------------------------------------------ delivery + safety

    def test_short_audio_fails_delivery_then_passes_after_roomtone(self):
        proj = project.init_project("Short Audio", "full", use_case="social-vertical", root=self.p("projects"))
        raw = clip(self.p("short.mp4"), w=1080, h=1920, dur=3, audio_dur=1.5)
        shutil.copy(raw, os.path.join(proj, "09_delivery", "reel.mp4"))
        rep = delivery.check(proj, duration=3)
        item = [c for c in rep["checks"] if c["check"] == "audio covers picture"][0]
        self.assertEqual(item["verdict"], "FAIL")
        self.assertIn("roomtone", item["note"])
        os.remove(os.path.join(proj, "09_delivery", "reel.mp4"))
        res = finish.roomtone(raw, out=os.path.join(proj, "09_delivery", "reel.mp4"))
        self.assertAlmostEqual(res["padded_to_s"], 3.0, delta=0.1)
        rep = delivery.check(proj, duration=3)
        item = [c for c in rep["checks"] if c["check"] == "audio covers picture"][0]
        self.assertEqual(item["verdict"], "PASS", item)
        item = [c for c in rep["checks"] if c["check"] == "no digital silence"][0]
        self.assertEqual(item["verdict"], "PASS", item)

    def test_refuses_without_out_inside_delivery(self):
        src = clip(self.p("proj", "09_delivery", "reel.mp4"), dur=1)
        with self.assertRaises(Refused) as cm:
            finish.texture(src)
        self.assertIn("08_assembly", str(cm.exception))
        with self.assertRaises(Refused):
            finish.roomtone(src)
        rc, _, err = self.run_cli("finish", "texture", src)
        self.assertEqual(rc, 2)
        self.assertEqual(os.listdir(self.p("proj", "09_delivery")), ["reel.mp4"])
        # with --out it is fine
        out = finish.texture(src, out=self.p("proj", "08_assembly", "reel-texture.mp4"))["path"]
        self.assertTrue(os.path.isfile(out))

    def test_partial_output_removed_on_failure(self):
        src = clip(self.p("f.mp4"), dur=1)
        dest = self.p("f-out.mp4")
        with open(dest, "w") as fh:
            fh.write("stale")
        with mock.patch.dict(finish.GRAIN, {"film": 9999}):
            with self.assertRaises(ShotcraftError) as cm:
                finish.texture(src, grain="film", out=dest)
        self.assertFalse(os.path.exists(dest))
        msg = str(cm.exception)
        self.assertIn("partial output removed", msg)
        self.assertLess(len(msg), 900)


if __name__ == "__main__":
    unittest.main()
