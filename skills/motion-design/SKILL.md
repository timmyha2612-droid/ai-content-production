---
name: motion-design
description: "This skill should be used for the motion graphics stage of a shotcraft production: titles, lower thirds, end cards, captions styled as graphics, logo animations, animated icons, charts and kinetic type. It picks the route (After Effects template fill, After Effects build, HyperFrames or another code route, Lottie for icons), runs After Effects on the user's Mac through an MCP bridge or osascript, or runs the code route anywhere. Triggers: \"add the titles\", \"make a lower third\", \"animate the logo\", \"end card\", \"kinetic type\", \"animated icon\", \"Lottie\", \"use my After Effects template\", \"build it in AE\", \"HyperFrames\", \"Remotion\", \"motion graphics stage\", or the producer reaching the mograph stage."
metadata:
  version: "0.1.0"
---

# Motion design (mograph stage)

Motion graphics carry what AI video does badly: exact text, logos, numbers, brand type and clean shapes. This skill
plans each graphic, picks the cheapest route that meets the delivery, makes it, shows preview frames, and gets the
user's approval.

In this skill, `sc.py` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Add `--json` when you need to read
the output. `MD` means `${CLAUDE_PLUGIN_ROOT}/skills/motion-design`.

References (read the one for the route you pick):
- `references/route-choice.md`: which route for which graphic, and the questions that decide it.
- `references/ae-route.md`: After Effects on the Mac (MCP bridge, osascript + JSX, aerender, nexrender), preview
  frames, and the known breakages.
- `references/code-route.md`: HyperFrames (default), Remotion (licence caveat), Lottie/dotLottie, Manim, Revideo.
- `scripts/ae/`: small ExtendScript helpers and the `run_jsx.sh` runner.

## 0. Open the stage

```
sc.py project status --json
sc.py stage status mograph
sc.py stage start mograph
```

The mograph stage may run alongside the sound stage; everything before it must be done or skipped. It is
optional: if it shows `skipped`, do nothing unless the user asks (then `sc.py stage reopen mograph --user-said ".."`).
The guard blocks writing in `07_mograph/` until the stage is open.

## 1. Read and list the graphics

Read: `03_script/shotlist.md` (the `mograph` column and the Mograph list under it), `03_script/script.md`
(on-screen text, exact wording), `04_bible/look.md` (palette, type, logo rules), `00_brief/job-card.md`
(delivery: aspect, size, fps, length), and the user's brand files in `00_inputs/`
(`sc.py asset list --role input --json`). On the single track (an animated icon or logo) the job card and the
approved final are the inputs.

Write `07_mograph/mograph-list.md`: one row per graphic.

```
| id | what | text (exact) | over | in_s | duration_s | size | alpha | route | status |
|---|---|---|---|---|---|---|---|---|---|
| M010 | lower third | "Ana Ruiz" / "Head Roaster" | S020 | 0.5 | 3.0 | 1080x1920 | yes | ae-template | planned |
| M020 | end card | logo + "Shop now" | S050 | 0 | 3.0 | 1080x1920 | no | code | planned |
```

- Text is copied from the script exactly; spelling and capitals are checked against it later.
- `over` is the shot it sits on, or `full` for a standalone card. `in_s` is where it starts within that shot.
- `alpha: yes` when it overlays video (delivered with transparency).

## 2. Pick the route, and ask what only the user knows

Follow `references/route-choice.md`. The order of preference:

1. **After Effects template fill**: the user has an AE template (`.aep` or `.mogrt`) for this graphic.
2. **After Effects build**: AE is installed on the Mac and the user wants AE project files they can open and edit.
3. **Code route**: HyperFrames by default (HTML + GSAP or Lottie rendered to video); runs anywhere, including
   headless Linux.
4. **Lottie / dotLottie**: animated UI icons and small loops for apps and the web.

Ask with **AskUserQuestion**, only what the files don't say (at most 3 questions):

