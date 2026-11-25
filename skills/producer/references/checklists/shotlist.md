# QA checklist: shot list

Stage output: `03_script/shotlist.md`, a markdown table (format:
`${CLAUDE_PLUGIN_ROOT}/skills/director/references/shotlist-format.md`). Gate: QA PASS.

Read: the job card, the script, the shot list, the preset (aspect, `shot_duration`, `handles_s`), and
`${CLAUDE_PLUGIN_ROOT}/rules/models.json` for the duration limits of the models the plan points at.

| id | check | how | kind | severity |
|---|---|---|---|---|
| SL-01 | The table parses: every shot has an id like S010, a duration_s greater than 0 and a purpose. | `python3 -c "import sys,json; sys.path.insert(0,'${CLAUDE_PLUGIN_ROOT}/scripts'); from shotcraft import stages; print(json.dumps(stages.check_evidence('<project>','shotlist'), indent=1))"` | fact | blocker |
| SL-02 | No id twice; ids in steps of 10 (inserts like S015 and split takes like S010A are fine). | Read the id column. | fact | major |
| SL-03 | The durations add up to the delivery length within 0.5 s, and match the script's rows. | Add them; compare with the script's time ranges. | fact | blocker |
| SL-04 | Every script row is covered by at least one shot, and every shot comes from a script row. | Map shots to rows. | fact | major |
| SL-05 | Shot lengths sit inside the preset's `shot_duration` range (if it has one), and the hook shot is short enough for the platform. | Compare with the preset. | fact | minor |
| SL-06 *(video)* | Each shot's generated length (its duration plus 2 x handles) fits at least one model the plan can use, or the shot is split. A shot longer than any one take is a finding. | `sc route --use-case <preset> --tier draft --kind video --duration <generated length>` (read-only) for the long shots. | fact | blocker |
| SL-07 | `kind` is set (video or image) where it is not obvious, and the image-first flag is set on video shots with people, a product, text, a complex move, 8 s or longer, or an end frame. | Read each row; apply the rule in the director skill. | judgement | major |
| SL-08 | Each purpose says what the viewer must get from the shot, not what the shot shows. | Read the purpose column. | judgement | minor |
| SL-09 | One camera idea per shot (no "push in then orbit"); the move fits the purpose and the length (fast moves need time to read). | Read the shot and move columns. | judgement | major |
| SL-10 | Coverage and rhythm: shot sizes vary across cuts; no two adjacent shots at the same size and angle of the same subject (a jump cut) unless meant. | Read the sequence. | judgement | minor |
| SL-11 | Continuity notes are there where shots join: screen direction, eyelines, the side of the 180-degree line, matched frames, light direction. | Read the continuity column for every cut that shares a subject or space. | judgement | major |
| SL-12 | Motion graphics are listed per shot (text, lower thirds, end card) and nothing that needs legible text is left to generation. | Compare with the script's on-screen text. | fact | major |
| SL-13 | The user's own material is used where the job card says so (`source` column pointing at `00_inputs/` files that exist). | `sc asset list --role input --json` | fact | major |
| SL-14 | The bible needs (characters, places, products, props) are listed so the bible stage can start. | Read the notes under the table. | fact | minor |
| SL-15 | Each scene has a line in the Scene light plans block (the anchored sources, as `Scene <n> (<place>): <anchor>`), and the `composition` column is filled for each generated shot (three techniques at most). | Read the block under the table against the scenes; read the composition column. | fact | major |
