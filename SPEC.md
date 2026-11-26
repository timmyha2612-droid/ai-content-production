# shotcraft — build spec (the contract every file follows)

shotcraft is a public Claude Code plugin (MIT) that works like a professional production crew for AI
content: from research and scripting to the "bible", prompt cards, draft and final generation, motion
graphics, sound, assembly, delivery and hand-off. Higgsfield is the default generation provider. The core
works with any provider; a provider plugs in as an adapter.

This file holds the decisions made with the plugin owner. Every skill, agent, script and hook follows it.
If code and this file disagree, this file wins until it is changed on purpose.

## 0. Principles

1. **The result depends on the request.** "Just a prompt" runs the `refine` track: quick questions, then a
   prompt card. Full production runs the `full` track and ends with a Higgsfield hand-off: the assets
   uploaded, plus a Canvas build sheet. One asset (icon, thumbnail, single shot) runs the `single` track.
2. **Fast by default, grilled where it matters.** For quick work: a complete prompt right away, plus at most
   3 questions, asked only where a wrong guess would waste credits. Deep grilling happens once, at project
   intake. The answers are saved and never asked again.
3. **Spend the least that still meets the use case.** Output is never bigger than the delivery needs.
   Durations are exact. Image first: a risky video starts as a cheap still. Drafts are cheap, finals are
   approved, and upscale happens only if the delivery needs it.
4. **Stages are enforced, not suggested.** Stage gates with evidence (§4), backed by a guard hook (§7).
5. **Creative calls are the user's; checks are the machine's.**
6. **Rights.** Every downloaded reference keeps its source URL and is tagged `reference-only`. It is never
   sent to a model as an input unless the user marks it `owned` or `licensed`.
7. **Never hard-code what can be read live.** Model limits and costs come from the provider (`higgsfield
   model get`, `higgsfield generate cost`). Rule files carry a `checked_at` date for every model.
8. **Hybrid inputs.** The user's own footage, photos, Blender renders and other files go in `00_inputs/`,
   tagged `owned`. Input sources (Blender and others) and output providers are extension points (§10). Build
   nothing for them now, but don't design them out.
9. **Python 3.9+ standard library only** for scripts (no pip installs). Rule files are JSON. Prose is
   markdown. External CLIs are optional and detected: `higgsfield`, `ffmpeg`/`ffprobe`, `yt-dlp`, `node`.
10. **Voice for users:** plain English, short sentences, no jargon without a one-line gloss. Never show
    internal IDs where a name will do.

## 1. Repo layout

```
shotcraft/
  .claude-plugin/plugin.json          name "shotcraft", version, description, author, keywords, license MIT
  .claude-plugin/marketplace.json     a single-plugin marketplace ("shotcraft"), source "./"
  README.md  LICENSE  CHANGELOG.md  SPEC.md  CONTRIBUTING.md
  hooks/hooks.json                    PreToolUse guard, SessionStart model check, UserPromptSubmit lesson nudge
  hooks/guard.py  hooks/session_start.py  hooks/prompt_nudge.py
  scripts/sc.py                       the ONE CLI entry: python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py" <group> <cmd>
  scripts/shotcraft/                  python package (stdlib only)
      __init__.py  paths.py  config.py  jsonio.py
      project.py      project init/open/status, folder layout, active-project registry
      manifest.py     project.json read/write (atomic), assets, generations, decisions
      stages.py       tracks, stage state machine, evidence checks, qa rounds
      rules.py        layered rules loader (plugin < personal < project), deep merge
      cards.py        prompt card parse/write/validate (JSON front matter + markdown body)
      compiler.py     card -> provider-ready prompt for a given model (length limits, avoid->positive)
      routing.py      use case + tier -> model choice, duration fitting, resolution fitting
      budget.py       credit ledger, threshold checks
      refs.py         reference download (yt-dlp / http), tagging, rights checks
      contact_sheet.py  HTML contact sheet for boards/drafts/finals
      delivery.py     ffprobe spec checks against preset/delivery spec
      assembly.py     ffmpeg animatic / string-out from approved shots + timings
      finish.py       natural-finish pass in post: matched film grain (+ mild vignette), room-tone safety floor
      scout.py        compare live model list vs rules/models.json, write scout report
      handoff.py      Higgsfield hand-off package (upload list + Canvas build sheet)
      lessons.py      lessons inbox (append/list/decide)
      providers/__init__.py  base.py  higgsfield.py  fake.py   (fake = test double, no network)
  scripts/tests/                      unittest tests (python3 -m unittest discover -s scripts/tests)
  rules/                              plugin defaults (JSON) — see §6
      taxonomy.json  negatives.json  positive_rewrites.json  models.json  routing.json  presets.json
      tracks.json  stages.json
  skills/<name>/SKILL.md (+ references/, templates/)
  agents/<name>.md
  templates/                          job-card.md, brief.md, prompt-card.md, script-2col.md, shotlist.md,
                                      bible-character.md, bible-environment.md, canvas-build-sheet.md, direction-note.md
```

