"""Core engine tests: project layout, manifest ids, stages, QA rounds, refine track, budget, lessons, CLI."""
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

from shotcraft import Refused, ShotcraftError  # noqa: E402
from shotcraft import budget, lessons, manifest, paths, project, stages  # noqa: E402
import sc  # noqa: E402


def minimal_validate(path):
    meta = stages.read_card_meta(path)
    if not meta or not meta.get("id") or not isinstance(meta.get("layers"), dict):
        return ["bad card"]
    return []


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-test-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home")})
        self.env.start()
        os.environ.pop("CLAUDE_SESSION_ID", None)
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        self.root = os.path.join(self.tmp, "projects")

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make(self, track="full", name="Dawn Reel", **kw):
        return project.init_project(name, track, root=self.root, **kw)

    def write(self, proj, rel, text="content\n"):
        p = os.path.join(proj, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def force(self, proj, **statuses):
        st = stages.load_state(proj)
        for k, v in statuses.items():
            st["stages"][k]["status"] = v
        stages.save_state(proj, st)

    def card(self, proj, sid, kind="video", tier_plan=None):
        meta = {"id": sid, "kind": kind, "tier_plan": tier_plan or ["draft", "final"],
                "layers": {"subject": {"subject": "a lighthouse"}}}
        return self.write(proj, "05_prompts/%s.md" % sid, "---\n%s\n---\n## Prompt\nx\n" % json.dumps(meta))


class ProjectTests(Base):
    def test_slugify(self):
        self.assertEqual(project.slugify("Sydney Dawn Reel!"), "sydney-dawn-reel")
        self.assertEqual(project.slugify("Café  — Ünïcode"), "cafe-unicode")
        self.assertEqual(project.slugify("???"), "project")

    def test_init_layout(self):
        proj = self.make(budget=300, threshold=40)
        self.assertEqual(os.path.basename(proj), "dawn-reel")
        for d in project.FOLDERS:
            self.assertTrue(os.path.isdir(os.path.join(proj, d)), d)
        data = manifest.load(proj)
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["track"], "full")
        self.assertEqual(data["budget"], {"credits": 300, "threshold_single_job": 40, "spent": 0, "reserved": 0})
        self.assertEqual(data["stages_included"], stages.track_stages("full"))
        self.assertEqual(data["handoff"]["canvas_sheet"], "10_handoff/canvas-build-sheet.md")
        st = stages.load_state(proj)
        self.assertTrue(all(st["stages"][s]["status"] == "pending" for s in st["order"]))
        self.assertTrue(os.path.isfile(paths.project_lessons_file(proj)))

    def test_init_refusals(self):
        self.make()
        with self.assertRaises(Refused):
            self.make()
        with self.assertRaises(Refused):
            project.init_project("X", "nope", root=self.root)
        with self.assertRaises(Refused):  # no root and no config
            project.init_project("Y", "full")

    def test_use_case_preset(self):
        if project.load_preset("social-vertical") is None:
            self.skipTest("presets.json not installed")
        proj = self.make(use_case="social-vertical")
        self.assertEqual(manifest.load(proj)["delivery"]["aspect"], "9:16")
        with self.assertRaises(Refused):
            project.init_project("Z", "single", use_case="not-a-preset", root=self.root)

    def test_session_registry(self):
        a = self.make(name="A")
        b = self.make(name="B")
        project.open_project(a, session_id="s1")
        project.open_project(b, session_id="s2")
        self.assertEqual(project.active_project("s1"), a)
        self.assertEqual(project.active_project("s2"), b)
        self.assertEqual(project.active_project("unknown"), b)  # falls back to active.json (last opened)
        with mock.patch.dict(os.environ, {"CLAUDE_SESSION_ID": "s1"}):
            self.assertEqual(project.resolve(), a)
        self.assertEqual(project.resolve(os.path.join(a, "05_prompts")), a)
        shutil.rmtree(b)
        self.assertIsNone(project.active_project("s2"))
        with self.assertRaises(Refused):
            project.resolve(session_id="s2")

    def test_status(self):
        proj = self.make()
        st = project.status(proj)
        self.assertEqual(st["next"], "intake")
        self.assertEqual(st["open"], [])


