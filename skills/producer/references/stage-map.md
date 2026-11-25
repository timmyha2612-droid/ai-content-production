# Stage map

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Every stage opens with `sc stage status` and
`sc stage start <stage>` and closes with `sc stage done <stage> [--user-said "<user's words>"]`. `done`
checks the evidence listed here itself (from `rules/stages.json`); it never takes it on trust.

Tracks:
- **full**: intake, research, concept, script, shotlist, bible, prompts, boards, drafts, finals,
  sound, assembly, delivery, handoff, learn
- **single**: intake, prompts, drafts, finals, delivery, handoff, learn
- **refine**: refine (no generation; normally no project at all, see the refine skill)

Optional (droppable at intake with the user's words, `sc stage skip <stage> --user-said "..."`): research,
concept, sound, assembly, boards, handoff. Motion graphics are not a shotcraft stage: they are done in the user's own motion graphics tool, from the shot list's graphics column.

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

### bible
- Who: `shotcraft:production-designer` (writes `04_bible/look.md`, `04_bible/environments/`,
  `04_bible/props/`, `04_bible/moodboard/`) in parallel with `shotcraft:character-designer` (writes
  `04_bible/characters/`). Pass each the shot list and the paths it owns.
- Hybrid: if the user brought a Blender scene or wants one, the production-designer plans "Blender
  blockout, render, use as start frame or reference". Renders go into `00_inputs/` as owned
  (`sc asset add PATH --rights owned --role environment --note "Blender render ..."`).
- Evidence: `04_bible/look.md` and at least one file in `characters/` or `environments/`.
- Gate: continuity QA PASS by `shotcraft:script-supervisor`, then the user's words.

### prompts
- Who: `shotcraft:cinematographer` fills the six layers per shot (camera, light, look, beats) from the
  shot list and bible; then `shotcraft:generation-tech` makes the cards valid, picks models and compiles.
  Split shots between agents when there are many (disjoint card files).
- Commands: `sc card new --shot S010 [--from-text "..."]`, `sc card validate <card>`,
  `sc route --use-case <preset> --tier draft|final [--kind video|image] [--duration 6] [--needs audio,refs,end_frame]`,
  `sc card compile <card> --model <id>`.
- Then the producer shows the user every compiled prompt (or a compact table: shot, model, length, prompt
  first line) and, on their yes, sets `"status": "approved"` and `"approved_said": "<their words>"` in each
  card's front matter. This must happen before `stage done prompts`: after that, `05_prompts/` is locked.
- Evidence: a valid card for every shot on the shot list (single track: at least one).
- Gate: QA PASS.

### boards (optional; image first)
- Who: `shotcraft:generation-tech`. Scope: video shots flagged image-first (people, product, text,
  complex moves, 8 s or longer, end frames) or whose card's tier_plan includes board.
- Commands: `sc gen estimate <card> --tier board`, `sc gen submit <card> --tier board [--user-said "..."]
  --wait`, `sc gen status|fetch G0001`, `sc sheet build --tier board`.
- Then the **review** skill. Approved boards become start frames for drafts (the card's `inputs` needs
  `{"asset": "<board asset id>", "as": "start_frame"}`; if 05_prompts is locked, ask before
  `sc stage reopen prompts`).
- Evidence: a completed board per image-first shot, and a board contact sheet. Gate: the user's words.

### drafts
- Who: `shotcraft:generation-tech` (all shots, cheap models, `settings.variants` takes each).
- Commands as boards with `--tier draft`; `sc sheet build --tier draft`.
- Then continuity QA with `shotcraft:script-supervisor` on the drafts (characters, wardrobe, light
  direction, screen direction across cuts), then the **review** skill.
- Evidence: a completed draft per shot, a draft contact sheet. Gate: continuity QA PASS + the user's words.

### finals
- Who: `shotcraft:generation-tech`, only for shots with an approved draft (or the user's words).
- Commands: `sc gen estimate <card> --tier final`, `sc gen submit <card> --tier final --user-said "..."
  --wait`; `--tier upscale` only when the delivery needs more pixels. `sc sheet build --tier final`.
- Then the **review** skill: every final approved or rejected with the user's words.
- Evidence: an approved final (or upscale) for every shot, none undecided. Gate: the user's words.

### sound (optional)
- Who: `shotcraft:sound`. Pass the script's sound column, the audio plan and the licence rules.
- Evidence: files in `07_sound/` and a licence note (a file with "licence" or "license" in its name).
- Gate: the user's words.

### assembly (optional)
- Who: `shotcraft:assistant-editor`. Commands: `sc assembly animatic [--audio <file>] [--burn-ids]`.
- Evidence: `08_assembly/animatic.mp4`, an EDL or notes. Gate: the user's words.

### delivery
- Who: `shotcraft:delivery`. Commands: `sc delivery check [--spec <preset>] [--duration S] [--tolerance S]
  [--lufs L]`.
- Hand the agent: `Master:`, `Spec:`, `Versions:`, `Reframe:` (if the user said), and `Grain:` copied from the
  job card's `Grain:` line (`off`, `subtle` or `film`, vignette yes or no). With grain off and no vignette the
  agent skips `sc finish texture`. It runs `sc finish roomtone` only as a single-bed safety floor when a
  deliverable still fails the digital-silence check; per-scene beds come from the sound stage.
- Evidence: delivered files in `09_delivery/` and `09_delivery/delivery-report.json` with every check PASS.
  The agent also writes `09_delivery/delivery-notes.md`, which always carries the AI-label line for realistic
  AI content.
- Gate: the spec check. A FAIL goes back to the stage that made the file.

### handoff (optional; default on the full track)
- Who: the **handoff** skill. Commands: `sc handoff build`, `sc handoff upload [--dry-run]`.
- Evidence: `10_handoff/canvas-build-sheet.md` and `10_handoff/upload-list.json`.
- Result for the user: the approved assets uploaded to Higgsfield and a Canvas build sheet that sets out
  every node, input and setting, plus browser-assisted Canvas set-up where available. Higgsfield has no
  Canvas API yet; say so plainly if asked.

### learn
- Who: the **learn** skill (it runs `shotcraft:learner` and puts each proposal to the user).
- Commands: `sc lessons list --status open`, `sc lessons decide N accept|reject --user-said "..."`.
- Evidence: every lesson in the project inbox decided. Gate: the user's words.

## Reopening

`sc stage reopen <stage> --user-said "..."` opens a done stage again and sets every later done or open stage
back to pending (their QA files move to history; skipped stages stay skipped; generations and approvals in
project.json are kept). Tell the user which stages go back before you run it.
