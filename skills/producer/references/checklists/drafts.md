# QA checklist: drafts (and boards)

Stage output: completed draft generations for every shot (`06_generations/drafts/`), recorded in `project.json`,
and a draft contact sheet in `06_generations/contact-sheets/`. Gate: continuity QA PASS (the script-supervisor
runs this checklist), then the user's words in the review skill.

**Boards** use the same checklist on stills (`06_generations/boards/`, tier `board`): skip the items marked
*(motion)*, and judge each board as the start frame its draft will use.

Read: the shot list, the bible, each shot's card, `project.json` generations for the tier (status, model,
params, outputs, approvals), the contact sheet, `sc asset list --role draft --json` (or `--role board`).

Look at the pictures yourself. For video, extract frames (first, middle, last, and a strip) as the
script-supervisor agent describes; the contact sheet is not enough to judge continuity.

## Continuity across shots (the script-supervisor's core)

| id | check | how | kind | severity |
|---|---|---|---|---|
| DR-C01 *(people)* | Character identity holds: same face, age, build, hair, skin tone and marks in every shot of that character, and within each clip from first to last frame. | Frames side by side against the character's bible file and anchor image. Name the shots and the feature that changed. | judgement | blocker |
| DR-C02 *(people)* | Wardrobe matches the bible for that scene: garments, colours, accessories, nothing appearing or vanishing between cuts. | Frames against the wardrobe plan. | fact | major |
| DR-C03 | Props: same object, colour, size, state (full, half, empty) and hand as the bible and the neighbouring shots. | Last frame of shot A beside first frame of shot B. | fact | major |
| DR-C04 | Light direction: the key comes from the same side and height within a scene; shadows fall the same way; the colour temperature matches. | Frames side by side; note where the shadows fall in each. | judgement | major |
| DR-C05 | Screen direction and the 180-degree line: travel keeps its direction across cuts (left to right stays left to right), eyelines match, two-person scenes keep each person on their side. | The cut pair strip (last frame of A beside first of B) for every cut that shares a subject or space. | judgement | major |
| DR-C06 | Palette matches `look.md`: the dominant colours of each shot sit in the palette; no shot drifts warmer, cooler or more saturated than its neighbours without a reason. | Average and dominant colours per shot (the agent's palette recipe); compare with the hex values. | judgement | major |
| DR-C07 | Time of day and weather are the same across a scene. | Frames side by side. | fact | major |
| DR-C08 | Matched frames: where the shot list says a shot ends on the frame the next one opens on, they match. | The cut pair strip. | judgement | major |
| DR-C09 | Environment: the same place looks like the same place (layout, materials, dressing) across its shots. | Frames against the environment file. | judgement | major |

## Each take

| id | check | how | kind | severity |
|---|---|---|---|---|
| DR-01 | Every shot has at least one completed draft (or board, for the boards stage) and the tier's contact sheet exists. | `sc stage status drafts --json`; `ls 06_generations/contact-sheets/`. | fact | blocker |
| DR-02 | The take does what the card asks: the subject, the action, the shot size and angle, the camera move and its speed. | Frames and the card's layers. | judgement | major |
| DR-03 *(motion)* | The length and handles fit: the clip is at least the shot's duration plus handles. | `ffprobe -v error -show_entries format=duration -of csv=p=0 <file>` against the card. | fact | major |
| DR-04 | Aspect and resolution are what the card asked for (or the compile's adjustment says why not). | `ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 <file>` | fact | major |
| DR-05 *(motion)* | No visible artefacts that would survive into the final: morphing hands or faces, limbs merging, objects melting or popping in and out, flicker, warped geometry, jitter. | Frame strip at 4 frames a second over the part that plays (skip the handles). Give the time. | judgement | major |
| DR-06 *(text)* | No legible text, logos or watermarks in the picture that the plan did not ask for (text belongs to motion graphics). | Frames. | fact | major |
| DR-07 *(product)* | The product looks like the user's product: shape, label, colours, proportions. | Frames against the user's product photos (asset ids in the prop file). | judgement | blocker |
| DR-08 | Safe zone *(9:16 and other social)*: faces, product and the action sit inside the preset's safe zone. | A frame with the safe zone measured from the preset's `safe_zone` pixels (scale to the take's size). | judgement | minor |
| DR-09 | The take reads at the planned length: the action lands inside the part that plays, not in the handles. | Frames at the in and out points. | judgement | minor |
| DR-10 | Failed, nsfw or ip_detected takes are noted with what to change in the prompt (no blind retries). | `project.json` generations with those statuses and their notes. | fact | minor |
| DR-11 | Inputs were allowed: no generation used a `reference-only` asset. | Each generation's `inputs` against `sc asset list --json`. | fact | blocker |
