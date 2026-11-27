---
name: handoff
description: "Hand-off of a shotcraft production, only when the user asks: the DaVinci Resolve package (approved finals by scene, a timeline that opens in shot order, a shot sheet), and optionally the Higgsfield upload. Triggers: \"send it to DaVinci\", \"make the DaVinci package\", \"hand it off\", \"put it in Higgsfield\"."
metadata:
  version: "0.2.0"
---

# Hand-off (DaVinci Resolve, on request)

The user finishes every piece in DaVinci Resolve: the edit, sound, music, grade and the final export. shotcraft
ends when every shot's final is approved. The hand-off turns those finals into a package that drops straight into
Resolve. It runs **only when the user asks for it**: never offer it at intake, never run it unasked.

In this skill, `sc.py` means `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/sc.py"`. Add `--json` when you need to read
the output.

## 0. Bring the stage back and open it

A new project starts with the hand-off skipped ("on request"). When the user asks:

```
sc.py stage include handoff --user-said "<their words asking for it>"
sc.py stage start handoff
```

Finals must be done first (`sc.py stage status`).

## 1. Check what goes in

```
sc.py handoff resolve --dry-run
```

It lists every shot in shot-list order with its scene and the file it will use: the approved upscale, else the
approved final; a shot covered by the user's own file uses that file. Any shot without an approved final is
listed as not ready: go back to finals for it, or ask the user whether to cut it from the shot list.

## 2. Build the package

```
sc.py handoff resolve
```

It writes `10_handoff/resolve/`:

| File | What it is |
|---|---|
| `SC01/SC01_S010_v1.mp4` ... | The approved take of every shot, copied and filed by scene. `v1` is the take's number among that shot's finals. |
| `timeline.fcpxml` | One timeline with every shot in order at its planned cut length, trimmed past the handles, at the job's frame rate and size. Each clip carries a note with its scene, shot and purpose. |
| `shots.csv` | Scene, place, time, shot, length, purpose, elements, file, take, model and prompt per shot. |

The package is recorded in project.json with a checksum per file; changing a file afterwards means building it
again. Frame rate and size come from the job card's delivery (else the clips themselves, else 30 fps 1080p).

Tell the user how to open it in Resolve:
1. File > Import > Timeline, pick `10_handoff/resolve/timeline.fcpxml`. Resolve imports the clips into the media
   pool and builds the timeline in shot order.
2. If Resolve asks about the frame rate, keep the timeline's (the job's) rate.
3. The clips have handles: trim or slip in Resolve as needed. `shots.csv` is the shot reference while editing.

If the user's **beon-edit** plugin is installed, the work in Resolve can carry on with it (grade, subtitles,
finish pass) when the user asks.

## 3. Optional: the Higgsfield project

Only if the user also wants the approved work in their Higgsfield account. `sc.py handoff upload --dry-run`
lists what would go up (approved finals and upscales, the inputs they use, the locked elements); never a
`reference-only` asset. On their yes: `sc.py handoff upload`. Locked elements are best kept as Higgsfield
Elements (the elements stage saves them with `elements_create` and `sc.py element link`). Higgsfield Canvas has
no API, so shotcraft does not build Canvas boards; `sc.py handoff build` still writes a Canvas build sheet if the
user asks for one.

## 4. Close

The gate is the evidence: the package built and unchanged.

```
sc.py stage done handoff --user-said "<the user's words, if they confirmed it>"
```

Tell the user where it is (`10_handoff/resolve/`), how many clips, and the frame rate and size. Then the
producer moves on to the learn stage.

## Never

- Never run the hand-off without the user asking for it.
- Never edit files in `10_handoff/resolve/` by hand; build it again with `sc.py handoff resolve`.
- Never run raw `higgsfield upload` or `higgsfield generate` commands; never upload a `reference-only` asset.