class ManifestTests(Base):
    def test_ids_and_updates(self):
        proj = self.make()
        p1 = self.write(proj, "01_research/refs/a.jpg")
        p2 = self.write(proj, "00_inputs/b.mov")
        a1 = manifest.add_asset(proj, p1, "reference-only", "reference", source_url="https://example.com/a")
        a2 = manifest.add_asset(proj, p2, "owned", "input")
        self.assertEqual((a1["id"], a2["id"]), ("A001", "A002"))
        self.assertEqual((a1["kind"], a2["kind"]), ("image", "video"))
        self.assertEqual(a1["path"], "01_research/refs/a.jpg")
        self.assertEqual(manifest.find_asset(proj, "A002")["rights"], "owned")
        g1 = manifest.add_generation(proj, shot="S010", tier="draft", model="m")
        g2 = manifest.add_generation(proj, shot="S010", tier="final", model="m")
        self.assertEqual((g1["id"], g2["id"]), ("G0001", "G0002"))
        self.assertEqual(g1["status"], "estimated")
        manifest.update_generation(proj, "G0001", status="completed", outputs=["x.mp4"])
        self.assertEqual(manifest.find_generation(proj, "G0001")["status"], "completed")
        with self.assertRaises(ShotcraftError):
            manifest.update_generation(proj, "G0099", status="failed")
        d = manifest.add_decision(proj, "concept", "Picked B", "go with B")
        self.assertEqual(manifest.load(proj)["decisions"][-1], d)

    def test_rights_rules(self):
        proj = self.make()
        p = self.write(proj, "01_research/refs/a.jpg")
        manifest.add_asset(proj, p, "reference-only", "reference")
        with self.assertRaises(Refused):
            manifest.mark_asset(proj, "A001", "owned", "")
        a = manifest.mark_asset(proj, "A001", "licensed", "we bought it")
        self.assertEqual(a["rights"], "licensed")
        with self.assertRaises(Refused):
            manifest.add_asset(proj, p, "stolen", "reference")
        outside = os.path.join(self.tmp, "elsewhere.jpg")
        open(outside, "w").close()
        with self.assertRaises(Refused):
            manifest.add_asset(proj, outside, "owned", "input")


