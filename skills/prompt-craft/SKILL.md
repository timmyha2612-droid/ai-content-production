---
name: prompt-craft
description: "This skill should be used whenever a shotcraft prompt card is written, filled, compiled or judged, or the user asks how to prompt: \"how should I prompt Kling / Seedance / Veo / Hailuo / Wan / Cinema Studio / Soul / Nano Banana / GPT Image / Seedream / Recraft / Flux\", \"what camera move should I use\", \"describe this shot properly\", \"what does dolly zoom mean\", \"why did the model ignore my prompt\", \"negative prompt\", \"avoid list\", \"prompt too long\", \"image to video prompt\". It is the reference for the six-layer taxonomy and its vocabulary (rules/taxonomy.json), the negatives and positive-rewrite system, Higgsfield's prompting rules, per-model notes and the camera-movement cookbook. Loaded by the refine and director skills and by the cinematographer and generation-tech agents."
metadata:
  version: "0.1.0"
---

# shotcraft: prompt craft

How to describe a shot so a generation model renders it right the first time. This skill is a reference:
it does not run stages. The refine skill, the director skill and the cinematographer and generation-tech
agents load it.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`.

## The core rules (Higgsfield's and ours)

1. **Concrete beats clever.** Concrete nouns, physical present-tense verbs, real materials and light.
   "A woman in her 30s dusts flour off her hands" beats "a baker in a magical moment".
2. **Order matters.** The compiler writes: subject and action, then world, camera, light and look, time and
   beats, then style. Models weight the start of the prompt most.
3. **Short.** Stay under the model's word cap (default 120 words, about 200 tokens). Long prompts distort;
   the compiler trims the lowest-priority fields first (texture, then practicals, era, camera look).
   Subject, action, movement, movement speed and shot size are never dropped.
4. **One clear camera move per shot,** with its speed. Two moves in one shot is the most common failure.
5. **Positive phrasing.** Most Higgsfield models have no negative prompt field. Say what you want ("tack
   sharp", "uninhabited landscape"), not what you do not want ("no blur", "no people"). The compiler rewrites
   the card's avoid list into positive wording for you (`references/negatives-system.md`).
6. **Image to video: motion only.** With a start frame the model already has the picture. Describe the camera
   move, the subject's motion and the beats. Never describe the frame again.
7. **Image to image: describe the change,** not the input ("turn into a watercolour, soft paper texture").
8. **Exact numbers.** Durations in seconds that match the cut, plus handles only when the edit needs them.
   The smallest resolution that meets the delivery.
9. **Safe content.** No real public figures, trademarks or branded characters, nothing sexual. These end as
   `nsfw` or `ip_detected` and waste a submit.
10. **Read limits live.** Never trust memory for durations, aspects, resolutions or costs: `rules/models.json`
    (with its `checked_at` date), `higgsfield model get <id>`, `sc gen estimate`.

## The six layers (the card's `layers`)

| Layer | Fields | In the prompt? |
|---|---|---|
| intent | use, platform, audience, brand | No. Planning only: why the shot exists |
| subject | subject, action, wardrobe_props, elements, consistency | Yes, first |
| world | environment, era, time_of_day, weather_season, atmosphere | Yes |
| camera | shot_size, angle, lens, dof, composition, movement, movement_speed, camera_look | Yes |
| light_look | setup, quality, direction, color_temp, practicals, palette_grade, texture, style_ref, mood | Yes |
| time_output | beats, pacing, loop, transition_in, transition_out, audio, on_screen_text | Yes (video: beats and pacing) |

Every field has a label, help text, a priority and a professional vocabulary (terms with a short meaning) in
`${CLAUDE_PLUGIN_ROOT}/rules/taxonomy.json`. How to read and use it: `references/taxonomy-guide.md`.
Fill what matters for the shot; leave the rest empty. Use the vocabulary's terms where they fit, because
they are the words models were trained on.

## Writing a card, step by step

1. Intent first (one line each): what the shot must do, for whom, on what platform.
2. Subject and action: who or what, doing one clear thing. Fixed wardrobe and props. For a recurring
   character, `consistency` names the reference (a bible image or Soul ID) and the card's `inputs` carry it.
3. World: place, time of day, atmosphere. Era and weather only when they matter.
4. Camera: shot size, angle, lens, then ONE move and its speed (`references/camera-movement-cookbook.md`).
   Locked-off when the subject moves a lot; a move when the subject is still.
5. Light and look: the setup and direction, colour temperature, grade, one style reference, mood.
6. Time and output (video): beats as time ranges that add up to the duration, pacing, loop, transitions,
   native audio, exact on-screen text (or none: text is safer added in motion graphics).
7. Avoid: start from `negatives.json` universal plus the categories that apply (people, text, product,
   motion, locked_off, loop, mograph, icon). Keep it short; every item costs prompt words when rewritten.
8. `sc card validate <card>`, then `sc route --use-case <preset> --tier draft|final [--kind video|image]
   [--duration <s>] [--needs audio,refs,end_frame]` to pick the model, then
   `sc card compile <card> --model <id>` and read the result: `adjustments` (values corrected for the
   model), `dropped_fields`, `unguarded`, `word_count`. Fix and compile again until it reads like a
   director's note.

## Per-model prompting

Each model family has its own strengths, limits and traps (for example: `nano_banana_2` is Nano Banana
**Pro**, Nano Banana 2 is `nano_banana_flash`; Veo 3.1 takes only 4, 6 or 8 s; Recraft takes no reference
images; some Cinema Studio versions default the prompt language to Chinese). Read
`references/model-prompting.md` before writing for a model you have not used in this session.

## Checking a compiled prompt (the 10-second test)

- Can you picture the first frame and the last frame?
- Is there exactly one camera move, with a speed?
- Does the action fit the duration (a 3 s shot holds one action, not three)?
- Is every word doing work? Cut adjectives that do not change the picture ("beautiful", "amazing").
- With a start frame: is there anything that re-describes the frame? Cut it.
- Is anything phrased as a negative? Rewrite it positively.
- Would a model mistake a word for a brand or a real person? Change it.

## References

- `references/taxonomy-guide.md`: how to use `rules/taxonomy.json`: layers, fields, priorities, trimming,
  vocabulary lookups, adding terms in personal rules.
- `references/negatives-system.md`: the avoid list, `negatives.json`, `positive_rewrites.json`, how the
  compiler guards against each term, and how to add your own.
- `references/model-prompting.md`: per-model notes for the Higgsfield models (Seedance, Kling, Veo, Hailuo,
  Wan, Cinema Studio, Soul, Nano Banana, GPT Image, Seedream, Recraft, Flux): prompt style, strengths, traps.
- `references/camera-movement-cookbook.md`: every move with what it says emotionally, when to use it, the
  wording that renders, speeds, and the moves models get wrong.
