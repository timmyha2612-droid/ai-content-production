# How to read and run the QA checklists

These checklists are for the reviewers: `shotcraft:qa-supervisor` (every building stage) and
`shotcraft:script-supervisor` (continuity on the bible, boards, drafts and finals). The verifier
(`shotcraft:qa-verifier`) reads them too, to judge whether a finding breaks a written rule.

One file per stage: `research.md`, `script.md`, `shotlist.md`, `bible.md`, `prompts.md`, `drafts.md` (also used
for boards), `finals.md`, `delivery.md`.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`.

## What wins when files disagree

plugin defaults (`rules/`, these checklists) < personal rules (`~/.shotcraft/rules/`) < project rules
(`<project>/.shotcraft/rules/`) < the job card (`00_brief/job-card.md`) < the user's own words recorded in
`00_brief/grilling.md` and in `project.json` decisions. A checklist number (for example "at most 7 words per text
card") is a default: if the job card or the user's words say otherwise, theirs wins and the item passes.

## Item format

Each item has:

- an **id** (`SC-04`), which stays the same across versions of the plugin;
- the **check**, in one line;
- **how** to check it: the command, measurement or file to read;
- the **default kind** of a finding: `fact` (checkable by anyone with the same files: a number, a missing file,
  a failed command), `judgement` (a trained eye: a weak hook, a move that will not render well) or `creative`
  (taste: the user decides);
- the **default severity** if it fails: `blocker` (the stage cannot close or the next stage would waste credits
  or time), `major` (clearly wrong, must be fixed before the user sees it), `minor` (worth fixing, does not hold
  the stage).

Items marked *(video)*, *(image)*, *(9:16)*, *(VO)*, *(people)*, *(text)* or *(product)* apply only when the job
has that thing. Mark the others `n/a` in `checked` with the reason.

## Rules for every reviewer

1. **Check what is there, not what you are told.** Read the files and measure. A builder's summary is not
   evidence.
2. **Run every item.** Every id appears once in your reply: in `checked` (with the result in a few words), in
   `not_checked` (with why), or as a finding. A reply that skips ids is sent back.
3. **Evidence a person can check.** A file and line, a shot id, a time in seconds, a number from a command,
   a frame you extracted (its path). "Feels off" is not evidence.
4. **When unsure between fact and judgement, use judgement**, so the verifier looks at it. When unsure between
   judgement and creative, use creative: taste goes to the user.
5. **One problem, one finding.** The same problem in five shots is one finding listing the five shots.
6. **Ids are stable across rounds.** A finding id is the checklist id plus a running number: `SC-04-1`,
   `SC-04-2`. In rounds 2 and 3, re-check every finding from the earlier rounds (re-measure, do not trust the
   fix report) and keep its id: say `fixed` or `still open`. New problems get new numbers.
7. **Do not re-raise what the user decided.** A creative call the user already answered (in `grilling.md`,
   in decisions, or in the producer's note for this round) is closed.
8. **Do not pad.** A clean stage has no findings. A minor finding is never a reason to FAIL.
9. **Verdict.** `FAIL` when at least one `blocker` or `major` finding of kind `fact` or `judgement` is open.
   Otherwise `PASS`. A creative finding never makes a FAIL on its own. Your verdict is provisional: the producer
   sets the final one after the verifier has looked at the judgement calls.

## Fix lines

Every finding has a `fix`: the concrete change, small enough to do in one pass, and the `owner` who should do it
(the agent or skill named in the stage map, for example `screenwriter`, `director`, `cinematographer`,
`generation-tech`, `production-designer`, `character-designer`, `delivery`). "Make it better"
is not a fix. "Cut S030 from 3.0 s to 2.0 s so the total is 15.0 s" is.

## Scratch files

Frames, contact strips and measurements go in a scratch folder outside the project
(`mktemp -d -t shotcraft-qa-XXXX`). Never write inside the project, and never into `.shotcraft/qa/`: the
producer records the round with `sc qa record`.
