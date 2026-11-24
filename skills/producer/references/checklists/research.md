# QA checklist: research

Stage outputs: `01_research/notes-*.md` (one per angle), `01_research/direction-note.md` (the merge), downloaded
references in `01_research/refs/` registered as assets. Gate: QA PASS.

Read: the job card, `01_research/direction-note.md`, every `notes-*.md`, the preset for the job's use case
(`${CLAUDE_PLUGIN_ROOT}/rules/presets.json`), `sc asset list --role reference --json`.

| id | check | how | kind | severity |
|---|---|---|---|---|
| RS-01 | `01_research/direction-note.md` exists and at least one asset has role `reference` (the stage evidence). | `sc stage status research --json`; `sc asset list --role reference --json` | fact | blocker |
| RS-02 | Every reference the notes cite exists as an asset, with its source URL and rights `reference-only`. | Match each asset id in the notes with `sc asset list --role reference --json`. Any reference marked `owned` or `licensed` without a recorded decision is a finding. | fact | blocker |
| RS-03 | Every file in `01_research/refs/` is registered as an asset (nothing downloaded and left untracked). | `ls -R 01_research/refs` against the asset list. | fact | major |
| RS-04 | The research answers the job card: the goal, the audience, the platform and the length. Each angle the producer asked for has a note. | Read the job card's Goal, Audience, Use case and Delivery lines; find where each is addressed. | judgement | major |
| RS-05 | Claims carry evidence: counts, durations, dates, asset ids. No "punchy hooks work well" without numbers or examples. | Read each "take" line and its support. | judgement | major |
| RS-06 | References are recent for platform patterns (social: mostly the last 6 months) and every one is dated. | The notes' dates and the yt-dlp info files next to downloads. | fact | minor |
| RS-07 | The direction note separates what to take (structure, pacing, framing ideas) from what is someone else's identity (their face, logo, exact set, character). Nothing proposes copying a creator, a brand or a real person. | Read the take and avoid lists. | judgement | blocker |
| RS-08 | The take and avoid lists are numbered, concrete and usable by the writer and the designers. | Read them: each item should be actionable in one line. | judgement | minor |
| RS-09 | Generation risks are named: legible text, fine hand work, crowds, fast physics, exact logos or products, and the cheaper route for each (image first, motion graphics for text, the user's own footage). | Compare the references and the idea with `${CLAUDE_PLUGIN_ROOT}/skills/prompt-craft/SKILL.md`. | judgement | major |
| RS-10 | Platform numbers match the preset: aspect, length, safe zones, loudness. Where research disagrees with the preset, the note says so and gives the source. | Compare with the preset entry. | fact | major |
| RS-11 | Contradictions between angles are resolved in the direction note (which evidence wins and why). | Read the notes side by side. | judgement | minor |
| RS-12 | Open questions are only what research could not settle, and none of them was already answered in `00_brief/grilling.md`. | Compare with grilling.md. | fact | minor |
| RS-13 | Failed fetches are listed with the reason; nothing was fetched by getting around a sign-in, paywall or private account. | The notes' Sources section; `sc asset list` source URLs. | fact | blocker |
| RS-14 | Real-world detail is there when the piece depends on a place, an era or a trade: materials, signage, props, wardrobe, light. | Read the visual-world note, if that angle was asked for. | judgement | minor |
