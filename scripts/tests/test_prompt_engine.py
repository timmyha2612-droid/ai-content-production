"""Tests for the prompt engine: rules merge, cards and the compiler.

These tests build their own tiny rule dicts and model profiles, so they do not depend on
rules/models.json or other files written elsewhere.
"""

import argparse
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shotcraft import cards, compiler, rules  # noqa: E402

PLUGIN_RULES = HERE.parent.parent / "rules"


def video_card(**over):
    meta = cards.new_card("S010", kind="video", use_case="social-vertical")
    meta["layers"]["subject"]["subject"] = "a red fox"
    meta["layers"]["subject"]["action"] = "trots through fresh snow"
    meta["settings"].update({"aspect": "9:16", "resolution": "1080p", "duration_s": 6, "audio": False})
    meta["avoid"] = []
    for k, v in over.items():
        meta[k] = v
    return meta


TINY_REWRITES = {
    "camera shake": "locked-off tripod shot, perfectly stable frame",
    "camera shake (moving camera)": "smooth, stabilised camera movement",
    "blurry": "tack-sharp focus",
}

PROFILE = {
    "id": "test_video",
    "name": "Test Video",
    "kind": "video",
    "durations": [4, 6, 8],
    "resolutions": ["720p", "1080p"],
    "aspects": ["16:9", "9:16", "1:1"],
    "start_frame": True,
    "end_frame": False,
    "refs": {"image": 2},
    "audio": False,
    "negative_prompt": False,
    "max_prompt_words": 120,
}


class RulesMergeTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def _write(self, layer, name, data):
        d = self.tmp / layer
        d.mkdir(parents=True, exist_ok=True)
        (d / (name + ".json")).write_text(json.dumps(data), encoding="utf-8")
        return d

    def test_deep_merge_dicts_and_list_replace(self):
        base = {"a": {"x": 1, "y": [1, 2]}, "b": 1}
        over = {"a": {"y": [9]}, "c": 3}
        self.assertEqual(rules.deep_merge(base, over), {"a": {"x": 1, "y": [9]}, "b": 1, "c": 3})
        self.assertEqual(base["a"]["y"], [1, 2], "base must not be mutated")

    def test_plus_key_appends(self):
        base = {"universal": ["blurry", "watermark"]}
        over = {"universal+": ["watermark", "noise"]}
        self.assertEqual(rules.deep_merge(base, over), {"universal": ["blurry", "watermark", "noise"]})

    def test_three_layers(self):
        p = self._write("plugin", "negatives", {"universal": ["a"], "by_category": {"text": ["t1"]}, "k": 1})
        u = self._write("user", "negatives", {"universal+": ["b"], "k": 2})
        pr = self._write("project", "negatives", {"by_category": {"text": ["t2"]}, "universal+": ["c"]})
        merged = rules.load_from_dirs("negatives", [p, u, pr, self.tmp / "missing"])
        self.assertEqual(merged["universal"], ["a", "b", "c"])
        self.assertEqual(merged["by_category"]["text"], ["t2"])
        self.assertEqual(merged["k"], 2)

    def test_plus_key_with_nothing_below(self):
        u = self._write("user", "x", {"items+": ["only"]})
        self.assertEqual(rules.load_from_dirs("x", [u]), {"items": ["only"]})

    def test_rule_dirs_order(self):
        dirs = rules.rule_dirs(project=str(self.tmp / "proj"))
        self.assertEqual(dirs[-1], self.tmp / "proj" / ".shotcraft" / "rules")
        self.assertEqual(len(dirs), 3)

    def test_bad_json_raises(self):
        d = self.tmp / "bad"
        d.mkdir()
        (d / "taxonomy.json").write_text("{nope", encoding="utf-8")
        with self.assertRaises(rules.RulesError):
            rules.load_from_dirs("taxonomy", [d])


