# Element prompting: characters, environments, props, style frames

Elements are built one by one in the elements stage, before any shot. Each element has one or more **views**;
each view is a prompt card (`04_elements/cards/E01A.md`) scaffolded from `rules/element_recipes.json` by
`sc.py element add`. `sc.py element views` lists them all. This page explains how to fill and judge them.

## The rule that matters most: sheets are neutral, plates are in the light

| Kind of view | Background | Light | Why |
|---|---|---|---|
| Sheets: turnaround, expressions, outfit, product, angles | plain light grey seamless | flat, even, shadowless | The model must learn the *thing*, not a place or a mood. Light and colour baked into a sheet leak into every shot that uses it. |
| Plates: environment plate, reverse, time variant | the place itself, empty | the scene's own light plan | The place *is* the light. Every shot of the scene is built on this. |
| Hero portrait, style frame | the film's world | the job's look | A check that the identity holds in the real look; the style frame is the look reference itself. |

## The anchor

Every element has one **anchor**: a single fixed sentence (15-30 words) that describes it, passed with
`--anchor`. The recipe puts it into every view's `subject` and `consistency`, and shot cards repeat it word for
word. Never paraphrase it. Concrete and physical: age range, build, face, hair, the outfit's key garment (a
character); the space, its main surfaces, the light source (a place); shape, material, colour, markings (a prop).
Never a real person's name or "looks like ...".

## Characters

| View | Use it when | Fill |
|---|---|---|
| `turnaround` (default) | always, for anyone seen in more than one shot | the anchor; outfit as worn in most scenes |
| `expressions` (default) | any readable face | replace the generic line with the 3-6 expressions the script needs, in physical terms ("brows pulled down, jaw set") |
| `outfit` | each outfit change (W1, W2...), one view each | every garment: colour (hex where it matters), material, fit, wear |
| `portrait` | before locking a lead, to check the identity in the look | the job's key light from look.md |

Judge: same face, hair and build in every panel; no extra characters; nothing cropped; clean background.
Hands and printed text drift first: simplify them in the anchor if they don't matter.

## Environments

| View | Use it when | Fill |
|---|---|---|
| `plate` (default) | every place a scene happens in | the depth planes (far, near, foreground), time of day, weather, the scene light plan word for word, practicals |
| `reverse` | conversations, turns, anything shot from both sides | same light, seen from the other side |
| `detail` | close-ups will show surfaces or set dressing | the textures and objects close-ups need |
| `time_variant` | the place appears at another time or weather (one view each) | that time's light; same camera position as the plate |

Judge: **no people**; clear floor space where the action happens; light from the planned side; deep focus so
the shot's own lens choice can soften it later.

## Props

| View | Use it when | Fill |
|---|---|---|
| `product` (default) | every hero prop or product | exact shape, material, colour, markings |
| `angles` | the prop is turned or handled on screen | front, side, back, top at one scale |
| `in_hand` | size matters (a phone, a glove, a cup) | the hand holding it naturally |

Judge: true colour, correct shape, no logos or text you don't own, no extra objects. A vehicle is a prop; a
creature or mascot is a character.

## Style frame

One `frame` view: a representative still of the finished film (palette with hex values, contrast, grain, lens
character, mood) from `04_elements/style/` and the job's look. It goes on shot cards as the `style` input.

## Models

Element views are stills that take references: Nano Banana 2 by default (`rules/routing.json`
`element_policy`), GPT Image 2.6 for text-heavy or graphic sheets, Seedream 4.5 or Cinema Studio Image 2.5 for
photoreal plates. Set `model.element` on the card to choose. Generate with `sc.py gen estimate|submit E01A
--tier element`; review with `sc.py sheet build --tier element`.

## From locked element to shot

1. `sc.py element lock E01 --user-said "..."` turns the approved takes into reference assets labelled `@Label`.
2. The user's yes, then save it to Higgsfield as an Element (Higgsfield MCP `elements_create`, category from the
   recipe's `hf_category`, the take as an `image_job` media) and record it: `sc.py element link E01
   --hf-element <uuid>`. On Higgsfield an Element is used by putting `<<<element_id>>>` in the prompt; it works
   on Nano Banana 2/Pro, GPT Image 2.6, Seedream, Seedance 2.0, Cinema Studio 3.0 and Kling 3.0 (Kling also
   needs a start image).
3. In the prompts stage, `sc.py element attach S010 --user-said "..."` puts each shot's locked elements on its
   card as inputs (characters as `character`, places and props as `reference`, the style frame as `style`).
   The shot prompt then mentions them by `@Label` and describes only what is new in the shot: placement,
   action, camera, light direction. It never re-describes a locked element.
