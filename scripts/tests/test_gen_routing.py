"""Routing, duration fitting, image-first, providers (fake + Higgsfield argv), the gen flow end to end with the fake
provider, and the model scout. No network, no higgsfield CLI."""
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from shotcraft import Refused, budget, cards, manifest, project, rules, routing, stages  # noqa: E402
from shotcraft import gen, scout  # noqa: E402
from shotcraft.providers import get_provider  # noqa: E402
from shotcraft.providers import higgsfield as hf  # noqa: E402
from shotcraft.providers.fake import FakeProvider  # noqa: E402
import sc  # noqa: E402

ROOT = os.path.dirname(SCRIPTS)


def load_rule(name):
    with open(os.path.join(ROOT, "rules", name), encoding="utf-8") as fh:
        return json.load(fh)


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = sc.main(list(argv))
    return rc, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-gen-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home"),
                                                "SHOTCRAFT_PROVIDER": "fake"})
        self.env.start()
        for k in ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "SHOTCRAFT_FAKE_STATUS", "SHOTCRAFT_FAKE_MODELS", "SHOTCRAFT_FAKE_HELP"):
            os.environ.pop(k, None)
        self.root = os.path.join(self.tmp, "projects")

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, proj, rel, text="content\n"):
        p = os.path.join(proj, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def single_project(self, use_case="social-vertical", budget_credits=None, threshold=50, approve_card=True,
                       inputs=None, duration=3, kind=None):
        proj = project.init_project("Gen Test", "single", use_case=use_case, budget=budget_credits,
                                    threshold=threshold, root=self.root)
        stages.start(proj, "intake")
        self.write(proj, "00_brief/job-card.md", "# Job card\nGoal: a dawn reel\nAudience: travellers\n"
                   "Use case: %s\nDelivery: 9:16 mp4\nBudget: 300 credits\n" % use_case)
        self.write(proj, "00_brief/grilling.md", "Q: who is it for?\nA: travellers\n")
        stages.done(proj, "intake", user_said="yes, the card is right")
        stages.start(proj, "prompts")
        self.card_path = self.make_card(proj, "S010", approve=approve_card, inputs=inputs, duration=duration,
                                        kind=kind, use_case=use_case)
        stages.qa_record(proj, "prompts", 1, "PASS")
        stages.done(proj, "prompts")
        stages.start(proj, "drafts")
        return proj

    def make_card(self, proj, sid, approve=True, inputs=None, duration=3, kind=None, use_case="social-vertical"):
        presets = rules.load("presets")
        meta = cards.new_card(sid, kind=kind, use_case=use_case, presets=presets,
                              taxonomy=rules.load("taxonomy"), negatives=rules.load("negatives"))
        meta["layers"]["subject"]["subject"] = "a lighthouse on a cliff"
        meta["layers"]["subject"]["action"] = "waves break below"
        meta["layers"]["camera"]["movement"] = "slow push-in"
        if meta["kind"] == "video":
            meta["settings"]["duration_s"] = duration
        meta["settings"]["variants"] = 1
        meta["inputs"] = inputs or []
        path = os.path.join(proj, "05_prompts", sid + ".md")
        cards.write(path, meta, cards.render_body(meta))
        if approve:
            cards.approve(proj, path, "looks good, go")
        return path


# ---------------------------------------------------------------- rule files

class RuleFileTests(unittest.TestCase):
    def setUp(self):
        self.models = load_rule("models.json")["providers"]["higgsfield"]["models"]
        self.routing = load_rule("routing.json")

    def test_every_routed_model_exists(self):
        for need, uc in self.routing["use_cases"].items():
            for tier in ("board", "draft", "final", "upscale"):
                for row in uc.get(tier, []):
                    self.assertIn(row["model"], self.models, "%s/%s -> %s" % (need, tier, row["model"]))

    def test_required_needs_present(self):
        for need in ("icon-logo", "graphic-with-text", "photoreal-people", "product-environment-still",
                     "video-general", "video-motion-physics", "video-dialogue-audio", "video-cinematic-multishot",
                     "mograph-loop", "storyboard-frame"):
            self.assertIn(need, self.routing["use_cases"])

    def test_every_preset_need_routes(self):
        presets = load_rule("presets.json")["presets"]
        for pid, p in presets.items():
            self.assertIn(p["need"], self.routing["use_cases"], pid)

    def test_profiles_have_spec_fields(self):
        for mid, m in self.models.items():
            for key in ("name", "kind", "durations", "resolutions", "aspects", "start_frame", "end_frame", "refs",
                        "audio", "negative_prompt", "seed", "max_prompt_words", "checked_at", "source"):
                self.assertIn(key, m, "%s lacks %s" % (mid, key))
            self.assertEqual(m["checked_at"], "2026-11-24")

    def test_nano_banana_trap(self):
        self.assertEqual(self.models["nano_banana_2"]["name"], "Nano Banana Pro")
        self.assertEqual(self.models["nano_banana_flash"]["name"], "Nano Banana 2")


# ---------------------------------------------------------------- routing

class RoutingTests(Base):
    def test_agreed_table(self):
        def first(uc, tier, **kw):
            return routing.route(uc, tier, **kw)["best"]["model"]
        self.assertEqual(first("icon-logo", "draft"), "recraft_v4_1")
        self.assertEqual(first("icon-logo", "final"), "recraft_v4_1")
        self.assertEqual(routing.route("icon-ui", "upscale")["candidates"], [])
        self.assertEqual(first("graphic-with-text", "draft"), "nano_banana_flash")
        self.assertEqual(first("graphic-with-text", "final"), "nano_banana_2")
        self.assertEqual(first("photoreal-people", "draft"), "text2image_soul_v2")
        self.assertEqual(first("photoreal-people", "final"), "soul_cinematic")
        self.assertEqual(first("photoreal-people", "upscale"), "topaz_image")
        self.assertEqual(first("video-general", "draft", duration=3), "seedance_2_0")
        self.assertEqual(first("video-general", "final", duration=5), "seedance_2_5")
        self.assertEqual(first("video-motion-physics", "final", duration=5), "kling3_0")
        self.assertEqual(first("video-dialogue-audio", "draft", duration=6), "veo3_1_lite")
        self.assertEqual(first("video-dialogue-audio", "final", duration=6), "veo3_1")
        self.assertEqual(first("video-cinematic-multishot", "final", duration=10), "cinematic_studio_video_3_5")

    def test_preset_maps_to_need(self):
        r = routing.route("social-vertical", "draft", duration=3)
        self.assertEqual(r["need"], "video-general")
        self.assertEqual(r["use_case"], "social-vertical")
        self.assertEqual(r["best"]["params"], {"mode": "fast", "resolution": "480p"})

    def test_duration_reorders_candidates(self):
        # Veo takes at most 8 s; a 20 s dialogue shot puts it behind... nothing, so it is marked as a chain
        r = routing.route("video-dialogue-audio", "final", duration=20)
        self.assertTrue(r["candidates"][0]["duration"]["chain"])
        # video-motion-physics final: Kling (max 15) needs a chain at 20 s; Seedance 2.5 (max 30) does not
        r = routing.route("video-motion-physics", "final", duration=20)
        self.assertEqual(r["best"]["model"], "seedance_2_5")

    def test_needs_filter(self):
        r = routing.route("video-motion-physics", "draft", duration=5, needs="end_frame")
        self.assertIsNone(r["best"])  # Kling Turbo has no end frame
        r = routing.route("video-general", "final", duration=5, needs="4k")
        self.assertEqual(r["best"]["model"], "seedance_2_0")

    def test_unknown_use_case_refused(self):
        with self.assertRaises(Refused):
            routing.route("no-such-thing", "draft")

    def test_cli_route(self):
        rc, out, _ = run_cli("route", "--use-case", "social-vertical", "--tier", "final", "--duration", "4",
                             "--json")
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["best"]["model"], "seedance_2_5")
        rc, out, _ = run_cli("route", "--use-case", "thumbnail", "--tier", "draft")
        self.assertEqual(rc, 0)
        self.assertIn("Nano Banana 2", out)


