"""Per-shot progress: batches after the board, draft -> final -> lock per shot, the gen gate, and the board's
progress, takes and actions (fake provider, no network)."""
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

from shotcraft import Refused  # noqa: E402
from shotcraft import board, board_server, cards, gen, jsonio, project, rules, shots, stages  # noqa: E402

SHOTLIST = """# Shot list

| Shot | Scene | Duration (s) | Purpose |
|---|---|---|---|
| S010 | 1 | 3 | hook |
| S020 | 1 | 3 | build |
| S030 | 2 | 3 | turn |
| S040 | 2 | 3 | end |
"""


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-shots-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home"),
                                                "SHOTCRAFT_PROVIDER": "fake"})
        self.env.start()
        for k in ("CLAUDE_SESSION_ID", "CLAUDE_CODE_SESSION_ID", "SHOTCRAFT_FAKE_STATUS"):
            os.environ.pop(k, None)
        self.proj = project.init_project("Bakery Reel", "full", use_case="social-vertical",
                                         root=os.path.join(self.tmp, "projects"))
        with open(os.path.join(self.proj, "03_script", "shotlist.md"), "w", encoding="utf-8") as fh:
            fh.write(SHOTLIST)
        self.set_stages(open_=("prompts",))
        for sid in ("S010", "S020", "S030", "S040"):
            self.card(sid)
        self.set_stages(done=("intake", "research", "concept", "script", "shotlist", "bible", "prompts", "boards"))

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_stages(self, done=(), open_=()):
        st = stages.load_state(self.proj)
        for s in done:
            st["stages"][s]["status"] = "done"
        for s in open_:
            st["stages"][s]["status"] = "open"
        stages.save_state(self.proj, st)

    def card(self, sid):
        meta = cards.new_card(sid, kind="video", use_case="social-vertical", presets=rules.load("presets"),
                              taxonomy=rules.load("taxonomy"), negatives=rules.load("negatives"))
        meta["layers"]["subject"]["subject"] = "a baker"
        meta["layers"]["subject"]["action"] = "dusts flour off her hands"
        meta["settings"]["duration_s"] = 3
        meta["settings"]["variants"] = 1
        path = os.path.join(self.proj, "05_prompts", sid + ".md")
        cards.write(path, meta, cards.render_body(meta))
        cards.approve(self.proj, path, "card looks right")

    def draft(self, sid):
        return gen.submit(self.proj, sid, "draft", wait=True)["generations"][0]

    def final(self, sid):
        return gen.submit(self.proj, sid, "final", wait=True)["generations"][0]


class TestSelectAndStart(Base):
    def test_select_forms(self):
        self.assertEqual(shots.select(self.proj, all_shots=True), ["S010", "S020", "S030", "S040"])
        self.assertEqual(shots.select(self.proj, ["S020-S040"]), ["S020", "S030", "S040"])
        self.assertEqual(shots.select(self.proj, ["s040-s030"]), ["S030", "S040"])
        self.assertEqual(shots.select(self.proj, ["S010, S030"]), ["S010", "S030"])
        self.assertEqual(shots.select(self.proj, scenes=["2"]), ["S030", "S040"])
        self.assertEqual(shots.select(self.proj, ["S010"], scenes=["2"]), ["S030", "S040", "S010"])
        for bad in (["S090"], ["S010-S090"], ["frog"]):
            with self.assertRaises(Refused):
                shots.select(self.proj, bad)
        with self.assertRaises(Refused):
            shots.select(self.proj, scenes=["9"])
        with self.assertRaises(Refused):
            shots.select(self.proj)

    def test_start_needs_the_board_and_words(self):
        with self.assertRaises(Refused):
            shots.start(self.proj, ["S010"], "")
        st = stages.load_state(self.proj)
        st["stages"]["boards"]["status"] = "open"
        stages.save_state(self.proj, st)
        with self.assertRaises(Refused) as cm:
            shots.start(self.proj, ["S010"], "go on shot one")
        self.assertIn("board", str(cm.exception))

    def test_progress_states(self):
        pr = shots.progress(self.proj)
        self.assertEqual(pr["S010"]["state"], "ready")
        self.assertEqual(pr["S030"]["scene"], "2")
        r = shots.start(self.proj, ["S010", "S020"], "start the first two")
        self.assertEqual(r["started"], ["S010", "S020"])
        self.assertEqual(shots.start(self.proj, ["S010"], "again")["already"], ["S010"])
        self.assertEqual(shots.progress(self.proj)["S010"]["state"], "in_progress")
        self.assertEqual(shots.pause(self.proj, ["S020"], "hold that one"), ["S020"])
        self.assertEqual(shots.progress(self.proj)["S020"]["state"], "paused")


