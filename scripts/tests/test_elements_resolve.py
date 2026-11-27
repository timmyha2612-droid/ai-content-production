"""Element-first flow: scenes -> shots, elements attached to shot cards, and the DaVinci hand-off package."""
import csv
import os
import shutil
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from shotcraft import Refused  # noqa: E402
from shotcraft import cards, elements, manifest, project, resolve, stages  # noqa: E402

SHOTLIST = """# Shot list

## Scenes

| Scene | Place | Time | Mode | Elements |
|---|---|---|---|---|
| SC01 | INT. BOXING GYM | NIGHT | shots | @Boxer @Gym |
| SC02 | EXT. ROOFTOP | DAWN | shots | @Boxer |

## Shots

| Shot | Scene | Duration (s) | Purpose | Elements |
|---|---|---|---|---|
| S010 | SC01 | 4 | he wraps his hands | |
| S020 | SC01 | 3 | the first punch | @Boxer @Gym @Gloves |
| S030 | SC02 | 5 | sunrise, he breathes | |
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-el-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home"),
                                                "SHOTCRAFT_PROVIDER": "fake"})
        self.env.start()
        self.proj = project.init_project("Old Boxer", "full", use_case="social-vertical",
                                         root=os.path.join(self.tmp, "projects"))
        with open(os.path.join(self.proj, "03_script", "shotlist.md"), "w", encoding="utf-8") as fh:
            fh.write(SHOTLIST)

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def force(self, **kw):
        st = stages.load_state(self.proj)
        for k, v in kw.items():
            st["stages"][k]["status"] = v
        stages.save_state(self.proj, st)

    def locked_element(self, name, category, label):
        self.force(elements="open")
        el = elements.add(self.proj, name, category, label=label, anchor=name)
        path = os.path.join(self.proj, "06_generations", "elements", "%s.png" % el["id"])
        with open(path, "wb") as fh:
            fh.write(b"png")
        assets = []
        for view in el["views"]:
            a = manifest.add_asset(self.proj, path, "generated", "character" if category == "character" else
                                   ("environment" if category == "environment" else "prop"))
            assets.append({"asset": a["id"], "view": view, "gen": None, "path": a["path"]})
        el.update({"status": "locked", "assets": assets})
        elements._save_element(self.proj, el)
        return el


class SceneTests(Base):
    def test_scenes_and_shot_elements(self):
        self.assertEqual([s["scene"] for s in stages.parse_scenes(self.proj)], ["SC01", "SC02"])
        self.assertEqual([r["id"] for r in stages.parse_shotlist(self.proj)], ["S010", "S020", "S030"])
        self.assertTrue(stages._ev_shotlist(self.proj, {"path": "03_script/shotlist.md"})[0])
        se = elements.shot_elements(self.proj)
        self.assertEqual(se["S010"], ["Boxer", "Gym"])  # from its scene
        self.assertEqual(se["S020"], ["Boxer", "Gym", "Gloves"])  # its own cell wins
        self.assertEqual(se["S030"], ["Boxer"])

    def test_shots_of_a_scene_must_be_together(self):
        with open(os.path.join(self.proj, "03_script", "shotlist.md"), "a", encoding="utf-8") as fh:
            fh.write("| S040 | SC01 | 2 | back in the gym | |\n")
        ok, _, why = stages._ev_shotlist(self.proj, {"path": "03_script/shotlist.md"})
        self.assertFalse(ok)
        self.assertIn("not together", why)


class ElementTests(Base):
    def test_views_come_from_the_recipes(self):
        cats = elements.recipes()
        for c in ("character", "environment", "prop", "style"):
            self.assertIn(c, cats)
            for v, r in cats[c]["views"].items():
                self.assertTrue(r.get("layers", {}).get("subject"), (c, v))
        self.force(elements="open")
        el = elements.add(self.proj, "Boxing gym", "environment", views=["plate", "reverse"], anchor="a gym")
        meta, _ = cards.read(os.path.join(self.proj, "04_elements", "cards", el["views"]["plate"] + ".md"))
        self.assertIn("people", meta["avoid"])
        self.assertIn("nobody in frame", meta["layers"]["subject"]["subject"])
        self.assertEqual(meta["layers"]["world"]["environment"], "a gym")  # the anchor once, in the world layer
        with self.assertRaises(Refused):
            elements.add(self.proj, "x", "prop", views=["turnaround"])
        # sheets are clean whatever the job's look; plates keep it
        prop = elements.add(self.proj, "Cup", "prop", anchor="a black cup")
        pm, _ = cards.read(os.path.join(self.proj, "04_elements", "cards", prop["views"]["product"] + ".md"))
        self.assertEqual(pm.get("finish"), "clean")
        self.assertNotIn("finish", meta)

    def test_elements_evidence_needs_every_named_element(self):
        self.locked_element("Old boxer", "character", "Boxer")
        self.locked_element("Gym", "environment", "Gym")
        ok, _, probs = stages.check_evidence(self.proj, "elements")
        self.assertFalse(ok)
        self.assertIn("@Gloves", probs[0])
        self.locked_element("Gloves", "prop", "Gloves")
        self.assertTrue(stages.check_evidence(self.proj, "elements")[0])

    def test_attach_puts_locked_elements_on_the_cards(self):
        for name, cat, lab in (("Old boxer", "character", "Boxer"), ("Gym", "environment", "Gym"),
                               ("Gloves", "prop", "Gloves")):
            self.locked_element(name, cat, lab)
        self.force(elements="done", prompts="open")
        for sid in ("S010", "S020", "S030"):
            meta = cards.new_card(sid, kind="video", use_case="social-vertical")
            cards.write(os.path.join(self.proj, "05_prompts", sid + ".md"), meta, cards.render_body(meta))
        plan, problems = elements.attach_plan(self.proj)
        self.assertEqual(problems, [])
        roles = {(p["shot"], p["label"]): p["as"] for p in plan}
        self.assertEqual(roles[("S020", "Boxer")], "character")
        self.assertEqual(roles[("S020", "Gym")], "reference")
        with self.assertRaises(Refused):
            elements.attach(self.proj, None, "")
        done = elements.attach(self.proj, ["S020"], "put them on")
        self.assertTrue(done)
        meta, _ = cards.read(os.path.join(self.proj, "05_prompts", "S020.md"))
        self.assertEqual({i["as"] for i in meta["inputs"]}, {"character", "reference"})


class ResolveTests(Base):
    def finals(self):
        for sid in ("S010", "S020", "S030"):
            path = os.path.join(self.proj, "06_generations", "finals", "%s-f1.mp4" % sid)
            with open(path, "wb") as fh:
                fh.write(b"not really a video")
            manifest.add_generation(self.proj, shot=sid, tier="final", status="completed", approved=True,
                                    outputs=["06_generations/finals/%s-f1.mp4" % sid], model="seedance_2_5",
                                    prompt="prompt for %s" % sid)

    def test_package_needs_the_user_to_ask(self):
        self.finals()
        with self.assertRaises(Refused) as cm:
            resolve.build(self.proj)
        self.assertIn("include handoff", str(cm.exception))

    def test_package_layout_timeline_and_evidence(self):
        self.finals()
        stages.include(self.proj, "handoff", "make the davinci package")
        self.force(handoff="open")
        rec = resolve.build(self.proj)
        self.assertEqual(rec["clips"], 3)
        base = os.path.join(self.proj, resolve.OUT_DIR)
        self.assertTrue(os.path.isfile(os.path.join(base, "SC01", "SC01_S010_v1.mp4")))
        self.assertTrue(os.path.isfile(os.path.join(base, "SC02", "SC02_S030_v1.mp4")))
        root = ET.parse(os.path.join(base, "timeline.fcpxml")).getroot()
        self.assertEqual(root.tag, "fcpxml")
        fmt = root.find("resources/format")
        self.assertEqual((fmt.get("width"), fmt.get("height"), fmt.get("frameDuration")), ("1080", "1920", "1/30s"))
        clips = root.findall(".//spine/asset-clip")
        self.assertEqual([c.get("name") for c in clips], ["SC01_S010_v1", "SC01_S020_v1", "SC02_S030_v1"])
        self.assertEqual([c.get("offset") for c in clips], ["0s", "4s", "7s"])
        self.assertEqual([c.get("duration") for c in clips], ["4s", "3s", "5s"])
        self.assertTrue(root.find("resources/asset/media-rep").get("src").startswith("file:///"))
        with open(os.path.join(base, "shots.csv"), encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(rows[0]["place"], "INT. BOXING GYM")
        self.assertEqual(rows[1]["elements"], "@Boxer @Gym @Gloves")
        self.assertTrue(stages.check_evidence(self.proj, "handoff")[0])
        with open(os.path.join(base, "shots.csv"), "a", encoding="utf-8") as fh:
            fh.write("tampered\n")
        self.assertFalse(stages.check_evidence(self.proj, "handoff")[0])

    def test_ntsc_and_missing_finals(self):
        self.assertEqual(resolve.frame_duration(23.976), (1001, 24000))
        self.assertEqual(resolve._t(resolve._frames(4, (1001, 24000)), (1001, 24000)), "1001/250s")  # 96 frames of 1001/24000 s
        stages.include(self.proj, "handoff", "package it")
        self.force(handoff="open")
        with self.assertRaises(Refused) as cm:
            resolve.build(self.proj)
        self.assertIn("S010 has no approved final", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