class DurationTests(unittest.TestCase):
    def test_list_shortest_covering(self):
        d = routing.fit_duration({"name": "X", "durations": [5, 10]}, 6)
        self.assertEqual(d["chosen_s"], 10)
        self.assertEqual(d["trim_s"], 4)
        self.assertIn("Trim 4 s", d["trim_plan"])
        self.assertTrue(d["fits"])

    def test_exact(self):
        d = routing.fit_duration({"durations": [4, 6, 8]}, 6)
        self.assertEqual((d["chosen_s"], d["trim_s"], d["trim_plan"]), (6, 0, None))

    def test_handles_added(self):
        d = routing.fit_duration({"durations": {"min": 4, "max": 30}}, 4, handles=0.5)
        self.assertEqual(d["requested_s"], 5)
        self.assertEqual(d["chosen_s"], 5)

    def test_range_rounds_up_and_clamps(self):
        self.assertEqual(routing.fit_duration({"durations": {"min": 3, "max": 15}}, 4.2)["chosen_s"], 5)
        self.assertEqual(routing.fit_duration({"durations": {"min": 4, "max": 15}}, 2)["chosen_s"], 4)

    def test_chain_for_long_shot(self):
        d = routing.fit_duration({"name": "Veo", "durations": [4, 6, 8], "start_frame": True}, 20)
        self.assertFalse(d["fits"])
        self.assertEqual(d["chain"]["takes"], 3)
        self.assertEqual(d["chain"]["each_s"], 8)
        self.assertTrue(d["chain"]["start_frame_chaining"])
        d = routing.fit_duration({"name": "Y", "durations": {"min": 2, "max": 10}}, 25)
        self.assertEqual(d["chain"]["takes"], 3)
        self.assertEqual(d["chain"]["each_s"], 9)
        self.assertIn("cut between takes", d["chain"]["plan"])

    def test_by_model_id(self):
        d = routing.fit_duration("veo3_1", 5)
        self.assertEqual(d["chosen_s"], 6)

    def test_no_duration_setting(self):
        d = routing.fit_duration({"name": "Z"}, 5)
        self.assertIsNone(d["chosen_s"])
        self.assertTrue(d["fits"])

    def test_fit_resolution(self):
        preset = rules.preset("social-vertical")
        self.assertEqual(routing.fit_resolution(preset, "draft")["resolution"], "720p")
        self.assertEqual(routing.fit_resolution(preset, "final")["resolution"], "1080p")
        self.assertEqual(routing.fit_resolution(preset, "board")["resolution"], "720p")
        self.assertEqual(routing.fit_resolution(preset, "final", "gemini_omni")["resolution"], "720p")
        thumb = rules.preset("thumbnail")
        self.assertEqual(routing.fit_resolution(thumb, "final", "text2image_soul_v2")["resolution"], "2k")
        self.assertEqual(routing.fit_resolution(thumb, "draft", "text2image_soul_v2")["resolution"], "1.5k")


