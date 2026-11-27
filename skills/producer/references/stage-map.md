# Stage map

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Every stage opens with `sc stage status` and
`sc stage start <stage>` and closes with `sc stage done <stage> [--user-said "<user's words>"]`. `done`
checks the evidence listed here itself (from `rules/stages.json`); it never takes it on trust.

Tracks:
- **full**: intake, research, concept, script, shotlist, elements, prompts, drafts, finals, handoff, learn
- **single**: intake, prompts, drafts, finals, handoff, learn
- **refine**: refine (no generation; normally no project at all, see the refine skill)

Optional (droppable at intake with the user's words, `sc stage skip <stage> --user-said "..."`): concept,
drafts. Research is required. The hand-off is **on request**: it starts skipped and runs only when the user asks
(`sc stage include handoff --user-said "..."`). Sound, music, the edit and the export happen in DaVinci, outside
shotcraft. Older projects keep their old stages (bible, boards, sound, assembly, delivery) and still work. Motion graphics are not a shotcraft stage: they are done in the user's own motion graphics tool, from the shot list's graphics column.

## What every agent gets

Spawn agents with the Agent tool, `subagent_type: "shotcraft:<name>"`. The prompt always carries:

```
Project: <abs path>
Stage: <stage>   (round <N> when it is a QA fix pass)
Job card: <abs path>/00_brief/job-card.md
Scope: <shot ids, or "all shots on 03_script/shotlist.md">
Task: <one paragraph: what to make, what the user decided that matters here>
Fix list: <only on a fix pass: the confirmed findings, verbatim>
Write only: <the exact paths this agent may write>
Return: the JSON summary your agent file defines.
```

Agents never talk to the user, never approve, never edit `project.json` by hand and never run raw
`higgsfield generate`. Parallel agents get disjoint paths. After an agent returns, read its summary, check
the files exist, and never pass its words on as the user's.

## Stages

### intake (producer)
- Work: the grilling, `00_brief/grilling.md`, `00_brief/job-card.md`, assets for the user's own files.
- Evidence: job card with Goal, Audience, Use case, Delivery and Budget filled; grilling.md exists.
- Gate: the user's words confirming the card.

### research (optional)
- Who: `shotcraft:researcher`, 2-4 in parallel, one angle each (for example: the references the user gave;
  what works on the platform now; the visual world and its real-life details; competitors or genre).
- Pass: the angle, the links to fetch, the job card, and the write path `01_research/notes-<angle>.md`.
- Commands they run: `sc refs fetch URL [--note "..."] [--shot S010]` (downloads into `01_research/refs/`,
  tagged `reference-only` with the source URL).
- Then: merge the notes into `01_research/direction-note.md` (one page: what to take, what to avoid, open
  questions). Do it yourself or with one more researcher pass.
- Evidence: `01_research/direction-note.md`, at least one asset with role reference.
- Gate: QA PASS (qa-loop.md).

### concept (optional)
- Who: the **creative-director** skill (it talks to the user).
- Evidence: `02_concept/concepts.md` with 2 or more `##` directions, and `02_concept/chosen.md`.
- Gate: the user's pick, in their words.

### script
- Who: `shotcraft:screenwriter`. Pass the chosen direction, length, message, on-screen text and audio plan.
- Writes: `03_script/script.md` (two columns: picture | sound and text; timings).
- Evidence: the script file. Gate: QA PASS, then the user's words.

### shotlist
- Who: the **director** skill.
- Evidence: `03_script/shotlist.md`, a markdown table with columns id (or Shot), duration_s (or Duration),
  purpose; optional kind and image_first. Ids look like S010, S020.
- Gate: QA PASS.

### elements
- Who: `shotcraft:character-designer` (characters) in parallel with `shotcraft:production-designer` (look,
  environments, props, style frame) write each element's sheet in `04_elements/<category>s/` and its anchor,
  then add it: `sc element add --name ... --category character|environment|prop|style --label ... --anchor
  "..." [--views ...]` (one card per view in `04_elements/cards/`, scaffolded from
  `rules/element_recipes.json`). `shotcraft:generation-tech` fills the cards' models and generates on the
  element tier; the **review** skill takes the user through the takes.
- Commands: `sc element views`, `sc card approve 04_elements/cards/E01A.md --user-said "..."`,
  `sc gen estimate|submit E01A --tier element`, `sc sheet build --tier element`, `sc gen approve|reject`,
  `sc element lock E01 --user-said "..."`, `sc element link E01 --hf-element <uuid>` after saving it to
  Higgsfield (MCP `elements_create`) with the user's yes.
- Hybrid: a Blender render or the user's own photo can be an element's view (`00_inputs/`, rights owned).
- Evidence: every element locked, and every `@Label` the shot list names is a locked element.
- Gate: continuity QA PASS by `shotcraft:script-supervisor`, then the user's words.

### prompts
- Who: `shotcraft:cinematographer` fills the six layers per shot (camera, light, look, beats) from the
  shot list and the locked elements, mentioning each by `@Label` and never re-describing it; then `shotcraft:generation-tech` makes the cards valid, picks models and compiles.
  Split shots between agents when there are many (disjoint card files).
- Commands: `sc card new --shot S010 [--from-text "..."]`, `sc card validate <card>`,
  `sc route --use-case <preset> --tier draft|final [--kind video|image] [--duration 6] [--needs audio,refs,end_frame]`,
  `sc card compile <card> --model <id>`.
- Then the producer shows the user every compiled prompt (or a compact table: shot, model, length, prompt
  first line) and, on their yes, sets `"status": "approved"` and `"approved_said": "<their words>"` in each
  card's front matter. This must happen before `stage done prompts`: after that, `05_prompts/` is locked.
- Then `sc element attach` (the plan) and, on the user's yes, `sc element attach --user-said "..."`: each
  shot's locked elements go on its card as inputs.
- Evidence: a valid card for every shot on the shot list (single track: at least one).
- Gate: QA PASS.

### drafts (optional)
- Who: `shotcraft:generation-tech` (cheap models, `settings.variants` takes each). Optional: elements are
  locked before the shots, so drafts are for risky shots only. Skipped, finals need no approved draft.
- Commands: `sc gen estimate <card> --tier draft`, `sc gen submit <card> --tier draft --user-said "..." --wait`, `sc sheet build --tier draft`.
- Then continuity QA with `shotcraft:script-supervisor` on the drafts (characters, wardrobe, light
  direction, screen direction across cuts), then the **review** skill.
- Evidence: a completed draft per shot, a draft contact sheet. Gate: continuity QA PASS + the user's words.

### finals
- Who: `shotcraft:generation-tech`, only for shots with an approved draft (or the user's words).
- Commands: `sc gen estimate <card> --tier final`, `sc gen submit <card> --tier final --user-said "..."
  --wait`; `--tier upscale` only when the delivery needs more pixels. `sc sheet build --tier final`.
- Then the **review** skill: every final approved or rejected with the user's words.
- Evidence: an approved final (or upscale) for every shot, none undecided. Gate: the user's words.

### handoff (only when the user asks)
- When: the user asks for it ("send it to DaVinci", "make the package"). `sc stage include handoff
  --user-said "<their words>"`, then `sc stage start handoff`. Never offer it unasked.
- Who: the **handoff** skill. Commands: `sc handoff resolve [--dry-run]`.
- Writes `10_handoff/resolve/`: the approved final of every shot filed by scene (`SC01/SC01_S010_v1.mp4`),
  `timeline.fcpxml` (every shot in order at its cut length; in Resolve: File > Import > Timeline) and
  `shots.csv`. Optional, on the user's yes: the Higgsfield project upload (`sc handoff upload`).
- Evidence: the package recorded by `sc handoff resolve`, unchanged since. Gate: the evidence.

### learn
- Who: the **learn** skill (it runs `shotcraft:learner` and puts each proposal to the user).
- Commands: `sc lessons list --status open`, `sc lessons decide N accept|reject --user-said "..."`.
- Evidence: every lesson in the project inbox decided. Gate: the user's words.

## Reopening

`sc stage reopen <stage> --user-said "..."` opens a done stage again and sets every later done or open stage
back to pending (their QA files move to history; skipped stages stay skipped; generations and approvals in
project.json are kept). Tell the user which stages go back before you run it.