class CardTest(unittest.TestCase):
    def test_roundtrip(self):
        meta = video_card()
        body = cards.render_body(meta)
        text = cards.dump(meta, body)
        meta2, body2 = cards.parse_text(text)
        self.assertEqual(meta, meta2)
        self.assertEqual(body.strip(), body2.strip())
        tmp = Path(tempfile.mkdtemp())
        try:
            path = tmp / "05_prompts" / "S010.md"
            cards.write(path, meta, body)
            meta3, body3 = cards.read(path)
            self.assertEqual(meta, meta3)
            self.assertIn("## Prompt", body3)
        finally:
            shutil.rmtree(tmp)

    def test_parse_errors(self):
        with self.assertRaises(cards.CardError):
            cards.parse_text("no front matter")
        with self.assertRaises(cards.CardError):
            cards.parse_text("---\n{\"id\": 1\n---\n")
        with self.assertRaises(cards.CardError):
            cards.parse_text("---\n{\"id\": \"S010\"}\n")

    def test_new_card_is_valid_once_subject_filled(self):
        meta = video_card()
        self.assertEqual(cards.validate(meta), [])

    def test_new_card_uses_preset(self):
        presets = {"presets": {"broll-insert": {"kind": "video", "aspect": "16:9", "handles_s": 0.5,
                                                "resolution": {"draft": "720p", "final": "1080p"},
                                                "duration": {"typical": 4, "min": 2, "max": 10}}}}
        meta = cards.new_card("S020", use_case="broll-insert", presets=presets)
        self.assertEqual(meta["kind"], "video")
        self.assertEqual(meta["settings"]["aspect"], "16:9")
        self.assertEqual(meta["settings"]["duration_s"], 4)
        self.assertEqual(meta["handles_s"], 0.5)

    def test_from_text_sorts_terms_and_keeps_description(self):
        tax = {"layers": {
            "camera": {"fields": {"movement": {"priority": 94, "vocab": [{"term": "push-in", "means": ""}]},
                                  "movement_speed": {"priority": 92, "vocab": [{"term": "slow", "means": ""}]},
                                  "lens": {"priority": 74, "vocab": [{"term": "50mm", "means": ""}]}}},
            "world": {"fields": {"time_of_day": {"priority": 82, "vocab": [{"term": "golden hour", "means": ""}]}}},
        }}
        meta = cards.new_card("S010", kind="video",
                              from_text="a barista pours latte art in a sunlit cafe, slow push-in, 50mm, golden hour",
                              taxonomy=tax)
        L = meta["layers"]
        self.assertEqual(L["subject"]["subject"], "a barista pours latte art in a sunlit cafe")
        self.assertEqual(L["camera"]["movement"], "push-in")
        self.assertEqual(L["camera"]["lens"], "50mm")
        self.assertEqual(L["camera"]["movement_speed"], "slow")
        self.assertEqual(L["world"]["time_of_day"], "golden hour")

    def test_validate_errors(self):
        meta = video_card()
        meta["id"] = "shot1"
        meta["kind"] = "gif"
        meta["settings"]["aspect"] = "wide"
        meta["inputs"] = [{"asset": "X1", "as": "start"}]
        meta["layers"]["camera"]["zoomies"] = "x"
        meta["layers"]["bogus"] = {}
        meta["status"] = "approved"
        errs = cards.validate(meta)
        joined = "\n".join(errs)
        for needle in ("id must be", "kind must be", "settings.aspect", "inputs[0].asset", "inputs[0].as",
                       "layers.camera.zoomies", "Unknown layer 'bogus'", "approved_said"):
            self.assertIn(needle, joined)

    def test_validate_video_needs_duration_and_beats_fit(self):
        meta = video_card()
        meta["settings"]["duration_s"] = 0
        self.assertTrue(any("duration_s" in e for e in cards.validate(meta)))
        meta = video_card()
        meta["layers"]["time_output"]["beats"] = [{"t": "0-4", "what": "a"}, {"t": "3-8", "what": "b"}]
        errs = cards.validate(meta)
        self.assertTrue(any("overlaps" in e for e in errs))
        self.assertTrue(any("past the shot length" in e for e in errs))

    def test_validate_needs_subject(self):
        meta = video_card()
        meta["layers"]["subject"]["subject"] = ""
        meta["layers"]["subject"]["action"] = ""
        self.assertTrue(any("subject or the action" in e for e in cards.validate(meta)))

    def test_validate_use_case_against_presets(self):
        meta = video_card()
        errs = cards.validate(meta, presets={"presets": {"thumbnail": {}}})
        self.assertTrue(any("not a known preset" in e for e in errs))


