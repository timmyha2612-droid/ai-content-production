# Shot list: <Project name>

<!--
03_script/shotlist.md. Written by the director skill in the shotlist stage, from 03_script/script.md.
Scenes first, then shots. The gate (sc.py stage done shotlist) reads two tables:

SCENE TABLE (columns scene, place, time, mode, elements):
  - A scene is one continuous piece of action in ONE place at ONE time. A new place or a new time is a new scene.
  - scene: SC01, SC02 ... in story order. place: the slugline place (INT. BOXING GYM). time: DAY, NIGHT, DAWN ...
  - mode: how Higgsfield makes it. "shots" = one generation per shot (most control, any model).
    "multi-shot" = the whole scene in ONE Kling 3.0 Omni generation with a prompt per shot (best continuity
    between its cuts); the scene's shots must add up to 15 s or less.
  - elements: the @Labels of the locked elements in the scene (characters, the place, props, style frame).

SHOT TABLE (columns id, scene, duration_s, purpose, elements):
  - A shot is one uninterrupted camera take between two cuts: one framing, one camera move.
  - id: S010, S020 ... in steps of 10, numbered through the whole piece; an insert is S015; a split take S010A.
  - scene: the scene it belongs to. A scene's shots sit together, in order.
  - duration_s: seconds the shot PLAYS IN THE EDIT, above 0. purpose: what the viewer must get from it.
  - elements: only when the shot differs from its scene (a prop only in this shot); empty = the scene's elements.
Other columns are free text: beat, kind (video or image), size_angle, move, composition, continuity, graphics,
source (gen, or a 00_inputs/ file the user supplied).
Pipes (|) inside a cell break a table: write "or" instead. Replace every <...> and delete these comments.
-->

Delivery: <aspect, width x height, fps> (preset <preset id>). Length: <flexible, set by the story, or the fixed
length>. Handles: <seconds> each side.
Script: 03_script/script.md

## Scenes

| scene | place | time | mode | elements |
|---|---|---|---|---|
| SC01 | <INT. PLACE> | <NIGHT> | <shots or multi-shot> | <@Character @Place @Prop> |
| SC02 | <EXT. PLACE> | <DAWN> | <shots or multi-shot> | <@Character @Place> |

## Shots

| id | scene | beat | duration_s | kind | purpose | elements | size_angle | move | composition | continuity | graphics | source |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| S010 | SC01 | <hook> | <seconds> | <video or image> | <what the viewer must get> | | <e.g. ECU, top-down> | <e.g. static> | <...> | <what must match> | <none> | <gen> |
| S020 | SC01 | <setup> | <seconds> | <video> | <...> | <@Prop, only if it differs> | <...> | <...> | <...> | <...> | <...> | <...> |
| S030 | SC02 | <payoff> | <seconds> | <video> | <...> | | <...> | <...> | <...> | <...> | <...> | <...> |

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

## Scene light plans

<!-- One line per scene: the light sources fixed to the set (key's world source and side, each practical with its
     colour, the ambient colour). The production designer copies each line word for word into the environment
     file's Light section; every card in the scene repeats the anchor. A place at two times of day is two scenes. -->

- SC01 (<place>): <anchor phrase, e.g. north window on the left wall, one table lamp right of the bed, blue hour outside>

## Elements to build

<!-- Every @Label used above, built and locked one by one in the elements stage before any shot is generated.
     Views per category: sc.py element views. -->

- Characters: <@Label, who, views (turnaround, expressions, outfit W1 ...), scenes>
- Environments: <@Label, the place, views (plate, reverse, time_variant ...), scenes>
- Props: <@Label, the object, views (product, angles, in_hand), shots>
- Style frame: <@Look, one frame of the finished film>

## Motion graphics list

- <Shot id: the text or graphic, exact wording>

## Risks

- <Shot id: what may be hard to generate (hands, text, fast physics, crowds) and the fallback>
