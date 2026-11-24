---
{
  "id": "S010",
  "title": "Short name for the shot",
  "kind": "video",
  "use_case": "social-vertical",
  "tier_plan": ["draft", "final"],
  "model": {"draft": null, "final": null, "upscale": null},
  "settings": {"aspect": "9:16", "resolution": "1080p", "duration_s": 3, "variants": 2, "audio": false},
  "handles_s": 0,
  "inputs": [],
  "layers": {
    "intent": {"use": "", "platform": "", "audience": "", "brand": ""},
    "subject": {"subject": "", "action": "", "wardrobe_props": "", "elements": "", "consistency": ""},
    "world": {"environment": "", "era": "", "time_of_day": "", "weather_season": "", "atmosphere": ""},
    "camera": {"shot_size": "", "angle": "", "lens": "", "dof": "", "composition": "",
               "movement": "", "movement_speed": "", "camera_look": ""},
    "light_look": {"setup": "", "quality": "", "direction": "", "color_temp": "", "practicals": "",
                   "palette_grade": "", "texture": "", "style_ref": "", "mood": ""},
    "time_output": {"beats": [], "pacing": "", "loop": false,
                    "transition_in": "", "transition_out": "", "audio": "", "on_screen_text": ""}
  },
  "avoid": ["blurry", "watermark", "flicker", "morphing"],
  "status": "draft",
  "approved_said": null,
  "rationale": {"model": "", "resolution": "", "duration": ""},
  "checked_rules_version": "0.1.0"
}
---

## Prompt (compiled for <model>)
(run: python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py" card compile <this file> --model <model id>)

## Avoid (guarded against)
- blurry
- watermark
- flicker
- morphing

## Beats
(none yet)

## Why these settings
- model: why this model fits the shot (and why not a cheaper one)
- resolution: the smallest size that meets the delivery
- duration: the exact cut length, plus handles if the edit needs them

<!--
How to fill this card

The front matter (between the two '---' lines) is JSON. It is the source of truth; the
sections below are refreshed by `sc.py card compile`. Make a new card with
`sc.py card new --shot S010 --use-case <preset> --from-text "..."` rather than copying this file.

id            Shot id, numbered in tens: S010, S020, S030. Insert a shot between two with S015.
kind          "video" or "image".
use_case      A preset id from rules/presets.json (social-vertical, broll-insert, thumbnail, icon-ui ...).
tier_plan     Which tiers this shot goes through: board (cheap still first), draft, final, upscale.
model         Model id per tier, chosen by routing (`sc.py route ...`). null until chosen.
settings      aspect ("9:16"), resolution ("720p", "1080p", "1k", "2k"), duration_s (the cut
              length in seconds, video only), variants (1-8), audio (native sound, video only).
handles_s     Extra seconds at each end for the editor. The generated length is
              duration_s + 2 x handles_s, fitted to what the model allows.
inputs        Assets from project.json: {"asset": "A003", "as": "start_frame|end_frame|reference|character|style"}.
              Never use an asset whose rights are reference-only.
              With a start frame, the prompt describes only motion: camera move, subject action, beats.

layers        Six layers. Fill what matters and leave the rest empty. Vocabulary and help for every
              field are in rules/taxonomy.json (the prompt-craft skill explains them).
  intent      Why the shot exists. Planning only; never written into the prompt.
  subject     Who or what, doing what. Concrete nouns, present-tense verbs.
  world       Place, era, time of day, weather, what is in the air.
  camera      Shot size, angle, lens, depth of field, composition, ONE clear move and its speed.
  light_look  Lighting setup, quality, direction, colour temperature, practicals, grade, texture,
              style and mood.
  time_output Beats as time ranges ({"t": "0-2", "what": "..."}), pacing, loop, transitions,
              native audio, exact on-screen text.

avoid         Short phrases to guard against. If the model has a negative prompt field they go
              there; otherwise each is rewritten into positive wording (rules/positive_rewrites.json).
              Anything with no rewrite is reported as "unguarded".
status        draft -> approved -> generated -> final. Anything past draft needs approved_said:
              the user's own words.
rationale     One line each: why this model, resolution and duration.

When the prompt is too long for the model, fields are dropped lowest priority first:
texture, then practicals, then era, then camera look, and so on. Subject, action, camera
move and shot size are never dropped.
-->