class CompileTest(unittest.TestCase):
    def test_order_and_basic_params(self):
        meta = video_card()
        meta["layers"]["world"]["environment"] = "pine forest"
        meta["layers"]["camera"]["movement"] = "slow dolly in"
        meta["layers"]["light_look"]["setup"] = "golden hour backlight"
        meta["layers"]["light_look"]["style_ref"] = "nature documentary"
        out = compiler.compile(meta, PROFILE, {"positive_rewrites": TINY_REWRITES})
        p = out["prompt"].lower()
        order = [p.index("red fox"), p.index("pine forest"), p.index("dolly in"),
                 p.index("golden hour backlight"), p.index("nature documentary")]
        self.assertEqual(order, sorted(order))
        self.assertEqual(out["params"], {"aspect_ratio": "9:16", "resolution": "1080p", "duration": 6})
        self.assertEqual(out["adjustments"], [])
        self.assertIsNone(out["negative_prompt"])
        self.assertEqual(out["word_count"], len(p.split()))
        self.assertNotIn("intent", json.dumps(out["dropped_fields"]))

    def test_defaults_without_profile(self):
        out = compiler.compile(video_card(), {}, {})
        self.assertEqual(out["max_prompt_words"], 120)
        self.assertIsNone(out["negative_prompt"])

    def test_trim_in_priority_order(self):
        meta = video_card()
        L = meta["layers"]
        L["light_look"]["texture"] = "Kodak Vision3 500T grain with warm halation around highlights"
        L["light_look"]["practicals"] = "string lights and a glowing neon sign in the far background"
        L["world"]["era"] = "late nineteen seventies small town Americana"
        L["camera"]["camera_look"] = "shot on a large format digital cinema camera"
        L["world"]["environment"] = "snowy pine forest clearing"
        L["camera"]["movement"] = "slow tracking shot alongside"
        L["camera"]["shot_size"] = "wide shot"
        # Fixed part without the four lowest fields:
        base = compiler.compile(dict(meta, layers={**L, "light_look": {**L["light_look"], "texture": "", "practicals": ""},
                                                   "world": {**L["world"], "era": ""},
                                                   "camera": {**L["camera"], "camera_look": ""}}),
                                PROFILE, {})["word_count"]
        prof = dict(PROFILE, max_prompt_words=base + 9)  # room for era (6 words) but not more
        tax = {"layers": {"light_look": {"fields": {"texture": {"priority": 10}, "practicals": {"priority": 20}}},
                          "world": {"fields": {"era": {"priority": 30}}},
                          "camera": {"fields": {"camera_look": {"priority": 40}}}}}
        out = compiler.compile(meta, prof, {"taxonomy": tax})
        dropped = [d["field"] for d in out["dropped_fields"]]
        self.assertEqual(dropped[:2], ["light_look.texture", "light_look.practicals"])
        self.assertLessEqual(out["word_count"], prof["max_prompt_words"])
        self.assertIn("red fox", out["prompt"].lower())
        self.assertIn("tracking shot", out["prompt"].lower())
        # Tighter limit: era and camera look go too, in that order; protected fields stay.
        prof2 = dict(PROFILE, max_prompt_words=base)
        out2 = compiler.compile(meta, prof2, {"taxonomy": tax})
        dropped2 = [d["field"] for d in out2["dropped_fields"]]
        self.assertEqual(dropped2[:4], ["light_look.texture", "light_look.practicals", "world.era",
                                        "camera.camera_look"])
        self.assertLessEqual(out2["word_count"], base)
        self.assertIn("trots through fresh snow", out2["prompt"].lower())

    def test_cannot_trim_protected_warns(self):
        meta = video_card()
        meta["layers"]["subject"]["subject"] = " ".join(["word"] * 50)
        out = compiler.compile(meta, dict(PROFILE, max_prompt_words=10), {})
        self.assertTrue(out["warnings"])
        self.assertIn("word word", out["prompt"])

    def test_avoid_rewritten_when_no_negative_field(self):
        meta = video_card(avoid=["camera shake", "blurry", "purple elephants"])
        out = compiler.compile(meta, PROFILE, {"positive_rewrites": TINY_REWRITES})
        self.assertIsNone(out["negative_prompt"])
        self.assertIn("locked-off tripod shot", out["prompt"].lower())
        self.assertIn("tack-sharp focus", out["prompt"].lower())
        self.assertEqual(out["unguarded"], ["purple elephants"])
        self.assertNotIn("camera shake", out["prompt"])

    def test_avoid_rewrite_respects_camera_move(self):
        meta = video_card(avoid=["camera shake"])
        meta["layers"]["camera"]["movement"] = "orbit"
        out = compiler.compile(meta, PROFILE, {"positive_rewrites": TINY_REWRITES})
        self.assertIn("smooth, stabilised camera movement", out["prompt"].lower())
        self.assertNotIn("locked-off", out["prompt"])

    def test_avoid_goes_to_negative_field(self):
        meta = video_card(avoid=["camera shake", "purple elephants"])
        out = compiler.compile(meta, dict(PROFILE, negative_prompt=True), {"positive_rewrites": TINY_REWRITES})
        self.assertEqual(out["negative_prompt"], "camera shake, purple elephants")
        self.assertNotIn("tripod", out["prompt"])
        self.assertEqual(out["unguarded"], [])

    def test_by_model_negatives_added(self):
        meta = video_card(avoid=[])
        rules_bundle = {"negatives": {"by_model": {"test_video": ["blurry"]}}, "positive_rewrites": TINY_REWRITES}
        out = compiler.compile(meta, PROFILE, rules_bundle)
        self.assertIn("tack-sharp focus", out["prompt"].lower())

    def test_start_frame_motion_only(self):
        meta = video_card(inputs=[{"asset": "A003", "as": "start_frame"}])
        L = meta["layers"]
        L["world"]["environment"] = "pine forest"
        L["light_look"]["setup"] = "golden hour backlight"
        L["camera"]["shot_size"] = "wide shot"
        L["camera"]["movement"] = "slow push-in"
        L["time_output"]["beats"] = [{"t": "0-3", "what": "fox looks up"}, {"t": "3-6", "what": "fox bounds away"}]
        out = compiler.compile(meta, PROFILE, {})
        self.assertTrue(out["motion_only"])
        p = out["prompt"].lower()
        for kept in ("trots through fresh snow", "slow push-in", "fox looks up", "fox bounds away"):
            self.assertIn(kept, p)
        for gone in ("red fox", "pine forest", "golden hour backlight", "wide shot"):
            self.assertNotIn(gone, p)
        dropped = {d["field"] for d in out["dropped_fields"]}
        self.assertTrue({"subject.subject", "world.environment", "light_look.setup", "camera.shot_size"} <= dropped)
        self.assertEqual(out["params"]["start_image"], "A003")

    def test_start_frame_on_model_without_one(self):
        meta = video_card(inputs=[{"asset": "A003", "as": "start_frame"}])
        out = compiler.compile(meta, dict(PROFILE, start_frame=False), {})
        self.assertFalse(out["motion_only"])
        self.assertNotIn("start_image", out["params"])
        self.assertEqual(out["params"]["image_references"], ["A003"])
        self.assertIn("red fox", out["prompt"].lower())
        self.assertTrue(any(a["param"] == "start_image" for a in out["adjustments"]))

    def test_duration_not_allowed_nearest(self):
        meta = video_card()
        meta["settings"]["duration_s"] = 7  # allowed 4, 6, 8 -> tie, take the longer
        out = compiler.compile(meta, PROFILE, {})
        self.assertEqual(out["params"]["duration"], 8)
        adj = [a for a in out["adjustments"] if a["param"] == "duration"][0]
        self.assertEqual((adj["from"], adj["to"]), (7, 8))
        meta["settings"]["duration_s"] = 5.2
        out = compiler.compile(meta, PROFILE, {})
        self.assertEqual(out["params"]["duration"], 6)
        meta["settings"]["duration_s"] = 30
        self.assertEqual(compiler.compile(meta, PROFILE, {})["params"]["duration"], 8)

    def test_duration_handles_and_range(self):
        meta = video_card()
        meta["settings"]["duration_s"] = 4
        meta["handles_s"] = 0.5
        prof = dict(PROFILE, durations={"min": 3, "max": 15})
        out = compiler.compile(meta, prof, {})
        self.assertEqual(out["params"]["duration"], 5)
        self.assertEqual(out["requested_duration_s"], 5)
        meta["settings"]["duration_s"] = 1
        meta["handles_s"] = 0
        out = compiler.compile(meta, prof, {})
        self.assertEqual(out["params"]["duration"], 3)
        self.assertTrue(out["adjustments"])

    def test_aspect_not_allowed_adjusted(self):
        meta = video_card()
        meta["settings"]["aspect"] = "4:5"
        out = compiler.compile(meta, PROFILE, {})
        self.assertEqual(out["params"]["aspect_ratio"], "1:1")
        adj = [a for a in out["adjustments"] if a["param"] == "aspect_ratio"]
        self.assertEqual(len(adj), 1)
        self.assertEqual(adj[0]["from"], "4:5")
        self.assertIn("crop", adj[0]["reason"])

    def test_resolution_and_audio_and_refs(self):
        meta = video_card(inputs=[{"asset": "A001", "as": "reference"}, {"asset": "A002", "as": "character"},
                                  {"asset": "A004", "as": "style"}])
        meta["settings"]["resolution"] = "4k"
        meta["settings"]["audio"] = True
        meta["layers"]["time_output"]["audio"] = "birdsong"
        out = compiler.compile(meta, PROFILE, {})
        self.assertEqual(out["params"]["resolution"], "1080p")
        self.assertEqual(out["params"]["image_references"], ["A001", "A002"])
        params = {a["param"] for a in out["adjustments"]}
        self.assertTrue({"resolution", "audio", "image_references"} <= params)
        self.assertNotIn("birdsong", out["prompt"])
        meta["settings"]["resolution"] = "540p"
        self.assertEqual(compiler.compile(meta, PROFILE, {})["params"]["resolution"], "720p")

    def test_image_card_skips_motion_fields(self):
        meta = cards.new_card("S030", kind="image", use_case="thumbnail")
        meta["layers"]["subject"]["subject"] = "a surprised chef"
        meta["layers"]["camera"]["movement"] = "orbit"
        meta["layers"]["time_output"]["on_screen_text"] = "TOO SALTY?"
        meta["settings"].update({"aspect": "16:9", "resolution": "2k"})
        prof = {"kind": "image", "aspects": ["16:9", "1:1"], "resolutions": ["1k", "2k"]}
        out = compiler.compile(meta, prof, {})
        self.assertNotIn("orbit", out["prompt"])
        self.assertIn('"TOO SALTY?"', out["prompt"])
        self.assertNotIn("duration", out["params"])


