---
name: storyboard
description: "Open a shotcraft project as a storyboard web app on 127.0.0.1: timeline, look book, shot panels, references with @labels, an assets tab and each shot's Higgsfield prompt. Triggers: \"open the storyboard\", \"show me the board\", \"I want to add references\", \"moodboard for this shot\", \"what goes to Higgsfield\"."
metadata:
  version: "0.1.0"
---

# shotcraft: storyboard

The storyboard is a local web app over the project. The user reads the script shot by shot, drops in
references for each attribute (character, wardrobe, props, environment, camera, lighting, mood) and for the
look book, names them, and sees what each shot will send to Higgsfield. It changes no card and generates
nothing.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`.

## What lives where

| Part | File | Who writes it |
|---|---|---|
| Board text: title, facts, worlds, look book, shots, notes | `board/board.json` | You, from the script, shot list and bible |
| The Higgsfield side of each shot (models, length, prompt) | `05_prompts/<shot>.md` | The prompts stage, read live |
| References the user adds | `00_inputs/board/` plus `project.json` assets | The app, through `sc` |

## 1. Write board/board.json

When the script exists (best after the shot list and bible), write `board/board.json`. `sc board init` writes a
sample to start from. Keep the user's exact words from the script for picture, voice-over and text cards.

- `title`, `summary`, `facts` (`[{value, label}]`).
- `worlds`: `[{id, label, color}]`, the visual worlds the shots belong to (eras, places), each with a tint.
- `look`: the director's look book, `[{attr, text}]`. Keep it to what the generations need: Visual worlds,
  Palette (hex values with roles and rough shares), Light and texture, Keep out, Moodboard. Edit rhythm and
  music belong on the shots.
- `shots`: one per shot-list row: `n`, `card` (the shot id such as `S010`, or `null` for a shot cut in the
  edit), `time`, `dur` (cut length in seconds), `world` (an id or `mix`), `name`, `size`, `picture`, `vo`,
  `text`, `sound`, `layers` (attribute: text, from the bible and the card), `risk`.
- `notes`: `[{title, items}]`.

Then `sc board check`: it validates the file and shows, per shot, the models chosen on the card, the prompt's
word count and any field the compiler left out. Fix what it reports.

## 2. Open it

`sc board serve` (add `--no-open` in a remote session). It prints a link with a one-time token. Give the user
the link and say: add references with + Ref, by dropping images, or by pasting; tap the tag to set rights;
click the @label to rename. The server stops with Ctrl+C. It binds to 127.0.0.1 only.

## 3. Rights, labels and @ mentions

- A new reference is **reference-only**: it guides your prompt wording and is never sent to a model. A frame
  still is **generated**. The user taps the tag to mark one **owned** or **licensed**.
- Every reference has a label (`@Character1` by default). The user renames it (`@Baker`). When you write a
  card, mention a sent reference by its label in the field it belongs to: `subject.consistency: "same face
  as @Baker"`, `wardrobe_props: "the apron from @Apron"`. The board turns each mention into the model's own
  pointer in slot order (character, then reference, then style): `@Image1`, `@Image2` on Seedance, plain
  words on a model with no pointer syntax on record. It warns when a mention names a reference that isn't
  sent, and when a sent reference is never mentioned.
- Some models refuse a real person's face as a reference. For the user's own likeness, prefer a Soul ID or a
  generated portrait of them, and say so before the first generation.

## 4. From the board to the cards

`sc board inputs` lists the card inputs the board's sendable references call for (`start_frame`, `character`,
`reference`, `style`), as `sc card set-input` commands. They are proposals. Run them only while boards,
drafts or finals is open, each with the user's own words for that input, then `sc card compile` again.
Never mark a reference's rights yourself: the user does that on the board.