class ImageFirstTests(unittest.TestCase):
    def card(self, **kw):
        base = {"kind": "video", "tier_plan": ["draft", "final"], "settings": {"duration_s": 4},
                "inputs": [], "layers": {"subject": {"subject": "a lighthouse"}, "camera": {"movement": "static"}}}
        base.update(kw)
        return base

    def test_plain_shot_is_not_image_first(self):
        self.assertFalse(routing.image_first(self.card()))

    def test_board_in_tier_plan(self):
        self.assertTrue(routing.image_first(self.card(tier_plan=["board", "draft", "final"])))

    def test_people_and_moves_and_length(self):
        self.assertTrue(routing.image_first(self.card(layers={"subject": {"subject": "a woman reading"}})))
        self.assertTrue(routing.image_first(self.card(layers={"subject": {"subject": "a hill"},
                                                              "camera": {"movement": "slow orbit"}})))
        self.assertTrue(routing.image_first(self.card(settings={"duration_s": 9})))
        self.assertTrue(routing.image_first(self.card(layers={"subject": {"subject": "the product bottle"}})))

    def test_never_for_images_or_with_start_frame(self):
        self.assertFalse(routing.image_first(self.card(kind="image", tier_plan=["board"])))
        self.assertFalse(routing.image_first(self.card(tier_plan=["board"],
                                                       inputs=[{"asset": "A001", "as": "start_frame"}])))


# ---------------------------------------------------------------- providers