Skills and agents refer to plugin files as `${CLAUDE_PLUGIN_ROOT}/...` and run scripts as
`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py" ...`.

## 2. User and project files

- `~/.shotcraft/config.json`: `{ "projects_root": str, "provider": "higgsfield", "default_threshold_credits": 50,
  "currency_note": str|null, "first_run_done": bool }`. Created on the first run (the producer asks for
  `projects_root`).
- `~/.shotcraft/rules/`: personal overrides. Same file names as `rules/`, deep-merged over them.
- `~/.shotcraft/sessions/<session_id>.json`: `{ "project": "<abs path>", "opened_at": iso }`. This is
  the active project for this Claude session (`sc.py project open`). Hooks read it from the `session_id`
  in their stdin. If there is no session file, `~/.shotcraft/active.json` is the fallback.
- `~/.shotcraft/scout/last.json`: the result of the last model check (timestamp, new, removed, changed).

Project folder, `<projects_root>/<slug>/`:

```
project.json                 manifest (§3) — written only via sc.py (guard blocks Edit/Write)
00_brief/   brief.md, job-card.md, grilling.md (every question + answer)
00_inputs/  user-provided files (rights: owned unless told otherwise)
01_research/ refs/ (downloads), direction-note.md
02_concept/  concepts.md (2–3 directions), chosen.md
03_script/   script.md (two-column), script.fountain (optional)
04_bible/    characters/ environments/ props/ moodboard/ look.md
05_prompts/  S010.md, S020.md ...  (one prompt card per shot; shots numbered by 10s)
06_generations/ boards/ drafts/ finals/ upscaled/ contact-sheets/
07_sound/
08_assembly/
09_delivery/ deliverables, delivery-notes.md (delivery agent), delivery-report.json (sc delivery check)
10_handoff/  canvas-build-sheet.md, upload-list.json
.shotcraft/  stages.json (guard-protected), qa/<stage>/round-N.json, lessons.md, rules/ (project rules)
```

On the `refine` track a project is optional. `sc.py refine save` writes the card to
`<projects_root>/_refine/<date>-<slug>.md`.

## 3. project.json (schema 1)

```json
{
  "schema": 1,
  "name": "Sydney Dawn Reel", "slug": "sydney-dawn-reel",
  "created": "2026-11-24T10:00:00+11:00",
  "track": "full|single|refine",
  "provider": "higgsfield",
  "use_case": "social-vertical",          // preset id (rules/presets.json)
  "delivery": {"aspect": "9:16", "resolution": "1080x1920", "fps": 30, "duration_s": 15, "formats": ["mp4"]},
  "budget": {"credits": 300, "threshold_single_job": 50, "spent": 0, "reserved": 0},
  "stages_included": ["intake", "..."],     // copy of the track with optional stages removed (user's words in decisions)
  "assets": [
    {"id": "A001", "path": "01_research/refs/x.jpg", "kind": "image|video|audio|3d|doc",
     "rights": "reference-only|owned|licensed|generated", "source_url": "https://...", "note": "...",
     "role": "reference|character|environment|prop|moodboard|input|board|draft|final|upscaled", "shot": "S010"|null,
     "added": iso}
  ],
  "generations": [
    {"id": "G0001", "shot": "S010", "card": "05_prompts/S010.md", "tier": "board|draft|final|upscale",
     "provider": "higgsfield", "model": "seedance_2_5", "params": {}, "prompt": "compiled text",
     "inputs": ["A003"], "cost_estimate": 35, "cost_actual": 35, "job_id": "...",
     "status": "estimated|submitted|completed|failed|nsfw|canceled|ip_detected",
     "outputs": ["06_generations/drafts/S010-d1.mp4"], "approved": null|true|false, "approval_said": "user words",
     "created": iso}
  ],
  "decisions": [{"at": iso, "stage": "concept", "text": "Picked direction B", "user_said": "go with B"}],
  "handoff": {"uploaded": [], "canvas_sheet": "10_handoff/canvas-build-sheet.md"}
}
```

## 4. Tracks and stages (rules/tracks.json, rules/stages.json)

Tracks (in order):

- **full**: intake, research, concept, script, shotlist, bible, prompts, boards, drafts, finals, sound,
  assembly, delivery, handoff, learn
- **single**: intake, prompts, drafts, finals, delivery, handoff, learn
- **refine**: refine   (no generation allowed at all)

Optional stages (the user can drop them at intake, recorded with their words): research, concept,
sound, assembly, boards, handoff. Dropping one is `sc.py stage skip <stage> --user-said "..."`.

Stage table (owner = the role that does the work; gate = what closes it):

