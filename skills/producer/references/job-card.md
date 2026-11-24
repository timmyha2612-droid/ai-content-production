# The job card (00_brief/job-card.md)

The job card is the one-page contract for a project. Every stage skill and agent reads it before working.
It is written at intake from the grilling answers, shown to the user, and closed with their words
(`sc stage done intake --user-said "..."`). Start from `${CLAUDE_PLUGIN_ROOT}/templates/job-card.md` when it
exists; otherwise use the layout below.

## Required lines (checked by `sc stage done intake`)

The intake evidence check (`rules/stages.json`, check `card_lines`) looks for these five labels, either as
`Label: value` lines or as `| Label | value |` table rows. A value of `<...>`, `TBD`, `...` or nothing counts
as empty and the stage will not close.

| Label | What goes there | Example |
|---|---|---|
| `Goal` | What the piece must achieve, in one sentence, with the one action or feeling it should cause | Get first-time visitors to book a tasting at the bakery this month |
| `Audience` | Who watches, where, and what they already know | Locals 25-45 scrolling Instagram on their phones, sound off, never heard of us |
| `Use case` | The preset id plus the platform in words | social-vertical (Instagram Reel and TikTok) |
| `Delivery` | Aspect, resolution, fps, exact length, formats, count | 9:16, 1080x1920, 30 fps, 15 s, MP4 H.264, 1 master + 1 cut-down 6 s |
| `Budget` | Credits for the job and the single-job threshold | 300 credits, ask me above 50 per job |

Keep each label exactly as written (capital first letter, no extra words before the colon).

## Recommended lines (not checked, but every crew member reads them)

| Label | What goes there |
|---|---|
| `Project` | Name and slug |
| `Track` | full or single, and why |
| `Deadline` | Date, and what happens if it slips |
| `Message` | The one thing the viewer must remember; any must-say lines |
| `Brand` | Name, colours (hex), fonts, logo file (asset id), do and don't |
| `Tone` | Three words, plus one reference that nails it |
| `Look` | The six-layer short answers that were settled at intake (subject, world, camera, light and look, time and output) |
| `Inputs` | The user's own files with asset ids and rights (e.g. `A001 kitchen-blockout.png, owned, Blender render`) |
| `References` | Links and asset ids, all `reference-only` unless the user said otherwise |
| `Stages` | Dropped stages with the user's words; who owns what (e.g. "sound: the user") |
| `Text on screen` | Exact copy, spelling checked with the user |
| `Audio` | Native model audio, music bed, voice-over, or silent (and who supplies it) |
| `Hand-off` | Higgsfield Canvas build (default for full), files only, or both |
| `Approver` | The user (always). Add others only if the user names them, and note that only the user's words close gates in shotcraft |
| `Open questions` | Anything still open, and which stage will settle it |

## Layout

```markdown
# Job card: <Project name>

Goal: <one sentence>
Audience: <who, where, what they know>
Use case: <preset id> (<platform>)
Delivery: <aspect>, <WxH>, <fps> fps, <length> s, <formats>, <count>
Budget: <N> credits, ask me above <T> per job

Track: full
Deadline: <date>
Message: <the one thing>
Brand: <name; colours; fonts; logo asset>
Tone: <three words>
Look: subject <...>; world <...>; camera <...>; light <...>; time <...>
Inputs: <asset ids, file names, rights, source>
References: <links / asset ids, reference-only>
Stages: dropped <stage> ("<user's words>"); sound by the user
Text on screen: "<exact copy>"
Audio: <...>
Hand-off: Higgsfield Canvas build sheet + upload
Approver: the user
Open questions: <...>

Confirmed: "<the user's words>" (<date>)
```

## Rules

- Write the user's answers, not your guesses. A line you inferred from the brief is marked `(from brief)`.
- Numbers are exact: seconds, pixels, credits. "Short" is not a length.
- When something changes later, update the card while the intake stage is reopened, or note the change in
  the stage that settled it and log it with `sc lessons add` if it is a preference. Do not edit the card
  silently.
