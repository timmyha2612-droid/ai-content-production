# QA checklist: drafts (and boards)

Stage output: completed draft generations for every shot (`06_generations/drafts/`), recorded in `project.json`,
and a draft contact sheet in `06_generations/contact-sheets/`. Gate: continuity QA PASS (the script-supervisor
runs this checklist), then the user's words in the review skill.

**Boards** use the same checklist on stills (`06_generations/boards/`, tier `board`): skip the items marked
*(motion)*, and judge each board as the start frame its draft will use.

Read: the shot list, the element sheets, each shot's card, `project.json` generations for the tier (status, model,
params, outputs, approvals), the contact sheet, `sc asset list --role draft --json` (or `--role board`).

Look at the pictures yourself. For video, extract frames (first, middle, last, and a strip) as the
script-supervisor agent describes; the contact sheet is not enough to judge continuity.

## Continuity across shots (the script-supervisor's core)

| id | check | how | kind | severity |
|---|---|---|---|---|
| DR-C01 *(people)* | Character identity holds: same face, age, build, hair, skin tone and marks in every shot of that character, and within each clip from first to last frame. | Frames side by side against the character's element sheet and anchor image. Name the shots and the feature that changed. | judgement | blocker |
| DR-C02 *(people)* | Wardrobe matches the element sheets for that scene: garments, colours, accessories, nothing appearing or vanishing between cuts. | Frames against the wardrobe plan. | fact | major |
| DR-C03 | Props: same object, colour, size, state (full, half, empty) and hand as the element sheets and the neighbouring shots. | Last frame of shot A beside first frame of shot B. | fact | major |
| DR-C04 | Light direction (key side): the key comes from the same side (frame-left, frame-right, behind, above) and height within a scene. It flips only where the camera crosses the line (then it must flip) or the script moves the source. | Record the key side per shot from the card and the frames; check each cut pair against the scene light plan and the shot list. | judgement | major |
| DR-C05 | Screen direction and the 180-degree line: travel keeps its direction across cuts (left to right stays left to right), eyelines match, two-person scenes keep each person on their side. | The cut pair strip (last frame of A beside first of B) for every cut that shares a subject or space. | judgement | major |
| DR-C06 | Palette matches `look.md`: the dominant colours of each shot sit in the palette; no shot drifts warmer, cooler or more saturated than its neighbours without a reason. | Average and dominant colours per shot (the agent's palette recipe); compare with the hex values. | judgement | major |
| DR-C07 | Time of day and weather are the same across a scene. | Frames side by side. | fact | major |
| DR-C08 | Matched frames: where the shot list says a shot ends on the frame the next one opens on, they match. | The cut pair strip. | judgement | major |
| DR-C09 | Environment: the same place looks like the same place (layout, materials, dressing) across its shots. | Frames against the environment file. | judgement | major |
| DR-C10 | Shadow direction: the nose and neck shadows (in each frame with a face) and any cast shadow on a wall or floor fall away from the same source. Mixed directions are a finding. | Frames; mark where each shadow falls. | judgement | major |
| DR-C11 | Source present and consistent: the window or practical (a lamp, screen or sign in the world) that motivates the key shows in the wide, or is named in the scene light plan, with the same colour and side in the close-ups. | The wide beside each close-up of the scene. | judgement | major |
| DR-C12 | Ratio band (how much brighter the key side is than the shadow side): each shot is soft (about 2:1), drama (about 4:1) or hard (8:1 and up), and the band does not jump inside a scene unless the script asks for it. | Frames side by side; note the band per shot against the scene light plan. | judgement | minor |
| DR-C13 | Colour per source: warm sources stay warm and cool stay cool across shots; no source changes colour between cuts, and no teal-and-orange grade replaces the sources' own colours. | Frames side by side against the scene light plan's colours and `look.md`. | judgement | major |
| DR-C14 | Time-of-day drift: golden-hour sun height and blue-hour sky level stay put, or move only in the direction the plan says. | Frames in shot-list order; note the sun height or sky level per shot. | judgement | major |
| DR-C15 | Reflections and patterns: on night exteriors, the streaks in puddles and wet ground sit under their sources; blind stripes and leaf dapple keep the same angle across the face, the wall and the next shot. | Frames; compare stripe angles across each cut pair. | judgement | minor |
| DR-C16 *(motion)* | Light holds still in the clip: the key does not move with the head or the camera, patterns (blinds, dapple) are not glued to faces, and exposure does not pump. Flicker or drift the card asks for on purpose passes. | Frame strip over the part that plays; watch the shadow edges and the brightness of a fixed wall. | judgement | major |

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
| DR-12 | No pasted-in subject: the place acts on the subject as the card's `subject.interaction` says (light from the place falls on them, weather shows on them, they touch the world, their scale fits). A subject lit differently from the set, or floating over it, is a finding. | Frames against the card's subject and world layers. | judgement | major |
| DR-13 | Depth reads: a foreground, the subject's plane and a background are all visible, with focus falling off naturally; *(motion)* near planes move faster than far ones on a camera move. Flat, one-plane frames are a finding. | Frames, and a strip over the camera move. | judgement | minor |
| DR-14 *(live action)* | Not too perfect: no sterile, spotless sets, airbrushed skin, perfect symmetry, hyper-sharp everything, flat even light or stock-photo posing. Clean presets (icons, products, logos) are meant to look pristine and skip this. | Frames against the card's `light_look.finish`; name the shot and what looks too perfect, with the rewrite from `${CLAUDE_PLUGIN_ROOT}/rules/positive_rewrites.json`. | judgement | minor |
