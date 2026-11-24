# QA checklist: script

Stage output: `03_script/script.md`, a two-column audio-visual script (PICTURE | SOUND and TEXT) with timings.
Gate: QA PASS, then the user's words.

Read: the job card, `02_concept/chosen.md`, `01_research/direction-note.md` (if research ran), the script, the
preset for the use case.

| id | check | how | kind | severity |
|---|---|---|---|---|
| SC-01 | The file exists and is in two columns with a time range on every row. | Read it. | fact | blocker |
| SC-02 | The rows add up to the delivery length on the job card within 0.5 s, and the stated total matches the rows. | Add the time ranges yourself. Give both numbers. | fact | blocker |
| SC-03 | Time ranges are continuous: no gaps, no overlaps, each row starts where the last ended. | Read every range. | fact | major |
| SC-04 | The hook is in the first 1-2 s, works with the sound off, and opens on motion, a face, a question, a surprising image or a result, never on a logo or a slow establishing shot (unless the job card asks for it). | Read the first row's picture column alone. | judgement | major |
| SC-05 | One message. The script says one thing, and it is the job card's goal. | Write the message in one sentence; compare with the Goal line. | judgement | major |
| SC-06 | The structure fits the length: under 20 s hook, one idea, payoff or call to action; 20-60 s hook, problem, turn, proof, payoff, call to action (or an equivalent); longer: a clear turn. | Map the rows to beats. | judgement | minor |
| SC-07 *(VO)* | Voice-over fits its time: about 2.5 words per second (2.0 calm or premium, up to 3.0 for a fast social read). Every row over the pace the script states is a finding. | Count the words per row and divide by the row's seconds. Give the numbers. | fact | major |
| SC-08 *(VO)* | Air: 0.3-0.5 s after the hook line and before the call to action. | Read the timings. | judgement | minor |
| SC-09 *(text)* | On-screen text: at most 5-7 words per card, held at least 1 s plus 0.3 s per word, exact wording and capitals given, and marked as designed text or caption. | Count words and hold times. | fact | major |
| SC-10 | One call to action, specific, in the last 2-3 s, matching the job card. | Read the last rows. | fact | major |
| SC-11 | Every picture line is something a model can make: one subject action, one camera idea, no legible text in the generated picture (text goes to motion graphics), no fine hand work or crowds without a plan, no real people's likeness, no brand logos the user does not own. | Read each picture line against `${CLAUDE_PLUGIN_ROOT}/skills/prompt-craft/SKILL.md`. | judgement | major |
| SC-12 | The picture and the voice-over do not say the same thing twice. | Read row by row. | judgement | minor |
| SC-13 | The script follows the chosen concept and the user's recorded likes and dislikes. | Compare with `02_concept/chosen.md` and `00_brief/grilling.md`. | fact | major |
| SC-14 | Claims in the script (prices, results, health, "best", "number one") are backed by the brief or flagged for the user. | Read every claim; find its source in the brief. | fact | major |
| SC-15 | Music and sound cues are described as a mood, tempo and where they hit, not as a named commercial track the job has no licence for. | Read the sound column. | fact | major |
| SC-16 | Plain, spoken English: short sentences, contractions, no lists of three adjectives, nothing the viewer has to read twice. | Read it aloud at pace. | judgement | minor |
| SC-17 | The writing is the user's call where it is taste: tone, jokes, word choice that breaks no rule. Raise these as `creative`, never as a FAIL. | Only raise what you would ask the user. | creative | minor |