class StageTests(Base):
    def intake_files(self, proj):
        self.write(proj, "00_brief/job-card.md",
                   "# Job card\n- **Goal:** launch reel\n- **Audience:** surfers\n- **Use case:** social-vertical\n"
                   "| Delivery | 9:16 1080x1920 |\n|---|---|\nBudget: 300 credits\n")
        self.write(proj, "00_brief/grilling.md", "Q: who? A: surfers\n")

    def test_order_and_intake(self):
        proj = self.make()
        with self.assertRaises(Refused):
            stages.start(proj, "research")
        stages.start(proj, "intake")
        with self.assertRaises(Refused):  # no evidence yet
            stages.done(proj, "intake", user_said="yes")
        self.write(proj, "00_brief/job-card.md", "- Goal: x\n- Audience: <who>\n- Use case: TBD\n")
        self.write(proj, "00_brief/grilling.md", "q\n")
        ok, _, problems = stages.check_evidence(proj, "intake")
        self.assertFalse(ok)
        self.assertIn("Audience", problems[0])
        self.intake_files(proj)
        with self.assertRaises(Refused):  # gate needs the user's words
            stages.done(proj, "intake")
        rec = stages.done(proj, "intake", user_said="yes, card is right")
        self.assertEqual(rec["status"], "done")
        self.assertEqual(manifest.load(proj)["decisions"][-1]["user_said"], "yes, card is right")
        with self.assertRaises(Refused):
            stages.start(proj, "intake")
        stages.start(proj, "research")
        with self.assertRaises(Refused):  # concept waits for research
            stages.start(proj, "concept")

    def test_skip(self):
        proj = self.make()
        with self.assertRaises(Refused):
            stages.skip(proj, "research", "")
        stages.skip(proj, "research", "no research needed")
        self.assertNotIn("research", manifest.load(proj)["stages_included"])
        with self.assertRaises(Refused):  # script is not optional
            stages.skip(proj, "script", "drop it")
        stages.skip(proj, "script", "skip the script, I have one")
        self.assertEqual(stages.load_state(proj)["stages"]["script"]["status"], "skipped")

    def test_qa_rounds_and_escalation(self):
        proj = self.make()
        self.force(proj, intake="done")
        stages.start(proj, "research")
        self.write(proj, "01_research/direction-note.md", "Direction\n")
        ref = self.write(proj, "01_research/refs/r.jpg")
        manifest.add_asset(proj, ref, "reference-only", "reference")
        with self.assertRaises(Refused):  # QA gate
            stages.done(proj, "research")
        with self.assertRaises(Refused):  # FAIL needs findings
            stages.qa_record(proj, "research", 1, "FAIL")
        with self.assertRaises(Refused):  # wrong round number
            stages.qa_record(proj, "research", 2, "PASS")
        stages.qa_record(proj, "research", 1, "FAIL", findings=[{"what": "thin"}])
        self.assertTrue(os.path.isfile(os.path.join(paths.qa_dir(proj, "research"), "round-1.json")))
        stages.qa_record(proj, "research", 2, "FAIL", findings=[{"what": "thin"}])
        stages.qa_record(proj, "research", 3, "FAIL", findings=[{"what": "thin"}])
        qa = stages.qa_status(proj, "research")
        self.assertTrue(qa["escalate"])
        self.assertIsNone(qa["next_round"])
        with self.assertRaises(Refused):
            stages.qa_record(proj, "research", 4, "PASS")
        with self.assertRaises(Refused):  # escalated: only the user's words close it
            stages.done(proj, "research")
        rec = stages.done(proj, "research", user_said="good enough, move on")
        self.assertTrue(rec["qa_override"])

    def test_qa_pass_closes(self):
        proj = self.make()
        self.force(proj, intake="done")
        stages.start(proj, "research")
        self.write(proj, "01_research/direction-note.md", "Direction\n")
        manifest.add_asset(proj, self.write(proj, "01_research/refs/r.jpg"), "reference-only", "reference")
        stages.qa_record(proj, "research", 1, "PASS")
        with self.assertRaises(Refused):
            stages.qa_record(proj, "research", 2, "PASS")
        self.assertEqual(stages.done(proj, "research")["status"], "done")

    def test_reopen(self):
        proj = self.make()
        self.force(proj, intake="done", research="done", concept="done")
        st = stages.load_state(proj)
        st["stages"]["script"]["status"] = "open"
        st["stages"]["script"]["qa_rounds"] = [{"round": 1, "verdict": "FAIL"}]
        stages.save_state(proj, st)
        self.write(proj, ".shotcraft/qa/script/round-1.json", "{}")
        res = stages.reopen(proj, "research", note="new refs", user_said="redo the research")
        self.assertEqual(res["reset"], ["concept", "script"])
        st = stages.load_state(proj)
        self.assertEqual(st["stages"]["research"]["status"], "open")
        self.assertEqual(st["stages"]["concept"]["status"], "pending")
        self.assertEqual(st["stages"]["script"]["qa_rounds"], [])
        self.assertEqual(st["stages"]["concept"]["history"][-1]["status"], "done")
        self.assertTrue(os.path.isfile(os.path.join(paths.qa_dir(proj, "script"), "history", "cycle-1",
                                                    "round-1.json")))
        self.assertEqual(st["stages"]["intake"]["status"], "done")
        with self.assertRaises(Refused):
            stages.reopen(proj, "learn")  # still pending

    def test_reopen_skipped_brings_it_back(self):
        proj = self.make()
        self.force(proj, intake="done")
        stages.skip(proj, "research", "no research")
        stages.reopen(proj, "research")
        self.assertIn("research", manifest.load(proj)["stages_included"])

    def test_sound_then_assembly_in_order(self):
        proj = self.make()
        order = stages.track_stages("full")
        self.assertNotIn("mograph", order)  # motion graphics live outside shotcraft
        self.force(proj, **{s: "done" for s in order[:order.index("sound")]})
        stages.start(proj, "sound")
        with self.assertRaises(Refused):
            stages.start(proj, "assembly")

    def test_one_open_at_a_time(self):
        proj = self.make()
        self.force(proj, intake="done", research="open")
        self.force(proj, concept="done")
        with self.assertRaises(Refused):
            stages.start(proj, "script")

    def test_paths_for_guard(self):
        proj = self.make()
        self.assertEqual(stages.stage_for_path(proj, "03_script/script.md"), "script")
        self.assertEqual(stages.stage_for_path(proj, "03_script/shotlist.md"), "shotlist")
        self.assertEqual(stages.stage_for_path(proj, "06_generations/upscaled/x.mp4"), "finals")
        self.assertEqual(stages.stage_for_path(proj, "./05_prompts/S010.md"), "prompts")
        self.assertIsNone(stages.stage_for_path(proj, "06_generations/contact-sheets/a.html"))
        self.assertFalse(stages.path_writable(proj, "project.json")[0])
        self.assertFalse(stages.path_writable(proj, ".shotcraft/stages.json")[0])
        self.assertFalse(stages.path_writable(proj, ".shotcraft/qa/script/round-1.json")[0])
        self.assertTrue(stages.path_writable(proj, "00_inputs/me.mov")[0])
        self.assertTrue(stages.path_writable(proj, ".shotcraft/lessons.md")[0])
        self.assertFalse(stages.path_writable(proj, "00_brief/job-card.md")[0])
        stages.start(proj, "intake")
        self.assertTrue(stages.path_writable(proj, "00_brief/job-card.md")[0])
        self.assertTrue(stages.stage_open(proj, "intake"))
        self.force(proj, intake="done")
        ok, why = stages.path_writable(proj, "00_brief/job-card.md")
        self.assertFalse(ok)
        self.assertIn("reopen", why)

    def test_shotlist_and_generation_evidence(self):
        proj = self.make()
        self.write(proj, "03_script/shotlist.md",
                   "# Shots\n\n| Shot | Duration (s) | Purpose | Kind | Image-first |\n|---|---|---|---|---|\n"
                   "| S010 | 4 | open on the sea | video | yes |\n| S020 | 3s | the reveal | video | no |\n")
        rows = stages.parse_shotlist(proj)
        self.assertEqual([r["id"] for r in rows], ["S010", "S020"])
        self.assertEqual(rows[1]["duration_value"], 3.0)
        self.assertTrue(rows[0]["image_first"])
        self.assertTrue(stages._ev_shotlist(proj, {"path": "03_script/shotlist.md"})[0])
        self.write(proj, "03_script/shotlist.md", "| id | duration_s | purpose |\n|--|--|--|\n| S010 | | x |\n")
        self.assertFalse(stages._ev_shotlist(proj, {"path": "03_script/shotlist.md"})[0])
        self.write(proj, "03_script/shotlist.md",
                   "| id | duration_s | purpose | image_first |\n|--|--|--|--|\n| S010 | 4 | a | yes |\n"
                   "| S020 | 3 | b | |\n")
        order = stages.track_stages("full")
        with mock.patch.object(stages, "validate_card", minimal_validate):
            self.card(proj, "S010")
            self.force(proj, **{s: "done" for s in order[:order.index("prompts")]})
            stages.start(proj, "prompts")
            ok, _, probs = stages.check_evidence(proj, "prompts")
            self.assertFalse(ok)
            self.assertIn("S020", probs[0])
            self.card(proj, "S020")
            self.assertTrue(stages.check_evidence(proj, "prompts")[0])
            self.write(proj, "05_prompts/S030.md", "no front matter")
            self.assertFalse(stages.check_evidence(proj, "prompts")[0])
            os.remove(os.path.join(proj, "05_prompts/S030.md"))
            # boards: only S010 is image-first
            self.force(proj, prompts="done", boards="open")
            manifest.add_generation(proj, shot="S010", tier="board", status="completed")
            self.assertFalse(stages.check_evidence(proj, "boards")[0])  # no contact sheet
            from shotcraft import contact_sheet
            self.write(proj, "06_generations/contact-sheets/boards.html", "<html></html>")
            self.assertFalse(stages.check_evidence(proj, "boards")[0])  # a hand-written sheet does not count
            contact_sheet.build(proj, "board", stamp="20261124-100000")
            self.assertTrue(stages.check_evidence(proj, "boards")[0])
            # drafts: every shot
            self.force(proj, boards="done", drafts="open")
            manifest.add_generation(proj, shot="S010", tier="draft", status="completed")
            contact_sheet.build(proj, "draft", stamp="20261124-100100")
            ok, _, probs = stages.check_evidence(proj, "drafts")
            self.assertFalse(ok)
            self.assertIn("S020", probs[0])
            manifest.add_generation(proj, shot="S020", tier="draft", status="failed")
            self.assertFalse(stages.check_evidence(proj, "drafts")[0])
            manifest.add_generation(proj, shot="S020", tier="draft", status="completed")
            self.assertFalse(stages.check_evidence(proj, "drafts")[0])  # the sheet doesn't show the new take
            contact_sheet.build(proj, "draft", stamp="20261124-100200")
            self.assertTrue(stages.check_evidence(proj, "drafts")[0])
            # finals: approved, none undecided
            self.force(proj, drafts="done", finals="open")
            manifest.add_generation(proj, shot="S010", tier="final", status="completed", approved=True)
            g = manifest.add_generation(proj, shot="S020", tier="upscale", status="completed")
            self.assertFalse(stages.check_evidence(proj, "finals")[0])
            manifest.update_generation(proj, g["id"], approved=True)
            self.assertTrue(stages.check_evidence(proj, "finals")[0])
            manifest.add_generation(proj, shot="S020", tier="final", status="completed")
            self.assertFalse(stages.check_evidence(proj, "finals")[0])  # one left undecided

    def test_delivery_and_sound_evidence(self):
        proj = self.make()
        self.write(proj, "07_sound/music.wav", "x")
        self.assertFalse(stages.check_evidence(proj, "sound")[0])
        self.write(proj, "07_sound/licences.md", "Track from X, licensed")
        self.assertTrue(stages.check_evidence(proj, "sound")[0])
        from shotcraft import delivery
        self.write(proj, "09_delivery/delivery-report.json", json.dumps({"verdict": "PASS"}))
        self.assertFalse(stages.check_evidence(proj, "delivery")[0])  # a hand-written report does not count
        self.write(proj, "09_delivery/reel.mp4", "x")
        delivery.record(proj, {"verdict": "PASS", "checks": [{"name": "fps"}], "failed": [], "spec": {}})
        self.assertTrue(stages.check_evidence(proj, "delivery")[0])
        self.write(proj, "09_delivery/reel.mp4", "changed")
        self.assertFalse(stages.check_evidence(proj, "delivery")[0])  # file changed since the check
        delivery.record(proj, {"verdict": "FAIL", "checks": [{}, {}], "failed": ["loudness"], "spec": {}})
        ok, _, probs = stages.check_evidence(proj, "delivery")
        self.assertFalse(ok)
        self.assertIn("loudness", probs[0])

    def test_learn_needs_decided_lessons(self):
        proj = self.make()
        lessons.add("Prefers slow push-ins", project=proj)
        self.assertFalse(stages.check_evidence(proj, "learn")[0])
        lessons.decide(1, "accept", "yes keep that", project=proj)
        self.assertTrue(stages.check_evidence(proj, "learn")[0])


