"""Generation: the only way shotcraft spends credits (SPEC sections 4 and 7).

`sc.py gen submit` enforces every gate itself (the guard hook lets sc.py through):
    1. the tier's stage is open (board -> boards, draft -> drafts, final/upscale -> finals); the refine track
       never generates                                                     (stages.gen_allowed)
    2. the card is in 05_prompts/, validates, and was approved with `sc.py card approve` (project.json holds the
       hash of the approved card; any later change needs a new approval)
    3. a final needs at least one approved draft of the shot, an upscale an approved final, or --skip-draft-said
    4. no input asset is reference-only (downloaded references are never sent to a model)
    5. the cost passes budget.check: over the single-job threshold or over what is left needs --user-said
Then it compiles the card for the model (compiler), uploads the inputs through the provider, submits each
variant, records each job in project.json (one generation per job) and holds the estimate in the budget.
With --wait it waits, downloads at once into 06_generations/<boards|drafts|finals|upscaled>/ as
<shot>-<b|d|f|u><n>.<ext>, adds each file as an asset (rights generated) and settles the budget.

The provider comes from $SHOTCRAFT_PROVIDER (fake forces the test double), else project.json, else the config.

API:
    TIER_DIR, TIER_ROLE, TIER_LETTER
    card_path(project, ref) -> abs path      ref: S010, 05_prompts/S010.md or a path
    plan(project, card, tier, model=None, variants=None, strict=True) -> plan dict
        model choice (--model > the card's model for the tier > routing), compiled prompt and params, the
        input assets by role, the duration fit, notes. strict=True refuses a shot longer than one take.
    gates(project, plan, skip_draft_said=None) -> [problems]   the stage/card/approval gates (not budget/rights);
        the card must be approved through `sc.py card approve` and unchanged since (hash in project.json)
    estimate(project, card, tier, model=None, variants=None, record=True) -> result
    submit(project, card, tier, model=None, variants=None, user_said=None, wait=False, timeout=600,
           provider=None, skip_draft_said=None, max_credits=None) -> result     user_said = budget yes;
           skip_draft_said = the separate yes for a final with no approved draft (or an upscale with no approved
           final); max_credits = the price the user said yes to (refused before any job if the live total is higher)
    refresh(project, gen_id, wait=False, timeout=600, provider=None) -> generation (status, download, budget)
    approve(project, gen_id, user_said, note=None) / reject(project, gen_id, user_said, note=None) -> generation
    cli_gen_estimate / cli_gen_submit / cli_gen_status / cli_gen_fetch / cli_gen_approve / cli_gen_reject (args)
"""
import copy
import json
import os
import re

from . import Refused, ShotcraftError, budget, jsonio, manifest, paths, project as project_mod, routing, rules, \
    stages
from .providers import get_provider
from .providers.base import ACTIVE, STATUS_HELP, TERMINAL

TIER_DIR = {"board": "boards", "draft": "drafts", "final": "finals", "upscale": "upscaled"}
TIER_ROLE = {"board": "board", "draft": "draft", "final": "final", "upscale": "upscaled"}
TIER_LETTER = {"board": "b", "draft": "d", "final": "f", "upscale": "u"}
APPROVED_CARD = ("approved", "generated", "final")
MEDIA_KEYS = ("start_image", "end_image", "image_references", "video_references", "audio_references",
              "source_video")
MAX_VARIANTS = 8


# ---------------------------------------------------------------- small helpers

def _said(s):
    return bool((s or "").strip())


def _clean(x):
    if x is None:
        return None
    x = round(float(x), 3)
    return int(x) if x.is_integer() else x


def card_path(project, ref):
    """The card file for a shot id (S010) or a path. Only cards in <project>/05_prompts/ are generated: that
    folder follows the prompts stage lock, and the card's approval is checked against it."""
    ref = str(ref or "").strip()
    if not ref:
        raise Refused("Name the card: a shot id (S010) or a path to 05_prompts/S010.md.")
    cands = []
    if re.match(r"^S\d{3,4}[A-Z]?$", ref):
        cands.append(os.path.join(project, "05_prompts", ref + ".md"))
    if os.path.isabs(os.path.expanduser(ref)):
        cands.append(os.path.expanduser(ref))
    else:
        cands += [os.path.abspath(ref), os.path.join(project, ref)]
    found = next((c for c in cands if os.path.isfile(c)), None)
    if found is None:
        raise ShotcraftError("No prompt card at %s." % ref)
    real = os.path.realpath(found)
    if os.path.dirname(real) != os.path.realpath(os.path.join(project, "05_prompts")):
        raise Refused("Cards are generated only from this project's 05_prompts/<shot>.md (not %s)." % ref)
    return real


