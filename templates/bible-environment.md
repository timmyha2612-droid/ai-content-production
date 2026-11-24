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

- Foreground: <...>
- Midground: <...>
- Background: <...>

## Light

- Source and direction: <e.g. large window frame left, soft>
- Time of day: <...>
- Colour temperature: <e.g. warm 3200K key, cool blue fill>
- Practicals: <lamps, screens, signs in frame>

## Weather and atmosphere

<e.g. clear; light haze; steam; dust in the light; rain on the glass>

## Dressing

- <object, colour, material, where it sits>

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