class RefineAndSingleTests(Base):
    def test_refine_track_blocks_generation(self):
        proj = self.make(track="refine")
        self.assertEqual(stages.load_state(proj)["order"], ["refine"])
        stages.start(proj, "refine")
        for tier in ("board", "draft", "final", "upscale"):
            ok, why = stages.gen_allowed(proj, tier)
            self.assertFalse(ok)
            self.assertIn("never generates", why)
        self.assertEqual(stages.stage_for_path(proj, "05_prompts/S010.md"), "refine")
        with mock.patch.object(stages, "validate_card", minimal_validate):
            with self.assertRaises(Refused):
                stages.done(proj, "refine")
            self.card(proj, "S010")
            self.assertEqual(stages.done(proj, "refine")["status"], "done")

    def test_single_track_gen_gates(self):
        proj = self.make(track="single")
        self.assertEqual(stages.load_state(proj)["order"],
                         ["intake", "prompts", "drafts", "finals", "delivery", "handoff", "learn"])
        ok, why = stages.gen_allowed(proj, "board")
        self.assertFalse(ok)
        self.force(proj, intake="done", prompts="done", drafts="open")
        self.assertTrue(stages.gen_allowed(proj, "draft")[0])
        self.assertFalse(stages.gen_allowed(proj, "final")[0])
        self.assertEqual(stages.gen_stage_for_tier("upscale"), "finals")
        with mock.patch.object(stages, "validate_card", minimal_validate):
            self.card(proj, "S010", kind="image")
            self.assertEqual(stages.planned_shots(proj), ["S010"])


