# Changelog

All notable changes to shotcraft are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). Rule files carry their own `rules_version` and `checked_at`
dates; rule changes that alter what gets generated are listed here too.

## [Unreleased]

## [0.1.0] - 2026-11-24

First public release.

### Added

- Three tracks: `refine` (just a prompt, no generation), `single` (one asset) and `full` (research to hand-off).
- Stage gates with evidence checked by code (`rules/tracks.json`, `rules/stages.json`), QA rounds (at most 3,
  then escalation to the user), reopen with history, and the user's own words recorded on every approval.
- `scripts/sc.py`: one command-line entry for projects, stages, QA, budget, assets and rights, prompt cards,
  routing, generation, references, contact sheets, delivery checks, the animatic, the model check, the
  hand-off and the lessons inbox. Python 3.9+ standard library only.
- Prompt engine: six-layer prompt cards (JSON front matter plus markdown), a compiler that fits a card to a
  model (prompt length, trimming order, motion-only for start frames, avoid items rewritten as positive
  wording, parameters corrected and reported).
- Rule files: taxonomy with a professional vocabulary, negatives, positive rewrites, Higgsfield model
  profiles, routing, and 16 use-case presets. Layered: plugin, personal (`~/.shotcraft/rules/`) and project.
- Higgsfield CLI provider, plus a fake provider for tests. Live cost checks before every job, a credit budget
  with a single-job threshold, and reference rights enforcement.
- Hooks: a guard (raw generation goes through `sc.py gen`, protected project files, stage folders writable
  only while their stage is open), a daily model check at session start, and a lessons reminder.
- The crew: producer, refine, creative-director, director, review, handoff, learn,
  model-scout and prompt-craft skills, and the agents they spawn.
- Higgsfield hand-off: approved assets uploaded and a Canvas build sheet (Canvas has no API yet).
- Templates for the job card, brief, two-column script, shot list, character and environment bible pages,
  prompt card, direction note and Canvas build sheet.

### Known limits

- Higgsfield Canvas cannot be built automatically; the hand-off writes a build sheet instead.
- Per-model negatives and some model limits are starting guesses, marked as unconfirmed in the rule files.
- Not yet tested on Python 3.9 itself (tests run on newer versions; the code avoids newer syntax).
