"""Tests for depth planes, subject-environment interaction and the natural-finish pass.

Covers the compiler's depth sentence, the natural-finish defaults on new cards, the grain clash rule, the
finish texture / roomtone commands and the delivery check for digital silence (the media parts need ffmpeg).
"""

import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shotcraft import Refused, cards, compiler, delivery, finish, project  # noqa: E402
import sc  # noqa: E402

PLUGIN_RULES = HERE.parent.parent / "rules"
HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))

PROFILE = {"id": "test_video", "kind": "video", "durations": [4, 6, 8], "resolutions": ["1080p"],
           "aspects": ["9:16"], "start_frame": True, "audio": False, "negative_prompt": False,
           "max_prompt_words": 400}


def load_rules(name):
    with open(PLUGIN_RULES / (name + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


def card(kind="video", **layers):
    meta = cards.new_card("S010", kind=kind, use_case="social-vertical")
    meta["layers"]["subject"]["subject"] = "a woman in a yellow raincoat"
    meta["layers"]["subject"]["action"] = "sips coffee"
    if kind == "video":
        meta["settings"].update({"aspect": "9:16", "resolution": "1080p", "duration_s": 6, "audio": False})
    meta["avoid"] = []
    for key, val in layers.items():
        layer, field = key.split("__")
        meta["layers"][layer][field] = val
    return meta


DEPTH = dict(world__environment="a narrow street cafe at night",
             world__background_far="city towers fading into rain haze",
             world__background_near="the cafe window with a chalkboard menu",
             subject__placement="seated at a window table, left third",
             world__foreground="rain running down the glass",
             world__parallax="the far towers barely move while the passing cars streak",
             subject__interaction="neon spill on her cheek, rain beading on her hood")


class DepthCompileTest(unittest.TestCase):
    def test_depth_sentence_order_labels_and_join(self):
        out = compiler.compile(card(**DEPTH), PROFILE, {})
        p = out["prompt"]
        want = ("Far background: city towers fading into rain haze; background: the cafe window with a chalkboard "
                "menu; midground: seated at a window table, left third; foreground: rain running down the glass; "
                "the far towers barely move while the passing cars streak.")
        self.assertIn(want, p)
        # interaction sits in the subject sentence, right after the action
        self.assertTrue(p.startswith("A woman in a yellow raincoat, sips coffee, neon spill on her cheek"), p)
        # world sentence before depth, depth before camera/light
        self.assertLess(p.index("narrow street cafe"), p.index("Far background"))
        self.assertEqual(out["warnings"], [])

    def test_labels_skipped_when_text_names_the_plane(self):
        out = compiler.compile(card(world__environment="a beach",
                                    world__foreground="out-of-focus dune grass in the foreground"), PROFILE, {})
        self.assertIn("out-of-focus dune grass in the foreground", out["prompt"].lower())
        self.assertNotIn("foreground: out-of-focus", out["prompt"].lower())

    def test_image_skips_parallax(self):
        meta = card(kind="image", **DEPTH)
        out = compiler.compile(meta, dict(PROFILE, kind="image"), {})
        self.assertNotIn("streak", out["prompt"])
        self.assertIn({"field": "world.parallax", "reason": "not used for a still image"}, out["dropped_fields"])
        self.assertIn("foreground: rain running", out["prompt"])

    def test_start_frame_keeps_interaction_and_parallax_only(self):
        meta = card(**DEPTH)
        meta["inputs"] = [{"asset": "A001", "as": "start_frame"}]
        out = compiler.compile(meta, PROFILE, {})
        self.assertTrue(out["motion_only"])
        self.assertIn("neon spill on her cheek", out["prompt"])
        self.assertIn("passing cars streak", out["prompt"])
        for gone in ("chalkboard", "rain running down", "city towers fading"):
            self.assertNotIn(gone, out["prompt"])
        self.assertEqual(out["warnings"], [])  # no depth warning in motion-only mode

    def test_warns_when_place_has_no_planes(self):
        out = compiler.compile(card(world__environment="a narrow street cafe at night"), PROFILE, {})
        self.assertTrue(any("No depth planes" in w for w in out["warnings"]), out["warnings"])
        out = compiler.compile(card(world__environment="a cafe", world__foreground="a cup edge"), PROFILE, {})
        self.assertFalse(any("No depth planes" in w for w in out["warnings"]))

    def test_depth_trimmed_before_core_fields(self):
        meta = card(**DEPTH)
        out = compiler.compile(meta, dict(PROFILE, max_prompt_words=30), {})
        dropped = [d["field"] for d in out["dropped_fields"]]
        self.assertIn("world.parallax", dropped)
        self.assertNotIn("subject.subject", dropped)
        self.assertLess(dropped.index("world.parallax"), dropped.index("world.foreground")
                        if "world.foreground" in dropped else len(dropped))

    def test_validate_accepts_new_fields(self):
        meta = card(**DEPTH)
        meta["layers"]["light_look"]["finish"] = "lived-in wear"
        self.assertEqual(cards.validate(meta), [])


class NaturalFinishTest(unittest.TestCase):
    def setUp(self):
        self.presets, self.tax, self.neg = load_rules("presets"), load_rules("taxonomy"), load_rules("negatives")

    def new(self, use_case):
        return cards.new_card("S010", use_case=use_case, presets=self.presets, taxonomy=self.tax,
                              negatives=self.neg)

    def test_natural_preset_gets_finish_and_guards(self):
        meta = self.new("social-vertical")
        default = self.tax["layers"]["light_look"]["fields"]["finish"]["defaults"]["natural"]
        self.assertEqual(meta["layers"]["light_look"]["finish"], default)
        for g in self.neg["by_finish"]["natural"]:
            self.assertIn(g, meta["avoid"])

    def test_clean_preset_stays_clean(self):
        meta = self.new("icon-ui")
        self.assertEqual(meta["layers"]["light_look"]["finish"], "")
        self.assertFalse(set(self.neg["by_category"]["too_perfect"]) & set(meta["avoid"]))

    def test_every_preset_declares_a_finish(self):
        for pid, p in self.presets["presets"].items():
            if isinstance(p, dict):
                self.assertIn(p.get("finish"), ("natural", "true_to_life", "clean"), pid)

    def test_too_perfect_guards_compile_positively(self):
        meta = self.new("social-vertical")
        meta["layers"]["subject"]["subject"] = "a barista"
        rules = {"positive_rewrites": load_rules("positive_rewrites"), "negatives": self.neg}
        out = compiler.compile(meta, PROFILE, rules)
        self.assertIn("photographed on a real camera", out["prompt"])
        self.assertEqual(out["prompt"].lower().count("subtle real-world imperfection"), 1)
        self.assertNotIn("cgi look", out["unguarded"])

    def test_grain_clash_drops_noise_guard(self):
        meta = card(light_look__texture="fine 35mm film grain")
        meta["avoid"] = ["noise", "blurry"]
        rules = {"positive_rewrites": load_rules("positive_rewrites")}
        out = compiler.compile(meta, PROFILE, rules)
        self.assertNotIn("noise-free", out["prompt"])
        self.assertNotIn("noise", out["unguarded"])
        self.assertTrue(any("'noise'" in w for w in out["warnings"]), out["warnings"])
        # without grain in the look the guard stays
        meta["layers"]["light_look"]["texture"] = ""
        out = compiler.compile(meta, PROFILE, rules)
        self.assertIn("noise-free", out["prompt"])


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + list(args), check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def clip_with_gap(path, w=320, h=240, dur=3, tone=1, fps=30):
    """A clip whose audio is a tone for `tone` seconds, then digital silence."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    ff("-f", "lavfi", "-i", "testsrc=size=%dx%d:rate=%s:duration=%s" % (w, h, fps, dur),
       "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=%s,apad=whole_dur=%s" % (tone, dur),
       "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", path)
    return path


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class FinishMediaTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-finish-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home"),
                                                "SHOTCRAFT_PROVIDER": "fake"})
        self.env.start()
        os.environ.pop("CLAUDE_SESSION_ID", None)
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = sc.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    def test_digital_silence_detection(self):
        src = clip_with_gap(os.path.join(self.tmp, "gap.mp4"))
        gaps = delivery.digital_silence(src)
        self.assertEqual(len(gaps), 1)
        self.assertAlmostEqual(gaps[0][0], 1.0, delta=0.1)
        self.assertAlmostEqual(gaps[0][1], 3.0, delta=0.15)

    def test_roomtone_fills_silence_and_keeps_picture(self):
        src = clip_with_gap(os.path.join(self.tmp, "gap.mp4"))
        res = finish.roomtone(src)
        self.assertEqual(res["digital_silence"], [])
        self.assertTrue(res["path"].endswith("gap-roomtone.mp4"))
        p = delivery.probe(res["path"])
        self.assertEqual((p["vcodec"], p["width"], p["height"]), ("h264", 320, 240))
        self.assertTrue(p["has_audio"])
        # a recorded bed via the CLI
        bed = os.path.join(self.tmp, "air.wav")
        ff("-f", "lavfi", "-i", "anoisesrc=color=brown:amplitude=0.3:duration=1", bed)
        out = os.path.join(self.tmp, "out", "bed.mp4")
        rc, stdout, _ = self.run_cli("finish", "roomtone", src, "--bed", bed, "--level", "-55", "--out", out,
                                     "--json")
        self.assertEqual(rc, 0, stdout)
        data = json.loads(stdout)
        self.assertEqual((data["bed"], data["digital_silence"]), ("air.wav", []))

    def test_roomtone_refusals(self):
        silent = os.path.join(self.tmp, "nosound.mp4")
        ff("-f", "lavfi", "-i", "testsrc=size=160x120:rate=25:duration=1", "-c:v", "libx264", "-preset",
           "ultrafast", "-pix_fmt", "yuv420p", silent)
        with self.assertRaises(Refused):
            finish.roomtone(silent)
        src = clip_with_gap(os.path.join(self.tmp, "gap.mp4"))
        with self.assertRaises(Refused):
            finish.roomtone(src, out=src)
        rc, _, _ = self.run_cli("finish", "roomtone", src, "--level", "-10")
        self.assertEqual(rc, 1)

    def test_texture_video_and_still(self):
        src = clip_with_gap(os.path.join(self.tmp, "gap.mp4"))
        res = finish.texture(src, grain="film", vignette=True)
        p = delivery.probe(res["path"])
        self.assertEqual((p["vcodec"], p["width"], p["height"], p["has_audio"]), ("h264", 320, 240, True))
        self.assertAlmostEqual(p["duration"], 3.0, delta=0.15)
        still = os.path.join(self.tmp, "frame.png")
        ff("-f", "lavfi", "-i", "color=c=gray:s=64x64", "-frames:v", "1", still)
        rc, stdout, _ = self.run_cli("finish", "texture", still, "--json")
        self.assertEqual(rc, 0)
        self.assertEqual(delivery.probe(json.loads(stdout)["path"])["kind"], "image")
        rc, _, _ = self.run_cli("finish", "texture", still, "--grain", "off")
        self.assertEqual(rc, 2)

    def test_delivery_flags_digital_silence(self):
        root = os.path.join(self.tmp, "projects")
        proj = project.init_project("Silence Test", "full", use_case="social-vertical", root=root)
        clip_with_gap(os.path.join(proj, "09_delivery", "reel.mp4"), w=1080, h=1920, dur=3)
        rep = delivery.check(proj, duration=3)
        item = [c for c in rep["checks"] if c["check"] == "no digital silence"][0]
        self.assertEqual(item["verdict"], "FAIL")
        self.assertIn("finish roomtone", item["note"])
        self.assertEqual(rep["verdict"], "FAIL")
        # allowed on purpose: skipped with a note
        with open(os.path.join(proj, "project.json"), encoding="utf-8") as fh:
            data = json.load(fh)
        data.setdefault("delivery", {})["allow_digital_silence"] = True
        with open(os.path.join(proj, "project.json"), "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        rep = delivery.check(proj, duration=3)
        self.assertFalse([c for c in rep["checks"] if c["check"] == "no digital silence"])
        self.assertTrue(any("allow_digital_silence" in n for n in rep["notes"]))

    def test_delivery_passes_after_roomtone(self):
        root = os.path.join(self.tmp, "projects")
        proj = project.init_project("Tone Test", "full", use_case="social-vertical", root=root)
        raw = clip_with_gap(os.path.join(self.tmp, "raw.mp4"), w=1080, h=1920, dur=3)
        finish.roomtone(raw, out=os.path.join(proj, "09_delivery", "reel.mp4"))
        rep = delivery.check(proj, duration=3)
        item = [c for c in rep["checks"] if c["check"] == "no digital silence"][0]
        self.assertEqual(item["verdict"], "PASS", item)


if __name__ == "__main__":
    unittest.main()
