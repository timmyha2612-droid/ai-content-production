"""Storyboard tests: board.json validation, references and rights, the Higgsfield inputs plan, the local server."""
import http.client
import json
import os
import shutil
import sys
import tempfile
import threading
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from shotcraft import Refused, ShotcraftError  # noqa: E402
from shotcraft import board, board_server, cards, jsonio, manifest, project  # noqa: E402

PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
       b"\x89\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-board-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home")})
        self.env.start()
        self.proj = project.init_project("Bakery Reel", "full", use_case="social-vertical",
                                         root=os.path.join(self.tmp, "projects"))
        data = json.loads(json.dumps(board.BOARD_TEMPLATE))
        data["shots"].append({"n": 2, "card": None, "time": "3.0-5.0", "dur": 2.0, "world": "dawn",
                              "name": "Edit only", "picture": "Cut from shot 1."})
        jsonio.write_json(board.board_file(self.proj), data)

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write_card(self, sid="S010", inputs=None):
        meta = {"id": sid, "kind": "video", "use_case": "social-vertical", "tier_plan": ["draft", "final"],
                "model": {"draft": "seedance_2_0", "final": "seedance_2_5"},
                "settings": {"aspect": "9:16", "resolution": "1080p", "duration_s": 5, "variants": 1,
                             "audio": False},
                "inputs": inputs or [], "status": "draft",
                "layers": {"subject": {"subject": "a baker in her 40s", "action": "dusts flour off her hands"},
                           "camera": {"shot_size": "medium shot", "movement": "locked-off"}}}
        path = os.path.join(self.proj, "05_prompts", sid + ".md")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(cards.dump(meta, ""))
        return path


class TestBoardData(Base):
    def test_template_is_valid(self):
        self.assertEqual(board.validate(board.load_board(self.proj)), [])

    def test_validate_catches_problems(self):
        errs = board.validate({"title": "", "shots": [{"n": 1, "dur": 0, "card": "shot1", "world": "nope"},
                                                      {"n": 1}], "worlds": [{"id": "dawn"}]})
        text = " ".join(errs)
        for bit in ("title is missing", "dur must be", "card 'shot1'", "world 'nope'", "shot 1 appears twice"):
            self.assertIn(bit, text)

    def test_missing_board_says_how_to_start(self):
        os.remove(board.board_file(self.proj))
        with self.assertRaises(ShotcraftError) as cm:
            board.load_board(self.proj)
        self.assertIn("sc.py board init", str(cm.exception))

    def test_attribute_mapping(self):
        self.assertEqual(board.input_role("Frame"), "start_frame")
        self.assertEqual(board.input_role("character"), "character")
        self.assertEqual(board.input_role("Light and texture"), "style")
        self.assertIsNone(board.input_role("Transition"))
        self.assertIsNone(board.input_role("Keep out"))
        self.assertEqual(board.asset_role("Wardrobe"), "prop")
        self.assertEqual(board.asset_role("Palette"), "moodboard")
        self.assertEqual(board.asset_role("Transition"), "reference")


class TestRefs(Base):
    def test_new_reference_is_reference_only_and_filed_in_inputs(self):
        a = board.add_ref(self.proj, PNG, "my photo.png", 1, "Character")
        self.assertEqual(a["rights"], "reference-only")
        self.assertEqual(a["role"], "character")
        self.assertEqual(a["shot"], "S010")
        self.assertTrue(a["path"].startswith("00_inputs/board/"))
        self.assertTrue(os.path.isfile(os.path.join(self.proj, a["path"])))
        self.assertEqual(a["board"], {"shot": 1, "attr": "Character", "name": "my photo.png", "label": "Character1"})

    def test_frame_still_is_generated(self):
        self.assertEqual(board.add_ref(self.proj, PNG, "still.png", 1, "Frame")["rights"], "generated")

    def test_refuses_non_images_and_bad_input(self):
        for args in ((PNG, "x.svg", 1, "Mood"), (PNG, "x.exe", 1, "Mood"), (b"", "x.png", 1, "Mood"),
                     (PNG, "x.png", "one", "Mood"), (PNG, "x.png", -1, "Mood"), (PNG, "x.png", 1, "")):
            with self.assertRaises(Refused):
                board.add_ref(self.proj, *args)

    def test_filename_cannot_escape_the_folder(self):
        a = board.add_ref(self.proj, PNG, "../../../etc/passwd.png", 1, "Mood")
        self.assertTrue(a["path"].startswith("00_inputs/board/"))
        self.assertNotIn("..", a["path"])

    def test_rights_change_is_recorded(self):
        a = board.add_ref(self.proj, PNG, "p.png", 1, "Character")
        board.set_rights(self.proj, a["id"], "owned")
        got = manifest.find_asset(self.proj, a["id"])
        self.assertEqual(got["rights"], "owned")
        self.assertEqual(got["rights_history"][-1]["to"], "owned")
        with self.assertRaises(Refused):
            board.set_rights(self.proj, a["id"], "mine")

    def test_remove_deletes_file_and_entry(self):
        a = board.add_ref(self.proj, PNG, "p.png", 1, "Mood")
        full = os.path.join(self.proj, a["path"])
        board.remove_ref(self.proj, a["id"])
        self.assertFalse(os.path.exists(full))
        self.assertIsNone(manifest.find_asset(self.proj, a["id"]))

    def test_remove_refuses_an_asset_a_card_uses(self):
        a = board.add_ref(self.proj, PNG, "p.png", 1, "Character")
        self.write_card(inputs=[{"asset": a["id"], "as": "character"}])
        with self.assertRaises(Refused):
            board.remove_ref(self.proj, a["id"])

    def test_only_board_assets_can_be_changed(self):
        src = os.path.join(self.proj, "00_inputs", "own.png")
        with open(src, "wb") as fh:
            fh.write(PNG)
        a = manifest.add_asset(self.proj, src, "owned", "input")
        with self.assertRaises(ShotcraftError):
            board.remove_ref(self.proj, a["id"])
        with self.assertRaises(ShotcraftError):
            board.set_rights(self.proj, a["id"], "licensed")


