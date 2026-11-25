# Cinematic composition for shotcraft

This guide turns a private Cosmos study board into working rules for shotcraft. The board is [Cinematic composition: shotcraft study](https://www.cosmos.so/timmy111/cinematic-composition-shotcraft-study). It has 15 sub-boards, one per technique, with about 20 to 27 film frames each. Every frame was viewed and broken down into placement, lens, light, colour and depth. The lessons are written for the cinematographer agent, the production-designer agent and the prompt-craft skill. They map straight onto the six prompt-card layers (Intent, Subject, World, Camera, Light & Look, Time & Output) and the depth fields (`world.background_far`, `world.background_near`, `subject.placement`, `world.foreground`, `world.parallax`), plus `subject.interaction` and `light_look.finish`. One idea runs through every board: the frames that look like cinema are built in planes, give the environment real weight, and are never too clean.

## How to use this

- **Pick from the chooser first.** Start from the story intent of the shot (what the viewer should feel), not from a technique you like.
- **Combine two or three techniques at most.** Most strong frames use one geometry technique (thirds, symmetry, leading lines), one depth technique (layers, atmosphere, frame within a frame) and one light technique (silhouette, chiaroscuro, colour blocking).
- **Fill all four depth fields on every card.** Use the "Depth planes" block in each section as the template for `background_far`, `background_near`, `subject.placement` and `foreground`.
- **Copy prompt phrases word for word, then make them specific.** Swap in the real object, colour and frame edge for the shot.
- **Check the failure modes before handing over.** Each section lists what image and video models get wrong and the wording that fixes it.
- **Use the reference frames as a sanity check.** Open the Cosmos links when you're unsure what a technique should look like. Do not name living artists or copy film frames into prompts unless the brief allows it.
- **Vertical 9:16 work:** read the vertical section and the cross-cutting notes. Most of these techniques still work in a tall frame, but the subject moves lower and the headroom gets designed.

## Quick chooser

| Story intent / feeling | Technique(s) | Key prompt phrase |
|---|---|---|
| Place a character inside a world | Depth layers + atmosphere | "layered composition with distinct foreground, midground and background, haze increasing with distance" |
| Outsider, between two worlds | Frame within a frame (doorway) | "framed by a dark doorway, bright landscape beyond, subject small in frame" |
| Being watched, surveillance | Frame within a frame (lit window) + high angle | "seen through a lit window at night, dark brick facade around it" |
| Trapped, ruled by tradition or a system | Nested frames, symmetry, high angle | "nested doorways receding into depth, figure small in the farthest one" |
| Fate, isolation, a long road ahead | Leading lines and vanishing point | "lone small figure standing at the vanishing point, one-point perspective" |
| Order, power, ritual, uncanny, deadpan comedy | Symmetry and centre-punch | "subject dead centre, camera square-on to the back wall, symmetrical but lived-in" |
| Natural, unforced, looking somewhere | Rule of thirds, off-centre | "subject on the right third, looking into open space on the left" |
| Loneliness, awe, smallness | Negative space and scale | "extreme wide shot, figure occupies less than 5% of the frame" |
| Power, threat, hero, myth | Low angle | "camera on the ground looking up, ultra-wide lens, figure towering against sky" |
| Defeat, vulnerability, being judged | High angle / top-down | "direct overhead shot, tiny figure on empty asphalt" |
| Mystery, archetype, opening or ending | Silhouette against light | "backlit figure as a solid black silhouette, exposed for the sky" |
| Secrecy, menace, a moral choice | Chiaroscuro, pools of light | "single hard key light, no fill, 70 percent of the frame in deep black" |
| Two people: equals, rivals, lovers, strangers | OTS, two-shot, distance | "over-the-shoulder, foreground shoulder soft and dark, his eyeline just off-lens" |
| Peak emotion, decision, confrontation | Close-up and extreme close-up | "extreme close-up, cropped at forehead and mid-nose, hard side light" |
| Find a small subject fast, stylised world | Colour blocking | "limited two-colour palette, small figure in a red costume against gold leaves" |
| Mood, scale, mystery at night or in nature | Atmosphere (haze, rain, shafts) | "strong backlight through haze, figure in silhouette walking into fog" |
| Native vertical that feels like cinema | Vertical 9:16 framing | "small lone figure in the lower third, towering shadowed wall above" |
| Chase, arrival, journey, epic scale | Staging for movement | "action moving along the lens axis toward camera, large cropped foreground figure" |

---

## 1. Depth layers: foreground, midground, background

Sub-board: https://www.cosmos.so/timmy111/depth-layers-foreground-midground-background

**What it is.** The frame is built as several planes stacked away from the lens: something close to camera, the subject in the middle distance, and one or more environment layers behind. Size, focus, tone and atmosphere tell the planes apart, so a flat image reads as deep 3D space.

**When to use.**
- Placing a character inside a world, when the place matters as much as the person.
- Showing a relationship or power gap: one person close, another small and far.
- Tension: a foreground object or figure the subject faces or does not see.
- Ensembles and crowds, where receding rows give scale.
- Quiet domestic moments seen through doorways into far rooms.
- Over-the-shoulder and silhouette points of view that put us in a character's head.

**Visual rules.**
- Build three planes, often four: a foreground at the frame edge, a midground subject, a near background that places the story, and a far background lost in haze.
- The foreground hugs a frame edge or the bottom of frame and is cropped hard. It is almost never fully shown or centred.
- Lead the eye with a gap. The subject sits in the opening the foreground leaves (through a noose, between doorframes, between heads).
- Go dark to bright from front to back. Foreground darkest, often a silhouette. Subject gets the key or rim light. Background lightest and lowest in contrast.
- Atmosphere does the far planes. Each layer back is paler and greyer.
- Commit to one lens feel. Either wide-angle deep focus (everything sharp, size shows distance) or a medium lens with a soft foreground. Far figures can be under a tenth of frame height.
- Motivate light from behind or the side (window, fire, low sun), so the foreground falls to silhouette.
- Keep colour muted and narrow. Put a warm accent (fire, lamp) in one plane only.
- Interiors get depth from rooms in a row, each in a different light.

**Depth planes.**
- *Far background:* sky, mountain, sea, fogged treeline or far window. Palest, lowest contrast, usually the top third.
- *Near background:* readable set dressing that places the story (grave crosses, a car and a waiting figure, telegraph poles, a second room). Often holds a secondary figure.
- *Subject placement:* midground, 1/4 to 1/2 of frame height, on a third or in the gap, cleanest light and sharpest focus.
- *Foreground:* cropped hard at an edge (head and shoulder, tree trunk, leaves, doorframe, flowers and mud). Dark, 15 to 50% of the frame.

**Subject–environment.** The subject is embedded in the space, with environment both in front and behind. The foreground usually belongs to the subject's world (their comrades, the wall they hide behind). Seen through it, the subject reads as watched, trapped or small. Secondary figures deep in frame set up a relationship across distance.

**Prompt phrases.**
- "layered composition with distinct foreground, midground and background"
- "out-of-focus tree trunk in the foreground frame right, character in the midground, figure waiting deep in the forest behind"
- "silhouetted head and shoulder in the near foreground, action lit in the distance"
- "shot through a doorway into a far lit room, figure small in the far room"
- "atmospheric haze that grows with distance, background pale and low contrast"
- "dark foreground, bright background, backlit by window light"
- "deep focus wide-angle, everything sharp from front to back"

**AI failure modes and fixes.**
- *Portrait-mode look: crisp subject in front of a generic blur wall.* Name a specific foreground object and its frame edge, plus a specific element behind the subject.
- *Even fake bokeh on every plane, halo cut-outs around hair.* Pick deep focus or one soft foreground. Ask for optical falloff. Don't write "bokeh background".
- *Tidy, decorative foreground (centred flower, perfect branch).* "cropped hard by the frame edge", "dark silhouette", "filling the left third".
- *No atmosphere, or fog painted evenly everywhere.* "haze increasing with distance", far background "pale and washed out", foreground dark and contrasty.
- *Clean frontal HDR light, every plane equally exposed.* Light from behind (window, fire, low sun), foreground near black, muted palette, grain, lifted blacks.
- *Wrong scale or cloned crowds.* Give sizes ("distant figure a tenth of frame height"), ask for varied poses and irregular spacing.
- *Spotless sets.* Add mud, debris, scuffed walls, worn furniture.
- *Video: planes smear or the foreground morphs.* Slow lateral dolly or locked-off, state parallax, keep the foreground object simple and solid.

**Reference frames.**
- [Ran (1985), Kurosawa](https://www.cosmos.so/e/1078945468): seated retainers along the bottom, lord in the midground, hazy mountain behind.
- [Children of Men (2006), Lubezki](https://www.cosmos.so/e/621244672): soft trunk on the right third, face peeking past it, car and waiting figure in the pines.
- [Stalker (1979), Tarkovsky](https://www.cosmos.so/e/920733567): flowers and mud, three men, telegraph poles dissolving into fog.
- [Western, likely The Good, the Bad and the Ugly](https://www.cosmos.so/e/1077623115): the noose loop frames the man, grave crosses behind.
- [Uncredited war film](https://www.cosmos.so/e/1255777651): black profile face fills the left half, soldiers in the surf, pale sea behind.
- [Uncredited colour interior](https://www.cosmos.so/e/144395888): warm near room, green-lit far doorway with a second figure.
- [The Spirit of the Beehive (1973)](https://www.cosmos.so/e/87867870): doorway inside doorway to a glowing far window.
- [Citizen Kane (1941), Toland](https://www.cosmos.so/e/1081400426): deep focus, low angle, crowd heads along the bottom.

---

## 2. Frame within a frame

Sub-board: https://www.cosmos.so/timmy111/frame-within-a-frame

**What it is.** A real object in the set (doorway, window, mirror, lattice, corridor end) draws a second, smaller rectangle inside the frame and puts the subject in it. The inner frame isolates the subject and says something about them: outsider, trapped, watched, shut away. On the board it is always physical architecture or car parts, never a graphic border.

**When to use.**
- An outsider or someone between two worlds (doorway to the outside).
- Voyeurism or surveillance (lit windows at night).
- Confinement, tradition, social order (nested doors, lattices, screens).
- Isolation inside a group or city (grid of windows).
- Introspection in transit (rear-view mirror).
- Arrivals and departures at a threshold.
- Interview or brand content that needs context instead of a flat backdrop.

**Visual rules.**
- The inner frame is a real opening in the set.
- Brightness contrast makes the frame. A dark interior around a bright exterior, or a lit window in a black night facade. Frame edges sit 2 to 4 stops off the opening.
- Dark frame, bright world: the subject goes to silhouette, rim light only.
- Lit window at night: a warm practical lamp in the room lights the subject. The wall around falls to black.
- Placement is often central and symmetrical. Asymmetric versions push the frame to one side and leave negative space.
- Frames can nest, each layer smaller and usually brighter.
- The subject is small, about 1/6 to 1/3 of frame height. Architecture dominates.
- Normal to slightly long lens look (35 to 50mm), straight verticals, locked-off level camera.
- Focus usually holds the frame edge and subject together.
- The frame material is worn: weathered wood, peeling paint, smeared or fogged glass.

**Depth planes.**
- *Far background:* a bright exterior that makes the opening a light source (mesas, ranch house, garden, skyline). Can be motion-blurred.
- *Near background:* the space right behind the subject (a room with a lamp, the next doorway in a nested set).
- *Subject placement:* just inside or beyond the opening, small, often silhouetted or practical-lit.
- *Foreground:* the framing architecture (jambs, porch beam, barn walls, sash, lattice, mirror housing). Dark, often 50 to 70% of the image.

**Subject–environment.** The environment holds the subject and carries the story. A doorway marks someone who won't cross the threshold. A window turns a private life into a screen for a hidden watcher. Nested screens make the house an orderly cage. The subject is almost never bigger than the architecture around them.

**Prompt phrases.**
- "framed by a dark doorway, bright landscape beyond"
- "silhouetted figure standing in an open barn door"
- "seen through a lit window at night, dark brick facade around it, warm table lamp the only light"
- "nested doorways receding into depth, figure small in the farthest one"
- "rear-view mirror reflection of the driver's eyes, landscape blurred beyond"
- "weathered wood frame, peeling paint, smudged glass"
- "normal lens, straight verticals, locked-off level camera"

**AI failure modes and fixes.**
- *A decorative border or picture frame instead of architecture.* Name the physical opening and say where the camera stands (inside looking out, outside looking in).
- *Subject too big, filling the doorway.* "subject small in frame, architecture dominant", "dark walls fill both sides of the frame".
- *Even lighting kills the frame.* "dark interior, bright exterior opening, high contrast, no fill light".
- *Fresh wood, spotless glass, perfect symmetry.* Weathered grain, chipped paint, fogged glass, dust in the light, grain, imperfect symmetry.
- *Wide-lens lean on the jambs.* "normal lens, straight verticals".
- *Opening blown to white or foreground mushed.* Deep focus and a readable exterior ("mesas visible on the horizon").
- *Nested frames turn into tiled nonsense arches.* Give count and order: "two open doorways in line, a third lit doorway at the far end".
- *Video: camera drifts through the doorway.* "static camera, subject moves within the frame".
- *Impossible mirrors.* "only her eyes visible in the rear-view mirror, face itself out of frame, slight dirt on the glass".

**Reference frames.**
- [The Searchers (1956), Ford](https://www.cosmos.so/e/296853068): dark porch frames Wayne against the orange desert.
- [The Power of the Dog (2021), Campion](https://www.cosmos.so/e/737453429): black barn walls, silhouette centred in the opening.
- [Ozu, uncaptioned](https://www.cosmos.so/e/1428359139): shoji panel, open screen, garden fence nested in depth.
- [Raise the Red Lantern (1991), Zhang Yimou](https://www.cosmos.so/e/1343858177): symmetrical lattice doors, tiny figures in the innermost frame.
- [Rear Window (1954), Hitchcock](https://www.cosmos.so/e/1837215765): lit window in a black brick facade.
- [Playtime (1967), Tati](https://www.cosmos.so/e/1680062108): a facade of lit window cells, each a small scene.
- [Land of Plenty (2004), Wenders](https://www.cosmos.so/e/732986119): rear-view mirror eyes, off-centre, motion-blurred desert.
- [Ford western, uncaptioned](https://www.cosmos.so/e/1666531661): cropped figure in the foreground, corridor, silhouette in the far doorway.

---

## 3. Leading lines and vanishing point

Sub-board: https://www.cosmos.so/timmy111/leading-lines-and-vanishing-point

**What it is.** Straight edges in the set (roads, rails, corridor walls, ceiling lights, floor tiles, fences, shelves) recede and meet at a vanishing point, and the subject stands on or right next to that point. Every line carries the eye to the person, so a tiny figure still reads as the subject.

**When to use.**
- Isolation, loneliness or fate: a small figure at the end of a corridor, road or track.
- Journeys, pursuit, inevitability.
- Institutional, uncanny or bureaucratic spaces (offices, hotels, archives).
- Formal, storybook tone with nested doorframes.
- Wide establishing shots where the subject must still be unmistakable.
- Walk-away or walk-toward shots along the lines.

**Visual rules.**
- Put the vanishing point on the subject, usually in the centre third.
- Camera at about the subject's eye line, dead level, square-on. Only the receding lines are diagonal.
- Stack several line families: floor edges, wall/ceiling joins, ceiling lights, door rows, rail pairs.
- Subject small, about 1/10 to 1/4 of frame height.
- Moderate wide lens (24 to 35mm look), deep focus. Long-lens road shots compress instead, but the lines still converge. No shallow focus on the environment.
- Light reinforces the lines: a lit end (window, glowing doorway), or rows of lights as lines themselves.
- One dominant hue fills the receding surfaces (red, amber, sepia, mint). The subject contrasts in value or colour.
- Symmetry is optional. Strict gives formal or uncanny. An off-centre vanishing point beside the subject feels more natural.

**Depth planes.**
- *Far background:* the vanishing point itself, often a lit window, doorway, horizon or tree line. Brightest or most contrasting area.
- *Near background:* repeated units (doors, shelves, fence posts, light fixtures) shrinking at a regular rhythm.
- *Subject placement:* small, on the path at or just in front of the vanishing point, near the horizon line.
- *Foreground:* the widest part of the lines (road, rail ties, floor, the nearest doorframe), in focus, lower third to half of the frame.

**Subject–environment.** The environment dominates but is built to point at the subject. The figure is usually alone or one of a pair, often facing into the depth or walking away. The frame reads as "this person, in this vast, ordered world".

**Prompt phrases.**
- "one-point perspective, symmetrical corridor converging to a vanishing point"
- "lone small figure standing exactly at the vanishing point"
- "walls, ceiling lights and doors receding toward the subject"
- "straight road running to the horizon, car on the road"
- "bright lit doorway at the end of a dark corridor"
- "eye-level camera, perfectly level horizon, deep focus"
- "monochrome red hallway, figure in white at the end"
- "worn floor, scuffed walls, uneven real-world surfaces"

**AI failure modes and fixes.**
- *Lines converge on empty frame.* "lines converge on the figure", "figure standing exactly at the vanishing point".
- *Subject too large.* "small distant figure, wide shot, a tenth of the frame".
- *Bent walls, mixed vanishing points, wrong-size doors.* "strict one-point perspective, straight parallel lines, level camera". Reject warped geometry.
- *Clone doors, glossy plastic walls, even light.* 35mm grain, practical sources, worn carpet, scuffed paint, dust.
- *Dutch tilt or fisheye "for drama".* "eye-level, no tilt, no fisheye, moderate wide lens".
- *Shallow focus blurs the lines.* "deep focus, foreground and background both sharp".
- *Clutter competing with the lines.* "empty corridor, single figure, minimal set".
- *Default teal-orange.* Name one space colour and one subject colour.
- *Video: wobbling vanishing point, sliding figure.* Locked-off, or a slow dolly on the corridor axis, "figure walks along the centre line".

**Reference frames.**
- [Queer (2024), Guadagnino](https://www.cosmos.so/e/1936374297): red walls and lamps meet on a white-suited figure.
- [Severance (TV)](https://www.cosmos.so/e/143004849): black corridor, glowing doorway with two small figures.
- [O Brother, Where Art Thou? (2000)](https://www.cosmos.so/e/1392343267): rails and furrows converge on the handcar.
- [Vanishing Point (1971)](https://www.cosmos.so/e/195992444): desert highway to the horizon.
- [Blade Runner 2049 (2017)](https://www.cosmos.so/e/1205092155): amber archive stacks, two figures on the centre line.
- [The Wonderful Story of Henry Sugar (2023), Anderson](https://www.cosmos.so/e/1981339420): nested doorframes, orange figure on mint.
- [La Roue (1923), Gance](https://www.cosmos.so/e/937054543): rails inside an iris toward a walking man.
- [North by Northwest (1959), Hitchcock](https://www.cosmos.so/e/1090293782): off-centre vanishing point beside Cary Grant.

---

## 4. Symmetry and centre-punch

Sub-board: https://www.cosmos.so/timmy111/symmetry-and-centre-punch

**What it is.** The subject sits at the exact horizontal centre, usually on the vanishing point, and the set is mirrored left and right around them. The camera faces the subject square-on. There is no relief at the sides, so the eye is pushed to the centre. Depending on light, colour and who stands there, it reads as order, power, ritual, comedy or dread.

**When to use.**
- Unease and the uncanny: a too-perfect world where something is wrong.
- Power and status: a subject enthroned square to camera.
- Ritual, sacred or contemplative moments.
- Deadpan comedy and storybook formality.
- Isolation: a small figure at the vanishing point of a vast space.
- Confrontations, arrivals and POV reveals (head-on to the audience).

**Visual rules.**
- Subject's centre line on the frame's centre line. Head on or just above the horizontal axis.
- Lens axis perpendicular to the back wall. No tilt, no yaw. Camera at eye or chest height.
- Wide to normal (18 to 35mm) for corridors and rooms. Longer lens for flat frontal planes (a facade, a lighthouse).
- Mirrored architecture does the framing: twin stairs, columns, arches, pews, hedges.
- Matched pairs flank the centre and reinforce the axis.
- Light is often frontal or overhead and even, or the light source is the centre (a backlit window).
- Restricted palette of 2 or 3 named colours.
- Keep real asymmetries: an exit sign on one wall, a door on one side only, grain, falloff. Strong symmetry, not mathematical mirroring.

**Depth planes.**
- *Far background:* a bright vanishing point at dead centre (end wall, window, doorway).
- *Near background:* mirrored side walls, columns, stairs or tiles converging evenly.
- *Subject placement:* on the centre line at or just in front of the vanishing point. Small in wides, large in mediums.
- *Foreground:* empty floor or carpet runner leading in, or a centred element (back of a head, a railing, a peephole vignette).

**Subject–environment.** The architecture converges on the subject and pins them in place. Depending on intent they are enthroned, trapped or swallowed. They usually face camera or walk straight away along the axis. A subject who stares into the lens turns the symmetry into a challenge to the viewer.

**Prompt phrases.**
- "perfectly symmetrical one-point perspective composition, subject dead centre"
- "camera square-on to the back wall, eye-level, locked-off"
- "mirrored architecture on both sides, twin staircases and columns"
- "matched pair standing side by side on the centre line"
- "bright window glowing behind the subject at centre"
- "symmetrical but lived-in, one exit sign on the left wall only"
- "rectilinear 24mm lens, straight verticals"

**AI failure modes and fixes.**
- *Pixel-perfect mirroring, cloned props and faces.* "symmetrical but lived-in" plus one named asymmetric detail.
- *Subject drifts off-centre, camera yaws.* "subject on the exact vertical centre line, vanishing point directly behind the head, camera perpendicular to the back wall, no tilt".
- *Model defaults to the rule of thirds.* Put "centred composition, dead centre" first in the prompt.
- *Sterile 3D-render corridors.* 35mm grain, practical falloff, halation, worn textures.
- *Fisheye bending verticals.* "rectilinear lens, straight verticals" (fisheye only for a deliberate peephole POV).
- *Centred portrait on a bokeh wall.* "deep focus, entire environment sharp", "small figure in a vast space".
- *Video: drift, orbit or handheld.* "locked-off static tripod" or "slow push-in exactly on the centre axis".
- *Busy random colour.* Limit to 2 or 3 named colours.

**Reference frames.**
- [The Shining (1980), Kubrick: corridor](https://www.cosmos.so/e/86823579): Danny's head in the foreground, twins at the vanishing point, EXIT sign asymmetry.
- [The Shining (1980), Kubrick: twins](https://www.cosmos.so/e/1181491767): matched pair staring into the lens.
- [2001: A Space Odyssey (1968)](https://www.cosmos.so/e/2002402753): astronaut at the end of a white octagonal corridor.
- [The Grand Budapest Hotel (2014)](https://www.cosmos.so/e/178936299): twin stairs and columns frame the concierge desk.
- [The Holy Mountain (1973)](https://www.cosmos.so/e/771733874): robed figure in a tiled chamber, an attendant each side.
- [Nostalghia (1983)](https://www.cosmos.so/e/22905910): three arches mirrored in a pool.
- [The Godfather Part II (1974)](https://www.cosmos.so/e/1942048166): Michael enthroned square to camera.
- [Blade Runner 2049 (2017)](https://www.cosmos.so/e/1181363837): lone figure on the axis of a golden stepped tunnel.

---

## 5. Rule of thirds and off-centre placement

Sub-board: https://www.cosmos.so/timmy111/rule-of-thirds-and-off-centre-placement

**What it is.** The subject and the horizon sit on or near the lines that split the frame into thirds, not in the centre. The empty side is used on purpose as looking room, landscape or negative space, and it balances the subject's weight. Two common forms: wide landscapes with a small figure on a vertical third and a low horizon, and tight interiors with the face pushed hard to one side.

**When to use.**
- Establishing shots where a small figure should feel alone or dwarfed.
- Character moments with looking room, so we feel where they're headed.
- Loneliness or longing: face pushed to one third, the other side empty or deep.
- Tension: subject cornered, the rest filled with a dark wall or door.
- Wide two-shots that balance two weights.
- Any time centring would feel static or like a passport photo.

**Visual rules.**
- Subject at about 30 to 40% or 60 to 70% across, never 50%. In wides the figure can be 3 to 10% of frame height.
- Horizon on the lower third (sky is the story) or upper third (ground is the story). Never through the middle.
- The open side sits in front of the subject's gaze or path.
- The empty side holds a counterweight (fog bank, a tree, a break in the clouds).
- Close-ups: face on one third, depth or soft street on the other.
- Short-siding (subject crowded into a corner under a heavy foreground mass) creates unease.
- Landscapes: 24 to 40mm look, deep focus. Telephoto flattens a plain. Interiors: 50 to 85mm, the open side in soft focus.
- Natural low-angle or overcast light, dusk and magic hour. Interiors use practicals and let the empty side go dark.
- Restrained colour. The empty area is the quietest, least saturated part of frame.

**Depth planes.**
- *Far background:* sky and mountains, often the top half to two-thirds. In close-ups, a deep soft street or corridor on the open side, or nothing (a flat wall).
- *Near background:* plain, field or desert running to a horizon on the lower third; or a textured wall right behind a face.
- *Subject placement:* on a vertical third, often under 10% of frame height in wides.
- *Foreground:* a blurred or silhouetted element at one edge (grass blades, a cropped shoulder, scrub). In tense interiors, a dark doorframe filling most of the frame.

**Subject–environment.** The environment is a co-subject. In wides, land and sky outweigh the person about 90 to 10, and that imbalance is the emotion. Gaze and travel point into the open space. In close shots the environment is a wall pressing in or a street opening away, and it reflects the character's state.

**Prompt phrases.**
- "subject on the right third, looking into open space on the left"
- "horizon on the lower third, vast sky fills two-thirds of the frame"
- "lone tree on the left third, distant figure right of centre"
- "face pushed to the frame edge, deep soft-focus street behind on the other side"
- "subject cornered in the lower right, heavy dark foreground door frame"
- "out-of-focus grass blades in the foreground"
- "magic hour backlight, figures in near silhouette against a pale sky"

**AI failure modes and fixes.**
- *Snaps to dead centre.* Name the side and third and what fills the empty side. Use a layout or depth guide when the model supports it.
- *Horizon through the middle.* "horizon line on the lower third", "low camera height".
- *Subject too big.* "tiny distant figure, extreme wide shot", give a size cue ("smaller than the tree").
- *Clutter in the negative space (birds, extra people, god rays).* "empty sky", "bare plain", and describe its texture so it's quiet but not blank.
- *HDR sky, plastic skin, glowing rim light.* 35mm still, soft natural light, grain, halation, muted palette. Avoid "epic", "8k", "hyperdetailed".
- *No lead room.* State gaze direction: "facing left, into the open space".
- *Everything sharp in a close-up.* "shallow depth of field, background soft on the open side".
- *Video recentres the subject.* "locked-off" or "slow pan that keeps the subject on the right third".

**Reference frames.**
- [No Country for Old Men (2007), Deakins](https://www.cosmos.so/e/562726048): Llewelyn right of centre facing a desert basin.
- [Arrival (2016), Bradford Young](https://www.cosmos.so/e/1256885791): shell on the left third, fog rolling in on the right.
- [Pride & Prejudice (2005)](https://www.cosmos.so/e/460379949): tree left third, tiny figure, storm sky.
- [In the Mood for Love (2000): Tony Leung](https://www.cosmos.so/e/1459004584): face left third, deep night street right.
- [In the Mood for Love (2000): two leads](https://www.cosmos.so/e/1361108190): both crowded right, wooden wall left.
- [Days of Heaven (1978), Almendros](https://www.cosmos.so/e/1788274603): house left, horizon low, figures balance right.
- [Paris, Texas (1984), Müller](https://www.cosmos.so/e/2032072003): red cap, low horizon, big sky.
- [Mr. Robot (TV)](https://www.cosmos.so/e/1561455965): subjects squeezed bottom right through a door gap.

---

## 6. Negative space and scale

Sub-board: https://www.cosmos.so/timmy111/negative-space-and-scale

**What it is.** The person takes only about 1 to 5% of the frame. The rest is open, low-detail space: sky, fog, snow, a hillside, a floor, darkness. The empty area is as much the subject as the person. The viewer reads loneliness, awe or alienation from how much space surrounds the figure.

**When to use.**
- Openings and establishing shots that place a character in a bigger world.
- Loneliness, grief, exile, searching, the end of a journey.
- Awe and the sublime: mountains, deserts, storms, myth.
- Modern alienation: empty plazas, brutalist interiors, a lit room in darkness.
- Breathers between dense scenes; title or end frames that need clean space for type.
- Quiet brand films that should feel cinematic, not busy.

**Visual rules.**
- Figure about 2 to 8% of frame height (up to 25% only when the field around it is a big blank plane).
- Off-centre on a thirds line or on the edge between two tonal masses.
- Horizon low (sky fills 60 to 90%) or high (ground fills most of the frame). Never in the middle.
- One dominant field of tone and texture (grey fog, orange dust, white snow, black void). The figure contrasts with it.
- Usually a long lens from far away, which flattens the figure against a wall of landscape. Sometimes a wide lens straight down.
- Usually only 2 or 3 planes.
- Atmosphere does the scaling: haze makes the background read as huge and far.
- Calibrate scale with something enormous beside the figure (a tree, cliff, giant, church facade).
- Soft, diffused light. No hard key on the figure. Mostly a silhouette or flat mid-tone.
- Nearly monochrome per frame. Any accent colour is tiny and sits on the figure.
- Wide 2.39:1 frames spend their extra width on emptiness.

**Depth planes.**
- *Far background:* a large atmospheric mass (mountain wall, fog bank, storm sky, black void), soft, 50 to 90% of the frame.
- *Near background:* a broad low-detail ground plane (snow, grass, dust, tiles, piazza).
- *Subject placement:* one small crisp silhouette, 2 to 8% of height, off-centre or on the horizon edge.
- *Foreground:* usually empty. If used, a dark soft mass along the bottom edge (rock, hay rick, bushes, wall).

**Subject–environment.** The environment dominates. The figure is a punctuation mark in a sentence written by landscape or architecture. Three relationships recur: sublime nature, mythic comparison (giants, cliffs), and architectural alienation. The figure usually faces away or is too small to show expression, so posture and position carry the emotion.

**Prompt phrases.**
- "extreme wide shot, tiny lone figure in a vast landscape"
- "figure occupies less than 5% of the frame"
- "small silhouette on the lower third, off-centre"
- "low horizon, sky fills most of the frame"
- "long telephoto lens compression from far away, distant mountain wall"
- "thick fog and atmospheric haze, overcast diffused light, muted nearly monochrome palette"
- "single tree beside the figure for scale"
- "small lit room floating in black darkness, tiny figure inside"

**AI failure modes and fixes.**
- *Figure grows into a mid-shot hero.* State the ratio and repeat it. Describe the landscape first and the person last.
- *Empty space fills up (birds, rocks, flares, rays).* "empty", "minimal", "single figure only", "plain overcast sky". Keep the prompt short.
- *Dead-centre poster with a middle horizon.* Name placement: "horizon at the bottom fifth of frame".
- *Hyper-sharp distance, HDR, saturated teal-orange.* Grain, soft distance, haze, muted colour, slightly underexposed. Avoid "8k", "epic", "cinematic lighting".
- *Mangled tiny silhouette.* Clean dark shape on a light field, simple pose (standing, walking away), plain coat.
- *Broken scale cues.* Put them "on the same ridge" or "beside the figure"; push the far background back with haze.
- *Video: push-in destroys scale, figure slides.* "locked-off static camera" or very slow lateral drift, slow walk, short clip.

**Reference frames.**
- [Nostos: The Return (1989)](https://www.cosmos.so/e/1259543831): speck of a figure under a mountain wall of cloud.
- [Pride & Prejudice (2005)](https://www.cosmos.so/e/460379949): thin strip of land, near-invisible figure, huge sky.
- [The Green Knight (2021)](https://www.cosmos.so/e/1207403938): rider on a rock, giants in the fog.
- [Uncaptioned snow slope](https://www.cosmos.so/e/879465358): pinprick figure where white snow meets black void.
- [L'Avventura (1960), Antonioni](https://www.cosmos.so/e/378490963): tiny figures in a deserted piazza.
- [Blade Runner 2049 (2017): dead tree](https://www.cosmos.so/e/1174112907): K small beside a bleached tree under flat grey sky.
- [Blade Runner 2049 (2017): snowy steps](https://www.cosmos.so/e/211988091): top-down figure on white steps.
- [Uncaptioned interior](https://www.cosmos.so/e/1042380017): small lit room in total black.

---

## 7. Low and high angles (power and vulnerability)

Sub-board: https://www.cosmos.so/timmy111/low-and-high-angles-power-and-vulnerability

**What it is.** Camera height and tilt change how strong the subject looks. Low angle (camera below the eyes looking up): the figure towers and cuts into the sky. That reads as power, threat, ego or myth. High angle (camera above looking down): the figure shrinks and the ground swallows them. That reads as defeat, isolation, being trapped or watched. On the board, high angles outnumber low about 2 to 1, and most are near-vertical top-down shots, not gentle tilts.

**When to use.**
- Introducing a dominant, threatening or heroic character; a power shift (low).
- Ego or politics with a symbol of power behind the speaker (low).
- Triumph and release in music or fashion (worm's-eye with sky and flare).
- Defeat, a beating, a collapse (high).
- Isolation: a lone figure in a car park, on steps (bird's-eye).
- Pursuit or surveillance down stairwells and alleys (high, with a foreground railing).
- A person overwhelmed by a city (low, looking past them at towers).
- Confrontations cut between the two angles.

**Visual rules.**
- *Low:* camera at the feet or ground, tilted up 30 to 80 degrees. Subject 50 to 80% of height, head against open sky.
- *Low lens:* ultra-wide (14 to 24mm) close to the body. Near limbs grow, the head shrinks. That forced perspective sells the size.
- *Low in a city:* verticals lean in and crown the figure.
- *Gentle low:* horizon in the bottom quarter, figure backlit against sky, no distortion.
- *High:* camera far above, often near-vertical. Subject 5 to 15% of height, off-centre. No horizon. Ground texture is everything else.
- *High structure:* parking lines, stair treads, a building edge or a stairwell spiral fence the subject in.
- *High voyeur:* shoot down an alley past a dark, soft railing at the frame edge.
- *Overhead close-up:* face on the floor, filling the frame.
- Pose matches the angle: standing, striding, reaching for low; lying, slumped, looking up for high.
- Low-angle light: bright sky behind, exposed for the sky, faces dark. High-angle light: dusk, blue hour, sodium, practicals pooling on the ground, long shadows.
- Always gritty: litter, cracks, snow, grain.

**Depth planes.**
- *Low angle:* far background open sky; near background converging buildings, trees or a giant symbol; subject's body in steep perspective; foreground a huge soft near limb or object (shoe sole, hand, fence post).
- *High angle:* no far background (no horizon); the ground plane is the backdrop; small subject lies on it; a dark soft edge (railing, ledge, fabric) at one side as foreground.

**Subject–environment.** Low angle: the environment crowns and serves the subject (unless the camera looks past them at towers, then the city wins). High angle: the environment dominates and judges. The more empty ground around the subject, the more vulnerable they read.

**Prompt phrases.**
- "extreme low angle worm's-eye view, camera on the ground looking up"
- "ultra-wide 16mm lens close to the subject, forced perspective, foot large in foreground"
- "figure towering against open sky, buildings converging toward the top of frame"
- "direct overhead top-down shot, camera straight above"
- "tiny lone figure on empty asphalt, parking lines framing him, drone height"
- "high angle down a narrow alley from a fire escape, out-of-focus railing in foreground"
- "bird's-eye view, ground fills the whole frame, no horizon"

**AI failure modes and fixes.**
- *Timid angle (eye level or 15 degrees).* Describe the physical camera position and its visible effect ("soles of shoes in foreground", "no horizon, only asphalt").
- *Low angle with a normal lens, no towering.* "ultra-wide 14 to 18mm inches from the subject, exaggerated forced perspective, converging verticals".
- *Subject too big in high angles.* "subject a tenth of the frame, surrounded by empty ground".
- *Broken foreshortening, faces twisted toward camera.* Choose poses that read from the angle; accept the back or top of the head.
- *Spotless asphalt, HDR, everything sharp.* Grain, muted grade, litter and cracks, soft foreground edge.
- *Stock-drone symmetry.* Subject off-centre, tilt a few degrees off true vertical, add an imperfect foreground edge.
- *Flat generic light in high angles.* Name it: blue-hour dusk, sodium streetlight pooling, long shadow across the ground.
- *Video drifts back to eye level or orbits.* "static locked-off top-down camera" or a slow vertical crane that stays top-down; short clips.

**Reference frames.**
- [Uncredited worm's-eye](https://www.cosmos.so/e/699721079): soft shoe sole in front, figure between leaning towers.
- [Citizen Kane (1941)](https://www.cosmos.so/e/1081400426): low on Kane at the podium, giant portrait behind.
- [Young Mr Lincoln (1939), Ford](https://www.cosmos.so/e/1443175055): gentle low, silhouette against storm clouds.
- [Joker (2019)](https://www.cosmos.so/e/1617798706): high down a grimy alley past fire-escape railings.
- [Blade Runner 2049 (2017)](https://www.cosmos.so/e/211988091): top-down on K on snowy steps.
- [Uncredited drone shot](https://www.cosmos.so/e/1793272460): lone man looking up between parking lines.
- [Mr. Robot (TV)](https://www.cosmos.so/e/1500508385): straight down a red spiral stairwell.
- [Tokyo Fist (1995)](https://www.cosmos.so/e/422970433): low past a face up at towering apartment blocks.

---

## 8. Silhouette and shape against light

Sub-board: https://www.cosmos.so/timmy111/silhouette-and-shape-against-light

**What it is.** The exposure is set for the bright background (sky, sun disc, window, light-wall, fog), so the subject drops to a near-solid black shape. Detail gives way to outline, so pose, profile and props tell the story. The light is always behind the subject, and the outline sits on the brightest, cleanest part of the background.

**When to use.**
- Openings and endings: walking into or out of a sunset.
- Hiding identity, building mystery or menace (a figure in a doorway).
- Turning people into archetypes or myth; showing a journey.
- World-building by shape (a camp, skyline or convoy against dusk smoke).
- Introspective interior beats at a bright window.
- Poster-style hero moments in a giant sun disc.
- Transitions where detail would distract.

**Visual rules.**
- Expose for the background. Subject at or near pure black, little or no fill. Edge detail only where haze wraps the light.
- Put the outline on the brightest part of the frame. Nothing dark overlaps it.
- The pose must read in outline: profiles, arms away from the body, props held out, legs apart.
- Low horizon. Ground is a solid black band, usually the bottom 15 to 30%.
- Long lens for a huge sun behind a tiny figure (sun 3 to 6 times the figure's height). Normal lens for interior silhouettes at a third to half of frame height.
- Figure on the centre line (sun-disc shots) or on a third against a window mullion or door edge.
- Groups read as a frieze: spaced apart along the horizon, outlines never merging.
- Colour lives in the sky (warm magic hour, cool dusk) or in high-key black and white. Small warm practicals in the black band add life.
- Real texture: grain, halation, uneven gradients, slightly lifted or crushed blacks.

**Depth planes.**
- *Far background:* the light source itself (sky gradient, sun disc, glowing haze, bright window). Brightest, smoothest, 50 to 80% of frame.
- *Near background:* optional flat black cut-outs on the horizon (skyline, trees, a camp, mullions).
- *Subject placement:* the black silhouette on the brightest patch, outline clear. Tiny in wides, a third to half of height in interiors.
- *Foreground:* solid black ground band, grass, door edge or bars, often the bottom 15 to 30% or the sides. Haze between planes adds separation.

**Subject–environment.** The environment supplies the light and the subject is the shape cut out of it. The setting is reduced to a few graphic planes, so the figure reads as an archetype. Scale carries the emotion: tiny against a vast sun reads as destiny or ending; a large close silhouette at a window reads as mystery or inner thought.

**Prompt phrases.**
- "backlit figure as a solid black silhouette, exposed for the sky"
- "lone figure standing on a low dark horizon"
- "huge setting sun disc behind a tiny distant figure, long telephoto lens"
- "figure in a doorway against a bright overexposed window"
- "clean readable outline, profile view, arm raised away from the body"
- "three soldiers in single file along a backlit ridge, spaced apart"
- "solid black ground band filling the lower third, small warm campfires glowing in it"

**AI failure modes and fixes.**
- *Fill light creeps in.* "subject in complete shadow, no fill light, face unreadable".
- *Glowing halo or neon rim around the whole figure.* "hard clean edge, no rim light" (unless haze is meant to wrap the edge).
- *Blob poses.* Profile or three-quarter back, limbs clear of the torso, prop held out.
- *Merged outlines.* "figures spaced apart, outline against clear sky, head above the horizon line".
- *Wrong sun scale.* "extreme telephoto, giant sun disc filling half the frame, tiny distant figure".
- *Wallpaper sunset (perfect gradient, vector sun).* Grain, halation, haze, streaky uneven clouds, soft sun edge in heat shimmer, muted palette, a 1970s film look.
- *Invented detail in the black.* "solid black ground band, crushed blacks".
- *Video: exposure lifts mid-shot, edges boil.* Locked exposure, slow or static camera, one-direction walk.

**Reference frames.**
- [Days of Heaven (1978)](https://www.cosmos.so/e/420751062): lone cut-out on a magic-hour sky.
- [THX 1138 (1971)](https://www.cosmos.so/e/1223867715): tiny figure in a giant telephoto sun.
- [Tommy (1975)](https://www.cosmos.so/e/1710241314): centred figure on a crest inside a yellow sun.
- [Skyfall (2012), Deakins](https://www.cosmos.so/e/1446772944): doorway silhouette against blue sky, gun barrel outline.
- [Atonement (2007)](https://www.cosmos.so/e/881222242): three soldiers spaced along a hazy field.
- [The Return of the Prodigal Son (1976)](https://www.cosmos.so/e/1925447792): gesturing arm clear of the torso.
- [Mad Max 2 (1981)](https://www.cosmos.so/e/1479325927): a camp as a jagged frieze, fires in the black.
- [Uncaptioned corridor](https://www.cosmos.so/e/831054746): small figure against a glowing light-wall.

---

## 9. Chiaroscuro and pools of light

Sub-board: https://www.cosmos.so/timmy111/chiaroscuro-and-pools-of-light

**What it is.** Chiaroscuro means strong light-and-dark contrast. The frame is built from darkness first. One hard, motivated source (top light, window, blinds, candle, lamp, tunnel exit) cuts a single island of light out of a mostly black frame, often 60 to 85% near black. The subject is inside the pool or cut out against it. The shape of the light becomes part of the composition.

**When to use.**
- Isolation, secrecy, moral ambiguity: interrogation, confession, a choice made alone.
- Noir, crime, thriller, period drama; menace and tension.
- Intimate night scenes lit by a candle, lamp or screen.
- Making a plain location look rich: hide everything but one dressed pool.
- Product hero moments against black.
- Moving toward a light (corridor to exit) for hope or escape.

**Visual rules.**
- One key, no fill. The shadow side goes to true black. Half-faces, or a slash of light across the eyes.
- The pool sits off-centre. The dark around it is negative space.
- Shape the source so it shows a pattern: blind bars, window arcs, slats, a round floor pool.
- Treat shadow as a second subject: a cast shadow bigger than the actor.
- The inverse move works too: a solid black figure against a bright window or wall.
- Depth comes from alternating dark and light bands, not overall exposure.
- Normal to slightly long lens (35 to 75mm look), eye level or slightly high looking into the pool.
- Haze only inside the beam, to show the shaft.
- Monochrome with a hot white pool, or one warm practical colour against black or teal-black. Rich blacks, never grey.
- Practicals in frame, so we see where the light comes from.

**Depth planes.**
- *Far background:* black, or one bright note (tunnel exit, window behind a silhouette).
- *Near background:* a wall or floor catching the pattern (blind bars, window arcs, a cast shadow).
- *Subject placement:* inside the pool or on its edge, often on a third, shadow side lost to black.
- *Foreground:* often a dark soft shape that frames or overlaps the subject (back of a head, chair back, a dark table).

**Subject–environment.** The light creates the environment. The set exists only where light lands; the rest is implied by darkness. The subject is isolated, trapped by bars of light or dwarfed by their own shadow. Often they face away or sit in profile, so light and space carry the emotion.

**Prompt phrases.**
- "chiaroscuro lighting, single hard key light, no fill"
- "70 percent of the frame in deep black shadow"
- "a single pool of overhead light on a dark floor, subject on the edge of the pool"
- "venetian blind shadows raking across the textured wall and bending over the face"
- "half of the face in total shadow", "a slash of warm light across the eyes"
- "long cast shadow on the wall, larger than the actor"
- "visible light shaft through haze, haze only inside the beam"
- "warm tungsten practical lamps, deep teal-black shadows"

**AI failure modes and fixes.**
- *Milky lifted shadows.* "deep crushed blacks, no fill, unlit areas fall to pure black, low key, one light source".
- *Rim, kicker and glow on everything.* Name one source and direction: "single hard light from a window high camera-left", "background unlit".
- *Poreless glossy faces.* Grain, natural skin texture, halation. Avoid "hyperrealistic, 8k".
- *Centred spotlight on a stage.* Subject on a third or the pool's edge, large asymmetric black, describe the pool's shape.
- *Blind shadows as a graphic overlay.* "raking across the textured wall, bending over the face, soft-edged with falloff".
- *Teal-orange neon.* One warm practical against neutral or teal-black, or black and white.
- *Video: pool flickers or drifts.* Static light, "the overhead lamp is static", let the subject move in and out of it.
- *Fog flattens the frame.* "light haze only visible inside the beam".

**Reference frames.**
- [The Man Who Wasn't There (2001), Deakins](https://www.cosmos.so/e/240061747): round overhead pool with slats, figure on its edge.
- [The Godfather Part II (1974), Willis](https://www.cosmos.so/e/1376671378): Michael alone at the lit end of a long table.
- [Il Conformista (1970), Storaro](https://www.cosmos.so/e/1097613777): blind bars across a quilted wall and face.
- [Classic noir, uncaptioned](https://www.cosmos.so/e/1856838528): window arcs across a curved staircase.
- [A Very Long Engagement (2004)](https://www.cosmos.so/e/1829411036): dark arches toward one glowing exit.
- [In the Mood for Love (2000)](https://www.cosmos.so/e/1234444886): warm hanging practicals, face half lit against green-black.
- [Pirates of the Caribbean (2003)](https://www.cosmos.so/e/2120442065): amber slash across one eye.
- [La Chimera (2023)](https://www.cosmos.so/e/37083359): candle carves a statue's face out of black.
- [Classic noir, uncaptioned](https://www.cosmos.so/e/1056331692): huge hat shadow dwarfs a small lit man.

---

## 10. Blocking two people: OTS, two-shot and distance

Sub-board: https://www.cosmos.so/timmy111/blocking-two-people-ots-two-shot-distance

**What it is.** Placing two characters so their positions tell you how they relate before anyone speaks. The over-the-shoulder (OTS) shot puts one person's back or shoulder in the near foreground and points at the other's face. The two-shot keeps both readable: side by side, facing in profile, or stacked in depth. Distance, height and whatever sits between them (table, divider, counter, mullion, empty wall) carries the meaning.

**When to use.**
- Dialogue where power matters: interrogation, negotiation, argument (OTS, tightening as tension rises).
- Equality or intimacy: mirrored profile or side-by-side with matching posture.
- Estrangement: depth staging, opposite edges, a divider between them.
- Quiet endings: a small pair in a vast environment.
- Status and comedy through height.
- Brand or story videos with two people talking.

**Visual rules.**
- *OTS:* near person is a dark, soft, cropped mass on one edge, 25 to 45% of width, back or rear three-quarter to camera. Far person sharp on the opposite third, eyeline just past the lens toward that shoulder.
- *OTS distance sets temperature:* a small shoulder with a table gap reads as a calm standoff; a huge soft head filling a third reads as an attack.
- *Profile two-shot:* both in profile at the same height, mirrored. Whatever is on the centre line is the subject (a divider splits them; empty cups join them).
- *Side by side:* matching posture says connected; eyelines that don't meet say not yet.
- *Depth-staged:* one face big in the foreground, the other small behind. Separation is read in depth.
- *Wide two-shot:* people at opposite edges or tiny, with architecture or empty sea between.
- *Height and power:* who stoops or looks up writes the power balance.
- 40 to 85mm look for OTS and tight two-shots. Wides held flat and level at eye height. No Dutch tilt.
- One motivated source. The far subject is brighter than the foreground shoulder.
- Grounded, period-real colour; natural skin; visible grain.

**Depth planes.**
- *Far background:* a blur of practical lights, or (in extreme wides) sea, sky or architecture filling 80% or more.
- *Near background:* soft environment (patrons, a lamp, a wall, a window grid).
- *Subject placement:* the far face sharp on a third (OTS); both in one midground plane (profile, side by side); or one foreground, one mid or far (depth staging).
- *Foreground:* the near person's soft dark shoulder and head, plus props between them (cups, bottles) that mark the gap.

**Subject–environment.** The environment is a third character standing between or around the pair. Tables, counters, dividers, mullions and corridors measure or interrupt the distance. The set also sets height and power (a low doorway, seated versus standing).

**Prompt phrases.**
- "over-the-shoulder shot, foreground shoulder and back of head soft and dark on frame left, her face sharp on the right third"
- "his eyeline just off-lens toward the foreground shoulder"
- "two-shot in profile across a small table, equal height, mirrored poses"
- "a vertical divider in the centre of the table splitting the couple"
- "depth-staged two-shot, his face large in the foreground on a phone, her figure small in the lit room behind"
- "wide two-shot, the two at opposite edges, window mullion between them, sea behind"
- "coffee cups and a ketchup bottle on the table between them"

**AI failure modes and fixes.**
- *Both look at camera; no eyeline.* "looking at him, eyeline just past the lens toward the foreground shoulder", "back of head to camera".
- *Foreground shoulder sharp and lit, or cropped out.* "foreground shoulder out of focus, dark, cropped by the frame edge, a third of the frame".
- *Stock-photo couple pressed together, smiling.* State the gap and what fills it; give each person a different pose and eyeline.
- *Plastic skin, sterile set, rim light on both.* Grain, lived-in set, one motivated source, foreground in shadow, muted colour.
- *Depth staging collapses into one plane.* State sizes and planes outright.
- *Extreme wides grow figures or add a dramatic sunset.* "figures tiny in the lower right, 85% empty water and sky, overcast flat light".
- *Video: orbit or push-in, people drift or merge.* "locked-off static camera, the two keep their positions".

**Reference frames.**
- [Heat (1995), Spinotti: diner](https://www.cosmos.so/e/1316977528): textbook OTS, ketchup and cup in the gap.
- [Marriage Story (2019)](https://www.cosmos.so/e/654248766): huge blurred head, pointing finger, aggressive OTS.
- [Light Sleeper (1992)](https://www.cosmos.so/e/835583465): profile two-shot split by a divider.
- [Before Sunrise (1995)](https://www.cosmos.so/e/1736215605): mirrored booth two-shot, equal intimacy.
- [Paris, Texas (1984), Müller](https://www.cosmos.so/e/1913881788): depth-staged two-shot, phone cords connect them.
- [Heat (1995): house](https://www.cosmos.so/e/588054997): opposite edges, mullion between, empty sea.
- [Tokyo Story (1953), Ozu](https://www.cosmos.so/e/1171405576): tiny couple on a sea wall.
- [Being John Malkovich (1999)](https://www.cosmos.so/e/1709943500): stooping into a low doorway; power through height.

---

## 11. Close-up and extreme close-up

Sub-board: https://www.cosmos.so/timmy111/close-up-and-extreme-close-up

**What it is.** The camera moves in until one part of the subject fills the frame. A close-up runs chin to hairline, often with the top of the head cropped. An extreme close-up (ECU) leaves only a slice: two eyes, one eye, or one hand doing something. Surroundings almost disappear, so texture, light and tiny movement carry the emotion. Three families on the board: eye strips, full-face close-ups in hard light, and hand inserts (a short cutaway to a detail).

**When to use.**
- The moment of decision or realisation, just before an action.
- Confrontation: a frontal stare almost into the lens.
- Peak emotion carried by a tear, a quiver, eyes turned up.
- Stand-off rhythm: scope eye strips intercut with wides.
- Intimacy and touch without faces (hand inserts).
- Texture and detail beats, product or prop detail.
- Hiding identity: an eye seen through a gap.

**Visual rules.**
- Crop through the anatomy on purpose. Eye strips cut through forehead and nose. Face close-ups cut the top of the skull.
- Wide formats (2.39:1) make eye strips stronger; 4:3 suits centred, symmetrical faces.
- Eyes carry the frame: one small catchlight, eyes on or near the upper third, gaze just off lens or almost into it.
- Short telephoto feel (85 to 135mm) shot close. Very shallow focus: eyes sharp, ears and hair soft.
- Depth planes collapse. Background is gone or a flat, blank tone.
- Hard single side light. One side in deep shadow, the other showing pores, sweat and tears. A strip of light across the eyes is a common motif.
- Rich grainy black and white, or one colour family (amber on black, teal against amber, cold blue). Skin keeps real redness and blemishes.
- Hand inserts follow the same rules: one gesture, shallow focus, soft wash behind.

**Depth planes.**
- *Far background:* missing, or one flat soft tone (blank wall, grey curtain, sea band, black).
- *Near background:* darkness or a soft shoulder, collar, hair edge.
- *Subject placement:* fills 70 to 100% of frame, eyes sharp, cropped through forehead, chin or skull.
- *Foreground:* optional, very soft, framing from inside the shot (prison bars, bandages, a hat brim, grass blades).

**Subject–environment.** The environment is replaced by the surface of the face or hand. The face becomes the landscape. When the environment shows, it is one cue at the edge (bars say prison, a hat brim says gunslinger). It works because earlier shots already set up the space.

**Prompt phrases.**
- "extreme close-up of two eyes, frame cropped at forehead and mid-nose"
- "anamorphic 2.39:1 eye strip, eyes spanning the frame edge to edge"
- "tight close-up, top of head cropped, chin at bottom edge"
- "85mm, very shallow depth of field, eyes sharp, ears softly blurred"
- "hard single side light, half of the face in deep shadow"
- "visible skin pores, fine wrinkles, sweat and natural blemishes, one small catchlight"
- "out-of-focus prison bars in the foreground framing the face"
- "insert shot of two hands about to touch, shallow focus, soft background"

**AI failure modes and fixes.**
- *Plastic, poreless, symmetrical skin.* "visible pores, fine wrinkles, uneven tone, sweat sheen, natural blemishes", grain.
- *Safe passport framing with headroom.* Name the crop lines; use 2.39:1 for eye strips.
- *Glassy, oversized, dead-centre eyes with ring-light catchlights.* "one small catchlight", "eyes slightly asymmetric", "gaze just off lens", eyes on the upper third.
- *Flat beauty-dish light.* "hard single side key, the other half in deep shadow, no fill".
- *Everything sharp, or fake even blur.* "focus on the eyes only, ears and hair falling softly out of focus".
- *Extra or fused fingers.* Simple gesture, soft background, regenerate or inpaint; slow hand movement in video.
- *HDR teal-orange.* One colour family, lifted blacks, halation.
- *Busy background or bokeh balls.* "blank, featureless background", "background falls to black".
- *Video: face morphs, unnatural blinks, drifting camera.* Locked-off or very slow push-in, short clip, "single slow blink".

**Reference frames.**
- [Taxi Driver (1976)](https://www.cosmos.so/e/945664467): eyes cropped through brow and nose, one in shadow.
- [Lone Wolf and Cub: Baby Cart to Hades](https://www.cosmos.so/e/583704716): scope eye strip under a soft hat brim.
- [The Passion of Joan of Arc (1928)](https://www.cosmos.so/e/2032562215): bare face, eyes turned up, blank ground.
- [Persona (1966)](https://www.cosmos.so/e/1441473006): hard side light, face as a landscape.
- [The Silence of the Lambs (1991)](https://www.cosmos.so/e/1600231013): frontal stare through soft bars.
- [Unknown film](https://www.cosmos.so/e/1017572823): one eye through a slit in bandages.
- [Un Chien Andalou (1929)](https://www.cosmos.so/e/1992582726): palm crawling with ants.
- [Whiplash (2014)](https://www.cosmos.so/e/1614180114): scope close-up, hard amber light on black.

---

## 12. Colour blocking and colour contrast

Sub-board: https://www.cosmos.so/timmy111/colour-blocking-and-colour-contrast-in-the-frame

**What it is.** The frame is built from a few large flat fields of colour (walls, curtains, foliage, snow, sky, costume). The subject stands out by hue, not by sharpness or brightness. Two approaches: the set is one dominant colour and the subject is its complement (the opposite on the colour wheel) or a neutral; or the whole world is muted and one costume is the only saturated accent.

**When to use.**
- Pulling the eye to a small figure in a wide or busy frame.
- Symbolic tension: each character owns a colour.
- Dreamlike, uncanny or stylised genres (horror, wuxia, neon noir, storybook).
- Brand moments where one colour must read instantly on a small screen.
- Visually noisy locations, where hue does the separation.

**Visual rules.**
- Limit the palette to 2 or 3 hues: one dominant field plus one opposing accent.
- The dominant colour is architectural: walls, floor, curtain, hillside, 60 to 80% of the frame, running to the edges.
- The subject can be small. Hue is enough to find them.
- Put the complement in the far opening (a blue door at the end of a red corridor) and stand the subject in or against it.
- Echo the subject's colour once in the set (a red curtain behind red pyjamas). This stops the accent looking pasted in.
- Wide to normal lens, deep focus, often one-point symmetry. Colour separates planes, so no heavy blur.
- Light motivates the colour (gels, neon, blue-hour ambient, natural daylight on coloured scenery). Most colour lives in production design and costume, not the grade.
- Only the block and the accent are saturated. Skin, floor and props stay muted; night shadows go near black.

**Depth planes.**
- *Far background:* the contrasting colour seen through an opening (blue door, pale exterior, green-curtained window, cool sky).
- *Near background:* the dominant colour block wrapping the frame, edge to edge.
- *Subject placement:* usually full-body and fairly small, where the two colours meet, or as a single accent in a muted field.
- *Foreground:* empty floor in the dominant colour, or a darker, less saturated framing element (a bamboo trunk, a soft curtain edge).

**Subject–environment.** The environment is a coloured stage and the subject is defined by how their colour relates to it: the complement of the set, or the same hue as one prop while the rest is the complement. In two-figure frames, colour sets characters against each other.

**Prompt phrases.**
- "bold colour blocking, limited two-colour palette"
- "small figure in a red costume against a field of golden autumn leaves"
- "saturated red corridor with a single blue doorway at the end, one-point perspective"
- "lone figure in a yellow raincoat on a desaturated blue-grey forest path at dusk"
- "red pyjamas against teal-green painted wood, a red curtain echoing the costume"
- "colour from practical gels and painted sets, 35mm grain"
- "muted skin tones, only the costume and the walls are saturated"

**AI failure modes and fixes.**
- *Rainbow creep.* Name exactly two or three colours; everything else "muted, desaturated, neutral".
- *Everything pushed to neon, including skin.* "saturated walls and costume only, natural skin, deep black shadows, film stock colour".
- *Smooth 3D-render walls.* Name the material (textured plaster, worn boards, carpet pattern), add grain.
- *Subject made hero by blur and size.* "small full-body figure, wide shot, deep focus, a tenth of the frame".
- *Colour graded on (global LUT).* Put colour in design and costume, describe light sources.
- *Accent bleeds into the background.* Complement in the opening, or the echo limited to one prop.
- *Video: palette drifts, new coloured objects appear.* Lock the palette in every segment, slow simple moves, large static colour elements.

**Reference frames.**
- [Suspiria (1977), Argento](https://www.cosmos.so/e/1588034754): red corridor, blue door, small woman in the doorway.
- [Hero (2002), Zhang Yimou](https://www.cosmos.so/e/601969447): red robe among gold leaves.
- [Uncaptioned wuxia](https://www.cosmos.so/e/2121400403): red rider among pale green bamboo.
- [The Wonderful Story of Henry Sugar (2023)](https://www.cosmos.so/e/795288682): red pyjamas, teal caravan, red curtain echo.
- [Uncaptioned still](https://www.cosmos.so/e/116273107): yellow raincoat on a blue-grey forest path.
- [Kill Bill: Vol. 1 (2003)](https://www.cosmos.so/e/1634164520): yellow against white kimono in blue night snow.
- [Uncaptioned Chinese period film](https://www.cosmos.so/e/1881788532): red lattice corridor to a pale blue-grey doorway.
- [Queer (2024)](https://www.cosmos.so/e/1936374297): all-red corridor, white figure, green window.

---

## 13. Atmosphere as depth: haze, rain, light shafts

Sub-board: https://www.cosmos.so/timmy111/atmosphere-haze-rain-light-shafts-as-depth

**What it is.** Particles in the air (haze, fog, smoke, rain, spray) build depth. Each step back gets more veiled, lower in contrast and closer to the colour of the air. Light through that air becomes visible: beams, shafts, blooming lamps, backlit rain. The subject is usually a dark silhouette against a brighter veil.

**When to use.**
- Giving exteriors readable scale and distance (cities, forests, mountains, long streets).
- Loneliness, mystery, threat, dreamlike mood.
- Night exteriors, where practicals need something to bloom in.
- Dark interiors with one shaped source drawing a beam.
- Establishing shots and transitions.
- Rain scenes that must read on camera.

**Visual rules.**
- Contrast falls with distance: foreground darkest and sharpest, subject mid-grey, far background almost the haze colour. Aim for 3 to 5 clear tonal steps.
- The subject is a silhouette placed where the haze behind is brightest.
- Light from behind or the side, into the lens. Front light makes atmosphere vanish.
- One hard source makes a beam; the beam can be the main line of the frame.
- Practicals bloom in wet air, and the halos shrink with distance.
- Subject small, midground, centred or on a third. A large dark shape frames one edge (bridge, cave mouth, trunks, arch).
- Wide to normal lens, deep focus. Long lenses stack hills into flat grey layers.
- One overall tint (sodium orange, steel blue, teal, grey-green) with one small warm practical as the accent. Blacks lift in the distance only.
- Wet ground doubles the light with reflections.
- Patchy, moving, uneven atmosphere. Grain over clarity.

**Depth planes.**
- *Far background:* almost gone into the haze, faint skyline, mountain or treeline.
- *Near background:* one step lighter and softer (buildings, trees, a truck with blooming headlights).
- *Subject placement:* 1/4 to 1/2 into the depth, silhouette or dim, against the brightest patch.
- *Foreground:* darkest, highest-contrast plane, a near-black frame (pier, cave wall, trunks, arch) or wet ground with reflections.

**Subject–environment.** The environment dominates. Atmosphere isolates the figure by stripping detail, so the eye has nowhere to go but the silhouette. People often walk away into the haze or stand at the edge of a bright veil. In interiors, the beam is often the real subject.

**Prompt phrases.**
- "thick atmospheric haze, layered depth fading into fog"
- "lone figure in silhouette walking away into dense fog"
- "strong backlight through haze, visible light shafts"
- "headlights and streetlamps blooming in misty night air, halos smaller with distance"
- "backlit rain streaks against a black background"
- "distant skyline fading in steps into orange dust haze"
- "wet cobblestones reflecting lamplight, fog down the street"
- "dark foreground frame, bright hazy midground, faded background"

**AI failure modes and fixes.**
- *Uniform digital fog filter.* "uneven, patchy, drifting fog with varying density", "smoke wisps".
- *God rays everywhere.* "one single hard light source, one beam", name the opening.
- *Subject front-lit and detailed.* "figure in silhouette, backlit, face not visible, rim light only".
- *No tonal steps.* Name the planes and the number of steps.
- *Even grey rain lines, front-lit.* "rain lit from behind, bright streaks only where the backlight hits, black background".
- *Clean saturated CGI sheen.* One tint, lifted blacks in the distance only, grain, halation, imperfect exposure.
- *Point lights with no bloom, or giant flares.* "soft halos around lamps in wet air, small and subtle".
- *Video: frozen fog layer.* "slowly drifting fog, particles moving through the beam, rain falling at real speed".

**Reference frames.**
- [Blade Runner 2049 (2017): orange haze](https://www.cosmos.so/e/136068033): skyline in 3 to 4 orange steps.
- [Blade Runner 2049 (2017): night fog](https://www.cosmos.so/e/2010318571): silhouette walks away, headlights bloom.
- [Blood Simple (1984)](https://www.cosmos.so/e/1739555774): beams through bullet holes.
- [King of New York (1990)](https://www.cosmos.so/e/1132458724): one projector beam through smoke.
- [Edward II (1991)](https://www.cosmos.so/e/1521452976): backlit rain against black.
- [Voyage to Cythera (1984)](https://www.cosmos.so/e/448523436): mountain mist in flat grey-green layers.
- [Interview with the Vampire (1994)](https://www.cosmos.so/e/1413801787): blue fog, gas lamps fading down a wet street.
- [Castle Rock (TV)](https://www.cosmos.so/e/594819694): sun through trees, glowing cyan forest haze.

---

## 14. Cinematic vertical framing (9:16)

Sub-board: https://www.cosmos.so/timmy111/cinematic-vertical-frames-9-16-and-portrait

**What it is.** Composing for a tall frame so the height tells the story. The subject is usually small and low, in the bottom third and often against an edge. The upper half to two-thirds holds architecture, light shafts, a hard shadow, a corridor or soft colour. Most board frames are mid-century tall street photographs (Fan Ho, Saul Leiter and others) plus three moving-image frames. These photographers already accepted heavy negative space in a tall format, which is why the lessons carry over to 9:16 video.

**When to use.**
- Native vertical delivery (Reels, TikTok, Shorts) that should feel like cinema, not a selfie.
- Lonely-figure beats: isolation, scale, a person against a city.
- Shots that need a clean zone for captions: subject low, text in the designed space above.
- Atmospheric B-roll where light is the real subject.
- Alleys, corridors, stairwells, doorways and windows, whose own verticals suit a tall frame.
- Melancholy, contemplation, noir, nostalgia.

**Visual rules.**
- Subject small and low: in most frames under 15% of height, in the bottom 40%.
- Massive, designed headroom: the top 50 to 70% holds something with weight (shadow wedge, overhang, tenement walls, light streaks, a cold door opening). Never blank.
- Use the edges. Subjects stand against a frame edge or strong vertical. Centre only when a corridor's vanishing point puts them there.
- Vanishing lines run top to bottom: walls converge toward the upper middle, the floor widens at the bottom.
- High angles flatten the ground into a blank page; long cast shadows become a second subject.
- Hard, low raking sun from one side or behind; haze in the backlight makes shafts.
- Frames within frames repeat the vertical format (doorway, shop window, mirror).
- Colour work: a large soft foreground blocker covers 30 to 50% of one side, subject seen through the gap (longer lens, shallow focus).
- B&W reads as 35 to 50mm deep focus; colour and film frames as 85mm and up, shallow.
- Muted palette with one saturated accent, or one cold hue throughout.
- The subject is usually a dark silhouette on a bright area, or lit against darkness. Faces are rarely the brightest thing.

**Depth planes.**
- *Far background:* the vanishing end of an alley or street, skyline or bridge tower, brightest and haziest, high in the frame.
- *Near background:* the dominant tall surface filling the upper frame (wall, shadow, overhang, light streaks). It sets the mood and takes the caption space.
- *Subject placement:* one small figure or a pair, low in frame, often silhouetted, often on a light pool with a long cast shadow.
- *Foreground:* empty ground (high angle), a dark framing mass (doorframe, overhang, railing), or a soft colour blocker covering a third to half the frame.

**Subject–environment.** The environment is the main character and the person gives it scale and emotion. The figure is dwarfed, framed or swallowed. They interact with a graphic element: walking into a shadow edge, standing in a gap, crossing a light pool. Cast shadows tie them to the ground.

**Prompt phrases.**
- "vertical 9:16 cinematic frame, composed natively for a tall frame"
- "small lone figure in the lower third, vast negative space above"
- "subject near the left edge against a towering wall"
- "diagonal hard shadow cutting across a pale wall"
- "narrow alley with converging walls, figures at the bottom of frame"
- "out-of-focus foreground blocker covering one third of the frame, subject seen through the gap"
- "frame within a frame, dark doorway around a crouched figure, cold blue light"
- "muted palette with a single red accent"

**AI failure modes and fixes.**
- *Centred, enlarged medium shot.* State size and position ("under one-tenth of frame height, bottom-left corner") and describe the upper space as its own subject.
- *Blank headroom that looks unfinished.* Give it texture: peeling plaster, a hard diagonal shadow, window glow, haze shafts.
- *Spotless CGI walls, HDR shadows.* Weathered surfaces, crushed blacks, grain, edge softness, stray pedestrians, asymmetric placement.
- *Fill light on the face.* "single hard raking sun, no fill, near-silhouette, long shadow toward camera".
- *One flat plane.* Name all three layers and a lens cue.
- *Teal-orange grade.* "muted palette, one red accent" or high-contrast black and white.
- *A 16:9 idea padded to vertical.* Build around vertical forms; say "composed natively for a tall frame".
- *Video: camera creeps in and the figure grows.* Lock off or slow vertical tilt; let the figure walk through the frame.

**Reference frames.**
- [Fan Ho, Approaching Shadow (1954)](https://www.cosmos.so/e/21691293): tiny figure bottom-left, shadow wedge above.
- [Fan Ho, Afternoon Chat (1959)](https://www.cosmos.so/e/381830838): extreme tall alley, children in the bottom fifth.
- [Fight Club (1999)](https://www.cosmos.so/e/1840496240): true 9:16, head in the bottom third, light streaks above.
- [Uncredited vertical film frame](https://www.cosmos.so/e/2119876958): dark door around a cold blue opening, crouched figure.
- [Fan Ho, Crossing](https://www.cosmos.so/e/249169772): high angle, umbrella walker and long shadow.
- [La Notte (1961), Antonioni](https://www.cosmos.so/e/1217692375): small woman under a huge concrete mass.
- [Saul Leiter](https://www.cosmos.so/e/541019291): teal soft blocker, figure in the gap, red accent.
- [Fan Ho, Hong Kong (1958)](https://www.cosmos.so/e/1593229663): glowing corridor end, running boy in the lower third.

---

## 15. Staging for movement: diagonals and depth staging

Sub-board: https://www.cosmos.so/timmy111/staging-for-movement-diagonals-and-depth-staging

**What it is.** Blocking so movement runs along the lens axis (toward or away from camera) or on a strong diagonal, never flat left to right across one plane. The movement creates depth: a near element is played against something approaching or receding, and the line of travel is also the vanishing line. In the best frames you can see where the motion came from and where it's going in one still.

**When to use.**
- Chases and escapes: threat in the background, victim in the foreground.
- Arrivals and confrontations: someone approaches while another waits in front.
- Epic mass movement: armies, migrations, convoys.
- Journeys: where they came from and where they're headed, in one frame.
- Interior suspense down one-point corridors.
- Any wide that would otherwise be a static postcard: add a moving element on a diagonal.

**Visual rules.**
- Put the line of travel on the depth axis or a diagonal.
- Build three or four planes, each with a job: foreground anchor (witness or victim), midground carrier, deep background destination or threat.
- Make the foreground big and cropped by the frame edge. The scale jump sells the distance.
- Mostly wide to normal, deep focus, strong convergence. A long lens can stack a mass charging toward camera.
- Repeat moving bodies along the diagonal; repetition with shrinking size turns a crowd into a direction.
- Atmosphere (dust, smoke, fog, spray) separates the planes.
- Foreground darker or silhouetted, background brighter, so the eye travels down the line into the light. Earthy, restrained palette.
- Low horizon for movement over land; no horizon (overhead) when the pattern is the point; centred vanishing point when movement is confined.
- Contrast case: flat lateral staging reads as a tableau, not travel.

**Depth planes.**
- *Far background:* the destination or threat, small and hazy (horizon, smoke, an incoming plane, a lone rider).
- *Near background:* the path becoming visible (road, rails, corridor, dust trail, a file of shrinking figures).
- *Subject placement:* the moving subject or mass on the diagonal or lens axis, where converging lines still read bodies.
- *Foreground:* a large cropped, often darker anchor (back of a head, a doorway silhouette, rifles, legs, a fence post). Leave it out only when the pattern carries the frame.

**Subject–environment.** The environment is the track the movement runs on. Roads, rails, corridors and slopes are framed so their perspective lines are the line of action, and the subject is placed on that line. The landscape defines direction, scale and threat. Characters are small when the story is about distance, and big in the foreground only as a witness or victim to measure it.

**Prompt phrases.**
- "deep staging, action moving along the lens axis toward camera"
- "strong diagonal line of movement across the frame"
- "large cropped foreground figure, back to camera, watching the approach"
- "subject running toward the lens while the threat closes in from the background"
- "file of figures receding on a diagonal into haze"
- "overhead shot, converging dust trails behind speeding cars"
- "crowd surging toward camera in compressed rows, long lens"
- "practical dust and smoke, foreground darker than background"

**AI failure modes and fixes.**
- *Side-on parade on one plane.* State direction ("receding diagonally from lower left foreground to upper right background") and what's in front and behind.
- *No foreground; medium subject on an empty backdrop.* Ask for a large cropped foreground element plus a small distant element.
- *Dustless air, cloned crowds, everything sharp.* Kicked-up dust, smoke, haze, grain, slight motion blur, irregular spacing.
- *Bending perspective, mixed vanishing points.* "single vanishing point", state camera height.
- *Video: motion drifts sideways mid-shot.* Lock the camera or "Steadicam following directly behind at hip height"; describe start and end positions in depth.
- *HDR teal-orange on every plane.* Natural daylight, hazy lower-contrast distance, foreground in shadow.
- *Mushy distant crowds.* Limit the count, or "rows of riders diminishing into dust".

**Reference frames.**
- [North by Northwest (1959)](https://www.cosmos.so/e/1659751014): crop-duster from the background, Grant running at camera.
- [Mad Max: Fury Road (2015), Seale](https://www.cosmos.so/e/1070383663): Furiosa's shoulder, War Rig on a diagonal, tiny figure behind.
- [Thelma & Louise (1991)](https://www.cosmos.so/e/1585592512): overhead, police cars converging, dust trails.
- [Days of Heaven (1978)](https://www.cosmos.so/e/1767546407): workers on the train roof, train cutting into deep space.
- [Once Upon a Time in the West (1968)](https://www.cosmos.so/e/386432704): dark doorway, rider approaching in dust.
- [Lawrence of Arabia (1962)](https://www.cosmos.so/e/853533824): long-lens camel charge toward camera.
- [The Hidden Fortress (1958)](https://www.cosmos.so/e/2002228319): four figures climbing in fog.
- [The Shining (1980)](https://www.cosmos.so/e/2129193541): Steadicam tricycle down a one-point corridor.

---

## Cross-cutting rules for every shot

### Depth planes

- **Every card names at least three planes.** Far background, near background, subject placement, and a foreground (or a stated reason there is none: ECU, top-down, a silhouette sun-disc). The prompt-card warning for missing planes should almost never fire.
- **Separate planes by tone first, focus second.** The most common board pattern is a dark foreground, a lit subject and a pale far background. Atmosphere lifts the far planes. Blur is optional.
- **Commit to one focus strategy.** Either deep focus (size shows distance) or one soft foreground plane. Never an even blur on everything but the subject.
- **The foreground is cropped, dark and specific.** Name the object and the frame edge it sits on. A tidy, fully visible foreground looks generated.
- **Give the far background one job.** Usually the brightest, haziest area, often the light source or the destination.
- **Video parallax.** Near planes move faster than far ones on a lateral move. State it in `world.parallax`. Keep the foreground object simple and solid so it doesn't morph.

### Subject and environment

- **The environment is never a backdrop.** It sits in front of and behind the subject. Write `subject.interaction` as a physical link between them (a shadow across the floor, light through blinds on the face, dust from each step, framed by the doorway).
- **Decide the size ratio on purpose.** Most strong frames on the board make the subject small (under a quarter of height; often under a tenth). Large subjects are for close-ups, OTS and low-angle power shots.
- **State the ratio in numbers.** "a tenth of the frame", "less than 5% of the frame". Models enlarge people unless told.
- **Gaze and travel point into space.** Into the open side, into the depth, or straight into the lens only for confrontation.
- **Let the set carry meaning.** Doorways, dividers, tables, corridors and light shapes say what the shot is about.

### Avoiding the too-perfect AI look

These came up on all 14 boards. Put the relevant ones in `light_look.finish` and the negatives.

- **One motivated light source.** Name its direction. No fill unless the shot needs it. No rim light on everyone.
- **Real blacks.** Crushed or slightly lifted by film, never milky grey and never HDR.
- **Muted, restrained colour.** Two or three named colours at most. No default teal-orange.
- **Grain, halation, gentle falloff and slight edge softness.** "35mm film still" helps on most models.
- **Lived-in surfaces.** Mud, scuffs, peeling paint, smudged glass, worn carpet, litter, dust in the light.
- **Imperfect symmetry and spacing.** One asymmetric detail in a symmetrical frame; varied poses and irregular gaps in crowds.
- **Natural skin.** Pores, fine lines, blemishes, one small catchlight.
- **Uneven atmosphere.** Patchy, drifting fog; one beam, not many; small lamp halos that shrink with distance.
- **Avoid trigger words.** "8k", "ultra detailed", "hyperrealistic", "epic", "cinematic lighting", "bokeh background".
- **Video:** locked-off or one slow, stated move; short clips; the subject moves inside the frame rather than the camera chasing them.

### Vertical 9:16 notes

- **Move the subject low.** Bottom third, often against an edge. Centre only on a corridor's vanishing point.
- **Design the headroom.** The upper 50 to 70% holds a textured surface, shadow or light, and doubles as caption space. Check the platform's UI zones (top and bottom on Reels, right and bottom on TikTok) before placing anything critical.
- **Build on vertical forms.** Doorways, alley walls, stairwells, towers, falling light streaks. Never pad a 16:9 idea.
- **What converts well:** frame within a frame, leading lines (alleys and corridors), negative space, high angles, silhouettes, chiaroscuro, atmosphere, soft foreground blockers.
- **What needs rework:** wide two-shots at opposite edges (stack them in depth instead), low-horizon landscapes (put the figure low and let the sky take the height), scope eye strips (use a single eye or a tight face close-up instead).
- **Foreground blockers work well in tall frames.** A soft shape covering a third of one side adds depth without crowding the subject.

---

## Proposed rule changes for shotcraft

**Status: applied** (see CHANGELOG, Unreleased). Where each part went:

- Taxonomy vocab: added to `rules/taxonomy.json` (`camera.composition`, the `world` depth fields,
  `subject.placement`, `subject.interaction`, `light_look.finish`). "bokeh from string lights" was replaced by
  "soft out-of-focus string lights at the edge"; "Dutch tilt" now says to use it on purpose only.
- Cinematographer: the intent-to-technique chooser, size ratio, tone before blur, angle wording, the vertical
  9:16 block and the two-person block are in `agents/cinematographer.md`; the short version is
  `skills/prompt-craft/references/composition-and-lighting.md`.
- Prompts checklist: the items became PR-21 to PR-36 in `skills/producer/references/checklists/prompts.md`
  (trigger words are PR-27). The director names each shot's technique in the shot list's `composition`
  column (`skills/director/references/shotlist-format.md`, SL-15).
- Reworded: the trigger-word list is wider than proposed ("ultra detailed", "hyperrealistic", "cinematic
  lighting", "well lit" too), and the mood term "epic" became "awe at vast scale".

Terms already in `rules/taxonomy.json` are not repeated below.

### `rules/taxonomy.json` vocab

**`camera.composition`** (add):
- `one-point perspective`: lines meet at one vanishing point, usually centre.
- `vanishing point on subject`: the subject stands where the receding lines meet.
- `nested frames`: doorway inside doorway, each smaller and brighter.
- `low horizon`: horizon on the lower third or lower; sky is the story.
- `high horizon`: horizon on the upper third or out of frame; ground is the story.
- `tiny figure, vast frame`: subject under about 5% of frame height.
- `pool of light`: one lit island in a mostly black frame.
- `colour blocking`: two or three flat colour fields; subject set apart by hue.
- `depth-staged two-shot`: one person large in front, the other small behind.
- `diagonal line of action`: movement along a diagonal or the lens axis.
- `eye strip`: extreme close-up cropped through forehead and nose.
- `low-placed subject, tall headroom`: vertical frame, subject in the bottom third, designed space above.
- `foreground blocker`: a large soft shape covering a third of one side, subject seen through the gap.
- Change `Dutch tilt` "means" to say it breaks calm geometry and should be deliberate, never decorative.

**`world.background_far`** (add): `pale far wall of haze`, `glowing doorway at the end of the corridor`, `bright window behind the subject`, `giant sun disc low on the horizon`, `vanishing point of the road at the horizon`, `black void`.

**`world.background_near`** (add): `second room in a different colour temperature`, `repeated doors receding at a steady rhythm`, `secondary figure waiting in the near distance`, `wall catching venetian-blind bars`, `dark cut-out skyline on the horizon`.

**`world.foreground`** (add): `silhouetted head and shoulder, cropped at the frame edge`, `dark door jambs filling both sides`, `soft tree trunk filling the right third`, `row of seated heads along the bottom edge`, `out-of-focus railing at the frame edge`, `solid black ground band`, `table props marking the gap between two people`. Consider replacing `bokeh from string lights` with `soft out-of-focus string lights at the edge`; the board warns against bokeh-as-background.

**`world.parallax`** (add): `figure walks along the corridor centre line, camera static`, `fog drifts through the beam while the room stays still`, `threat grows from background toward the lens`.

**`subject.placement`** (add): `exactly at the vanishing point`, `on the edge of the light pool`, `bottom third against the left edge (vertical)`, `cornered lower right under a heavy foreground mass`, `on the brightest patch of sky, outline clear`.

**`subject.interaction`** (add): `seen through the foreground, half hidden`, `facing into the open space of the frame`, `walking away into the haze`, `shadow larger than the actor on the wall`, `blind bars bending across the face`, `costume colour echoed by one prop in the set`.

**`light_look.finish`** (add): `crushed blacks, no milky shadows`, `haze increasing with distance, uneven and drifting`, `lived-in set: scuffs, dust, worn surfaces`, `one asymmetric detail in a symmetrical frame`, `soft lamp halos that shrink with distance`.

### `agents/cinematographer.md`

- Add a **story-intent-to-technique table** (the quick chooser above, trimmed) to the Composition section, so the agent picks technique from intent.
- Add a **size-ratio rule**: write the subject's share of frame height as a number whenever the shot is wider than a medium.
- Add a **"tone before blur" rule** for planes: foreground darkest, far background palest; choose deep focus or one soft foreground, never an even background blur.
- Add **angle wording**: describe camera position and visible effect (e.g. "camera on the ground, soles in foreground"), not just "low angle".
- Add a **vertical 9:16 block**: subject low, designed headroom as caption space, build on vertical forms, the convert/rework list above.
- Add a **two-person block**: OTS shoulder size sets the temperature, eyeline just off-lens, name what sits in the gap.

### Prompts checklist (prompt-craft / producer checklists)

- [ ] Story intent maps to a named technique, at most three combined.
- [ ] Far background, near background, placement and foreground all filled (or the exception stated).
- [ ] Foreground is specific, cropped and names its frame edge.
- [ ] Subject size given as a fraction of the frame for anything wider than a medium.
- [ ] Gaze or travel direction stated and points into space.
- [ ] One light source named with direction; fill stated as none or low.
- [ ] Palette named in two or three colours.
- [ ] `light_look.finish` has at least two imperfection terms.
- [ ] No trigger words ("8k", "hyperdetailed", "epic", "bokeh background").
- [ ] Video: one camera move with speed, or locked-off; parallax written.
- [ ] Vertical: subject in the lower third and headroom described as a surface, clear of platform UI zones.