class BudgetTests(Base):
    def test_threshold_and_remaining(self):
        proj = self.make(budget=100, threshold=50)
        self.assertTrue(budget.check(proj, 50)["ok"])
        r = budget.check(proj, 51)
        self.assertFalse(r["ok"])
        self.assertTrue(r["needs_user_said"])
        self.assertTrue(budget.check(proj, 51, user_said="fine, go")["ok"])
        with self.assertRaises(Refused):
            budget.require(proj, 80)
        budget.reserve(proj, 40, gen_id="G0001")
        self.assertEqual(budget.status(proj)["remaining"], 60)
        budget.commit(proj, 40, 35, gen_id="G0001")
        st = budget.status(proj)
        self.assertEqual((st["spent"], st["reserved"], st["remaining"]), (35, 0, 65))
        r = budget.check(proj, 45)
        self.assertTrue(r["ok"])
        budget.reserve(proj, 30)
        r = budget.check(proj, 45)  # 35 left
        self.assertFalse(r["ok"])
        self.assertIn("left in the budget", r["reason"])
        budget.release(proj, 30)
        self.assertEqual(budget.status(proj)["reserved"], 0)
        self.assertEqual([e["op"] for e in budget.ledger(proj)], ["reserve", "commit", "reserve", "release"])
        with self.assertRaises(Refused):
            budget.check(proj, -1)

    def test_no_total_budget(self):
        proj = self.make(threshold=50)
        self.assertIsNone(budget.status(proj)["remaining"])
        self.assertTrue(budget.check(proj, 49)["ok"])
        self.assertFalse(budget.check(proj, 500)["ok"])


