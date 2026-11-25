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
    "subject": {"subject": "", "action": "", "placement": "", "interaction": "",
                "wardrobe_props": "", "elements": "", "consistency": ""},
    "world": {"environment": "", "background_far": "", "background_near": "", "foreground": "",
              "parallax": "", "era": "", "time_of_day": "", "weather_season": "", "atmosphere": ""},
    "camera": {"shot_size": "", "angle": "", "lens": "", "dof": "", "composition": "",
               "movement": "", "movement_speed": "", "camera_look": ""},
    "light_look": {"setup": "", "quality": "", "direction": "", "color_temp": "", "practicals": "",
                   "palette_grade": "", "texture": "", "finish": "", "style_ref": "", "mood": ""},
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
              placement: where the subject stands in the space (which plane, which part of the
              frame, what is around them). It is the midground of the depth sentence.
              interaction: how the place and the subject act on each other: light from the place
              on them (neon spill on a cheek), weather on them (wet hair, breath fogging), their
              contact with the world (a footprint in a puddle), scale (small against the street).
              Models get this wrong most often; a subject that ignores its surroundings looks
              pasted in.
  world       Place, era, time of day, weather, what is in the air. The depth planes build the
              frame in layers, like a multiplane set-up in classic animation:
              background_far   the most distant plane: sky, skyline, hills. Often soft and hazy.
              background_near  the plane just behind the subject: shopfront, back wall, shelves.
              foreground       what sits between camera and subject: rain on glass, a cup edge,
                               a doorframe. Usually out of focus. It makes a frame feel shot.
                               Name it, crop it and say which frame edge it sits on ("dark
                               door jamb filling the left edge"). Usually the darkest plane.
              parallax         how each plane moves and how fast (video only; image cards skip
                               it). Near planes move faster than far ones on a camera move.
              The planes print as one "depth" sentence after the world sentence and before camera:
              far background; background; midground (placement); foreground; depth motion.
              Compile warns "No depth planes" when environment is set but no plane is.
              With a start frame, the static planes are dropped (the frame already shows them);
              interaction and parallax are kept.
  camera      Shot size, angle, lens, depth of field, composition, ONE clear move and its speed.
              composition: the technique the shot list chose for the shot's intent (frame within
              a frame, leading lines, negative space ...), at most three combined. For anything
              wider than a medium, give the subject's size as a fraction of the frame ("a tenth
              of the frame height"); models enlarge people unless told.
  light_look  Lighting setup, quality, direction, colour temperature, practicals, grade, texture,
              finish, style and mood.
              Name ONE key (the main light) with its source in the world, side of frame, height and
              hardness: "hard key from the frame-left window, high". direction always holds a side
              or a position, never only "cinematic". Fill is "none" or "low".
              Say what stays dark ("the room falls into darkness"), except for high key and
              overcast looks. Models only leave things dark when told.
              practicals: every lamp, screen or sign carries its colour ("warm tungsten desk lamp",
              "cool blue phone light"); state the ambient colour too.
              In a scene, repeat the scene light plan's anchor phrase word for word on every card.
              finish: real-world imperfection (lived-in wear, real-lens behaviour such as slight
              vignetting and gentle focus falloff, a little handheld life). Fill it for live-action
              looks. On any card with a face, it carries natural skin texture ("visible pores, fine
              lines"); never "flawless", "perfect skin" or "HDR". For presets marked "natural", `card new` fills it and adds "cgi look" and "too
              perfect" to avoid; for "true_to_life" (real estate) it fills the true-to-life default and
              adds "cgi look" and "flat even lighting". A symmetrical composition drops asymmetry
              wording. Leave it empty for clean graphics, icons
              and products. It is a craft fix for a natural look, not a way to beat AI detectors
              or hide a watermark; realistic AI content still needs the platform's AI label when
              it is posted. If texture or finish asks for grain, compile
              drops "noise" and "grain" from avoid and warns.
  time_output Beats as time ranges ({"t": "0-2", "what": "..."}), pacing, loop, transitions,
              native audio, exact on-screen text.

avoid         Short phrases to guard against. If the model has a negative prompt field they go
              there; otherwise each is rewritten into positive wording (rules/positive_rewrites.json).
              Anything with no rewrite is reported as "unguarded".
status        draft -> approved -> generated -> final. Anything past draft needs approved_said:
              the user's own words.
rationale     One line each: why this model, resolution and duration.

Prompt order: subject, action and interaction; world; depth; camera; light and look;
time and beats; style.

When the prompt is too long for the model, fields are dropped lowest priority first:
texture, then practicals, then era, then camera look, and so on. Among the new fields,
parallax goes first, then far background, finish, near background and foreground; placement
and interaction are kept longest. Subject, action, camera move and shot size are never dropped.
-->