- "Do you have an After Effects template or brand motion kit for these?" (options: yes, I'll share it / no)
- "Do you need editable After Effects project files, or are rendered files enough?"
- Brand fonts, if `look.md` names a font the machine may not have: "Is <font> installed and licensed on this
  machine?"

Check the machine before promising the AE route:
- `uname -s` must be `Darwin` (macOS) for `scripts/ae/run_jsx.sh`. Windows works with `AfterFX.com -r` (see
  `ae-route.md`). Linux has no After Effects: use the code route.
- `bash "$MD/scripts/ae/run_jsx.sh" --list` shows which After Effects versions are installed.
- An AE MCP bridge counts when its tools are available in this session (see `ae-route.md`).

Write the route per graphic in the `route` column.

## 3. Make the graphics

Spawn the **motion-designer** agent, one per route (or one per graphic when they are independent), with:

- the project path and stage `mograph`;
- the graphic ids and their rows from `07_mograph/mograph-list.md`;
- the route, and for AE: the AE version from `run_jsx.sh --list`, the template path, and whether an MCP bridge is
  connected;
- the delivery spec (aspect, size, fps), `04_bible/look.md` and the brand files' paths;
- where to write: AE projects in `07_mograph/ae/`, code projects in `07_mograph/code/<id>/`, renders in
  `07_mograph/renders/`, preview frames in `07_mograph/previews/`;
- the return shape: `{"made": [{"id", "files", "preview", "route", "warnings"}], "blocked": [{"id", "why"}]}`.

The agent never talks to the user. Anything that needs the user (a dialog in AE, a missing font, a licence
question) comes back as `blocked`, and you ask.

Work you do yourself in the main session (not in an agent):
- Driving After Effects through an MCP bridge when the user is watching their Mac: dialogs that pop up need them.
- Installing anything (HyperFrames, Remotion, Manim, nexrender): ask first. Never install without a yes.

Naming: `M010_lower-third.mov`, `M020_end-card.mp4`. Overlays with alpha: ProRes 4444 `.mov` (or WebM VP9 with
alpha for the web). Full-frame cards: H.264 `.mp4` at the delivery size and fps. Icons: `.lottie` or `.json`
plus a static SVG or PNG fallback.

## 4. Preview, then ask

For each graphic, make 2 to 4 preview frames (start of the move, the settled hold, the exit) in
`07_mograph/previews/`, and look at them yourself first (Read the PNGs). Check: the text is exact, nothing is
cut off, it sits inside the platform's safe zone (social vertical: keep text away from the top 250 px and bottom
400 px on 1080x1920), it is readable at phone size, colours and type match `look.md`.

Then show the user the preview paths and a one-line description per graphic, and ask with **AskUserQuestion**:
"Approve these graphics?" with options "Approve all", "Changes needed" (then ask which and what, in one question).

## 5. QA, then close

The gate is a QA PASS plus the user's words.

1. Spawn the **qa-supervisor** agent with: the project path, stage `mograph`, the round number
   (`sc.py qa status --stage mograph --json`, field `next_round`), `07_mograph/mograph-list.md`, the renders and
   previews, `04_bible/look.md`, `03_script/script.md` and the delivery spec. It checks spelling against the
   script, timing against `duration_s`, size, fps, alpha where needed, safe zones, and brand rules.
2. Spawn the **qa-verifier** agent on the judgement calls.
3. Record the round (findings in a temporary file outside `.shotcraft/qa/`):
   ```
   sc.py qa record --stage mograph --round <N> --verdict PASS|FAIL --findings <findings.json> --note "<one line>"
   ```
   FAIL: fix, then the next round. After 3 FAILs, escalate: only the user's words can close it.
4. Register each approved render, so assembly and delivery can find it. The file is ours, so the user's approval
   words go with it:
   ```
   sc.py asset add 07_mograph/renders/M010_lower-third.mov --rights owned --role final --kind video --shot S020 --note "mograph M010 lower third" --user-said "<the user's approval words>"
   ```
5. Close with the user's own words:
   ```
   sc.py stage done mograph --user-said "<the user's exact words>"
   ```

If the user corrects a style or a habit ("always fade lower thirds, never slide"), log it before acting on it:
`sc.py lessons add "<one line>" --kind general` (or `--kind project`).

## Never

- Never generate with a model in this stage. A graphic that should be AI-generated (an abstract animated loop)
  belongs on the shot list as a shot and is made in drafts and finals.
- Never use a font, template or music the user has not confirmed they may use.
- Never press through an After Effects dialog for the user, and never close their open AE project without saving
  unless they say so.
- Never install software or change macOS permissions without asking.
- Never close the stage with invented user words.
