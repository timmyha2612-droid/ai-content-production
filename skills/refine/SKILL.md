---
name: refine
description: "This skill should be used when the user wants a prompt rather than a production: \"refine this prompt\", \"make this prompt better\", \"fix my prompt\", \"write me a Higgsfield prompt\", \"give me a prompt for ...\", \"prompt for Kling / Seedance / Veo / Hailuo / Wan / Cinema Studio / Soul / Nano Banana / GPT Image / Seedream / Recraft / Flux\", \"turn this idea into a video prompt\", \"image prompt for a thumbnail\", \"why does my prompt give bad results\". It is the fast path (the refine track): a complete, model-aware prompt card straight away, at most 3 questions and only where a wrong guess would waste credits, saved with sc.py refine save, and an offer to generate it (one question with the live price, through the quick skill)."
metadata:
  version: "0.1.0"
---

# shotcraft: refine (the fast path)

The user wants a prompt, not a project. Give them a complete, paste-ready result **first**, then at most
3 questions. No intake, no stages, no generation. Generation only happens if they say yes to the offer at
the end, and then the producer skill takes over.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Load the **prompt-craft** skill for the vocabulary,
the negatives system and the per-model notes (`prompt-craft/references/model-prompting.md`).

## 1. Read the request (no questions yet)

Work out, from the user's words and anything they attached:

- **Kind:** video or image. A "shot", "clip", "reel", "move" is video; a "thumbnail", "still", "poster",
  "icon", "frame" is image.
- **Use case preset** (`rules/presets.json`): social-vertical, youtube, youtube-short, thumbnail, icon-ui,
  broll-insert, web-hero, product-shot, ... Pick the closest; it sets aspect, resolution and typical length.
- **Model:** the one they named, mapped to its id (table below), else the routing pick.
- **Start frame:** if they have an image to animate, the prompt describes motion only.
- **Their content:** keep every specific thing they said (names, colours, actions, text) word for word.
  Improve structure and craft around it, never their intent.

| They say | Model id | Note |
|---|---|---|
| Seedance | `seedance_2_5` | 4-30 s, up to 1080p. "4K" means `seedance_2_0` |
| Kling | `kling3_0` | 3-15 s; `kling3_0_turbo` for fast and cheap |
| Veo | `veo3_1` | 4, 6 or 8 s only; 16:9 or 9:16 only |
| Hailuo / Minimax | `minimax_hailuo` | 6 or 10 s; no audio |
| Wan | `wan2_7` | `wan2_6` for stylised and cheap |
| Cinema Studio | `cinematic_studio_video_4_0` | camera, lens, light and genre controls |
| Soul | `text2image_soul_v2` | people, editorial; `soul_cinematic` for cinematic stills |
| Nano Banana | `nano_banana_flash` | TRAP: `nano_banana_2` is Nano Banana **Pro** |
| Nano Banana Pro | `nano_banana_2` | top fidelity, accurate text |
| GPT Image | `gpt_image_2_6` | text on images, SVG and GIF output |
| Seedream | `seedream_v5_pro` | faces, character sheets |
| Recraft | `recraft_v4_1` | logos, icons, vector look; prompt only, no references |
| Flux | `flux_2` | precise prompt adherence |

No model named: `sc route --use-case <preset> --tier final --kind video|image [--duration <s>]
[--needs audio,refs,end_frame] --json` and take `best` (say why in the settings table). If they want to
test cheaply first, also route `--tier draft`.

## 2. Build the card and compile it

Work in a scratch file outside any project folder (for example `<your scratch dir>/refine/<slug>.md`).

1. Start the card:
   - If no project is active (`sc doctor --json` shows `active_project: null`), seed it from their text:
     `sc card new --shot S010 --from-text "<their prompt or idea>" --json` and write the returned `text` to
     the scratch file. (With a project active, `card new` would write into that project's `05_prompts/`, so
     copy `${CLAUDE_PLUGIN_ROOT}/templates/prompt-card.md` instead.)
2. Fill the JSON front matter: `id` "S010", a short `title`, `kind`, `use_case`, `tier_plan` (["final"], or
   ["draft", "final"]), `model` per tier, `settings` (aspect, resolution, `duration_s` for video, variants,
   audio), `inputs` only if they gave a file (refine has no project assets, so describe it in the beats and
   the settings table instead and leave `inputs` empty), the six `layers` (prompt-craft), `avoid` (start
   from the universal list plus the categories that apply), and `rationale` (model, resolution, duration).