def _card_hash(meta):
    from . import cards
    return cards.card_hash(meta)


def _read_card(path):
    from . import cards
    try:
        return cards.read(path)
    except cards.CardError as exc:
        raise Refused("The card %s cannot be read: %s" % (path, exc))


def _card_errors(project, meta):
    from . import cards
    try:
        presets = rules.load("presets", project)
    except Exception:
        presets = None
    return cards.validate(meta, presets=presets)


def _needs_from_card(meta, tier):
    if tier == "board":
        return []
    out = []
    if (meta.get("settings") or {}).get("audio"):
        out.append("audio")
    roles = [i.get("as") for i in (meta.get("inputs") or []) if isinstance(i, dict)]
    if "start_frame" in roles:
        out.append("start_frame")
    if "end_frame" in roles:
        out.append("end_frame")
    if any(r in ("reference", "character", "style") for r in roles):
        out.append("refs")
    return out


def _use_case(project, meta):
    uc = meta.get("use_case")
    if uc:
        return uc
    try:
        return manifest.load(project).get("use_case")
    except ShotcraftError:
        return None


# ---------------------------------------------------------------- plan

def _choose_model(project, meta, tier, model, use_case):
    """-> (model_id, routing need or None, reason)"""
    need = None
    if use_case:
        try:
            need = routing.resolve_need(use_case, project)[0]
        except Refused:
            need = None
    if model:
        return model, need, "you asked for it (--model)"
    card_model = (meta.get("model") or {}).get(tier) if isinstance(meta.get("model"), dict) else None
    if card_model and tier != "board":
        return card_model, need, "the card names it for the %s tier" % tier
    if not use_case:
        raise Refused("The card has no use_case and the project has none, so there is no route. Pass --model.")
    settings = meta.get("settings") or {}
    res = routing.route(use_case, tier, kind=None if tier == "board" else meta.get("kind"),
                        duration=settings.get("duration_s") if tier not in ("board",) else None,
                        needs=_needs_from_card(meta, tier), project=project)
    best = res.get("best")
    if best is None:
        why = "; ".join(res.get("notes") or []) or "no model fits"
        if res.get("candidates"):
            why = "; ".join(res["candidates"][0]["problems"]) + ". " + why
        raise Refused("No model to route %s %s to: %s Pass --model to choose one." % (meta.get("id"), tier, why))
    return best["model"], res["need"], best.get("why") or "first fitting row for %s, %s" % (res["need"], tier)


def _approved(gens, shot, tiers):
    return [g for g in gens if g.get("shot") == shot and g.get("tier") in tiers and g.get("approved") is True
            and g.get("status") == "completed"]


def _hashes(project, assets):
    out = set()
    for r in assets:
        try:
            out.add(manifest.file_sha256(os.path.join(project, r["path"])))
        except (OSError, KeyError):
            pass
    return out


def _asset_paths(project, data, ids_by_role):
    """-> ({role: [abs paths]}, problems)"""
    out, problems = {}, []
    ref_only = [r for r in data.get("assets", []) if r.get("rights") == "reference-only"]
    ref_paths = {r.get("path") for r in ref_only}
    ref_hashes = None
    for role, ids in ids_by_role.items():
        for aid in ids:
            a = manifest.find_asset(data, aid)
            if a is None:
                problems.append("input %s is not an asset in this project (sc.py asset add ...)" % aid)
                continue
            same = a.get("rights") != "reference-only" and a.get("path") in ref_paths
            if not same and a.get("rights") != "reference-only" and ref_only:
                if ref_hashes is None:
                    ref_hashes = _hashes(project, ref_only)
                try:
                    same = manifest.file_sha256(os.path.join(project, a["path"])) in ref_hashes
                except OSError:
                    same = False
            if same:
                problems.append("%s (%s) is the same file as a reference-only download. References are never sent "
                                "to a model; if the user owns or licensed it, mark the reference itself: sc.py asset "
                                "mark <id> --rights owned --user-said \"...\"" % (aid, a.get("path")))
                continue
            if a.get("rights") == "reference-only":
                problems.append("%s (%s) is reference-only. References are never sent to a model; if the user "
                                "owns or licensed it: sc.py asset mark %s --rights owned --user-said \"...\""
                                % (aid, a.get("path"), aid))
                continue
            p = os.path.join(project, a["path"])
            if not os.path.exists(p):
                problems.append("input %s is missing on disk: %s" % (aid, a["path"]))
                continue
            out.setdefault(role, []).append(p)
    return out, problems


