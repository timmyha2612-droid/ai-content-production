# After Effects route

After Effects (AE) runs only on macOS and Windows. Claude drives it in one of three ways, best first:

1. **An MCP bridge** that is connected in this session.
2. **ExtendScript (JSX) files** run through `osascript` on the Mac (`scripts/ae/run_jsx.sh`), or `AfterFX.com -r`
   on Windows.
3. **Rendering without the AE window**: `aerender` for renders, `nexrender` for template fill and batches.

Always: **template fill first, build second.** If the user has a template, only change its text, colours and
media. Build from scratch only when there is no template.

Facts below were checked in November 2026. Re-check versions and flags (`--help`) before relying on them.

## 1. MCP bridges

Use a bridge when its tools are available in this session. They talk to a running AE, so the user's Mac must be
on, AE open, and the user nearby for dialogs.

- **kumoproductions/mcp-aftereffects** (MIT). No AE panel to install; it passes commands through a mailbox
  folder. Supports AE 2024 to 2026. Can render single frames for previews. A modal dialog in AE blocks it until
  someone closes the dialog.
- **The Artlist MCP AE bridge.** Needs Artlist's desktop host running on the Mac. Its tools (names start with
  `ae_`, for example a version check, project and comp info, an action tool, single-frame render, asset import,
  save) cover inspecting, editing and previewing.

How to work with a bridge:
1. Check the version and the open project first (the bridge's version and project-info tools).
2. Never close or overwrite the user's open project. Save new work as a new file in `07_mograph/ae/`.
3. After each change, render one preview frame and look at it before going on.
4. If a call hangs or times out, ask the user to look at AE: almost always a dialog is open.

## 2. ExtendScript through osascript (macOS)

AppleScript's `DoScriptFile` broke on AE 2024 with macOS Sonoma. The JavaScript-for-Automation (JXA) form works:

```
osascript -l JavaScript -e 'Application("Adobe After Effects 2026").doscriptfile("/abs/path/script.jsx")'
```

`scripts/ae/run_jsx.sh` wraps this (below, `$MD` is `${CLAUDE_PLUGIN_ROOT}/skills/motion-design`). It finds the newest installed AE (or the one you name), passes a JSON
parameter file to the script, and prints the script's JSON result:

```
bash "$MD/scripts/ae/run_jsx.sh" --list
bash "$MD/scripts/ae/run_jsx.sh" "$MD/scripts/ae/lower_third.jsx" params.json
bash "$MD/scripts/ae/run_jsx.sh" --app "Adobe After Effects 2025" "$MD/scripts/ae/render_queue.jsx" rq.json
```

It writes a small wrapper script that sets `$.global.SC_PARAMS_FILE` and `$.global.SC_RESULT_FILE`, then runs the
helper with `$.evalFile`. Exit codes: 0 ok, 1 the script failed, 3 no AE found, 4 not macOS, 5 macOS refused
permission.

### The helpers (`scripts/ae/`, ES3 ExtendScript)

| script | does | key params |
|---|---|---|
| `lower_third.jsx` | builds a lower third comp: accent bar + title + subtitle, eased in and out, optional preview PNG | `comp_name`, `width`, `height`, `fps`, `duration_s`, `title`, `subtitle`, `font_title`, `font_subtitle`, `title_size`, `subtitle_size`, `text_color`, `bar_color`, `align` (left, right, center), `margin_px`, `anim_in_s`, `anim_out_s`, `save_project`, `preview_png`, `preview_time_s` |
| `import_and_comp.jsx` | imports generated clips and lays them out in shot order in one comp, trimmed to each shot's length, with a marker per shot | `comp_name`, `width`, `height`, `fps`, `clips` [{`path`, `shot`, `in_s`, `duration_s`}], `sort_by_shot`, `fit` (fill, fit, none), `folder_name`, `save_project` |
| `render_queue.jsx` | adds comps to the render queue with a render settings template and an output module template, optional render now | `comps` [names], `output_dir`, `output_template`, `render_template`, `render_now`, `save_project` |

Colours are `[r, g, b]` from 0 to 1. Paths must be absolute. Each script writes `{"ok": true|false, ...,
"warnings": [...]}` to the result file; read the warnings (missing fonts, missing templates).

Example `params.json` for a lower third:

```json
{
  "comp_name": "M010_lower-third",
  "width": 1080, "height": 1920, "fps": 30, "duration_s": 3.0,
  "title": "Ana Ruiz", "subtitle": "Head Roaster",
  "font_title": "Inter-Bold", "font_subtitle": "Inter-Regular",
  "title_size": 64, "subtitle_size": 40,
  "text_color": [1, 1, 1], "bar_color": [0.93, 0.55, 0.2],
  "align": "left", "margin_px": [96, 520],
  "anim_in_s": 0.5, "anim_out_s": 0.4,
  "save_project": "/Users/me/Projects/reel/07_mograph/ae/M010_lower-third.aep",
  "preview_png": "/Users/me/Projects/reel/07_mograph/previews/M010_hold.png",
  "preview_time_s": 1.5
}
```

Fonts are PostScript names (`Inter-Bold`, not `Inter Bold`). On AE 2024 and later the script checks each font
and warns if it is missing.

### Windows

```
"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.com" -r C:\path\wrapper.jsx
```

Write the same wrapper by hand: set `$.global.SC_PARAMS_FILE` and `$.global.SC_RESULT_FILE`, then
`$.evalFile("C:/path/lower_third.jsx")`.

## 3. Rendering

### aerender (ships with AE)

Renders a saved project without the AE window. Fast and reliable for finals.

```
"/Applications/Adobe After Effects 2026/aerender" -project /abs/M010_lower-third.aep \
  -comp "M010_lower-third" -RStemplate "Best Settings" -OMtemplate "High Quality with Alpha" \
  -output /abs/07_mograph/renders/M010_lower-third.mov
```

- `-s` and `-e` set the start and end frame (a single frame for a preview: the same number for both, with an
  image sequence output template such as "PNG Sequence" if your AE has one; otherwise use the helper's
  `preview_png`).
- Output module template names differ between AE versions. List them in AE (Edit > Templates > Output Module) or
  read the warnings from `render_queue.jsx`, which lists the ones it found.
- H.264 output from the render queue exists in AE 2023 and later; older versions need Media Encoder.

### nexrender (template fill and batches)

nexrender fills an AE template from a JSON job (text layers, images, colours) and renders it with aerender, on
macOS or Windows workers. Use it for many versions of one template (names, sizes, languages).

- A job names the template (`template.src`, `template.composition`), the assets to replace (by layer name), and
  post-render actions (encode, copy).
- Run one job with its CLI (for example `npx @nexrender/cli --file job.json`, pointing `--binary` at `aerender`);
  check the exact flags with `--help` for the installed version.
- Ask before installing it (it needs Node).

## 4. Preview frames

Always look before showing the user:
- Bridge: its single-frame render tool.
- JSX: the helpers' `preview_png` (uses `CompItem.saveFrameToPng`, which works but is not in Adobe's documented
  API; if it fails the result says so).
