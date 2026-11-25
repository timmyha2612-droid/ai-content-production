"""Media tools: contact sheet HTML, delivery checks, the animatic, the hand-off sheet, reference rights."""
import csv
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

from shotcraft import Refused, ShotcraftError  # noqa: E402
from shotcraft import assembly, contact_sheet, delivery, handoff, manifest, project, refs, stages  # noqa: E402
import sc  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))
PNG_1X1 = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
           b"\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff\xff?\x00\x05\xfe\x02\xfe\xa7V\xbd\xfa\x00\x00\x00\x00IEND\xaeB`\x82")


def ff(*args):
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + list(args), check=True, stdout=subprocess.DEVNULL,
                   stderr=subprocess.DEVNULL)


def make_clip(path, w=320, h=240, dur=2, fps=30, audio=True, vcodec="libx264"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    args = ["-f", "lavfi", "-i", "testsrc=size=%dx%d:rate=%s:duration=%s" % (w, h, fps, dur)]
    if audio:
        args += ["-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=%s" % dur,
                 "-c:a", "aac", "-shortest"]
    args += ["-c:v", vcodec, "-preset", "ultrafast", "-pix_fmt", "yuv420p", path]
    ff(*args)
    return path


def make_png(path, w=64, h=64):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if HAVE_FFMPEG:
        ff("-f", "lavfi", "-i", "color=c=red:s=%dx%d" % (w, h), "-frames:v", "1", path)
    else:
        with open(path, "wb") as fh:
            fh.write(PNG_1X1)
    return path


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-media-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home"),
                                                "SHOTCRAFT_PROVIDER": "fake"})
        self.env.start()
        os.environ.pop("CLAUDE_SESSION_ID", None)
        os.environ.pop("CLAUDE_CODE_SESSION_ID", None)
        self.root = os.path.join(self.tmp, "projects")

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def make(self, track="full", use_case="social-vertical", name="Media Test"):
        return project.init_project(name, track, use_case=use_case, root=self.root)

    def write(self, proj, rel, text="content\n"):
        p = os.path.join(proj, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(text)
        return p

    def card(self, proj, sid, duration=2, handles=0, kind="video", inputs=None, title=None, body=None):
        meta = {"id": sid, "title": title or "Shot %s" % sid, "kind": kind, "use_case": "social-vertical",
                "tier_plan": ["draft", "final"], "model": {"draft": "seedance_2_0", "final": "seedance_2_5"},
                "settings": {"aspect": "9:16", "resolution": "1080p", "duration_s": duration, "audio": False},
                "handles_s": handles, "inputs": inputs or [],
                "layers": {"subject": {"subject": "a lighthouse"}}}
        text = "---\n%s\n---\n%s" % (json.dumps(meta, indent=2), body or "## Prompt (compiled for x)\nA lighthouse.\n")
        return self.write(proj, "05_prompts/%s.md" % sid, text)

    def shotlist(self, proj, rows):
        lines = ["| id | duration_s | purpose |", "|---|---|---|"]
        lines += ["| %s | %s | %s |" % r for r in rows]
        return self.write(proj, "03_script/shotlist.md", "\n".join(lines) + "\n")

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = sc.main(list(argv))
        return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------- contact sheet

class ContactSheetTests(Base):
    def test_sheet_html(self):
        proj = self.make()
        self.shotlist(proj, [("S010", 2, "Hook"), ("S020", 3, "Reveal")])
        self.card(proj, "S010", title="Dawn reveal")
        self.card(proj, "S020")
        self.write(proj, "06_generations/drafts/S010-d1.mp4", "not really a video")
        make_png(os.path.join(proj, "06_generations/drafts/S010-d2.png"))
        manifest.add_generation(proj, shot="S010", tier="draft", model="seedance_2_0", status="completed",
                                prompt="A <b>lighthouse</b> & sea", cost_actual=22,
                                outputs=["06_generations/drafts/S010-d1.mp4", "06_generations/drafts/S010-d2.png"],
                                approved=True, approval_said="love the second one",
                                params={"aspect_ratio": "9:16", "duration": 5})
        manifest.add_generation(proj, shot="S020", tier="draft", model="seedance_2_0", status="nsfw",
                                cost_estimate=22, outputs=[])
        manifest.add_generation(proj, shot="S010", tier="final", model="seedance_2_5", status="completed",
                                outputs=["06_generations/finals/S010-f1.mp4"])
        res = contact_sheet.build(proj, "draft", stamp="20261124-101500")
        self.assertEqual(res["rel"], "06_generations/contact-sheets/draft-20261124-101500.html")
        with open(res["path"], encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn('<video src="../drafts/S010-d1.mp4" controls loop muted', text)
        self.assertIn('<img src="../drafts/S010-d2.png"', text)
        self.assertIn("A &lt;b&gt;lighthouse&lt;/b&gt; &amp; sea", text)
        self.assertNotIn("<b>lighthouse", text)
        self.assertIn("Approved", text)
        self.assertIn("love the second one", text)
        self.assertIn("Blocked by the content filter", text)
        self.assertIn("prefers-color-scheme: dark", text)
        self.assertIn("Dawn reveal", text)
        self.assertNotIn("S010-f1", text)  # finals are not on the draft sheet
        self.assertLess(text.index('id="S010"'), text.index('id="S020"'))
        self.assertEqual(res["totals"]["cost"], 22)  # the blocked (nsfw) job is not charged
        ok, _, _ = stages._ev_contact_sheet(proj, {"tier": "draft"})
        self.assertTrue(ok)

    def test_final_sheet_and_cli(self):
        proj = self.make()
        self.card(proj, "S010")
        manifest.add_generation(proj, shot="S010", tier="upscale", model="topaz_video", status="completed",
                                outputs=["06_generations/upscaled/S010-u1.mp4"])
        rc, out, err = self.run_cli("sheet", "build", "--tier", "final", "--project", proj, "--json")
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        self.assertIn("final-", data["rel"])
        self.assertEqual(data["missing"], ["06_generations/upscaled/S010-u1.mp4"])
        with open(data["path"], encoding="utf-8") as fh:
            self.assertIn("File not found", fh.read())


# ---------------------------------------------------------------- delivery

@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class DeliveryTests(Base):
    def test_video_pass_and_report(self):
        proj = self.make()
        clip = make_clip(os.path.join(proj, "09_delivery", "reel.mp4"), w=1080, h=1920, dur=2, fps=30)
        lu = delivery.loudness(clip)
        self.assertIsNotNone(lu)
        rep = delivery.check(proj, duration=2, lufs=lu["integrated_lufs"])
        names = {c["check"]: c["verdict"] for c in rep["checks"]}
        for k in ("resolution", "aspect", "frame rate", "video codec", "duration", "loudness"):
            self.assertEqual(names.get(k), "PASS", (k, rep["checks"]))
        self.assertTrue(os.path.isfile(os.path.join(proj, delivery.REPORT)))
        ok, _, why = stages._ev_delivery_report(proj, {"path": delivery.REPORT})
        if names.get("true peak") == "PASS":
            self.assertEqual(rep["verdict"], "PASS")
            self.assertTrue(ok, why)

    def test_video_fail(self):
        proj = self.make()
        make_clip(os.path.join(proj, "09_delivery", "wrong.mp4"), w=320, h=240, dur=1, fps=25, audio=False)
        rep = delivery.check(proj)
        self.assertEqual(rep["verdict"], "FAIL")
        failed = {c["check"] for c in rep["checks"] if c["verdict"] == "FAIL"}
        self.assertTrue({"resolution", "aspect", "frame rate", "duration"} <= failed, failed)
        ok, _, _ = stages._ev_delivery_report(proj, {"path": delivery.REPORT})
        self.assertFalse(ok)
        rc, out, _ = self.run_cli("delivery", "check", "--project", proj, "--json")
        self.assertEqual(rc, 2)
        self.assertEqual(json.loads(out)["verdict"], "FAIL")

    def test_shot_duration_from_card(self):
        proj = self.make()
        self.card(proj, "S010", duration=1)
        make_clip(os.path.join(proj, "09_delivery", "S010-final.mp4"), w=1080, h=1920, dur=1, fps=30, audio=False)
        rep = delivery.check(proj)
        dur = [c for c in rep["checks"] if c["check"] == "duration"][0]
        self.assertEqual(dur["verdict"], "PASS", dur)
        self.assertIn("S010", dur["expected"])

    def test_image(self):
        proj = self.make(use_case="thumbnail", name="Thumb")
        make_png(os.path.join(proj, "09_delivery", "thumb.png"), 1280, 720)
        rep = delivery.check(proj)
        self.assertEqual(rep["verdict"], "PASS", rep["checks"])
        self.assertIn("file size", {c["check"] for c in rep["checks"]})

    def test_no_files(self):
        proj = self.make()
        rep = delivery.check(proj)
        self.assertEqual(rep["verdict"], "FAIL")


# ---------------------------------------------------------------- assembly

@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class AssemblyTests(Base):
    def test_animatic(self):
        proj = self.make()
        self.shotlist(proj, [("S010", 1, "Hook"), ("S020", 1.5, "Reveal"), ("S030", 1, "End")])
        self.card(proj, "S010", duration=1, handles=0.5)
        self.card(proj, "S020", duration=1.5)
        self.card(proj, "S030", duration=1)
        make_clip(os.path.join(proj, "06_generations/finals/S010-f1.mp4"), dur=2)
        make_clip(os.path.join(proj, "06_generations/drafts/S010-d1.mp4"), dur=2)
        make_clip(os.path.join(proj, "06_generations/drafts/S020-d1.mp4"), dur=2)
        manifest.add_generation(proj, shot="S010", tier="draft", status="completed", approved=True,
                                outputs=["06_generations/drafts/S010-d1.mp4"])
        manifest.add_generation(proj, shot="S010", tier="final", status="completed", approved=True,
                                outputs=["06_generations/finals/S010-f1.mp4"])
        manifest.add_generation(proj, shot="S020", tier="draft", status="completed",
                                outputs=["06_generations/drafts/S020-d1.mp4"])
        audio = os.path.join(self.tmp, "music.m4a")
        ff("-f", "lavfi", "-i", "sine=frequency=220:duration=1", "-c:a", "aac", audio)
        res = assembly.build(proj, audio=audio)
        out = os.path.join(proj, assembly.OUT)
        self.assertTrue(os.path.isfile(out))
        p = delivery.probe(out)
        self.assertEqual((p["width"], p["height"]), (1080, 1920))
        self.assertAlmostEqual(p["duration"], 3.5, delta=0.15)
        self.assertTrue(p["has_audio"])
        with open(os.path.join(proj, assembly.CSV), encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual([r["shot"] for r in rows], ["S010", "S020", "S030"])
        self.assertEqual(rows[0]["source_tier"], "final")
        self.assertEqual(rows[0]["src_in_s"], "0.500")   # handles trimmed
        self.assertEqual(rows[1]["source_tier"], "draft")
        self.assertEqual(rows[2]["source_tier"], "slate")
        self.assertEqual(rows[2]["rec_in_s"], "2.500")
        self.assertTrue(any("S030" in n for n in res["notes"]))

    def test_still_board(self):
        proj = self.make()
        self.card(proj, "S010", duration=1)
        make_png(os.path.join(proj, "06_generations/boards/S010-b1.png"), 320, 240)
        manifest.add_generation(proj, shot="S010", tier="board", status="completed",
                                outputs=["06_generations/boards/S010-b1.png"])
        rc, out, err = self.run_cli("assembly", "animatic", "--project", proj, "--json")
        self.assertEqual(rc, 0, err)
        data = json.loads(out)
        self.assertEqual(data["segments"][0]["source_kind"], "image")
        self.assertAlmostEqual(delivery.probe(os.path.join(proj, assembly.OUT))["duration"], 1.0, delta=0.1)


# ---------------------------------------------------------------- handoff

class HandoffTests(Base):
    def setup_project(self):
        proj = self.make()
        self.shotlist(proj, [("S010", 2, "Hook")])
        frame = make_png(os.path.join(proj, "00_inputs", "frame.png"))
        a1 = manifest.add_asset(proj, frame, "owned", "input", shot="S010")
        ref = make_png(os.path.join(proj, "01_research", "refs", "x", "ref.png"))
        a2 = manifest.add_asset(proj, ref, "reference-only", "reference", source_url="https://example.com/ref.png")
        hero = make_png(os.path.join(proj, "04_bible", "characters", "hero.png"))
        a3 = manifest.add_asset(proj, hero, "generated", "character")
        self.card(proj, "S010", inputs=[{"asset": a1["id"], "as": "start_frame"},
                                        {"asset": a2["id"], "as": "reference"}])
        self.write(proj, "06_generations/finals/S010-f1.mp4", "video bytes")
        manifest.add_generation(proj, shot="S010", tier="final", model="seedance_2_5", status="completed",
                                prompt="The camera pushes in slowly on the lighthouse.",
                                params={"aspect_ratio": "9:16", "resolution": "1080p", "duration": 5,
                                        "audio": False, "start_image": a1["id"], "image_references": [a2["id"]]},
                                outputs=["06_generations/finals/S010-f1.mp4"], approved=True,
                                approval_said="yes that one")
        return proj, a1, a2, a3

    def test_build_sheet(self):
        proj, a1, a2, a3 = self.setup_project()
        res = handoff.build(proj)
        self.assertEqual(res["shots"], 1)
        with open(os.path.join(proj, handoff.SHEET), encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn("{{", text)
        self.assertIn("The camera pushes in slowly on the lighthouse.", text)
        self.assertIn("seedance_2_5", text)
        self.assertIn("start frame", text)
        self.assertIn("00_inputs/frame.png", text)
        self.assertIn("reference-only", text)
        self.assertIn('approved: "yes that one"', text)
        with open(os.path.join(proj, handoff.UPLOAD_LIST), encoding="utf-8") as fh:
            ul = json.load(fh)
        paths = {i["path"] for i in ul["items"]}
        self.assertEqual(paths, {"06_generations/finals/S010-f1.mp4", "00_inputs/frame.png",
                                 "04_bible/characters/hero.png"})
        self.assertEqual([s["path"] for s in ul["skipped"]], ["01_research/refs/x/ref.png"])
        plan = ul["canvas"]["shots"][0]
        ports = {e["port"] for e in plan["edges"]}
        self.assertIn("start_image", ports)
        self.assertIn("prompt", ports)
        self.assertNotIn("image_references", ports)  # the reference-only input is not connected
        self.assertTrue(stages._ev_file(proj, {"path": handoff.SHEET})[0])
        self.assertTrue(stages._ev_json(proj, {"path": handoff.UPLOAD_LIST})[0])

    def test_upload_dry_run_and_fake(self):
        proj, a1, a2, a3 = self.setup_project()
        rc, out, err = self.run_cli("handoff", "upload", "--dry-run", "--project", proj, "--json")
        self.assertEqual(rc, 0, err)
        self.assertEqual(len(json.loads(out)["would_upload"]), 3)
        res = handoff.upload(proj)
        self.assertEqual(len(res["uploaded"]), 3)
        self.assertFalse(res["failed"])
        data = manifest.load(proj)
        self.assertEqual(len(data["handoff"]["uploaded"]), 3)
        with open(os.path.join(proj, handoff.SHEET), encoding="utf-8") as fh:
            self.assertIn("fake-upload-", fh.read())
        again = handoff.upload(proj)
        self.assertEqual(again["uploaded"], [])
        self.assertEqual(again["already"], 3)


# ---------------------------------------------------------------- refs

class RefsTests(Base):
    def test_fetch_file_url_tags_reference_only(self):
        proj = self.make()
        src = make_png(os.path.join(self.tmp, "web", "look.png"))
        url = "file://" + src
        res = refs.fetch(proj, url, note="the look", shot="S010")
        self.assertEqual(res["method"], "download")
        a = res["assets"][0]
        self.assertEqual(a["rights"], "reference-only")
        self.assertEqual(a["role"], "reference")
        self.assertEqual(a["source_url"], url)
        self.assertEqual(a["shot"], "S010")
        self.assertTrue(a["path"].startswith("01_research/refs/"))
        self.assertTrue(os.path.isfile(os.path.join(proj, res["folder"], "source.json")))
        chk = refs.rights_check(proj, [a["id"]])
        self.assertFalse(chk["ok"])
        self.assertIn("reference-only", chk["reason"])
        with self.assertRaises(Refused):
            refs.require_rights(proj, [a["id"]])
        self.assertFalse(refs.rights_check(proj, ["A999"])["ok"])
        manifest.mark_asset(proj, a["id"], "licensed", "we bought this one")
        self.assertTrue(refs.rights_check(proj, [a["id"]])["ok"])

    def test_cli_fetch(self):
        proj = self.make()
        src = make_png(os.path.join(self.tmp, "web", "b.png"))
        rc, out, err = self.run_cli("refs", "fetch", "file://" + src, "--project", proj, "--json")
        self.assertEqual(rc, 0, err)
        self.assertEqual(json.loads(out)["assets"][0]["rights"], "reference-only")

    def test_video_platform_needs_ytdlp(self):
        proj = self.make()
        self.assertTrue(refs.is_video_platform("https://www.instagram.com/reel/abc/"))
        self.assertFalse(refs.is_video_platform("https://example.com/a.jpg"))
        with mock.patch("shotcraft.refs.shutil.which", return_value=None):
            with self.assertRaises(ShotcraftError):
                refs.fetch(proj, "https://www.youtube.com/watch?v=xyz")
            page = self.write(proj, "../page.html", "<html><body>hi</body></html>")
            with self.assertRaises(Refused):
                refs.fetch(proj, "file://" + os.path.abspath(page))
        self.assertEqual(os.listdir(os.path.join(proj, "01_research", "refs")), [])

    def test_ytdlp_route_mocked(self):
        proj = self.make()

        def fake_ytdlp(url, folder, notes, cookies=None, timeout=900):
            p = os.path.join(folder, "clip-abc.mp4")
            with open(p, "wb") as fh:
                fh.write(b"x")
            return [p], {"title": "A reel", "uploader": "someone"}
        with mock.patch("shotcraft.refs.shutil.which", return_value="/usr/bin/yt-dlp"), \
                mock.patch("shotcraft.refs._ytdlp", side_effect=fake_ytdlp):
            res = refs.fetch(proj, "https://www.tiktok.com/@x/video/1")
        self.assertEqual(res["method"], "yt-dlp")
        self.assertEqual(res["assets"][0]["rights"], "reference-only")
        self.assertEqual(res["assets"][0]["kind"], "video")
        self.assertIn("A reel", res["assets"][0]["note"])

    def test_refuses_non_web(self):
        proj = self.make()
        with self.assertRaises(Refused):
            refs.fetch(proj, "/tmp/some/file.png")


if __name__ == "__main__":
    unittest.main()
