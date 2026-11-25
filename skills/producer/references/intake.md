# Intake: the grilling

The intake is the one deep conversation of a project. It is compulsory, it happens in one go before anything
is built, and its answers are never asked again. Every later stage reads the job card instead of asking.

## How to ask

- **Tool:** AskUserQuestion. At most 4 questions per call. Each question has 2 to 4 options; the tool adds
  "Other" so the user can type anything. Use `multiSelect: true` only where several answers can be true
  (platforms, stages to drop).
- **Recommended answer first.** Label it "(Recommended)" and put the reason in its description in one line
  ("Reels are 9:16 and up to 90 s on most accounts; 15 s keeps the hook tight"). Base it on the brief, the
  preset (`rules/presets.json`) and what costs the least while meeting the use case.
- **Header:** a 1-2 word chip (Goal, Audience, Length, Budget, Camera ...).
- **Frontier style.** Ask the decisions that shape everything else first. Each round is built from the
  answers to the last: drop questions that are now answered, sharpen the rest, add the follow-up a good
  producer would ask ("You said sound off: so every key line needs on-screen text. Who writes it?").
- **Never ask what the brief already answers.** Put it in the round's intro line instead: "From your brief:
  15 s Reel for the bakery launch. Four questions to pin down the rest."
- **Back to back.** Rounds follow each other with no other tool calls between, except reading a file the
  user just pointed to. Say at the start: "Starting the intake: about N questions in M rounds."
