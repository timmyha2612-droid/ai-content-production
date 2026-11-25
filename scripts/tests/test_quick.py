"""The quick track (one shot, one price, one yes), editing a source video (relights), and the provider fixes
that came with it: the price check sends the inputs, and a wait never returns while the job still runs.
No network, no higgsfield CLI (the fake provider and a mocked runner)."""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from shotcraft import Refused, cards, compiler, gen, manifest, quick, rules, stages  # noqa: E402
from shotcraft.providers import higgsfield as hf  # noqa: E402
import sc  # noqa: E402

HAS_FFMPEG = shutil.which("ffmpeg") is not None


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = sc.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


def relight_card(path, kind="video", model="seedance_2_5"):
    meta = cards.new_card("S010", kind=kind, use_case="real-estate", presets=rules.load("presets"),
                          taxonomy=rules.load("taxonomy"), negatives=rules.load("negatives"))
    meta["title"] = "Tower relight"
    L = meta["layers"]
    L["subject"]["subject"] = "the tower top from the source video"
    L["subject"]["action"] = "same slow rise"
    L["subject"]["consistency"] = "same buildings, framing and camera path; only light and sky change"
    L["subject"]["placement"] = "tower fills the right half"
    L["camera"]["movement"] = "slow drone rise"
    L["camera"]["lens"] = "24mm look"
    L["world"]["background_far"] = "pale blue sky, gold-lit clouds"
    L["light_look"].update(setup="golden hour", quality="hard low sun", direction="sun low from frame left",
                           color_temp="warm amber sun, cool blue shade",
                           texture="crisp sideways shadows from balcony fins, glints on glass balustrades",
                           finish="true-to-life colour, gentle contrast")
    if kind == "video":
        meta["settings"].update(duration_s=3, aspect="9:16", resolution="1080p", audio=False)
        meta["handles_s"] = 0.5
    meta["model"] = {"draft": model, "final": model, "upscale": None}
    meta["inputs"] = []
    cards.write(path, meta, cards.render_body(meta))
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-quick-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home"),
                                                "SHOTCRAFT_PROVIDER": "fake"})
        self.env.start()
        for k in ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "SHOTCRAFT_FAKE_STATUS"):
            os.environ.pop(k, None)
        self.root = os.path.join(self.tmp, "projects")
        self.card = relight_card(os.path.join(self.tmp, "card.md"))
        self.clip = os.path.join(self.tmp, "clip.mp4")
        if HAS_FFMPEG:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24",
                            "-t", "6", "-pix_fmt", "yuv420p", self.clip], check=True)
        else:
            with open(self.clip, "wb") as fh:
                fh.write(b"\x00" * 64)

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def plan(self, **kw):
        args = dict(name="Relight", inputs=[(self.clip, "source")], rights="owned", root=self.root, tier="final",
                    budget_credits=200, threshold=50)
        args.update(kw)
        return quick.plan(self.card, **args)


