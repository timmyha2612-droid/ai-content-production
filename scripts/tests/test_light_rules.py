"""Tests for the lighting and composition rule additions: rules/light_setups.json, the flat_light guards the
compiler adds on low-key setups (negatives.json applies_when), the new taxonomy vocab, and that the touched rule
files still round-trip with json.dumps(indent=2).
"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from shotcraft import cards, compiler  # noqa: E402

PLUGIN_RULES = HERE.parent.parent / "rules"


def load(name):
    with open(PLUGIN_RULES / (name + ".json"), encoding="utf-8") as fh:
        return json.load(fh)


TAX, NEG, RW, PRESETS = load("taxonomy"), load("negatives"), load("positive_rewrites"), load("presets")
RULES = {"taxonomy": TAX, "negatives": NEG, "positive_rewrites": RW, "presets": PRESETS}
FLAT = NEG["by_category"]["flat_light"]
ADD = NEG["applies_when"]["flat_light"]["add"]

NEG_PROFILE = {"id": "test_neg", "kind": "image", "resolutions": ["1080p"], "aspects": ["9:16"],
               "negative_prompt": True, "max_prompt_words": 400}
POS_PROFILE = dict(NEG_PROFILE, id="test_pos", negative_prompt=False)


def card(avoid=None, **layers):
    meta = cards.new_card("S010", use_case="social-vertical", presets=PRESETS, taxonomy=TAX, negatives=NEG)
    meta["kind"] = "image"
    meta["layers"]["subject"]["subject"] = "a man at a kitchen table"
    for key, val in layers.items():
        layer, field = key.split("__")
        meta["layers"][layer][field] = val
    if avoid is not None:
        meta["avoid"] = avoid
    return meta


def negatives_of(meta, profile=NEG_PROFILE):
    out = compiler.compile(meta, profile, RULES)
    return [a.strip() for a in (out["negative_prompt"] or "").split(",") if a.strip()], out


class LightSetupsTest(unittest.TestCase):
    KEYS = ("intent", "setup", "quality", "direction", "color_temp", "practicals", "finish", "stays_dark",
            "do_not_use_when", "board_url")

    def test_loads_with_required_keys(self):
        doc = load("light_setups")
        self.assertTrue(doc.get("version") and doc.get("about"))
        setups = doc["setups"]
        self.assertEqual(len(setups), 16)
        self.assertEqual(len({s["id"] for s in setups}), 16)
        for s in setups:
            for k in self.KEYS:
                self.assertIn(k, s, s.get("id"))
                self.assertTrue(s[k], "{}: {} is empty".format(s["id"], k))
            self.assertIsInstance(s["intent"], list)
            self.assertIsInstance(s["do_not_use_when"], list)
            self.assertTrue(s["board_url"].startswith("https://www.cosmos.so/"), s["id"])

    def test_low_key_flag_matches_the_compiler_trigger(self):
        for s in load("light_setups")["setups"]:
            meta = card(avoid=[], light_look__setup=s["setup"], light_look__quality=s["quality"])
            added = compiler._conditional_guards(meta, NEG, [])
            self.assertEqual(bool(added), s["low_key"], s["id"])


class FlatLightGuardTest(unittest.TestCase):
    def test_low_key_setup_adds_flat_light_guards(self):
        for setup in ("low key", "Rembrandt lighting", "split lighting", "practical lighting", "candlelight",
                      "top light pendant pool", "chiaroscuro", "neon lighting + motivated lighting"):
            neg, _ = negatives_of(card(avoid=["blurry", "watermark"], light_look__setup=setup))
            for t in FLAT[:ADD]:
                self.assertIn(t, neg, setup)
            self.assertNotIn(FLAT[ADD], neg, setup)
            # appended after the card's own guards, so those stay the protected first MIN_GUARDS
            self.assertEqual(neg[:2], ["blurry", "watermark"], setup)

    def test_quality_can_trigger(self):
        neg, _ = negatives_of(card(avoid=[], light_look__setup="motivated lighting",
                                   light_look__quality="chiaroscuro, fast falloff"))
        self.assertIn(FLAT[0], neg)

    def test_high_key_and_overcast_add_nothing(self):
        for layers in ({"light_look__setup": "high key"},
                       {"light_look__setup": "overcast softbox sky"},
                       {"light_look__setup": "three-point lighting"},
                       {"light_look__setup": "practical lighting", "world__weather_season": "overcast"},
                       {"light_look__setup": "low key", "light_look__quality": "high-key soft wrap"}):
            neg, _ = negatives_of(card(avoid=["blurry"], **layers))
            self.assertFalse(set(FLAT) & set(neg), layers)

    def test_no_duplicates_when_already_listed(self):
        neg, _ = negatives_of(card(avoid=["softbox", "blurry"], light_look__setup="low key"))
        self.assertEqual(neg.count("softbox"), 1)
        self.assertEqual(neg[:2], ["softbox", "blurry"])

    def test_rewritten_into_prompt_without_negative_field(self):
        meta = card(avoid=["blurry"], light_look__setup="split lighting")
        out = compiler.compile(meta, POS_PROFILE, RULES)
        self.assertIn(RW[FLAT[0]], out["prompt"])
        for t in FLAT[:ADD]:
            self.assertNotIn(t, out["unguarded"])

    def test_trimming_keeps_the_cards_own_guards(self):
        meta = card(avoid=["blurry", "watermark"], light_look__setup="low key",
                    light_look__quality="hard light, fast falloff")
        full = compiler.compile(meta, POS_PROFILE, RULES)
        tight = dict(POS_PROFILE, max_prompt_words=max(10, full["word_count"] - 12))
        out = compiler.compile(meta, tight, RULES)
        self.assertNotIn("blurry", out["unguarded"])
        self.assertNotIn("watermark", out["unguarded"])
        self.assertTrue(set(FLAT[:ADD]) & set(out["unguarded"]), out["unguarded"])

    def test_auto_guards_trim_before_practicals_and_texture(self):
        # A low-key card with a real practical at a 120-word cap: the generic flat_light rewrites go first,
        # the practical that motivates the light stays.
        meta = card(avoid=["blurry", "watermark"], light_look__setup="Rembrandt lighting",
                    light_look__quality="hard light, fast falloff",
                    light_look__practicals="oil lamp on the table, warm 1800K",
                    light_look__texture="fine 35mm grain")
        meta["layers"]["subject"]["action"] = ("leans over the table and turns the page of an old ledger slowly, "
                                               "then looks up toward the dark doorway")
        meta["layers"]["world"]["environment"] = ("a cramped farmhouse kitchen at night with a scrubbed pine "
                                                  "table, copper pans on hooks and a stone floor")
        meta["layers"]["world"]["atmosphere"] = "thin woodsmoke hanging under the low beams"
        meta["layers"]["camera"]["shot_size"] = "medium close-up"
        meta["layers"]["camera"]["lens"] = "50mm"
        meta["layers"]["world"]["background_near"] = "a dresser of blue and white plates fading into shadow"
        meta["layers"]["world"]["foreground"] = "the soft dark edge of a chair back"
        meta["layers"]["subject"]["wardrobe_props"] = "a worn wool cardigan, reading glasses on a cord"
        meta["layers"]["light_look"]["direction"] = "key from frame left, above eye level"
        full = compiler.compile(meta, POS_PROFILE, RULES)
        self.assertGreater(full["word_count"], 120)
        out = compiler.compile(meta, dict(POS_PROFILE, max_prompt_words=120), RULES)
        dropped = {d["field"] for d in out.get("dropped") or []}
        self.assertNotIn("light_look.practicals", dropped)
        self.assertIn("oil lamp on the table", out["prompt"])
        self.assertTrue(set(FLAT[:ADD]) & set(out["unguarded"]), out["unguarded"])
        self.assertNotIn("blurry", out["unguarded"])

    def test_flat_light_first_terms_are_distinct(self):
        self.assertEqual(FLAT[:ADD], ["flat lighting", "lifted shadows", "rim light on both sides"])
        self.assertEqual(NEG["applies_when"]["flat_light"]["priority"], 5)
        self.assertLess(NEG["applies_when"]["flat_light"]["priority"],
                        TAX["layers"]["light_look"]["fields"]["texture"]["priority"])

    def test_every_flat_light_term_has_a_rewrite(self):
        for t in FLAT:
            self.assertIn(t, RW)
        self.assertEqual(RW["lifted shadows"], "deep shadows that fall to black")


class VocabAdditionsTest(unittest.TestCase):
    def terms(self, layer, field):
        return {v["term"].lower() for v in TAX["layers"][layer]["fields"][field]["vocab"]}

    def test_new_terms_present(self):
        want = {
            ("camera", "composition"): ["one-point perspective", "pool of light", "foreground blocker"],
            ("world", "background_far"): ["black void", "pale far wall of haze"],
            ("world", "background_near"): ["wall catching venetian-blind bars"],
            ("world", "foreground"): ["soft out-of-focus string lights at the edge", "solid black ground band"],
            ("world", "parallax"): ["threat grows from background toward the lens"],
            ("subject", "placement"): ["exactly at the vanishing point"],
            ("subject", "interaction"): ["blind bars bending across the face"],
            ("light_look", "setup"): ["paramount lighting", "candlelight", "mixed night street light"],
            ("light_look", "quality"): ["shadows go to black", "veiling flare"],
            ("light_look", "direction"): ["rim from behind left", "key on far side (short)"],
            ("light_look", "color_temp"): ["oil lamp 1800k", "blue hour sky"],
            ("light_look", "practicals"): ["bare bulb", "venetian blinds (as source shape)"],
            ("light_look", "finish"): ["crushed blacks with no milky shadows", "gentle flame flicker"],
            ("light_look", "palette_grade"): ["navy shadows with detail"],
        }
        for (layer, field), terms in want.items():
            have = self.terms(layer, field)
            for t in terms:
                self.assertIn(t.lower(), have, "{}.{}".format(layer, field))

    def test_replaced_and_changed_glosses(self):
        self.assertNotIn("bokeh from string lights", self.terms("world", "foreground"))
        vocab = {v["term"]: v["means"] for v in TAX["layers"]["light_look"]["fields"]["setup"]["vocab"]}
        self.assertNotIn("magenta and cyan", vocab["neon lighting"])
        comp = {v["term"]: v["means"] for v in TAX["layers"]["camera"]["fields"]["composition"]["vocab"]}
        self.assertIn("never as decoration", comp["Dutch tilt"])
        self.assertIn("side", TAX["layers"]["light_look"]["fields"]["direction"]["help"])

    def test_no_vocab_term_is_a_banned_trigger_word(self):
        banned = {"8k", "hyperdetailed", "ultra detailed", "hyperrealistic", "epic", "cinematic lighting",
                  "beautiful lighting", "well lit", "bokeh background", "flawless", "perfect skin", "hdr"}
        for lname, ldef in TAX["layers"].items():
            for fname, fdef in ldef["fields"].items():
                for v in fdef.get("vocab") or []:
                    self.assertNotIn(v["term"].lower(), banned, "{}.{}".format(lname, fname))
        self.assertIn("awe at vast scale", self.terms("light_look", "mood"))

    def test_no_duplicate_terms(self):
        for lname, ldef in TAX["layers"].items():
            for fname, fdef in ldef["fields"].items():
                terms = [v["term"].lower() for v in fdef.get("vocab") or []]
                self.assertEqual(len(terms), len(set(terms)), "{}.{}".format(lname, fname))


class RoundTripTest(unittest.TestCase):
    def test_rule_files_round_trip(self):
        for name in ("taxonomy", "negatives", "positive_rewrites", "light_setups"):
            raw = (PLUGIN_RULES / (name + ".json")).read_text(encoding="utf-8")
            self.assertEqual(json.dumps(json.loads(raw), indent=2, ensure_ascii=False) + "\n", raw, name)


if __name__ == "__main__":
    unittest.main()
