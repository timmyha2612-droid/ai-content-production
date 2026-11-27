# Changelog

All notable changes to shotcraft are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/). Rule files carry their own `rules_version` and `checked_at`
dates; rule changes that alter what gets generated are listed here too.

## [Unreleased]

## [0.6.0] - 2026-11-27

### Changed

- **Shot layers** (`board.SHOT_LAYERS`): Character, Wardrobe, Performance, Emotion, Environment, Camera,
  Lighting, Mood, Start frame, End frame. Performance and Emotion keep people from rendering stiff; the
  Environment is written as a place, with its props in it; Transition is gone (cutting belongs to the edit).
  The sample board, the storyboard skill and the cinematographer's notes follow them.
- Start frame and End frame references map to the card's `start_frame` and `end_frame` inputs (frames start as
  generated); on the card they become the opening and closing beats ("opens on ...", "ends on ...").

- **Layer tiers** (`board.LAYER_TIERS`): required (Character, Performance, Environment, Camera, Lighting, Start
  frame), conditional (Wardrobe, Emotion, End frame) and optional (Mood, Sound, Speed, Keep out). `sc.py board
  check` and the app warn when a generated shot misses a required layer; the app folds optional layers away.
- **Cut order follows the tiers** (`rules/taxonomy.json` 0.2.0): mood and texture are trimmed first, then the
  extra place detail, then wardrobe and light colour; the light's direction now stays with the subject, its
  action and the camera move. The generic film-finish line still goes before the shot's own depth details.

### Fixed

- The compiler never trims a field that holds an `@Label` mention, so a long prompt can't silently drop the
  link to a reference image.

## [0.5.0] - 2026-11-27

### Added

- **Blender skill** (`skills/blender`): builds references in Blender once the user connects it themselves. Plans
  in plain words first, builds to the shot's card (lens, 9:16, depth-plane collections, one camera move over
  the exact duration, the look book's key light), renders clay, lit and camera-move versions into
  `00_inputs/blender/`, and puts them on the board.
- `sc.py board add PATH --shot N --attr A [--label L] [--rights owned --user-said "..."]`: an image from disk
  (a Blender render, a photo) onto the board.

### Changed

- **Every generation now waits for the user's yes to its live price**, however small (`confirm_every_generation`
  in the user config, on by default; set it to false to let jobs under the threshold go without asking).
  Estimates say so too. The production designer's Blender route now follows the blender skill.

## [0.4.0] - 2026-11-27

### Added

- **Storyboard app** (`sc.py board init|check|inputs|serve`, `skills/storyboard`): the project as a local web
  app on 127.0.0.1, read from `board/board.json` and the cards. Timeline, director's look book, shot panels
  with each shot's models, settings and compiled prompt, references on every attribute (upload, drop or
  paste), and an Assets tab. Standard library only.
- Board references are project assets in `00_inputs/board/`, reference-only until the user marks them owned,
  licensed or generated. `sc.py board inputs` proposes the matching `card set-input` commands (start frame,
  character, reference, style) for sendable references only.
- **Labels and @ mentions:** every reference has a unique label; cards can mention it as `@Label`, and the
  board resolves mentions into the model's pointers (`@Image1` ... on Seedance) in slot order, with warnings
  for mentions that aren't sent and sent references never mentioned.
- **Shot by shot** (`sc.py shots status|start|pause|lock|unlock`): after the whole board is approved, put any
  batch in progress (shots, ranges, scenes or all). In-progress shots make drafts and finals and keep their
  cards editable while the drafts and finals stages stay closed; a lock needs an approved final and blocks
  generation and card changes until unlocked. The board shows each shot's state and takes, and can start a
  batch, approve, redo, pause, lock and unlock with the words the user types.

### Changed

- `gen` asks `shots.gen_allowed` for the stage gate, and cards of an in-progress shot can be approved or
  edited with the prompts stage closed. Nothing changes for projects that don't start shots.

## [0.3.0] - 2026-11-26