- From a finished render: `ffmpeg -ss 1.5 -i M010.mov -frames:v 1 07_mograph/previews/M010_hold.png`.

## 5. Known breakages and fixes

| symptom | cause | fix |
|---|---|---|
| A call hangs, the bridge times out, osascript waits forever | A modal dialog is open in AE (missing fonts, "saved in a newer version", crash recovery, update notice, "script wants to write files") | Ask the user to look at AE and close the dialog. The helpers wrap work in `app.beginSuppressDialogs()`, which stops some, not all. |
| osascript error -1743 "Not authorized to send Apple events" | macOS Automation permission | System Settings > Privacy & Security > Automation: allow the terminal app (or Claude) to control After Effects. The user must click this; never script it. |
| Script runs but cannot read params or write results | AE's scripting file access is off | AE > Settings > Scripting & Expressions: tick "Allow Scripts to Write Files and Access Network". |
| Text shows in a fallback font, or a "missing fonts" dialog | The font is not installed or not activated | Ask the user to install or activate it (Adobe Fonts, their licence). Never swap fonts without their yes. |
| osascript returns error -1712 (timed out) on a long render | Apple events time out after about 2 minutes; AE keeps working | Render with `aerender` instead of `render_now`, or wait and check the output file. |
| `doscriptfile` not understood | Wrong application name | Use the exact app name from `run_jsx.sh --list` (for example "Adobe After Effects 2026"). |
| Expressions error on a template | The template uses an expression engine or effect the installed AE lacks | Ask the user; do not rewrite their template's expressions without a yes. |

UXP plugins for AE are in public beta only (Nov 2026) and Adobe's own local MCP is in private beta (expected
early 2027). Do not depend on either yet; check again when they ship.