class CompileSourceTests(unittest.TestCase):
    def compile(self, meta, model="seedance_2_5"):
        prof, _ = rules.model_profile(model, "higgsfield")
        return compiler.compile(meta, prof, rules.compiler_rules())

    def meta(self):
        tmp = tempfile.mkdtemp()
        try:
            meta, _ = cards.read(relight_card(os.path.join(tmp, "c.md")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return meta

    def test_source_leaves_out_camera_and_keeps_light(self):
        meta = self.meta()
        meta["inputs"] = [{"asset": "A001", "as": "source"}]
        res = self.compile(meta)
        self.assertTrue(res["edit_source"])
        self.assertEqual(res["params"].get("source_video"), "A001")
        self.assertNotIn("image_references", res["params"])
        dropped = {d["field"]: d["reason"] for d in res["dropped_fields"]}
        self.assertIn("camera.movement", dropped)
        self.assertIn("camera.lens", dropped)
        self.assertIn("subject.placement", dropped)
        self.assertIn("balcony fins", res["prompt"])
        self.assertIn("frame left", res["prompt"])
        self.assertNotIn("light_look.texture", dropped)

    def test_light_survives_a_tight_word_cap(self):
        meta = self.meta()
        meta["inputs"] = [{"asset": "A001", "as": "source"}]
        meta["layers"]["subject"]["consistency"] = " ".join(["same buildings and balconies"] * 6)
        prof, _ = rules.model_profile("seedance_2_5", "higgsfield")
        prof = dict(prof, max_prompt_words=70)
        res = compiler.compile(meta, prof, rules.compiler_rules())
        dropped = [d["field"] for d in res["dropped_fields"]]
        self.assertNotIn("light_look.direction", dropped)
        self.assertNotIn("light_look.setup", dropped)

    def test_without_source_nothing_changes(self):
        res = self.compile(self.meta())
        self.assertFalse(res["edit_source"])
        self.assertIn("slow drone rise", res["prompt"])

    def test_source_role_validates(self):
        meta = self.meta()
        meta["inputs"] = [{"asset": "A001", "as": "source"}]
        self.assertEqual([e for e in cards.validate(meta) if "inputs" in e], [])


class ProviderFixTests(unittest.TestCase):
    def test_estimate_sends_inputs(self):
        seen = []

        def runner(argv, timeout):
            seen.append(argv)
            return 0, json.dumps({"credits": 81}), ""
        p = hf.HiggsfieldProvider(runner=runner, sleeper=lambda s: None)
        n = p.estimate("seedance_2_5", {"mode": "video_edit", "duration": 4},
                       {"video_references": ["/tmp/clip.mp4"]}, "relight")
        self.assertEqual(n, 81)
        self.assertIn("--video-references", seen[0])
        self.assertIn("/tmp/clip.mp4", seen[0])

    def test_wait_uses_real_flags_and_polls_until_done(self):
        calls, states = [], iter(["in_progress", "in_progress", "completed"])

        def runner(argv, timeout):
            calls.append(argv)
            if argv[1:3] == ["generate", "wait"]:
                return 1, "", "unknown flag"
            return 0, json.dumps({"id": "j1", "status": next(states), "url": "https://x/y.mp4"}), ""
        slept = []
        p = hf.HiggsfieldProvider(runner=runner, sleeper=slept.append)
        st = p.wait("j1", timeout=600)
        self.assertEqual(st["status"], "completed")
        wait_argv = calls[0]
        self.assertIn("--timeout", wait_argv)
        self.assertIn("--interval", wait_argv)
        self.assertNotIn("--wait-timeout", wait_argv)
        self.assertEqual(len(slept), 2)

    def test_wait_times_out_while_running(self):
        def runner(argv, timeout):
            if argv[1:3] == ["generate", "wait"]:
                return 1, "", "deadline exceeded"
            return 0, json.dumps({"id": "j1", "status": "in_progress"}), ""
        p = hf.HiggsfieldProvider(runner=runner, sleeper=lambda s: None)
        with mock.patch("shotcraft.providers.higgsfield.time.time", side_effect=[0, 0, 10_000, 10_000]):
            st = p.wait("j1", timeout=60)
        self.assertTrue(st.get("timed_out"))


class QuickTrackTests(Base):
    def test_plan_prices_without_spending(self):
        res = self.plan()
        proj = res["project"]
        data = manifest.load(proj)
        self.assertEqual(data["track"], "quick")
        self.assertEqual(data.get("generations", []), [])
        pl = res["estimate"]["plan"]
        self.assertEqual(pl["params"].get("mode"), "video_edit")
        self.assertEqual(list(pl["inputs"]), ["video_references"])
        self.assertTrue(any("Price:" in line for line in res["summary"]))
        self.assertTrue(any(line.startswith("Ask the user once") for line in res["summary"]), res["summary"])
        self.assertFalse(any("Fix before asking" in line for line in res["summary"]), res["summary"])
        self.assertEqual(stages.load_state(proj)["stages"]["quick"]["status"], "open")

    def test_one_yes_generates_the_final_without_a_draft(self):
        proj = self.plan()["project"]
        res = quick.go(proj, "yes, go at 1080p")
        g = res["generations"][0]
        self.assertEqual(g["tier"], "final")
        self.assertEqual(g["status"], "completed")
        self.assertTrue(g["outputs"])
        self.assertEqual(g["params"].get("mode"), "video_edit")
        kept = quick.keep(proj, "keep it")
        self.assertEqual(kept["stage"]["status"], "done")

    def test_go_needs_words_and_a_price(self):
        proj = self.plan()["project"]
        with self.assertRaises(Refused):
            quick.go(proj, "")
        quick._save_settings(proj, priced={})
        data = manifest.load(proj)
        data["quick"]["priced"] = {}
        manifest.save(proj, data)
        with self.assertRaises(Refused):
            quick.go(proj, "go")

    def test_go_refuses_a_card_changed_after_pricing(self):
        proj = self.plan()["project"]
        card = quick._the_card(proj)
        meta, body = cards.read(card)
        meta["layers"]["light_look"]["setup"] = "blue hour"
        cards.write(card, meta, body)
        with self.assertRaises(Refused):
            quick.go(proj, "go")

    def test_inputs_need_rights(self):
        with self.assertRaises(Refused):
            self.plan(rights=None)

    def test_redo_rejects_and_needs_a_new_price(self):
        proj = self.plan()["project"]
        quick.go(proj, "go")
        quick.redo(proj, "too orange", "warmer but less orange")
        with self.assertRaises(Refused):
            quick.go(proj, "go again")

    def test_model_without_edit_mode_is_refused(self):
        relight_card(self.card, model="kling3_0")
        with self.assertRaises(Refused):
            self.plan()

    @unittest.skipUnless(HAS_FFMPEG, "needs ffmpeg")
    def test_trim_and_crop_the_source(self):
        res = self.plan(trim="1-4", crop="202:360:200:0")
        proj = res["project"]
        a = [x for x in manifest.load(proj)["assets"] if x["role"] == "input"][0]
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=width,height",
                              "-of", "json", os.path.join(proj, a["path"])], capture_output=True, text=True)
        info = json.loads(out.stdout)
        self.assertAlmostEqual(float(info["format"]["duration"]), 3.0, delta=0.15)
        self.assertEqual(info["streams"][0]["width"], 202)

    def test_cli_flow(self):
        rc, out, err = run_cli("quick", "plan", self.card, "--name", "Relight", "--input", self.clip, "--as",
                               "source", "--rights", "owned", "--root", self.root, "--budget", "200")
        self.assertEqual(rc, 0, err)
        self.assertIn("Price:", out)
        proj = out.splitlines()[0].split("Project: ", 1)[1]
        rc, out, err = run_cli("quick", "go", "--project", proj, "--user-said", "yes go")
        self.assertEqual(rc, 0, err)
        self.assertIn("completed", out)
        rc, out, err = run_cli("quick", "keep", "--project", proj, "--user-said", "keep it")
        self.assertEqual(rc, 0, err)