class ProviderTests(Base):
    def test_get_provider_env_forces_fake(self):
        self.assertEqual(get_provider("higgsfield").name, "fake")
        with mock.patch.dict(os.environ, {"SHOTCRAFT_PROVIDER": ""}):
            self.assertEqual(get_provider("higgsfield").name, "higgsfield")

    def test_prepare_maps_params(self):
        p = FakeProvider()
        out = p.prepare("kling3_0", "x", {"resolution": "1080p", "audio": False, "duration": 5,
                                         "aspect_ratio": "9:16"})
        self.assertEqual(out["params"], {"mode": "pro", "sound": "off", "duration": 5, "aspect_ratio": "9:16"})
        out = p.prepare("text2image_soul_v2", "x", {"resolution": "1.5k", "aspect_ratio": "9:16"})
        self.assertEqual(out["params"], {"quality": "1.5k", "aspect_ratio": "9:16"})
        out = p.prepare("seedance_2_5", "x", {"resolution": "1080p"}, {"start_image": "u1"})
        self.assertEqual(out["params"]["mode"], "omni_reference")
        out = p.prepare("seedance_2_5", "x", {"resolution": "1080p"})
        self.assertEqual(out["params"]["mode"], "t2v")
        out = p.prepare("z_image", "x", {"resolution": "1k", "aspect_ratio": "1:1"}, {"image_references": ["u"]})
        self.assertNotIn("resolution", out["params"])
        self.assertEqual(out["media"], {})
        self.assertTrue(any("resolution" in n for n in out["notes"]))
        out = p.prepare("veo3_1", "x", {"audio": False, "duration": 6})
        self.assertTrue(any("always makes sound" in n for n in out["notes"]))

    def test_higgsfield_argv_and_parsing(self):
        calls = []

        def runner(argv, timeout):
            calls.append(argv)
            if argv[1:3] == ["generate", "cost"]:
                return 0, json.dumps({"credits": 35}), ""
            if argv[1:3] == ["generate", "create"]:
                return 0, json.dumps([{"id": "job-1", "status": "queued"}]), ""
            if argv[1:3] == ["generate", "get"]:
                return 0, json.dumps({"id": "job-1", "status": "completed",
                                      "result_url": "https://cdn.example/x.mp4",
                                      "params": {"start_image": "https://cdn.example/in.png"}}), ""
            if argv[1:3] == ["upload", "create"]:
                return 0, json.dumps({"id": "up-1"}), ""
            return 1, "", "unknown"

        p = hf.HiggsfieldProvider(runner=runner, sleeper=lambda s: None)
        self.assertEqual(p.estimate("seedance_2_5", {"resolution": "720p", "duration": 5}), 35.0)
        job = p.submit("seedance_2_5", "drone over a valley", {"resolution": "1080p", "duration": 5,
                                                               "aspect_ratio": "16:9", "audio": False},
                       {"start_image": "up-1"})
        self.assertEqual(job, "job-1")
        create = calls[1]
        self.assertEqual(create[:4], ["higgsfield", "generate", "create", "seedance_2_5"])
        self.assertIn("--json", create)
        self.assertEqual(create[create.index("--prompt") + 1], "drone over a valley")
        self.assertEqual(create[create.index("--start-image") + 1], "up-1")
        self.assertEqual(create[create.index("--mode") + 1], "omni_reference")
        self.assertEqual(create[create.index("--generate_audio") + 1], "false")
        self.assertEqual(create[create.index("--aspect_ratio") + 1], "16:9")
        st = p.status("job-1")
        self.assertEqual(st["status"], "completed")
        self.assertEqual(st["result_urls"], ["https://cdn.example/x.mp4"])
        self.assertEqual(p.upload(__file__), "up-1")

    def test_higgsfield_backoff_and_auth(self):
        seq = [(1, "", "Higgsfield API error (HTTP 429)"), (1, "", "Failed to decode response. Body: <html>captcha"),
               (0, json.dumps([{"job_set_type": "z_image", "name": "Z Image", "type": "image"}]), "")]
        slept = []

        def runner(argv, timeout):
            return seq.pop(0)

        p = hf.HiggsfieldProvider(runner=runner, sleeper=slept.append)
        models = p.list_models()
        self.assertEqual(models[0]["id"], "z_image")
        self.assertEqual(slept, [30, 30])

        p = hf.HiggsfieldProvider(runner=lambda a, t: (1, "", "Session expired."), sleeper=lambda s: None)
        with self.assertRaises(hf.ProviderAuthError):
            p.list_models()

        p = hf.HiggsfieldProvider(runner=lambda a, t: (1, "", "HTTP 429"), sleeper=lambda s: None)
        with self.assertRaises(hf.ProviderError):
            p.list_models()

    def test_status_normalized(self):
        p = hf.HiggsfieldProvider(runner=lambda a, t: (0, json.dumps({"id": "j", "status": "NSFW"}), ""))
        self.assertEqual(p.status("j")["status"], "nsfw")

    def test_fake_cost_is_deterministic(self):
        p = FakeProvider()
        a = p.estimate("seedance_2_5", {"resolution": "1080p", "duration": 5})
        b = p.estimate("seedance_2_5", {"resolution": "1080p", "duration": 5})
        self.assertEqual(a, b)
        self.assertEqual(a, 20.0)
        self.assertEqual(p.estimate("z_image", {}), 2.0)
        self.assertEqual(p.estimate("text2image_soul_v2", {"resolution": "1.5k"}), 3.0)


