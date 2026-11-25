# Changelog

All notable changes to shotcraft are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). Rule files carry their own `rules_version` and `checked_at`
dates; rule changes that alter what gets generated are listed here too.

## [Unreleased]

### Added

- Depth planes on prompt cards: `world.background_far`, `world.background_near`, `world.foreground`,
  `world.parallax` and `subject.placement` compile into one depth sentence (far background; background;
  midground; foreground; depth motion), like a multiplane cel set-up. `subject.interaction` says how the
  subject and the place act on each other. The compiler warns when a place has no planes. Image cards skip
  parallax; start-frame cards keep interaction and parallax only.
- Natural finish: `light_look.finish`, a `finish` on every preset (`natural` for live action,
  `true_to_life` for real estate: true colour, slightly uneven motivated light, real-lens character, no wear,
  no lens softness; `clean` for graphics, icons and products), and a `too_perfect` avoid category with
  positive rewrites. The taxonomy holds one finish default per value (`defaults`; `clean` has none), and the
  defaults do not ask for asymmetry. `card new` fills the finish and adds two guards on live-action presets.
  When a look asks for grain, "noise"/"grain" guards are dropped with a warning. When the composition asks
  for symmetry, asymmetry wording and the "perfect symmetry" guard are dropped with a warning.
- Focus-aware "blurry" rewrite: on a shallow-focus shot it becomes "sharp focus on the subject"
  (`blurry (shallow focus)`), not "tack-sharp focus, crisp fine detail".
- `sc.py finish texture` (matched film grain, optional mild vignette; keeps the codec family: H.264 CRF 14,
  ProRes 422 HQ, ProRes 4444 with alpha kept; 8-bit filters; high-quality JPEG and WebP stills) and
  `sc.py finish roomtone` (a single-bed safety floor under the audio, levelled to `--level` dBFS: generated
  pink noise or one neutral `--bed`, for a deliverable that still fails the digital-silence check; per-scene
  beds are laid by the sound stage in the mix). Without `--out`, finish refuses a file inside `09_delivery/`;
  the documented chain is texture to a work file in `08_assembly/`, then roomtone to the final file in
  `09_delivery/`.
- Grain decided at intake (Texture question): `off`, `subtle` or `film`, vignette yes or no, recorded on the
  job card as `Grain:` and passed to the delivery agent. Off with no vignette skips the texture pass.
- Delivery check "no digital silence" (nothing under -90 dB for 0.5 s or longer; the preset or project
  delivery can set `allow_digital_silence`).
- Delivery check "audio covers picture": FAIL when the audio ends 0.5 s or more before the picture.
- `09_delivery/delivery-notes.md`, written by the delivery agent, always carries the AI-label line for
  realistic AI content, whether or not the finish ran (QA item DL-16; new item DL-17 for audio length).
- Composition vocab from `docs/research/cinematic-composition-guide.md`: new `camera.composition` terms
  (one-point perspective, nested frames, low/high horizon, tiny figure in a vast frame, pool of light, colour
  blocking, depth-staged two-shot, eye strip, foreground blocker and more), plus terms for
  `world.background_far`, `background_near`, `foreground`, `parallax`, `subject.placement`,
  `subject.interaction` and `light_look.finish`. "Dutch tilt" now says to use it on purpose, never as
  decoration. "bokeh from string lights" is replaced by "soft out-of-focus string lights at the edge".
- Lighting vocab from `docs/research/cinematic-lighting-guide.md`: new `light_look` terms for `setup`
  (Paramount, short-loop, window chiaroscuro, blinds gobo, candlelight, screen glow key, mixed night street
  light and more), `quality`, `direction`, `color_temp`, `practicals`, `finish` and `palette_grade`. The
  `direction` help now says to always name a side or position. "neon lighting" now ties each colour to its
  sign instead of suggesting magenta and cyan.
- `rules/light_setups.json`: the 16 setups of the lighting chooser, each with intent, the `light_look`
  fields, a finish default, what stays dark, when not to use it and its study board link.
- `flat_light` avoid group ("flat lighting", "lifted shadows", "rim light on both sides", "evenly lit",
  "softbox", "beauty lighting", "HDR") with positive rewrites. The compiler adds its first three at the end of
  the avoid list when `light_look.setup` or `quality` names a low-key family setup, unless the shot is high
  key or overcast. Trigger words live in `negatives.json` `applies_when`. An `applies_when` rule can set its
  own trim `priority`; `flat_light` uses 5, so these guards are trimmed before the card's practicals and
  texture.
- Scene light plans: the director writes one per scene under the shot list; the production designer copies
  it word for word into the environment file's Light section (`Scene light plan (scene <n>):`); the
  cinematographer copies the anchor from there onto every card (PR-36, BI-C14, SL-15). The shot list also
  gets a recommended `composition` column.

### Changed

- The `light_look.mood` term "epic" is now "awe at vast scale": "epic" is a banned trigger word.
- `skills/prompt-craft/references/depth-and-finish.md`, plus updates to the cinematographer,
  production-designer, character-designer, sound, delivery and assistant-editor agents, the director and
  intake, the templates and the QA checklists.

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
