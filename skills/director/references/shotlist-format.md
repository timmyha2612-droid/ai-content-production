# Shot list format (03_script/shotlist.md)

The shot list stage closes only when `sc.py stage done shotlist` can read this file. It looks for a markdown
table (a header row, then a `|---|` row, then one row per shot). Other text around the table is fine.

## Columns the gate checks

| column | accepted header names | rule |
|---|---|---|
| id | `id`, `Shot`, `shot_id` | Looks like `S010`. Steps of 10; an insert between S010 and S020 is `S015`; a split take can be `S010A`. No id twice. |
| duration_s | `duration_s`, `Duration`, `Duration (s)`, `dur`, `seconds` | A number of seconds greater than 0, e.g. `2.5` or `2.5s`. This is the length the shot **plays in the edit**, not the generated length. |
| purpose | `purpose`, `why`, `intent` | What the viewer must get from the shot, in a few words. Not empty, not `TBD`, `...` or `<...>`. |

## Columns other stages read

| column | accepted header names | values |
|---|---|---|
| kind | `kind`, `type`, `media` | `video` or `image` |
| image_first | `image_first`, `Image-first`, `board` | `yes` / `no` (also `y`, `x`, `true`, `board`). A shot also counts as image-first when its card's `tier_plan` includes `board`. The boards stage needs a board for every video shot flagged here. |

## Recommended extra columns (free text; the gate ignores them)

`beat`, `shot` (size and angle, e.g. `MCU, low angle`), `move` (e.g. `slow push-in`), `action`,
`composition` (the technique from the composition guide's quick chooser, three at most: one geometry, one
depth, one light, e.g. `frame within a frame; deep staging`; PR-21 checks the card against it),
`depth` (foreground, background and how the subject meets the place, e.g. `fg: rain on glass; bg: neon
shopfront; neon spill on her cheek`; the cinematographer turns it into the card's depth fields), `continuity`,
`graphics` (text or graphics to add on this shot in the user's motion graphics tool), `source` (`gen` or a `00_inputs/` file the user supplied), `notes`.

Keep cells short. Pipes (`|`) inside a cell break the table: write "or" instead.

## Under the table

- **Total:** the sum of `duration_s` and the delivery length.
- **Generated length per shot:** from `sc route` (see the director skill).
- **Scene light plans:** one line per scene, as `Scene <n> (<place>): <anchor phrase>`. The anchor names the
  light sources fixed to the set (the key's world source and side, each practical with its colour, the
  ambient colour). The production designer copies each line word for word into the environment file's Light
  section, and every card of the scene repeats the anchor. A place used at two times of day is two scenes.
- **Bible needs** and the **Graphics list**.

## Example (15 s social vertical, 9:16)

```
# Shot list: Morning Ritual reel

Delivery: 9:16, 1080x1920, 30 fps, 15.0 s. Handles: 0.5 s each side (preset social-vertical).

| id | beat | duration_s | kind | image_first | purpose | shot | move | composition | depth | continuity | graphics | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S010 | hook | 1.5 | video | no | Stop the scroll: steam curls off a black cup | ECU, top-down | static, steam moves | centre framing; pool of light | fg: blurred spoon edge; bg: dark kitchen, window glow; steam catches the window light | dark stone surface, cool dawn light | none | gen |
| S020 | setup | 3.0 | video | yes | Introduce the product exactly as it looks | MS, eye level | slow push-in | rule of thirds; foreground frame | fg: soft cup rim; bg: window, garden haze; window light rakes the label | bottle label faces camera; same stone | product name lower third | gen |
| S030 | turn | 2.5 | video | no | Show the ritual: hand pours | CU | locked-off | as shot | own footage | hand enters frame left to right | none | 00_inputs/pour_take3.mov |
| S040 | payoff | 5.0 | video | yes | The hero: sunrise hits the cup | WS to MCU | crane down, ease out | deep staging; light leads the eye | fg: steam; bg: window, then rooftops; sun warms the cup and casts its shadow; rooftops slow, steam drifts | ends on the frame S050 opens on | none | gen |
| S050 | CTA | 3.0 | image | no | Brand and call to action | MCU | slow Ken Burns in post | negative space for the end card | as S040 | match S040's last frame | logo + "Shop now" end card | gen |

**Total:** 15.0 s (delivery 15.0 s).

**Generated length per shot (draft):** S010 -> 4 s take, trim to 1.5 s. S020 -> 4 s. S040 -> 6 s.
**Scene light plans:**
- Scene 1 (kitchen counter): east window on the left wall, low dawn sun, cool blue room ambient
**Bible needs:** the product (exact label), the stone surface, dawn light.
**Graphics list (for your motion graphics tool):** lower third on S020; end card on S050.
```

## Common refusals and fixes

- "has no shot table": the header row needs an `id` (or `Shot`) column and the second line must be `|---|...`.
- "'Shot 1' is not a shot id like S010": use S010-style ids.
- "S030 has no duration_s": a number is required, even for stills (how long the still holds on screen).
- "S020 has no purpose": write what the shot is for, not what it shows.