### Added

- Studio interview lighting: 8 `interview_` setups in `rules/light_setups.json` (documentary soft key,
  three-point, high-key white, low-key void, dressed set with practicals, coloured wash, window-style side
  light, podcast and multi-person), from `docs/research/studio-interview-lighting-guide.md`. Every row now
  has a `category` (`cinematic` or `interview`); interview rows add `people`, a `rig` with the practical
  numbers (key, fill, rim, background stops and distance, A/B lenses, contrast) and a 2-3 light
  `small_kit`.
- **Recipes** for files dropped in with a few words (`rules/recipes.json`, read by sc.py only): relight, sky,
  cleanup, background, animate, extend. `sc.py quick recipes --say "..." --file F` picks one from the words
  and the file type; `sc.py quick plan --recipe NAME` sets the model, mode, input role, what must stay and the
  length (matched to the source clip). Each recipe lists unprofiled Higgsfield candidates for model-scout.
- Card field `source_edit` (`edit`, `extend_forward`, `extend_backward`) and named `edit_modes` per model
  (Seedance 2.5 gains video extension).

### Changed

- **Smaller context footprint.** Skill and agent descriptions cut from about 14,500 to about 4,000
  characters. The prompt hook speaks only in a session bound to a shotcraft project and only when the
  prompt reads like a correction; the session-start hook ignores projects opened by other sessions; the
  guard follows the session's own project, or the last opened project only when the work is inside its
  folder; a failed model check is no longer reported as removed models.

### Fixed

- `card set-input --as source` keeps one source; an image card with a start or end frame is refused again.
- Recipes never keep a model that can't make the recipe's output (a video model on a still), and an update
  keeps the recipe (an extension stays an extension).

## [0.2.0] - 2026-11-26

### Added

- **Quick track** (`quick`): one shot, one prompt card, one live price, one yes, then it generates, waits
  and downloads. No intake grilling, no QA agents, no drafts unless asked. New `sc.py quick plan` (sets up
  the project, copies and optionally trims and crops the inputs with `--trim` / `--crop` / `--scale`, refuses
  what submit would refuse, prices it live, spends nothing), `sc.py quick go --user-said` (the user's yes to
  the shown prompt and price approves the card and the spend, then submits, waits and downloads),
  `sc.py quick keep` and `sc.py quick redo`. `go` spends exactly what the latest plan priced (model, takes,
  tier) and only once: the price is claimed before the first job, a higher live price is refused before
  anything is submitted (`gen.submit --max_credits`), and a changed card needs a new plan. `--update` keeps the
  project's inputs and earlier choices. Plain `sc.py gen submit` on a quick project keeps the draft gate. New `quick` skill; the refine skill now offers generation
  through it, and the producer routes "just generate it" requests to it.
- **Editing a source video** (relights, sky changes, restyles): a card input `"as": "source"` sends the
  user's clip as the one video reference in the model's edit mode (`edit_mode` in models.json: Seedance
  2.5 and Cinema Studio 4.0 use `--mode video_edit`). The compiler leaves out camera, framing and beat
  fields (the source sets them) and trims the light fields last. A model with no edit mode is refused.

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

### Fixed

- The price check (`generate cost`) now sends the card's inputs, so modes that need media (video edit,
  omni reference) can be priced and submitted.
- Waiting for a job: `higgsfield generate wait` was called with flags that do not exist
  (`--wait-timeout`, `--wait-interval`), so every wait returned at once while the job still ran. It now uses
  `--timeout` / `--interval` and falls back to polling until the job finishes or the time is up.
- `card set-input --as source` replaces the source and asks for the card's approval again (it changes the
  mode, prompt and price). Uploads get time in proportion to the file size. A wait keeps polling through
  passing errors, stops after 5 failed status checks in a row, and no longer mistakes a "401" in a good answer
  for a sign-in problem.
- Beat timings no longer double the unit ("0-4 ss"), and an on-screen text of "none" adds nothing to the
  prompt.

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
