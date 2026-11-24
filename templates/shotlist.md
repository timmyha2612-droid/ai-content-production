# Shot list: <Project name>

<!--
03_script/shotlist.md. Written by the director skill in the shotlist stage, from 03_script/script.md.
The gate (sc.py stage done shotlist) reads the ONE table below. Rules it checks:
  - id: looks like S010. Steps of 10; an insert between S010 and S020 is S015; a split take is S010A. No id twice.
  - duration_s: seconds the shot PLAYS IN THE EDIT, a number above 0 (e.g. 2.5). Stills too: how long they hold.
  - purpose: what the viewer must get from the shot, in a few words. Not empty, not TBD, ... or <...>.
Other stages read:
  - kind: video or image.
  - image_first: yes or no. "yes" means the shot starts as a cheap still (a board) before any video is made.
    A shot also counts as image-first when its prompt card's tier_plan includes "board".
The other columns are free text the gate ignores: beat, size_angle (shot size and angle, e.g. MCU, low angle),
move (camera movement, e.g. slow push-in), continuity, mograph (text or graphics on this shot),
source (gen, or a 00_inputs/ file the user supplied, e.g. their own footage or a 3D render).
Keep the id column first. Do not add a second table with an id or Shot column: it would be read as more shots.
Pipes (|) inside a cell break the table: write "or" instead.
Replace every <...> and delete these comments when the list is filled.
-->

Delivery: <aspect, width x height, fps, total length in seconds> (preset <preset id>). Handles: <seconds> each side.
Script: 03_script/script.md

| id | beat | duration_s | kind | image_first | purpose | size_angle | move | continuity | mograph | source |
|---|---|---|---|---|---|---|---|---|---|---|
| S010 | <hook> | <seconds> | <video or image> | <yes or no> | <what the viewer must get> | <e.g. ECU, top-down> | <e.g. static> | <what must match the shots around it> | <none, or the text> | <gen or 00_inputs/file> |
| S020 | <setup> | <seconds> | <video or image> | <yes or no> | <what the viewer must get> | <...> | <...> | <...> | <...> | <...> |
| S030 | <payoff> | <seconds> | <video or image> | <yes or no> | <what the viewer must get> | <...> | <...> | <...> | <...> | <...> |

**Total:** <sum of duration_s> s (delivery <length> s).

## Generated length per shot

<!-- The take each shot needs from the model: play length plus handles, fitted to the model's allowed durations.
     The cinematographer and generation-tech use this; sc.py card compile fits it exactly. -->

- S010: plays <seconds> s, generate <seconds> s, trim <where>
- S020: ...

## Coverage and pacing

- Hook: <what happens in the first 1 to 2 seconds, and why it stops the scroll>
- Rhythm: <shot lengths and where the pace changes>
- Ending: <the last frame, call to action, loop point if it loops>

## Continuity

- <A fact that must hold across shots: screen direction, wardrobe, props, light direction, time of day.>

## Bible needs

- Characters: <names, shots>
- Environments: <places, shots>
- Props: <hero props, shots>

## Motion graphics list

- <Shot id: the text or graphic, exact wording>

## Risks

- <Shot id: what may be hard to generate (hands, text, fast physics, crowds) and the fallback>
