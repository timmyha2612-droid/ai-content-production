# Prompting Higgsfield models, family by family

Notes for writing prompts that each model renders well. Limits change: the source of truth is
`rules/models.json` (each model has a `checked_at` date and `strengths`, `weaknesses`, `gotchas`), then
`higgsfield model get <id>` live. Costs only ever come from `sc gen estimate`. Notes marked *(practice)* are
working habits, not documented behaviour; drop them if your results say otherwise, and log what you learn
with `sc lessons add "..." --kind model`.

## Rules for every model

- **About 200 tokens at most** (shotcraft's default cap is 120 words). Long prompts distort.
- **Positive phrasing.** No Higgsfield image or video model on the CLI has a negative prompt field (only
  Text to 3D does). The compiler turns the avoid list into positive wording.
- **Image to video: motion only.** With `--start-image` the prompt describes the camera move, the subject's
  motion and the beats. Re-describing the frame fights the frame.
- **Image to image: the change only.** "Turn into a watercolour, soft paper texture", not the whole picture.
- **Seed is mostly not exposed and fps is not a parameter.** Expect variation between takes: plan 2 takes
  for drafts.
- **The CLI corrects out-of-range values** (aspect, duration, resolution) and reports `adjustments`;
  unknown parameters are a hard error. shotcraft's compiler corrects them first and tells you why.
- **Blocked content ends the job:** `nsfw` and `ip_detected`. No real public figures, trademarks, branded
  characters or sexual content. Describe "a sports car in metallic red", not a brand and model name.
- **Media roles differ per model** (start_image, end_image, image_references, video_references,
  audio_references). shotcraft maps the card's `inputs` to them and drops what the model cannot take, with a note.

## Quick pick

| Need | First choice | Cheaper draft | Notes |
|---|---|---|---|
| General video, motion, people, multi-shot | Seedance 2.5 | Seedance 2.0 fast, Kling 3.0 Turbo | Seedance 2.0 for native 4K |
| Strong physics on a budget | Minimax Hailuo | | No audio |
| Dialogue and native sound | Veo 3.1 | Veo 3.1 Lite | 4, 6 or 8 s only |
| Named camera styles, genre, cinema look | Cinema Studio 4.0 | | Video 3.5 for camera_style presets |
| Ads, UGC, product showcase with avatars | Marketing Studio Video | | Runs Higgsfield's ad flow |
| Photoreal people, editorial, consistent face | Soul 2.0 (+ Soul ID) | | Soul Cinema for cinematic stills |
| Faces, character sheets, face edits | Seedream 5.0 Pro | Seedream 5.0 Lite | |
| Characters, cartoons, quick edits | Nano Banana 2 (`nano_banana_flash`) | Nano Banana 2 Lite | |
| Top fidelity, accurate text and layout | Nano Banana Pro (`nano_banana_2`) | | The id trap below |
| Text on images, design, SVG or GIF | GPT Image 2.6 | | |
| Logos, icons, vector look | Recraft V4.1 | | Prompt only |
| Precise adherence, a different look | FLUX.2 | | Flux Kontext for edits |
| Places with no people | Soul Location | | Prompt only |

`sc route` makes this pick from `rules/routing.json`; this table is for judging it.

## Seedance (Bytedance): `seedance_2_5`, `seedance_2_0`, `seedance_2_0_mini`, `seedance1_5`

- **Seedance 2.5**: Higgsfield's default video model. 4-30 s in one take, 480p/720p/1080p. Multi-shot,
  consistent identity, heavy motion, image to video, editing and extension. Modes `t2v` (prompt only) and
  `omni_reference` (with media); shotcraft switches to `omni_reference` when the card has inputs.
- **Seedance 2.0**: up to native 4K; `--mode fast` for cheap 480p/720p drafts (fast is 480p/720p only).
  Up to 9 images (start and end frames count), 3 videos, 3 audio, 12 media in total; audio references need an
  image or video too. Native audio (`generate_audio`) is on by default: shotcraft sends the card's audio
  setting. Has a `genre` parameter.
- **Seedance 2.0 Mini**: 480p/720p only; cheap drafts with the same references.
- **Seedance 1.5 Pro**: 4, 8 or 12 s; budget clean single takes; audio on by default; end frame needs a start frame.
- **Prompt style:** subject and action first, then one camera move with its speed, then light and look.
  Seedance follows camera language well; name the move plainly ("slow dolly in", "orbit right").
  *(practice)* For a deliberate multi-shot take, give each shot its own short sentence in order with its
  timing ("0-3 s: wide of the bay at dawn. 3-6 s: close-up of the rower's hands."), and keep shotcraft's
  default of one shot per card unless the shot list plans a multi-shot take.
- **Traps:** 2.5 tops out at 1080p (say why when switching to 2.0 for 4K). Do not downgrade to 1.5 only
  because its durations are listed explicitly. Text on screen renders poorly: add it in motion graphics.

## Kling: `kling3_0`, `kling3_0_turbo`, `kling2_6`

- **Kling 3.0**: 3-15 s, 16:9 / 9:16 / 1:1. Size by `--mode std|pro|4k`. Start and end frames. Good motion
  and physics at a lower cost; multi-shot and audio sync. `--sound` defaults to on: shotcraft sends off
  unless the card wants audio.
- **Kling 3.0 Turbo**: fast and cheap simple motion, 720p/1080p, a single start frame only, no end frame, no
  references. A good draft model.
- **Kling 2.6**: 5 or 10 s, start frame only, sound on by default.
- **Prompt style:** single-plane scenes with one clear action read best. Physical verbs and weight ("the
  wave crashes and sprays over the rocks"). Keep subjects few.
- **Traps:** *(practice)* identity drift and rubbery motion on long or busy takes (shotcraft adds these to the
  avoid list for Kling 3.0). Prefer a start frame for people.

## Veo (Google): `veo3_1`, `veo3_1_lite`, `veo3`

- **Veo 3.1**: ultra-realistic, native dialogue and sound, lip-sync. Durations **4, 6 or 8 s only**;
  **16:9 or 9:16 only**; `--quality basic|high|ultra` instead of a resolution flag; no flag to turn audio off.
  Start frame only (max 1).
- **Veo 3.1 Lite**: cheaper, for drafts and volume; start and end frames (both set means 8 s); audio off by
  default.
- **Veo 3**: needs a start frame, no duration flag.
- **Prompt style:** write dialogue as a short quoted line with who says it and how ("she says, warmly:
  'We open at six.'"). Describe the sound you want (room tone, footsteps, distant traffic). Keep one speaker
  per shot where possible.
- **Traps:** a 5 s cut needs a 6 s take trimmed in the edit (the compiler picks the nearest, longer on a tie).
  A 1:1 or 4:5 delivery must be cropped from 9:16 or 16:9. *(practice)* It may invent captions or text;
  shotcraft guards "extra text" for Veo 3.1.

## Minimax Hailuo: `minimax_hailuo`

- 6 or 10 s; resolution 512 / 768 / 1080 (1080 not at 10 s); no aspect flag; no audio.
- Variants: `minimax-2.3` (default) works from a prompt alone; the other variants need a start or end frame;
  end frame is not supported on the 2.3 variants.
- **Prompt style:** cheap with strong physics: lean on physical action (pouring, falling, splashing, cloth).
- **Traps:** framing follows the start frame when there is one; with no aspect flag, give it a start frame
  at the delivery aspect when the aspect matters.

## Wan: `wan2_7`, `wan2_6`

- **Wan 2.7**: synchronized audio with consistent characters; 2-15 s; 720p/1080p; end frame needs a start
  frame; one audio reference at most.
- **Wan 2.6**: 5, 10 or 15 s; size by `--quality 720p|1080p`; cheap, stylised, experimental; video references
  allow only 5 or 10 s; some configurations reject media.
- **Prompt style:** strong for intentionally artistic looks; name the style clearly (ink wash, claymation,
  painterly).

## Cinema Studio (Higgsfield): `cinematic_studio_video_4_0`, `cinematic_studio_video_3_5`, `cinematic_studio_3_0`, `cinematic_studio_video_v2`, `cinematic_studio_video`; stills `cinematic_studio_2_5`

- **4.0**: the modern default when the user asks for Cinema Studio. 4-15 s, up to 1080p, camera, lens, light
  and genre controls, native audio on by default. Does not show in `higgsfield model list`; check with
  `higgsfield model get`.
- **Video 3.5**: named controls as parameters: `camera_style` (classic_static, silent_machine, one_take,
  epic_scale, intimate_observer, impossible_camera, documentary_snap, raw_chaos, dreamy_flow),
  `light_scheme` (soft_cross, contre_jour, overhead_fall, window, practicals, silhouette), `color_grading`
  (naturalistic_clean, bleached_warm, hyper_neon, teal_orange_epic, sodium_decay, cold_steel, bleach_bypass,
  classic_bw), `genre`, multi-shot. These three style axes cannot be combined with `style_prompt`.
  Default duration is 15 s: always pass the duration.
- **3.0**: up to 4K, multi-shot, speed ramps (`speedramp`).
- **Trap:** on 3.0 and 3.5 `--prompt_language` defaults to Chinese (`zh`); shotcraft sends `en`. If you ever
  run one by hand, set it.
- **Prompt style:** when the model has a parameter for it (camera style, light scheme, grade, genre), use
  the parameter and keep the prompt for subject, action and beats. Do not say the same thing in both.
- **Cinema Studio Image 2.5**: cinematic stills up to 4K, dramatic film look; good for boards in a cinematic
  piece.

## Soul (Higgsfield): `text2image_soul_v2`, `soul_cinematic`, `soul_cinema_studio`, `soul_location`, `soul_cast`

- **Soul 2.0**: photoreal people, UGC, editorial, fashion. Size by `--quality 1.5k|2k`. Curated styles via
  `--style_id` (not with an image reference). Takes a Soul ID for a consistent face.
- **Soul ID** is made from 5-20 photos of a person who agreed (`higgsfield soul-id create` goes through
  shotcraft's gate; ask the producer). Never make one of a real person without their consent.
- **Soul Cinema** (`soul_cinematic`): cinematic stills, film-grade light, one image reference at most.
  `soul_cinema_studio` is a separate model with style presets and `enhance_prompt`.
- **Soul Location**: places with no people, prompt only, fixed sizes per aspect.
- **Soul Cast**: characterful personas, text only, 16:9 only. Only when the user names it.
- **Prompt style:** editorial language works: wardrobe, styling, pose, setting, light ("soft window light,
  candid half-smile, linen shirt, film photograph look").

## Nano Banana (Google): `nano_banana_flash`, `nano_banana_2`, `nano_banana_2_lite`, `nano_banana`

- **TRAP: the id `nano_banana_2` is Nano Banana Pro.** Nano Banana 2 is `nano_banana_flash`. Say the display
  name to the user and check the id twice.
- **Nano Banana 2** (`nano_banana_flash`): the fast everyday default for characters, cartoons and edits; up
  to 14 image references; 1k/2k/4k.
- **Nano Banana Pro** (`nano_banana_2`): top fidelity, accurate text and layout, up to 4K. Use when the user
  names it or text accuracy matters.
- **Nano Banana 2 Lite**: 1k only, quick cheap reference edits; aspect `auto` needs an image reference.
- **Prompt style:** conversational instructions work well for edits ("Keep the person and the pose. Change
  the jacket to deep green corduroy."). For new images, the usual order: subject, setting, light, style.

## GPT Image (OpenAI): `gpt_image_2_6`, `gpt_image_2_6_flare`, `gpt_image_2_5`, `gpt_image_2`

- **GPT Image 2.6** (Sunburst): Higgsfield's default image model: general images, reference-guided editing,
  design, typography, UI. Native animated GIF and SVG output via `--output_format`.
- SVG takes no image references. Flare is a separate model id (`gpt_image_2_6_flare`), not a variant flag.
- **Prompt style:** put on-image text in double quotes and say where it goes and how it looks ("headline
  'OPEN LATE' in bold condensed white sans-serif, top third"). Describe layout like a designer: grid, margins,
  hierarchy. Good for thumbnails and banners.

## Seedream (Bytedance): `seedream_v5_pro`, `seedream_v5_lite`, `seedream_v4_5`

- **5.0 Pro**: faces, character sheets, complex scene edits with faces; up to 10 image references;
  1k / 1.5k / 2k.
- **5.0 Lite**: faster instruction-based edits. **4.5**: earlier, use when named.
- **Prompt style:** for a character sheet, ask for the layout explicitly ("character turnaround: front,
  three-quarter, profile and back views, neutral grey background, same outfit"). For face edits, say what
  must stay the same.

## Recraft: `recraft_v4_1`

- Logos, icons, flat and vector-like illustration, brand marks, controlled palettes.
- **Prompt only: no image references.** `--model_type vector` for vector output; `--colors` and
  `background_color` take `#RRGGBB`.
- **Prompt style:** short and graphic: object, style, line weight, palette ("a coffee cup icon, flat
  geometric, 2 px uniform strokes, two colours #1E3A5F and #F2C14E, centred, plain background"). No camera
  or lighting words. Use the icon avoid list (fine detail, thin lines, photorealism, text in icon).

## Flux (Black Forest Labs): `flux_2`, `flux_kontext`

- **FLUX.2**: precise prompt adherence; a different look from the Nano Banana family.
- **Flux Kontext**: context-aware editing and style transfer, typography remix; up to 4 image references; no
  resolution control.
- **Prompt style:** Flux follows long, specific descriptions closely, but shotcraft's word cap still applies;
  spend the words on the subject and the style.

## Others worth knowing

- **Marketing Studio Video / Image**: Higgsfield's ad flow with avatars, products, hooks and settings. The
  default for "make an ad" on the Higgsfield side; default video duration 15 s, so always pass the duration.
- **Gemini Omni Flash** (and 1.1): fast reference-to-video with Google-style understanding.
- **Grok Video 1.5**: bold, stylised image to video from a required start frame.
- **Z Image**: the fastest, cheapest image drafts.
- **Upscalers** (`topaz_image`, `topaz_video`, `bytedance_*_upscale`, `video_upscale`): only when the delivery
  needs more pixels than the final model gives (the `upscale` tier).