class TestAddFile(Base):
    def test_add_file_with_label_and_rights(self):
        src = os.path.join(self.tmp, "render.png")
        with open(src, "wb") as fh:
            fh.write(PNG)
        with self.assertRaises(Refused):
            board.add_file(self.proj, src, 1, "Environment", rights="owned")  # no words
        a = board.add_file(self.proj, src, 1, "Environment", label="BakerySet", rights="owned",
                           user_said="these are my Blender renders")
        self.assertEqual((a["rights"], a["board"]["label"]), ("owned", "BakerySet"))
        self.assertTrue(a["path"].startswith("00_inputs/board/"))
        with self.assertRaises(ShotcraftError):
            board.add_file(self.proj, os.path.join(self.tmp, "missing.png"), 1, "Mood")


class TestPlanAndHiggsfield(Base):
    def test_reference_only_is_never_proposed(self):
        board.add_ref(self.proj, PNG, "p.png", 1, "Character")
        self.assertEqual(board.inputs_plan(self.proj), [])

    def test_plan_maps_attributes_to_card_inputs(self):
        c = board.add_ref(self.proj, PNG, "face.png", 1, "Character")
        board.set_rights(self.proj, c["id"], "owned")
        f = board.add_ref(self.proj, PNG, "still.png", 1, "Frame")
        n = board.add_ref(self.proj, PNG, "note.png", 1, "Transition")
        board.set_rights(self.proj, n["id"], "owned")
        plan = {(p["asset"], p["as"], p["card"]) for p in board.inputs_plan(self.proj)}
        self.assertEqual(plan, {(c["id"], "character", "S010"), (f["id"], "start_frame", "S010")})
        self.assertIn("--user-said", board.inputs_plan(self.proj)[0]["command"])

    def test_look_book_style_applies_to_every_generated_shot_but_never_as_start_frame(self):
        s = board.add_ref(self.proj, PNG, "grade.png", 0, "Palette")
        board.set_rights(self.proj, s["id"], "licensed")
        fr = board.add_ref(self.proj, PNG, "f.png", 0, "Frame")
        plan = board.inputs_plan(self.proj)
        self.assertEqual([(p["card"], p["as"]) for p in plan], [("S010", "style")])
        self.assertNotIn(fr["id"], [p["asset"] for p in plan])

    def test_view_reads_card_and_compiles_without_writing(self):
        path = self.write_card()
        with open(path, encoding="utf-8") as fh:
            before = fh.read()
        v = board.view(self.proj)
        h = v["hf"]["1"]
        self.assertEqual(h["models"]["final"]["id"], "seedance_2_5")
        self.assertIn("baker", h["prompt"])
        self.assertLessEqual(h["words"], h["max_words"])
        with open(path, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), before)
        self.assertNotIn("2", v["hf"])  # the edit-only shot has no card

    def test_missing_card_is_reported(self):
        self.assertTrue(board.view(self.proj)["hf"]["1"]["missing"])


