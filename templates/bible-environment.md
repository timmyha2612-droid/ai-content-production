# <Place name, e.g. Cafe counter at dawn>

<!--
04_bible/environments/<env-slug>.md, one file per place. Written by the production-designer agent in the bible
stage, alongside 04_bible/look.md (palette, grade, light logic, texture, look line) and 04_bible/props/.
The environment line is the exact sentence every prompt card reuses word for word in its world layer, so the
place looks the same in every shot. Use concrete nouns and terms from rules/taxonomy.json (world and light_look).
References are reference-only: they guide the look and are never sent to a model as inputs. Only owned,
licensed or generated assets can be card inputs.
Replace every <...> and delete these comments when the page is filled.
-->

Used in: <shot ids, e.g. S010, S020, S040>
Environment line: "<one sentence: the place, its key surfaces and objects, the light source and direction, time of day, atmosphere>"
References: <asset ids with what to take from each, all reference-only unless the user said otherwise>
Inputs usable: <owned, licensed or generated asset ids that may be start frames or references; or none>

## Description

<What the place is, in concrete nouns: surfaces, materials, colours, scale.>

## Layers of depth

<!-- Build the place in planes, like a multiplane set-up in classic animation. Each line feeds the matching
     prompt card field: background_far, background_near, subject.placement, foreground, parallax. -->

- Far background: <the most distant plane: sky, skyline, hills; often soft and hazy>
- Near background: <the plane just behind the people: shopfront, back wall, shelves; may have several layers>
- Midground: <where people stand, and what is around them>
- Foreground: <what sits between camera and subject: rain on glass, a cup edge, leaves, a doorframe; usually soft>
- What moves on each plane: <video only. e.g. far clouds drift slowly; traffic streaks in the near background; foreground slides past faster on a camera move>

## Subject and environment

<!-- How the place acts on the people in it, as cause and effect. Feeds subject.interaction on each card.
     A subject that ignores the place looks pasted in. -->

- Light: <what the place's light does to the people, e.g. neon spill on a cheek, window light on one side of the face>
- Weather: <e.g. wet hair, breath fogging, wind in a coat>
- Contact: <e.g. a footprint in a puddle, a hand on misted glass, elbows on the counter>
- Scale: <e.g. small against the street, filling the booth>

## Light

- Source and direction: <e.g. large window frame left, soft>
- Time of day: <...>
- Colour temperature: <e.g. warm 3200K key, cool blue fill>
- Practicals: <lamps, screens, signs in frame>
- Scene light plan (scene <n>): "<copied word for word from the Scene light plans block in 03_script/shotlist.md>"
<!-- One line per scene set here; a place used at two times of day needs two lines. Cards repeat the anchor
     phrase word for word and continuity is checked against it. -->

## Weather and atmosphere

<e.g. clear; light haze; steam; dust in the light; rain on the glass>

## Dressing

- <object, colour, material, where it sits>

Natural finish: <wear and signs of use that make the place lived-in, e.g. scuffed counter edge, a chipped mug, a menu with a coffee ring; or "clean" for a pristine product or graphic set>

## Never in frame

- <logos you do not own, modern objects in a period scene, clutter, people if the place is empty>

## Shots

| shot | camera position | what we see of the place |
|---|---|---|
| <S010> | <e.g. low, frame right of the counter> | <...> |

## Hybrid plan

<!-- Optional. When the place is built or blocked out in 3D (for example Blender) or shot for real. -->

- Route: <none | 3D blockout, render, use as start frame | the user's own footage or photos>
- Status: <planned | rendered (asset ids) | supplied by the user (asset ids)>
- Notes: <camera matches, lens, resolution of the renders>