- **Plain English.** Gloss any craft term in the option description ("Dolly in: the camera moves toward the
  subject, which builds focus").
- **Record everything.** Every question and the user's answer, word for word, go into
  `00_brief/grilling.md` (heading per round). The job card is written from it.

## Round plan

| Round | Covers | Typical size |
|---|---|---|
| 0 (only on a new machine or unclear request) | Projects folder (first-run.md); track: refine / single / full | 1-2 |
| 1 Brief | Goal, audience, use case and platform, length and delivery | 4 |
| 2 Money and material | Budget, threshold, the user's own files and their rights, references, deadline | 3-4 |
| 3 Scope | Optional stages to drop, who does what, hand-off target, audio plan | 2-4 |
| 4 Subject and world | Who or what, action, place, era, time of day | up to 4 |
| 5 Camera and light | Camera language, movement appetite, lighting and look, mood | up to 4 |
| 6 Time and output | Pacing, beats, loop, transitions, on-screen text, audio | up to 4 |
| Close | Confirm the job card | 1 |

For the **single** track, merge rounds 4-6 into one round of the 4 questions that matter most for that asset.
For a creative piece where research and concept are on, keep rounds 4-6 light: ask the user's fixed points
and taste only. The creative-director will propose directions; do not pre-decide them here.

## Question bank

Pick from these. Each has the recommended-answer logic in brackets. Rewrite them for the user's project; do
not read them out as a list.

### Brief

1. **Goal.** "What should someone do or feel after watching?" Options: buy / book / sign up; remember the
   brand; understand a product or idea; entertainment or art. [Recommend what the brief implies.]
2. **One message.** "If they remember one thing, what is it?" [Offer two candidate lines drawn from the brief.]
3. **Audience.** "Who is it for, and where will they see it?" [Platform plus viewing mode: phone, sound off.]
4. **Prior knowledge.** "Do they know the brand or product already?" Options: never heard of it; know it,
   need a reason now; loyal fans.
5. **Call to action.** "What should the last frame ask?" [End card with one CTA; none for art pieces.]
6. **Success.** "How will you judge it worked?" Options: views and watch time; clicks or bookings; client
   sign-off; personal portfolio.
7. **Constraints.** "Anything that must or must not appear?" (people, competitors, claims, locations).

### Use case and delivery

1. **Platform / preset.** Options from `presets.json`: social-vertical, youtube, youtube-short, thumbnail,
   icon-ui, broll-insert, web-hero, banner-ad, product-shot ... [Recommend the preset that matches the platform.]
2. **Length.** Exact seconds for the master. [Preset's typical; shorter wins when unsure.]
3. **Versions.** "Do you need cut-downs or other aspects?" Options: one master only (Recommended for a first
   cut); master + 6 s bumper; master + 16:9 and 1:1 versions.
4. **Resolution and frame rate.** [The preset's delivery size; never bigger. Upscale only if the delivery
   needs more than the final model gives.]
5. **Format.** MP4 H.264 (Recommended), ProRes for an edit, PNG/JPG/WebP/SVG for stills, GIF/Lottie for UI.
6. **Handles.** For B-roll going into an edit: "Add half a second either end for the editor?" [Yes for
   broll-insert, no for social masters.]
7. **Safe zones.** For social: "Leave room for the platform's buttons and captions?" [Yes.]
8. **Deadline.** Date and time zone; what can drop if it slips.

### Budget

1. **Credits for the job.** Options built from a quick estimate: lean (drafts on cheap models, finals on
   the hero shots only), standard, premium. Give the number of credits for each. [Lean unless the brief says
   premium.]
2. **Single-job threshold.** "Ask before any one job above how many credits?" [The config default, usually 50.]
3. **Variants.** "How many takes per shot at draft?" [2 for video, 3-4 for stills.]
4. **Image first.** "Test risky video shots as a cheap still first?" [Yes: people, products, text, complex
   moves, shots 8 s or longer.]

### Rights and inputs (hybrid work)

1. **Your material.** "Are you bringing anything of your own?" multiSelect: footage you shot; photos;
   brand files (logo, fonts); a Blender scene or renders; After Effects or other renders; nothing.
   [Each file goes to `00_inputs/` as `owned` with a note.]
2. **Blender.** When they have or want a 3D environment: "Should we build or render the environment in
   Blender first and use the render as the start frame?" Options: yes, I'll render it; yes, use the Blender
   connection here (only if a Blender MCP is connected); no, generate it. [Blender first when the space must
   match a real or fixed layout across many shots.]
3. **Rights.** "Do you own or license everything you are giving me?" Options: all mine; some is licensed
   (I'll say which); some is reference only. [Anything unclear stays `reference-only`.]
4. **References.** "Any links that show the look or pacing you want?" [They are downloaded as
   reference-only and never sent to a model.]
5. **People.** "Real people in it? Do we have their consent and photos for a consistent face?" [A Soul ID
   needs 5-20 photos of a person who agreed.]
6. **Brand and IP.** "Any logos, characters or products that are not yours?" [Avoid: models reject protected
   content (`ip_detected`).]

### Stages and roles

1. **Drop stages** (multiSelect): research, concept, boards, sound, assembly, handoff. Explain each
   in its description. [Keep research and concept for new creative work; drop sound when there is no
   text or graphics; keep handoff on the full track.]
2. **Who does what.** "Anything you'll do yourself?" multiSelect: music and sound; the edit; colour grade;
   motion graphics; none. [Their stages are dropped with their words or marked as theirs on the card.]
3. **Hand-off.** "How do you want the result?" Options: Higgsfield Canvas build (Recommended on the full
   track: assets uploaded plus a node-by-node build sheet); files in the project folder only; both.
4. **Audio plan.** Options: native audio from the video model; a music bed and sound design added later;
   voice-over; silent with captions. [Silent with captions for sound-off social; native audio only when the
   model and shot benefit, since it can cost more.]

### Layer 1: intent (never written into prompts)

- What job does the piece do for the brand? Which platform behaviour matters (hook in 1 s, loop)?
- Who is the hero: the product, a person, a place, an idea?

### Layer 2: subject

- **Subject.** "Who or what is on screen?" [Concrete: "a woman in her 30s, flour on her apron", not "a person".]
- **Action.** "What do they do?" One clear action per shot. [Present tense, physical verbs.]
- **Wardrobe and props.** Fixed items that must stay the same across shots.
- **Consistency.** "Does the same character or product appear in several shots?" [Yes means a character
  sheet in the bible and a Soul ID or reference images.]

### Layer 3: world

- **Place.** Interior or exterior; real or invented; one location or several.
- **Era.** Present day (Recommended unless the brief says otherwise), period, near future.
- **Time of day.** Golden hour, blue hour, midday, night. [Golden hour for warmth; overcast for products.]
- **Weather and season.** Only when it matters.
- **Atmosphere.** Haze, rain, dust, steam, smoke. [Light haze helps light read on camera.]

### Layer 4: camera

- **Camera language.** Options: calm and composed (locked-off, slow dolly); energetic (handheld, whip
  pans, crash zooms); epic (crane, drone, wide); intimate (close-ups, shallow focus). [From tone.]
- **Movement appetite.** "One simple move per shot, or showpiece moves?" [One clear move per shot: models
  render one move well and several moves poorly.]
- **Lens feel.** Wide and immersive (24-35 mm); natural (50 mm); compressed and flattering (85-135 mm);
  macro for product detail.
- **Shot sizes.** Mostly wide, mostly close, or a mix with an establishing wide.

### Layer 5: light and look

- **Lighting.** Natural daylight; soft studio; high-key bright; low-key moody; neon or practicals.
- **Colour and grade.** Warm, cool, teal and orange, pastel, monochrome, brand colours. [Brand colours
  when there is a brand.]
- **Texture.** Clean digital (Recommended for products); film grain; vintage 16 mm; VHS.
- **Style reference.** Photoreal; cinematic; editorial; animation styles; 3D clay; flat graphic.
- **Mood.** Three words.

### Layer 6: time and output

- **Pacing.** Fast cuts (1-2 s shots); medium (3-4 s); slow and lingering (5 s+). [Fast for social hooks.]
- **Structure.** Hook, build, reveal, CTA; or a single continuous shot.
- **Loop.** "Should it loop seamlessly?" [Yes for web heroes and UI.]
- **Transitions.** Hard cuts (Recommended); match cuts; whip transitions; dissolves.
- **On-screen text.** Exact words, who writes them, captions for sound-off viewing. [Text is added in
  motion graphics, not generated, unless it is one short word on an image model good at text.]
- **Audio.** Native sound, music mood, voice-over script and voice.

## Writing grilling.md

```markdown
# Grilling: <Project>

## Round 1: Brief (<date>)
- Q: What should someone do or feel after watching?
  A: "<user's words>"
- Q: ...
```

Then write the job card (`job-card.md` in this folder) and show it for confirmation.