# ---------------------------------------------------------------- the gen flow

class GenFlowTests(Base):
    def test_full_single_flow(self):
        proj = self.single_project()
        # estimate: recorded, no money held
        rc, out, err = run_cli("gen", "estimate", "S010", "--tier", "draft", "--project", proj, "--json")
        self.assertEqual(rc, 0, err)
        est = json.loads(out)
        self.assertEqual(est["plan"]["model"], "seedance_2_0")
        self.assertEqual(est["plan"]["params"]["mode"], "fast")
        self.assertEqual(est["plan"]["params"]["resolution"], "480p")
        self.assertEqual(est["plan"]["params"]["duration"], 4)  # 3 s shot -> shortest take that covers it
        self.assertEqual(est["generation"]["status"], "estimated")
        self.assertEqual(est["gates"], [])
        self.assertEqual(budget.status(proj)["reserved"], 0)

        # submit --wait: downloads, names the file, registers the asset, settles the budget
        rc, out, err = run_cli("gen", "submit", "S010", "--tier", "draft", "--wait", "--project", proj, "--json")
        self.assertEqual(rc, 2)  # every generation needs a yes to its price first
        rc, out, err = run_cli("gen", "submit", "S010", "--tier", "draft", "--wait", "--project", proj, "--json",
                               "--user-said", "yes, about 10 credits is fine")
        self.assertEqual(rc, 0, err)
        res = json.loads(out)
        g = res["generations"][0]
        self.assertEqual(g["status"], "completed")
        self.assertEqual(g["outputs"], ["06_generations/drafts/S010-d1.mp4"])
        self.assertTrue(os.path.isfile(os.path.join(proj, g["outputs"][0])))
        st = budget.status(proj)
        self.assertEqual((st["spent"], st["reserved"]), (g["cost_actual"], 0))
        assets = manifest.list_assets(proj, role="draft")
        self.assertEqual(assets[0]["rights"], "generated")
        self.assertEqual(assets[0]["path"], "06_generations/drafts/S010-d1.mp4")

        # a second draft gets the next number
        g2 = gen.submit(proj, "S010", "draft", wait=True, user_said="go")["generations"][0]
        self.assertEqual(g2["outputs"], ["06_generations/drafts/S010-d2.mp4"])

        # finals refused while the drafts stage is open, and without an approved draft
        rc, out, err = run_cli("gen", "submit", "S010", "--tier", "final", "--project", proj)
        self.assertEqual(rc, 2)
        self.assertIn("finals", err)

        from shotcraft import contact_sheet
        contact_sheet.build(proj, "draft", stamp="20261124-101500")
        stages.qa_record(proj, "drafts", 1, "PASS", by="script-supervisor")
        stages.done(proj, "drafts", user_said="drafts look right")
        stages.start(proj, "finals")
        with self.assertRaises(Refused) as cm:
            gen.submit(proj, "S010", "final")
        self.assertIn("no approved draft", str(cm.exception))

        # approval needs the user's words and a completed job
        rc, _, _ = run_cli("gen", "approve", g["id"], "--project", proj, "--user-said", "draft 1 is the one")
        self.assertEqual(rc, 0)
        self.assertTrue(manifest.find_generation(proj, g["id"])["approved"])
        rc, _, _ = run_cli("gen", "reject", g2["id"], "--project", proj, "--user-said", "too dark",
                           "--note", "underexposed")
        self.assertEqual(rc, 0)
        self.assertIs(manifest.find_generation(proj, g2["id"])["approved"], False)

        res = gen.submit(proj, "S010", "final", wait=True, user_said="go")
        f = res["generations"][0]
        self.assertEqual(res["plan"]["model"], "seedance_2_5")
        self.assertEqual(res["plan"]["params"]["resolution"], "1080p")
        self.assertEqual(f["outputs"], ["06_generations/finals/S010-f1.mp4"])
        gen.approve(proj, f["id"], "final approved")
        ok, found, problems = stages.check_evidence(proj, "finals")
        self.assertTrue(ok, problems)

        # status/fetch on a finished job change nothing
        rc, out, _ = run_cli("gen", "status", f["id"], "--project", proj, "--json")
        self.assertEqual(json.loads(out)["status"], "completed")
        rc, out, _ = run_cli("gen", "fetch", f["id"], "--project", proj, "--json")
        self.assertEqual(rc, 0)

    def test_unapproved_card_refused(self):
        proj = self.single_project(approve_card=False)
        with self.assertRaises(Refused) as cm:
            gen.submit(proj, "S010", "draft")
        self.assertIn("not approved", str(cm.exception))

    def test_refine_track_never_generates(self):
        proj = project.init_project("Prompt Only", "refine", use_case="social-vertical", root=self.root)
        stages.start(proj, "refine")
        self.make_card(proj, "S010")
        with self.assertRaises(Refused) as cm:
            gen.submit(proj, "S010", "draft")
        self.assertIn("never generates", str(cm.exception))

    def test_reference_only_input_refused(self):
        proj = self.single_project()
        ref = self.write(proj, "01_research/refs/look.png", "png")
        a = manifest.add_asset(proj, ref, "reference-only", "reference", source_url="https://example.com/x")
        self.make_card(proj, "S020", inputs=[{"asset": a["id"], "as": "start_frame"}])
        with self.assertRaises(Refused) as cm:
            gen.submit(proj, "S020", "draft")
        self.assertIn("reference-only", str(cm.exception))
        # once the user says they own it, it goes through and is uploaded first
        manifest.mark_asset(proj, a["id"], "owned", "that's my own photo")
        g = gen.submit(proj, "S020", "draft", wait=True, user_said="go")["generations"][0]
        self.assertEqual(g["status"], "completed")
        self.assertEqual(g["inputs"], [a["id"]])
        self.assertTrue(g["uploads"])
        self.assertTrue(any(c["call"] == "upload" for c in FakeProvider().calls()))

    def test_owned_input_used_as_start_frame(self):
        proj = self.single_project()
        src = os.path.join(self.tmp, "mine.png")
        with open(src, "wb") as fh:
            fh.write(b"png")
        rc, out, err = run_cli("asset", "add", src, "--rights", "owned", "--role", "input", "--project", proj,
                               "--json")
        self.assertEqual(rc, 0, err)
        aid = json.loads(out)["id"]
        self.make_card(proj, "S030", inputs=[{"asset": aid, "as": "start_frame"}])
        pl = gen.plan(proj, "S030", "draft")
        self.assertEqual(pl["inputs"], {"start_image": [aid]})
        self.assertTrue(pl["motion_only"])

    def test_budget_threshold_needs_user_said(self):
        proj = self.single_project(threshold=1)
        rc, out, err = run_cli("gen", "submit", "S010", "--tier", "draft", "--project", proj)
        self.assertEqual(rc, 2)
        self.assertIn("threshold", err)
        self.assertEqual(budget.status(proj)["reserved"], 0)
        rc, out, err = run_cli("gen", "submit", "S010", "--tier", "draft", "--wait", "--project", proj,
                               "--user-said", "yes, spend it", "--json")
        self.assertEqual(rc, 0, err)
        decisions = manifest.load(proj)["decisions"]
        self.assertTrue(any("overrode" in d["text"] and d["user_said"] == "yes, spend it" for d in decisions))

    def test_every_generation_needs_a_yes_even_under_the_threshold(self):
        proj = self.single_project(threshold=1000)
        with self.assertRaises(Refused) as cm:
            gen.submit(proj, "S010", "draft")
        self.assertIn("priced first", str(cm.exception))
        self.assertEqual(budget.status(proj)["reserved"], 0)
        est = gen.estimate(proj, "S010", "draft")
        self.assertTrue(est["budget"]["needs_user_said"])
        gen.submit(proj, "S010", "draft", user_said="yes, go")
        from shotcraft import config
        cfg = config.load()
        cfg["confirm_every_generation"] = False
        config.save(cfg)
        gen.submit(proj, "S010", "draft")  # opted out: under the threshold goes without asking

    def test_remaining_budget_needs_user_said(self):
        proj = self.single_project(budget_credits=1, threshold=100)
        with self.assertRaises(Refused) as cm:
            gen.submit(proj, "S010", "draft")
        self.assertIn("left in the budget", str(cm.exception))

    def test_failed_job_releases_budget(self):
        proj = self.single_project()
        with mock.patch.dict(os.environ, {"SHOTCRAFT_FAKE_STATUS": "nsfw"}):
            g = gen.submit(proj, "S010", "draft", wait=True, user_said="go")["generations"][0]
        self.assertEqual(g["status"], "nsfw")
        self.assertIn("content filter", g["help"])
        st = budget.status(proj)
        self.assertEqual((st["spent"], st["reserved"]), (0, 0))
        with self.assertRaises(Refused):
            gen.approve(proj, g["id"], "fine")

    def test_submit_without_wait_then_status(self):
        proj = self.single_project()
        g = gen.submit(proj, "S010", "draft", user_said="go")["generations"][0]
        self.assertEqual(g["status"], "submitted")
        self.assertGreater(budget.status(proj)["reserved"], 0)
        g = gen.refresh(proj, g["id"])
        self.assertEqual(g["status"], "completed")
        self.assertEqual(g["outputs"], ["06_generations/drafts/S010-d1.mp4"])
        self.assertEqual(budget.status(proj)["reserved"], 0)

    def test_variants_make_one_generation_each(self):
        proj = self.single_project()
        res = gen.submit(proj, "S010", "draft", variants=2, wait=True, user_said="go")
        self.assertEqual([g["outputs"][0] for g in res["generations"]],
                         ["06_generations/drafts/S010-d1.mp4", "06_generations/drafts/S010-d2.mp4"])

    def test_long_shot_refused_with_chain_plan(self):
        proj = self.single_project(duration=40)
        with self.assertRaises(Refused) as cm:
            gen.submit(proj, "S010", "draft", model="kling3_0_turbo")
        self.assertIn("takes", str(cm.exception))

    def test_element_card_generates_on_the_element_tier_and_locks(self):
        from shotcraft import elements
        proj = project.init_project("Boxer", "full", use_case="social-vertical", root=self.root)
        st = stages.load_state(proj)
        for s in ("intake", "research", "concept", "script", "shotlist"):
            st["stages"][s]["status"] = "done"
        stages.save_state(proj, st)
        with self.assertRaises(Refused):  # elements stage not open
            elements.add(proj, "Boxer", "character")
        st = stages.load_state(proj)
        st["stages"]["elements"]["status"] = "open"
        stages.save_state(proj, st)
        el = elements.add(proj, "Old Boxer", "character", label="Boxer",
                          anchor="a wiry boxer in his sixties, grey stubble, broken nose, faded red hoodie")
        self.assertEqual(el["id"], "E01")
        self.assertEqual(el["views"], {"turnaround": "E01A", "expressions": "E01B"})
        meta, _ = cards.read(os.path.join(proj, "04_elements", "cards", "E01A.md"))
        self.assertIn("turnaround", meta["layers"]["subject"]["subject"])
        self.assertIn("faded red hoodie", meta["layers"]["subject"]["subject"])
        self.assertEqual(meta["tier_plan"], ["element"])
        self.assertIn("text labels", meta["avoid"])
        with self.assertRaises(Refused):
            elements.add(proj, "Another", "character", label="Boxer")  # label taken
        cards.approve(proj, os.path.join(proj, "04_elements", "cards", "E01A.md"), "turnaround looks right")
        cards.approve(proj, os.path.join(proj, "04_elements", "cards", "E01B.md"), "faces too")
        with self.assertRaises(Refused):  # an element card is never a draft
            gen.submit(proj, "E01A", "draft", wait=True, user_said="go")
        g1 = gen.submit(proj, "E01A", "element", wait=True, user_said="go")["generations"][0]
        self.assertEqual(g1["model"], "nano_banana_2")
        self.assertTrue(g1["outputs"][0].startswith("06_generations/elements/E01A-e1"))
        g2 = gen.submit(proj, "E01B", "element", wait=True, user_said="go")["generations"][0]
        with self.assertRaises(Refused):  # no approved take yet
            elements.lock(proj, "E01", "lock him")
        gen.approve(proj, g1["id"], "that's him")
        gen.approve(proj, g2["id"], "good faces")
        el = elements.lock(proj, "@Boxer", "lock him")
        self.assertEqual(el["status"], "locked")
        a = manifest.find_asset(proj, el["assets"][0]["asset"])
        self.assertEqual((a["role"], a["rights"], a["label"]), ("character", "generated", "Boxer"))
        self.assertTrue(stages.check_evidence(proj, "elements")[0])
        elements.link(proj, "E01", "8b2f6a50-1c1e-4a8e-9a43-0d6f5f3c2a11")
        self.assertEqual(elements.get(proj, "E01")["hf_element_id"], "8b2f6a50-1c1e-4a8e-9a43-0d6f5f3c2a11")


