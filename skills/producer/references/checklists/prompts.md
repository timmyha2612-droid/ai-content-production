# QA checklist: prompts

Stage output: one prompt card per shot in `05_prompts/<shot>.md` (format:
`${CLAUDE_PLUGIN_ROOT}/templates/prompt-card.md`). Gate: QA PASS, and every card validates.

Read: the shot list, the bible (look line, environment, character and prop lines), every card, the preset,
`${CLAUDE_PLUGIN_ROOT}/rules/models.json` and `routing.json` (through `sc route`), and
`${CLAUDE_PLUGIN_ROOT}/skills/prompt-craft/SKILL.md`.

You are read-only: do **not** run `sc card compile` (it writes the compiled prompt back into the card). To see a
compile without writing, run:

```
python3 -c "import sys,json; sys.path.insert(0,'${CLAUDE_PLUGIN_ROOT}/scripts'); from shotcraft import cards,compiler,rules; P='<project>'; meta,_=cards.read(P+'/05_prompts/<shot>.md'); prof,err=rules.model_profile('<model id>', project=P); print(err or json.dumps(compiler.compile(meta, prof, rules.compiler_rules(P)), indent=1))"
```

It returns the prompt, params, `adjustments`, `unguarded`, `dropped_fields`, `word_count` and `warnings`.

| id | check | how | kind | severity |
|---|---|---|---|---|
| PR-01 | Every shot on the shot list has a card, and every card validates. | `python3 -c "import sys,json; sys.path.insert(0,'${CLAUDE_PLUGIN_ROOT}/scripts'); from shotcraft import stages; print(json.dumps(stages.check_evidence('<project>','prompts'), indent=1))"`, and `sc card validate 05_prompts/<shot>.md --json` for each card. | fact | blocker |
| PR-02 | Settings match the delivery and the shot list: aspect, resolution tier (draft cheap, final no bigger than the delivery needs), `duration_s` equal to the shot list's duration, `handles_s` from the preset. | Compare front matter with the shot list and preset. | fact | blocker |
| PR-03 | The model for each tier is a real, routed choice: the model exists in `models.json`, and for the shot's need and length it is the routing pick or the card's rationale says why not. | `sc route --use-case <preset> --tier draft\|final --kind <kind> --duration <generated s> [--needs ...] --json` | fact | major |
| PR-04 | The compile for each tier's model is clean: no `adjustments` that change the meaning (a different aspect, a duration much longer than the shot), no `warnings` left unexplained. | The read-only compile above, per tier. Quote the adjustment. | fact | major |
| PR-05 | Prompt length is under the model's `max_prompt_words`; nothing important was dropped (subject, action, movement, shot size are never dropped; check `dropped_fields`). | The compile's `word_count`, `max_prompt_words` and `dropped_fields`. | fact | major |
| PR-06 | Avoid terms are guarded: every avoid item has a positive rewrite or goes in a negative field. `unguarded` items are listed with a suggested rewrite. | The compile's `unguarded`. | fact | minor |
| PR-07 | The bible lines are used word for word: the look line in light_look, the environment line in world, each character's consistency line, each prop line. Wording drift between cards of the same scene is a finding. | Compare each card's layers with the bible files. | fact | major |
| PR-08 | One subject action and one camera move per shot; the move and speed fit the duration (`${CLAUDE_PLUGIN_ROOT}/skills/prompt-craft/references/camera-movement-cookbook.md`). | Read the subject and camera layers. | judgement | major |
| PR-09 | Image-to-video cards (a start frame input) describe only the motion: camera move, subject motion, beats. They do not describe the frame again. | Read the card; the compile's `motion_only` should be true. | fact | major |
| PR-10 | Inputs are allowed: no input asset has rights `reference-only`; every input asset exists; `as` is start_frame, end_frame, reference, character or style; the model accepts that input (start/end frame, number of image refs). | `sc asset list --json` for rights; the model profile for `start_frame`, `end_frame`, `refs`. | fact | blocker |
| PR-11 | Continuity between adjacent cards: screen direction, light direction (the key stays on the same side of frame inside a scene, and flips only when the camera crosses the line), time of day, wardrobe and props match the shot list's continuity notes and the bible. | Read neighbouring cards side by side. | judgement | major |
| PR-12 | Generation risks are handled: no legible text asked of the model (text goes to motion graphics), hands and products use image first or references, crowds are avoided or simplified. | Read the subject and time_output layers (`on_screen_text` should be empty or say "added in post"). | judgement | major |
| PR-13 | `tier_plan` is sensible: `board` for image-first shots, `final` only where a final is needed, `upscale` only if the delivery needs more pixels than the final model makes. | Compare with the shot list's image_first flag, the preset and the model's resolutions. | fact | major |
| PR-14 | Variants are 1-2 for drafts unless the job card says otherwise (cost). | Front matter `settings.variants`. | judgement | minor |
| PR-15 | The rationale explains the model, resolution and duration in plain words. | Read `rationale`. | fact | minor |
| PR-16 | No real person's name or likeness, no brand the user does not own, no private detail from the brief in the prompt. | Read the compiled prompt. | fact | blocker |
| PR-17 | Card status: cards waiting for the user's approval are `draft`; any card marked `approved` has `approved_said` with words, not a placeholder. | Front matter `status` and `approved_said`. | fact | major |
| PR-18 | Depth planes *(live action)*: the frame is built in layers like a multiplane set-up. The card names a foreground (`world.foreground`) and at least one background plane (`world.background_near` or `background_far`), where the subject stands (`subject.placement`) and how the place acts on them (`subject.interaction`: light spill, weather, contact, scale). Video cards that move the camera say how the planes move (`world.parallax`). A subject with no interaction looks pasted in. | Read the subject and world layers; the compile's `warnings` must not include "No depth planes". Image-to-video cards keep only interaction and parallax (the start frame already shows the planes). | fact | major |
| PR-19 | Natural finish: cards on a natural preset (social, YouTube, b-roll) have `light_look.finish` filled (lived-in detail, real-lens character) and "cgi look" and "too perfect" in avoid; cards on a true_to_life preset (real estate) have the true-to-life default (true-to-life colour, slightly uneven motivated light, real-lens character) and "cgi look" and "flat even lighting". A symmetrical composition carries no asymmetry wording. Clean presets (icons, logos, products, thumbnails) leave finish empty. | The preset's `finish` in `${CLAUDE_PLUGIN_ROOT}/rules/presets.json`; the card's light_look and avoid. | fact | minor |
| PR-20 | No grain clash: if texture or finish asks for grain or film stock, avoid does not also ask for no noise or no grain. The compiler drops the clashing guard and warns; fix the card so the warning goes. | The compile's `warnings`. | fact | minor |