class TestLabelsAndMentions(Base):
    def owned(self, name, attr, shot=1):
        a = board.add_ref(self.proj, PNG, name, shot, attr)
        board.set_rights(self.proj, a["id"], "owned")
        return a

    def test_default_labels_are_unique_and_renamable(self):
        a = board.add_ref(self.proj, PNG, "a.png", 1, "Character")
        b = board.add_ref(self.proj, PNG, "b.png", 1, "Character")
        self.assertEqual((a["board"]["label"], b["board"]["label"]), ("Character1", "Character2"))
        self.assertEqual(board.set_label(self.proj, a["id"], "@Baker")["board"]["label"], "Baker")
        with self.assertRaises(Refused):
            board.set_label(self.proj, b["id"], "baker")  # taken, any case
        for bad in ("", "1st", "has space", "x" * 25, "<b>"):
            with self.assertRaises(Refused):
                board.set_label(self.proj, b["id"], bad)

    def test_mentions_become_seedance_pointers_in_slot_order(self):
        style = self.owned("g.png", "Lighting")
        face = self.owned("f.png", "Character")
        board.set_label(self.proj, face["id"], "Baker")
        board.set_label(self.proj, style["id"], "Glow")
        r = board.resolve_mentions(self.proj, "S010", "@Baker kneads dough in @Glow light", "seedance_2_5")
        self.assertEqual(r["prompt"], "@Image1 kneads dough in @Image2 light")
        self.assertEqual([(x["label"], x["as"]) for x in r["slots"]], [("Baker", "character"), ("Glow", "style")])
        self.assertEqual(r["warnings"], [])

    def test_other_models_get_plain_words(self):
        face = self.owned("f.png", "Character")
        board.set_label(self.proj, face["id"], "Baker")
        r = board.resolve_mentions(self.proj, "S010", "@Baker smiles", "kling3_0")
        self.assertEqual(r["prompt"], "Baker smiles")
        self.assertTrue(any("No @ pointer syntax" in w for w in r["warnings"]))

    def test_mention_warnings(self):
        ref_only = board.add_ref(self.proj, PNG, "r.png", 1, "Mood")
        board.set_label(self.proj, ref_only["id"], "Fog")
        sent = self.owned("s.png", "Props")
        r = board.resolve_mentions(self.proj, "S010", "@Fog and @Ghost", "seedance_2_5")
        self.assertEqual(r["prompt"], "Fog and Ghost")
        text = " ".join(r["warnings"])
        self.assertIn("@Fog is reference-only", text)
        self.assertIn("No reference is called @Ghost", text)
        self.assertIn("@%s is sent but the prompt never mentions it" % sent["board"]["label"], text)

    def test_start_frame_takes_no_image_slot(self):
        self.owned("f.png", "Frame")
        self.assertEqual(board.resolve_mentions(self.proj, "S010", "x", "seedance_2_5")["slots"], [])


class TestServer(Base):
    def setUp(self):
        super().setUp()
        self.srv, self.token = board_server.make_server(self.proj, 0)
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def req(self, method, path, body=None, token=True, host=None):
        c = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        h = {"Host": host or "127.0.0.1:%d" % self.port}
        if token:
            h["X-Board-Token"] = self.token
        c.request(method, path, body=body, headers=h)
        r = c.getresponse()
        data = r.read()
        c.close()
        return r.status, data

    def test_needs_token_and_local_host(self):
        self.assertEqual(self.req("GET", "/api/board", token=False)[0], 403)
        self.assertEqual(self.req("GET", "/api/board", host="evil.example")[0], 403)
        self.assertEqual(self.req("GET", "/", token=False)[0], 403)  # the page needs ?t=
        st, body = self.req("GET", "/?t=" + self.token, token=False)
        self.assertEqual(st, 200)
        self.assertIn(self.token.encode(), body)
        self.assertNotIn(b"__BOARD_TOKEN__", body)

    def test_upload_rights_file_and_remove(self):
        st, body = self.req("POST", "/api/refs?shot=1&attr=Character&name=a.png", PNG)
        self.assertEqual(st, 200)
        aid = json.loads(body)["id"]
        st, body = self.req("POST", "/api/refs/%s/rights" % aid, json.dumps({"rights": "owned"}))
        self.assertEqual(json.loads(body)["rights"], "owned")
        view = json.loads(self.req("GET", "/api/board")[1])
        self.assertTrue(view["refs"][0]["send"])
        self.assertEqual(view["plan"][0]["as"], "character")
        st, body = self.req("GET", "/files/%s?t=%s" % (aid, self.token), token=False)
        self.assertEqual((st, body), (200, PNG))
        self.assertEqual(self.req("GET", "/files/%s" % aid, token=False)[0], 403)
        st, body = self.req("POST", "/api/refs/%s/label" % aid, json.dumps({"label": "Baker"}))
        self.assertEqual(json.loads(body)["label"], "Baker")
        self.assertEqual(self.req("POST", "/api/refs/%s/label" % aid, json.dumps({"label": "no way"}))[0], 400)
        self.assertEqual(self.req("DELETE", "/api/refs/" + aid)[0], 200)
        self.assertEqual(self.req("GET", "/files/%s?t=%s" % (aid, self.token), token=False)[0], 404)

    def test_bad_requests(self):
        self.assertEqual(self.req("POST", "/api/refs?shot=1&attr=Mood&name=x.svg", b"<svg/>")[0], 400)
        self.assertEqual(self.req("POST", "/api/refs/A999/rights", json.dumps({"rights": "owned"}))[0], 404)
        self.assertEqual(self.req("GET", "/files/..%2Fproject.json?t=" + self.token, token=False)[0], 404)


if __name__ == "__main__":
    unittest.main()
