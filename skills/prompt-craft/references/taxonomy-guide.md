# Using rules/taxonomy.json

The taxonomy is the vocabulary of a shot. The prompt card's `layers` follow it field for field, and the
compiler uses it to order and trim the prompt.

## Shape of the file

```json
{
  "version": "...", "checked_at": "...",
  "prompt_order": ["subject", "world", "depth", "camera", "light_look", "time_output", "style"],
  "trim": {"protect_at_or_above": 90,
           "first_to_drop": ["light_look.texture", "light_look.practicals", "world.era", "camera.camera_look"]},
  "layers": {
    "<layer>": {
      "label": "...", "help": "...", "in_prompt": true,
      "fields": {
        "<field>": {"label": "...", "help": "...", "priority": 0-100,
                    "vocab": [{"term": "dolly in", "means": "the camera moves toward the subject"}]}
      }
    }
  }
}
```

- **layers**: intent, subject, world, camera, light_look, time_output. `intent` has `in_prompt: false`: it
  guides choices but is never written into a prompt.
- **help**: one line on what the field is for. Read it before filling a field you are unsure about.
- **vocab**: professional terms with a short meaning. Use the term in the card; use the meaning to explain it
  to the user in plain English.
- **priority**: how important the field is to the picture. Higher survives trimming.

## Priorities and trimming

| Priority | Fields |
|---|---|
| 90-100 (never dropped) | subject 100, action 98, movement 94, movement_speed 92, shot_size 90 |
| 80-89 | environment 88, on_screen_text 85, beats 84, time_of_day 82, setup 80 |
| 60-79 | angle 78, mood 76, placement 75, lens 74, interaction 73, composition 72, style_ref 70, loop 70, audio 68, foreground 67, elements 66, pacing 64, atmosphere 62, background_near 61, palette_grade 60 |
| 40-59 | dof 58, color_temp 56, direction 54, background_far 53, quality 52, weather_season 50, parallax 49, consistency 48, finish 47, wardrobe_props 46, transition_in 44, transition_out 42, camera_look 40 |
| below 40 | era 30, practicals 20, texture 10 |

When the compiled prompt is over the model's word cap, the compiler drops the lowest-priority item first,
one at a time, until it fits: texture, practicals, era and camera look go first (the `first_to_drop` list),
then transitions, then the positive guard phrases from the avoid list (priority 45; a dropped guard shows up
in `unguarded`), then wardrobe and so on upward. Each drop is reported in `dropped_fields`. It never drops a
field at or above 90. If something dropped mattered for this shot, the
fix is to shorten a higher field, not to fight the trimmer: fewer adjectives, one style reference, one
atmosphere word.

Image cards skip the motion fields (movement, movement_speed, beats, pacing, transitions, parallax). A card
with a start frame keeps only motion (camera move, subject action and interaction, parallax, beats); the
static planes are already in the frame.

## Looking up terms

Quick lookups without opening the whole file:

```bash
python3 -c "import json,sys; t=json.load(open(sys.argv[1])); f=t['layers'][sys.argv[2]]['fields'][sys.argv[3]]; print(f['help']); [print('-', v['term'], ':', v['means']) for v in f['vocab']]" \
  "${CLAUDE_PLUGIN_ROOT}/rules/taxonomy.json" camera movement
```

Swap `camera movement` for any layer and field (`light_look setup`, `world foreground`, `subject interaction`, `time_output
transition_in` ...).

## Filling fields well

- **One idea per field.** `movement: "slow dolly in"` not `"dolly in then orbit then crane up"`.
- **Taxonomy term plus specifics.** `setup: "Rembrandt lighting, key from camera left"`; `lens: "85mm,
  shallow depth of field"`. The term anchors the model; the specifics make it this shot.
- **Free text is fine** where no term fits. The vocabulary is a palette, not a cage. The subject is almost
  always free text.
- **No repetition across layers.** If `mood` says "tense", do not also put "tense" in `atmosphere`.
- **Beats add up.** `[{"t": "0-2", "what": "..."}, {"t": "2-5", "what": "..."}]` for a 5 s shot.
- **On-screen text** is the exact copy in quotes, or empty. Many models misspell; text is usually added in
  motion graphics. If the shot needs generated text, use a model good at text (see model-prompting.md) and
  keep it to a word or two.

## Depth planes and the natural finish

Seven fields build the frame in layers and keep it from looking too perfect. Full guide with a worked
example: `depth-and-finish.md`.

| Field | What goes in it |
|---|---|
| `subject.placement` | Where the subject stands: which plane, which part of frame, what is around them. Printed as the midground |
| `subject.interaction` | How the place and the subject act on each other: light on them, weather on them, contact, scale. Printed after the action |
| `world.background_far` | The most distant plane: sky, skyline, hills. Often soft and hazy |
| `world.background_near` | The plane just behind the subject: shopfront, back wall, bar shelves |
| `world.foreground` | What sits between camera and subject: rain on glass, a cup edge, leaves. Usually out of focus |
| `world.parallax` | Video only: how each plane moves and how fast. Near planes move faster than far ones |
| `light_look.finish` | Real-world imperfection: lived-in wear, motivated light, real-lens character. Empty for clean graphics, icons and products |

The planes print as one depth sentence after the world sentence ("Far background: ...; background: ...;
midground: ...; foreground: ...; ..."). Each part gets its plane label unless the text already names it.
The compiler warns "No depth planes" when `environment` is set but no foreground or background is.
`finish` has one default per preset finish value (`defaults` in the taxonomy), which `sc card new` fills
in: `natural` ("subtle real-world imperfection: lived-in detail, real-lens character") and `true_to_life`
(real estate: "true-to-life colour, slightly uneven motivated light, real-lens character"; no wear, no lens
softness). `clean` presets have no default and leave it empty. The defaults no longer ask for asymmetry, and
when `camera.composition` asks for symmetry (symmetry, centred, centre-punch) the compiler drops any
asymmetry wording from the finish and the "perfect symmetry" avoid item, with a warning. `finish` ranks
below the depth fields (47), so a plane you wrote outranks the generic finish.

## The style layer

`prompt_order` ends in `style`: the compiler places `style_ref` (film look, art style, genre) last, after
time and beats, so it colours the whole prompt without pushing out the subject.

## Personal and project vocabulary

Add terms without touching the plugin: create `~/.shotcraft/rules/taxonomy.json` (personal) or
`<project>/.shotcraft/rules/taxonomy.json` (project) with only what changes. Files deep-merge over the
plugin's: dicts merge, lists replace, and a key ending in `+` appends. To add a lens term:

```json
{"layers": {"camera": {"fields": {"lens": {"vocab+": [
  {"term": "Helios 44 swirl bokeh", "means": "vintage Soviet 58mm lens with swirling out-of-focus background"}
]}}}}}
```

The learn skill proposes such additions after a job; they are written only after the user's yes.
