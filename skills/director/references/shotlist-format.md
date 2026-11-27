# Shot list format (03_script/shotlist.md)

Scenes first, then shots. The shot list stage closes only when `sc.py stage done shotlist` can read two markdown
tables in this file (a header row, a `|---|` row, then one row each). Other text around them is fine.

## The scene table

A scene is one continuous piece of action in one place at one time. The scene table is the table with a `scene`
and a `place` column.

| column | accepted header names | rule |
|---|---|---|
| scene | `scene`, `scene_id`, `sc` | Looks like `SC01`, in story order. No id twice. |
| place | `place`, `location`, `where`, `set` | The slugline place: `INT. BOXING GYM`. Not empty. |
| time | `time`, `time_of_day`, `when` | `DAY`, `NIGHT`, `DAWN` ... Not empty. A place at two times is two scenes. |
| mode | `mode`, `generation` | `shots` (one generation per shot) or `multi-shot` (the whole scene in one Kling 3.0 Omni generation, 15 s at most). Empty means `shots`. |
| elements | `elements`, `uses` | The `@Labels` of the elements in the scene: `@Boxer @Gym @Look`. |

## The shot table

A shot is one uninterrupted camera take between two cuts. The shot table is the table with an `id` (or `Shot`)
column.

| column | accepted header names | rule |
|---|---|---|
| id | `id`, `Shot`, `shot_id` | Looks like `S010`, numbered through the whole piece in steps of 10; an insert is `S015`; a split take `S010A`. No id twice. |
| scene | `scene`, `sc` | A scene from the scene table. A scene's shots sit together, in order. |
| duration_s | `duration_s`, `Duration`, `Duration (s)`, `dur`, `seconds` | Seconds above 0, e.g. `2.5`. The length the shot **plays in the edit**, not the generated length. |
| purpose | `purpose`, `why`, `intent` | What the viewer must get from the shot. Not empty, not `TBD`, `...` or `<...>`. |
| elements | `elements`, `uses` | Only when the shot differs from its scene (a prop in this shot only). Empty: the scene's elements. |

Other stages read `kind` (`video` or `image`) and `source` (`gen`, or a `00_inputs/` file the user supplied).
Free-text columns: `beat`, `size_angle`, `move`, `composition`, `depth`, `continuity`, `graphics`, `notes`.
Keep cells short. Pipes (`|`) inside a cell break the table: write "or" instead.

## Under the tables

- **Total:** the sum of `duration_s` (with a flexible length, this total becomes the delivery length).
- **Generated length per shot:** from `sc route` (see the director skill).
- **Scene light plans:** one line per scene, as `SC01 (<place>): <anchor phrase>`, copied word for word into the
  environment sheet's Light section and repeated on every card of the scene.
- **Elements to build:** every `@Label` with what it is, its views (`sc.py element views`) and its scenes.
- **Graphics list** for the user's motion graphics tool.

## Example

```
# Shot list: Old Boxer

Delivery: 9:16, 1080x1920, 30 fps (preset social-vertical). Length: flexible, set by the story. Handles: 0.5 s.

## Scenes

| scene | place | time | mode | elements |
|---|---|---|---|---|
| SC01 | INT. BOXING GYM | NIGHT | shots | @Boxer @Gym @Look |
| SC02 | EXT. ROOFTOP | DAWN | multi-shot | @Boxer @Rooftop @Look |

## Shots

| id | scene | beat | duration_s | kind | purpose | elements | size_angle | move | continuity |
|---|---|---|---|---|---|---|---|---|---|
| S010 | SC01 | hook | 2.5 | video | Hands, tape, breath: he is still doing this | @Boxer @Gym @Tape | ECU | static | tape on the left hand first |
| S020 | SC01 | setup | 4 | video | The empty gym; he is alone | | WS | slow push-in | single caged bulb, key from frame right |
| S030 | SC01 | turn | 3 | video | First punch lands on the heavy bag | | MCU, low | handheld | bag swings left |
| S040 | SC02 | payoff | 4 | video | Sunrise, he breathes | | WS | static | breath fogs |
| S050 | SC02 | payoff | 3 | video | Close on his face, eyes closed | | CU | slow push-in | sun on the right cheek |

**Total:** 16.5 s. SC02 multi-shot: 7 s (fits one 15 s take).
**Scene light plans:**
- SC01 (boxing gym): one caged bulb above the bag, frame right; cold blue spill from a high window left
- SC02 (rooftop): low sun from frame right, blue sky behind, warm rim on the face
**Elements to build:** @Boxer (character: turnaround, expressions, outfit W1); @Gym (environment: plate,
reverse); @Rooftop (environment: plate); @Tape (prop: product, in_hand); @Look (style: frame).
```

## Common refusals and fixes

- "no scene table": add the scenes table above the shots, with `scene` and `place` columns.
- "S030 has no scene" / "is in scene SC03, which is not in the scene table": fill the scene column.
- "the shots of scene SC01 are not together": a scene's shots sit in one block; a return to the place later is
  a new scene (SC03) with the same place.
- "multi-shot scene SC02 runs 18 s": make it `shots`, or split it into two scenes.
- "has no shot table": the shot table needs an `id` (or `Shot`) column and a `|---|` line under the header.
- "S020 has no purpose": write what the shot is for, not what it shows.
