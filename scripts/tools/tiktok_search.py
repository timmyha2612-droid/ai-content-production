#!/usr/bin/env python3
"""Free TikTok discovery through the open-source TikTok-Api (https://github.com/davidteather/TikTok-Api).

Optional, and only on the user's own computer: it drives a real browser and TikTok blocks most cloud and data
centre addresses. It is unofficial and breaks when TikTok changes; when it fails, fall back to yt-dlp, the
Creative Center in the browser, or a paid search with the user's yes.

Setup, once:  pip install TikTokApi && python -m playwright install chromium
Token:        an ms_token cookie from tiktok.com in the user's own browser, passed as --ms-token or the
              ms_token environment variable (a fresh one works best).

Writes one JSON object per video (TikTok-Api's video dict), ready for:
    sc.py discover collect <out>.jsonl --source tiktok-api

    python3 tiktok_search.py hashtag stopmotion --count 40 --out raw/tiktok-stopmotion.jsonl
    python3 tiktok_search.py user somecreator --count 30 --out raw/tiktok-somecreator.jsonl
    python3 tiktok_search.py trending --count 30 --out raw/tiktok-trending.jsonl
"""
import argparse
import asyncio
import json
import os
import sys


async def run(a):
    try:
        from TikTokApi import TikTokApi
    except ImportError:
        sys.exit("TikTok-Api isn't installed: pip install TikTokApi && python -m playwright install chromium")
    token = a.ms_token or os.environ.get("ms_token")
    rows = 0
    with open(a.out, "a", encoding="utf-8") as out:
        async with TikTokApi() as api:
            await api.create_sessions(ms_tokens=[token] if token else None, num_sessions=1, sleep_after=3,
                                      browser=os.environ.get("TIKTOK_BROWSER", "chromium"), headless=not a.show)
            if a.mode == "hashtag":
                videos = api.hashtag(name=a.query.lstrip("#")).videos(count=a.count)
            elif a.mode == "user":
                videos = api.user(a.query.lstrip("@")).videos(count=a.count)
            else:
                videos = api.trending.videos(count=a.count)
            async for v in videos:
                out.write(json.dumps(v.as_dict, ensure_ascii=False) + "\n")
                rows += 1
    print("%d videos written to %s" % (rows, a.out))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("mode", choices=["hashtag", "user", "trending"])
    p.add_argument("query", nargs="?", default="", help="the hashtag or the username (not for trending)")
    p.add_argument("--count", type=int, default=30)
    p.add_argument("--out", required=True, help="a .jsonl file (appended to)")
    p.add_argument("--ms-token", dest="ms_token")
    p.add_argument("--show", action="store_true", help="show the browser window")
    a = p.parse_args(argv)
    if a.mode != "trending" and not a.query:
        p.error("give the hashtag or the username")
    asyncio.run(run(a))


if __name__ == "__main__":
    main()
