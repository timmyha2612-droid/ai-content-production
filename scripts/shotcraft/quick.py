"""The quick track: one shot, one prompt, one price, one yes (SPEC section 4, track "quick").

The full and single tracks are built for productions: intake grilling, QA agents, drafts before finals. For one
shot that is mostly waiting. The quick track keeps what protects the user (live price before any spend, the
budget, rights on inputs, every generation through sc.py, the user's own words on record) and drops the rest.

    sc.py quick plan CARD --name NAME [--input PATH --as source|start_frame|reference ... --rights owned]
                     [--trim START-END] [--crop W:H:X:Y] [--tier final|draft] [--model ID] [--variants N]
        Creates the project on the quick track, copies the inputs into 00_inputs/ (trimming and cropping a
        video first when asked), puts the card in 05_prompts/, validates and compiles it, and gets the live
        price. Prints the one thing to show the user: prompt, settings, price, budget. Spends nothing.
    sc.py quick go --user-said "..." [--timeout S] [--no-wait]
        The user's yes to that summary approves the card AND the spend for the tier shown (it names the price),
        then submits, waits until the job is finished and downloads it.
    sc.py quick keep --user-said "..."  /  sc.py quick redo --user-said "..." --note "what to change"
        Approve the newest result and close the project, or reject it (the note goes on the record) so the
        card can be changed and `quick plan --update` run again.

API: plan(...), go(...), keep(...), redo(...) and the cli_quick_* wrappers.
"""
import json
import os
import re
import shutil
import subprocess
import time

from . import Refused, ShotcraftError, budget, jsonio, manifest, paths, project as project_mod, stages

STAGE = "quick"
TIERS = ("draft", "final")
VIDEO_EXT = (".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi", ".mxf", ".mts", ".m2ts")
SCALE_RE = re.compile(r"^-?\d+:-?\d+$")
ROLES = ("source", "start_frame", "end_frame", "reference", "character", "style")


# ---------------------------------------------------------------- helpers

def _cards():
    from . import cards
    return cards


def _gen():
    from . import gen
    return gen


def _parse_trim(text):
    if not text:
        return None
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*$", str(text))
    if not m:
        raise Refused("--trim takes START-END in seconds, for example 22-26.")
    a, b = float(m.group(1)), float(m.group(2))
    if b <= a:
        raise Refused("--trim: the end (%s) must be after the start (%s)." % (b, a))
    return a, b


def _prepare_input(src, dest_dir, trim=None, crop=None, scale=None):
    """Copy an input into 00_inputs/, trimming / cropping a video with ffmpeg when asked. -> dest path"""
    os.makedirs(dest_dir, exist_ok=True)
    base, ext = os.path.splitext(os.path.basename(src))
    if not trim and not crop and not scale:
        dest = _unique(dest_dir, base + ext)
        shutil.copy2(src, dest)
        return dest
    if not shutil.which("ffmpeg"):
        raise ShotcraftError("--trim, --crop and --scale need ffmpeg (sc.py doctor).")
    tag = []
    if trim:
        tag.append("%g-%gs" % trim)
    if crop:
        tag.append("crop")
    if scale:
        tag.append("scaled")
    dest = _unique(dest_dir, "%s_%s.mp4" % (base, "_".join(tag)))
    cmd = ["ffmpeg", "-v", "error", "-y"]
    if trim:
        cmd += ["-ss", "%g" % trim[0], "-t", "%g" % (trim[1] - trim[0])]
    cmd += ["-i", src, "-an"]
    vf = []
    if crop:
        if not re.match(r"^[\w.+\-*/()]+:[\w.+\-*/()]+:[\w.+\-*/()]+:[\w.+\-*/()]+$", crop):
            raise Refused("--crop takes ffmpeg's W:H:X:Y, for example 1215:2160:1400:0.")
        vf.append("crop=%s" % crop)
    if scale:
        if not SCALE_RE.match(scale):
            raise Refused("--scale takes W:H, for example 1080:1920 (-2 keeps the aspect).")
        vf.append("scale=%s:flags=lanczos" % scale)
    vf.append("format=yuv420p")
    cmd += ["-vf", ",".join(vf), "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-movflags", "+faststart",
            dest]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    except subprocess.TimeoutExpired:
        raise ShotcraftError("ffmpeg took too long preparing %s." % src)
    if r.returncode != 0 or not os.path.exists(dest):
        raise ShotcraftError("ffmpeg could not prepare %s: %s" % (src, (r.stderr or "").strip()[:300]))
    return dest


