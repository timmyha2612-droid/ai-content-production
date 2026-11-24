# The QA loop

Every building stage is checked by someone who did not build it, before the user sees it. The loop is:
**reviewer, then verifier, then fix, then record.** At most 3 rounds, then the user decides.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`.

## Which stages, which reviewer

| Stage | Gate | Reviewer |
|---|---|---|
| research | QA PASS | `shotcraft:qa-supervisor` |
| script | QA PASS + user | `shotcraft:qa-supervisor` |
| shotlist | QA PASS | `shotcraft:qa-supervisor` |
| bible | continuity QA PASS + user | `shotcraft:script-supervisor` |
| prompts | QA PASS | `shotcraft:qa-supervisor` (and every card must pass `sc card validate`) |
| drafts | continuity QA PASS + user | `shotcraft:script-supervisor` |
| mograph | QA PASS + user | `shotcraft:qa-supervisor` |

Other stages have no QA gate, but you may still run a reviewer when the user asks ("QA this").

## One round

1. **Check the round.** `sc qa status --stage <stage>` gives the next round number, whether it already
   passed, and whether it must escalate.
2. **Reviewer.** Spawn the reviewer with: project path, stage, round N, job card path, the files to check,
   the stage's evidence and gate (from stage-map.md), and on rounds 2-3 the previous round's findings and
   what was fixed. It returns findings, each with:
   - `id` (R2-03), `severity` (blocker | major | minor), `type` (fact | judgement | creative),
   - `where` (file and line, shot id or timecode), `what` (the problem), `fix` (the concrete change),
   - `owner` (the agent or skill that should fix it).
   Facts are checkable (a duration that does not add up, a missing shot, an invalid card, a broken spec).
   Judgement calls are craft opinions (weak hook, unclear action, a move that will not render well).
   Creative calls are taste and belong to the user.
3. **Verifier.** Spawn `shotcraft:qa-verifier` with the same files and the judgement findings only. It
   confirms or rejects each with a one-line reason. Facts do not need verifying; creative calls are not
   verified, they go to the user.
4. **Decide the verdict.**
   - PASS: no confirmed blocker or major finding left (minors may be listed for the record).
   - FAIL: any confirmed blocker or major.
5. **Record it.** Write the findings (with the verifier's verdict on each) to a JSON file outside the
   project's `.shotcraft/qa/` folder (a temp file is fine), then:
   `sc qa record --stage <stage> --round <N> --verdict PASS|FAIL --findings <file.json> [--note "..."]`.
   A FAIL needs its findings file. Never write into `.shotcraft/qa/` yourself; the guard blocks it.
6. **Fix.** Send the confirmed findings to each owner (same agent type, a fix pass, with the fix list
   verbatim and the paths it may write). Put the creative calls to the user in one AskUserQuestion call
   (up to 4), with your recommendation first. Then start the next round.

On PASS, carry on with the stage's gate: if it also needs the user's words, show the result and ask.

## Findings file shape

```json
[
  {"id": "R1-01", "severity": "major", "type": "fact", "where": "03_script/shotlist.md S030",
   "what": "Shot durations add up to 19 s; the delivery is 15 s.", "fix": "Cut S030 to 2 s and S050 to 3 s.",
   "owner": "director", "verified": null},
  {"id": "R1-02", "severity": "minor", "type": "judgement", "where": "05_prompts/S020.md",
   "what": "Two camera moves in one shot (orbit and push-in).", "fix": "Keep the push-in only.",
   "owner": "cinematographer", "verified": "confirmed: models render one move far more reliably"}
]
```

## After 3 FAIL rounds: escalate

`sc qa status` reports escalate and `sc qa record` refuses a round 4. Stop and tell the user, plainly:

- what still fails (the confirmed findings, one line each),
- what was tried in the three rounds,
- the options, with your recommendation first: accept it as it is; try a different approach (say which);
  change the scope (drop or simplify the shot or stage).

If they accept: `sc stage done <stage> --user-said "<their words>"`. The stage closes with the QA override
noted in the stage record and the decisions. Log the reason as a lesson if it says something about their
taste (`sc lessons add "..." --kind project`).

## Rules

- The builder never reviews its own work; use a fresh agent for each round.
- The reviewer and verifier never fix and never talk to the user.
- Do not shop for a PASS: one reviewer per round, and its confirmed findings stand.
- A finding about taste is never a FAIL on its own; it is a question for the user.