class RealRulesTest(unittest.TestCase):
    """Sanity checks on the shipped rule files written by this part."""

    def load(self, name):
        with open(PLUGIN_RULES / (name + ".json"), encoding="utf-8") as fh:
            return json.load(fh)

    def test_rewrites_cover_negatives(self):
        neg, rw = self.load("negatives"), self.load("positive_rewrites")
        terms = set(neg["universal"])
        for lst in list(neg["by_category"].values()) + list(neg["by_model"].values()):
            terms |= set(lst)
        self.assertEqual(sorted(t for t in terms if t not in rw), [])

    def test_taxonomy_shape(self):
        tax = self.load("taxonomy")
        total = 0
        for lname, fields in cards.LAYER_FIELDS.items():
            for f in fields:
                fd = tax["layers"][lname]["fields"][f]
                self.assertTrue(fd["label"] and fd["help"])
                self.assertIsInstance(fd["priority"], (int, float))
                for v in fd["vocab"]:
                    self.assertTrue(v["term"] and v["means"])
                total += len(fd["vocab"])
        self.assertGreaterEqual(total, 300)
        p = {k: tax["layers"][k.split(".")[0]]["fields"][k.split(".")[1]]["priority"]
             for k in ("light_look.texture", "light_look.practicals", "world.era", "camera.camera_look")}
        self.assertLess(p["light_look.texture"], p["light_look.practicals"])
        self.assertLess(p["light_look.practicals"], p["world.era"])
        self.assertLess(p["world.era"], p["camera.camera_look"])

    def test_presets_complete(self):
        pre = self.load("presets")["presets"]
        for pid in ("social-vertical", "social-square", "social-landscape", "youtube", "youtube-short",
                    "thumbnail", "icon-ui", "logo-animation", "web-hero", "banner-ad", "broll-insert",
                    "real-estate", "product-shot", "storyboard-animatic", "billboard-print", "presentation"):
            p = pre[pid]
            for key in ("aspect", "resolution", "fps", "duration", "handles_s", "delivery_formats", "need", "notes"):
                self.assertIn(key, p, "{} lacks {}".format(pid, key))
        self.assertIn("svg", pre["icon-ui"]["delivery_formats"][0].lower())


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.old_home = os.environ.get("SHOTCRAFT_HOME")
        os.environ["SHOTCRAFT_HOME"] = str(self.tmp / "home")

    def tearDown(self):
        if self.old_home is None:
            os.environ.pop("SHOTCRAFT_HOME", None)
        else:
            os.environ["SHOTCRAFT_HOME"] = self.old_home
        shutil.rmtree(self.tmp)

    def run_cli(self, fn, **kw):
        ns = argparse.Namespace(json=True, **kw)
        buf, err = io.StringIO(), io.StringIO()
        with redirect_stdout(buf), redirect_stderr(err):
            code = fn(ns)
        out = buf.getvalue()
        return code, (json.loads(out) if out.strip() else None)

    def test_card_new_validate_and_refine_save(self):
        proj = self.tmp / "proj"
        (proj / ".shotcraft").mkdir(parents=True)
        code, out = self.run_cli(cards.cli_card_new, shot="S010", kind="video", use_case=None,
                                 from_text="a red fox trots through fresh snow, slow push-in", project=str(proj))
        self.assertEqual(code, 0, out)
        path = proj / "05_prompts" / "S010.md"
        self.assertTrue(path.is_file())
        code, out = self.run_cli(cards.cli_card_validate, path=str(path), project=str(proj))
        self.assertEqual(code, 2)  # use_case still empty
        meta, body = cards.read(path)
        meta["use_case"] = "social-vertical"
        cards.write(path, meta, body)
        code, out = self.run_cli(cards.cli_card_validate, path=str(path), project=str(proj))
        self.assertEqual(code, 0, out)
        code, out = self.run_cli(cards.cli_card_new, shot="S010", kind="video", use_case=None,
                                 from_text=None, project=str(proj))
        self.assertEqual(code, 2)  # already exists
        code, out = self.run_cli(cards.cli_refine_save, path=str(path), slug="Fox Test")
        self.assertEqual(code, 0, out)
        self.assertTrue(Path(out["path"]).is_file())
        self.assertIn("fox-test", out["path"])

    def test_card_compile_cli_uses_project_models(self):
        proj = self.tmp / "proj"
        rdir = proj / ".shotcraft" / "rules"
        rdir.mkdir(parents=True)
        (rdir / "models.json").write_text(json.dumps(
            {"providers": {"higgsfield": {"models": {"test_video": PROFILE}}}}), encoding="utf-8")
        path = proj / "05_prompts" / "S010.md"
        cards.write(path, video_card())
        code, out = self.run_cli(cards.cli_card_compile, path=str(path), model="test_video",
                                 provider=None, project=str(proj))
        self.assertEqual(code, 0, out)
        self.assertIn("red fox", out["prompt"].lower())
        _, body = cards.read(path)
        self.assertIn("compiled for test_video", body)
        self.assertIn("red fox", body)
        code, out = self.run_cli(cards.cli_card_compile, path=str(path), model="nope",
                                 provider=None, project=str(proj))
        self.assertEqual(code, 2)


if __name__ == "__main__":
    unittest.main()
