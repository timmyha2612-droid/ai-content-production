---
name: handoff
description: "This skill should be used for the hand-off stage of a shotcraft production: uploading the approved work to Higgsfield, writing the Canvas build sheet, and offering to set up the Higgsfield Canvas board in the browser step by step. Triggers: \"hand it off\", \"put it in Higgsfield\", \"set up the Canvas\", \"build the board\", \"upload the finals\", \"I want everything ready in Higgsfield\", \"handoff stage\", or the producer reaching the handoff stage on the full or single track."
metadata:
  version: "0.1.0"
---

# Hand-off (Higgsfield Canvas)

When the user runs a whole production with shotcraft, the end result lives in Higgsfield: every approved shot, its
inputs and the bible uploaded, and a Canvas board (Higgsfield's node-based workspace) laid out shot by shot with
every prompt, model and setting ready, so the user can open it, re-run, branch or extend any shot.

Higgsfield Canvas has **no API, CLI or MCP access** as of November 2026 (an open feature request on the
Higgsfield CLI). So the hand-off is: upload the files, write the build sheet, and offer to build the board in
the user's browser with them watching. When a Canvas API appears, this skill changes to building it directly.

In this skill, `sc.py` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Add `--json` when you need to read
the output.

## 0. Open the stage

```
sc.py project status --json
sc.py stage status handoff
sc.py stage start handoff
```

The hand-off is optional. If the user dropped it at intake it shows as `skipped`; only run it if they ask (then
`sc.py stage reopen handoff --user-said ".."`). Delivery must be done first.

## 1. Check for a Canvas API first

Run the model check's report (it also looks for signs of a Canvas command or model):

```
sc.py scout report --json
```

- If `canvas_api_detected` is true, tell the user what was seen (`canvas_evidence`), and that shotcraft cannot
  build through it yet: the build sheet and browser route below still work. Suggest a lesson so the plugin is
  updated: `sc.py lessons add "Higgsfield Canvas may have an API now: <evidence>" --kind model`.
- If the report is old (more than a day) or missing, run `sc.py scout check` first. If the Higgsfield CLI is
  missing or signed out, `sc.py doctor` says how to fix it; uploading needs it.

## 2. See what will be uploaded

```
sc.py handoff upload --dry-run
```

It lists the files that would go up: approved finals and upscales, the inputs those shots use (start and end
frames, references the user owns or licensed), and the bible (characters, environments, props, moodboard). It
never uploads an asset tagged `reference-only`; those are listed as left out, with the reason.

Show the user the list in short form (counts, and anything left out and why). If an asset they need is left out
because it is `reference-only` but they own it or have a licence, they can say so and you record it:
`sc.py asset mark <asset id> --rights owned --user-said "<their words>"` (or `licensed`). Never change rights
without their words.

Ask with **AskUserQuestion**: "Upload these <N> files to your Higgsfield account?" (options: "Upload",
"Change the list first", "Skip the upload, just write the sheet").

## 3. Upload and write the sheet

```
sc.py handoff upload
sc.py handoff build
```

- `upload` sends each file once (a file already uploaded and unchanged is not sent again), records the upload ids,
  and rebuilds the sheet. Failed uploads are listed; retry them with the same command.
- `build` writes `11_handoff/canvas-build-sheet.md` (the human sheet, one node group per shot: input nodes,
  prompt node, model node with settings, edges) and `11_handoff/upload-list.json` (the same plan as data, under
  `canvas`). Run it after any change.

Read the sheet yourself. Check that every approved shot is there, each prompt is the compiled one from its card,
and nothing says "not uploaded" unless the user chose to skip it.

## 4. Offer the browser build

Ask with **AskUserQuestion**: "Do you want me to set up the Canvas board in your browser now? You watch, and I
stop before anything that spends credits." Options: "Yes, build it with me", "No, I'll use the sheet myself".

Only offer this when a browser tool is connected in this session (Claude in Chrome on the user's Mac, or another
browser-control tool the user has connected). If none is connected, say that the sheet is ready and how to
connect Claude in Chrome if they want help next time.

The browser build, step by step:

1. Ask the user to open Higgsfield in Chrome, signed in, and to open (or create) the Canvas board for this
   project. Do not sign in for them and never type passwords.
2. Work one shot at a time, in shot-list order, following `11_handoff/upload-list.json` → `canvas`:
   add the input nodes (pick each file from the user's uploads by its upload id or file name), add the prompt
   node and paste the prompt exactly, add the model node, choose the model and settings from the sheet, connect
   the edges.
3. After each shot, take a screenshot, compare it with the sheet, and tell the user in one line what was built
   ("S020 done: start frame, prompt, Seedance 2.5 at 9:16 1080p 6 s").
4. **Never press Run, Generate or anything that spends credits.** The approved results already exist. If the user
   wants a new take, they press it, or they say so and you confirm the cost Canvas shows first.
5. If the page differs from the sheet (a model renamed, a setting missing, a layout change), stop, tell the user
   what differs, and log it: `sc.py lessons add "<what differed>" --kind model`.
6. If anything asks for a login, a payment, a permission or a captcha, stop and hand it to the user.

## 5. Close

The gate is evidence only: the sheet and the upload list.

```
sc.py stage done handoff --user-said "<the user's words, if they confirmed the hand-off>"
```

Tell the user where everything is: the Canvas board (if built), `11_handoff/canvas-build-sheet.md`, and the
delivery files in `10_delivery/`. Then the producer moves on to the learn stage.

## Never

- Never run raw `higgsfield upload` or `higgsfield generate` commands; use `sc.py handoff upload`.
- Never upload a `reference-only` asset, and never mark rights without the user's own words.
- Never press a button in Canvas that spends credits without the user's explicit yes for that run.
- Never enter credentials or handle payments in the browser.
