# Composition and lighting: the short version

How to pick framing and light from what a shot must make the viewer feel, and how to write it so a model
renders cinema instead of a catalogue picture. This is the compact version of two research guides. Go to the
full guides for each technique's visual rules, failure modes, fixes and reference frames:

- `${CLAUDE_PLUGIN_ROOT}/docs/research/cinematic-composition-guide.md` (15 techniques: where things sit).
- `${CLAUDE_PLUGIN_ROOT}/docs/research/cinematic-lighting-guide.md` (16 setups: what the eye sees first and what
  stays hidden).

One idea runs through both: **cinema frames are built in planes, lit from one place the audience can believe
in, and never too clean.** Models do the opposite by default: subject pasted flat, lit from everywhere, every
shadow lifted, every skin polished.

Jargon in one line: *key* = the main light. *Fill* = light that lifts the shadows. *Rim* = light from behind
that outlines the subject. *Practical* = a lamp, screen or sign that appears in shot. *Ratio* = how much
brighter the lit side is than the shadow side (2:1 soft, 8:1 dramatic). *Falloff* = how fast light fades with
distance. *Motivated* = light that seems to come from a real source in the scene. *OTS* = over-the-shoulder.

## How to use this

1. Start from the story intent (what the viewer should feel), not from a technique you like.
2. Pick one composition row and one light row. Combine two or three techniques at most: one geometry, one
   depth, one light.
3. Copy the key phrase, then make it specific: the real object, colour, side and frame edge for this shot.
4. Fill `light_look` from the setup's entry in `rules/light_setups.json` (`setup`, `quality`, `direction`,
   `color_temp`, `practicals`, a `finish` default, `stays_dark`, `do_not_use_when`).
5. Run the checklist at the end before handing the card over.

## Composition chooser

| Intent | Technique | Key phrase |
|---|---|---|
| Place a character inside a world | Depth layers + atmosphere | "distinct foreground, midground and background, haze increasing with distance" |
| Outsider, between two worlds | Frame in frame (doorway) | "framed by a dark doorway, bright landscape beyond, subject small in frame" |
| Being watched | Frame in frame (lit window) + high angle | "seen through a lit window at night, dark brick facade around it" |
| Trapped by tradition or a system | Nested frames, symmetry, high angle | "nested doorways receding into depth, figure small in the farthest one" |
| Fate, isolation, the road ahead | Leading lines, vanishing point | "lone small figure at the vanishing point, one-point perspective" |
| Order, power, ritual, deadpan | Symmetry, centre-punch | "subject dead centre, square-on to the back wall, symmetrical but lived-in" |
| Natural, unforced | Rule of thirds | "subject on the right third, looking into open space on the left" |
| Loneliness, awe, smallness | Negative space and scale | "extreme wide shot, figure under 5% of the frame" |
| Power, threat, hero | Low angle | "camera on the ground looking up, ultra-wide lens, figure towering against sky" |
| Defeat, being judged | High angle, top-down | "direct overhead shot, tiny figure on empty asphalt" |
| Mystery, opening or ending | Silhouette | "backlit figure as a solid black silhouette, exposed for the sky" |
| Secrecy, menace, a moral choice | Chiaroscuro, pool of light | "single hard key, no fill, 70 percent of the frame in deep black" |
| Two people | OTS, two-shot, distance | "over-the-shoulder, near shoulder soft and dark, his eyeline just off-lens" |
| Peak emotion, a decision | Close-up, extreme close-up | "extreme close-up, cropped at forehead and mid-nose, hard side light" |
| Find a small subject fast | Colour blocking | "two-colour palette, small figure in a red coat against gold leaves" |
| Mood and scale at night or in nature | Atmosphere (haze, rain, shafts) | "strong backlight through haze, figure walking into fog" |
| Native vertical that feels like cinema | Vertical 9:16 | "small lone figure in the lower third, towering shadowed wall above" |
| Chase, arrival, journey | Staging for movement | "action along the lens axis toward camera, large cropped foreground figure" |

## Light chooser

