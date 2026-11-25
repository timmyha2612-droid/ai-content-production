# QA checklist: finals

Stage output: a completed final (or upscale) for every approved shot (`06_generations/finals/`,
`06_generations/upscaled/`), all approved or rejected by the user, and a final contact sheet. Gate: the user's
words. There is no QA gate on finals, but the producer runs this when the user asks ("QA this"), or before the
review when the finals changed model or settings from the approved drafts.

Read: the shot list, the bible, the cards, the approved drafts and the finals in `project.json`, the preset, the
final contact sheet.

| id | check | how | kind | severity |
|---|---|---|---|---|
| FI-01 | Every shot has a completed final or upscale, and every final is approved or rejected (none undecided) before the stage closes. | `sc stage status finals --json`; `project.json` generations with tier final or upscale. | fact | blocker |
| FI-02 | Each final comes from an approved draft of the same shot (or the user's recorded words allowed it without one). | Generations: an approved draft per shot; or a decision with the user's words. | fact | blocker |
| FI-03 | The final keeps what was approved in the draft: framing, action, timing, character, product, look. Anything that changed is named. | Frames from the approved draft beside frames from the final at the same times. | judgement | major |
| FI-04 | Resolution meets the delivery and is not bigger than it needs (no upscale when the final already covers the delivery size). | `ffprobe` width and height against the preset's `resolution.delivery`. | fact | major |
| FI-05 | Continuity across the finals: DR-C01 to DR-C16 from `drafts.md`, on the finals. | As in drafts.md. | judgement | major |
| FI-06 | Artefacts: DR-05, DR-06 and DR-07 from `drafts.md`, at full resolution (finals show detail the drafts hid: skin, hands, small text, edges). | Frames at full size, cropped to the detail. | judgement | major |
| FI-07 | Length, frame rate and audio are what the edit needs: the clip covers the shot plus handles; audio is present only where the card asked for it. | `ffprobe -v error -show_entries stream=codec_type,r_frame_rate:format=duration -of json <file>` | fact | major |
| FI-08 | Cost: the actual spend of the finals is within what the user approved; any overrun is recorded with the user's words. | `sc budget status --json`; generations' `cost_estimate` and `cost_actual`. | fact | minor |
| FI-09 | Files are downloaded into the project and registered as assets with rights `generated` (provider links expire). | `sc asset list --role final --json` and `--role upscaled`. | fact | blocker |
| FI-10 | The final keeps the approved draft's light: same key side, ratio band, source colours and shadow direction, and still matches the scene light plan (final and upscale models can relight a shot). | Frames from the approved draft beside the final at the same times; then the light items DR-C04 and DR-C10 to DR-C16 on the final's cut pairs. | judgement | major |