def plan(project, card, tier, model=None, variants=None, strict=True):
    from . import compiler
    if tier not in TIER_DIR:
        raise Refused("Tier must be one of: %s." % ", ".join(TIER_DIR))
    path = card_path(project, card)
    meta, _body = _read_card(path)
    stem = os.path.splitext(os.path.basename(path))[0]
    shot = meta.get("id") or stem
    if str(shot) != stem:
        raise Refused("The card %s has id %s; a card's id must match its file name." % (
            paths.rel_to(project, path) or path, shot))
    use_case = _use_case(project, meta)
    preset = rules.preset(use_case, project) if use_case else None
    data = manifest.load(project)
    notes, adjustments = [], []
    mid, need, reason = _choose_model(project, meta, tier, model, use_case)
    profile, err = rules.model_profile(mid, "higgsfield", project)
    if profile is None:
        raise Refused(err)
    row = routing.tier_row(need, tier, mid, project) if need else None
    row_params = dict((row or {}).get("params") or {})
    for k, v in ((profile.get("tier_params") or {}).get(tier) or {}).items():
        row_params.setdefault(k, v)
    out = {"card": path, "card_rel": paths.rel_to(project, path) or path, "shot": shot, "tier": tier,
           "kind": meta.get("kind"), "model": mid, "model_name": profile.get("name") or mid,
           "model_reason": reason, "need": need, "use_case": use_case, "card_status": meta.get("status"),
           "card_hash": _card_hash(meta),
           "card_errors": _card_errors(project, meta), "notes": notes, "adjustments": adjustments,
           "duration": None, "prompt": None, "negative_prompt": None, "params": {}, "inputs": {},
           "input_paths": {}, "input_problems": [], "source": None}
    if profile.get("unconfirmed"):
        notes.append("Some of %s's limits are unconfirmed; the provider corrects them if needed." % out["model_name"])
    # Variants are for exploring. Boards and drafts use the card's count; a final makes ONE take of what was
    # already approved unless the caller asks for more (--variants), because finals are the expensive tier.
    if variants:
        n = variants
    elif tier in ("final", "upscale"):
        n = 1
    else:
        n = (meta.get("settings") or {}).get("variants") or 1
    try:
        n = int(n)
    except (TypeError, ValueError):
        n = 1
    out["variants"] = max(1, min(MAX_VARIANTS, n))

    if tier == "upscale":
        gens = data.get("generations", [])
        src = _approved(gens, shot, ("final",))
        if not src:
            src = [g for g in gens if g.get("shot") == shot and g.get("tier") == "final"
                   and g.get("status") == "completed" and g.get("approved") is not False]
        if not src or not src[-1].get("outputs"):
            raise Refused("Nothing to upscale for %s: there is no completed final yet." % shot)
        source = src[-1]
        role = "video_references" if (profile.get("upscales") == "video") else "image_references"
        out["source"] = source["id"]
        out["params"] = dict(row_params)
        out["input_paths"] = {role: [os.path.join(project, source["outputs"][0])]}
        out["inputs"] = {role: [source["outputs"][0]]}
        out["variants"] = 1
        if source.get("params", {}).get("duration"):
            out["params"].setdefault("duration", source["params"]["duration"])
        notes.append("Upscaling %s (%s). Upscale only when the delivery needs more pixels." % (
            source["id"], source["outputs"][0]))
        return out

    c = copy.deepcopy(meta)
    settings = c.setdefault("settings", {})
    if tier == "board" and profile.get("kind") == "image" and c.get("kind") == "video":
        c["kind"] = "image"
        settings.pop("duration_s", None)
        settings.pop("audio", None)
        notes.append("Board: a still of the shot's key frame (image first), not a video.")
    if tier in ("board", "draft"):
        policy = rules.load("routing", project).get("draft_policy") or {}
        if policy.get("handles") is False and c.get("handles_s"):
            notes.append("No handles on a %s (they are added on the final)." % tier)
            c["handles_s"] = 0
    if "resolution" in row_params:
        settings["resolution"] = row_params.pop("resolution")
    elif preset:
        fr = routing.fit_resolution(preset, tier)
        if fr.get("resolution") and re.match(r"^(\d+(\.\d+)?k|\d+p?)$", str(fr["resolution"]).lower()):
            settings["resolution"] = fr["resolution"]
    compiled = compiler.compile(c, profile, rules.compiler_rules(project))
    params = {k: v for k, v in compiled["params"].items() if k not in MEDIA_KEYS}
    adjustments.extend(compiled.get("adjustments") or [])
    notes.extend(compiled.get("warnings") or [])
    if compiled.get("unguarded"):
        notes.append("Not guarded in the prompt (no positive wording): %s." % ", ".join(compiled["unguarded"]))
    if c.get("kind") == "video" and settings.get("duration_s") is not None and profile.get("durations"):
        df = routing.fit_duration(profile, settings["duration_s"], c.get("handles_s") or 0, shortest=True)
        out["duration"] = df
        if df.get("chain"):
            msg = "%s %s Split the shot into several cards (for example %sA, %sB) or pick a model with longer " \
                  "takes." % (df["reason"], df["chain"]["plan"], shot, shot)
            if strict:
                raise Refused(msg)
            notes.append(msg)
        elif df.get("chosen_s") is not None and params.get("duration") != df["chosen_s"]:
            adjustments[:] = [a for a in adjustments if a.get("param") != "duration"]
            adjustments.append({"param": "duration", "from": params.get("duration"), "to": df["chosen_s"],
                                "reason": df.get("reason")})
            params["duration"] = df["chosen_s"]
        if df.get("trim_plan"):
            notes.append(df["trim_plan"])
    for k, v in row_params.items():
        params.setdefault(k, v)
    if compiled.get("negative_prompt") and profile.get("negative_prompt"):
        params["negative_prompt"] = compiled["negative_prompt"]
    # media: asset ids by role; video and audio assets go to their own reference slots
    ids = {}
    for key in ("start_image", "end_image"):
        if compiled["params"].get(key):
            ids[key] = [compiled["params"][key]]
    for aid in compiled["params"].get("image_references") or []:
        a = manifest.find_asset(data, aid) or {}
        slot = {"video": "video_references", "audio": "audio_references"}.get(a.get("kind"), "image_references")
        ids.setdefault(slot, []).append(aid)
    src = compiled["params"].get("source_video")
    if src:
        # edit the user's own video: the model's edit mode with exactly one video reference
        a = manifest.find_asset(data, src) or {}
        want = meta.get("source_edit") or "edit"
        modes = profile.get("edit_modes") or {}
        em = modes.get(want) or {}
        if a and a.get("kind") != "video":
            msg = "The source input %s is not a video (%s)." % (src, a.get("kind"))
            if strict:
                raise Refused(msg)
            notes.append(msg)
        elif not em:
            msg = ("%s cannot %s a video. Pick a model that can (Seedance 2.5 edits and extends; Cinema Studio 4.0 "
                   "edits) with --model, or change the input from source to reference."
                   % (out["model_name"], "extend" if want.startswith("extend") else "edit"))
            if strict:
                raise Refused(msg)
            notes.append(msg)
        else:
            ids = {"video_references": [src]}
            params.update(em)
            notes.append("%s the source video %s (%s)." % ("Extending" if want.startswith("extend") else "Editing",
                                                           src, ", ".join("%s %s" % kv for kv in em.items())))
    refs = profile.get("refs") or {}
    for slot, lim_key in (("video_references", "video"), ("audio_references", "audio")):
        if ids.get(slot) and not refs.get(lim_key):
            notes.append("%s takes no %s; %s left out." % (out["model_name"], slot.replace("_", " "),
                                                          ", ".join(ids[slot])))
            ids.pop(slot)
    # every input on the card is checked for rights, even the ones this model cannot take
    all_ids = sorted({i.get("asset") for i in (meta.get("inputs") or []) if isinstance(i, dict) and i.get("asset")})
    _, problems = _asset_paths(project, data, {"_all": all_ids})
    input_paths, _ = _asset_paths(project, data, ids)
    out.update({"prompt": compiled["prompt"], "negative_prompt": compiled.get("negative_prompt"),
                "params": params, "inputs": ids, "input_paths": input_paths, "input_problems": problems,
                "word_count": compiled.get("word_count"), "max_prompt_words": compiled.get("max_prompt_words"),
                "dropped_fields": compiled.get("dropped_fields"), "motion_only": compiled.get("motion_only")})
    return out


