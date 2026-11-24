# Route choice

Pick one route per graphic. The rule: **template fill > AE build > code (HyperFrames) > Lottie for icons**, then
adjust for the machine, the user's need for editable files, and licences.

## Decision table

| the graphic | the user has | best route | why |
|---|---|---|---|
| lower third, title, end card | an AE template or brand motion kit | AE template fill | Their look, their timing; only text and colours change. |
| lower third, title, end card | AE on a Mac, wants editable files | AE build (`scripts/ae/lower_third.jsx`) | They can open and tweak the `.aep`. |
| lower third, title, end card | no AE, or rendered files are enough | code: HyperFrames | Works headless anywhere, versionable, fast to change. |
| kinetic type, animated captions | anything | code: HyperFrames (GSAP text effects) | Precise per-word timing from a script or transcript. |
| logo animation | an AE logo template | AE template fill | Logos are brand assets; keep them in the brand's tool. |
| logo animation | an SVG logo, no AE | code: HyperFrames (SVG + GSAP) | Vector-sharp at any size. |
| animated UI icon for an app or the web | anything | Lottie / dotLottie | Tiny files, scale without loss, play natively in apps. Export a static SVG too. |
| chart, number count-up, data story | anything | code: HyperFrames (simple charts) or Manim (maths, precise data) | Numbers are exact; easy to update. |
| abstract animated background loop | anything | not this stage: a generated shot (`mograph-loop`) | Models do texture and motion well; plan it on the shot list. |
| many versions of one graphic (names, sizes, languages) | AE template | nexrender batch (AE) or a code loop | One template, a data file, many renders. |

## Questions that decide it

Ask only what the files don't answer:

1. Is there a template or brand motion kit? (Yes: template fill, whichever tool it is in.)
2. Does the user need editable source files, and in which tool? (AE files: AE route. "Just the video": any.)
3. Which machine runs it? macOS with AE: AE route possible. Windows with AE: AE route with `AfterFX.com -r`.
   Linux or cloud: code route only.
4. Is the brand font installed and licensed on that machine? (Missing fonts are the most common AE failure; on
   the code route, web fonts must be licensed for embedding.)
5. Is the user's company bigger than 3 people? (Remotion needs a paid company licence then; HyperFrames,
   Revideo and Manim do not.)

## Outputs by use

| use | file |
|---|---|
| overlay on video in an edit | ProRes 4444 `.mov` with alpha (Mac and most NLEs) |
| overlay for the web | WebM VP9 with alpha, plus a ProRes master |
| full-frame card or title | H.264 `.mp4` at the delivery size, fps and length |
| app or web icon | `.lottie` (dotLottie) or Lottie `.json`, plus static `.svg` |
| social platform upload of a graphic alone | H.264 `.mp4`, the platform's size |

Match the delivery: same frame rate as the edit, the delivery size (not bigger), exact length from the mograph
list. Keep text inside the safe zones of the platform.
