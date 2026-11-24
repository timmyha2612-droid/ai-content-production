# QA checklist: mograph (motion graphics)

Stage output: files in `07_mograph/` (`ae/` for After Effects projects and renders, `code/` for HyperFrames,
Remotion, Lottie or similar). Gate: QA PASS, then the user's words.

Read: the script (exact on-screen text), the shot list's mograph column, the bible (`look.md` palette and type
rules, the brand files from `00_inputs/`), the preset (aspect, fps, safe zone), the renders.

Extract frames from each render at the start, at the moment each text element is fully on screen, and at the
end (see the script-supervisor's frame recipes; any reviewer can use them).

| id | check | how | kind | severity |
|---|---|---|---|---|
| MG-01 | Every graphic the shot list and script ask for exists as a render (and its source project or code is kept). | Compare the mograph list with `ls -R 07_mograph`. | fact | blocker |
| MG-02 | The text is exactly the script's text: wording, spelling, capitals, punctuation, numbers, prices, dates. | Frames against the script, letter by letter. | fact | blocker |
| MG-03 | Read time: each text element is fully on screen for at least 1 s plus 0.3 s per word. | Frame times from in to out of each element. | fact | major |
| MG-04 | Safe zone: text and logos sit inside the preset's safe zone for the platform (9:16: clear of the top, bottom and right edge areas). | A frame measured against the preset's `safe_zone` pixels. | fact | major |
| MG-05 | Legibility: size and contrast are enough on a phone (text height at least about 3% of frame height for body text on social; strong contrast against what is behind it). | Frame measurements. | judgement | major |
| MG-06 | Brand: fonts, colours (hex from the bible or brand files) and logo use follow the brand; the logo is the user's file, never redrawn by a model. | Compare with `look.md` and the brand files; check the logo asset's rights. | fact | major |
| MG-07 | Fonts are licensed for this use and present (no fallback font in the render). | The project or code's font list; frames for fallback shapes. | fact | major |
| MG-08 | Technical match with the picture: same resolution, aspect and frame rate as the delivery; alpha where it will be overlaid (ProRes 4444 or PNG sequence, or a clear note that it is a full-frame render). | `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,pix_fmt,codec_name -of json <file>` | fact | major |
| MG-09 | Timing matches the cut: each graphic's in and out match the script's time ranges and the shot it sits on (within 2 frames). | Compare with the script and `09_assembly/shots.csv` if it exists. | fact | major |
| MG-10 | Motion quality: easing (no linear starts and stops unless the style asks for it), no jumps, no clipped animation at the start or end, loops loop cleanly. | Frame strip at the frame rate around each in and out. | judgement | minor |
| MG-11 | Style matches the chosen concept and is consistent across every graphic in the piece. | Frames side by side. | judgement | minor |
| MG-12 | Taste: style choices that break no rule (which animation, which accent colour) are the user's. | Raise as a question only. | creative | minor |
