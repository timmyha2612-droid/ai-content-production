# QA checklist: delivery

Stage output: the deliverable files in `09_delivery/` and `09_delivery/delivery-report.json` written by
`sc delivery check`, with every check PASS. Gate: the spec check. The producer runs this checklist when the user
asks, or before telling the user the job is ready.

Read: the job card's Delivery line, the preset (`sc delivery check` uses it), the delivery report, the
deliverables, the licence notes in `07_sound/`.

You are read-only: `sc delivery check` writes the report, so do not run it. Re-measure without writing:

```
python3 -c "import sys,json; sys.path.insert(0,'${CLAUDE_PLUGIN_ROOT}/scripts'); from shotcraft import delivery; print(json.dumps(delivery.check('<project>', write=False), indent=1))"
```

| id | check | how | kind | severity |
|---|---|---|---|---|
| DL-01 | `09_delivery/delivery-report.json` exists, is newer than every deliverable, and every check in it is PASS. | Read it; compare its time with the files' modified times (`ls -lt 09_delivery`: the report should be on top). | fact | blocker |
| DL-02 | Your own re-measure agrees with the report (no file changed after the report). | The read-only check above. | fact | blocker |
| DL-03 | Every deliverable the job card asks for is there: each format, aspect and size, the cut-downs, the thumbnails or stills. | Compare the Delivery line with `ls 09_delivery`. | fact | blocker |
| DL-04 | The spec: resolution, aspect, frame rate, codec, pixel format (yuv420p for social H.264), audio codec and sample rate, file size limit. | The report, or `ffprobe -v error -show_entries stream=codec_name,width,height,r_frame_rate,pix_fmt,sample_rate:format=duration,size -of json <file>` | fact | blocker |
| DL-05 | Duration within 0.5 s of the planned length (or the job card's tolerance). | The report's duration items. | fact | blocker |
| DL-06 | Loudness (when there is audio): integrated loudness within 1 LU of the target (default -14 LUFS for social and web), true peak at or below -1 dBTP. | The report's loudness items; re-measure with `ffmpeg -hide_banner -nostats -i <file> -af ebur128=peak=true -f null -` and read the summary. | fact | major |
| DL-07 | The picture survived the export: no black frames at the start or end, no frozen frames, no letterbox bars that should not be there, nothing important cropped off. | `ffmpeg -i <file> -vf blackdetect=d=0.1:pix_th=0.10 -an -f null -` and `freezedetect=n=-60dB:d=0.5`; frames at start, middle and end. | fact | major |
| DL-08 | Framing after any reframe (for example 16:9 to 9:16): faces, product and text are still in frame and inside the safe zone. | Frames against the preset's `safe_zone`. | judgement | major |
| DL-09 | Not upscaled past what the source holds: a deliverable bigger than its source final is flagged (it should have gone through an upscale generation, with the user's yes). | Compare each deliverable's size with its source asset's size. | fact | major |
| DL-10 | File names say what they are and match the job (`<project-slug>_<preset>_<WxH>_v<N>.<ext>`, shot deliverables include the shot id), no spaces, no duplicates. | `ls 09_delivery`. | fact | minor |
| DL-11 | Licences: every music, sound, font and stock asset in the deliverables has a licence note covering this use. | `07_sound/` licence notes, `sc asset list --rights licensed --json`. | fact | blocker |
| DL-12 | No reference-only material ended up in a deliverable (a downloaded reference used as a frame, a sound or a still). | Compare the sources the delivery agent lists with `sc asset list --rights reference-only --json`. | fact | blocker |
| DL-13 | Social extras when the job card asks for them: captions file (.srt or burned in), a cover frame or thumbnail inside the platform's limits. | `ls 09_delivery`; image size and file size. | fact | minor |
| DL-14 | No digital silence (when there is audio): no stretch of pure digital zero, 0.5 s or longer. Real recordings never fall to absolute zero, and silence between cuts sounds dead. Fix: the per-scene room tone and ambience beds belong in the sound mix (a missing scene bed goes back to sound); as a safety floor, `sc finish roomtone` lays one bed under the whole file (the neutral safety bed from `07_sound/mix-notes.md`, or generated pink noise when there is none). Skipped only when the preset or the project's delivery block sets `allow_digital_silence: true`; the job card or `grilling.md` must give the user's reason. | The report's digital-silence item; re-measure with `ffmpeg -hide_banner -nostats -i <file> -af silencedetect=n=-90dB:d=0.5 -f null -` and read the time ranges. | fact | major |
| DL-15 | One matched grain setting across every shot of the job, and it is the job card's `Grain:` line: if `sc finish texture` was used, every shot got the same `--grain` value (and the same `--vignette` choice); with grain `off` and no vignette, texture was skipped. Clean presets usually have no grain. | Compare the finish notes or generation records per shot; frames side by side at 100%. | fact | minor |
| DL-16 | Disclosure intact: the natural finish (grain, room tone) is a craft fix for a natural look, never a way past AI detection. No provider watermark is cropped, blurred or covered, no metadata is edited to hide AI origin, and `09_delivery/delivery-notes.md` (written by the delivery agent) always carries the AI-label line for realistic AI content, whether or not the finish ran (Content Credentials (C2PA) do not survive any edit or re-encode, so the label is the disclosure). | Frames, for watermarks; `ffprobe -v error -show_format <file>` tags against the source final; `09_delivery/delivery-notes.md`. | fact | blocker |
| DL-17 | Audio covers picture (when there is audio; the report's "audio covers picture" item): the audio track runs to the end of the picture, so the last seconds do not play in dead silence. | The report's "audio covers picture" item; `ffprobe -v error -show_entries stream=codec_type,duration -of json <file>`. | fact | major |