## Composition and light (PR-21 to PR-36)

These items come from the composition and lighting guides:
`${CLAUDE_PLUGIN_ROOT}/docs/research/cinematic-composition-guide.md` and
`${CLAUDE_PLUGIN_ROOT}/docs/research/cinematic-lighting-guide.md`. Each guide opens with a quick chooser (story
intent to technique or setup) and lists, per technique, what models get wrong. They apply to live-action looks;
on clean presets (icons, logos, products, thumbnails) mark them `n/a`. Image-to-video cards describe motion only,
so mark the frame items (PR-22 to PR-26, PR-29) `n/a` there. Items the prompts stage cannot check by reading the
card alone are `judgement`: the verifier looks at them.

*Key* = the main light. *Fill* = light that lifts the shadows. *Practical* = a lamp, screen or sign seen in shot.

| id | check | how | kind | severity |
|---|---|---|---|---|
| PR-21 | Composition from intent: the shot's story intent maps to a named technique from the composition chooser (for example "outsider" to a frame within a frame), at most three combined: one geometry, one depth, one light technique. | The shot list's `composition` column and the card's `camera.composition`, against the chooser. | judgement | minor |
| PR-22 | Depth planes filled, with values: far background, near background, placement and foreground are all filled, or the card says why one is missing (extreme close-up, top-down, a silhouette against a sun disc). Each plane carries a value word as well as content (dark, lit, bright accent, clipped), and the planes follow one of the four depth patterns: dark-light-dark, dark-lit-bright, dark-lit-patterned, bright recedes. This is stricter than PR-18. | Read the world and subject layers. Filled-or-reason is a fact; the pattern fitting the setup is the judgement. | judgement | minor |
| PR-23 | The foreground is specific, cropped and names its frame edge ("dark door jamb filling the left edge"), not a tidy, fully visible object. One focus plan: deep focus, or one soft foreground plane; never an even blur on everything but the subject. | Read `world.foreground` and `camera.dof`. | judgement | minor |
| PR-24 | Subject size as a number: any shot wider than a medium gives the subject's share of the frame ("a tenth of the frame height", "less than 5% of the frame"). Models enlarge people unless told. | `camera.shot_size`; then look for the fraction in `subject.placement` or `camera.composition`. | fact | minor |
| PR-25 | Gaze or travel direction is stated and points into space: into the open side of the frame or into depth. Straight into the lens only for confrontation. | Read `subject.action` and `subject.placement`. | judgement | minor |
| PR-26 | The palette is named in two or three colours, with no default teal-and-orange grade standing in for motivated colour. | Read `light_look.palette_grade`. | fact | minor |
| PR-27 | No trigger words in the compiled prompt: "8k", "hyperdetailed", "ultra detailed", "hyperrealistic", "epic", "cinematic lighting", "beautiful lighting", "well lit", "bokeh background", "flawless", "perfect skin", "HDR", and "studio lighting" outside studio work. | Search the read-only compile's `prompt`. Quote each hit. | fact | minor |
| PR-28 | *(video)* The camera move has a speed, or the shot is locked-off; `world.parallax` is written for any move. The light is fixed to the set (not to the head or the camera), and any flicker or drift is written on purpose ("gentle flame flicker"). | Read the camera, world and light_look layers. | judgement | minor |
| PR-29 | *(9:16)* The subject sits in the lower third, the headroom is described as a surface (textured wall, shadow, light) that can carry captions, and nothing critical sits in the platform's UI zones (top and bottom on Reels, right and bottom on TikTok). | Read `subject.placement`, `camera.composition` and the world layers. | judgement | minor |
| PR-30 | Light setup from intent: `light_look.setup` comes from the lighting chooser row that matches the shot's intent, and does not hit that setup's "do not use" line (for example, butterfly for gritty documentary; split when both eyes must read). The setup's own failure modes are guarded in the wording (Rembrandt triangle closed at the bottom; butterfly shadow straight down; split line on the nose bridge; rim on one side only; reflections under their sources). | The setup's section in the lighting guide, against the card's light_look. | judgement | minor |
| PR-31 | One key: the card names one key light with its world source, side of frame, height, and hard or soft ("hard key from the frame-left window, high"). `direction` holds a side or a position (frame-left, frame-right, behind, above, below), never only "cinematic". Fill is "none" or "low", or a second light has a job and a source and stays weaker than the key (backlit setups: the rim is the key). | Read `light_look.setup`, `quality`, `direction` and `practicals`. | fact | major |
| PR-32 | The key's source is shown or proven: it is in frame, at the frame edge, or proven by a footprint in a depth field (a sun patch, a pool on the table, a cast shadow, a beam in haze). `subject.interaction` says where the light lands on the subject ("lamp light on her hands and left cheek"). Describe the cause (source position and size), not a pattern painted on. | Read the world layers, `subject.interaction` and `light_look.practicals`. | judgement | minor |
| PR-33 | Colour per source: each practical carries its colour ("warm tungsten lamp", "orange sodium streetlight"), and the ambient colour is stated. | Read `light_look.practicals` and `color_temp`. | fact | minor |
| PR-34 | What stays dark is stated ("the room falls into darkness", "background near-black"), except on high key and overcast setups. Models only leave things dark when told. | Read the light_look and world layers. | fact | major |
| PR-35 | Finish has substance: on natural and true_to_life presets, `light_look.finish` has at least two imperfection terms; *(people)* every card with a face has natural skin texture wording there ("natural skin texture, visible pores, fine lines"). Adds to PR-19. | Read `light_look.finish`. | fact | minor |
| PR-36 | The scene light plan's anchor phrase (the `Scene light plan (scene <n>):` line in the environment file's Light section, for example "north window on the left wall, one table lamp right of the bed") appears word for word in every card of that scene. Models keep no memory between shots, so the shared phrase rebuilds the same light. | Compare each card's light_look with that bible line; it must also match the Scene light plans block under the shot list word for word. | fact | major |
