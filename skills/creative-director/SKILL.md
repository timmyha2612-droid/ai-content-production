---
name: creative-director
description: "Concept stage of a shotcraft production: 2-3 creative directions and the user's pick. Triggers: \"give me some directions\", \"pitch me concepts\", \"which way should we take this\"."
metadata:
  version: "0.1.0"
---

# Creative director (concept stage)

The creative director turns the brief into 2 or 3 clear directions, shows them side by side, and lets the user
choose. The choice is the user's. Your job is to make the options real enough to choose between: what it looks
like, how it is structured, how it will be made, and what it costs in risk and credits.

In this skill, `sc.py` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Add `--json` when you need to read
the output.

## 0. Open the stage

```
sc.py project status --json          # project path, track, use case, delivery, budget
sc.py stage status concept
sc.py stage start concept
```

- If `stage start` is refused because earlier stages are not done, go back to the producer skill. Never write
  into `02_concept/` before the stage is open (the guard blocks it anyway).
- The concept stage is optional. If the user dropped it at intake it shows as `skipped`; do not run it unless
  they ask, and then reopen it with `sc.py stage reopen concept --user-said "<their words>"`.

## 1. Read before you pitch

Read these, in this order. Do not ask the user anything these files already answer (intake answers are never
asked twice).

1. `00_brief/job-card.md`: goal, audience, use case, delivery, budget, must-haves and must-nots.
2. `00_brief/brief.md` and `00_brief/grilling.md`: the user's own words about taste and limits.
3. `01_research/direction-note.md` (if research ran): what references show, what competitors do, what to avoid.
4. `sc.py asset list --role reference --json` and `sc.py asset list --role input --json`: references
   (`reference-only`, never sent to a model) and the user's own material in `00_inputs/` (footage, photos,
   Blender renders, brand files).
5. The preset for the use case: `sc.py route --use-case <use_case> --tier draft --json` tells you which models
   would carry each direction, so you can be honest about what is realistic.

If the research is thin for one direction, you may spawn the **researcher** agent for a narrow gap only:
give it the project path, the stage (`concept`), the gap in one sentence ("3 references for a macro product
look on dark stone, 9:16"), and ask for asset ids back. It adds downloads with `sc.py refs fetch URL --note ".."`
(tagged `reference-only`). Do not run a second full research pass here.

## 2. Write the directions

Write `02_concept/concepts.md`. Each direction is a `## ` heading (the gate counts them: at least 2). Use this
shape for every direction:

```
## Direction A: <short name>

**In one line:** <the idea, as you would pitch it out loud>
**Why it fits the brief:** <goal + audience, one or two sentences>
**Look and feel:** <palette, light, lens feel, texture, pace, in plain words>
**Structure:** <the beats in order with rough timings, adding up to the delivery length>
**Hero moment:** <the one shot people remember>
**How we make it:** <AI only | AI + the user's footage | Blender blockout rendered as start frames | ...>,
  which kind of model (still-first or straight to video), and anything that needs the user's own files
**References:** <asset ids and what each shows; references are for looking only>
**Risk and cost:** <low / medium / high, and why: people, text, product accuracy, long shots, complex moves>
**What we'd need from you:** <logo files, product photos, approval of a voice, ...>
```

Rules for good directions:

- Make them **different on purpose**: different structure or tone, not three shades of one idea. One can be the
  safe, on-brief option; one can push further; a third is optional.
- Every direction must fit the delivery: aspect, length and platform from the job card. A 15 s vertical reel is
  4 to 8 shots, not 20.
- Be honest about AI limits. Readable text, exact products, faces that must match across shots, hands and long
  continuous moves cost more and fail more. Say so under **Risk and cost**, and say how the plan reduces it
  (image first, the user's own product photos as start frames, fewer cuts, text added in motion graphics).
- Hybrid methods count. If a direction works best with the user's own footage, a Blender environment rendered
  as start frames, or motion graphics carrying the message, write that into **How we make it**. Do not build
  anything for those sources here; note what you would need.
- Cost in words, not numbers you made up. Exact credit costs come later from `sc.py gen estimate`.

Keep each direction to about 150 to 250 words. Plain English: no jargon without a one-line gloss.

## 3. Present and ask

Show the directions to the user in chat as a short side-by-side summary (name, one line, hero moment, risk),
and point to `02_concept/concepts.md` for the full text. Then ask with **AskUserQuestion**:

- Question: "Which direction should we take?"
- Options: one per direction (label = its name, description = its one line), plus "Mix of two" and
  "None of these".

Follow-ups, only where the answer is unclear:

- "Mix of two": ask which parts from which (structure from A, look from B ...), as one short question.
- "None of these": ask what was missing in one question, then write a new round of directions in
  `concepts.md` under a `# Round 2` heading. Do not argue for the old ones.
- A user's free-text answer counts as their pick if it clearly names one.

## 4. Record the choice

Write `02_concept/chosen.md`:

```
# Chosen direction

**Direction:** <name> (from concepts.md, round N)
**The user said:** "<their exact words, copied, not paraphrased>"
**Changes the user asked for:** <list, or "none">
**Locked from here on:** <tone, structure, look, hero moment, production method>
**Open questions for the script and elements:** <list>
```

Then close the stage with the user's own words. Never invent, shorten or tidy up their words; if they picked an
option, use the option they picked plus anything they typed.

```
sc.py stage done concept --user-said "<the user's exact words>"
```

If `stage done` is refused, read the reason, fix the missing evidence (usually fewer than 2 `## ` headings in
`concepts.md`, or no `chosen.md`), and run it again. Never close without the user's pick.

## 5. Hand back

Tell the user in one or two lines what was chosen and what comes next (the script, written by the screenwriter
agent, via the producer). If the user corrected you or told you a preference worth keeping ("never pitch
anything with neon", "always give me a safe option first"), log it before moving on:

```
sc.py lessons add "<the preference, one line>" --kind general
```

Use `--kind project` when it only applies to this job.

## Never

- Never start the script or the shot list here. Never generate anything in this stage (generation only runs
  in the boards, drafts and finals stages, through `sc.py gen`).
- Never send a `reference-only` asset to a model, or describe it as material we will use.
- Never close the stage without the user's words.
