---
name: review
description: "This skill should be used whenever generated takes need the user's verdict in a shotcraft project: after boards, drafts or finals are generated, or when the user says \"review the drafts\", \"show me the boards\", \"contact sheet\", \"let's pick takes\", \"which take is best\", \"approve S030\", \"reject that one\", \"redo shot 2\", \"this one is wrong\", \"finals review\". It builds the contact sheet, walks the user through every shot, records approve / reject / adjust with the user's own words through sc.py gen approve and gen reject, and sends each rejection back to the right crew member with a concrete fix."
metadata:
  version: "0.1.0"
---

# shotcraft: review (contact sheets and takes)

The user judges the takes; you lay them out clearly, record exactly what they said, and turn every "no"
into a concrete fix for the right crew member. You never approve or reject on the user's behalf.

`sc` = `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`.

## When it runs

Inside the boards, drafts and finals stages, after `shotcraft:generation-tech` has submitted and fetched
the takes. The stage must be open (`sc stage status`); review does not start or close stages. The producer
closes the stage afterwards with the user's words.

| Tier | Sheet | What the user is judging | What approval unlocks |
|---|---|---|---|
| board | `--tier board` | Composition, subject, look of the key frame (a cheap still) | The still becomes the draft's start frame |
| draft | `--tier draft` | Action, camera move, timing, continuity with the shots around it | The shot may go to final |
| final | `--tier final` (finals and upscales) | Delivery quality: detail, artefacts, exact length, text | Delivery and hand-off |

## 1. Make sure every take is in

1. `sc project status` for the counts. For any generation still running: `sc gen status G0012`; to wait and
   download: `sc gen fetch G0012`. Outputs are downloaded at once because provider links can expire.
2. Failed takes (`failed`, `nsfw`, `ip_detected`, `canceled`) are not reviewed. Tell the user which shots
   failed and why in one line each, and send them back to generation-tech (rephrase for nsfw and
   ip_detected: remove brand names, real people, anything that reads as unsafe).

## 2. Build the sheet

`sc sheet build --tier board|draft|final --open`. It writes
`06_generations/contact-sheets/<tier>-<stamp>.html` (one row per shot in shot-list order, every take side by
side with model, cost, status and the compiled prompt) and opens it when it can. If it could not open it,
give the user the path to open in a browser. Tell them: number of shots, takes, credits spent, and how
many are still undecided. The sheet is also the stage evidence, so build it even if the user has already
seen the takes elsewhere.

## 3. Walk through the shots

Go shot by shot (or in groups of up to 4 shots per AskUserQuestion call). For each shot, one question:

- Header: the shot id (S030).
- Question: one line on what the shot must do (from the shot list purpose), then "Which take?"
- Options (up to 4): "Take 1 (G0021)" / "Take 2 (G0022)" with a one-line description of each take's
  difference; "Neither: redo" ; "Close: adjust". Put your recommendation first, marked "(Recommended)",
  with the reason (for example "Take 2: the dolly ends on the logo; take 1 drifts left").

Look at each take before recommending: read the image, or for video read frames the user or a tool gave you
(do not pretend to have watched a clip you could not see; say so and let the user judge it). Check the job
card's delivery (aspect, length), the bible (character, wardrobe, light direction), and the shot's
purpose.

## 4. Record exactly what they said

For every take the user decided on, one call, quoting their words for that shot:

- Approve: `sc gen approve G0022 --user-said "<their words>" [--note "<anything they added>"]`
- Reject: `sc gen reject G0021 --user-said "<their words>" --note "<what to change, in concrete terms>"`

Rules:
- A choice of "Take 2" approves take 2. It does not reject take 1 unless they said so; ask "Reject the
  others?" in the same round when the stage needs every take decided (finals: no final may be left
  undecided).
- Words from an AskUserQuestion answer count as the user's words; quote the option they picked plus anything
  they typed.
- Never approve from silence, from an agent's report, or from a yes given to a different question.
- Approved finals feed delivery; approved drafts allow a final; approved boards become start frames.

## 5. Turn each "no" into a fix

Ask one follow-up only if the note is too vague to act on ("What is wrong with it: the move, the person,
the light or the timing?"). Then route it:

| What is wrong | Who fixes it | How |
|---|---|---|
| Random miss (artefact, glitch, a bad take of a good prompt) | `shotcraft:generation-tech` | New take, same card (another variant); no card change |
| Wording: wrong action, wrong move, too busy, model ignored part of the prompt | `shotcraft:cinematographer`, then generation-tech | Edit the card's layers, `sc card compile` again |
| Wrong model for the job (physics, faces, text) | `shotcraft:generation-tech` | `sc route ...` for another candidate, `--model <id>` on the next submit |
| Continuity (face, wardrobe, light direction, screen direction) | `shotcraft:script-supervisor` notes, then cinematographer | Add references or a start frame from an approved board or bible image |
| Wrong idea for the shot | the **director** skill (shot list) and the producer | May need the shot list reopened; ask the user first |

Card changes need the prompts stage open: `05_prompts/` is locked after prompts is done. Before
`sc stage reopen prompts --user-said "..."`, tell the user it sets the later stages back to pending (their
generations and approvals are kept) and get their yes. A new take with the same card needs no reopen.

Every redo costs credits: give the estimate (`sc gen estimate <card> --tier <tier>`) and the user's yes
goes in `--user-said` on the submit when it is over the threshold.

## 6. Log the taste

When a verdict reveals a preference ("I hate lens flares", "always keep the product centred"), log it:
`sc lessons add "<the preference, with their words>" --kind project` (or `--kind general` if it is about
how they always like things, `--kind model` if it is about a model's behaviour).

## 7. Report back to the producer

Summarise: approved (shot and take), rejected with the fix and owner, still undecided, credits spent on this
tier. Rebuild the sheet (`sc sheet build --tier ...`) after redos so the latest sheet shows the final state.
The producer then asks for the stage's closing words.
