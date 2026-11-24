# Research findings (2026-11-24) — build-time notes, re-verify before relying on them

## Higgsfield
- Official Claude Code plugin exists: `higgsfield-ai/skills` (`/plugin install higgsfield@higgsfield`, 9 skills). shotcraft is the "director" and works alongside it; it does not rebuild it.
- Three surfaces:
  - CLI `@higgsfield/cli` (binary `higgsfield`, `higgsfield auth login`, plan credits, `model list/get --json`, `generate cost`). **shotcraft uses this.**
  - Hosted MCP `https://mcp.higgsfield.ai/mcp` (OAuth, plan credits; exact tool names unconfirmed).
  - REST API `api.higgsfield.ai` (header `Authorization: Key id:secret`, separate prepaid USD; POST /{model_path}; GET /requests/{id}/status; statuses queued/in_progress/completed/failed/nsfw/canceled). The CLI and REST catalogues and IDs DIFFER.
- Negative prompts: not exposed on CLI image/video models (only tripo_3d). Higgsfield's guide: "Phrase positively". Keep prompts under about 200 tokens. Image-to-video: describe motion only.
- Seed is mostly not exposed; fps is not a parameter. The CLI clamps out-of-range values and returns `adjustments`; unknown params are a hard error.
- Trap: `nano_banana_2` = Nano Banana **Pro**; `nano_banana_flash` = Nano Banana 2.
- Terminal statuses include `nsfw` and `ip_detected`. Back off on 429 and captcha HTML (wait 30 s).
- Output URLs may expire (about 7 days, unconfirmed): download immediately.
- Soul ID: `higgsfield soul-id create --name X --soul-2|--soul-cinematic --image ...` (5–20 photos), then `--soul-id` on text2image_soul_v2 / soul_cinematic.
- Camera presets: Cinematic Studio 3.5 `camera_style` (classic_static, one_take, epic_scale, impossible_camera, documentary_snap, raw_chaos, dreamy_flow…), `light_scheme`, `color_grading`, `genre`, `speedramp`. The web app's DoP has 50+ named moves (crash zoom, dolly zoom, crane up, bullet time, FPV drone…).
- Sora 2, DoP and Lipsync Studio appear to be web-app only.
- Upscale/utility jobs: topaz_image, topaz_video, bytedance_image_upscale, bytedance_video_upscale, video_upscale, video_deflicker, color_grading_lut, reframe, outpaint, background removers.
- Credit costs (mixed sources): Nano Banana Pro 2/img (4 at 4K); Seedance 2.5 35/5s@720p, 80@1080p; Seedance 2.0 about 22/5s@720p; Kling 3.0 about 7–10/5s@720p; Veo 3.1 about 29–40/4s. Plans are about $0.04–0.075/credit. ALWAYS use `generate cost` live.
- **Canvas** (node-based board) has NO API/CLI/MCP access as of Nov 2026 (open feature request higgsfield-ai/cli#2). Hand-off = upload assets + Canvas build sheet + optional browser-assisted build.

## Motion graphics
- AE needs Mac/Windows. Routes:
  - kumoproductions/mcp-aftereffects (MIT, no panel, mailbox folder, AE 2024–2026, single-frame previews; modal dialogs block it).
  - The Artlist MCP AE bridge (needs Artlist's desktop host on the Mac).
  - ExtendScript via `osascript -l JavaScript -e 'Application("Adobe After Effects 2026").doscriptfile("x.jsx")'` (AppleScript DoScriptFile broke on AE 2024 + Sonoma).
  - aerender for renders; nexrender for template fill + batch (Mac/Win workers).
- UXP for AE is in public beta only. Adobe's local MCP has a private beta expected in early 2027.
- Code route, works headless on Linux:
  - HyperFrames (HeyGen, Apache-2.0, HTML+GSAP/Lottie → MP4, ships Claude Code skills). The default.
  - Remotion (paid for companies >3 people: Creators $25/seat/mo, Automators $0.01/render with a $100/mo minimum).
  - Revideo and Manim (MIT).
  - Lottie/dotLottie for UI icons (LottieFiles Creator MCP).
- Main breakages: modal dialogs, macOS Automation/Accessibility permissions, missing fonts.
