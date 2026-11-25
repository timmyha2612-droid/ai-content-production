# The negatives system

Every card has an `avoid` list: short phrases for what must not happen ("camera shake", "warped text").
How they reach the model depends on the model.

## Two routes

1. **The model has a negative prompt field** (`"negative_prompt": true` in `rules/models.json`; on the
   Higgsfield CLI today that is only Text to 3D, `tripo_3d`): the compiler joins the avoid list into
   `negative_prompt` and sends it in that field.
2. **No negative field** (every Higgsfield image and video model at the time of writing): the compiler
   rewrites each avoid term into positive wording from `rules/positive_rewrites.json` and adds it inside the
   prompt, after the description. This is Higgsfield's own advice: phrase positively. Writing "no blur" in
   the prompt can make blur more likely, because the model reads the word "blur".

Terms with no rewrite are listed in the compile output as `unguarded`. They are not in the prompt at all.
Either add positive wording to a layer yourself, add a rewrite (below), or accept the risk and tell the user
what to watch for.

## Where avoid terms come from (`rules/negatives.json`)

| Group | Use it when | Examples |
|---|---|---|
| `universal` | Every card | blurry, low resolution, jpeg artifacts, watermark, logo, distorted proportions, overexposed, duplicate subject |
| `by_category.people` | People or faces in frame | extra fingers, deformed hands, plastic skin, face morphing, identity drift |
| `by_category.text` | Any on-screen or on-product text | warped text, misspelled text, gibberish text |
| `by_category.product` | A hero product | wrong label, deformed product, melted edges, floating product |
| `by_category.motion` | Any video | camera shake, jitter, flicker, morphing, rubbery motion, sliding feet |
| `by_category.locked_off` | A static camera | camera movement, zoom, handheld wobble, reframing |
| `by_category.loop` | A seamless loop | visible loop seam, jump at loop point |
| `by_category.mograph` | Motion graphics plates | busy background, off-brand colours, gradient banding |
| `by_category.icon` | Icons and UI | fine detail, thin lines, photorealism, text in icon |
| `by_category.too_perfect` | Live-action looks that must not read as "AI perfect" | cgi look, too perfect, airbrushed skin, perfect symmetry, sterile spotless set, hyper-sharp everywhere, flat even lighting, stock-photo posing |
| `by_category.flat_light` | Added by the compiler on low-key looks (see below) | flat lighting, lifted shadows, rim light on both sides, evenly lit, softbox, beauty lighting, HDR |
| `by_model.<id>` | Added automatically for that model | starting guesses from community reports, not confirmed by Higgsfield |

`sc card new` starts the card with a short avoid list. For live-action presets (`"finish": "natural"`:
social, YouTube, B-roll; `"finish": "true_to_life"`: real estate) it also adds the first two `too_perfect`
items, "cgi look" and "too perfect". When the composition asks for symmetry, the compiler drops "perfect
symmetry" (its rewrite asks for asymmetry) and warns.
Add the categories that apply. Keep the list short
(about 4 to 8 items): every guard costs prompt words, and guards are trimmed before most layers when the
prompt is over the cap.

## Guards the compiler adds on its own (`applies_when`)

`negatives.json` `applies_when` lists guards the compiler adds without you. Today there is one: `flat_light`.
It stops a low-key look (dark, with deep shadow) from drifting back to flat, even studio light.

- It fires when `light_look.setup` or `light_look.quality` holds a low-key family word: low key, split,
  Rembrandt, short lighting, practical, top light, firelight, candlelight, neon, night exterior, chiaroscuro
  and the like. The full trigger list is `applies_when.flat_light.any` in `negatives.json`.
- It does not fire on high key or overcast (`unless`), even if a trigger word is also there.
- It adds the first three `flat_light` terms ("flat lighting", "lifted shadows", "rim light on both sides"),
  so you will see them in the card's Avoid output, or in `unguarded` when trimmed. Terms already on the card
  are not added twice.
- They go at the end of the avoid list, and their rewrites have a low trim priority (5): when the prompt is
  over the word cap they are dropped first, before the card's own guards, the practicals and the texture.
- `card new` cannot add them, because `setup` is filled after the card is made. To guard more of the group,
  add the terms to the card's avoid list yourself.

The rule and its fields are in SPEC.md section 6.

## How rewriting works (`rules/positive_rewrites.json`)

A flat map from avoid term to positive phrasing:

```json
{
  "blurry": "tack-sharp focus, crisp fine detail",
  "watermark": "clean unmarked image",
  "camera shake": "locked-off tripod shot, perfectly stable frame",
  "camera shake (moving camera)": "smooth stabilised camera movement"
}
```

- A key ending in ` (moving camera)` is used instead of the plain key when the shot has a camera move. That
  stops "camera shake" turning into "locked-off tripod shot" on a dolly shot.
- A key ending in ` (shallow focus)` is used instead of the plain key on a shallow-focus shot: a live-action
  finish (natural or true_to_life), or a depth of field or plane that says shallow, bokeh, soft or out of
  focus. So "blurry" becomes "sharp focus on the subject" (`blurry (shallow focus)`), not "tack-sharp focus,
  crisp fine detail", which would fight the soft background.
- Two terms with the same rewrite are written once.
- Every `too_perfect` term has a rewrite toward a natural look: "sterile spotless set" becomes "lived-in
  set with small signs of use", "airbrushed skin" becomes "natural skin texture with visible pores and fine
  lines". Full list: `depth-and-finish.md`.
- Keys starting with `_` are comments and are ignored.
- Matching is case-insensitive on the whole term.

## The grain clash

When `light_look.texture` or `light_look.finish` asks for grain or film stock (grain, film stock, 35mm,
16mm, super 8, halation), the compiler drops the "noise", "grain" and "film grain" avoid items and warns. A
"noise-free" guard would fight the look you asked for. Do not add them back on a grainy shot.

## Adding your own

Personal (all your projects): `~/.shotcraft/rules/positive_rewrites.json`. Project only:
`<project>/.shotcraft/rules/positive_rewrites.json`. Only the new keys are needed; files deep-merge over
the plugin's.

```json
{
  "lens flare": "clean optics with no stray light, flare-free",
  "lens flare (moving camera)": "clean optics, flare-free as the camera moves"
}
```

To add avoid terms to a category, append with a `+` key in `~/.shotcraft/rules/negatives.json`:

```json
{"by_category": {"product+": ["reflections of the crew"]}}
```

Without the `+` the list would replace the plugin's list instead of adding to it. Give each new term a
rewrite too, or it will show up as `unguarded`. The learn skill proposes these after a job, and writes them
only after the user's yes.

## Good rewrites

- Describe the wanted result, not the absence: "unbranded surfaces" (not "no logos").
- Be visual: "five fingers on each hand, natural relaxed hands" is clearer than "correct anatomy".
- Short: 3 to 8 words. A long rewrite pushes out layer content.
- Do not contradict the shot: a "perfectly still frame" rewrite on a handheld shot fights the movement field.
- Do not use `too_perfect` on clean graphics, icons or pristine product shots: there, clean is the point.

## When a term keeps failing

If a model keeps producing what the avoid list guards against, the prompt is usually the cause, not the
list: two moves in one shot (morphing), too many subjects (duplicates), text on a model weak at text
(gibberish), a long take (identity drift). Fix the layer, change the model (`sc route`), or use image first
(a board as the start frame). Log what you learnt: `sc lessons add "<model> <behaviour>" --kind model`.
