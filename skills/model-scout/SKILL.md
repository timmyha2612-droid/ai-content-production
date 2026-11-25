---
name: model-scout
description: "Review new, removed or changed Higgsfield models and update shotcraft's model and routing rules. Triggers: \"run model-scout\", \"any new models?\", \"is there a better model now\"."
metadata:
  version: "0.1.0"
---

# Model scout

Higgsfield adds, renames and retires models often. shotcraft's model profiles (`rules/models.json`) and routing
(`rules/routing.json`, which model to try first for each need and tier) carry a `checked_at` date, and limits and
costs are always read live at generation time. This skill keeps the rules current: it compares the live list with
the rules, studies what changed, and lets the user decide what to adopt.

It is not a stage. It can run any time, with or without a project open.

In this skill, `sc.py` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Add `--json` when you need to read
the output.

## 1. Run the check

```
sc.py scout check --json
```

It asks the Higgsfield CLI for the live model list, compares it with the rules in effect (plugin < personal <
project), and writes `~/.shotcraft/scout/last.json`:
- `new`: models the rules don't know;
- `removed`: models the rules list that the live list no longer has;
- `changed`: a different name or kind;
- `stale_models` and `stale_routing`: entries whose `checked_at` is older than 30 days;
- `canvas_api_detected` and `canvas_evidence`: signs that Higgsfield Canvas has an API now.

If it exits 1 (`ok` false), the CLI is missing or signed out: run `sc.py doctor` and tell the user the one-line fix
(install `@higgsfield/cli` with npm, or `higgsfield auth login`, which the user runs themselves). If the user only
wants to see the last result: `sc.py scout report`.

If nothing is new, removed, changed or stale, say so in one line and stop.

## 2. Send the model-scout agent

Spawn the **model-scout** agent with:
- the report path `~/.shotcraft/scout/last.json` and the lists to study (new, removed, changed, stale), at most
  about 10 models per agent (split bigger batches across agents running in parallel);
- the rule files in effect: `${CLAUDE_PLUGIN_ROOT}/rules/models.json` and `routing.json`, plus
  `~/.shotcraft/rules/` and the project's `.shotcraft/rules/` if a project is open;
- the reference docs: `${CLAUDE_PLUGIN_ROOT}/docs/research/higgsfield-cli/MODELS.md` and
  `${CLAUDE_PLUGIN_ROOT}/docs/research/higgsfield-skills/model-catalog.md` (dated; the live CLI wins);
- what it may run: read-only Higgsfield commands such as `higgsfield model list --json`,
  `higgsfield model get <id> --json` and `higgsfield generate cost ...` (cost checks spend nothing), and
  `sc.py route ...`. It never generates;
- what to return (JSON):
  `{"models": [{"id", "action": "add|update|retire", "profile": {<models.json profile with checked_at and source>}, "unconfirmed": ["fields guessed, not read live"], "summary": "<one line>"}], "routing": [{"need", "tier", "action": "insert|reorder|remove", "rows": [<the full new tier list>], "why", "evidence"}], "notes": [str]}`.

Profiles follow the `models.json` shape: `name`, `kind`, `vendor`, `durations` (list or `{min, max}`),
`resolutions`, `aspects`, `start_frame`, `end_frame`, `refs`, `audio`, `negative_prompt`, `seed`,
`max_prompt_words`, `strengths`, `weaknesses`, `gotchas`, `checked_at`, `source`. Anything not read from the live
CLI must be listed in `unconfirmed`.

## 3. Present the proposals

Show a short table first: each model with its action and one-line summary, then each routing change with the
need and tier, the new order and why. Mark unconfirmed fields clearly.

Ask with **AskUserQuestion**, up to 4 proposals per call (one question each). Options:
- "Adopt for me" (write to personal rules),
- "Adopt for this project only" (only when a project is open),
- "Not now",
- "Adopt, and suggest it to shotcraft" (personal rules now, plus a pull request, section 5).

Routing changes matter most: say which shots or use cases would pick a different model, and what that means for
cost (check with `higgsfield generate cost` through the agent, never a guess). A newer model is not automatically
better: propose it first in a tier only with evidence (its limits fit the need better, it is cheaper for the same
job, or the user has seen it do better).

Record what the user decided as a lesson, with their words, so it shows at the learn stage and in the record:

```
sc.py lessons add "<model or routing change, one line>" --kind model
sc.py lessons decide <n> accept|reject --user-said "<their exact words>"
```

(With no project open these go to the personal inbox automatically; with a project open, add `--personal` to
both commands for changes that are not about this project.)

## 4. Apply the approved changes

Write only to personal rules (`~/.shotcraft/rules/`) or project rules (`<project>/.shotcraft/rules/`); never to
`${CLAUDE_PLUGIN_ROOT}/rules/`.

- New or updated model: merge into `models.json` under
  `{"providers": {"higgsfield": {"models": {"<id>": {<profile>}}}}}`. Objects merge key by key, so an update can
  hold only the changed fields plus `checked_at`.
- Retired model: write
  `{"providers": {"higgsfield": {"models": {"<id>": {"in_model_list": false, "retired": true, "checked_at": "<today>"}}}}}`
  (`in_model_list: false` stops the check reporting it as removed again; `retired` is a note for people) and
  remove it from routing (below), which is what stops shotcraft choosing it.
- Routing: in `routing.json` lists **replace** the list below them, so write the full new tier list:
  `{"use_cases": {"<need>": {"draft": [<rows in the new order>], "checked_at": "<today>"}}}`. A stale row the user
  re-confirmed needs only the new `checked_at`.

Steps:
1. Read the existing personal (or project) file, or start from `{}`.
2. Merge the change in, keeping everything already there.
3. Write it with the Write tool.
4. Check it loads and routes as intended:
   ```
   python3 -c "import sys; sys.path.insert(0, '${CLAUDE_PLUGIN_ROOT}/scripts'); from shotcraft import rules; rules.load('models'); rules.load('routing'); print('ok')"
   sc.py route --use-case <need> --tier draft
   sc.py scout check
   ```
   The second check should no longer list what was adopted.

If a project is open and a card already names a model that was retired or re-routed, tell the user which cards
(`05_prompts/S*.md`) are affected. Changing a card belongs to the prompts stage, through the producer.

## 5. Contributing to shotcraft (only when the user chooses it)

The plugin's defaults change only through a pull request to the shotcraft repository:

1. Ask first: "Prepare a pull request with these model and routing updates? It goes public on GitHub."
2. Work in a separate clone or fork of the repository, never in the installed plugin folder.
3. Update `rules/models.json` and `rules/routing.json` there with `checked_at` and `source`, keep the unconfirmed
   marks, and run `python3 -m unittest discover -s scripts/tests`.
4. Describe the evidence (CLI output, costs, limits). Never include the user's projects, prompts, outputs or
   account details.
5. Show the diff and the PR text; open it with `gh` only after the user's yes.

## 6. Canvas API

If `canvas_api_detected` is true, tell the user what was seen (`canvas_evidence`). The hand-off still uses the
build sheet and the browser route until shotcraft supports the API; suggest a pull request or an issue on the
shotcraft repository so the handoff module can gain a direct Canvas build, and log it:
`sc.py lessons add "Higgsfield Canvas API seen: <evidence>" --kind model`.

## Never

- Never generate anything to test a model. Cost checks (`higgsfield generate cost`) are fine; a test generation
  needs the user's yes and goes through `sc.py gen` inside a project.
- Never edit the plugin's own rule files, and never adopt a change the user did not approve.
- Never present a guessed limit or cost as confirmed.