| Intent | Setup | Key phrase |
|---|---|---|
| Hidden motives, gravitas | Rembrandt | "single key high and 45 degrees frame-left, small triangle of light under the far eye, background near-black" |
| Glamour, star reveal, beauty | Butterfly / Paramount | "hard key on the lens axis, high, angled down, small shadow straight under the nose" |
| Duality, threat, interrogation | Split | "hard side light at 90 degrees at eye height, half the face in shadow" |
| Everyday drama close-ups | Loop, broad or short | "soft key 30-45 degrees, slightly high, on the far side of the face" |
| Optimism, clean commercial, dream | High key | "large soft frontal light, low contrast, one colour temperature" |
| Menace, secrets, noir | Low key | "single hard key, fast falloff, the room falls into deep shadow" |
| Introspection, quiet domestic | Window light | "soft window light from frame-left, gradual falloff, room dims away from the glass" |
| Mystery, longing, memory | Backlight / rim | "low sun behind the subject, rim on one side, face in soft shadow" |
| Night interiors, screen life | Motivated practicals | "warm desk lamp the only light, steep falloff, back of the room black" |
| Nostalgia, romance, endings | Golden hour | "low sun behind, contre-jour, warm rim, cool sky in the shadows" |
| Melancholy, transition | Blue hour | "deep blue sky behind, warm tungsten lamps in the windows" |
| Urban noir, restless night | Night exterior, mixed colour | "orange sodium streetlight and a green fluorescent shopfront, each in its own pool" |
| Grief, austerity, realism | Overcast | "soft overcast sky from above, low contrast, shadows keep detail but stay dark" |
| Heat, summer, trapped | Hard sun / dappled | "hard low sun through venetian blinds frame-right, stripes across face and wall" |
| Period, intimacy, survival | Firelight / candlelight | "candle the only light, low and warm from below, cool night outside" |
| Power, isolation in a pool | Top light | "single pendant lamp overhead, pool of light on the table, room black" |

**Setup fit.** Check `do_not_use_when` before committing. Rembrandt is wrong for bright comedy or beauty;
butterfly is wrong for grit or documentary (it looks posed); split is wrong whenever both eyes must read.

## Depth patterns: tone before blur

Separate planes by brightness first and focus second. Commit to one pattern per card and give every depth field
a value word (dark, lit, bright accent, clipped) as well as its content.

| Pattern | Foreground | Subject | Near background | Far background | Setups |
|---|---|---|---|---|---|
| Dark-light-dark | dark shape | brightest, in the pool | falls to black | black or one small accent | Rembrandt, split, low key, practicals, top light, firelight |
| Dark-lit-bright | dark frame | rim-lit or silhouetted | glowing edges | brightest (sky, window, haze) | backlight, golden hour, blue hour |
| Dark-lit-patterned | dark mass | crossed by the pattern | cast shadow and pattern | brightest patterned wall or street | hard sun, dappled |
| Bright recedes | clean or a little darker | dark accent against pale | one step down | brightest, often clipped | high key, overcast |

Example: `world.foreground` "dark out-of-focus door jamb filling the left edge"; `world.background_far` "one
warm lit window, otherwise black".

## Rules for every shot

**Planes**
- Name at least three planes, or state why there is no foreground (ECU, top-down, a silhouette against the sun).
- The foreground is cropped, dark and specific: name the object and the frame edge it sits on. A tidy, fully
  visible foreground looks generated.
- Give the far background one job: usually the brightest, haziest area, often the light source or destination.
- One focus strategy: deep focus (size shows distance) or one soft foreground plane. Never an even blur on
  everything but the subject.
- Video: near planes move faster than far ones; a dark foreground sliding past a lit midground reads as depth.
  Keep the foreground object simple and solid so it doesn't morph.

**Subject and place**
- Size ratio in numbers for anything wider than a medium: "a tenth of the frame", "under 5% of the frame".
  Models enlarge people unless told.
- Angle as position and effect: "camera on the ground looking up, soles in the foreground", not just "low
  angle". Dutch tilt only on purpose.
- `subject.interaction` says where the light lands on the subject: which cheek, which hands, what colour.
- Gaze and travel point into open space or into depth; into the lens only for confrontation.

**Light**
- **One key, named.** Its source in the world, side of frame, height, hard or soft. `direction` always holds a
  side or position. Fill, rim and practicals are written relative to it; a second light gets a job and a source.
- **Cause, not pattern.** Write where the source is and how big. Never ask for a "Rembrandt triangle" or "blind
  stripes" without the source that casts them, or the model paints the pattern on.
- **Show or prove the source:** in frame, at the frame edge, or by a footprint (sun patch, pool on the table,
  beam in haze).
- **Name the dark.** Every card except high key and overcast says what falls into darkness.
- **Colour pairing.** Every practical carries its colour ("warm tungsten lamp", "cool blue phone light"); state
  the ambient colour. One temperature dominates; warm and cool split at the edge of the source's reach. Leave
  sources uncorrected. No global teal-and-orange grade instead of motivated colour.