3. Apply the cross-cutting craft rules yourself, without asking (skip them for clean graphics, icons, logos
   and products; with a start frame keep only the light and motion parts):
   - **Depth planes:** fill far background, near background, placement and foreground, each with a value
     word (dark, lit, bright accent). The foreground names its frame edge. For shots wider than a medium,
     give the subject's size as a fraction of the frame.
   - **One named key:** its source, side of frame, height and hard or soft ("soft key from the frame-left
     window, high"). Fill none or low. Each practical carries its colour.
   - **What stays dark:** one line, except for high key and overcast looks.
   - **Natural finish:** `light_look.finish` with real-world imperfection; natural skin texture on any face.
   - **No trigger words:** drop "8k", "hyperdetailed", "hyperrealistic", "epic", "cinematic lighting",
     "beautiful lighting", "bokeh background", "flawless", "perfect skin" and "HDR", even when the user wrote
     them. Say in the settings table what you replaced.
   The detail is in `${CLAUDE_PLUGIN_ROOT}/docs/research/cinematic-composition-guide.md` and
   `cinematic-lighting-guide.md` (quick choosers at the top, cross-cutting rules at the end).
4. `sc card validate <file>`. Fix every error it lists.
5. `sc card compile <file> --model <id> --json`. It returns `prompt`, `negative_prompt` (only for models with
   a negative field), `params`, `adjustments` (values it corrected for the model, each with a reason),
   `dropped_fields` (what it trimmed to stay under the word cap), `unguarded` (avoid terms with no positive
   wording), `word_count` and `max_prompt_words`. It also writes the Prompt and Avoid sections into the card.
6. Read the compiled prompt as a director would. If a dropped field mattered, shorten something else in the
   layers and compile again. If `unguarded` lists something important, add positive wording to a layer
   (for example "steady locked-off frame" in camera) and compile again.

## 3. Show the result (this exact shape)

**Prompt for <Model name>** (<word_count> words)
```
<compiled prompt, paste-ready>
```

**Avoid**: if the model has a negative prompt field, a second code block with the negative prompt. Otherwise
one line: "This model has no negative field, so these are already phrased positively inside the prompt:
<terms>." List any `unguarded` terms as "Watch for: ...".

**Settings**

| Setting | Value | Why |
|---|---|---|
| Model | Seedance 2.5 | <one line> |
| Aspect | 9:16 | <one line> |
| Resolution | 720p draft / 1080p final | <one line: the smallest that meets the delivery> |
| Duration | 5 s | <one line: the cut length; note any adjustment the compiler made> |
| Takes | 2 | <one line> |
| Audio | off | <one line> |
| Start frame | your image | <only if they have one: "prompt describes motion only"> |

**Beats** (video only): a short table of time ranges and what happens (`0-2 s`, `2-5 s`).

Then: "Saved to <path>." and, only if they asked for options, **Alternatives**: a Safe version (fewer
moving parts, most likely to render cleanly) and a Bold version (one bigger creative swing), each one code
block. Never offer alternatives unasked.

Plain English throughout. Gloss any craft term the user may not know in a few words.

## 4. At most 3 questions, only where a wrong guess wastes credits

After the result, ask only what would change the cost or make the output unusable. One AskUserQuestion
call, 1 to 3 questions, the current assumption first and labelled "(Recommended)". Typical:

- Platform or aspect (a 16:9 clip is wasted on a Reel).
- Exact length (it sets the model and the cost; Veo only does 4, 6 or 8 s).
- Image or video, or "do you have a start frame?" (with a frame the prompt changes to motion only).
- Native audio on or off (it can change the model and the cost).
- Exact on-screen text, when there is any.

Never ask about taste you can decide well (lens, light, grade); decide it and show it in the settings table.
If nothing is risky, ask nothing and say "Tell me if any setting is off."

When they answer: update the card, `sc card validate`, `sc card compile` again, show the new result in the
same shape, and save again.

## 5. Save

`sc refine save <file>` validates the card and saves it as `<projects_root>/_refine/<date>-<slug>.md` (the
slug comes from the card title; it never overwrites, it adds -2, -3). Give the user the saved path.

If the user asks for the work to be tracked as a refine project instead: `sc project init --name "<name>"
--track refine`, `sc stage start refine`, put the card in `05_prompts/S010.md`, `sc stage done refine`.

## 6. Offer to generate

End with one line: "Want me to generate it? One question with the live price, then it renders and
downloads (about <N> credits)."

On yes, load the **quick** skill: `sc quick plan <this card> ...` prices it, one question with the price,
`sc quick go` generates, waits and downloads. Use the **producer** skill (single or full track) only when the
user wants drafts, a delivery check and hand-off, or more than one shot. The refine track itself never
generates.

## Rules

- Complete result first, questions second. Never answer a prompt request with only questions.
- Never more than 3 questions. Never ask what the request already says.
- Stay under the model's word cap (default 120 words, about 200 tokens); the compiler trims the
  lowest-priority fields first. Positive phrasing, one camera move per shot, concrete nouns and verbs.
- With a start frame: motion only (camera move, subject motion, beats). Never describe the frame again.
- Never claim a model feature or limit you have not read from `rules/models.json`, `sc route` or
  `higgsfield model get`. Never quote a credit price from memory.
- Never generate from this skill, and never run raw `higgsfield generate`.