def _unique(folder, name):
    base, ext = os.path.splitext(name)
    dest, k = os.path.join(folder, name), 2
    while os.path.exists(dest):
        dest = os.path.join(folder, "%s-%d%s" % (base, k, ext))
        k += 1
    return dest


def _quick_project(project):
    data = manifest.load(project)
    if data.get("track") != "quick":
        raise Refused("%s is on the %s track; sc.py quick works only on quick projects." % (
            project, data.get("track")))
    return data


def _the_card(project):
    folder = os.path.join(project, "05_prompts")
    cards = sorted(f for f in os.listdir(folder) if f.endswith(".md")) if os.path.isdir(folder) else []
    if len(cards) != 1:
        raise Refused("A quick project holds exactly one card in 05_prompts/ (found %d)." % len(cards))
    return os.path.join(folder, cards[0])


def _settings(project):
    data = manifest.load(project)
    return data.get("quick") or {}


def _save_settings(project, **kw):
    """Set the given keys exactly (None included): what is saved is what was priced, never a stale value."""
    data = manifest.load(project)
    q = dict(data.get("quick") or {})
    q.update(kw)
    data["quick"] = q
    manifest.save(project, data)
    return q


def _summary(project, est):
    pl = est["plan"]
    b = est["budget"]
    lines = ["Quick shot %s: %s %s with %s." % (pl["shot"], pl["variants"], "take" if pl["variants"] == 1 else
                                                 "takes", pl["model_name"]),
             "Prompt (%s of %s words):" % (pl.get("word_count"), pl.get("max_prompt_words")), pl["prompt"] or ""]
    if pl.get("params"):
        lines.append("Settings: " + ", ".join("%s %s" % (k.replace("_", " "), ("on" if v else "off")
                                                         if isinstance(v, bool) else v)
                                              for k, v in sorted(pl["params"].items())))
    if pl.get("inputs"):
        lines.append("Inputs: " + ", ".join("%s %s" % (r.replace("_", " "), ", ".join(map(str, v)))
                                            for r, v in sorted(pl["inputs"].items())))
    for a in pl.get("adjustments") or []:
        lines.append("Changed %s: %s -> %s. %s" % (a["param"], a["from"], a["to"], a.get("reason") or ""))
    for n in pl.get("notes") or []:
        lines.append("Note: %s" % n)
    if pl.get("dropped_fields"):
        lines.append("Left out: " + ", ".join("%s (%s)" % (d["field"], d["reason"]) for d in pl["dropped_fields"]))
    lines.append("Price: %s credits (%s each, live from %s). Budget: %s." % (
        est["credits_total"], est["credits_each"], est["provider"],
        "no limit" if b.get("remaining") is None else "%s left after this" % _left_after(b, est["credits_total"])))
    if b.get("needs_user_said") or not b.get("ok", True):
        why = str(b.get("reason") or "").strip().rstrip(".")
        lines.append("Budget: %s. Say this in the question; their yes to it is the override." % why)
    # the card approval and the draft gate are what `quick go` settles with the user's one yes
    blockers = [g for g in est["gates"] if "not approved" not in g and "no approved draft" not in g]
    if blockers:
        lines.append("Fix before asking: " + " | ".join(blockers))
    else:
        lines.append("Ask the user once, with the prompt and price above. Their yes: sc.py quick go --user-said "
                     "\"<their words>\"")
    return lines


def _presets():
    from . import rules
    try:
        return rules.load("presets")
    except Exception:
        return None


def _left_after(b, total):
    try:
        return round(float(b["remaining"]) - float(total), 3)
    except (TypeError, ValueError, KeyError):
        return b.get("remaining")


# ---------------------------------------------------------------- plan / go / keep / redo

