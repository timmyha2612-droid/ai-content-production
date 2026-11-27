---
name: research
description: "Research stage of a shotcraft production: find viral videos on TikTok, Instagram and YouTube Shorts, rank them, download the best as references and count the patterns they share. Free first; a paid scraper only with the user's yes to its price. Triggers: \"find viral videos about\", \"what's working on TikTok for\", \"research the platform\", \"find the pattern\"."
metadata:
  version: "0.1.0"
---

# shotcraft: research (social discovery)

Goal: a short, evidence-based direction note. Not "punchy hooks work", but "7 of the top 10 open with a hand
entering frame inside 1.5 s". You find the posts, rank them fairly, download the strongest as reference-only,
break each one down, and count what repeats.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Everything lands in `01_research/discovery/`.
Open the research stage first (`sc stage start research`).

## 0. Scope, in one question round

Ask with AskUserQuestion (recommended option first) only what the job card doesn't already say:
- Platforms: TikTok, Instagram Reels, YouTube Shorts (default: all three, TikTok first).
- What to search: 3 to 6 keywords or hashtags, plus any accounts to study (competitors, creators they like).
- Region and window: default Australia, last 90 days.
- Their own saved posts: ask them to paste links if they have any. Their saves are the best signal there is.

## 1. Free sources first

Work down this list and stop widening once you have about 30 to 60 posts worth ranking.

1. **The user's links.** `yt-dlp --dump-json --skip-download URL > 01_research/discovery/raw/links.jsonl`
   for each (append), then `sc discover collect 01_research/discovery/raw/links.jsonl --source links`.
2. **TikTok Creative Center** (free, official): `https://ads.tiktok.com/business/creativecenter/` →
   Trends → Hashtags, Songs, Creators and TikTok Videos, filtered by region, industry and 7, 30 or 120 days.
   It's a web app: read it in the user's browser (load the `chrome-browser` skill and use Claude in Chrome)
   rather than WebFetch. Note the top hashtags and songs for the brief, and copy each video's link, creator and
   any shown numbers into `01_research/discovery/raw/creative-center.csv` (columns `url,author,views,likes,
   posted,caption`; leave unknown cells empty). Then `sc discover collect ... --source creative-center`.
   Its Top Ads section is worth a look for ad briefs.
3. **Open-source tools on the user's computer** (free; they need a home internet connection, not a cloud
   workspace, and they're unofficial, so they break when the platforms change):
   - **TikTok-Api** for hashtags, accounts and trending, with full numbers:
     `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/tools/tiktok_search.py" hashtag <tag> --count 40 --out
     01_research/discovery/raw/tiktok-<tag>.jsonl`, then `sc discover collect ... --source tiktok-api`. First time:
     `pip install TikTokApi && python -m playwright install chromium`, and an `ms_token` cookie from tiktok.com
     in the user's browser (ask before reading it).
   - **Instaloader** for Instagram metadata without downloading media: `instaloader --no-pictures --no-videos
     --no-video-thumbnails --no-compress-json --count 30 --dirname-pattern
     01_research/discovery/raw/instaloader/{target} -- <profile>`, then `sc discover collect
     01_research/discovery/raw/instaloader --source instaloader`. Hashtags (`"#tag"`) and most profiles now need
     a sign-in: only with the user's yes, add `--load-cookies chrome`.
4. **yt-dlp searches and profiles** (free):
   - YouTube Shorts: `yt-dlp "ytsearchdate30:<keyword> shorts" --dump-json --skip-download` (newest 30).
   - A public TikTok account: `yt-dlp --dump-json --skip-download --playlist-end 30 https://www.tiktok.com/@<user>`.
   Save to `raw/<source>.jsonl` and collect. TikTok and Instagram change often: when a command fails, note it
   and move on, never try to get around a block.
5. **Instagram** mostly needs a sign-in. Ask once: "Instagram usually blocks downloads unless I borrow your
   browser's sign-in for it. OK to use your Chrome cookies for Instagram only?" Only with a yes, add
   `--cookies-from-browser chrome`.

## 2. Paid search, only with a yes to the price

When the free set is thin (under about 20 posts) or the brief needs a whole hashtag or keyword with numbers,
propose one paid search through Apify (connected as an MCP server) or Bright Data:

1. Pick a scraper: `search-actors` for "TikTok hashtag" or "Instagram reels", then `fetch-actor-details` on the
   best two. Prefer pay-per-result actors that run on Apify's free plan, with recent successful runs and a
   price per 1,000 results. Skip actors that need a paid plan or a monthly rental.
2. Price it: results you'll ask for (cap them: 100 to 300 is plenty) x price per result. Show it with
   AskUserQuestion: "TikTok #stopmotion, last 30 days, up to 200 posts on <actor>: about US$0.06 (Apify's free
   monthly credit usually covers this). Run it?" Never run it before their yes, and a yes covers only that run.
3. Run with the cap set in the actor's input, then save the dataset items as
   `01_research/discovery/raw/apify-<platform>-<date>.json` and `sc discover collect ... --source apify`.
4. Write the run, the price and their words in the research note's Sources.

## 3. Rank, fetch, break down

1. `sc discover rank --since-days 90 --top 20` (add `--platform tiktok` to look at one platform). Show the user
   the top 10 in a few lines if they're watching. The score favours breakouts from small accounts and recent
   posts; `ranked.md` explains each number.
2. `sc discover fetch-top --n 10` downloads the top 10 as reference-only (with `--cookies-from-browser chrome`
   only after the Instagram yes). Failures are listed; keep their links in the note.
3. Break each fetched video down: spawn `shotcraft:researcher` agents in parallel (2 to 3 videos each, angle
   "platform patterns", `Write only: 01_research/discovery/breakdowns-<n>.json`). Merge their arrays into
   `01_research/discovery/breakdowns.json`, one object per video:
   `{"asset", "url", "hook_s", "hook_type", "length_s", "shots", "avg_shot_s", "format", "sound",
   "text_on_screen", "talking_head", "cta", "pacing", "notes"}`.
4. `sc discover patterns` counts what repeats and writes `patterns.md`.

## 4. The direction note

Spawn the merge pass (`shotcraft:researcher`, `Write only: 01_research/direction-note.md`) with
`ranked.md`, `patterns.md` and the breakdowns. The note leads with the patterns that show up in at least half
the set, with counts, then what to avoid, then generation risks (text, hands, crowds). Then QA as usual.

## Rules

- Everything downloaded is reference-only with its source link. Study it; never repost it, never send it to a
  model, never copy a creator's face, logo or set. Borrow structure and pacing.
- Public posts only. No private accounts, no paywalls, no getting around sign-ins or blocks.
- No money without a shown price and a yes, even inside a free credit.