# ---------------------------------------------------------------- scout

class ScoutTests(Base):
    def test_no_changes_against_own_list(self):
        rep = scout.check(provider=FakeProvider(), today="2026-11-24")
        self.assertTrue(rep["ok"])
        self.assertEqual((rep["new"], rep["removed"], rep["changed"]), ([], [], []))
        self.assertFalse(rep["canvas_api_detected"])
        self.assertEqual(rep["stale_routing"], [])
        self.assertTrue(os.path.isfile(scout.last_path()))

    def test_diff_new_removed_changed_and_canvas(self):
        live = [m for m in FakeProvider().list_models() if m["id"] != "z_image"]
        for m in live:
            if m["id"] == "kling3_0":
                m["name"] = "Kling 3.0 Omni"
        live.append({"id": "seedance_3_0", "name": "Seedance 3.0", "kind": "video"})
        live.append({"id": "canvas_board", "name": "Canvas Board", "kind": "utility"})
        rep = scout.check(provider=FakeProvider(models=live, help="Commands:\n  canvas   build boards"),
                          today="2026-11-24")
        self.assertEqual([m["id"] for m in rep["new"]], ["canvas_board", "seedance_3_0"])
        self.assertEqual([m["id"] for m in rep["removed"]], ["z_image"])
        self.assertEqual(rep["changed"], [{"id": "kling3_0", "field": "name", "known": "Kling v3.0",
                                           "live": "Kling 3.0 Omni"}])
        self.assertTrue(rep["canvas_api_detected"])
        self.assertIn("2 new", rep["summary"])
        self.assertIn("run model-scout", rep["summary"])
        self.assertEqual(scout.load_last()["new"], rep["new"])

    def test_stale_rows_flagged(self):
        rep = scout.check(provider=FakeProvider(), today="2027-01-30")
        self.assertTrue(rep["stale_routing"])
        self.assertTrue(rep["stale_models"])
        self.assertIn("routing row", rep["summary"])

    def test_cli_scout(self):
        rc, out, err = run_cli("scout", "check", "--json")
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out)["provider"], "fake")
        rc, out, _ = run_cli("scout", "report")
        self.assertEqual(rc, 0)
        self.assertIn("Canvas API", out)

    def test_unavailable_provider(self):
        p = hf.HiggsfieldProvider(cli="definitely-not-installed-xyz")
        rep = scout.check(provider=p, write=False)
        self.assertFalse(rep["ok"])
        self.assertIn("not installed", rep["error"])


if __name__ == "__main__":
    unittest.main()


class FinalVariantTests(unittest.TestCase):
    def test_final_defaults_to_one_take(self):
        import inspect
        from shotcraft import gen as g
        src = inspect.getsource(g.plan)
        self.assertIn('elif tier in ("final", "upscale"):', src)