# ---------------------------------------------------------------- gates

def gates(project, pl, skip_draft_said=None, quick_priced=False):
    """Stage, card and approval gates for a submit. Returns problems (empty = pass).
    skip_draft_said: the user's words for a final with no approved draft (or an upscale with no approved final).
    It is a separate yes from the budget one (--user-said), so one answer never waives both."""
    problems = []
    ok, why = stages.gen_allowed(project, pl["tier"])
    if not ok:
        problems.append(why)
    data = manifest.load(project)
    if pl["tier"] != "upscale":
        appr = manifest.card_approval(data, pl["shot"])
        if pl.get("card_errors"):
            problems.append("the card does not validate: %s" % "; ".join(pl["card_errors"][:5]))
        elif pl.get("card_status") not in APPROVED_CARD or not appr:
            problems.append("the card is not approved yet (status %s). Show it to the user, then: sc.py card approve "
                            "%s --user-said \"<their words>\"" % (pl.get("card_status"), pl.get("card_rel")))
        elif appr.get("hash") != pl.get("card_hash"):
            problems.append("the card changed since the user approved it. Show them the change, then: sc.py card "
                            "approve %s --user-said \"<their words>\"" % pl.get("card_rel"))
    gens = data.get("generations", [])
    # The quick track goes straight to the tier the user chose, but only through `sc.py quick go`, whose one yes
    # named that tier and its price. A plain `sc.py gen submit` on a quick project keeps the draft gate.
    quick = quick_priced and data.get("track") == "quick"
    if pl["tier"] == "final" and not quick and not _approved(gens, pl["shot"], ("draft",)) \
            and not _said(skip_draft_said):
        problems.append("%s has no approved draft. Approve one (sc.py gen approve GEN_ID --user-said \"...\") or, if "
                        "the user wants to go straight to the final, pass their words with --skip-draft-said."
                        % pl["shot"])
    if pl["tier"] == "upscale" and not _approved(gens, pl["shot"], ("final",)) and not _said(skip_draft_said):
        problems.append("%s has no approved final to upscale. Approve one first, or pass the user's words with "
                        "--skip-draft-said." % pl["shot"])
    return problems