def plan(card_file, name=None, inputs=None, rights=None, trim=None, crop=None, scale=None, tier=None,
         model=None, variants=None, budget_credits=None, threshold=None, root=None, session_id=None,
         project=None, provider=None):
    """Set up (or, with project=, update) a quick project and price it. Spends nothing."""
    cards = _cards()
    gen = _gen()
    if project is not None:
        # an update keeps what the user already chose unless this call changes it
        _quick_project(project)
        prev = _settings(project)
        tier = tier or prev.get("tier")
        model = model or prev.get("model")
        variants = variants or prev.get("variants")
    tier = tier or "final"
    if tier not in TIERS:
        raise Refused("--tier must be one of: %s." % ", ".join(TIERS))
    if scale and not SCALE_RE.match(str(scale)):
        raise Refused("--scale takes W:H, for example 1080:1920 (-2 keeps the aspect).")
    src_card = os.path.abspath(os.path.expanduser(card_file))
    if not os.path.isfile(src_card):
        raise ShotcraftError("No card at %s." % card_file)
    meta, body = cards.read(src_card)
    inputs = list(inputs or [])
    for p, role in inputs:
        if role not in ROLES:
            raise Refused("--as must be one of: %s." % ", ".join(ROLES))
        if not os.path.exists(os.path.expanduser(p)):
            raise ShotcraftError("No input file at %s." % p)
    if inputs and rights not in ("owned", "licensed", "reference-only"):
        raise Refused("Say whose the inputs are: --rights owned (the user's own footage or photos), licensed, or "
                      "reference-only (never sent to a model).")
    trim_t = _parse_trim(trim)
    sources = [p for p, r in inputs if r == "source"]
    if len(sources) > 1:
        raise Refused("Only one --as source video can be edited per shot.")
    if (trim_t or crop or scale) and not sources:
        raise Refused("--trim, --crop and --scale apply to the source video; add it with --input PATH --as source.")
    for p in sources:
        if os.path.splitext(p)[1].lower() not in VIDEO_EXT:
            raise Refused("The source must be a video (%s); a still to animate is --as start_frame." % p)
    shot = meta.get("id") or "S010"
    errs = cards.validate(dict(meta, inputs=[]), presets=_presets())
    if errs:
        raise Refused("The card does not validate:\n- " + "\n- ".join(errs))
    if project is not None:
        folder = os.path.join(project, "05_prompts")
        others = [f for f in os.listdir(folder) if f.endswith(".md") and f != "%s.md" % shot] \
            if os.path.isdir(folder) else []
        if others:
            raise Refused("This quick project already has a different card (%s); the card's id must stay %s."
                          % (", ".join(others), os.path.splitext(others[0])[0]))

    updating = project is not None
    if project is None:
        if not (name or "").strip():
            name = meta.get("title") or meta.get("id") or "quick shot"
        stamp = time.strftime("%Y%m%d-%H%M")
        project = project_mod.init_project("%s %s" % (name.strip(), stamp), "quick",
                                           use_case=meta.get("use_case") or None, budget=budget_credits,
                                           threshold=threshold, root=root)
        project_mod.open_project(project, session_id)
        stages.start(project, STAGE)
    else:
        st = stages.load_state(project)["stages"][STAGE]["status"]
        if st != "open":
            stages.start(project, STAGE)
        if budget_credits is not None or threshold is not None:
            raise Refused("Change the budget with sc.py budget set on the existing project.")

    # inputs: copied (the source trimmed / cropped / scaled) into 00_inputs/, recorded with their rights.
    # On --update the project card keeps the inputs it already has (the scratch card never holds them), so a
    # changed prompt can't silently turn an edit of the user's clip into text-to-video.
    notes = []
    if updating:
        existing = os.path.join(project, "05_prompts", "%s.md" % shot)
        old_inputs = []
        if os.path.isfile(existing):
            old_meta, _ = cards.read(existing)
            old_inputs = [i for i in (old_meta.get("inputs") or []) if isinstance(i, dict)]
        given = [i for i in (meta.get("inputs") or []) if isinstance(i, dict)]
        if given and given != old_inputs:
            notes.append("The new card's own inputs were ignored; the project's inputs are kept (add files with "
                         "--input).")
        card_inputs = old_inputs
    else:
        card_inputs = [i for i in (meta.get("inputs") or []) if isinstance(i, dict)]
    for p, role in inputs:
        src = os.path.abspath(os.path.expanduser(p))
        edit = role == "source" and bool(trim_t or crop or scale)
        dest = _prepare_input(src, os.path.join(project, "00_inputs"),
                              trim=trim_t if edit else None, crop=crop if edit else None,
                              scale=scale if edit else None)
        note = "quick input from %s" % src
        if edit and trim_t:
            note += ", %g-%g s" % trim_t
        if edit and crop:
            note += ", crop %s" % crop
        if edit and scale:
            note += ", scale %s" % scale
        a = manifest.add_asset(project, dest, rights, "input", note=note, shot=shot)
        card_inputs = [i for i in card_inputs if not (role in ("source", "start_frame", "end_frame")
                                                      and i.get("as") == role)]
        card_inputs.append({"asset": a["id"], "as": role})
    meta["inputs"] = card_inputs
    if model:
        m = meta.get("model") if isinstance(meta.get("model"), dict) else {}
        m[tier] = model
        meta["model"] = m
    if variants:
        meta.setdefault("settings", {})["variants"] = int(variants)
    meta["tier_plan"] = [tier]
    meta["status"] = "draft"
    meta["approved_said"] = None
    meta.pop("approved_hash", None)
    dest_card = os.path.join(project, "05_prompts", "%s.md" % shot)
    cards._atomic_write(dest_card, cards.dump(meta, body))
    errs = gen._card_errors(project, meta)
    if errs:
        raise Refused("The card does not validate:\n- " + "\n- ".join(errs))
    _save_settings(project, priced={})
    # the strict plan refuses now what submit would refuse later (a model that cannot edit, a take too long)
    gen.plan(project, dest_card, tier, model=model, variants=variants, strict=True)
    est = gen.estimate(project, dest_card, tier, model=model, variants=variants, record=False, provider=provider)
    pl = est["plan"]
    # exactly what was priced is what `go` spends: tier, model, take count, total, card
    _save_settings(project, tier=tier, model=pl["model"], variants=pl["variants"],
                   priced={"credits_each": est["credits_each"], "credits_total": est["credits_total"],
                           "model": pl["model"], "variants": pl["variants"], "tier": tier,
                           "at": jsonio.now_iso(), "card_hash": pl["card_hash"], "used_by": None})
    summary = _summary(project, est)
    summary[1:1] = ["Note: %s" % n for n in notes]
    return {"ok": True, "project": project, "card": dest_card, "estimate": est, "summary": summary}