- **Scene light plan.** Each scene has one anchor phrase for the sources fixed to the set ("north window on the
  left wall, one table lamp right of the bed, blue hour outside"). The director writes it in the shot list, the
  production designer copies it into the environment file's Light section, and the cards repeat it word for
  word. Across the 180-degree line the key flips side of frame, because the world
  has not moved.

**Not too perfect** (put the relevant ones in `light_look.finish`)
- Real blacks: deep, falling to black (or crushed), never milky grey or HDR. Slight underexposure beats catalogue exposure.
- Two or three named colours at most.
- Lived-in surfaces: scuffs, dust in the light, smudged glass.
- Natural skin on every face: "natural skin texture, visible pores, fine lines".
- Uneven atmosphere: patchy fog, one beam, lamp halos that shrink with distance.
- One asymmetric detail in a symmetrical frame.

## Vertical 9:16

- Subject low (bottom third, often against an edge), usually under 15% of frame height.
- Design the headroom: the upper 50-70% holds a textured surface, shadow or light, never blank. It is the
  caption space; keep it clear of platform UI zones (`presets.json` `safe_zone`).
- Build on vertical forms (doorways, alleys, stairwells, towers). Never pad a 16:9 idea.
- Rework: wide two-shots (stack in depth), low-horizon landscapes (figure low, sky takes the height), wide eye
  strips (one eye or a tight face).

## Two people

- OTS: the near shoulder is a dark, soft mass cropped by one edge; the far face is sharp, brighter, on the
  opposite third. A small shoulder reads as a calm standoff; a huge head filling a third reads as an attack.
- Eyeline just off-lens toward the near shoulder, never both at camera.
- Name what sits in the gap (cups, a divider, a counter). State sizes and planes for a depth-staged two-shot.

## Interviews

For sit-down interviews and podcasts, use the `"category": "interview"` entries in `rules/light_setups.json`.
The full rigs, small-kit versions, mistakes, prompt phrases and reference frames are in
`${CLAUDE_PLUGIN_ROOT}/docs/research/studio-interview-lighting-guide.md`.

**The rule under every setup:** one big soft key, close to the face, on the side the subject looks towards
(*short side*: the cheek nearest the lens stays in shadow). Black *negative fill* (a flag that takes light
away) does the shaping. The background is lit, or kept dark, on its own.

| Interview type | Setup | Key phrase |
|---|---|---|
| Emotional story, founder, doc | Documentary soft key, dark background | "large soft key on the short side, negative fill, background two stops under, one warm practical" |
| Corporate or charity testimonial | Classic three-point | "gridded soft key, low bounce fill, subtle high rim, backdrop lit separately" |
| Two-chair editorial, clean brand talk | High-key white studio | "soft overhead key per chair, white cyc a stop over the face" |
| Testimony, true crime, gravitas | Low-key black void | "one gridded soft key, no fill, black background, face falls off into shadow" |
| Podcast host, author, recurring set | Dressed set with practicals | "high soft key, two dimmed warm lamps beside the head, shelves in soft pools" |
| Tech, music, creator brand | Coloured background wash | "neutral key on the face, teal wash on the wall only, colour never on skin" |
| Brand doc, subjects with glasses | Window-style soft side light | "big diffusion frame 60-90 degrees to the side, black flag opposite" |
| Two to four people at a table | Podcast / multi-person | "matched soft key over each seat, background practicals, eyeline to the other person" |

Write "natural skin texture" on every face; never smoothing or a beauty glow. State the background in stops
against the face. Keep coloured light off the skin.

## Banned trigger words

Never write these; they invite an invisible softbox, plastic skin or a generic look:
"8k", "ultra detailed", "hyperdetailed", "hyperrealistic", "epic", "flawless", "perfect skin", "HDR",
"beautiful lighting", "cinematic lighting", "well lit", "bokeh background", and "studio lighting" outside
studio work. Replace each with the concrete thing you want (a named source, a texture, a soft named foreground).

## Checklist before handover

- [ ] Story intent maps to a named technique and setup; at most three techniques combined.
- [ ] Setup checked against its `do_not_use_when`.
- [ ] Far background, near background, placement and foreground filled (or the exception stated), each with a
      value word, following one depth pattern.
- [ ] Foreground is specific, cropped and names its frame edge.
- [ ] Subject size as a fraction of the frame for anything wider than a medium.
- [ ] Gaze or travel direction stated and pointing into space.
- [ ] One key named with its world source, side, height and hard or soft; fill stated as none or low.
- [ ] The source is in frame, at the frame edge, or proven by a footprint.
- [ ] Each practical carries its colour; the ambient colour is stated.
- [ ] What stays dark is stated (except high key and overcast).
- [ ] `subject.interaction` says where the light lands on the subject.
- [ ] Palette named in two or three colours.
- [ ] `light_look.finish` has at least two imperfection terms; skin texture wording on every face.
- [ ] No banned trigger words.
- [ ] The scene's anchor phrase repeated word for word; key side matches the previous shot, or flips correctly
      across the line.
- [ ] Video: one camera move with speed, or locked-off; parallax written; the light source stays fixed to the
      set, and any flicker is described on purpose.
- [ ] Vertical: subject in the lower third, headroom described as a surface, clear of UI zones.
