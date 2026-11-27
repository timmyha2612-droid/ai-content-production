# shotcraft

A production crew for AI video and images, as a Claude Code plugin.

shotcraft works the way a professional crew does: a producer runs the job, a researcher, screenwriter,
director, designers, a cinematographer and a generation tech each do their part, a supervisor checks
continuity, and nothing moves to the next stage until the work is there and you have said yes. Higgsfield is
the default generator. Other providers can plug in.

What you get depends on what you ask for:

| You ask for | Track | You get |
|---|---|---|
| "Just a prompt" ("write me a Higgsfield prompt for...", "refine this prompt") | `refine` | A complete prompt card right away, at most 3 quick questions, compiled for the model you will use, with settings and the reasons for them. No credits spent. |
| "Just generate it" (one shot now: a relight, a clip, a still) | `quick` | One prompt card, the live price, one yes, then it generates, waits and downloads. No intake, no QA agents, no drafts unless you ask. |
| One asset (an icon, a thumbnail, a single shot) | `single` | A short intake, a prompt card, cheap drafts, an approved final that matches the delivery spec, and the hand-off. |
| A full piece (a reel, an ad, an explainer, a short film) | `full` | Research to hand-off: brief, concept, script, shot list, bible, cards, boards, drafts, finals, motion graphics, sound, an animatic, delivery checks, and a Higgsfield hand-off with every approved asset uploaded and a Canvas build sheet. |

## Contents

