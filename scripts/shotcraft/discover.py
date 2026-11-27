"""Social discovery for the research stage: collect posts, rank them, fetch the best, count what repeats
(SPEC section 15).

Free first. Posts come from what the researcher gathers: links the user saved, yt-dlp metadata (`yt-dlp
--dump-json`, YouTube search, public TikTok pages), TikTok Creative Center read in the browser, the open-source
TikTok-Api (scripts/tools/tiktok_search.py) and Instaloader (Instagram) on the user's own computer, and, only with
the user's yes to the shown price, a paid scraper's dataset (Apify and the like). Whatever the source, `collect`
turns it into one list of posts in <project>/01_research/discovery/posts.json. Nothing here spends money or
talks to a platform except `fetch_top`, which uses the normal reference download (reference-only, source kept).

Ranking is explainable, not magic. For each post:
    engagement = (likes + 2 x comments + 3 x shares + 2 x saves) / views
    breakout   = views / followers                    (when the account size is known)
    recency    = 0.5 ** (days old / half_life)        (half_life 30 days by default)
    score      = log10(views + 10) x (1 + 5 x min(engagement, 0.3)) x (1 + log10(1 + min(breakout, 100)))
                 x recency
so a breakout from a small account beats a big account's ordinary post, and last week beats last year.

Patterns: the researcher writes one breakdown per fetched video into discovery/breakdowns.json; `patterns`
counts what repeats ("hook under 1.5 s: 7 of 10") and writes discovery/patterns.md.

API:
    normalize(record, source=None) -> post dict | None
    collect(project, paths, source=None) -> {"added", "updated", "skipped", "total", "path"}
    score(post, now=None, half_life=30) -> (score, parts)
    rank(project, top=20, since_days=None, platform=None, min_views=0, half_life=30) -> [posts]
    fetch_top(project, n=10, cookies_from_browser=None) -> {"fetched": [...], "failed": [...]}
    patterns(project) -> {"n", "lines", "path"}
    cli_discover_collect / rank / fetch_top / patterns
"""
import csv
import datetime as _dt
import glob
import json
import lzma
import math
import os
import re
import statistics

from . import Refused, ShotcraftError, jsonio, refs

DISCOVERY = "01_research/discovery"
_NUM = re.compile(r"^\s*([\d.,]+)\s*([kKmMbB]?)\s*$")


def _dir(project):
    return os.path.join(project, DISCOVERY)