def go(project, user_said, wait=True, timeout=1800, provider=None):
    """The user's one yes: approve the card and the priced spend, submit, wait, download. A price is spent once;
    a higher live price, a changed card or a second go needs a new plan and a new yes."""
    cards = _cards()
    gen = _gen()
    if not (user_said or "").strip():
        raise Refused("sc.py quick go needs the user's own words (--user-said), given to the summary from "
                      "sc.py quick plan.")
    _quick_project(project)
    card = _the_card(project)
    priced = _settings(project).get("priced") or {}
    if priced.get("credits_total") is None:
        raise Refused("Price it first: sc.py quick plan (the user's yes must be to a shown price).")
    if priced.get("used_by"):
        jobs = [j for j in priced["used_by"] if j != "claimed"]
        raise Refused("That price was already used%s. %sFor another take: sc.py quick plan --update and a new yes "
                      "to the new price." % (
                          (" (%s)" % ", ".join(jobs)) if jobs else " by a go that did not finish",
                          ("To wait for or download it: sc.py gen fetch %s. " % jobs[0]) if jobs else
                          "Check what was submitted with sc.py project status. "))
    meta, _ = cards.read(card)
    if gen._card_hash(meta) != priced.get("card_hash"):
        raise Refused("The card changed after it was priced. Run sc.py quick plan --update again and show the new "
                      "price before going ahead.")
    cards.approve(project, card, user_said)
    # claim the price before anything is submitted: a failure part-way, a crash or a second `go` can never spend
    # this yes again. Jobs are added to used_by as each one is created.
    claimed = dict(priced, used_by=["claimed"], used_at=jsonio.now_iso())
    _save_settings(project, priced=claimed)
    made = []

    def on_job(g):
        made.append(g["id"])
        _save_settings(project, priced=dict(claimed, used_by=list(made)))
    try:
        res = gen.submit(project, card, priced["tier"], model=priced.get("model"), variants=priced.get("variants"),
                         user_said=user_said, wait=False, provider=provider, max_credits=priced["credits_total"],
                         quick_priced=True, on_job=on_job)
    except Refused:
        if not made:
            _save_settings(project, priced=priced)  # refused before any job: the price was not spent
        raise
    ids = [g["id"] for g in res["generations"]]
    _save_settings(project, priced=dict(claimed, used_by=ids))
    if wait:
        res["generations"] = [gen.refresh(project, gid, wait=True, timeout=timeout, provider=provider)
                              for gid in ids]
        res["budget"] = budget.status(project)
    return res


def _newest_completed(project):
    gens = [g for g in manifest.load(project).get("generations", []) if g.get("status") == "completed"
            and g.get("approved") is None]
    if not gens:
        raise Refused("No finished result waiting for a decision. Check with sc.py gen status GEN_ID.")
    return gens[-1]


