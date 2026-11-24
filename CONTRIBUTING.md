# Contributing to shotcraft

Thanks for helping. shotcraft is mostly craft knowledge stored as data, so the most useful contributions are
often small: a model limit that changed, a better routing choice, a vocabulary term, a positive rewrite.

[SPEC.md](SPEC.md) is the design contract. If a change needs the contract to move, change SPEC.md in the same
pull request and say why.

## Ground rules

- **Python 3.9+, standard library only.** No pip installs. External tools (`higgsfield`, `ffmpeg`, `ffprobe`,
  `yt-dlp`, `node`) are optional and must be detected, never assumed.
- **Rules are JSON, prose is markdown.** Keep craft knowledge in `rules/*.json`, not hard-coded in Python.
- **Plain English** in anything a user reads: short sentences, a one-line gloss for any craft term, names
  instead of internal ids.
- **Public and generic.** No personal names, company or client names, private links or account details in
  rules, examples, tests or docs. Use made-up examples ("a neighbourhood bakery").
- **Do not loosen a gate without saying so.** Changes to `rules/stages.json` or `rules/tracks.json`, or to the
  guard, need a clear reason in the pull request.
- **Rights first.** Nothing may send a `reference-only` asset to a model.

## Run the tests

```bash
python3 -m unittest discover -s scripts/tests -v
```

The tests need no network and no Higgsfield CLI (they use the fake provider). Add a test for any behaviour
you change. Check that every JSON file still parses:

```bash
for f in rules/*.json .claude-plugin/*.json hooks/hooks.json; do python3 -m json.tool "$f" >/dev/null || echo "bad: $f"; done
```

To try the plugin locally in Claude Code: `/plugin marketplace add /path/to/your/shotcraft`, then
`/plugin install shotcraft@shotcraft`.

## Proposing a model change (`rules/models.json`)

Higgsfield adds and changes models often. To update a model:

1. Get the facts from the CLI, not from memory or marketing pages:
   `higgsfield model list --json` and `higgsfield model get <id> --json`. For costs, run
   `higgsfield generate cost ...` (costs are never stored as fixed truth; they are read live at run time).
2. Edit the model's entry: `durations`, `resolutions`, `aspects`, `start_frame`, `end_frame`, `refs`, `audio`,
   `negative_prompt`, `max_prompt_words`, `strengths`, `weaknesses`, `gotchas`.
3. Set `checked_at` to today's date and `source` to where the facts came from (for example
   `higgsfield model get, CLI 1.x`).
4. Mark anything you could not confirm as unconfirmed (in `gotchas` or a note), rather than leaving it out or
   stating it as fact.
5. Watch for name traps: the CLI's model ids do not always match the marketing names (for example,
   `nano_banana_2` is Nano Banana Pro). Keep `name` as the name a user would recognise.
6. Bump `rules_version` in `models.json` and add a line to [CHANGELOG.md](CHANGELOG.md).

Running "run model-scout" inside Claude Code does steps 1 to 3 for you and can open the pull request after you
approve the changes.

## Proposing a routing change (`rules/routing.json`)

Routing says which model to try first for a need (icon-logo, photoreal-people, video-general and so on) at
each tier (draft, final, upscale). In the pull request, say:

- which need and tier, and the old and new order;
- why: quality, cost (with live `generate cost` numbers), limits, or failure rate; and
- what you tested: ideally the same card at both choices, with the results compared.

Drafts should stay cheap. Finals should be the cheapest model that meets the use case, not the most expensive.
Update the row's `checked_at`.

## Proposing other rule changes

| File | Good changes |
|---|---|
| `taxonomy.json` | New terms with a short, concrete `means`. Keep terms that a crew member would say on set. Change a field's `priority` only with a reason (it controls trimming). |
| `negatives.json` | Avoid items that fix a real, repeatable failure. Per-model items need an example of the failure. |
| `positive_rewrites.json` | Every negatives term needs a rewrite. A key ending in ` (moving camera)` is used when the shot has a camera move. |
| `presets.json` | Platform specs with a source and date (platform limits change). |

Remember the layering: users can override any rule file in `~/.shotcraft/rules/` or per project in
`<project>/.shotcraft/rules/` without forking. A change belongs in the plugin when it helps everyone.

## Skills, agents and templates

- Skills live in `skills/<name>/SKILL.md` with references under `references/`. The description says exactly
  when the skill should be used.
- Agents live in `agents/<name>.md`. Each says what it is given, what it reads, exactly which paths it
  writes, which `sc.py` commands it may run, what it must never do, and its JSON return shape. Agents never
  talk to the user and never approve anything.
- Templates in `templates/` must keep the labels and columns the stage checks read (see `rules/stages.json`):
  the job card's `Goal`, `Audience`, `Use case`, `Delivery` and `Budget` lines, and the shot list's `id`,
  `duration_s` and `purpose` columns.

## Pull requests

- One topic per pull request.
- Tests pass, JSON parses, and the changelog has a line under `Unreleased`.
- Describe the change in plain English: what it changes for the user, and how you checked it.

By contributing you agree that your contribution is licensed under the MIT licence of this project.