# ---------------------------------------------------------------- estimate / submit

def _provider(project, name=None, provider=None):
    return provider or get_provider(name, project=project)


def _estimate_each(prov, pl):
    return float(prov.estimate(pl["model"], pl["params"], pl["input_paths"] or None, pl.get("prompt")))


def estimate(project, card, tier, model=None, variants=None, record=True, provider=None):
    pl = plan(project, card, tier, model=model, variants=variants, strict=False)
    prov = _provider(project, provider=provider)
    each = _estimate_each(prov, pl)
    total = each * pl["variants"]
    chk = budget.check(project, total)
    g = None
    if record:
        g = manifest.add_generation(project, shot=pl["shot"], card=pl["card_rel"], tier=tier, provider=prov.name,
                                    model=pl["model"], params=pl["params"], prompt=pl["prompt"],
                                    inputs=sorted({a for v in pl["inputs"].values() for a in v}),
                                    cost_estimate=_clean(each), status="estimated", variants=pl["variants"])
    return {"ok": True, "generation": g, "plan": _public_plan(pl), "provider": prov.name,
            "credits_each": _clean(each), "credits_total": _clean(total), "budget": chk,
            "gates": gates(project, pl) + pl["input_problems"]}


def _public_plan(pl):
    return {k: v for k, v in pl.items() if k not in ("input_paths",)}


