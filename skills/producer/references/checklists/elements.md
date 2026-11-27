# QA checklist: elements

Stage outputs: `04_elements/style/look.md`, `04_elements/characters/` (cast.md plus one file per recurring character),
`04_elements/environments/`, `04_elements/props/`, `04_elements/style/moodboard/`. Gate: continuity QA PASS (the
script-supervisor runs this checklist), then the user's words.

Read: the job card, the script, the shot list, every element sheet, `sc asset list --json` (the element sheets's references
and inputs), `00_brief/grilling.md`.

The BI-C items are continuity: they decide whether every shot can be generated so that the cuts match. The other
items are design quality.

## Continuity (the script-supervisor's core)

| id | check | how | kind | severity |
|---|---|---|---|---|
| BI-C01 | Every character, place and recurring or hero prop in the shot list has an element (sheet, @Label, locked takes). Nothing recurring is left to chance. | Build the list from the shot list and script; tick each against `cast.md`, `environments/`, `props/`. | fact | blocker |
| BI-C02 | Each character has one fixed description (face, build, hair, skin, age range, marks) written so it can be pasted word for word into every card, with no "or" and no ranges that let a model choose. | Read each character file's model sheet and its consistency line. | judgement | major |
| BI-C03 | Each character has a consistency method that will work for its shots: a reference image (owned, licensed or generated), an approved board to use as a start frame, or a Soul ID with 5-20 photos the user owns. The method is possible with the rights we have. | Check each anchor asset id in `sc asset list --json`: rights must not be `reference-only`. | fact | blocker |
| BI-C04 | Wardrobe continuity: each character's outfit per scene is fixed (garments, colours as hex or exact names, fit, accessories), with a change only where the script has a time jump, and each change is named with the shots it covers. | Read the wardrobe plan against the shot list's scenes. | fact | major |
| BI-C05 | Props are pinned: shape, material, colour, size relative to the hand, which hand holds it, its state (full, half, empty) per shot where it changes. | Read each prop file against the shots that use it. | fact | major |
| BI-C06 | Light direction per environment: where the key light comes from (frame left or right, high or low, motivated by what), its quality and colour temperature, and that it stays the same across shots in the same place and time. | Read each environment file and `look.md` light logic. | fact | major |
| BI-C07 | Time of day and weather per scene are stated once and are the same across every shot of that scene. | Compare environment files with the script's scenes. | fact | major |
| BI-C08 | Palette: `look.md` gives the palette as hex values with roles and rough ratios; wardrobe, props and environments sit inside it (or the exceptions are deliberate and named). | Check every colour named in the other element sheets against the palette. | fact | major |
| BI-C09 | Screen direction is planned where it matters: who is on which side of frame, which way travel goes (left to right, right to left), and the 180-degree line for any two-person or subject-object scene. | Read the element sheets's notes and the shot list's continuity column together. | judgement | major |
| BI-C10 | Reusable lines exist and are consistent: the look line, each environment line, each character's consistency line and each prop line. The same thing is described in the same words everywhere it appears. | Search the element sheets for each named thing; compare the wording. | fact | major |
| BI-C11 | Era and never-in-frame lists cover anything that would break the world (modern phones in a period piece, logos we have no rights to, the wrong car). | Read `look.md` and environment files. | judgement | minor |
| BI-C12 | Each environment defines its depth planes: what sits in the foreground, the background just behind the subject (shopfront, back wall, shelves) and the far background (sky, skyline, hills), each in words that can be pasted into `world.foreground`, `background_near` and `background_far`. For live-action looks it also names signs of use (scuffs, a worn step, clutter on a counter), so sets do not look sterile. | Read each environment file. | fact | major |
| BI-C13 | Each character says how they react to the place's weather and light (hair wet in rain, breath fogging in cold, neon spill on the skin, squinting into sun), so `subject.interaction` is the same across shots. | Read each character file against the environments they appear in. | judgement | minor |
| BI-C14 | Each scene has a scene light plan: one line naming its anchored sources (the "anchor", for example "north window on the left wall, one table lamp right of the bed, blue hour outside"). It gives the key's world source, its side of frame, height and hard or soft; each practical (a lamp, screen or sign in the world) with its colour; the ambient colour; and, for hard patterns (blinds, leaves), the angle of the stripes. The cards will repeat the anchor word for word, and continuity is checked against it. | Read each environment file's Light section for a `Scene light plan (scene <n>):` line per scene in the shot list; a place used at two times needs two. Each must match the shot list's Scene light plans block word for word. | fact | major |
| BI-C15 | Light changes inside a scene are planned: the ratio band (soft about 2:1, drama about 4:1, hard 8:1 and up; key to fill), any change the script asks for (a lamp switched on, the source moving, a jump in ratio) with the shots it covers, and for golden or blue hour the direction the sun or sky level moves across the scene. Anything not planned here is a break later. | Read the scene light plans against the script and the shot list's scenes. | fact | major |

## Design quality

| id | check | how | kind | severity |
|---|---|---|---|---|
| BI-01 | The stage evidence is there: `04_elements/style/look.md` and at least one file in `characters/` or `environments/`. | `sc stage status elements --json` | fact | blocker |
| BI-02 | The look matches the chosen concept and the job card (brand colours, mood, the user's likes and dislikes). | Compare with `02_concept/chosen.md`, the job card and `grilling.md`. | fact | major |
| BI-03 | Descriptions use concrete nouns and taxonomy terms a model understands, not adjectives ("brushed brass counter, terrazzo floor", not "elegant space"). | Read the environment and look lines. | judgement | minor |
| BI-04 | No real person's likeness, no celebrity look-alike, no trademarked character; types are described, not names. | Read the character files. | fact | blocker |
| BI-05 | Moodboard and references stay `reference-only` and are never named as inputs; only owned, licensed or generated assets are named as card inputs. | Compare every asset id the element sheets names as an input with its rights. | fact | blocker |
| BI-06 | Hybrid plans (the user's footage, photos, a Blender blockout rendered as a start frame) name the exact files in `00_inputs/` or the render to be made, and which shots use them. | Check the files exist: `sc asset list --role input --json`. | fact | major |
| BI-07 | Product accuracy *(product)*: the product is described from the user's own photos (label, colours, shape, scale) and the plan says how it will be kept exact (reference image, image first, or the real product composited in post). | Read the prop file; check the photos are assets with rights owned or licensed. | fact | major |
| BI-08 | The look is something the chosen models can do (for example, film grain and anamorphic flares are described as texture, not relied on for the story). | Compare with `${CLAUDE_PLUGIN_ROOT}/skills/prompt-craft/references/model-prompting.md`. | judgement | minor |
