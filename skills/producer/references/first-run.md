# First run and setup

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`.

Run this when `sc doctor --json` shows no config (`config.exists: false`) or no `projects_root`, or when the
user says "set up shotcraft". It takes about a minute. Do it once per machine.

## 1. Where projects live (ask, never guess)

`sc setup` with no folder is refused on purpose: "ask the user where projects should live". Ask with
AskUserQuestion, one question:

- Question: "Where should shotcraft keep your projects? Each project gets its own folder there."
- Options (recommended first):
  - `~/shotcraft-projects` (Recommended): "Easy to find, outside any code repo."
  - `~/Documents/shotcraft`: "Inside Documents, so it is backed up with them."
  - A folder you already use for video work: "Type the path in Other."

Then `sc setup --projects-root "<their folder>"`. It saves `~/.shotcraft/config.json` and runs doctor.

## 2. Read the doctor report out in plain words

`sc doctor` checks:

| Check | Needed for | If missing, tell the user |
|---|---|---|
| `higgsfield` (the Higgsfield CLI) | every generation, live model limits and costs | "Install it with `npm install -g @higgsfield/cli`, then sign in." Needs Node. |
| Higgsfield sign-in | generation | "Run `higgsfield auth login` in your terminal (in Claude Code you can type `! higgsfield auth login`). It opens a browser." The user runs it; it is interactive. |
| `ffmpeg` / `ffprobe` | delivery checks, the animatic | "Install ffmpeg (macOS: `brew install ffmpeg`; Windows: `winget install ffmpeg`; Linux: your package manager)." |
| `yt-dlp` | downloading reference videos | "Optional. Install with `brew install yt-dlp` or `pipx install yt-dlp`." |
| `node` | the Higgsfield CLI, the code route for motion graphics | "Install Node 18 or newer." |
| rule files | everything | A broken install: reinstall the plugin. |

Only raise what blocks the user's request. Planning stages (intake, research, concept, script, shot list,
bible, prompts) need none of the tools. Refine needs none.

Credits are the user's Higgsfield plan credits. shotcraft never shows a price in money unless the user set
`currency_note` in the config. Costs always come live from Higgsfield (`gen estimate`), never from memory.

## 3. Higgsfield's own plugin

Higgsfield publishes an official Claude Code plugin (`/plugin install higgsfield@higgsfield`). It can sit
alongside shotcraft:

- shotcraft is the director: stages, cards, budget, approvals, hand-off.
- Higgsfield's plugin is the toolbox: its skills know the CLI well.
- While shotcraft is installed, its guard sends every raw generation (`higgsfield generate create`,
  `higgsfield upscale`, `higgsfield soul-id create`) through `sc gen ...`, and blocks Higgsfield MCP
  generate, upload, edit and train tools while a project is active. Reads always work.

## 4. Personal rules (optional)

Personal overrides live in `~/.shotcraft/rules/` with the same file names as the plugin's `rules/`. They
deep-merge over the plugin's (lists replace; a key ending in `+` appends). Project overrides live in
`<project>/.shotcraft/rules/`. The learn and model-scout skills write there after the user says yes.
Stage gates (`tracks.json`, `stages.json`) are always read from the plugin, so no override can loosen a gate.

## 5. Done

Tell the user in two lines: where projects go, what works now, what is missing and only matters later. Then
carry on with their request (track choice, Step 1 of the producer skill).
