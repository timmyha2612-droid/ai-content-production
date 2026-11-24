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
| PR-11 | Continuity between adjacent cards: screen direction, light direction, time of day, wardrobe and props match the shot list's continuity notes and the bible. | Read neighbouring cards side by side. | judgement | major |
| PR-12 | Generation risks are handled: no legible text asked of the model (text goes to motion graphics), hands and products use image first or references, crowds are avoided or simplified. | Read the subject and time_output layers (`on_screen_text` should be empty or say "added in post"). | judgement | major |
| PR-13 | `tier_plan` is sensible: `board` for image-first shots, `final` only where a final is needed, `upscale` only if the delivery needs more pixels than the final model makes. | Compare with the shot list's image_first flag, the preset and the model's resolutions. | fact | major |
| PR-14 | Variants are 1-2 for drafts unless the job card says otherwise (cost). | Front matter `settings.variants`. | judgement | minor |
| PR-15 | The rationale explains the model, resolution and duration in plain words. | Read `rationale`. | fact | minor |
| PR-16 | No real person's name or likeness, no brand the user does not own, no private detail from the brief in the prompt. | Read the compiled prompt. | fact | blocker |
| PR-17 | Card status: cards waiting for the user's approval are `draft`; any card marked `approved` has `approved_said` with words, not a placeholder. | Front matter `status` and `approved_said`. | fact | major |