def submit(project, card, tier, model=None, variants=None, user_said=None, wait=False, timeout=600,
           provider=None, skip_draft_said=None, max_credits=None, quick_priced=False, on_job=None):
    pl = plan(project, card, tier, model=model, variants=variants, strict=True)
    problems = gates(project, pl, skip_draft_said, quick_priced=quick_priced)
    if problems:
        raise Refused("Not generating %s %s: %s" % (pl["shot"], tier, " | ".join(problems)))
    if pl["input_problems"]:
        raise Refused("Not generating %s %s: %s" % (pl["shot"], tier, " | ".join(pl["input_problems"])))
    prov = _provider(project, provider=provider)
    if not prov.available():
        raise ShotcraftError("The %s provider is not available here (is the CLI installed? run sc.py doctor)."
                             % prov.name)
    each = _estimate_each(prov, pl)
    total = each * pl["variants"]
    if max_credits is not None and total > float(max_credits) + 1e-6:
        # the user said yes to a price; a higher live price needs a new yes before anything is submitted
        raise Refused("%s %s now costs about %s credits (%d x %s), more than the %s the user said yes to. Show the "
                      "new price and ask again." % (pl["shot"], tier, _clean(total), pl["variants"], _clean(each),
                                                    _clean(max_credits)))
    chk = budget.check(project, total, user_said=user_said)
    if not chk["ok"]:
        raise Refused("%s %s would cost about %s credits (%d x %s): %s" % (
            pl["shot"], tier, _clean(total), pl["variants"], _clean(each), chk["reason"]))
    gstage = stages.gen_stage(project, tier)
    if _said(user_said):
        overrides = ["budget: %s" % chk["reason"]] if chk.get("needs_user_said") else []
        manifest.add_decision(project, gstage, "Generate %s %s with %s, about %s credits%s"
                              % (pl["shot"], tier, pl["model_name"], _clean(total),
                                 (" (the user overrode: %s)" % " | ".join(overrides)) if overrides else ""),
                              user_said)
    if _said(skip_draft_said):
        skipped = [p for p in gates(project, pl, None, quick_priced=quick_priced) if "no approved" in p]
        if skipped:
            manifest.add_decision(project, gstage, "Generate %s %s without the usual approval first (the user "
                                  "overrode: %s)" % (pl["shot"], tier, " | ".join(skipped)), skip_draft_said)
    # upload the inputs once
    uploads, media = {}, {}
    for role, plist in pl["input_paths"].items():
        for p in plist:
            if p not in uploads:
                uploads[p] = prov.upload(p)
            media.setdefault(role, []).append(uploads[p])
    media = role_single(media)
    upload_ids = {(paths.rel_to(project, p) or p): u for p, u in uploads.items()}
    asset_ids = sorted({a for v in pl["inputs"].values() for a in v if re.match(r"^A\d+$", str(a))})
    results = []
    for i in range(pl["variants"]):
        g = manifest.add_generation(
            project, shot=pl["shot"], card=pl["card_rel"], tier=tier, provider=prov.name, model=pl["model"],
            params=pl["params"], prompt=pl["prompt"], inputs=asset_ids, cost_estimate=_clean(each),
            status="estimated", variant=i + 1, variants=pl["variants"], uploads=upload_ids,
            source=pl.get("source"), user_said=user_said if _said(user_said) else None)
        budget.reserve(project, each, gen_id=g["id"], note="%s %s" % (pl["shot"], tier))
        try:
            job = prov.submit(pl["model"], pl["prompt"], pl["params"], media or None)
        except Exception as exc:
            budget.release(project, each, gen_id=g["id"], note="submit failed")
            manifest.update_generation(project, g["id"], status="failed", error=str(exc)[:500], reserved=0,
                                       budget_settled=True)
            raise
        g = manifest.update_generation(project, g["id"], job_id=job, status="submitted",
                                       submitted_at=jsonio.now_iso(), reserved=_clean(each), budget_settled=False)
        if on_job:
            on_job(g)
        if wait:
            g = refresh(project, g["id"], wait=True, timeout=timeout, provider=prov)
        results.append(g)
    return {"ok": True, "generations": results, "plan": _public_plan(pl), "provider": prov.name,
            "credits_each": _clean(each), "credits_total": _clean(total), "budget": budget.status(project)}


def role_single(media):
    """start_image/end_image are single values for the provider."""
    out = {}
    for k, v in media.items():
        out[k] = v[0] if k in ("start_image", "end_image") and isinstance(v, list) and v else v
    return out


# ---------------------------------------------------------------- after submit

def _next_names(project, tier, shot, count=8):
    folder = os.path.join(project, "06_generations", TIER_DIR[tier])
    letter = TIER_LETTER[tier]
    rx = re.compile(r"^%s-%s(\d+)(?:\.|-|$)" % (re.escape(shot), letter))
    used = 0
    names = os.listdir(folder) if os.path.isdir(folder) else []
    for g in manifest.load(project).get("generations", []):
        names += [os.path.basename(o) for o in g.get("outputs") or []]
    for n in names:
        m = rx.match(n)
        if m:
            used = max(used, int(m.group(1)))
    return ["%s-%s%d" % (shot, letter, used + k) for k in range(1, count + 1)]