def _num(v):
    """123, "1,234", "12.5K", "3M" -> float; anything else -> None."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if v >= 0 else None
    m = _NUM.match(str(v))
    if not m:
        return None
    try:
        n = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    return n * {"": 1, "k": 1e3, "m": 1e6, "b": 1e9}[m.group(2).lower()]


def _get(rec, *paths):
    """First present value among dotted paths ("authorMeta.fans")."""
    for p in paths:
        cur = rec
        for part in p.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
                cur = cur[int(part)]
            else:
                cur = None
                break
        if cur not in (None, ""):
            return cur
    return None


def _date(v):
    """ISO string, yt-dlp YYYYMMDD, or epoch seconds -> ISO date string."""
    if v in (None, ""):
        return None
    try:
        if isinstance(v, (int, float)) or (isinstance(v, str) and v.isdigit() and len(v) > 8):
            return _dt.datetime.fromtimestamp(float(v), _dt.timezone.utc).date().isoformat()
        s = str(v)
        if re.match(r"^\d{8}$", s):
            return "%s-%s-%s" % (s[:4], s[4:6], s[6:])
        return _dt.date.fromisoformat(s[:10]).isoformat()
    except (ValueError, OSError, OverflowError):
        return None


def _platform(url, hint=None):
    u = (url or "").lower()
    for name in ("tiktok", "instagram", "youtube", "facebook", "x.com", "twitter"):
        if name in u:
            return {"x.com": "x", "twitter": "x"}.get(name, name)
    h = (hint or "").lower()
    if "youtu" in h:
        return "youtube"
    return h or "other"


def normalize(rec, source=None):
    if not isinstance(rec, dict):
        return None
    if isinstance(rec.get("node"), dict):  # Instaloader's per-post JSON ({"node": {...}})
        rec = dict(rec["node"], _source=rec.get("_source"))
    url = _get(rec, "webVideoUrl", "webpage_url", "url", "postUrl", "link", "shareUrl", "video_url")
    if not url and rec.get("id") and _get(rec, "author.uniqueId"):  # TikTok-Api's video dict
        url = "https://www.tiktok.com/@%s/video/%s" % (_get(rec, "author.uniqueId"), rec["id"])
    if not url and rec.get("shortcode"):  # Instaloader
        url = "https://www.instagram.com/%s/%s/" % ("reel" if rec.get("is_video") else "p", rec["shortcode"])
    if not url or not re.match(r"^https?://", str(url)):
        return None
    views = _num(_get(rec, "playCount", "stats.playCount", "view_count", "videoViewCount", "videoPlayCount",
                      "video_view_count", "video_play_count", "views", "plays", "viewCount"))
    tags = _get(rec, "hashtags", "tags", "challenges") or []
    if isinstance(tags, str):
        tags = re.findall(r"#?(\w+)", tags)
    if not tags:  # fall back to the hashtags written in the caption
        tags = re.findall(r"#(\w+)", str(_get(rec, "text", "caption", "desc", "description",
                                               "edge_media_to_caption.edges.0.node.text") or ""))
    tags = [str((t.get("name") or t.get("title")) if isinstance(t, dict) else t).lstrip("#").lower()
            for t in tags if t][:30]
    caption = _get(rec, "text", "caption", "description", "title", "desc",
                   "edge_media_to_caption.edges.0.node.text") or ""
    post = {
        "url": str(url).split("?")[0] if "tiktok.com" in str(url) or "instagram.com" in str(url) else str(url),
        "platform": _platform(str(url), _get(rec, "extractor_key", "platform")),
        "author": _get(rec, "authorMeta.name", "author.uniqueId", "authorName", "ownerUsername", "owner.username",
                       "uploader", "channel", "author", "username"),
        "followers": _num(_get(rec, "authorMeta.fans", "author.followerCount", "authorStats.followerCount",
                               "channel_follower_count", "followers", "ownerFollowers", "followersCount")),
        "views": views,
        "likes": _num(_get(rec, "diggCount", "stats.diggCount", "like_count", "likesCount",
                           "edge_media_preview_like.count", "edge_liked_by.count", "likes")),
        "comments": _num(_get(rec, "commentCount", "stats.commentCount", "comment_count", "commentsCount",
                              "edge_media_to_comment.count", "comments")),
        "shares": _num(_get(rec, "shareCount", "stats.shareCount", "repost_count", "shares", "sharesCount")),
        "saves": _num(_get(rec, "collectCount", "stats.collectCount", "saves", "savesCount")),
        "posted": _date(_get(rec, "createTimeISO", "createTime", "timestamp", "upload_date", "takenAt",
                             "taken_at_timestamp", "posted", "date")),
        "duration": _num(_get(rec, "videoMeta.duration", "video.duration", "duration", "videoDuration",
                              "video_duration", "length")),
        "caption": str(caption)[:500],
        "hashtags": tags,
        "sound": _get(rec, "musicMeta.musicName", "music.title", "track", "musicInfo.song_name", "sound"),
        "source": source or rec.get("_source") or "unknown",
    }
    if isinstance(post["author"], dict):
        post["author"] = post["author"].get("uniqueId") or post["author"].get("name")
    if post["author"] is not None:
        post["author"] = str(post["author"])[:80]
    if post["sound"] is not None:
        post["sound"] = str(post["sound"])[:120]
    return post


def _read_any(path):
    """A JSON array, an object with items/data/results, JSON lines, a CSV, a yt-dlp .info.json, or a folder of
    those (searched recursively for *.json and *.csv)."""
    if os.path.isdir(path):
        out = []
        for p in sorted(glob.glob(os.path.join(path, "**", "*.json"), recursive=True)
                        + glob.glob(os.path.join(path, "**", "*.json.xz"), recursive=True)
                        + glob.glob(os.path.join(path, "**", "*.jsonl"), recursive=True)
                        + glob.glob(os.path.join(path, "**", "*.csv"), recursive=True)):
            if os.path.basename(p) in ("posts.json", "ranked.json", "breakdowns.json", "source.json"):
                continue
            out += _read_any(p)
        return out
    if path.lower().endswith(".xz"):  # Instaloader compresses its metadata by default
        with lzma.open(path, "rt", encoding="utf-8") as fh:
            text = fh.read()
    else:
        with open(path, encoding="utf-8-sig") as fh:
            text = fh.read()
    if path.lower().endswith(".csv"):
        return list(csv.DictReader(text.splitlines()))
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except ValueError:
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    raise ShotcraftError("%s is not JSON, JSON lines or CSV." % path)
        return rows
    if isinstance(data, dict):
        for k in ("items", "data", "results", "entries", "posts"):
            if isinstance(data.get(k), list):
                return data[k]
        return [data]
    return data if isinstance(data, list) else []


def _load_posts(project):
    data = jsonio.read_json(os.path.join(_dir(project), "posts.json"))
    return data if isinstance(data, list) else []


def collect(project, paths, source=None):
    if not paths:
        raise Refused("Give at least one file or folder of posts (JSON, JSON lines, CSV or yt-dlp .info.json).")
    posts = {p["url"]: p for p in _load_posts(project)}
    added = updated = skipped = 0
    for path in paths:
        if not os.path.exists(path):
            raise ShotcraftError("No such file or folder: %s" % path)
        for rec in _read_any(path):
            p = normalize(rec, source)
            if p is None:
                skipped += 1
                continue
            old = posts.get(p["url"])
            if old:
                for k, v in p.items():  # keep the richest value per field
                    if old.get(k) in (None, "", []) and v not in (None, "", []):
                        old[k] = v
                for k in ("views", "likes", "comments", "shares", "saves", "followers"):
                    if p.get(k) is not None and (old.get(k) or 0) < p[k]:
                        old[k] = p[k]
                updated += 1
            else:
                p["collected_at"] = jsonio.now_iso()
                posts[p["url"]] = p
                added += 1
    out = os.path.join(_dir(project), "posts.json")
    jsonio.write_json(out, list(posts.values()))
    return {"added": added, "updated": updated, "skipped": skipped, "total": len(posts),
            "path": os.path.relpath(out, project)}


def score(post, now=None, half_life=30):
    now = now or _dt.date.today()
    v = post.get("views")
    if not v:
        return 0.0, {"why": "no view count"}
    l, c, s, sv = (post.get(k) or 0 for k in ("likes", "comments", "shares", "saves"))
    eng = (l + 2 * c + 3 * s + 2 * sv) / v
    f = post.get("followers")
    breakout = (v / f) if f else None
    days = None
    rec = 1.0
    if post.get("posted"):
        try:
            days = max(0, (now - _dt.date.fromisoformat(post["posted"])).days)
            rec = 0.5 ** (days / float(half_life))
        except ValueError:
            pass
    sc = math.log10(v + 10) * (1 + 5 * min(eng, 0.3)) * \
        (1 + math.log10(1 + min(breakout, 100)) if breakout is not None else 1) * rec
    return round(sc, 3), {"engagement": round(eng, 4), "breakout": round(breakout, 2) if breakout else None,
                          "days_old": days, "recency": round(rec, 3)}


def rank(project, top=20, since_days=None, platform=None, min_views=0, half_life=30, now=None):
    posts = _load_posts(project)
    if not posts:
        raise Refused("No posts collected yet: sc.py discover collect FILE ...")
    now = now or _dt.date.today()
    out = []
    for p in posts:
        if platform and p.get("platform") != platform:
            continue
        if (p.get("views") or 0) < min_views:
            continue
        sc, parts = score(p, now, half_life)
        if since_days is not None and parts.get("days_old") is not None and parts["days_old"] > since_days:
            continue
        out.append(dict(p, score=sc, **parts))
    out.sort(key=lambda p: p["score"], reverse=True)
    for i, p in enumerate(out, 1):
        p["rank"] = i
    d = _dir(project)
    jsonio.write_json(os.path.join(d, "ranked.json"), out)
    lines = ["# Ranked posts", "", "Score = reach x engagement x breakout x recency (see discover.py).", "",
             "| # | Platform | Author | Views | Eng. | Breakout | Days | Score | Link |",
             "|---|---|---|---|---|---|---|---|---|"]
    for p in out[:top]:
        lines.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (
            p["rank"], p["platform"], (p.get("author") or "").replace("|", "/"), _short(p.get("views")),
            "%.1f%%" % (100 * p["engagement"]) if "engagement" in p else "-",
            "%sx" % p["breakout"] if p.get("breakout") else "-",
            p["days_old"] if p.get("days_old") is not None else "-", p["score"], p["url"]))
    with open(os.path.join(d, "ranked.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return out[:top]


def _short(n):
    if n is None:
        return "-"
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if n >= div:
            return "%.1f%s" % (n / div, suf)
    return str(int(n))


def fetch_top(project, n=10, cookies_from_browser=None):
    ranked = jsonio.read_json(os.path.join(_dir(project), "ranked.json"))
    if not isinstance(ranked, list) or not ranked:
        raise Refused("Rank the posts first: sc.py discover rank")
    done, failed = [], []
    for p in ranked[:n]:
        if p.get("assets"):
            continue
        note = "discovery #%d (score %s, %s views)" % (p["rank"], p.get("score"), _short(p.get("views")))
        try:
            r = refs.fetch(project, p["url"], note=note, cookies_from_browser=cookies_from_browser)
            p["assets"] = [a["id"] for a in r["assets"]]
            done.append({"rank": p["rank"], "url": p["url"], "assets": p["assets"]})
        except (ShotcraftError, OSError) as exc:
            failed.append({"rank": p["rank"], "url": p["url"], "why": str(exc)[:200]})
    jsonio.write_json(os.path.join(_dir(project), "ranked.json"), ranked)
    return {"fetched": done, "failed": failed}


# Breakdown fields the researcher fills per video, and how `patterns` reads them.
NUMERIC = {"hook_s": [("hook under 1.5 s", lambda x: x < 1.5), ("hook under 3 s", lambda x: x < 3)],
           "length_s": [("under 20 s", lambda x: x < 20), ("20 to 45 s", lambda x: 20 <= x <= 45),
                        ("over 45 s", lambda x: x > 45)],
           "avg_shot_s": [("cuts faster than every 1.5 s", lambda x: x < 1.5),
                          ("shots of 1.5 to 3 s", lambda x: 1.5 <= x <= 3), ("shots over 3 s", lambda x: x > 3)]}
CATEGORICAL = ("hook_type", "format", "sound", "text_on_screen", "talking_head", "cta", "pacing")


def patterns(project):
    path = os.path.join(_dir(project), "breakdowns.json")
    rows = jsonio.read_json(path)
    if not isinstance(rows, list) or not rows:
        raise Refused("No breakdowns yet: write one object per fetched video into %s/breakdowns.json." % DISCOVERY)
    rows = [r for r in rows if isinstance(r, dict)]
    n = len(rows)
    for r in rows:
        if r.get("avg_shot_s") is None and _num(r.get("length_s")) and _num(r.get("shots")):
            r["avg_shot_s"] = _num(r["length_s"]) / _num(r["shots"])
    lines = ["# What repeats across %d videos" % n, ""]
    for field, bands in NUMERIC.items():
        vals = [_num(r.get(field)) for r in rows if _num(r.get(field)) is not None]
        if not vals:
            continue
        lines.append("**%s** (median %s, from %d of %d)" % (field, round(statistics.median(vals), 2), len(vals), n))
        for label, test in bands:
            k = sum(1 for v in vals if test(v))
            lines.append("- %s: %d of %d" % (label, k, len(vals)))
        lines.append("")
    for field in CATEGORICAL:
        vals = [str(r.get(field)).strip().lower() for r in rows if r.get(field) not in (None, "")]
        if not vals:
            continue
        counts = {}
        for v in vals:
            counts[v] = counts.get(v, 0) + 1
        top = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:5]
        lines.append("**%s**: " % field + "; ".join("%s (%d of %d)" % (k, c, len(vals)) for k, c in top))
    lines += ["", "A pattern is worth copying when it shows up in at least half the set. Borrow structure and "
                  "pacing, never a creator's face, logo or set."]
    out = os.path.join(_dir(project), "patterns.md")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    return {"n": n, "lines": lines, "path": os.path.relpath(out, project)}


# ---------------------------------------------------------------- CLI

def _project(args):
    from . import project as _p
    return _p.resolve(getattr(args, "project", None), getattr(args, "session_id", None))


def _out(args, obj, text):
    print(json.dumps(obj, indent=2, ensure_ascii=False) if getattr(args, "json", False) else text)
    return 0


def cli_discover_collect(args):
    r = collect(_project(args), args.paths, getattr(args, "source", None))
    return _out(args, {"ok": True, **r}, "%d new, %d updated, %d skipped. %d posts in %s." % (
        r["added"], r["updated"], r["skipped"], r["total"], r["path"]))


def cli_discover_rank(args):
    top = rank(_project(args), top=args.top, since_days=args.since_days, platform=args.platform,
               min_views=args.min_views or 0, half_life=args.half_life)
    text = "\n".join("%2d. %s %s  %s views, eng %.1f%%, breakout %s, score %s  %s" % (
        p["rank"], p["platform"], p.get("author") or "?", _short(p.get("views")), 100 * p.get("engagement", 0),
        ("%sx" % p["breakout"]) if p.get("breakout") else "-", p["score"], p["url"]) for p in top)
    return _out(args, {"ok": True, "top": top}, text or "Nothing matches.")


def cli_discover_fetch_top(args):
    r = fetch_top(_project(args), args.n, getattr(args, "cookies_from_browser", None))
    text = "Fetched %d, failed %d." % (len(r["fetched"]), len(r["failed"]))
    for f in r["failed"]:
        text += "\n- #%d %s: %s" % (f["rank"], f["url"], f["why"])
    return _out(args, {"ok": True, **r}, text)


def cli_discover_patterns(args):
    r = patterns(_project(args))
    return _out(args, {"ok": True, **r}, "\n".join(r["lines"]))