- [How it works](#how-it-works)
- [The crew](#the-crew)
- [Tracks and stage gates](#tracks-and-stage-gates)
- [Install](#install)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Your own material (hybrid inputs)](#your-own-material-hybrid-inputs)
- [Configuration and rule layers](#configuration-and-rule-layers)
- [How model updates work](#how-model-updates-work)
- [The storyboard app](#the-storyboard-app)
- [The Higgsfield hand-off and the Canvas limitation](#the-higgsfield-hand-off-and-the-canvas-limitation)
- [The Higgsfield REST API (optional, not built)](#the-higgsfield-rest-api-optional-not-built)
- [Works alongside Higgsfield's official plugin](#works-alongside-higgsfields-official-plugin)
- [The command line](#the-command-line)
- [Roadmap](#roadmap)
- [Contributing and licence](#contributing-and-licence)

## How it works

Six ideas run through the whole plugin:

1. **Fast by default, grilled where it matters.** Quick work gets a complete answer at once. A project gets
   one deep intake interview at the start; the answers go on a job card and are never asked again.
2. **Spend the least that still meets the use case.** Output is never bigger than the delivery needs.
   Durations are exact. Risky video starts as a cheap still ("image first"). Drafts are cheap, finals are
   approved by you, and upscaling happens only when the delivery needs it. Every job checks the live cost
   first and shows you the price of every generation, waiting for your yes, however small. It also flags
   anything over your single-job threshold or the project budget.
3. **Stages are enforced, not suggested.** Each stage closes only when its evidence exists (checked by
   code, not taken on trust) and its gate is met: a QA pass, your words, or a spec check. A guard hook stops
   files being written into a stage that is not open, and routes every generation through the budget and
   rights checks.
4. **Creative calls are yours; checks are the machine's.** Agents never approve anything. Every approval is
   recorded with your own words.
5. **Rights are tracked.** Every downloaded reference keeps its source link and is tagged `reference-only`.
   It is never sent to a model as an input unless you mark it `owned` or `licensed`.
6. **Shot, not generated.** Every live-action frame is built in planes, the way a multiplane cel set-up
   was: far background, near background, the subject in the midground, then a foreground, plus how each
   plane moves. Each card also says how the subject and the place act on each other (light, weather,
   contact, scale), so the subject never looks pasted in. A natural finish guards against the too-perfect
   AI look: lived-in detail, motivated light and real-lens character in the prompt (`natural`, or
   `true_to_life` for real estate: true colour and real-lens character, no wear), per-scene room tone in the
   sound mix, matched film grain and a room-tone safety floor in post, and delivery checks that fail pure
   digital silence and audio that ends before the picture. This is a craft fix
   for a natural look, not a way to hide that the work is AI-made or to beat AI detectors. shotcraft never
   crops or covers a watermark. Content Credentials (C2PA) do not survive an edit or an ffmpeg re-encode,
   so realistic AI content still needs the platform's own AI label when you post it.

## The crew

Skills talk to you. Agents do heavy, parallel or fresh-eyes work and report back to the producer.

```
producer ─ intake ─► researcher×N ─► creative-director ─► screenwriter ─► director
          ─► production-designer ∥ character-designer ─► script-supervisor
          ─► cinematographer ─► generation-tech (cards) ─► boards ─► review ─► drafts ─► script-supervisor ─► review
          ─► finals ─► sound ─► assistant-editor ─► delivery ─► handoff ─► learn
qa-supervisor + qa-verifier after every building stage (max 3 rounds).
```

`─►` means "then", `∥` means "at the same time", `×N` means several in parallel.

**Skills** (you talk to these)

| Skill | What it does |
|---|---|
| producer | The hub and the entry point. First-run setup, choosing the track, the intake interview, the job card, the budget, running every stage, sending work to the crew, every approval, the QA loop. |
| refine | "Just a prompt." Up to 3 questions, then a prompt card compiled for the chosen model. Works with no project. |
| creative-director | Two or three concept directions from the brief and research; records your pick. |
| director | The shot list: beats, what each shot is for, exact durations, which shots start as a still, continuity notes. |
| review | Contact sheets for boards, drafts and finals. Collects approve, reject or adjust, and sends rejections to the right crew member. |
| handoff | Uploads approved assets to Higgsfield and writes the Canvas build sheet. |
| learn | End-of-job learning: turns your corrections into rule proposals, and changes rules only after your yes. |
| model-scout | Reviews new or changed Higgsfield models and proposes routing changes. |
| storyboard | Opens the project as a local web app: timeline, look book, shot panels, references with @labels, an assets tab and each shot's Higgsfield prompt. |
| blender | Builds references in Blender (once you connect Blender yourself): sets, subject and camera motion, and renders matched to the shot's card, saved onto the board. |
| prompt-craft | Reference: the six-layer prompt structure, the vocabulary, the negatives system, per-model notes. |

**Agents** (the producer spawns these): researcher, screenwriter, production-designer, character-designer,
cinematographer, generation-tech, script-supervisor (continuity QA), sound, assistant-editor,
delivery, qa-supervisor, qa-verifier, learner, model-scout.

## Tracks and stage gates

| Track | Stages, in order |
|---|---|
| full | intake, research, concept, script, shotlist, bible, prompts, boards, drafts, finals, sound, assembly, delivery, handoff, learn |
| single | intake, prompts, drafts, finals, delivery, handoff, learn |
| quick | quick (plan and price, one yes, generate, keep or redo) |
| refine | refine (no generation at all) |

On the quick track, drop in a clip or still with a few words ("refine this", "clean up the bins", "nicer sky") and the matching recipe sets the model and mode.

Optional stages, which you can drop at intake (your words are recorded): research, concept, boards,
sound, assembly, handoff. Motion graphics and sound may run at the same time; otherwise one stage is open at
a time.

| Stage | Who does it | What must exist | What closes it |
|---|---|---|---|
| intake | producer | `00_brief/job-card.md` with Goal, Audience, Use case, Delivery and Budget filled; `grilling.md` | your words |
| research | researcher agents | `01_research/direction-note.md`, at least one reference | QA pass |
| concept | creative-director | `02_concept/concepts.md` (2 or more directions), `chosen.md` | your words |
| script | screenwriter | `03_script/script.md` (two-column) | QA pass + your words |
| shotlist | director | `03_script/shotlist.md`: every shot has an id, a duration and a purpose | QA pass |
| bible | production-designer, character-designer | `04_bible/look.md` + a character or environment file | continuity QA pass + your words |
| prompts | cinematographer, generation-tech | a valid prompt card for every shot | QA pass |
| boards | generation-tech | a still for every shot marked image-first; a contact sheet | your words |
| drafts | generation-tech | a draft for every shot; a contact sheet | continuity QA pass + your words |
| finals | generation-tech | an approved final for every shot | your words |
| sound | sound agent | files in `07_sound/` + licence notes | your words |
| assembly | assistant-editor | an animatic, an EDL or notes | your words |
| delivery | delivery agent | delivered files + `delivery-report.json` with every check passing | spec check |
| handoff | producer (handoff skill) | `10_handoff/canvas-build-sheet.md` + `upload-list.json` | evidence |
| learn | learner → producer | every lesson accepted or rejected with your words | your words |

QA runs in rounds: a QA supervisor checks the stage, a verifier double-checks its judgement calls, the crew
fixes what is confirmed. After 3 failed rounds the producer brings it to you, and your words can close the
stage. Going back is always possible: reopening a stage resets the later ones to pending and keeps their
history.

A project folder looks like this:

```
<projects_root>/<project-slug>/
  project.json      the manifest: assets, rights, generations, costs, decisions (changed only by sc.py)
  00_brief/  00_inputs/  01_research/  02_concept/  03_script/  04_bible/  05_prompts/
  06_generations/  07_sound/  08_assembly/  09_delivery/  10_handoff/
  .shotcraft/       stage state, QA rounds, the lessons inbox, project rules
```

## Install

In Claude Code:

```
/plugin marketplace add timmyha2612-droid/ai-content-production
/plugin install shotcraft@shotcraft
```

Restart Claude Code if the skills do not
show up straight away. Then say "set up shotcraft"; the producer asks where your projects should live and
checks your tools.

To try a local copy instead: `/plugin marketplace add /path/to/shotcraft`, then the same install line.

## Prerequisites

Required:

- **Claude Code** and **Python 3.9 or newer** (standard library only; nothing to pip install).
- **The Higgsfield CLI**, signed in to your Higgsfield account. Generation uses your plan credits.

  ```bash
  # macOS / Linux
  curl -fsSL https://raw.githubusercontent.com/higgsfield-ai/cli/main/install.sh | sh
  # or Homebrew
  brew install higgsfield-ai/tap/higgsfield
  # or npm (any platform, including Windows)
  npm install -g @higgsfield/cli

  higgsfield auth login
  ```

  Without it, the refine track still works fully (prompt cards need no generator), and the planning stages
  of a project work too.

Optional (detected; shotcraft says what is missing when a stage needs it):

| Tool | Used for |
|---|---|
| `ffmpeg` and `ffprobe` | delivery checks (resolution, length, fps, codec, loudness, digital silence, audio covers picture), the animatic, still frames, the natural-finish pass (grain, room tone) |
| `yt-dlp` | downloading reference videos (kept as `reference-only`) |
| `node` | the code route for motion graphics (HTML and animation rendered to MP4) |

Run `python3 "<plugin folder>/scripts/sc.py" doctor`, or just ask the producer to "check my setup".

## Quick start

Talk to Claude in plain English. These are examples, not commands you must type exactly.

**Just a prompt (refine track)**

> Write me a Higgsfield prompt: slow dolly-in on a black coffee cup at dawn, steam rising, 9:16, for a Reel.

You get a complete prompt at once, plus at most 3 questions where a wrong guess would waste credits (for
example, which model or whether there is a start frame). The card is saved to
`<projects_root>/_refine/<date>-<slug>.md`. Nothing is generated.

> Refine this prompt for Seedance: "a woman walks through a market, cinematic, 4k, no blur"

The prompt is rebuilt in the six-layer order, trimmed to the model's length limit, and "no blur" is
rewritten as positive wording, since most Higgsfield video models have no negative prompt field.

**One asset (single track)**

> Make me a YouTube thumbnail for my video "I cooked for 30 days on a camp stove".

A short intake (a few questions in one round), a job card, a prompt card, cheap drafts on a contact sheet,
your pick, a final at the right size (1280x720), a delivery check, and the hand-off.

**A full production (full track)**

> Start a production: a 15-second Instagram Reel launching a neighbourhood bakery's sourdough. Budget 300
> credits, ask me above 50 per job.

The producer runs the intake interview, writes the job card, and walks the stages with you: research and
references, two or three concepts, the script, the shot list, the bible (look, places, people), a prompt card
per shot, image-first boards, drafts, approved finals, titles and end card, sound, an animatic, delivery
checks, and finally the Higgsfield hand-off. You approve at each gate. Say "where are we?" at any time.

**Picking up later**

> Continue the bakery project.

The producer opens the project, reads its stage state and job card, and carries on from the open stage.

## Your own material (hybrid inputs)

Your own footage, photos, product shots, 3D renders (for example from Blender) and other files go in
`00_inputs/`, tagged `owned`. They can be used as start frames, end frames, character or style references,
or cut straight into the edit. You can mix generated and real material shot by shot: the shot list has a
`source` column for that. A production designer may also plan an environment as "3D blockout, render, use as
a start frame".

## Configuration and rule layers

Your settings live in `~/.shotcraft/` (set `SHOTCRAFT_HOME` to move it):

| File | What it holds |
|---|---|
| `config.json` | `projects_root` (asked on first run), `provider` (`higgsfield`), `default_threshold_credits` (50), `confirm_every_generation` (true: every generation waits for your yes to its price), a currency note |
| `rules/` | your personal rule overrides |
| `sessions/`, `active.json` | which project is active in which Claude session |
| `scout/last.json` | the last model check |
| `lessons.md` | lessons logged when no project is open |

All of shotcraft's craft knowledge is data in `rules/*.json`, read in three layers, each merged over the one
before:

```
plugin rules/  <  ~/.shotcraft/rules/  <  <project>/.shotcraft/rules/
```

| File | What it holds |
|---|---|
| `taxonomy.json` | the six prompt layers (intent, subject, world, camera, light and look, time and output), every field with help, a priority for trimming, and a professional vocabulary |
| `negatives.json` | things to avoid: universal, by category (people, text, product, motion, loops, motion graphics, icons) and by model |
| `positive_rewrites.json` | how each "avoid" item is said positively for models with no negative prompt |
| `models.json` | each Higgsfield model's limits: durations, resolutions, aspects, start and end frames, references, audio, prompt length, strengths, gotchas, and the date it was checked |
| `routing.json` | which model to use for which need and tier (draft, final, upscale), in fallback order |
| `presets.json` | use-case presets: social vertical, square and landscape, YouTube and Shorts, thumbnail, icon, logo animation, web hero, banner ad, B-roll insert, real estate, product shot, storyboard, billboard, presentation |
| `tracks.json`, `stages.json` | the tracks and the stage table |

Merge rules: objects merge key by key, lists replace, and a key ending in `+` appends to the list instead.
For example, `~/.shotcraft/rules/negatives.json` with

```json
{ "universal+": ["lens flare"] }
```

adds "lens flare" to every avoid list without copying the rest of the file.

The stage table and tracks are read from the plugin only. A personal or project rule file cannot loosen a
gate.

The learn stage writes accepted lessons to your personal or project rules, never to the plugin. To share an
improvement with everyone, open a pull request (see [CONTRIBUTING.md](CONTRIBUTING.md)).

## How model updates work

Model limits and costs are never trusted from memory:

- **Costs are always live.** Every generation is priced with `higgsfield generate cost` first.
- **Limits come from the CLI.** `models.json` is a starting point with a `checked_at` date per model. The
  CLI's own answer (`higgsfield model get`) wins, and the CLI reports any value it clamped.
- **A daily check.** At the start of a Claude session, if the last check is older than 20 hours, shotcraft
  compares the live model list with `models.json` (12-second limit, silent on failure). If models were
  added, removed or changed, you see one line: "N new Higgsfield models since <date>. Say 'run model-scout'
  to review." It also flags routing rows not checked for 30 days.
- **You decide.** "Run model-scout" reviews the changes and proposes new routing and model entries. Approved
  changes go into your personal rules straight away, and can be sent upstream as a pull request.

## The storyboard app

`sc.py board serve` opens the project as a storyboard on `http://127.0.0.1` (Python standard library, nothing
to install). Claude writes `board/board.json` from the script, shot list and look book; the app adds:

- **A timeline** with every shot sized by its cut length, and the director's look book above the shots.
- **References on every attribute.** Click + Ref, drop images, or paste. Each one is saved in `00_inputs/board/`
  and recorded as a project asset. New references are reference-only (they guide the prompt and are never
  sent); tap the tag to mark one owned, licensed or generated.
- **Labels and @ mentions.** Name a reference (`@Baker`) and mention it in a card. On Seedance the board turns
  `@Baker` into `@Image1`, `@Image2` and so on, in the order the images are sent, and shows the map.
- **The Higgsfield side of each shot:** models per tier, settings, the compiled prompt with a Copy button,
  and anything the compiler had to leave out.
- **An Assets tab** with every material, what it maps to (start frame, character, reference, style, or not
  sent) and the `card set-input` commands the producer will run with your yes.

- **Shot by shot.** Once the whole board is approved, put any batch in progress (`S010-S030`, `scene 2` or
  all). Each shot then moves draft, final, locked on its own, and the board shows its takes as they come back
  from Higgsfield, with approve, redo, pause, lock and unlock. Every action records the words you type.

The server binds to 127.0.0.1 only and every request needs the one-time token in the link it prints.

## The Higgsfield hand-off and the Canvas limitation

A full production ends with a hand-off package in `10_handoff/`:

- every approved asset uploaded to your Higgsfield account (`upload-list.json` records what went up), and
- a **Canvas build sheet** (`canvas-build-sheet.md`): the nodes, their prompts, settings and inputs, and how
  they connect, so the board can be rebuilt in Higgsfield Canvas in minutes.

As of November 2026, Higgsfield Canvas has no API, CLI or MCP access, so shotcraft cannot build the board
for you directly. On a Mac with Claude in Chrome, the handoff skill can offer to set the board up in your
browser while you watch. When Higgsfield opens a Canvas API, the hand-off will build the board itself.

## The Higgsfield REST API (optional, not built)

Higgsfield also has a REST API (`api.higgsfield.ai`) with separate prepaid billing in US dollars, its own key,
and a model catalogue whose names differ from the CLI's. shotcraft does not use it: it uses the CLI and your
plan credits. If you need the REST API (for example on a server with no CLI), it can be added as another
provider adapter under `scripts/shotcraft/providers/`, following `base.py`. Contributions welcome.

## Works alongside Higgsfield's official plugin

Higgsfield publishes its own Claude Code plugin (`/plugin marketplace add higgsfield-ai/skills`, then
`/plugin install higgsfield@higgsfield`) with skills for generation, Soul ID, product shoots, brand kits and
more. shotcraft does not replace it. Think of shotcraft as the director and producer, and the official
plugin as a set of specialist tools. Both can be installed at once.

One thing to know: while a shotcraft project is open, the guard sends Higgsfield generation and upload calls
through `sc.py gen`, so the budget, stage and rights checks always run. With no project open, those tools
work as normal.

## The command line

Skills and agents drive one script, and you can run it yourself:

```bash
sc="python3 <plugin folder>/scripts/sc.py"
$sc doctor
$sc project init --name "Bakery Reel" --track full --use-case social-vertical --budget 300 --threshold 50
$sc project status
$sc stage status
$sc card new --shot S010 --from-text "slow dolly-in on a black cup at dawn, steam rising"
$sc card compile 05_prompts/S010.md --model seedance_2_0
$sc route --use-case social-vertical --tier draft --kind video --duration 4
$sc gen estimate 05_prompts/S010.md --tier draft
$sc budget status
$sc sheet build --tier draft --open
$sc board check
$sc board serve
$sc board add 00_inputs/blender/S050-lit-v01.png --shot 5 --attr Frame --rights owned --user-said "my renders"
$sc shots start S010-S030 --user-said "scene one first"
$sc shots lock S010 --user-said "lock it"
$sc finish texture 08_assembly/reel.mp4 --grain subtle --out 08_assembly/reel_tex.mp4
$sc finish roomtone 08_assembly/reel_tex.mp4 --out 09_delivery/bakery-reel_social-vertical_1080x1920_v1.mp4
```

The finish pass chains: `texture` writes a work file outside `09_delivery/` (here `08_assembly/`), then `roomtone` runs on that file and
writes the final file into `09_delivery/`. Paths are relative to the current directory. Without `--out`,
finish refuses a file inside `09_delivery/`, because work files left there fail the delivery check. Skip
`texture` when the job card's `Grain:` is off with no vignette. `roomtone` is a single-bed safety floor
(generated pink noise, or one neutral `--bed`) for a deliverable that still fails the digital-silence check;
the per-scene room tone and ambience beds belong in the sound mix.

Every command takes `--json`, `--project PATH` and `--session-id ID`. Exit codes: 0 ok, 2 refused (a gate is
not met; the message says why and what to do), 1 error. `$sc --help` and `$sc <group> --help` list the rest.

Generation only happens through `sc.py gen submit`, which checks that the right stage is open, the card is
valid and approved, the cost fits the budget (or you said yes), and no input is reference-only.

Run the tests (no network, no Higgsfield CLI needed):

```bash
python3 -m unittest discover -s scripts/tests -v
```

## Roadmap

- **Autopilot.** Run the stages between gates without stopping for routine steps, pausing only for your
  approvals, spend over the threshold, and QA escalations.
- **Blender as an input source.** Through a Blender MCP: build or adjust the environment in Blender, render
  blockouts and camera passes into `00_inputs/`, and use them as start frames and references.
- **Higgsfield Canvas API.** Build the Canvas board directly once Higgsfield exposes it.
- **NLE editing plugins.** A bridge that hands approved shots, timings and the animatic to editing plugins for
  DaVinci Resolve, Premiere Pro and other editors, so the cut continues where shotcraft stops.
- **More providers.** Other generators as adapters behind the same interface.

## Contributing and licence

See [CONTRIBUTING.md](CONTRIBUTING.md) for how to propose rule and model changes and how to run the tests.
[SPEC.md](SPEC.md) is the design contract. Changes are listed in [CHANGELOG.md](CHANGELOG.md).

MIT licence. See [LICENSE](LICENSE). shotcraft is an independent project and is not made by or affiliated with
Higgsfield.