class CompilerTextFixTests(unittest.TestCase):
    def test_beat_times_get_one_s(self):
        self.assertEqual(compiler._fragment("time_output.beats", [{"t": "0-4 s", "what": "rise"},
                                                                 {"t": "4-7", "what": "climb"}]),
                         "0-4 s: rise; 4-7 s: climb")

    def test_no_text_says_nothing(self):
        for v in ("none", "None", "no text"):
            self.assertEqual(compiler._fragment("time_output.on_screen_text", v), "")
        self.assertIn("SALE", compiler._fragment("time_output.on_screen_text", "SALE"))


class ReviewFixTests(Base):
    """Regression tests for the pre-push review of 0.2.0."""

    def test_update_prices_what_go_spends(self):
        proj = self.plan(variants=3)["project"]
        res = quick.plan(self.card, project=proj)  # an update keeps the earlier choice of 3 takes
        self.assertEqual(res["estimate"]["plan"]["variants"], 3)
        res = quick.plan(self.card, project=proj, variants=1)  # and a changed choice is what gets priced
        self.assertEqual(res["estimate"]["plan"]["variants"], 1)
        out = quick.go(proj, "yes")
        self.assertEqual(len(out["generations"]), 1)

    def test_a_partial_submit_still_uses_the_price(self):
        proj = self.plan(variants=2)["project"]
        from shotcraft.providers.fake import FakeProvider
        real = FakeProvider.submit
        calls = []

        def flaky(self_, *a, **k):
            calls.append(1)
            if len(calls) == 2:
                raise RuntimeError("network blip")
            return real(self_, *a, **k)
        with mock.patch.object(FakeProvider, "submit", flaky):
            with self.assertRaises(RuntimeError):
                quick.go(proj, "yes", wait=False)
        with self.assertRaises(Refused):
            quick.go(proj, "yes", wait=False)
        submitted = [g for g in manifest.load(proj)["generations"] if g.get("job_id")]
        self.assertEqual(len(submitted), 1)

    def test_plain_gen_submit_keeps_the_draft_gate_on_quick(self):
        proj = self.plan()["project"]
        quick.go(proj, "yes")
        with self.assertRaises(Refused):
            gen.submit(proj, "S010", "final")

    def test_refused_over_price_leaves_the_price_usable(self):
        proj = self.plan()["project"]
        with mock.patch("shotcraft.gen._estimate_each", return_value=999.0):
            with self.assertRaises(Refused):
                quick.go(proj, "yes")
        quick.go(proj, "yes")  # same price, live price back to normal: allowed once

    def test_image_source_is_refused(self):
        img = os.path.join(self.tmp, "still.png")
        with open(img, "wb") as fh:
            fh.write(b"\x89PNG\r\n")
        with self.assertRaises(Refused):
            self.plan(inputs=[(img, "source")], scale="640:360")

    def test_bad_scale_is_refused(self):
        with self.assertRaises(Refused):
            self.plan(scale="1080:1920,drawtext=text=x")

    def test_budget_breach_is_in_the_summary(self):
        res = self.plan(budget_credits=500, threshold=1)
        self.assertTrue(any(line.startswith("Budget:") for line in res["summary"]), res["summary"])

    def test_wait_ignores_401_inside_a_good_answer(self):
        def runner(argv, timeout):
            return 0, json.dumps({"id": "j1", "status": "completed", "seed": 401, "url": "https://x/y.mp4"}), ""
        st = hf.HiggsfieldProvider(runner=runner, sleeper=lambda s: None).wait("j1", timeout=60)
        self.assertEqual(st["status"], "completed")

    def test_wait_gives_up_on_a_job_it_cannot_read(self):
        def runner(argv, timeout):
            if argv[1:3] == ["generate", "wait"]:
                return 1, "", "boom"
            return 1, "", "job not found"
        p = hf.HiggsfieldProvider(runner=runner, sleeper=lambda s: None)
        p.max_tries = 1
        from shotcraft.providers.base import ProviderError
        with self.assertRaises(ProviderError):
            p.wait("nope", timeout=600)

    def test_a_price_is_spent_once(self):
        proj = self.plan()["project"]
        quick.go(proj, "yes go", wait=False)
        with self.assertRaises(Refused):
            quick.go(proj, "yes go", wait=False)
        self.assertEqual(len(manifest.load(proj)["generations"]), 1)

    def test_higher_live_price_is_refused_before_submitting(self):
        proj = self.plan()["project"]
        with mock.patch("shotcraft.gen._estimate_each", return_value=999.0):
            with self.assertRaises(Refused):
                quick.go(proj, "yes")
        self.assertEqual(manifest.load(proj).get("generations", []), [])

    def test_update_keeps_the_source(self):
        proj = self.plan()["project"]
        res = quick.plan(self.card, project=proj)
        self.assertEqual(list(res["estimate"]["plan"]["inputs"]), ["video_references"])
        self.assertEqual(res["estimate"]["plan"]["params"].get("mode"), "video_edit")

    @unittest.skipUnless(HAS_FFMPEG, "needs ffmpeg")
    def test_trim_applies_to_the_source_only(self):
        img = os.path.join(self.tmp, "ref.png")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=c=red:s=64x64", "-frames:v", "1",
                        img], check=True)
        relight_card(self.card, model="seedance_2_5")
        proj = self.plan(inputs=[(self.clip, "source"), (img, "reference")], trim="1-3")["project"]
        paths_ = sorted(a["path"] for a in manifest.load(proj)["assets"] if a["role"] == "input")
        self.assertTrue(any(p.endswith("ref.png") for p in paths_), paths_)

    @unittest.skipUnless(HAS_FFMPEG, "needs ffmpeg")
    def test_scale_alone_is_applied(self):
        proj = self.plan(scale="320:180")["project"]
        a = [x for x in manifest.load(proj)["assets"] if x["role"] == "input"][0]
        out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width", "-of", "csv=p=0",
                              os.path.join(proj, a["path"])], capture_output=True, text=True)
        self.assertEqual(out.stdout.strip(), "320")

    def test_trim_needs_a_source(self):
        with self.assertRaises(Refused):
            self.plan(inputs=[(self.clip, "reference")], trim="1-3")


