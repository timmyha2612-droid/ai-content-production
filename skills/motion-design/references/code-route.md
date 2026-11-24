# Code route

Motion graphics written as code and rendered to video. Works anywhere, including headless Linux and cloud
sessions, and keeps every graphic as editable text in the project (`07_mograph/code/<id>/`).

Facts below were checked in November 2026. Tools change fast: read each tool's own README and `--help` for the
installed version before running it, and ask the user before installing anything.

Common needs: Node.js (`sc.py doctor` shows if `node` is found), a headless Chrome or Chromium for HTML-based
renderers, and `ffmpeg` for encoding and preview frames.

## 1. HyperFrames (the default)

HyperFrames (by HeyGen, Apache-2.0) renders HTML pages animated with GSAP (or Lottie) into MP4. Good for lower
thirds, titles, end cards, kinetic type, simple charts and logo reveals.

- It ships its own Claude Code skills. If they are installed, use them for the HyperFrames specifics (project
  setup, the render command, timing helpers). If not, offer to install them following the HyperFrames README;
  do not guess its commands.
- One composition per graphic, in `07_mograph/code/<id>/`. Set the canvas size, frame rate and length from the
  mograph list and the delivery spec.
- Keep the exact text in one data object at the top of the file, so a change of wording is one edit.
- Fonts: load only fonts the user is licensed to embed (a local file in the project, or a web font whose
  licence allows it). Wait for fonts to load before the first frame renders, or the first frames use a fallback.
- Transparency: if HyperFrames cannot write alpha in the installed version, render on a solid key colour only as
  a last resort; prefer a renderer that writes alpha (Remotion, or an image sequence with alpha encoded with
  ffmpeg, below).

## 2. Remotion (React, licence caveat)

Remotion renders React components to video and handles alpha well.

- **Licence:** free for individuals and companies of up to 3 people. Companies with more than 3 people need a
  paid company licence (Nov 2026: Creators about $25 per seat a month; Automators $0.01 per render with a $100 a
  month minimum). Ask the user before using it: "Is your company more than 3 people? Remotion needs a paid
  licence then."
- Render: `npx remotion render <entry file> <composition id> 07_mograph/renders/M010.mov`.
- Alpha: `--codec=prores --prores-profile=4444` (and transparent backgrounds in the component), or
  `--codec=vp9` with an alpha pixel format for WebM. Check the flags with `npx remotion render --help`.

## 3. Revideo (MIT)

A code-first video framework (TypeScript, a fork of Motion Canvas) with no company licence fee. A good
alternative to Remotion when the licence is a problem and the user wants a React-free code base.

## 4. Lottie and dotLottie (UI icons, small loops)

- For animated icons in apps and on the web: deliver `.lottie` (dotLottie, compressed) or Lottie `.json`, plus a
  static `.svg` (and PNG sizes if asked).
- Ways to make them: hand-written Lottie JSON for very simple icons; AE with the Bodymovin exporter when the AE
  route is available; the LottieFiles Creator MCP if it is connected in this session.
- Keep icons small: few layers, no raster images inside, no expressions. Loop cleanly (the last frame matches the
  first). Match the icon grid in `look.md` (for example 24 px with 2 px strokes).
- Preview: render a few frames to PNG with a Lottie player in headless Chrome, or open the file in the LottieFiles
  previewer and screenshot it.

## 5. Manim (maths and exact data)

Manim (Community edition, MIT, Python) is best for charts, equations and data stories where numbers must be
exact.

- It is a Python package with system dependencies (Cairo, Pango, ffmpeg, optionally LaTeX). It is not part of
  shotcraft; ask before installing it in the user's environment.
- Render: `manim -qh scene.py SceneName` (high quality); `-t` for a transparent background (writes `.mov` with
  alpha). Set the frame rate and size to the delivery (`--fps`, `-r WIDTH,HEIGHT`; check `manim render --help`).

## 6. Encoding and previews with ffmpeg

From an image sequence with alpha (PNG) to a ProRes 4444 master:

```
ffmpeg -framerate 30 -i frames/%05d.png -c:v prores_ks -profile:v 4 -pix_fmt yuva444p10le 07_mograph/renders/M010.mov
```

WebM with alpha for the web:

```
ffmpeg -i 07_mograph/renders/M010.mov -c:v libvpx-vp9 -pix_fmt yuva420p -b:v 0 -crf 30 07_mograph/renders/M010.webm
```

H.264 for a full-frame card (no alpha):

```
ffmpeg -framerate 30 -i frames/%05d.png -c:v libx264 -pix_fmt yuv420p -crf 18 -movflags +faststart 07_mograph/renders/M020.mp4
```

A preview frame:

```
ffmpeg -ss 1.5 -i 07_mograph/renders/M010.mov -frames:v 1 07_mograph/previews/M010_hold.png
```

Check every render against the mograph list: `ffprobe -v error -show_entries stream=width,height,r_frame_rate,pix_fmt -show_entries format=duration -of json <file>`.
