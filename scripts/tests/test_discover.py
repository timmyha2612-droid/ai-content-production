"""Social discovery: normalising posts from yt-dlp, Apify and CSV, collecting, ranking, fetching the top and
counting patterns. No network: fetch is mocked."""
import datetime as dt
import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
if SCRIPTS not in sys.path:
    sys.path.insert(0, SCRIPTS)

from shotcraft import Refused, ShotcraftError  # noqa: E402
from shotcraft import discover, jsonio, project  # noqa: E402

TODAY = dt.date(2026, 11, 27)

APIFY_TIKTOK = {  # the shape of Apify's common TikTok scrapers
    "webVideoUrl": "https://www.tiktok.com/@smallcreator/video/111?is_from_webapp=1",
    "authorMeta": {"name": "smallcreator", "fans": 2000}, "playCount": 400000, "diggCount": 52000,
    "commentCount": 900, "shareCount": 3100, "collectCount": 4000, "createTimeISO": "2026-11-20T08:00:00.000Z",
    "videoMeta": {"duration": 18}, "text": "clay to cgi #stopmotion #ai", "hashtags": [{"name": "stopmotion"},
                                                                                      {"name": "ai"}],
    "musicMeta": {"musicName": "original sound"}}
BIG_ACCOUNT = {
    "webVideoUrl": "https://www.tiktok.com/@bigbrand/video/222", "authorMeta": {"name": "bigbrand", "fans": 5000000},
    "playCount": 600000, "diggCount": 9000, "commentCount": 100, "shareCount": 50,
    "createTimeISO": "2026-11-18T08:00:00Z", "videoMeta": {"duration": 30}, "text": "new drop"}
APIFY_INSTAGRAM = {
    "url": "https://www.instagram.com/reel/ABC/", "ownerUsername": "reelmaker", "videoPlayCount": 120000,
    "likesCount": 8000, "commentsCount": 300, "timestamp": "2026-10-01T10:00:00.000Z", "videoDuration": 22.4,
    "caption": "hand drawn vs AI", "hashtags": ["animation", "ai"]}
YTDLP_INFO = {
    "webpage_url": "https://www.youtube.com/shorts/xyz", "extractor_key": "Youtube", "uploader": "editorguy",
    "channel_follower_count": 15000, "view_count": 90000, "like_count": 6000, "comment_count": 250,
    "upload_date": "20261115", "duration": 41, "title": "Editors cut film by hand"}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="sc-disc-")
        self.env = mock.patch.dict(os.environ, {"SHOTCRAFT_HOME": os.path.join(self.tmp, "home")})
        self.env.start()
        self.proj = project.init_project("Reel Research", "full", use_case="social-vertical",
                                         root=os.path.join(self.tmp, "projects"))

    def tearDown(self):
        self.env.stop()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, obj, raw=False):
        p = os.path.join(self.tmp, name)
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(obj if raw else json.dumps(obj))
        return p


class TestNormalize(unittest.TestCase):
    def test_apify_tiktok(self):
        p = discover.normalize(APIFY_TIKTOK, "apify")
        self.assertEqual(p["url"], "https://www.tiktok.com/@smallcreator/video/111")  # tracking query dropped
        self.assertEqual((p["platform"], p["author"], p["followers"], p["views"]), ("tiktok", "smallcreator",
                                                                                 2000, 400000))
        self.assertEqual((p["likes"], p["shares"], p["saves"], p["posted"]), (52000, 3100, 4000, "2026-11-20"))
        self.assertEqual(p["hashtags"], ["stopmotion", "ai"])
        self.assertEqual(p["duration"], 18)

    def test_apify_instagram(self):
        p = discover.normalize(APIFY_INSTAGRAM)
        self.assertEqual((p["platform"], p["author"], p["views"], p["likes"]), ("instagram", "reelmaker", 120000,
                                                                               8000))
        self.assertIsNone(p["followers"])
        self.assertEqual(p["posted"], "2026-10-01")

    def test_ytdlp_info(self):
        p = discover.normalize(YTDLP_INFO)
        self.assertEqual((p["platform"], p["followers"], p["posted"], p["caption"]),
                         ("youtube", 15000, "2026-11-15", "Editors cut film by hand"))

    def test_human_numbers_and_rejects(self):
        p = discover.normalize({"url": "https://tiktok.com/@a/video/1", "views": "1.2M", "likes": "45K",
                                "comments": "1,234", "posted": "1764230400"})
        self.assertEqual((p["views"], p["likes"], p["comments"]), (1.2e6, 45000, 1234))
        self.assertTrue(p["posted"].startswith("2025-"))
        for bad in ({}, {"url": "not a link"}, {"url": "javascript:alert(1)"}, "x", None):
            self.assertIsNone(discover.normalize(bad))