| stage | owner | outputs (evidence) | gate |
|---|---|---|---|
| intake | producer | 00_brief/job-card.md with required lines filled; grilling.md | `--user-said` (user confirmed the card) |
| research | researcher agent(s) | 01_research/direction-note.md, ≥1 asset role=reference | QA PASS |
| concept | creative-director skill | 02_concept/concepts.md (≥2 directions), chosen.md | `--user-said` |
| script | screenwriter agent | 03_script/script.md | QA PASS + `--user-said` |
| shotlist | director skill | 03_script/shotlist.md, every shot has id, duration_s, purpose | QA PASS |
| bible | production-designer + character-designer agents | 04_bible/look.md + ≥1 file in characters/ or environments/ | continuity QA PASS + `--user-said` |
| prompts | cinematographer + generation-tech agents | a valid card in 05_prompts/ for every shot on the shot list (single: ≥1 card) | QA PASS (cards validate) |
| boards | generation-tech | ≥1 generation tier=board per video shot that needs image-first; contact sheet | `--user-said` |
| drafts | generation-tech | ≥1 completed draft per shot; contact sheet | continuity QA PASS + `--user-said` |
| finals | generation-tech | a completed final (or upscale) per approved shot, all approved | `--user-said` |
| sound | sound agent | files in 07_sound/ + licence notes | `--user-said` |
| assembly | assistant-editor agent | 08_assembly/animatic.mp4 or EDL/notes | `--user-said` |
| delivery | delivery agent | 09_delivery/ files + delivery-notes.md (always with the AI-label line for realistic AI content) + delivery-report.json with all checks PASS | spec check PASS |
| handoff | producer (handoff skill) | 10_handoff/canvas-build-sheet.md + upload-list.json | evidence only |
| learn | learner agent → producer | lessons decided (each accepted/rejected with the user's words) | `--user-said` |
| refine | refine skill | a valid prompt card saved | evidence only |

State machine (`.shotcraft/stages.json`): each stage is `pending|open|done|skipped`, with `opened_at`,
`done_at`, `evidence`, `user_said`, and `qa_rounds`.
- `start` is refused unless every earlier included stage is done or skipped. Only one stage is open at a
  time.
- `done` checks the evidence itself; it never takes evidence on trust.
- `reopen <stage>` sets that stage to open and every later stage back to pending, keeping their history.
- `skip` needs `--user-said` and the stage must be optional (or the user's words must name the stage).

QA rounds: `sc.py qa record --stage S --round N --verdict PASS|FAIL --findings <json file>` writes
`.shotcraft/qa/<stage>/round-N.json`. There are at most 3 rounds; after round 3 FAILs, the producer
escalates to the user, and the user's words can close the stage (`--user-said`, with the QA override noted).

CLI (all print JSON with `--json`, otherwise human text; exit code 0 = ok, 2 = refused, 1 = error):

```
sc.py setup [--projects-root DIR]                 first-run config + `doctor`
sc.py doctor                                       which CLIs exist, auth status, versions, config sanity
sc.py project init --name N --track T [--use-case U] [--budget C] [--threshold C] [--root DIR]
sc.py project open PATH [--session-id ID]          register active project for this session
sc.py project status [--project P]
sc.py stage status|start|done|skip|reopen [STAGE] [--project P] [--user-said "..."] [--note "..."]
sc.py qa record ... | sc.py qa status --stage S
sc.py card new --shot S010 [--from-text "..."] | card validate PATH | card compile PATH --model M [--json]
sc.py route --use-case U --tier draft|final|upscale [--kind image|video] [--duration 6] [--needs audio,refs,end_frame]
sc.py budget status | budget check --credits N
sc.py gen estimate CARD --tier T [--model M]       (calls provider cost; records status=estimated)
sc.py gen submit CARD --tier T [--model M] [--variants N] [--user-said "..."] [--wait]
sc.py gen status|fetch GEN_ID
sc.py gen approve GEN_ID --user-said "..." | gen reject GEN_ID --user-said "..." [--note]
sc.py asset add PATH --rights R --role ROLE [--source-url U] [--shot S] | asset list | asset mark ID --rights R --user-said "..."
sc.py refs fetch URL [--note] [--shot]             download into 01_research/refs, tagged reference-only
sc.py sheet build --tier board|draft|final [--open]
sc.py delivery check [--spec preset-id]           incl. "no digital silence" and "audio covers picture"
sc.py finish texture FILE [--grain off|subtle|film] [--vignette] [--out P]   matched grain, one setting per job
sc.py finish roomtone FILE [--bed FILE] [--level -60] [--out P]           single-bed safety floor under the audio
                   (paths relative to the current directory; without --out, finish refuses a FILE in 09_delivery/)
sc.py assembly animatic [--audio file]
sc.py scout check [--json] | scout report
sc.py handoff build | handoff upload [--dry-run]
sc.py lessons add "text" [--kind general|project|model] | lessons list | lessons decide N accept|reject --user-said "..."
sc.py refine save CARD_TEXT_FILE                   refine-track save
```

## 5. Prompt card (05_prompts/S010.md)

A JSON front matter block between `---` lines, followed by a markdown body:

```
---
{
  "id": "S010", "title": "Dawn drone reveal", "kind": "video|image",
  "use_case": "social-vertical", "tier_plan": ["board", "draft", "final"],
  "model": {"draft": "seedance_2_0", "final": "seedance_2_5", "upscale": null},
  "settings": {"aspect": "9:16", "resolution": "1080p", "duration_s": 6, "variants": 2, "audio": false},
  "handles_s": 0.5,
  "inputs": [{"asset": "A003", "as": "start_frame|end_frame|reference|character|style"}],
  "layers": {
    "intent":   {"use": "...", "platform": "...", "audience": "...", "brand": "..."},
    "subject":  {"subject": "...", "action": "...", "placement": "...", "interaction": "...",
                 "wardrobe_props": "...", "elements": "...", "consistency": "..."},
    "world":    {"environment": "...", "background_far": "...", "background_near": "...", "foreground": "...",
                 "parallax": "...", "era": "...", "time_of_day": "...", "weather_season": "...", "atmosphere": "..."},
    "camera":   {"shot_size": "...", "angle": "...", "lens": "...", "dof": "...", "composition": "...",
                 "movement": "...", "movement_speed": "...", "camera_look": "..."},
    "light_look": {"setup": "...", "quality": "...", "direction": "...", "color_temp": "...", "practicals": "...",
                   "palette_grade": "...", "texture": "...", "finish": "...", "style_ref": "...", "mood": "..."},
    "time_output": {"beats": [{"t": "0-2", "what": "..."}], "pacing": "...", "loop": false,
                    "transition_in": "...", "transition_out": "...", "audio": "...", "on_screen_text": "..."}
  },
  "avoid": ["camera shake", "warped text"],
  "status": "draft|approved|generated|final",
  "approved_said": null,
  "rationale": {"model": "...", "resolution": "...", "duration": "..."},
  "checked_rules_version": "0.1.0"
}
---
## Prompt (compiled for <model>)
...paste-ready text...

## Avoid (guarded against)
...
## Beats
...
## Why these settings
...
```

`card compile` takes the layers and produces the prompt text for a model, following §6:
- Order: subject+action (+ interaction) → world → depth → camera → light & look → time/beats → style.
- Depth (the frame built like a multiplane cel set-up): one sentence of `world.background_far`;
  `world.background_near`; `subject.placement` (the midground); `world.foreground`; `world.parallax`, joined
  with "; " and labelled ("far background: …") unless the text already names the plane.
  `subject.interaction` (how the subject and the place act on each other: light, weather, contact, scale)
  follows the action. Image cards skip parallax. With a start frame only interaction and parallax are kept
  from these. When `world.environment` is set but no foreground or background plane is, compile warns.
- `light_look.finish` is the finish for live-action looks; empty for clean ones. The taxonomy field holds one
  default per preset finish value (`defaults`: `natural`, `true_to_life`; `clean` has none). The defaults do
  not ask for asymmetry, and a card whose composition is symmetric drops asymmetry wording (the "perfect
  symmetry" guard and its rewrite). The "blurry" avoid item is focus-aware: on a shallow-focus card it is
  rewritten through `blurry (shallow focus)` ("sharp focus on the subject") instead of the tack-sharp
  rewrite, so it does not fight the soft background. When texture or finish asks for grain, "noise"/"grain" avoid items
  are dropped with a warning (they would fight the look).
- Stay under the model's `max_prompt_words` (default 120 words, roughly 200 tokens). Drop the
  lowest-priority fields first: texture, then practicals, then era, then camera_look (the depth fields sit
  between: finish 47, parallax 49, far background 53, near background 61, foreground 67, interaction 73,
  placement 75).
- For image-to-video with a start frame, describe only the motion (camera + subject motion + beats), not the
  frame again.
- `avoid` goes into the model's negative field if `negative_prompt: true`; otherwise each item is rewritten
  through `positive_rewrites.json` into positive wording inside the prompt. Items with no rewrite are
  listed as `unguarded` in the compile output.
- The output also includes the provider params (aspect, resolution, duration, refs) validated against the
  model profile. Out-of-range values are corrected and reported (`adjustments`).

## 6. Rule files (rules/*.json; personal and project layers deep-merge over them)

- `taxonomy.json`: the 6 layers. Each field has `label`, `help` and `vocab` (a list of terms with a short
  `means`), plus `priority` (used for trimming). Vocabulary must be rich and professional: shot sizes
  (EWS…ECU, insert, OTS, POV, two-shot…), angles, lenses (focal lengths, anamorphic, macro, fisheye,
  tilt-shift), DOF, composition (rule of thirds, centre-punch, symmetry, leading lines, negative space,
  frame-in-frame, Dutch), movements (static/locked-off, pan, tilt, dolly in/out, truck, pedestal, crane/jib,
  boom, arc/orbit, push-in, pull-out, dolly zoom, crash zoom, whip pan, handheld, Steadicam/gimbal, FPV
  drone, aerial top-down, bullet time, rack focus, snorricam, hyperlapse, timelapse), speed and easing,
  lighting setups (Rembrandt, butterfly, split, loop, broad/short, high/low key, motivated, practical,
  silhouette, backlight/rim, volumetric, neon, golden/blue hour, overcast), colour temperatures, palettes
  and grades, film stocks and textures, genres and styles, moods, atmosphere and FX, transitions, motion
  graphics styles (flat, isometric, kinetic type, glassmorphism, 3D clay, line art, liquid motion, glitch,
  particles), and audio terms.
- `negatives.json`: `{ "universal": [...], "by_category": {"people": [...], "text": [...], "product": [...],
  "motion": [...], "locked_off": [...], "loop": [...], "mograph": [...], "icon": [...], "too_perfect": [...]},
  "by_model": {"<model>": [...]} }`. `too_perfect` (strongest first) guards against the over-perfect AI
  finish; `card new` adds its first two items on presets whose `finish` is `natural`. `flat_light` guards a
  low-key look against drifting back to flat, even studio light. `applies_when` holds guards the compiler
  adds on its own: `{"<group>": {"fields": [...], "any": [...], "unless_fields": [...], "unless": [...],
  "add": n, "priority": p}}`. When a listed field holds an `any` word and no `unless` word appears, the first
  `add` terms of `by_category.<group>` go at the end of the avoid list (never twice). The optional `priority`
  is the trim priority of their prompt rewrites (default: the taxonomy's `trim.guard_priority`), and these
  guards are never among the protected first two; `flat_light` uses 5, so it is trimmed before
  `light_look.texture` (10) and `light_look.practicals` (20). `flat_light` fires on low-key
  family setups (low key, split, Rembrandt, "short lighting" named as such, practicals, top light, firelight, night exterior,
  chiaroscuro) in `light_look.setup` or `quality`, but not on high key or overcast. The trigger words live
  in the rule file, not in code. `card new` cannot add these: `setup` is filled after the card is made.
- `light_setups.json`: 24 lighting setups. `category` says where a row comes from: 16 `cinematic` rows (the
  quick chooser of `docs/research/cinematic-lighting-guide.md`) and 8 `interview` rows (the studio setups of
  `docs/research/studio-interview-lighting-guide.md`, ids starting `interview_`). Each has `id`, `name`,
  `category`, `intent` (list), `setup`, `quality`, `direction`, `color_temp`, `practicals`, `finish` (a
  default), `stays_dark` (what the card must say falls into darkness), `do_not_use_when` (list), `low_key` (true
  when the setup text triggers the `flat_light` guards) and `board_url` (the Cosmos study board with reference
  frames). Interview rows add three optional fields. `people` is a number or a `[min, max]` range. `rig` holds
  the practical numbers for a crew brief: `key` (`source`, `side`, `angle`, `height`, `distance_m`, `kelvin`),
  `fill` (often negative fill: a black panel that soaks up bounce), `rim`, `background` (`stops_vs_face`,
  `subject_distance_m`, `notes`), `camera` (`a_mm`, `b_mm`, `aperture`, `eyeline`) and `contrast_ratio`.
  `small_kit` is the same look with 2-3 lights, one line per light. Ranges are `[min, max]`. The rig is for
  planning, not for the prompt. The cinematographer picks the row whose intent fits the shot (filtering on
  `category`) and copies the fields into `light_look`, adding the side of frame.
- `positive_rewrites.json`: `{ "<avoid term>": "<positive phrasing>" }`, for example "camera shake" →
  "locked-off tripod shot, perfectly stable frame".
- `models.json`: `{ "rules_version": "...", "providers": { "higgsfield": { "surface": "cli", "models": { "<id>":
  { "name": "Seedance 2.5", "kind": "video|image|upscale|audio|3d|utility", "vendor": "...",
  "durations": [..]|{"min":4,"max":30}, "resolutions": [...], "aspects": [...], "start_frame": bool,
  "end_frame": bool, "refs": {"image": n, "video": n, "audio": n}, "audio": bool, "negative_prompt": bool,
  "seed": bool, "max_prompt_words": 120, "variants": ["std","fast"], "strengths": [...], "weaknesses": [...],
  "gotchas": [...], "checked_at": "2026-11-24", "source": "..." } } } } }`. Seed it from the Higgsfield CLI's
  MODELS.md and model catalogue (see the research notes in `docs/research/`). Mark anything unconfirmed.
- `routing.json`: `{ "use_cases": { "<need>": { "draft": [model ids in fallback order + params], "final": [...],
  "upscale": [...], "notes": "..." } }, "image_first": { "rule": "...", "applies_when": [...] } }`. Needs
  include: icon-logo, graphic-with-text, photoreal-people, product-environment-still, video-general,
  video-motion-physics, video-dialogue-audio, video-cinematic-multishot, mograph-loop, storyboard-frame.
- `presets.json`: use-case presets, each with `aspect`, `resolution` (draft and final), `fps`,
  `duration` (typical / min / max), `handles_s`, `delivery_formats`, `need` (a routing key), `notes`,
  `finish` (`natural` for live action; `true_to_life` for real estate: true colour, slightly uneven motivated
  light, real-lens character, no wear, no lens softness; `card new` fills `light_look.finish` from the taxonomy
  field's `defaults` for that value; `clean` for graphics, icons and products, left empty), optional `allow_digital_silence` (skips the delivery
  check for pure digital silence).
  Includes: social-vertical (reel/story/TikTok), social-square, social-landscape, youtube, youtube-short,
  thumbnail, icon-ui (small sizes, SVG preferred), logo-animation, web-hero, banner-ad sizes, broll-insert
  (16:9 or matching the edit, with handles), real-estate, product-shot, storyboard-animatic, billboard-print,
  presentation. The 3 tuned first: social-vertical, broll-insert, thumbnail.
- `tracks.json` / `stages.json`: §4 as data. stages.py reads these; it never hard-codes them.

## 7. Hooks

`hooks/guard.py` (PreToolUse; matchers: `Bash`, `Write|Edit|MultiEdit|NotebookEdit`, `mcp__.*[Hh]iggsfield.*`).
It exits with code 2 and a reason to block; otherwise it exits 0.
- Raw generation is blocked. A Bash command running `higgsfield generate create`, `higgsfield generate`
  followed by anything other than `cost|list|get|status|wait`, `higgsfield upscale`, or `higgsfield
  soul-id create` must go through `sc.py gen ...`. The block message says so. Reads (`higgsfield model
  list/get`, `generate cost`, `account`, `auth status`) pass.
- An MCP higgsfield tool whose name contains generate, create, upscale, edit, train or upload is blocked
  while a project is active (use `sc.py gen`). When no project is active, it passes with a stderr note.
- `sc.py gen submit` is allowed through the guard, but `sc.py` enforces the gates itself: the right stage
  is open (board→boards, draft→drafts, final/upscale→finals; on the refine track never); the card
  validates and its status is approved (for final, at least one approved draft or `--user-said`);
  `budget.check` passes (over the threshold or over the remaining budget needs `--user-said`); and no
  input asset has rights `reference-only`.
- Edit or Write to `project.json` or anything under `.shotcraft/stages.json` / `.shotcraft/qa/` is blocked.
  These change only through `sc.py`.
- Writing into a stage folder before its stage is open is blocked (folder→stage map below), when a project is
  active and the path is inside it. `00_inputs/` and `.shotcraft/lessons.md` are always allowed.
  Map: 00_brief→intake, 01_research→research, 02_concept→concept, 03_script/script*→script,
  03_script/shotlist*→shotlist, 04_bible→bible, 05_prompts→prompts (also refine), 06_generations/boards→boards,
  drafts→drafts, finals|upscaled→finals, 07_sound→sound, 08_assembly→assembly,
  09_delivery→delivery, 10_handoff→handoff. A stage marked `done` is writable only if it is reopened.
- Fail open when there is no active project, except that raw generation is always routed through `sc.py`.
  The guard never crashes a tool call: on an internal error, print a note and exit 0.

`hooks/session_start.py` (SessionStart):
- If `higgsfield` exists and `~/.shotcraft/scout/last.json` is older than 20 h, run `sc.py scout check`
  with a 12 s timeout.
- Print one line when models are new, removed or changed: "N new Higgsfield models since <date> — say
  'run model-scout' to review".
- Also flag routing rows whose `checked_at` is older than 30 days.
- Print the active project and its open stage if a session file exists.
- Silent on any failure.

`hooks/prompt_nudge.py` (UserPromptSubmit): when a project is active, add a short reminder: "If the user
just corrected or explained a preference, log it: sc.py lessons add ...". Keep it under 200 characters.

## 8. The crew (skills talk to the user; agents do heavy, parallel or fresh-eyes work)

Skills (`skills/<name>/SKILL.md`):
| skill | role |
|---|---|
| producer | THE HUB. Entry point for any shotcraft production. First run/setup, track choice, intake grilling, job card, budget, running stages via `sc.py stage`, routing work to the crew, every user approval, QA loop, escalation. The map of every other skill and agent. |
| refine | Quick prompt refinement (refine track). Up to 3 questions, then a prompt card compiled for the chosen model, avoid list, settings and reasons. Also handles "refine this prompt" with no project. |
| creative-director | Concept stage: 2–3 directions from the brief and research. Presents them and records the user's pick. |
| director | Shot list stage (and the light version for single shots): beats, shot purpose, coverage, exact durations, image-first flags, continuity notes. |
| review | Contact sheet review for boards, drafts and finals: builds the sheet, collects approve/reject/adjust in chat, records it with the user's words, and sends rejections back to the right crew member. |
| handoff | Higgsfield hand-off: uploads approved assets, writes the Canvas build sheet, and offers browser-assisted Canvas setup (Claude in Chrome) on the Mac. Watches for a Canvas API. |
| learn | End-of-job learning: runs the learner agent and puts the rule proposals to the user. Writes only to personal or project rules. |
| model-scout | Runs the model-scout agent, presents proposed routing and models changes, and applies the approved ones to personal rules (or proposes a PR to the plugin). |
| prompt-craft | Reference skill: the 6-layer taxonomy, the vocabulary, the negatives system, per-model prompting notes, Higgsfield prompting rules. Loaded by refine/director/agents. |

Agents (`agents/<name>.md`, frontmatter `name`, `description`, `tools` or `disallowedTools`, `color`):
researcher, screenwriter, production-designer, character-designer, cinematographer, generation-tech,
script-supervisor (continuity QA), sound, assistant-editor, delivery, qa-supervisor,
qa-verifier, learner, model-scout.

Each agent file states what it gets in the prompt (project path, stage, shot ids, round), the files it must
read, exactly what it writes (paths), the `sc.py` commands it may run, what it must never do, and its return
format (JSON-shaped summary). Agents never talk to the user, never approve anything, never edit
`project.json` by hand, and never run raw `higgsfield generate`.

How they work together:

```
producer ─ intake ─► researcher×N ─► creative-director ─► screenwriter ─► director
          ─► production-designer ∥ character-designer ─► script-supervisor
          ─► cinematographer ─► generation-tech (cards) ─► boards ─► review ─► drafts ─► script-supervisor ─► review
          ─► finals ─► sound ─► assistant-editor ─► delivery ─► handoff ─► learn
qa-supervisor + qa-verifier after every building stage (max 3 rounds).
```

## 9. Higgsfield provider (providers/higgsfield.py)

- Surface: the official CLI `higgsfield` (npm `@higgsfield/cli`, login via `higgsfield auth login`, plan
  credits). Exact subcommands and flags MUST be taken from the CLI's README/MODELS.md (a copy is in
  `docs/research/higgsfield-cli/`). Use `--json` wherever the CLI supports it.
- The interface (`providers/base.py`): `available()`, `auth_status()`, `list_models()`, `get_model(id)`,
  `estimate(model, params) -> credits`, `submit(model, prompt, params, inputs) -> job_id`, `status(job_id)`,
  `wait(job_id, timeout)`, `download(job_id, dest_dir) -> [paths]`, `upload(path) -> url_or_id`.
- Handle the statuses queued, in_progress, completed, failed, nsfw, canceled and ip_detected. Back off on
  429 and captcha HTML (wait 30 s, max 3 tries).
- Download outputs immediately; provider URLs may expire.
- `fake.py` implements the same interface deterministically for tests.
- REST API (`api.higgsfield.ai`, separate USD billing) is a documented optional mode in README. Not built.

## 9a. Natural finish in post (finish.py)

- `finish texture`: ffmpeg `noise` (temporal + uniform) at one fixed strength per job (`subtle` 6, `film` 12)
  and an optional mild `vignette`. Video is re-encoded at high quality in its codec family: H.264 CRF 14
  (VP9 for .webm); in a .mov whose source is ProRes or deeper than 8-bit, ProRes 422 HQ, or 4444 with the
  alpha kept when the source has alpha. The noise and vignette
  filters work in 8-bit, so a 10-bit source is filtered at 8-bit precision. Audio is copied when the container can hold it, otherwise re-encoded (with a note). Stills work too;
  JPEG and WebP are written at high quality. Never overwrites the source. The grain setting comes from the
  job card's `Grain:` line (decided at intake); with `off` and no vignette, texture is skipped.
- `finish roomtone`: a single-bed safety floor for a deliverable that still fails the digital-silence check:
  one bed under the existing audio (`amix`, no normalising, so the mix is untouched), levelled to `--level`
  dBFS (-80 to -40, default -60) by measuring its mean volume: one neutral `--bed` (looped), else generated
  pink noise, low-passed. The picture is copied. The result is re-checked for digital silence (exit 2 if any
  remains). Per-scene room tone and ambience beds are laid by the sound stage in the mix or the assembly.
- Paths are relative to the current directory. Without `--out`, finish refuses a FILE inside `09_delivery/`
  (work files left there fail the delivery check). The chain: `texture --out` a work file outside `09_delivery/`
  (`08_assembly/`, or a scratch folder as the delivery agent uses), then `roomtone` on that file `--out` the
  final file in `09_delivery/`.
- Delivery check "no digital silence": `silencedetect` at -90 dB for 0.5 s or longer on every file with
  audio; FAIL lists the ranges and points to `finish roomtone`. `allow_digital_silence: true` (preset or
  project `delivery`) skips it with a note.
- Delivery check "audio covers picture": a file whose audio stream ends 0.5 s or more before its video FAILs (the
  end would play in dead silence).
- `09_delivery/delivery-notes.md` is written by the delivery agent (the checker skips .md). It always carries
  the AI-label line for realistic AI content, whether or not the finish ran.
- This is a craft fix for a natural look, not a way to hide that work is AI-made or to beat AI detectors. It
  never crops or covers a watermark. Content Credentials (C2PA) do not survive an edit or an ffmpeg re-encode,
  so the delivery note says realistic AI content needs the platform's AI label when posted.

## 10. Extension points (design only)

- Motion graphics are out of scope (removed 2026-11-25): they are built in the user's own motion graphics
  tool. shotcraft hands over the shot list's `graphics` column and leaves clean frame space for them.

- `providers/`: other generators (Artlist, fal, Runway, …) follow `base.py`.
- Input sources: Blender (via a Blender MCP), the user's own shoots, After Effects renders. They land in
  `00_inputs/` with rights `owned` and a `source` note. The production-designer agent may plan an
  environment as "Blender blockout → render → use as start frame / reference".
- Canvas: when Higgsfield exposes a Canvas API, `handoff.py` gains `build_canvas()`. Until then it writes the
  build sheet.

## 11. Testing

`python3 -m unittest discover -s scripts/tests -v` must pass with no network and no `higgsfield`. Cover: rules
merge, card parse/validate/compile (length trimming, avoid rewriting, start-frame motion-only, param
correction, the depth sentence, the natural finish and the grain clash), light rules (`light_setups.json`
keys, `flat_light` guards added on low-key setups and not on high key or overcast and trimmed before the
practicals, new vocab present and no banned trigger word in it, rule
files still round-trip with `json.dumps(indent=2, ensure_ascii=False)`), routing (duration fitting picks a
model whose durations fit; image-first flag), stages (order, evidence, skip, reopen, QA rounds, refine track
blocks gen), budget threshold, guard decisions (feed hook JSON on stdin), the fake provider gen flow end to
end, refs rights enforcement, contact sheet HTML generation, and (with ffmpeg) finish texture/roomtone and the
digital-silence check. Storyboard: board.json validation, reference rights and labels, the inputs plan, @ mention
resolution, and the local server's token, host and upload checks. Shot by shot: selections, the board
gate, draft to final to lock with stages closed, locks blocking generation and card edits, and the board's
progress, takes and actions.

## 12. Storyboard (board.py, board_server.py, scripts/board/app.html)

A local web app over a project, for reading the script shot by shot and collecting references. It is a view:
it never writes a card, opens a stage or generates.

- **Text:** `<project>/board/board.json` (title, facts, worlds, look book, shots, notes). Claude writes it
  from the script, shot list and bible; `sc.py board check` validates it.
- **Higgsfield side:** read live from each shot's card in `05_prompts/` (models per tier, settings, the prompt
  compiled for the final model as a dry run).
- **References:** uploaded images go to `00_inputs/board/` and into `project.json` as assets with a `board`
  key `{shot, attr, name, label}` (shot 0 is the look book). A new reference is `reference-only`; a frame
  still is `generated`. Rights change only by the user's tap on the board, recorded through
  `manifest.mark_asset`. A reference a card or a generation uses can't be removed.
- **Attribute to card input:** Frame → `start_frame`; Character → `character`; Wardrobe, Props,
  Environment → `reference`; Lighting, Mood, Camera and the look book's Visual worlds, Palette, Light and
  texture, Moodboard → `style`; anything else is not sent. `sc.py board inputs` lists the matching
  `card set-input` commands for sendable references only; the producer runs them with the user's words.
- **@ mentions:** each reference has a unique label. A card field may mention one as `@Label`; the board
  resolves mentions against the shot's sendable references in slot order (character, reference, style) into
  the model's pointer (`MENTION_STYLE`, `@Image{n}` for Seedance) or plain words, and warns about mentions
  of references that aren't sent and sent references never mentioned. The card keeps `@Label`.
- **Server:** stdlib `http.server` on 127.0.0.1 only. Every request needs the per-run token (header or `?t=`)
  and a localhost `Host`, so other web pages can't read or post to it. Uploads are images only (no SVG),
  20 MB at most, with sanitised file names.

## 13. Shot by shot (shots.py)

After the boards stage is done (or prompts, on a track with no boards), the user may put any batch of shots
in progress: shot ids, ranges (`S010-S040`), scenes (a `scene` column in the shot list, or `scene` in
board.json) or all. State lives in `.shotcraft/shots.json` (sc.py only; the guard blocks it).

- An in-progress shot may make draft, final and upscale takes while the drafts and finals stages are closed
  (`gen.gates` asks `shots.gen_allowed`), and its own card stays editable and approvable. Board takes still
  follow the boards stage.
- `lock` needs an approved final (or upscale) of the shot and the user's words; it records the take. A locked
  shot makes nothing and its card can't change, even with a stage open, until `unlock` with the user's words.
- States derive from the generations: ready, in progress, draft running, draft to review, draft approved,
  final running, final to review, final approved, locked (plus paused and waiting).
- The storyboard shows each shot's state and takes (`/gen/<id>/<n>` serves outputs) and can start a batch,
  approve or reject a take, pause, lock and unlock. Every action carries the words the user typed on the
  board; an empty field is refused. Generation itself never starts from the board.
- The drafts and finals stages still close the usual way, with their evidence, once every shot is locked.

