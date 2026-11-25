---
name: quick
description: "One shot generated now, no intake or drafts: one prompt, one live price, one yes. Also edits of the user's own video or still: relight, sky, clean up or remove objects, change background, animate, extend. Triggers: \"just generate it\", \"relight this\", \"refine this clip\", \"change the background\", \"clean this up\"."
metadata:
  version: "0.1.0"
---

# shotcraft: quick (one shot, one price, one yes)

The user wants the shot, not a process. Get them from request to downloaded file with **one** question.
What stays: the live price before any spend, the budget, rights on their inputs, every generation through
`sc`, their own words on record. What goes: intake rounds, job card, QA agents, drafts, stage ceremony.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Load the **prompt-craft** skill for the vocabulary
and per-model notes.

## 1. Write the card (no questions yet)

Work in your scratch folder, not in a project. Same as the refine skill steps 1 and 2: `sc card new --shot
S010 --from-text "<their words>" --json` (with a project already active, for example an earlier quick shot,
`card new` would write into that project: copy `${CLAUDE_PLUGIN_ROOT}/templates/prompt-card.md` instead),
fill the front matter, `sc card validate`, then a read-only
`sc card compile <file> --model <id> --dry-run`. If there is already a refine card for this shot, use it.

- **Editing their own video** (relight, sky change, restyle, clean-up): the clip is an input with
  `--as source`. The source sets framing, camera move and timing, so leave camera and beats empty and spend
  the words on what changes ("only light and sky change", the key, its side and height, the shadows it
  casts, the palette). The compiler drops camera fields and protects the light fields from trimming. Only
  models with an edit mode can do this (Seedance 2.5, Cinema Studio 4.0); `sc quick plan` refuses others.
- **Animating a still**: the image is `--as start_frame`; the prompt is motion only.
- **A file dropped in with a few words** ("refine this", "clean up the bins", "nicer sky"): run
  `sc quick recipes --say "<their words>" --file <file>`. It names the recipe (relight, sky, cleanup,
  background, animate, extend) with its prompt tips; ask only when it says there is no clear winner. Then
  `sc quick plan ... --recipe <name>` sets the model, mode, input role, what must stay and the length.
- **From an editing timeline** (DaVinci Resolve, Premiere): taking the shot out and putting the result back
  is the editing tool's job; here the exported clip is just `--input` with its recipe.
- **Length**: generate the cut length plus handles only when the model's minimum needs it (a 3 s insert on
  a 4 s minimum model is 3 s + 0.5 s handles).
- **Tier**: `final` at the delivery resolution by default. `--tier draft` only when the user wants a cheap
  test first or the shot is risky (people, text, heavy motion) and they agree.

## 2. Plan and price: `sc quick plan`

```
sc quick plan <card.md> --name "<short name>" \
  [--input <their file> --as source --rights owned] [--trim 22-26] [--crop 1215:2160:1400:0 --scale 1080:1920] \
  [--tier final|draft] [--model <id>] [--variants N] [--budget <credits>]
```

It creates the project on the quick track (named with a date stamp, under the projects folder), copies the
inputs into `00_inputs/` (trimming, cropping and scaling the `source` video with ffmpeg first, so you never
cut it by hand; other inputs are copied as they are),
puts the card in `05_prompts/`, refuses anything submit would refuse (a model that cannot edit, a take too
long) and gets the **live** price. It spends nothing.

`--rights owned` only for the user's own footage, photos or renders (their shoot folder, their client's
files they produce). Anything downloaded or made by someone else is `reference-only` and is never sent.

## 3. Ask once

One AskUserQuestion with everything the yes covers, from the plan's output:

- the compiled prompt (short version is fine), the model, tier, resolution, aspect, length, takes
- what the input is and that it is theirs ("your drone clip, 22-26 s, cropped to 9:16")
- the price in credits and what is left of the budget

Options: "Go: <N> credits (Recommended)" and "Change something". Nothing else. Do not ask about taste you
can decide (lens, light, grade): decide it and show it in the prompt.

## 4. Generate: `sc quick go`

On their yes: `sc quick go --user-said "<their exact words>"`, run in the background (it waits until the
job is finished and downloads it, up to 30 minutes). Their one yes approves the card and the spend shown;
the quick track needs no draft first.

`go` spends exactly what was priced (model, takes, total) and only once. It refuses, before anything is
submitted, when the live price is higher than the one they said yes to, when the card changed since pricing,
or when that price was already spent (then `sc gen fetch GEN_ID` waits for and downloads the running job;
never run `go` again to "retry"). On a refusal over price: show the new price and ask again.

If they changed something instead: edit the scratch card, `sc quick plan <card> --update`, ask again with the
new price. `--update` keeps the project's inputs (the source clip and its trim and crop); pass `--input ...`
again only to replace them.

## 5. Show it, then keep or redo

When it is downloaded: send the file, plus a before/after strip for an edit (3 frames of the source above
3 of the result, ffmpeg `hstack`/`vstack`). Say plainly what worked and what did not, against the prompt.
Then one question: keep / redo.

- Keep: `sc quick keep --user-said "<their words>"` (approves it and closes the project).
- Redo: `sc quick redo --user-said "<their words>" --note "<what to change>"`, change the scratch card,
  `sc quick plan <card> --update` (the inputs are kept), ask again with the new price.

Log a lesson only when they corrected you or stated a preference (`sc lessons add`).

## Rules

- One question before spending. Never spend without the user's words to a shown price.
- Never run raw `higgsfield generate`; always `sc quick go` (or `sc gen` on other tracks).
- Never send a file the user did not make or license; `--rights` is their answer, not your guess.
- Never make it bigger or longer than the delivery needs.
- A shot that needs a full crew (several shots, continuity, a script) is not quick: say so and offer the
  producer skill.