class TestFlow(Base):
    def test_shot_goes_draft_final_lock_while_stages_stay_closed(self):
        with self.assertRaises(Refused) as cm:
            self.draft("S010")
        self.assertIn("shots start", str(cm.exception))
        shots.start(self.proj, ["S010"], "do shot one first")
        d = self.draft("S010")
        self.assertEqual(shots.progress(self.proj)["S010"]["state"], "draft_review")
        gen.approve(self.proj, d["id"], "draft is good")
        self.assertEqual(shots.progress(self.proj)["S010"]["state"], "draft_approved")
        f = self.final("S010")
        self.assertEqual(shots.progress(self.proj)["S010"]["state"], "final_review")
        with self.assertRaises(Refused):
            shots.lock(self.proj, "S010", "lock it")  # final not approved yet
        gen.approve(self.proj, f["id"], "final is perfect")
        self.assertEqual(shots.progress(self.proj)["S010"]["state"], "final_approved")
        rec = shots.lock(self.proj, "S010", "lock it in")
        self.assertEqual(rec["locked_gen"], f["id"])
        self.assertEqual(shots.progress(self.proj)["S010"]["state"], "locked")
        # the other shots are untouched: still gated by the closed drafts stage
        with self.assertRaises(Refused):
            self.draft("S020")
        self.assertEqual(stages.load_state(self.proj)["stages"]["drafts"]["status"], "pending")

    def test_locked_shot_makes_nothing_until_unlocked(self):
        shots.start(self.proj, ["S010"], "go")
        gen.approve(self.proj, self.draft("S010")["id"], "ok")
        gen.approve(self.proj, self.final("S010")["id"], "ok")
        shots.lock(self.proj, "S010", "locked")
        self.set_stages(open_=("drafts",))  # even with the stage open, a lock wins
        with self.assertRaises(Refused) as cm:
            self.draft("S010")
        self.assertIn("locked", str(cm.exception))
        shots.unlock(self.proj, "S010", "one more pass on the light")
        self.assertEqual(shots.progress(self.proj)["S010"]["state"], "final_approved")
        self.draft("S010")

    def test_board_tier_still_follows_the_stage(self):
        shots.start(self.proj, ["S010"], "go")
        ok, why = shots.gen_allowed(self.proj, "board", "S010")
        self.assertFalse(ok)

    def test_shots_json_is_guarded(self):
        ok, why = stages.path_writable(self.proj, ".shotcraft/shots.json")
        self.assertFalse(ok)

    def test_card_of_an_in_progress_shot_stays_editable_and_a_locked_one_does_not(self):
        self.assertFalse(stages.path_writable(self.proj, "05_prompts/S010.md")[0])
        shots.start(self.proj, ["S010"], "go")
        self.assertTrue(stages.path_writable(self.proj, "05_prompts/S010.md")[0])
        self.assertFalse(stages.path_writable(self.proj, "05_prompts/S020.md")[0])
        cards.approve(self.proj, os.path.join(self.proj, "05_prompts", "S010.md"), "new light is right")
        gen.approve(self.proj, self.draft("S010")["id"], "ok")
        gen.approve(self.proj, self.final("S010")["id"], "ok")
        shots.lock(self.proj, "S010", "locked")
        self.assertFalse(stages.path_writable(self.proj, "05_prompts/S010.md")[0])
        with self.assertRaises(Refused):
            cards.approve(self.proj, os.path.join(self.proj, "05_prompts", "S010.md"), "change it")


class TestBoardTakes(Base):
    def setUp(self):
        super().setUp()
        data = json.loads(json.dumps(board.BOARD_TEMPLATE))
        data["shots"] = [{"n": i + 1, "card": sid, "time": "0-3", "dur": 3, "name": sid, "picture": "x"}
                         for i, sid in enumerate(("S010", "S020", "S030", "S040"))]
        jsonio.write_json(board.board_file(self.proj), data)
        self.srv, self.token = board_server.make_server(self.proj, 0)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def post(self, path, obj):
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=5)
        c.request("POST", path, body=json.dumps(obj), headers={"X-Board-Token": self.token,
                                                               "Host": "127.0.0.1"})
        r = c.getresponse()
        data = json.loads(r.read() or b"{}")
        c.close()
        return r.status, data

    def test_board_batch_approve_lock(self):
        st, r = self.post("/api/shots/start", {"scenes": ["1"], "said": "scene one first"})
        self.assertEqual((st, r["started"]), (200, ["S010", "S020"]))
        self.assertEqual(self.post("/api/shots/start", {"all": True, "said": ""})[0], 400)  # no words, no go
        d = self.draft("S010")
        v = board.view(self.proj)
        self.assertEqual(v["progress"]["S010"]["state"], "draft_review")
        self.assertEqual(v["takes"]["S010"][0]["id"], d["id"])
        self.assertTrue(v["takes"]["S010"][0]["files"][0]["url"].startswith("/gen/" + d["id"]))
        self.assertEqual(self.post("/api/gen/%s/decision" % d["id"], {"approve": True, "said": "love it"})[0], 200)
        f = self.final("S010")
        self.post("/api/gen/%s/decision" % f["id"], {"approve": True, "said": "final yes"})
        st, r = self.post("/api/shots/S010/lock", {"said": "lock shot one"})
        self.assertEqual((st, r["locked"]), (200, True))
        self.assertEqual(board.view(self.proj)["progress"]["S010"]["locked_gen"], f["id"])
        c = http.client.HTTPConnection("127.0.0.1", self.srv.server_address[1], timeout=5)
        c.request("GET", "/gen/%s/0?t=%s" % (f["id"], self.token), headers={"Host": "127.0.0.1"})
        r = c.getresponse()
        self.assertEqual((r.status, len(r.read()) > 0), (200, True))
        c.close()

    def test_decision_needs_words(self):
        shots.start(self.proj, ["S010"], "go")
        d = self.draft("S010")
        self.assertEqual(self.post("/api/gen/%s/decision" % d["id"], {"approve": True, "said": " "})[0], 400)


if __name__ == "__main__":
    unittest.main()
