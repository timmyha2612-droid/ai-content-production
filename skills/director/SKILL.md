---
name: director
description: "Shot list stage of a shotcraft production (and planning one shot): beats, shots, exact durations. Triggers: \"break it into shots\", \"make the shot list\", \"fit it to 15 seconds\"."
metadata:
  version: "0.1.0"
---

# Director (shot list stage)

The director turns the approved script into a shot list that the cinematographer can write cards from and the
budget can survive: every shot has a reason to exist, an exact length, and a note on how it joins its
neighbours. The shot list is also where money is saved: fewer, better shots; image first where a wrong guess
would waste video credits; exact durations with small handles.

In this skill, `sc.py` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Add `--json` when you need to read
the output.

References (read when you need them):
- `references/shotlist-format.md`: the exact table the gate checks, with an example.
- `references/coverage-and-pacing.md`: shot purpose, size progression, pacing by format, continuity for AI.
- `references/duration-fitting.md`: fitting shots to the delivery length and to model lengths, handles, chains.

## 0. Open the stage

```
sc.py project status --json
sc.py stage status shotlist
sc.py stage start shotlist
```

If `start` is refused, go back to the producer skill. The guard blocks writing `03_script/shotlist*` until the
stage is open.

On the **single** track there is no shot list stage: see section 6.

## 1. Read first

1. `03_script/script.md` (two columns: picture and sound). This is approved; do not rewrite it. If a line
   cannot be shot, say so and send it back through the producer (the script stage would be reopened).
2. `02_concept/chosen.md`: the locked tone, structure, hero moment and production method.
3. `00_brief/job-card.md`: delivery (aspect, length, fps), budget, must-haves.
4. The preset: `sc.py route --use-case <use_case> --tier draft --kind video --json` shows the draft models and
   their lengths. The preset's `handles_s` sets the handles.
5. `04_bible/` is not written yet (the bible comes after the shot list). Note what the bible must cover
   (characters, environments, props that recur) in the continuity column.
6. `sc.py asset list --role input --json`: the user's own footage, photos or renders that can fill a shot
   instead of a generation.

## 2. Plan the beats, then the shots

