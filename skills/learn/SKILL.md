---
name: learn
description: "This skill should be used at the end of every shotcraft job (the learn stage) and whenever the user wants shotcraft to remember something: it reads the lessons inbox, runs the learner agent over the job, puts each proposed rule change to the user sorted as general, project or model, and writes the accepted ones to personal or project rules (never to the plugin's own defaults unless the user chooses to contribute a pull request). Triggers: \"learn from this job\", \"remember this for next time\", \"always do it this way\", \"only for this project\", \"what did we learn\", \"review the lessons\", \"learn stage\", or the producer reaching the learn stage."
metadata:
  version: "0.1.0"
---

# Learn (end of job)

The user teaches shotcraft in two ways: what they **say** during a job (corrections, preferences, reasons), and what
they **choose** (approvals, rejections, the notes on rejected takes, the QA findings they agreed with). Both go
into the lessons inbox as they happen. At the end of the job this skill turns them into rule changes, and only
the user's yes makes a lesson a rule.

In this skill, `sc.py` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Add `--json` when you need to read
the output.

## During every job: log, don't decide

Whenever the user corrects something or explains a preference, log it before acting on it:

```
sc.py lessons add "<one-line rule in plain words>" --kind general|project|model
```

- `general`: applies to every job ("always give me a safe direction first", "never use neon").
- `project`: only this job or this brand ("this brand never shows faces").
- `model`: about a model or route ("Kling 3.0 warps text on packaging", "Seedance 2.5 is worth it for slow
  pushes").
- With no project open (for example on the refine track) the lesson goes to the personal inbox
  (`~/.shotcraft/lessons.md`). Add `--personal` to send it there even with a project open.

A one-off instruction ("make S020 brighter") is not a lesson. A reason, an "always", a "never" or a "for this
brand" is.

## 0. Open the stage

```
sc.py project status --json
sc.py stage status learn
sc.py stage start learn
```

The learn stage is the last stage of the full and single tracks. The refine track has no learn stage: run
sections 2 to 5 on the personal inbox (`--personal`) without stage commands.

## 1. Gather the job

```
sc.py lessons list --json
sc.py lessons list --personal --status open --json
```

Spawn the **learner** agent with:
- the project path and the track;
- the inbox paths: `<project>/.shotcraft/lessons.md` and `~/.shotcraft/lessons.md`;
- what to read: `project.json` (decisions with the user's words, generations with approvals, rejections and
  notes, cost estimates against actual cost), `.shotcraft/qa/*/round-*.json` (QA findings), the cards in
  `05_prompts/`, `00_brief/grilling.md`, and the rule files in effect (plugin `rules/`, `~/.shotcraft/rules/`,
  `<project>/.shotcraft/rules/`);
- what to return (JSON), one proposal per lesson:
  `{"proposals": [{"lesson": n|null, "kind": "general|project|model", "evidence": "<what in the job shows it, with the user's words>", "rule": "<the rule in one line>", "target": "personal|project|pr", "file": "<rule file name, e.g. negatives.json>", "change": {<the JSON to merge>}, "why": "<one line>", "confidence": "high|medium|low"}], "new_lessons": [{"text", "kind", "evidence"}]}`.

The learner never talks to the user and never writes rule files. It proposes only.

If the learner returns `new_lessons` (patterns it found that nobody logged, for example "three takes rejected
for the same reason"), add each to the inbox first so it gets decided like the others:
`sc.py lessons add "<text>" --kind <kind>`.

## 2. Put the proposals to the user

Sort them into three groups and present one group at a time: **general**, then **model**, then **project**.
For each proposal show the rule in one line, the evidence (with the user's own earlier words), and where it would
be written.

Ask with **AskUserQuestion**, up to 4 proposals per call (one question each), options:
- "Yes, for every job" (personal rules),
- "Only this project" (project rules),
- "No",
- for general and model lessons that would help everyone: "Yes, and suggest it to shotcraft" (personal rules now,
  plus a pull request to the plugin later, see section 4).

Their answer decides the lesson. Record it with their own words (the option they picked plus anything they
typed). Never decide a lesson for them, and never paraphrase their words:

```
sc.py lessons decide <n> accept --user-said "<their exact words>"
sc.py lessons decide <n> reject --user-said "<their exact words>"
```

Personal-inbox lessons are decided with `--personal`.

## 3. Write the accepted rules

Where each accepted lesson goes:

| answer | file | notes |
|---|---|---|
| for every job | `~/.shotcraft/rules/<file>.json` | personal layer, merged over the plugin's defaults on every job |
| only this project | `<project>/.shotcraft/rules/<file>.json` | project layer, merged last |
| suggest it to shotcraft | personal file now, plus a PR (section 4) | the plugin's own `rules/` is never edited here |

Which file fits which lesson:

| lesson about | file | example change |
|---|---|---|
| a word or look to avoid | `negatives.json` | `{"universal+": ["lens flare"]}` or `{"by_category": {"product+": ["warped label"]}}` |
| how to phrase an avoid term positively | `positive_rewrites.json` | `{"lens flare": "clean lens, no flare, controlled highlights"}` |
| a model's strengths, weaknesses or gotchas | `models.json` | `{"providers": {"higgsfield": {"models": {"kling3_0": {"weaknesses+": ["warps small text on packaging"]}}}}}` |
| which model to try first for a use case | `routing.json` | the whole tier list for that need, in the new order (lists replace; see below) |
| defaults for a use case (aspect, handles, length) | `presets.json` | `{"presets": {"social-vertical": {"handles_s": 0.25}}}` |
| vocabulary for prompts | `taxonomy.json` | `{"layers": {"light_look": {"fields": {"mood": {"vocab+": [{"term": "quiet luxury", "means": "..."}]}}}}}` |

How merging works (the rules loader, plugin < personal < project):
- objects merge key by key;
- a list **replaces** the list below it, so to reorder routing write the full list for that tier;
- a key ending in `+` **appends** to the list below it without duplicates (use it for avoid terms, weaknesses,
  vocabulary).

Steps for each file:
1. Read the existing personal or project file if there is one (it may not exist yet; start from `{}`).
2. Merge the change in by hand, keeping what is there. Add `"checked_at": "<today>"` to a model or routing entry
   you change.
3. Write the file with the Write tool (the guard allows `~/.shotcraft/rules/` and `<project>/.shotcraft/rules/`).
4. Check it loads and merges:
   ```
   python3 -c "import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts'); from shotcraft import rules; rules.load('<name>'); print('ok')"
   ```
   For a project rule, pass the project: `rules.load('<name>', '<project path>')`. For a routing change, also
   run `sc.py route --use-case <need> --tier draft` and check the order is what the user asked for.

Lessons with no rule file to land in (a working habit, such as "ask me before any shot over 8 s"): keep them as
accepted lessons. The accepted line in the inbox is the record, and the producer reads accepted lessons in
`~/.shotcraft/lessons.md` and `<project>/.shotcraft/lessons.md` at intake. For a general habit from a project
inbox, also log it in the personal inbox so it carries to the next job:
`sc.py lessons add "<text>" --kind general --personal`, then decide it there with the same words.

Lessons about stages and gates (`tracks.json`, `stages.json`) cannot be changed in personal or project rules:
shotcraft reads those only from the plugin so a gate can't be loosened by accident. They can only become a pull
request.

## 4. Contributing to shotcraft (only when the user chooses it)

The plugin's own defaults (`${CLAUDE_PLUGIN_ROOT}/rules/`) are never edited from a job. If the user picked
"suggest it to shotcraft", offer to prepare a pull request to the shotcraft repository on GitHub:

1. Ask first: "Prepare a pull request with these <N> rules? It goes public on GitHub." Only go on with a yes.
2. Work in a separate clone or fork of the shotcraft repository, never in the installed plugin folder.
3. Make the same change in `rules/<file>.json` there (with `checked_at`), and say in the PR why, using the
   evidence. Never include the user's project names, client names, file paths, prompts or personal details:
   describe the pattern, not the job.
4. Run the tests: `python3 -m unittest discover -s scripts/tests`.
5. Show the user the diff and the PR text before it is opened. Open it with `gh` only after their yes.

## 5. Close

Every lesson in the project inbox must be accepted or rejected (an empty inbox passes). Then close with the user's
own words:

```
sc.py lessons list --status open
sc.py stage done learn --user-said "<the user's exact words>"
```

Tell the user in two or three lines what was learned and where it was written.

## Never

- Never edit `${CLAUDE_PLUGIN_ROOT}/rules/` or any other plugin file from a job.
- Never write a rule the user did not accept, and never widen it (a project lesson stays a project rule).
- Never put the user's private details (names, clients, projects, prompts) in a pull request.
- Never decide a lesson, or close the stage, without the user's own words.