class ReviewFixUnitTests(unittest.TestCase):
    def test_light_boost_stays_trimmable(self):
        tmp = tempfile.mkdtemp()
        try:
            meta, _ = cards.read(relight_card(os.path.join(tmp, "c.md")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        meta["inputs"] = [{"asset": "A001", "as": "source"}]
        prof, _ = rules.model_profile("seedance_2_5", "higgsfield")
        res = compiler.compile(meta, dict(prof, max_prompt_words=25), rules.compiler_rules())
        self.assertLessEqual(res["word_count"], 25 + 15)  # protected subject/action may overrun slightly
        self.assertTrue(any(d["field"].startswith("light_look.") for d in res["dropped_fields"]))

    def test_two_sources_do_not_validate(self):
        tmp = tempfile.mkdtemp()
        try:
            meta, _ = cards.read(relight_card(os.path.join(tmp, "c.md")))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        meta["inputs"] = [{"asset": "A001", "as": "source"}, {"asset": "A002", "as": "source"}]
        self.assertTrue(any("source" in e for e in cards.validate(meta)))

    def test_cost_timeout_scales_with_the_file(self):
        tmp = tempfile.mkdtemp()
        try:
            big = os.path.join(tmp, "big.mp4")
            with open(big, "wb") as fh:
                fh.truncate(300 * 1000 * 1000)
            seen = []

            def runner(argv, timeout):
                seen.append(timeout)
                return 0, json.dumps({"credits": 5}), ""
            hf.HiggsfieldProvider(runner=runner, sleeper=lambda s: None).estimate(
                "seedance_2_5", {"mode": "video_edit"}, {"video_references": [big]}, "x")
            self.assertGreaterEqual(seen[0], 300)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_wait_survives_a_status_blip(self):
        answers = iter([(1, "", "HTTP 502 bad gateway"),
                        (0, json.dumps({"id": "j1", "status": "completed", "url": "https://x/y.mp4"}), "")])

        def runner(argv, timeout):
            if argv[1:3] == ["generate", "wait"]:
                return 1, "", "connection reset"
            return next(answers)
        p = hf.HiggsfieldProvider(runner=runner, sleeper=lambda s: None)
        p.max_tries = 1
        self.assertEqual(p.wait("j1", timeout=600)["status"], "completed")

    def test_cli_wait_is_not_retried_past_the_deadline(self):
        calls = []

        def runner(argv, timeout):
            calls.append(argv[1:3])
            if argv[1:3] == ["generate", "wait"]:
                return 1, "", "HTTP 429 too many requests"
            return 0, json.dumps({"id": "j1", "status": "completed", "url": "https://x/y.mp4"}), ""
        hf.HiggsfieldProvider(runner=runner, sleeper=lambda s: None).wait("j1", timeout=600)
        self.assertEqual(calls.count(["generate", "wait"]), 1)


if __name__ == "__main__":
    unittest.main()