def keep(project, user_said, gen_id=None, note=None):
    gen = _gen()
    _quick_project(project)
    g = manifest.find_generation(project, gen_id) if gen_id else _newest_completed(project)
    if g is None:
        raise ShotcraftError("No generation %s in this project." % gen_id)
    g = gen.approve(project, g["id"], user_said, note)
    rec = stages.done(project, STAGE, user_said=user_said)
    return {"ok": True, "generation": g, "stage": rec}


def redo(project, user_said, note, gen_id=None):
    gen = _gen()
    _quick_project(project)
    if not (note or "").strip():
        raise Refused("Say what to change (--note), in the user's words where you can.")
    g = manifest.find_generation(project, gen_id) if gen_id else _newest_completed(project)
    if g is None:
        raise ShotcraftError("No generation %s in this project." % gen_id)
    g = gen.reject(project, g["id"], user_said, note)
    _save_settings(project, priced={})
    return {"ok": True, "generation": g}


# ---------------------------------------------------------------- CLI

def _emit(args, data, text):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        print(text)


def _proj(args):
    return project_mod.resolve(getattr(args, "project", None), getattr(args, "session_id", None))


def cli_quick_plan(args):
    ins = []
    for p, r in zip(getattr(args, "input", None) or [], getattr(args, "as_role", None) or []):
        ins.append((p, r))
    if len(getattr(args, "input", None) or []) != len(getattr(args, "as_role", None) or []):
        raise Refused("Give one --as for each --input (source, start_frame, end_frame, reference, character, style).")
    proj = _proj(args) if getattr(args, "update", False) else None
    res = plan(args.card, name=getattr(args, "name", None), inputs=ins, rights=getattr(args, "rights", None),
               trim=getattr(args, "trim", None), crop=getattr(args, "crop", None), scale=getattr(args, "scale", None),
               tier=getattr(args, "tier", None), model=getattr(args, "model", None),
               variants=getattr(args, "variants", None), budget_credits=getattr(args, "budget", None),
               threshold=getattr(args, "threshold", None), root=getattr(args, "root", None),
               session_id=getattr(args, "session_id", None), project=proj)
    out = dict(res)
    out["estimate"] = {k: v for k, v in res["estimate"].items() if k != "plan"}
    out["plan"] = res["estimate"]["plan"]
    _emit(args, out, "Project: %s\n%s" % (res["project"], "\n".join(res["summary"])))
    return 0


def cli_quick_go(args):
    proj = _proj(args)
    res = go(proj, args.user_said, wait=not getattr(args, "no_wait", False),
             timeout=getattr(args, "timeout", None) or 1800)
    gen = _gen()
    lines = ["Submitted %d job(s), about %s credits." % (len(res["generations"]), res["credits_total"])]
    lines += ["  " + gen._gen_line(g) for g in res["generations"]]
    for w in res.get("warnings") or []:
        lines.append("Note: " + w)
    done = [g for g in res["generations"] if g.get("status") == "completed"]
    if done:
        lines.append("Show the user the result. Keep it: sc.py quick keep --user-said \"...\"; change it: sc.py "
                     "quick redo --user-said \"...\" --note \"what to change\".")
    elif any(g.get("status") in ("queued", "in_progress", "submitted") for g in res["generations"]):
        lines.append("Still rendering. Wait and download: sc.py gen fetch GEN_ID")
    _emit(args, res, "\n".join(lines))
    from .providers.base import TERMINAL
    bad = [g for g in res["generations"] if g.get("status") in TERMINAL and g.get("status") != "completed"]
    return 1 if bad and len(bad) == len(res["generations"]) else 0


def cli_quick_keep(args):
    res = keep(_proj(args), args.user_said, gen_id=getattr(args, "gen_id", None), note=getattr(args, "note", None))
    g = res["generation"]
    _emit(args, res, "Kept %s: %s. The quick project is done." % (g["id"], ", ".join(g.get("outputs") or [])))
    return 0


def cli_quick_redo(args):
    res = redo(_proj(args), args.user_said, args.note, gen_id=getattr(args, "gen_id", None))
    g = res["generation"]
    _emit(args, res, "Rejected %s (%s). Change the card, then: sc.py quick plan CARD --update, and ask again with the "
                     "new price." % (g["id"], g.get("approval_note")))
    return 0
