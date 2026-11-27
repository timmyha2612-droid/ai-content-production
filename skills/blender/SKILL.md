---
name: blender
description: "Build shotcraft references in Blender: blockout sets, subject and camera motion, and renders matched to a shot's prompt card (lens, 9:16, depth planes, look book light), saved to the project and the board. Triggers: \"let's build it in Blender\", \"block out the set\", \"render a start frame\", \"camera move reference\"."
metadata:
  version: "0.1.0"
---

# shotcraft: Blender references

Blender is where the user and you build what a prompt can't pin down: the exact layout of a place, where the
subject stands and moves, and the real camera path. The renders become references and start frames, so they
must match the shot's card, or Higgsfield gets two different instructions.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`.

## Before you start

- The user connects Blender to Claude themselves. Check that Blender tools are in this session (their names
  usually contain `blender`). If none are, don't try to install anything: write the plan (step 2) into the
  shot's environment file in `04_elements/environments/` and tell the user it's ready to build once Blender is
  connected.
- Blender runs on the user's own computer. Work only inside the project folder, in `00_inputs/blender/`.
- The connection can run any Python in Blender. Save a copy before each big step
  (`bpy.ops.wm.save_as_mainfile(filepath=..., copy=True)`), never delete or overwrite the user's own objects,
  scenes or files without asking, and keep each script short and readable.
- Rendering costs no credits, only time. Say roughly how long a render will take before a slow one.

## 1. Read the shot first

Read the card (`05_prompts/<shot>.md`), the look book in `board/board.json` (or `04_elements/style/look.md`) and the
environment file. Pull out: aspect and size, lens, shot size and angle, the camera move and its speed, the
duration, the depth planes (far, near, subject, foreground), the key light's source, side and colour, what
stays dark, and the palette.

## 2. Plan in plain words, then build

Tell the user the plan in a few lines and wait for their yes before building:
"Set: workshop table, pegboard behind, moss set in the middle. Camera: 85mm at the dinosaur's eye level, slow
push-in over 6.5 s. Light: one warm lamp at frame left. Renders: clay still, lit still, camera-move preview."

Build to these rules so the render and the card agree:

| Card says | In Blender |
|---|---|
| Aspect 9:16 | Output 1080 x 1920 (720 x 1280 for quick previews), the same aspect for every render of the shot |
| Lens 35mm, 85mm ... | Camera focal length the same, sensor 36 mm wide |
| Shot size and angle | Camera height and framing to match; the subject at the card's share of the frame |
| Depth planes | Collections `FG`, `SUBJECT`, `BG_NEAR`, `BG_FAR`; something in front of the subject and something behind |
| Camera move + speed | One move, keyframed over exactly the card's duration at the preset's frame rate (30 fps for vertical social), ease in and out to match "slow" |
| Key light | One key named `KEY` coming from a source you can see or that is clearly placed in the set (window, lamp, monitor); colour from its temperature; little or no world light, so the named areas stay dark |
| Palette | Materials in the look book's colours; plain grey for anything not yet designed |

Use real scale (metres). Model simply: blockout shapes are fine; detail only where the camera sees it. Use
only your own modelling, CC0 assets (for example from Poly Haven) or assets the user licensed; write the
source and licence of every downloaded asset in the environment file. No branded products, logos or known
characters.

Show the user the viewport (a screenshot) before rendering, and change what they ask.

## 3. Render the useful versions

Save into `00_inputs/blender/` as `<shot>-<kind>-v01.<ext>` (`S050-clay-v01.png`), bumping the version
instead of overwriting.

| Render | What it's for | Engine |
|---|---|---|
| `clay` still | Layout and composition reference (grey material override) | EEVEE, fast |
| `lit` still | Start frame candidate, matched to the look book | EEVEE, or Cycles for the final pick |
| `move` preview | Camera path and timing as a motion reference (H.264 MP4, card duration exactly) | EEVEE viewport or render |
| `depth` (optional) | A mist or depth pass, for compositing or a depth-guided model | Either |

## 4. Put them on the board and wire them to the card

Renders made with the user are theirs, so ask once: "These Blender renders are yours, mark them owned?"
With their words:

- Stills: `sc board add 00_inputs/blender/S050-lit-v01.png --shot 5 --attr Frame --rights owned --user-said
  "<their words>"`; the clay still as `--attr Environment` or `--attr Camera` with a label such as `--label
  DinoSet`. Labels let cards mention them as `@DinoSet`.
- Videos (the move preview): the board shows images only for now. Register it with `sc asset add
  00_inputs/blender/S050-move-v01.mp4 --rights owned --role input --shot S050 --note "camera move reference"`
  and mention it in the card's notes.
- Then `sc board inputs` lists the card inputs these call for. The producer runs them with the user's words.
  A lit still used as the start frame turns the card into motion only: the prompt then describes the camera
  move and the action, not the picture.

Every render you hand over is a reference: generation still goes through the card, the live price and the
user's yes.