1. List the beats from the script (hook, setup, turn, payoff, call to action, or the script's own structure)
   with their target timing. The beat timings must add up to the delivery length.
2. For each beat, choose the fewest shots that do its job. Give each shot one **purpose** (what the viewer
   must get from it) and one main action. See `references/coverage-and-pacing.md`.
3. Give each shot an exact `duration_s` (the length it plays in the edit, not the generated length). The total
   must equal the delivery length, within 0.5 s. See `references/duration-fitting.md`.
4. Flag **image-first** where a still should come before video: people or a recurring character, a product or
   logo that must look exact, readable text, a complex camera move, shots of 8 s or more, or a shot that needs
   an end frame (match cut, loop).
5. Mark the **kind**: `video` or `image` (a still used as a held frame or a Ken Burns move is an `image`).
6. Mark what belongs to **motion graphics** in the `graphics` column (titles, lower thirds, end card,
   captions, icons, charts). shotcraft does not build motion graphics: they are added afterwards in the
   user's own motion graphics tool, so leave clean space in the frame for them and never generate the text
   into the picture unless the user wants it in-world. An abstract animated loop that is better generated
   stays a shot on this list (use case `mograph-loop`).
7. Mark shots the user's own material covers (`source: 00_inputs/...`) so nothing is generated twice.
8. Write continuity notes: who and what recurs, screen direction, light and time of day, the frame this shot
   must match at its start or end.
9. Note the **depth** of each shot, layer by layer like a multiplane set-up in classic animation: the
   foreground (between camera and subject: rain on glass, a doorframe), the near and far background, and how
   the subject and the place act on each other (neon spill on a cheek, wet hair, a hand on misted glass). The
   cinematographer turns this into the card's `subject.placement`, `subject.interaction`, `world.foreground`,
   `world.background_near`, `world.background_far` and, for video, `world.parallax` (how each layer moves).
   Never leave interaction blank when a person or product is in a place: a subject that ignores its
   surroundings looks pasted in.
10. Name the **composition** of each shot from the quick chooser in
    `${CLAUDE_PLUGIN_ROOT}/docs/research/cinematic-composition-guide.md`: start from what the viewer should
    feel, then pick the technique ("outsider, between two worlds" -> frame within a frame). Combine three at
    most: one geometry, one depth, one light technique.
11. Write one **scene light plan** per scene: a line naming the light sources fixed to the set, for example
    "north window on the left wall, one table lamp right of the bed, blue hour outside". Pick the setup from
    the chooser in `${CLAUDE_PLUGIN_ROOT}/docs/research/cinematic-lighting-guide.md`. You own this line. The
    production designer copies it word for word into the environment file's Light section in the bible stage,
    and the cinematographer copies the anchor phrase from there onto every card in the scene, so the key stays
    on the same side of frame from shot to shot.

## 3. Write the shot list

Write `03_script/shotlist.md` in the format in `references/shotlist-format.md` (start from
`${CLAUDE_PLUGIN_ROOT}/templates/shotlist.md` if it exists). Shot ids are `S010`, `S020` ... (steps of 10, so
an insert can become `S015`). Required columns: `id`, `duration_s`, `purpose`. Strongly recommended: `kind`,
`image_first`, `beat`, `shot`, `move`, `composition`, `depth`, `continuity`, `graphics`, `source`.

Under the table add:
- **Total:** the sum of `duration_s` and the delivery length.
- **Generated length per shot:** from `sc.py route --use-case <use_case> --tier draft --kind video --duration <duration_s>`
  for each video shot (it adds the handles and picks a length the model allows). Note any shot that needs a
  chain of two takes or a different model.
- **Scene light plans:** one line per scene (step 2.11), as `Scene <n> (<place>): <anchor phrase>`.
- **Bible needs:** the characters, environments and props that recur.
- **Graphics list:** everything for the user's motion graphics tool, per shot, with timing.

## 4. Ask the creative calls

Ask only what changes the plan. Use **AskUserQuestion**, at most 3 questions in one go, for example:

- Pacing: "Fast cuts (about 1.5 s a shot) or fewer, longer shots (about 3 s)?" when the script allows both.
- The hero shot: which beat gets the longest or most expensive shot.
- Image-first on borderline shots, stating the trade-off in credits and time.

Show the user the table (or a short summary of it with the total length) before QA. Record what they asked for
in the shot list; it is not a gate here, but their words go on record when the stage closes.

## 5. QA, then close

The gate is a QA PASS. Run the QA loop (the producer skill describes it in full):

1. Spawn the **qa-supervisor** agent with: the project path, stage `shotlist`, the round number (from
   `sc.py qa status --stage shotlist --json`, field `next_round`), and the files to check
   (`03_script/shotlist.md`, `03_script/script.md`, `02_concept/chosen.md`, `00_brief/job-card.md`).
   It checks: every script line covered, durations sum to the delivery, each shot has one purpose, image-first
   flags follow the rule, continuity notes are present, nothing on the list is impossible for the routed models.
2. Spawn the **qa-verifier** agent on the supervisor's judgement calls (fresh eyes), with the same files and the
   findings file.
3. Record the round. The findings JSON goes in a temporary file outside `.shotcraft/qa/` (the guard protects that
   folder; `sc.py` copies the findings in):
   ```
   sc.py qa record --stage shotlist --round <N> --verdict PASS|FAIL --findings <findings.json> --note "<one line>"
   ```
4. On FAIL: fix what is confirmed, ask the user any creative call a finding raises, and run the next round. After
   3 FAIL rounds, escalate to the user; only their words can close the stage then.
5. Close:
   ```
   sc.py stage done shotlist --user-said "<the user's own words about the shot list, if they gave any>"
   ```
   `--user-said` is optional for this gate but record the user's words when they approved the list. Never
   invent them.

## 6. Single track: the light version

On the single track (one shot, icon or thumbnail) there is no shot list stage. The director's work happens inside
the **prompts** stage, which must be open (`sc.py stage status prompts`):

1. Decide the one shot's purpose, exact `duration_s` (video), and beats (what happens in which second).
2. Decide if it should go image-first (same rule as above). On the single track there is no boards stage, so an
   image-first plan means a cheap still draft first, approved, then used as the start frame for the video draft.
3. Create the card and fill those parts:
   ```
   sc.py card new --shot S010 --from-text "<the user's description>"
   ```
   Then set `settings.duration_s`, `layers.time_output.beats` and `rationale.duration` in `05_prompts/S010.md`,
   note the shot's depth (foreground, background, how the subject meets the place), its composition
   technique and its light plan (steps 2.10 and 2.11) for the cinematographer,
   and validate: `sc.py card validate 05_prompts/S010.md`.
4. Hand the card to the cinematographer and generation-tech agents through the producer. The prompts stage gate
   is theirs; do not close it here.

## Never

- Never generate here. Never pick final models; routing is a suggestion until the card is compiled.
- Never pad durations to look generous: the edit length is exact and handles are small.
- Never put a `reference-only` asset in the `source` column.
- Never close the stage with invented user words.