class LessonsTests(Base):
    def test_inbox(self):
        a = lessons.add("Likes warm grades")
        b = lessons.add("Kling for physics", kind="model")
        self.assertEqual((a["n"], b["n"]), (1, 2))
        with self.assertRaises(Refused):
            lessons.add("x", kind="weird")
        with self.assertRaises(Refused):
            lessons.decide(1, "accept", "")
        item = lessons.decide(2, "reject", 'not "always"')
        self.assertEqual(item["status"], "rejected")
        items = lessons.list_lessons()
        self.assertEqual(items[1]["user_said"], 'not "always"')
        self.assertEqual(lessons.open_count(), 1)
        self.assertTrue(paths.user_lessons_file().startswith(os.environ["SHOTCRAFT_HOME"]))


class CliTests(Base):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = sc.main(list(argv))
        return rc, out.getvalue(), err.getvalue()

    def test_flow(self):
        rc, out, _ = self.run_cli("setup", "--projects-root", self.root, "--json")
        self.assertEqual(rc, 0)
        self.assertTrue(json.loads(out)["config"]["first_run_done"])
        rc, out, _ = self.run_cli("project", "init", "--name", "Test Reel", "--track", "full", "--budget", "100",
                                  "--session-id", "sess1", "--json")
        self.assertEqual(rc, 0)
        proj = json.loads(out)["project"]
        rc, out, _ = self.run_cli("--json", "stage", "status", "--session-id", "sess1")
        self.assertEqual(json.loads(out)["next"], "intake")
        rc, out, err = self.run_cli("stage", "start", "research", "--session-id", "sess1")
        self.assertEqual(rc, 2)
        self.assertIn("intake", err)
        rc, out, _ = self.run_cli("stage", "start", "intake", "--project", proj, "--json")
        self.assertEqual(rc, 0)
        rc, out, _ = self.run_cli("budget", "check", "--credits", "60", "--json")
        self.assertEqual(rc, 2)
        self.assertTrue(json.loads(out)["needs_user_said"])
        rc, out, _ = self.run_cli("budget", "check", "--credits", "60", "--user-said", "ok", "--json")
        self.assertEqual(rc, 0)
        src = os.path.join(self.tmp, "my-shoot.mov")
        open(src, "w").close()
        rc, out, _ = self.run_cli("asset", "add", src, "--rights", "owned", "--role", "input", "--json")
        self.assertEqual(rc, 0)
        a = json.loads(out)
        self.assertEqual((a["id"], a["path"]), ("A001", "00_inputs/my-shoot.mov"))
        rc, out, _ = self.run_cli("lessons", "add", "Prefers 24 fps", "--json")
        self.assertEqual(json.loads(out)["inbox"], paths.project_lessons_file(proj))
        rc, out, _ = self.run_cli("lessons", "decide", "1", "accept", "--user-said", "yes")
        self.assertEqual(rc, 0)
        findings = self.write(proj, "00_inputs/f.json", "[{\"what\": \"x\"}]")
        rc, out, _ = self.run_cli("qa", "record", "--stage", "intake", "--round", "1", "--verdict", "fail",
                                  "--findings", findings, "--json")
        self.assertEqual(rc, 0)
        rc, out, _ = self.run_cli("qa", "status", "--stage", "intake", "--json")
        self.assertEqual(json.loads(out)["next_round"], 2)
        rc, out, _ = self.run_cli("project", "status")
        self.assertEqual(rc, 0)
        self.assertIn("Test Reel", out)

    def test_delegation_missing_module(self):
        with mock.patch("importlib.import_module", side_effect=ModuleNotFoundError("x", name="shotcraft.handoff")):
            rc, out, err = self.run_cli("handoff", "build")
        self.assertEqual(rc, 1)
        self.assertIn("not available", err)

    def test_delegation_calls_module(self):
        fake = mock.Mock()
        fake.cli_gen_status = mock.Mock(return_value=0)
        with mock.patch("importlib.import_module", return_value=fake):
            rc, _, _ = self.run_cli("gen", "status", "G0001", "--json")
        self.assertEqual(rc, 0)
        args = fake.cli_gen_status.call_args[0][0]
        self.assertEqual((args.gen_id, args.json), ("G0001", True))

    def test_no_project(self):
        rc, _, err = self.run_cli("stage", "status")
        self.assertEqual(rc, 2)
        self.assertIn("No active project", err)


if __name__ == "__main__":
    unittest.main()