class TestOpenSourceShapes(Base):
    TIKTOKAPI = {"id": "7300", "desc": "clay to skin #stopmotion", "createTime": 1764000000,
                 "author": {"uniqueId": "claykid"}, "authorStats": {"followerCount": 3000},
                 "stats": {"playCount": 250000, "diggCount": 30000, "commentCount": 500, "shareCount": 900,
                           "collectCount": 1200}, "music": {"title": "original sound"},
                 "challenges": [{"title": "stopmotion"}], "video": {"duration": 14}}
    INSTALOADER = {"node": {"shortcode": "Cxyz", "is_video": True, "video_view_count": 80000,
                            "edge_media_preview_like": {"count": 5000}, "edge_media_to_comment": {"count": 120},
                            "taken_at_timestamp": 1763000000, "owner": {"username": "animator"},
                            "edge_media_to_caption": {"edges": [{"node": {"text": "hand drawn #animation"}}]},
                            "video_duration": 19.5}}

    def test_tiktok_api_video(self):
        p = discover.normalize(self.TIKTOKAPI)
        self.assertEqual(p["url"], "https://www.tiktok.com/@claykid/video/7300")
        self.assertEqual((p["followers"], p["views"], p["saves"], p["duration"], p["hashtags"]),
                         (3000, 250000, 1200, 14, ["stopmotion"]))

    def test_instaloader_post_and_compressed_files(self):
        p = discover.normalize(self.INSTALOADER)
        self.assertEqual((p["url"], p["author"], p["views"], p["likes"], p["comments"]),
                         ("https://www.instagram.com/reel/Cxyz/", "animator", 80000, 5000, 120))
        self.assertEqual((p["caption"], p["hashtags"]), ("hand drawn #animation", ["animation"]))
        import lzma
        folder = os.path.join(self.tmp, "instaloader", "animator")
        os.makedirs(folder)
        with lzma.open(os.path.join(folder, "2025-11-13_UTC.json.xz"), "wt", encoding="utf-8") as fh:
            json.dump(self.INSTALOADER, fh)
        r = discover.collect(self.proj, [os.path.join(self.tmp, "instaloader")], "instaloader")
        self.assertEqual((r["added"], r["total"]), (1, 1))

    def test_search_script_explains_a_missing_install(self):
        import subprocess
        script = os.path.join(SCRIPTS, "tools", "tiktok_search.py")
        r = subprocess.run([sys.executable, script, "--help"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0)
        self.assertIn("hashtag", r.stdout)


class TestCollectAndRank(Base):
    def test_collect_merges_sources_and_formats(self):
        a = self.write("apify.json", [APIFY_TIKTOK, BIG_ACCOUNT, {"junk": 1}])
        b = self.write("ig.jsonl", json.dumps(APIFY_INSTAGRAM) + "\n", raw=True)
        c = self.write("saved.csv", "url,author,views,likes,posted\n"
                                    "https://www.tiktok.com/@smallcreator/video/111,smallcreator,410000,,2026-11-20\n",
                       raw=True)
        folder = os.path.join(self.tmp, "infos")
        os.makedirs(folder)
        with open(os.path.join(folder, "v.info.json"), "w") as fh:
            json.dump(YTDLP_INFO, fh)
        r = discover.collect(self.proj, [a, b], "apify")
        self.assertEqual((r["added"], r["skipped"], r["total"]), (3, 1, 3))
        r = discover.collect(self.proj, [c, folder], "links")
        self.assertEqual((r["added"], r["updated"], r["total"]), (1, 1, 4))
        posts = {p["url"]: p for p in jsonio.read_json(os.path.join(self.proj, discover.DISCOVERY, "posts.json"))}
        small = posts["https://www.tiktok.com/@smallcreator/video/111"]
        self.assertEqual((small["views"], small["likes"], small["followers"]), (410000, 52000, 2000))
        with self.assertRaises(ShotcraftError):
            discover.collect(self.proj, [os.path.join(self.tmp, "missing.json")])
        with self.assertRaises(Refused):
            discover.collect(self.proj, [])

    def test_breakout_beats_a_big_accounts_ordinary_post(self):
        discover.collect(self.proj, [self.write("a.json", [APIFY_TIKTOK, BIG_ACCOUNT])])
        top = discover.rank(self.proj, now=TODAY)
        self.assertEqual([p["author"] for p in top], ["smallcreator", "bigbrand"])
        self.assertEqual(top[0]["breakout"], 200.0)
        self.assertTrue(os.path.isfile(os.path.join(self.proj, discover.DISCOVERY, "ranked.md")))

    def test_recency_and_filters(self):
        old = dict(APIFY_TIKTOK, webVideoUrl="https://www.tiktok.com/@smallcreator/video/999",
                   createTimeISO="2025-11-20T00:00:00Z")
        discover.collect(self.proj, [self.write("a.json", [APIFY_TIKTOK, old, APIFY_INSTAGRAM])])
        s_new, _ = discover.score(discover.normalize(APIFY_TIKTOK), TODAY)
        s_old, parts = discover.score(discover.normalize(old), TODAY)
        self.assertGreater(s_new, s_old * 100)
        self.assertEqual(parts["days_old"], 372)
        self.assertEqual(len(discover.rank(self.proj, since_days=90, now=TODAY)), 2)
        self.assertEqual([p["platform"] for p in discover.rank(self.proj, platform="instagram", now=TODAY)],
                         ["instagram"])
        self.assertEqual(discover.score({"url": "x"}, TODAY)[0], 0.0)
        shutil.rmtree(os.path.join(self.proj, discover.DISCOVERY))
        with self.assertRaises(Refused):
            discover.rank(self.proj)


class TestFetchTopAndPatterns(Base):
    def test_fetch_top_uses_reference_download_and_skips_done(self):
        discover.collect(self.proj, [self.write("a.json", [APIFY_TIKTOK, BIG_ACCOUNT, APIFY_INSTAGRAM])])
        discover.rank(self.proj, now=TODAY)
        calls = []

        def fake_fetch(project, url, note=None, cookies_from_browser=None, **kw):
            calls.append((url, note))
            if "instagram" in url:
                raise ShotcraftError("private post")
            return {"assets": [{"id": "A%03d" % (len(calls) + 1)}]}
        with mock.patch("shotcraft.refs.fetch", side_effect=fake_fetch):
            r = discover.fetch_top(self.proj, n=3)
            self.assertEqual((len(r["fetched"]), len(r["failed"])), (2, 1))
            self.assertIn("discovery #1", calls[0][1])
            r2 = discover.fetch_top(self.proj, n=3)  # already-fetched posts are skipped
            self.assertEqual(len(r2["fetched"]), 0)

    def test_patterns_counts_what_repeats(self):
        rows = [{"hook_s": 1.0, "length_s": 18, "shots": 12, "hook_type": "hand enters frame", "sound": "voiceover"},
                {"hook_s": 1.2, "length_s": 24, "shots": 10, "hook_type": "Hand enters frame", "sound": "trending song"},
                {"hook_s": 2.5, "length_s": 50, "avg_shot_s": 4, "hook_type": "question", "sound": "voiceover"},
                {"hook_s": 0.8, "length_s": 15, "shots": 15, "hook_type": "hand enters frame"}]
        jsonio.write_json(os.path.join(self.proj, discover.DISCOVERY, "breakdowns.json"), rows)
        r = discover.patterns(self.proj)
        text = "\n".join(r["lines"])
        self.assertEqual(r["n"], 4)
        self.assertIn("hook under 1.5 s: 3 of 4", text)
        self.assertIn("cuts faster than every 1.5 s: 1 of 4", text)  # 15 s / 15 shots; 18 / 12 is exactly 1.5
        self.assertIn("shots of 1.5 to 3 s: 2 of 4", text)
        self.assertIn("hand enters frame (3 of 4)", text)
        self.assertIn("voiceover (2 of 3)", text)

    def test_patterns_needs_breakdowns(self):
        with self.assertRaises(Refused):
            discover.patterns(self.proj)


if __name__ == "__main__":
    unittest.main()