def _settle(project, g, st, prov):
    """Apply a provider status to a generation: download on completion, settle the budget."""
    status = st.get("status")
    fields = {"status": status, "checked_at": jsonio.now_iso()}
    reserved = g.get("reserved")
    if reserved is None:
        reserved = g.get("cost_estimate") or 0
    if status == "completed":
        outputs = list(g.get("outputs") or [])
        missing = not outputs or not all(os.path.exists(os.path.join(project, o)) for o in outputs)
        if missing:
            dest = os.path.join(project, "06_generations", TIER_DIR[g["tier"]])
            files = prov.download(g["job_id"], dest, names=_next_names(project, g["tier"], g["shot"] or "X"))
            outputs = [paths.rel_to(project, f) for f in files]
            fields["outputs"] = outputs
            fields["downloaded_at"] = jsonio.now_iso()
            assets = []
            for f in files:
                a = manifest.add_asset(project, f, "generated", TIER_ROLE[g["tier"]], shot=g.get("shot"),
                                       note="%s %s by %s" % (g["id"], g["tier"], g.get("model")))
                assets.append(a["id"])
            fields["assets"] = assets
        if not g.get("budget_settled"):
            actual = st.get("cost") if st.get("cost") is not None else g.get("cost_estimate") or 0
            budget.commit(project, reserved, actual, gen_id=g["id"])
            fields.update({"cost_actual": _clean(actual), "reserved": 0, "budget_settled": True})
    elif status in TERMINAL:
        if not g.get("budget_settled"):
            budget.release(project, reserved, gen_id=g["id"], note=status)
            fields.update({"reserved": 0, "budget_settled": True, "cost_actual": 0})
        fields["error"] = st.get("error") or STATUS_HELP.get(status)
        fields["help"] = STATUS_HELP.get(status)
    elif st.get("timed_out"):
        fields["note"] = "still running when the wait ended; check later with sc.py gen status %s" % g["id"]
    return manifest.update_generation(project, g["id"], **fields)


def refresh(project, gen_id, wait=False, timeout=600, provider=None):
    g = manifest.find_generation(project, gen_id)
    if g is None:
        raise ShotcraftError("No generation %s in this project." % gen_id)
    if g.get("status") == "estimated" or not g.get("job_id"):
        return g
    prov = _provider(project, g.get("provider"), provider)
    if g.get("status") in TERMINAL and g.get("status") != "completed":
        return g
    if g.get("status") == "completed" and g.get("budget_settled") and g.get("outputs") and all(
            os.path.exists(os.path.join(project, o)) for o in g["outputs"]):
        return g
    st = prov.wait(g["job_id"], timeout=timeout) if wait else prov.status(g["job_id"])
    return _settle(project, g, st, prov)


def _decide(project, gen_id, user_said, approved, note=None):
    if not _said(user_said):
        raise Refused("Approving or rejecting needs the user's own words (--user-said).")
    g = manifest.find_generation(project, gen_id)
    if g is None:
        raise ShotcraftError("No generation %s in this project." % gen_id)
    if g.get("status") != "completed":
        raise Refused("%s is %s; only a completed generation can be %s." % (
            gen_id, g.get("status"), "approved" if approved else "rejected"))
    g = manifest.update_generation(project, gen_id, approved=approved, approval_said=user_said,
                                   approval_note=note, decided_at=jsonio.now_iso())
    stage = stages.gen_stage(project, g["tier"]) if g.get("tier") else None
    manifest.add_decision(project, stage, "%s %s %s (%s)%s" % (
        "Approved" if approved else "Rejected", gen_id, g.get("shot"), g.get("tier"),
        (": " + note) if note else ""), user_said)
    return g


def approve(project, gen_id, user_said, note=None):
    return _decide(project, gen_id, user_said, True, note)


def reject(project, gen_id, user_said, note=None):
    return _decide(project, gen_id, user_said, False, note)


# ---------------------------------------------------------------- CLI

def _proj(args):
    return project_mod.resolve(getattr(args, "project", None), getattr(args, "session_id", None))


def _emit(args, data, text):
    if getattr(args, "json", False):
        print(json.dumps(data, indent=2, ensure_ascii=False, default=str))
    else:
        print(text)


