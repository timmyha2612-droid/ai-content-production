"""Tests for the depth / natural-finish compile fixes: symmetry vs asymmetry, focus-aware blur guard, finish
guard order, grain clash, true-to-life finish, depth warning by finish, priorities, placement label, repeated
wording and vocab terms that --from-text can match. Uses the shipped rule files where it matters.
"""

import json
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shotcraft import cards, compiler  # noqa: E402

PLUGIN_RULES = HERE.parent.parent / "rules"

PROFILE = {"id": "test_video", "kind": "video", "durations": [4, 6, 8], "resolutions": ["1080p"],
           "aspects": ["9:16"], "start_frame": True, "audio": False, "negative_prompt": False,
           "max_prompt_words": 400}


def load(name):
    with open(PLUGIN_RULES / (name + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


TAX, NEG, RW, PRESETS = load("taxonomy"), load("negatives"), load("positive_rewrites"), load("presets")
RULES = {"taxonomy": TAX, "negatives": NEG, "positive_rewrites": RW, "presets": PRESETS}


def new(use_case="social-vertical", **layers):
    meta = cards.new_card("S010", use_case=use_case, presets=PRESETS, taxonomy=TAX, negatives=NEG)
    meta["layers"]["subject"]["subject"] = "a woman in a yellow raincoat"
    meta["layers"]["subject"]["action"] = "sips coffee"
    for key, val in layers.items():
        layer, field = key.split("__")
        meta["layers"][layer][field] = val
    return meta


class SymmetryTest(unittest.TestCase):
    def test_natural_default_has_no_asymmetry(self):
        for v in TAX["layers"]["light_look"]["fields"]["finish"]["defaults"].values():
            self.assertNotIn("asymmetr", v.lower())

    def test_symmetric_composition_drops_asymmetry_and_guard(self):
        meta = new(camera__composition="perfectly symmetrical one-point perspective",
                   light_look__finish="lived-in detail, natural asymmetry, real-lens character")
        meta["avoid"] = ["perfect symmetry", "blurry"]
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertNotIn("asymmetr", out["prompt"].lower())
        self.assertIn("lived-in detail, real-lens character", out["prompt"].lower())
        self.assertTrue(any("symmetry" in w and "finish" in w for w in out["warnings"]), out["warnings"])
        self.assertTrue(any("'perfect symmetry'" in w for w in out["warnings"]), out["warnings"])
        self.assertNotIn("perfect symmetry", out["unguarded"])

    def test_centre_punch_counts_but_asymmetric_does_not(self):
        for comp in ("centre-punch framing", "subject centred", "centered frame"):
            self.assertTrue(compiler.SYMMETRY_RE.search(comp), comp)
        for comp in ("asymmetric balance", "off-centre on the left third", "off-centred subject"):
            self.assertFalse(compiler.SYMMETRY_RE.search(comp), comp)
        meta = new(camera__composition="asymmetric balance", light_look__finish="natural asymmetry")
        meta["avoid"] = ["perfect symmetry"]
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertIn("natural asymmetry", out["prompt"].lower())
        self.assertIn("slightly asymmetric composition", out["prompt"])


class BlurryGuardTest(unittest.TestCase):
    def test_shallow_variant_for_natural_preset(self):
        meta = new()
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertIn(RW["blurry (shallow focus)"], out["prompt"].lower())
        self.assertNotIn("tack-sharp", out["prompt"])

    def test_shallow_variant_from_dof_on_clean_preset(self):
        meta = new("product-shot", camera__dof="shallow depth of field")
        meta["avoid"] = ["blurry"]
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertIn("sharp focus on the subject", out["prompt"].lower())
        meta["layers"]["camera"]["dof"] = ""
        meta["layers"]["world"]["foreground"] = "out-of-focus cup rim"
        self.assertIn("sharp focus on the subject", compiler.compile(meta, PROFILE, RULES)["prompt"].lower())

    def test_plain_rewrite_when_nothing_is_soft(self):
        meta = new("product-shot")
        meta["avoid"] = ["blurry"]
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertIn("tack-sharp focus", out["prompt"].lower())


class GuardOrderTest(unittest.TestCase):
    def test_finish_guard_inside_kept_guards(self):
        for uc in ("social-vertical", "real-estate"):
            meta = new(uc)
            self.assertIn("cgi look", meta["avoid"][:compiler.MIN_GUARDS], (uc, meta["avoid"]))

    def test_trim_keeps_cgi_guard_with_real_taxonomy(self):
        meta = new(world__environment="a narrow street cafe at night",
                   world__background_far="city towers fading into rain haze",
                   world__background_near="the cafe window with a chalkboard menu",
                   world__foreground="rain running down the glass",
                   world__parallax="the far towers barely move while the passing cars streak",
                   subject__placement="seated at a window table, left third",
                   subject__interaction="neon spill on her cheek, rain beading on her hood",
                   camera__shot_size="medium close-up", camera__movement="slow dolly in",
                   camera__lens="50mm", light_look__setup="neon practicals and soft window light",
                   light_look__mood="quiet and melancholic", light_look__palette_grade="teal and amber",
                   light_look__texture="fine film grain", light_look__quality="soft diffused light",
                   light_look__direction="side light from the window", light_look__color_temp="mixed warm and cool",
                   world__time_of_day="late night", world__atmosphere="light rain and mist",
                   world__weather_season="wet autumn", subject__wardrobe_props="a paper cup and a wet umbrella",
                   camera__angle="eye level", camera__composition="rule of thirds with layered depth")
        meta["settings"].update({"aspect": "9:16", "resolution": "1080p", "duration_s": 6, "audio": False})
        out = compiler.compile(meta, dict(PROFILE, max_prompt_words=120), RULES)
        self.assertLessEqual(out["word_count"], 120)
        self.assertIn(RW["cgi look"], out["prompt"])
        dropped = [d["field"] for d in out["dropped_fields"]]
        self.assertIn("light_look.finish", dropped)
        # user-written depth (parallax on a moving-camera video) outlasts the generic finish default
        self.assertLess(dropped.index("light_look.finish"),
                        dropped.index("world.parallax") if "world.parallax" in dropped else len(dropped))
        for kept in ("world.foreground", "world.background_near", "subject.placement", "subject.interaction"):
            self.assertNotIn(kept, dropped)


class GrainTest(unittest.TestCase):
    def test_stock_name_and_substring_guards(self):
        meta = new(light_look__texture="Kodak Portra 400")
        meta["avoid"] = ["digital noise", "film grain", "blurry"]
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertNotIn("noise-free", out["prompt"])
        w = " ".join(out["warnings"])
        self.assertIn("'digital noise'", w)
        self.assertIn("'film grain'", w)

    def test_texture_vocab_meaning_grain(self):
        words = compiler._grain_words(TAX)
        self.assertIn("heavy grain", words)
        self.assertNotIn("clean digital", words)

    def test_negated_grain_keeps_guard(self):
        for look in ("clean digital, no grain", "grain-free", "shot without grain"):
            meta = new(light_look__texture=look)
            meta["avoid"] = ["noise"]
            out = compiler.compile(meta, PROFILE, RULES)
            self.assertIn("noise-free", out["prompt"], look)
            self.assertFalse(any("grain" in w for w in out["warnings"]), (look, out["warnings"]))


class TrueToLifeTest(unittest.TestCase):
    def test_real_estate_preset(self):
        self.assertEqual(PRESETS["presets"]["real-estate"]["finish"], "true_to_life")
        meta = new("real-estate")
        self.assertEqual(meta["layers"]["light_look"]["finish"],
                         TAX["layers"]["light_look"]["fields"]["finish"]["defaults"]["true_to_life"])
        self.assertIn("cgi look", meta["avoid"])
        self.assertIn("flat even lighting", meta["avoid"])
        self.assertNotIn("too perfect", meta["avoid"])
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertIn("motivated light that falls off naturally", out["prompt"])

    def test_legacy_single_default(self):
        tax = json.loads(json.dumps(TAX))
        fdef = tax["layers"]["light_look"]["fields"]["finish"]
        del fdef["defaults"]
        fdef["default"] = "old default text"
        meta = cards.new_card("S010", use_case="social-vertical", presets=PRESETS, taxonomy=tax, negatives=NEG)
        self.assertEqual(meta["layers"]["light_look"]["finish"], "old default text")
        meta = cards.new_card("S010", use_case="icon-ui", presets=PRESETS, taxonomy=tax, negatives=NEG)
        self.assertEqual(meta["layers"]["light_look"]["finish"], "")

    def test_legacy_comma_guard_still_rewrites(self):
        meta = new()
        meta["avoid"] = ["flat, even lighting"]
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertIn("motivated light that falls off naturally", out["prompt"].lower())


class DepthWarningTest(unittest.TestCase):
    def test_only_for_natural_looks(self):
        meta = new("product-shot", world__environment="a marble kitchen counter")
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertFalse(any("No depth planes" in w for w in out["warnings"]), out["warnings"])
        for uc in ("social-vertical", "real-estate"):
            meta = new(uc, world__environment="a marble kitchen counter")
            out = compiler.compile(meta, PROFILE, RULES)
            self.assertTrue(any("No depth planes" in w for w in out["warnings"]), uc)


class PriorityTest(unittest.TestCase):
    def test_finish_below_depth_fields_and_in_sync(self):
        fields = {(l, f): fd for l, ld in TAX["layers"].items() for f, fd in (ld.get("fields") or {}).items()}
        fin = fields[("light_look", "finish")]["priority"]
        for k in (("world", "parallax"), ("world", "background_far"), ("world", "background_near"),
                  ("world", "foreground"), ("subject", "placement"), ("subject", "interaction")):
            self.assertLess(fin, fields[k]["priority"], k)
        for (l, f), fd in fields.items():
            key = "{}.{}".format(l, f)
            if key in compiler.DEFAULT_PRIORITY:
                self.assertEqual(compiler.DEFAULT_PRIORITY[key], fd["priority"], key)


class PlacementLabelTest(unittest.TestCase):
    def test_no_midground_label_when_plane_named(self):
        for v in ("in the foreground, close to lens", "against the background wall", "close to the lens"):
            self.assertEqual(compiler._fragment("subject.placement", v), v)
        self.assertEqual(compiler._fragment("subject.placement", "left third"), "midground: left third")


class RepeatedWordingTest(unittest.TestCase):
    def test_guard_skipped_when_fields_say_it(self):
        meta = new()
        meta["avoid"] = ["too perfect", "cgi look"]
        out = compiler.compile(meta, PROFILE, RULES)
        self.assertEqual(out["prompt"].lower().count("real-world imperfection"), 1)
        self.assertNotIn("too perfect", out["unguarded"])

    def test_contained_normalises(self):
        self.assertTrue(compiler._contained("Subtle real-world imperfections", "a subtle real-world imperfection: x"))
        self.assertFalse(compiler._contained("clean unmarked image", "a clean image"))


class VocabTermsTest(unittest.TestCase):
    def test_no_vocab_term_has_comma_or_semicolon(self):
        bad = []
        for lname, ldef in TAX["layers"].items():
            for fname, fdef in (ldef.get("fields") or {}).items():
                for v in fdef.get("vocab") or []:
                    term = v.get("term") if isinstance(v, dict) else v
                    if isinstance(term, str) and re.search(r"[,;]", term):
                        bad.append("{}.{}: {}".format(lname, fname, term))
        self.assertEqual(bad, [])

    def test_from_text_matches_reworded_terms(self):
        fills, _ = cards.extract_from_text("midground on the left third, slightly uneven motivated light", TAX)
        self.assertEqual(fills["subject"]["placement"], "midground on the left third")
        self.assertEqual(fills["light_look"]["finish"], "slightly uneven motivated light")


if __name__ == "__main__":
    unittest.main()
