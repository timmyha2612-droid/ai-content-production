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

`beat`, `shot` (size and angle, e.g. `MCU, low angle`), `move` (e.g. `slow push-in`), `action`, `continuity`,
`mograph` (text or graphics on this shot), `source` (`gen` or a `00_inputs/` file the user supplied), `notes`.

Keep cells short. Pipes (`|`) inside a cell break the table: write "or" instead.

## Example (15 s social vertical, 9:16)

```
# Shot list: Morning Ritual reel

Delivery: 9:16, 1080x1920, 30 fps, 15.0 s. Handles: 0.5 s each side (preset social-vertical).

| id | beat | duration_s | kind | image_first | purpose | shot | move | continuity | mograph | source |
|---|---|---|---|---|---|---|---|---|---|---|
| S010 | hook | 1.5 | video | no | Stop the scroll: steam curls off a black cup | ECU, top-down | static, steam moves | dark stone surface, cool dawn light | none | gen |
| S020 | setup | 3.0 | video | yes | Introduce the product exactly as it looks | MS, eye level | slow push-in | bottle label faces camera; same stone | product name lower third | gen |
| S030 | turn | 2.5 | video | no | Show the ritual: hand pours | CU | locked-off | hand enters frame left to right | none | 00_inputs/pour_take3.mov |
| S040 | payoff | 5.0 | video | yes | The hero: sunrise hits the cup | WS to MCU | crane down, ease out | ends on the frame S050 opens on | none | gen |
| S050 | CTA | 3.0 | image | no | Brand and call to action | MCU | slow Ken Burns in post | match S040's last frame | logo + "Shop now" end card | gen |

**Total:** 15.0 s (delivery 15.0 s).

**Generated length per shot (draft):** S010 -> 4 s take, trim to 1.5 s. S020 -> 4 s. S040 -> 6 s.
**Bible needs:** the product (exact label), the stone surface, dawn light.
**Mograph list:** lower third on S020; end card on S050.
```

## Common refusals and fixes

- "has no shot table": the header row needs an `id` (or `Shot`) column and the second line must be `|---|...`.
- "'Shot 1' is not a shot id like S010": use S010-style ids.
- "S030 has no duration_s": a number is required, even for stills (how long the still holds on screen).
- "S020 has no purpose": write what the shot is for, not what it shows.