def _plan_lines(pl):
    lines = ["%s %s with %s. Why: %s" % (pl["shot"], pl["tier"], pl["model_name"],
                                        pl["model_reason"].rstrip(". ") + ".")]
    if pl.get("prompt"):
        lines.append("Prompt (%s of %s words): %s" % (pl.get("word_count"), pl.get("max_prompt_words"),
                                                     pl["prompt"]))
    if pl.get("params"):
        lines.append("Settings: " + ", ".join("%s %s" % (k.replace("_", " "), ("on" if v else "off") if
                                                         isinstance(v, bool) else v)
                                              for k, v in sorted(pl["params"].items())))
    if pl.get("inputs"):
        lines.append("Inputs: " + ", ".join("%s %s" % (r.replace("_", " "), ", ".join(map(str, v)))
                                            for r, v in sorted(pl["inputs"].items())))
    for a in pl.get("adjustments") or []:
        lines.append("Changed %s: %s -> %s. %s" % (a["param"], a["from"], a["to"], a.get("reason") or ""))
    for n in pl.get("notes") or []:
        lines.append("Note: %s" % n)
    return lines


def _gen_line(g):
    s = "%s %s %s: %s" % (g["id"], g.get("shot"), g.get("tier"), g.get("status"))
    if g.get("outputs"):
        s += " -> " + ", ".join(g["outputs"])
    if g.get("error") and g.get("status") != "completed":
        s += " (%s)" % g["error"]
    if g.get("approved") is not None:
        s += " [%s]" % ("approved" if g["approved"] else "rejected")
    return s


def cli_gen_estimate(args):
    proj = _proj(args)
    res = estimate(proj, args.card, args.tier, model=getattr(args, "model", None),
                   variants=getattr(args, "variants", None))
    pl = res["plan"]
    lines = _plan_lines(pl)
    lines.append("Cost: about %s credits each, %s for %d variant(s). %s" % (
        res["credits_each"], res["credits_total"], pl["variants"],
        "Within budget." if res["budget"]["ok"] else "Needs the user's yes: " + res["budget"]["reason"]))
    if res["gates"]:
        lines.append("Before submitting: " + " | ".join(res["gates"]))
    if res.get("generation"):
        lines.append("Recorded as %s (estimate only)." % res["generation"]["id"])
    _emit(args, res, "\n".join(lines))
    return 0


def cli_gen_submit(args):
    proj = _proj(args)
    res = submit(proj, args.card, args.tier, model=getattr(args, "model", None),
                 variants=getattr(args, "variants", None), user_said=getattr(args, "user_said", None),
                 wait=bool(getattr(args, "wait", False)), timeout=getattr(args, "timeout", None) or 600,
                 skip_draft_said=getattr(args, "skip_draft_said", None))
    lines = _plan_lines(res["plan"])
    lines.append("Submitted %d job(s), about %s credits." % (len(res["generations"]), res["credits_total"]))
    lines += ["  " + _gen_line(g) for g in res["generations"]]
    if not getattr(args, "wait", False):
        lines.append("Check with: sc.py gen status GEN_ID (downloads as soon as it is done).")
    _emit(args, res, "\n".join(lines))
    bad = [g for g in res["generations"] if g.get("status") in TERMINAL and g.get("status") != "completed"]
    return 1 if bad and len(bad) == len(res["generations"]) else 0


def cli_gen_status(args):
    proj = _proj(args)
    g = refresh(proj, args.gen_id, wait=False)
    _emit(args, g, _gen_line(g) + (("\n" + g["help"]) if g.get("help") and g.get("status") != "completed" else ""))
    return 0


def cli_gen_fetch(args):
    proj = _proj(args)
    g = refresh(proj, args.gen_id, wait=True, timeout=getattr(args, "timeout", None) or 600)
    _emit(args, g, _gen_line(g))
    if g.get("status") == "completed":
        return 0
    return 1 if g.get("status") in TERMINAL else 0


def cli_gen_approve(args):
    g = approve(_proj(args), args.gen_id, args.user_said, getattr(args, "note", None))
    _emit(args, g, "Approved %s (%s %s)." % (g["id"], g.get("shot"), g.get("tier")))
    return 0


def cli_gen_reject(args):
    g = reject(_proj(args), args.gen_id, args.user_said, getattr(args, "note", None))
    _emit(args, g, "Rejected %s (%s %s).%s" % (g["id"], g.get("shot"), g.get("tier"),
                                                (" Note: " + g["approval_note"]) if g.get("approval_note") else ""))
    return 0
