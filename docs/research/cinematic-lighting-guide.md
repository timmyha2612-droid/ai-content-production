# Cinematic lighting for shotcraft

This guide turns a private Cosmos study board into working lighting rules for shotcraft. The parent board is [Cinematic lighting setups: shotcraft study](https://www.cosmos.so/timmy111/cinematic-lighting-setups-shotcraft-study). It has 16 sub-boards, one per setup, each with about 19 to 22 film stills and photographs. Every frame was viewed and broken down into key position, fill, rim, practicals, ratio, colour, motivation and depth. The guide is for the cinematographer agent, the production-designer agent and the prompt-craft skill. It maps onto the Light & Look layer (`setup`, `quality`, `direction`, `color_temp`, `practicals`, `palette_grade`, `texture`, `finish`, `style_ref`, `mood`), the depth fields (`world.background_far`, `world.background_near`, `subject.placement`, `world.foreground`, `world.parallax`), `subject.interaction` (how light from the place falls on the subject) and `light_look.finish` (natural imperfection, never too perfect).

It is the companion to [docs/research/cinematic-composition-guide.md](cinematic-composition-guide.md). Composition decides where things sit. Lighting decides what the eye sees first, what stays hidden, and whether the frame feels real.

One idea runs through all 16 boards: **cinema light comes from one place the audience can believe in, it falls off, and it leaves most of the frame darker than the face.** AI models do the opposite by default. They light everything from everywhere, lift every shadow and polish every skin. Most of this guide is about stopping that.

## How to use this

- **Start from the story intent, not the setup.** Use the chooser to go from what the viewer should feel to a setup. Then fill the five core fields (`setup`, `quality`, `direction`, `color_temp`, `practicals`) from that row.
- **Name one key and its side on every card.** "Key from frame-left window, high" beats "cinematic lighting". `direction` must always name a side (frame-left / frame-right / behind / above).
- **Describe the cause, not the patch.** Say where the light is and how big it is. The pattern (triangle, butterfly, stripes) then follows. Asking for the pattern alone gets it painted on.
- **Show or imply the source.** Put the window, lamp, sign, sun or flame in `practicals` or in a depth field, and say what it lights in `subject.interaction`.
- **Say what stays dark.** Every low-key or practical setup needs a line like "the room falls into darkness" or "background near-black". Models only leave things dark when told.
- **Fill all depth planes with values.** For each plane, say whether it is dark, lit, or a bright accent. The "Depth and space" block in each section is the template.
- **Use the failure modes as a review checklist.** Each section lists what image and video models get wrong and the wording that fixes it.
- **Use the reference frames as a sanity check.** Open the `https://www.cosmos.so/e/<id>` links when unsure. Do not put living artists' or DPs' names, or film titles, into prompts unless the brief allows style references.
- **Jargon in one line:** *key* = the main light. *Fill* = light that lifts the shadows. *Rim / back / hair light* = light from behind that outlines the subject. *Practical* = a lamp or screen that appears in shot. *Ratio* = how much brighter the key side is than the shadow side (2:1 is soft, 8:1 is dramatic). *Falloff* = how fast light fades with distance. *Motivated* = light that seems to come from a real source in the scene. *Terminator* = the line where light turns to shadow on a face. *Cookie / gobo* = something in front of a light that breaks it into a pattern. *Contre-jour* = shooting toward the light.

## Quick chooser

Format of the last column: `setup` / `quality` / `direction` / `color_temp` / `practicals`.

| Story intent / mood | Setup | Light & Look fields in one line |
|---|---|---|
| Hidden motives, gravitas, moral weight | Rembrandt | Rembrandt lighting / hard or soft, high contrast / 45-degree key, high, frame-left / tungsten 3200K key, cool dark background / one lamp or window in background |
| Glamour, star reveal, icon, beauty | Butterfly / Paramount | butterfly lighting / hard light (classic) or soft clamshell (beauty) / key on lens axis, above, angled down / tungsten 3200K / none, or overhead fixture implied |
| Duality, threat, a decision, interrogation | Split | split lighting / hard light, fast falloff / side light at 90 degrees, eye height / tungsten 3200K or neutral / one lamp, window or blind slats |
| Everyday drama close-ups; open vs closed character | Loop, broad, short | loop lighting + short (moody) or broad (open) / soft or hard / 30-45 degree key, slightly high / warm tungsten key, cool shadow / window or lamp off-frame |
| Optimism, clean commercial, clinical, dream | High key | high key / soft, wraparound, low contrast / large frontal or overhead / one temperature throughout (cool white or warm cream) / ceiling panels, big window |
| Menace, secrets, noir, isolation | Low key | low key / hard, fast falloff / single high key or backlight / amber tungsten, or warm spark on cool ambient / blinds, street lamp, bulb |
| Introspection, period, quiet domestic | Window light | window light / soft, gradual falloff / side light 60-110 degrees / daylight 5600-7000K, warm skin / the window itself, sun patch on wall |
| Mystery, longing, separation, memory | Backlight / rim | backlight + rim light / hard / back light or contre-jour, one side / warm 2700-3500K or cyan / sun, window, lamp or stage light behind |
| Real night interiors, insomnia, screen life | Motivated practicals | practical lighting / soft at source, fast falloff / from the practical's side / tungsten 2700-3200K vs cool screen / desk lamp, screen glow, pendant |
| Nostalgia, romance, endings, awe | Golden hour | golden hour sunlight / hard sun, soft bounce / contre-jour or low side, 0-10 degrees up / 2500-3500K sun, cool sky shadows / none (the sun) |
| Melancholy, transition, quiet unease | Blue hour | blue hour ambient + practical lighting / soft skylight, small hard practicals / sky behind or window side / cool sky vs tungsten 2000-3200K / streetlamp, table lamp, lit windows |
| Urban noir, alienation, restless night | Night exterior mixed colour | neon lighting + motivated lighting / hard coloured spill / side or top from street sources / sodium vapour + fluorescent green / street lamps, neon sign, car headlights |
| Grief, austerity, folk dread, realism | Overcast | overcast softbox sky / soft, low contrast / top light (exterior) or window side (interior) / overcast 6500K / none |
| Heat, summer, watched, trapped | Hard sun / dappled | gobo pattern / hard light / high side, 60-90 degrees / warm sun, cool shade / blinds, leaves, window grid |
| Period, intimacy, folk horror, survival | Firelight / candlelight | firelight / small source, fast falloff / low, from below and side / candlelight 1900K, cool night outside / candles, lantern, torch, campfire |
| Power, interrogation, isolation in a pool | Top light | top light / hard, fast falloff / overhead 60-90 degrees / tungsten 3200K or fluorescent green / pendant lamp, ceiling fixture |

**Interviews.** Sit-down studio interviews and podcasts have their own guide: [docs/research/studio-interview-lighting-guide.md](studio-interview-lighting-guide.md). It covers 8 interview setups with rigs, small-kit versions, camera placement and reference frames. This guide stays general; the two link to each other.

---

## 1. Rembrandt lighting

Board: [Rembrandt lighting](https://www.cosmos.so/timmy111/rembrandt-lighting)

**What it is.** One dominant key about 45 degrees to one side and 30-50 degrees above eye line. The nose shadow falls down and across the far cheek and joins the cheek shadow. All that stays lit on the shadow side is a small inverted triangle under the far eye, no wider than the eye and no longer than the nose. Fill is low or absent, so the face reads as sculpted and half-hidden. The board runs from hard-key Hollywood studio portraits through Gordon Willis's low-key Godfather to a cool Deakins night exterior and soft window portraits.

**When to use.**
- Moral ambiguity, a character with something hidden: the half-shadowed face literally hides part of them.
- Gravitas and authority: patriarchs, bosses, interrogators, a decision being made.
- Quiet interiority in drama or a character portrait.
- Night or interior scenes motivated by one window, lamp or streetlight.
- Brand or documentary hero portraits that should feel timeless rather than commercial.
- Not for bright comedy, upbeat lifestyle or beauty shots that need open skin. Use butterfly or broad soft light there.

**Sources.**
- *Key:* one source at roughly 10-11 or 1-2 o'clock, set high and angled down. The subject turns slightly toward it so the far cheek catches the triangle. Hard and small (fresnel, bare bulb) gives a crisp nose shadow. A window or big diffusion gives the same geometry with a gradual edge.
- *Fill:* little or none. Shadow detail comes from room bounce, never from a second visible key.
- *Back/rim:* optional and subtle. A hard edge on the shadow side traces hair and shoulder against black (Karsh's Bogart). Most film stills use none.
- *Practicals:* motivate the key or sit as one small highlight in the background (backlit blinds behind Vito, a lit window deep in a night exterior).

**Ratio and contrast.** Portrait versions about 4:1 to 8:1; noir and Godfather versions 8:1 to 16:1 or more. The test: the triangle must be brighter than the shadow around it, darker than the lit cheek, and closed at the bottom by the joined shadows. Light leaking down the cheek means it has become loop or short. No triangle means it has become split. Background blacks may clip; lit-cheek highlights must not.

**Colour.** One dominant temperature from the key. Warm family: tungsten or amber key around 2800-3400K, shadows neutral or cool (Casino puts a warm key against dark teal-green). Cool family: one bluish-white night source around 5000-6500K with a small warm window deep in the background (Prisoners). The key decides the skin colour; ambient takes the complementary temperature at a far lower level. Never give the fill a third hue.

**Motivation.** A high side source: a window or last sun, an office or bar lamp, a streetlight or porch light, a desk lamp. Show it on the key side: window edge or curtains in frame, a lamp glowing behind, blinds lit from outside. The key must come from the same side as the visible source, and from above it.

**Depth and space.**
- `background_far`: near-black or one dark colour, broken at most by one small motivated highlight.
- `background_near`: a soft gradient, brighter behind the shadow side of the head, darker behind the lit side, so both edges separate.
- `subject.placement`: the brightest values in frame (lit cheek, forehead, nose bridge, triangle). Body and wardrobe fall off fast.
- `foreground`: a dark out-of-focus shape or soft flare past a window frame, curtain or shoulder; always darker than the face.

**Prompt phrases.** "Rembrandt lighting" · "single key light high and 45 degrees to the side" · "small triangle of light under the far eye" · "nose shadow joining the cheek shadow" · "deep shadow side, very little fill" · "low-key chiaroscuro portrait" · "warm tungsten key, cool dark background" · "soft window light from one side" · "background falling to near-black" · "one practical glowing in the background" · "subtle hair rim light on the shadow side" · "natural skin texture, visible pores" · "35mm film still, film grain"

**AI failure modes and fixes.**
- *Triangle painted on, not cast:* a bright patch on an otherwise evenly lit face. Fix: describe the cause ("single high key at 45 degrees, nose shadow joins the cheek shadow, almost no fill"). Reject frames where the shadow side matches the lit side apart from the triangle.
- *Lit from everywhere:* beauty wrap plus a second key. Fix: "one light source only", "deep shadow on the far side of the face", dark background. Avoid "well lit", "studio lighting", "softbox".
- *Shadows disagree with the source:* nose, hair and collar shadows point different ways, or the visible window is on the wrong side. Fix: name the side on every shot and put the motivating source on that side of frame.
- *Key too low or frontal:* split light or no nose shadow. Fix: "key above eye line, angled down", "subject turned slightly toward the light".
- *Plastic skin, HDR shadows.* Fix: "natural skin texture, pores, subtle imperfections, film grain, shadows allowed to go black"; avoid "flawless", "HDR", "ultra-detailed".
- *Unmotivated glow:* rims on both sides, halo behind the head. Fix: at most one subtle rim on the shadow side; background dark except one practical.
- *Video drift:* the triangle wanders or the key follows the face like a ring light. Fix: anchor the source to the set ("fixed window light on the left wall"), small head turns, camera on the shadow side.

**Pairs with (composition).** Short-side camera so the triangle faces the lens; tight close-ups and MCUs at or just below eye level; negative space on the dark side; large black areas; dirty frames past a window edge, shoulder or hand; off-centre thirds with the face looking into the light; slow push-ins; shallow focus with one practical bokeh highlight.

**Reference frames.**
- [1954028380](https://www.cosmos.so/e/1954028380), *The Godfather* (1972), Gordon Willis: the core geometry, key high frame-left, closed triangle, very little fill.
- [2045378239](https://www.cosmos.so/e/2045378239), Marlon Brando studio portrait, 1950: hard small key, crisp joined shadows, grey gradient behind the shadow side.
- [333123428](https://www.cosmos.so/e/333123428), Aes Harris studio portrait: key frame-right, gentle fill, easiest frame for reading direction and ratio.
- [1877249531](https://www.cosmos.so/e/1877249531), *Casino* (1995), Robert Richardson: warm tungsten key against dark teal-green.
- [1434827771](https://www.cosmos.so/e/1434827771), *Prisoners* (2013), Roger Deakins: single cool night source, no fill, warm window deep in the background.
- [14289618](https://www.cosmos.so/e/14289618): warm low window light from frame-right, cold blue-black curtains behind.
- [2033805060](https://www.cosmos.so/e/2033805060), Bogart, 1946, Yousuf Karsh: high key plus a hard rim on black.
- [1548067173](https://www.cosmos.so/e/1548067173): shot through a window frame; all four depth planes.

---

## 2. Butterfly / Paramount lighting

Board: [Butterfly / Paramount lighting](https://www.cosmos.so/timmy111/butterfly-slash-paramount-lighting)

**What it is.** One key on the lens axis, directly in front and well above eye line, pointing down. The nose casts a small symmetrical shadow straight down toward the upper lip, shaped like a butterfly. The same light carves shadows under the cheekbones, jaw and brow. A hard spot gives the 1930s-40s studio glamour version (crisp butterfly, hollow cheeks, a pool of light on the backdrop). A large soft source with lots of fill gives the modern beauty version, where the nose shadow is only a faint smudge. Tells: the nose shadow points straight down; both cheeks get equal light; catchlights sit high and central; the chin shadow falls on the neck.

**When to use.**
- Glamour, star or icon moments: introducing the femme fatale, the diva, the leading lady.
- Old-Hollywood, noir or 1930s-40s pastiche.
- Beauty, cosmetics, fragrance and jewellery close-ups (soft, high-fill version).
- Worship or longing beats, face tipped up into the light.
- Cold, untouchable characters (hard key, little fill, eyes half-lidded under the brow shadow).
- Not for naturalistic drama, grit or documentary: it reads as posed for camera.

**Sources.**
- *Key:* on the lens axis, 30-50 degrees above eye line. Classic: a small, distant hard fresnel spot, often throwing an oval halo on the seamless behind the head. Beauty: a beauty dish, big octa or diffused frame just above the lens.
- *Fill:* from below (white card or low soft light: the clamshell). Very little in the Paramount look; a lot in beauty work.
- *Back/rim:* a small hard kicker or top-back spot rims hair and shoulders off a dark ground.
- *Background:* a separate spot or gradient, bright behind the head, falling to dark.
- *Practicals:* none in portraits. On set, motivate as a ceiling lamp, chandelier, stage spot or high window.

**Ratio and contrast.** Paramount/Hurrell about 4:1 to 8:1: near-white forehead, nose bridge and cheekbone tops; deep grey or black cheek hollows and eye sockets; backgrounds near black or a single halo. Black wardrobe frames the white face. Beauty version about 2:1 or less, open shadows, skin texture kept.

**Colour.** The board is mostly B&W: luminous skin against velvet blacks. In colour, a 3200K tungsten key gives warm peachy skin; fill matches the key (white card). Modern beauty uses neutral 5600K and warms in the grade. Avoid mixed colour on the face: one clean colour from one direction.

**Motivation.** A light overhead and in front: ceiling fixture, chandelier, stage spot, streetlamp, skylight. Show it by including the fixture's glow at the top edge, letting a hat brim cut the light, keeping a body shadow on the wall that agrees with the height, or a halo on the backdrop. Or motivate it by gesture: the subject tips her face up into a lamp.

**Depth and space.**
- `background_far`: dark, or a halo bright at centre falling off at the edges.
- `background_near`: mouldings, a door frame, or the subject's cast shadow, which proves the key's height.
- `subject.placement`: the face is the brightest thing in frame; black wardrobe takes the body to near black; a hair rim separates where tones merge.
- `foreground`: hands, gloves, a hat brim, fur or a cigarette holder catch some key as a second, dimmer layer. Out-of-focus foreground goes dark, not bright.

**Prompt phrases.** "butterfly lighting" · "Paramount lighting" · "single hard key light directly above the camera, angled down" · "small symmetrical butterfly shadow under the nose" · "sculpted cheekbones with shadowed hollows" · "high central catchlights in both eyes" · "dark shadow under the chin falling on the neck" · "1930s Hollywood glamour portrait" · "spotlight halo on the backdrop behind the head" · "face tipped up into an overhead light" · "thin hair rim light separating the head from the dark background" · "black velvet wardrobe falling to pure black" · "silver gelatin black and white, fine film grain" · "soft clamshell beauty lighting with a white reflector below the chin" · "warm 3200K tungsten key, natural skin texture"

**AI failure modes and fixes.**
- *Flat, lit from everywhere:* "glamour" read as even beauty light, no nose shadow, no hollows. Fix: one hard key above the camera aimed down, "small butterfly shadow under the nose", "shadowed cheek hollows", "minimal fill".
- *Key drifts to the side:* diagonal nose shadow, one cheek darker (loop or Rembrandt). Fix: "nose shadow points straight down, symmetrical", "both cheeks equally lit"; face square to camera or tipped up.
- *Shadows disagree with the source:* top-lit face but a side cast shadow, or two cast shadows. Fix: one source only; ask for the body's shadow low behind the subject, or keep the background dark.
- *Plastic, perfect skin:* waxy and poreless. Fix: "natural skin texture, visible pores, fine film grain"; for period, "silver gelatin".
- *Halo and rim everywhere:* rims on both sides, evenly lit background. Fix: one thin rim from behind and above, background darker than the face, halo falling to black, black wardrobe.
- *Unmotivated on set:* overhead key from nowhere while room practicals sit at the side. Fix: put a ceiling lamp, chandelier or stage spot over the subject in the prompt.
- *Eyes sunk to black:* key too high. Fix: "high central catchlights", "reflector below the chin".

**Pairs with (composition).** Centred, symmetrical, square-on framing; tight or choker close-ups; MCU with hands framing the face; low-key frames with black negative space; slight high angle or face tipped up; frame within a frame via hat brim, veil or fur collar; shallow focus on a dark ground; black wardrobe silhouetted on a halo; slow push-in for the star reveal.

**Reference frames.**
- [1889776244](https://www.cosmos.so/e/1889776244), Brenda Marshall by George Hurrell: textbook hard butterfly with an oval halo on the backdrop.
- [1136896098](https://www.cosmos.so/e/1136896098), Marlene Dietrich, 1932: hard overhead key, hollowed cheeks, almost no fill.
- [377028757](https://www.cosmos.so/e/377028757), *Shanghai Express* (1932) still: face tipped up into the light; motivation by gesture.
- [352638842](https://www.cosmos.so/e/352638842): strong butterfly, pure black background, hair kicker, hand in foreground at a lower level. The clearest lesson on the board.
- [2000257823](https://www.cosmos.so/e/2000257823), Greta Garbo, 1931: symmetrical nose shadow plus a hard body shadow on the wall showing source height. (The builder credited this to 1238834235, which is not on the board and shows a different pose.)
- [2070760386](https://www.cosmos.so/e/2070760386), Laszlo Willinger portrait for MGM, 1947: hat brim cuts the top light.
- [1138763709](https://www.cosmos.so/e/1138763709), Dorothy Dandridge, 1951: warm tungsten colour version.
- [514703244](https://www.cosmos.so/e/514703244), Calvin Klein Obsession campaign: modern soft clamshell with real skin texture; the anti-plastic reference.

---

## 3. Split lighting

Board: [Split lighting](https://www.cosmos.so/timmy111/split-lighting)

**What it is.** One hard or semi-hard key at about 90 degrees to the face, at eye height, so the bridge of the nose becomes the boundary. One cheek and eye are fully lit; the other half falls into deep shadow or black. Almost no fill. Tighter variants flag the key or pass it through a gap, leaving only a vertical sliver of face. It is the most graphic, least flattering portrait light: the face literally becomes two halves.

**When to use.**
- Duality and inner conflict: a character torn between two choices or two selves.
- Threat, menace, a hidden agenda.
- Interrogation, confession, a decision in close-up.
- Noir and crime: the villain's reveal, the moment someone turns.
- Isolation at night: one window, one lamp, the rest dark.
- Grief or withdrawal in a gentler warm version.
- Standoff close-ups before violence.
- Avoid for comedy, warm romance, beauty, product, or whenever both eyes must read.

**Sources.**
- *Key:* at 9 or 3 o'clock, exactly side-on (10-20 degrees forward for a softer version where the far eye just catches light). At or slightly above eye level, so the nose shadow lies across the far cheek; no triangle. Usually hard (bare fresnel, sun or streetlight through a window, a lamp). Modern versions use a small soft source close in, so the edge rolls off over 1-2 cm. Shaped variants come through a blind, door crack or slat.
- *Fill:* none, or negative fill (black flags). In colour, a whisper of room bounce keeps the far eye barely visible.
- *Back/rim:* normally none. A kicker on the shadow-side jaw is an occasional variant; use sparingly.
- *Practicals:* the source is often in or just outside frame (window panes, a fire, a lamp). Background practicals stay dim and out of focus.

**Ratio and contrast.** Classic B&W and noir 8:1 to 16:1 or more, shadow side crushed to black. Softer colour versions 4:1 to 8:1, far eye a dark shape with a tiny catchlight. The transition across the nose is short; with a hard key it is a single line. The background is usually as dark as the shadow side, so the dark half merges into the room (a lost edge). Expose for the lit cheek and let everything else go.

**Colour.** Warm family: tungsten, candle, firelight or low sun at about 2700-3200K; skin amber; the black side has a slight warm brown lift, not blue. Neutral or cool family: daylight or moonlight, often graded cyan or green-grey, or monochrome. When temperatures mix, the key keeps one warm hue and any cooler spill goes to the far background only. Never let a second colour fill the shadow side evenly; that becomes a two-tone gel look.

**Motivation.** A single window, a door or curtain gap, slatted blinds, a bedside or desk lamp, a candle, a fire, a streetlight, and a room otherwise dark. Show it: window slats behind, a second figure's cast shadow on the wall at the key's angle, blind stripes on the face, fire glow in the background. If the source cannot be shown, give the subject a reason to be side-on to it.

**Depth and space.**
- `background_far`: black void, or only small motivated highlights (slats, a dim practical, a blurred lit figure).
- `background_near`: a wall catching a cast shadow or a slash of the same key. This is the best way to show the source and add a layer.
- `subject.placement`: the only lit plane, and only half of it; the lit cheek is the brightest thing in frame. Separation on the dark side comes from a faint kicker or a slight tonal step, or not at all.
- `foreground`: empty or a dark out-of-focus shoulder, door frame or blind. A second face can sit here with its own softer light (Othello).

**Prompt phrases.** "split lighting" · "hard side light at 90 degrees" · "half the face in deep shadow" · "light falls off at the bridge of the nose" · "no fill light, single source" · "lit by one window off-frame" · "warm tungsten lamp from the side" · "dark room, black background" · "light through a gap in the blinds, slash of light across the face" · "the far eye lost in shadow" · "high contrast chiaroscuro portrait" · "natural skin texture, pores visible" · "cast shadow on the wall behind"

**AI failure modes and fixes.**
- *Fill creep:* dark side lifted to 2:1. Fix: "no fill", "the shadow side falls to black", "one single light source"; negatives "flat lighting, evenly lit, softbox, beauty lighting".
- *Lit from everywhere:* rim, hair light, background glow and key together. Fix: name the only source; ask for a black background; negate "rim light, backlight, studio lighting".
- *The terminator wanders:* diagonal split, highlights on the shadow side. Fix: "the light boundary runs straight down the bridge of the nose, key exactly side-on at eye height".
- *Shadows disagree with the source:* window on frame-left but face lit from the right. Fix: put source and lit side on the same side in the prompt, and say where the wall shadow falls.
- *Plastic skin:* hard side light should reveal texture. Fix: "visible pores, fine lines, slight sheen on the lit cheek, film grain"; negate "airbrushed, retouched".
- *Two-tone stylisation:* teal or magenta in the dark half. Fix: "single warm tungsten source, the shadow side dark and neutral"; cool tones only in the far background.
- *Unmotivated:* a perfect split in a bright daylit room. Fix: "night interior, only light from one lamp", and put the source or its pattern in frame.
- *Video:* the split line swims or exposure pumps. Fix: "static key light, consistent across the shot", slow head turns; a turn into the light can be the reveal.

**Pairs with (composition).** Tight close-ups and ECUs, eyes on a third; profile or three-quarter turn toward the key; negative space on the shadow side; frame within a frame (door gaps, blinds); off-centre with the lit side facing open space; low-key minimal backgrounds; two-shot contrast with one face split and one soft; slow push-in or a head turn into the light; dark out-of-focus foreground shapes.

**Reference frames.**
- [1633054738](https://www.cosmos.so/e/1633054738), *Lone Wolf and Cub: Sword of Vengeance* (1972): textbook colour split, window panes behind motivate it.
- [525646635](https://www.cosmos.so/e/525646635), B&W noir-style portrait: crisp terminator, far side true black.
- [1373050319](https://www.cosmos.so/e/1373050319), photo by Josef Beyer: extreme flagged sliver.
- [664651439](https://www.cosmos.so/e/664651439), uncredited film still: slatted window, a second figure's shadow on the wall and the split face all agree.
- [1885588389](https://www.cosmos.so/e/1885588389), *Waves* (2019): small deep-amber source, negative fill, softer edge.
- [1994477041](https://www.cosmos.so/e/1994477041), *Euphoria* S2: gentle warm split, far eye keeps a glint. (Viewed as a reference; not on the sub-board itself.)
- [150965616](https://www.cosmos.so/e/150965616), uncredited: neutral-cool key, blue-teal background as the only second colour.
- [203394041](https://www.cosmos.so/e/203394041), *Othello* (1951): hard split on the man, soft light on the woman below. (Viewed as a reference; not on the sub-board itself.)

---

## 4. Loop, broad and short lighting

Board: [Loop, broad and short lighting](https://www.cosmos.so/timmy111/loop-broad-and-short-lighting)

**What it is.** Names for where one key sits relative to the face and to the way the face turns. **Loop:** key 30-45 degrees off axis and slightly above eye line; the nose casts a small shadow down and to the side that does not touch the cheek shadow. **Broad:** face at three-quarter, key on the side nearer camera (the ear side), so the widest area of skin is lit; reads open and approachable. **Short:** key on the side turned away from camera, so the near cheek and ear fall into shadow; slims the face and reads moody or intimate. Loop describes the nose shadow; broad and short describe which side is lit, so they combine. Most of this board is "short-loop".

**When to use.**
- Dialogue singles: short for tension, secrets, grief or seduction; broad for warmth, openness, honesty.
- Classic glamour and noir mood (hard short-loop, low fill, dark background).
- Introspective naturalistic drama with a window or lamp as a soft short key.
- Interviews and documentary: soft loop with gentle fill flatters without looking lit.
- Arcs within a scene: open a character with broad, turn them into short as it darkens.
- Shaping faces: short slims a round face, broad opens a narrow one.

**Sources.**
- *Key:* one source 30-60 degrees off axis and 20-45 degrees above eye line. Studio versions use a hard fresnel at 1-2 or 10-11 o'clock. For short lighting it sits on the side the face turns toward; for broad, on the ear side. Naturalistic versions use a window, daylight through a frame, or a practical just off-frame. Hard sun through a gap gives a strip of light.
- *Fill:* low or absent in drama (near side almost black); brighter in glamour loop; from white walls in daylight frames.
- *Back/rim:* classic stills add a hard hair or edge light opposite the key. Naturalistic stills separate by darkness alone.
- *Background:* often a soft pool or gradient behind the shadow side of the face.
- *Practicals:* in film the key is motivated by a lamp, firelight or neon.

**Ratio and contrast.** Short-loop drama about 8:1 to 16:1, shadow side 3-4+ stops under. Classic noir and glamour short-loop 4:1 to 8:1 with a rim. Glamour loop and broad 2:1 to 3:1. Window broad 2:1 to 4:1, set by room bounce. Keep the loop small and pointing down at the key's angle; if it reaches the cheek shadow, it has become Rembrandt.

**Colour.** B&W studio frames: read for value only. Colour film stills: warm tungsten, amber or sunset key at 2700-3400K or warmer; shadow side and background neutral or cool (teal void, blue window patch, magenta and blue bokeh). Daylight window versions neutral, 5000-5600K. Keep fill the colour of the room's ambient; no second strong colour on the face unless a practical motivates it.

**Motivation.** Studio portraits are frankly unmotivated. In film, the key comes from a window just off frame (sun shapes on the wall confirm it), a blind cutting the sun into a strip, a fire or lamp low to one side, an overhead fixture, or club and street neon. Block the actor relative to the source rather than moving the light: turning toward or away from it chooses short or broad.

**Depth and space.**
- `background_far`: dark or a soft gradient, often brighter behind the shadow side of the face; in colour, out-of-focus coloured bokeh or a cool void.
- `background_near`: a wall catching the source (window patches, cast shadows, a warm tungsten wash). This places the source without lighting the face flat.
- `subject.placement`: the only full exposure; the key carves one plane; the shadow side merges with the background unless a rim or tonal step holds the head shape.
- `foreground`: shoulders, hands and clothes fall off below the face, or sit as dark out-of-focus shapes. Light runs face to body, subject to background, warm to cool.

**Prompt phrases.** "short lighting, key light on the far side of the face" · "small loop shadow from the nose falling down and to the side" · "broad lighting, the near cheek lit by a soft key" · "single hard key light high and 45 degrees to one side" · "near side of the face falling into deep shadow" · "low fill, high contrast portrait, 8:1 lighting ratio" · "1940s Hollywood studio portrait, hard Fresnel key, hair rim light" · "soft window light from one side, the face turned toward the window" · "warm tungsten key, cool dark background" · "a strip of late sun across the eyes through a gap in the blinds" · "firelight on one side of the face, the rest falling into black" · "natural skin texture, pores visible, specular highlight on the cheekbone"

**AI failure modes and fixes.**
- *Flat frontal light:* no nose shadow, no darker side. Fix: name side and angle ("key 45 degrees camera-left, high, small loop shadow under the nose to the right, the near cheek in shadow").
- *Lit from everywhere:* several catchlights, evenly bright body and background. Fix: "single source, low fill", "dark background", "one catchlight on the key side".
- *Broad and short mixed up.* Fix: describe it physically ("face turned three-quarter to the right, light from the right lighting the far cheek, the near ear side dark").
- *Unmotivated studio key in a naturalistic room.* Fix: name and show the source ("window just off frame left, sunlight patches on the wall behind").
- *Shadows disagree:* nose, neck and wall shadows point different ways. Fix: state the direction once and repeat it in the shadows.
- *Plastic skin.* Fix: "natural skin texture, fine pores, crisp specular on the cheekbone, gradual transition from light to shadow, film grain".
- *Loop grows into Rembrandt or split.* Fix: "small loop shadow that does not touch the cheek shadow", key "slightly above eye level, 30-45 degrees off axis".
- *Colour contamination:* teal-orange grade over everything. Fix: "warm key only on the lit side of the face, shadows neutral to cool, background cool".

**Pairs with (composition).** Close-ups and MCU singles; three-quarter face turns (needed to tell broad from short); negative space on the shadow side or in the look direction; shallow focus with dark or bokeh ground; low-key single bright subject; gaze off-frame toward the source; shot-reverse-shot alternating short and broad to show power; window edge visible as motivation; chiaroscuro diagonals.

**Reference frames.**
- [1285865758](https://www.cosmos.so/e/1285865758), Hedy Lamarr, MGM (Clarence Bull): textbook short-loop, near side into black.
- [639145041](https://www.cosmos.so/e/639145041), Lauren Bacall, 1943, John Engstead: noir short-loop with hair rim, about 6-8:1.
- [520671619](https://www.cosmos.so/e/520671619), Ava Gardner, 1943: glamour loop, open fill; the low-contrast end.
- [489916354](https://www.cosmos.so/e/489916354), Oscar Isaac: broad lighting with a soft warm key; open and vulnerable.
- [1303701139](https://www.cosmos.so/e/1303701139), Amy Acker: soft short lighting against black.
- [1082146022](https://www.cosmos.so/e/1082146022), *Keeping Time* (2023): warm practical short key on darker skin, warm wall shows the room's source.
- [1930249693](https://www.cosmos.so/e/1930249693): hard warm sun strip on the short side, cool window patch in the corner.
- [966814108](https://www.cosmos.so/e/966814108), *Sanctuary* (2022): orange key, magenta and blue neon bokeh behind.

---

## 5. High key

Board: [High key](https://www.cosmos.so/timmy111/high-key)

**What it is.** The whole frame sits in the upper half of the tonal range: pale surfaces, a large soft key, fill strong enough to almost erase shadow, and a background at or above the subject's brightness, often clipping to white. Contrast comes from a few dark accents (eyes, hair, dark trousers), not from shadow. Four forms on the board: architectural (a set that is a lightbox of overhead tubes, THX 1138); portrait on white seamless or open shade (Avedon); bright daylight lifestyle with a window behind; and warm overexposed sun close-ups drifting into memory (Her). High key does not mean no shape: the best frames keep a gentle gradient from one side.

**When to use.**
- Clean optimism, safety, commercial brightness (food, family, wellness, tech, cosmetics).
- Sterile, clinical or dystopian control: white institutions where nothing can hide.
- Isolation in emptiness: a small figure in a field of white.
- Honest truth portraits where texture carries the story.
- Memory, dream, nostalgia, the afterlife: bleached warm close-ups.
- Comedy and storybook tableaux; fashion and beauty where garment and shape matter more than mood.

**Sources.**
- *Key:* very large and soft, at or near the camera axis or 10-11 o'clock, 15-30 degrees up. In architecture shots the key IS the ceiling (rows of tubes or diffuser panels). In Avedon it is open shade or overcast sky. In lifestyle, a big window behind or beside, so subjects are partly backlit.
- *Fill:* heavy and everywhere: white walls, floors, cloths, garments and cyc bounce. Shadows within about a stop of the key.
- *Back/rim:* often none needed; the background is already brighter. In warm close-ups the sun behind flares the hair.
- *Background:* lit separately 1-2.5 stops over the key on a cyc, or self-lit by the ceiling.
- *Practicals:* ceiling fixtures, a pendant, globe lamps. Motivation, not exposure points.

**Ratio and contrast.** Key to fill about 1.5:1 to 2:1. Skin shadows never go below lower midtones; the darkest values come from objects and costume. Background at or above the subject, often clipped. Histogram piled into the top third with a small cluster of true blacks.

**Colour.** Neutral to cool white (4500-5600K, sometimes a faint green fluorescent cast): clinical and controlled. Monochrome: paper-white background, light-grey skin. Warm white (3200-4300K look): cream, butter or peach rooms and amber sun glow. Keep one temperature across key, fill and background: high key has no shadow to hide a mismatch. Low to moderate saturation; small colour accents do the colour work.

**Motivation.** Something big and bright in the world: a ceiling of tubes or panels, a wall of windows, overcast sky, the sun behind, a white studio. Show it: tubes running to the vanishing point, a blown window behind the family, a pendant over the table. Every surface being pale is part of the motivation: the room is the reflector.

**Depth and space.** High key separates planes with brightness and perspective, not darkness.
- `background_far`: brightest, often clipped (corridor end, blown window, cyc, pale sky).
- `background_near`: walls and shelves one step down, with converging ceiling lights and floor edges giving depth.
- `subject.placement`: separated by a dark accent or saturated colour against the pale field; in portraits, a thin soft jaw shadow and dark eyes.
- `foreground`: clean and empty, or an out-of-focus pale frame slightly darker than the middle.
- Planes get brighter and softer with distance.

**Prompt phrases.** "high-key lighting" · "bright, low-contrast, soft wraparound light" · "white seamless background blown out to pure white" · "large soft frontal key with heavy bounce fill" · "almost shadowless face, gentle shadow under the jaw only" · "overhead fluorescent ceiling panels lighting a white corridor" · "white walls bouncing daylight into the room" · "warm window backlight, airy bright interior" · "lifted shadows, milky blacks, pale pastel palette" · "dark eyes and dark clothing as the only deep tones" · "clean clinical white, slight cool fluorescent tint" · "35mm film grain, natural skin texture and pores"

**AI failure modes and fixes.**
- *Grey and muddy:* "high key" read as "flat", everything midtone. Fix: "background brighter than the subject, clipping to pure white", "bright exposure", plus one dark accent.
- *No direction at all:* faces look scanned and pasted on. Fix: name one big source and where it is; allow "a faint soft shadow under the chin and on the far cheek".
- *Plastic skin:* worse here, since nothing hides smoothing. Fix: "visible pores, freckles, fine lines, unretouched, film grain".
- *Shadows disagree:* hard cast shadows in a soft-panel room. Fix: "soft, diffuse, overhead light; soft pools directly under the figure only".
- *Unmotivated glow.* Fix: name or show the source.
- *Colour mismatch:* warm faces in a cool room, neon creeping in. Fix: one stated temperature for the whole frame.
- *Blown skin and white fabric.* Fix: "background clipped, skin and white fabric retain detail, soft highlight rolloff".
- *Video exposure pumping.* Fix: "locked exposure, constant even light".

**Pairs with (composition).** Small figure in large negative space; one-point perspective and symmetry down corridors; centred frontal tableau; tight close-ups where texture is the subject; arches and doorways as pale frames; minimalism with one colour or dark accent; repetition and pattern; full-length fashion with generous headroom.

**Reference frames.**
- [1212862414](https://www.cosmos.so/e/1212862414), *THX 1138* (1971): overhead tubes, one-point aisle, tiny white figure.
- [1580612988](https://www.cosmos.so/e/1580612988), *THX 1138*: near 1:1 wrap; the clinical extreme.
- [1185388674](https://www.cosmos.so/e/1185388674), Avedon, *In the American West*: open shade on white seamless, full skin texture kept.
- [986479573](https://www.cosmos.so/e/986479573), uncredited (flagged by the builder as *Her*, unconfirmed): cream-yellow office under diffuser panels; separation only from dark trousers.
- [998704902](https://www.cosmos.so/e/998704902), *Her* (2013): warm backlit flare, milky blacks; the memory version.
- [1561436297](https://www.cosmos.so/e/1561436297), B&W fashion: figure on a cyc blown to white.
- [1564353745](https://www.cosmos.so/e/1564353745), lifestyle: white room through an arch, window backlight, pendant as motivation.
- [1792387224](https://www.cosmos.so/e/1792387224), uncredited: cool white corridor, dark trousers and backpack as separation.

---

## 6. Low key

Board: [Low key](https://www.cosmos.so/timmy111/low-key)

**What it is.** Most of the frame sits in shadow. A single hard, directional key shows only the planes that matter (a forehead and cheekbone, a stripe of blind light, a pool on the floor, a rim) and everything else falls to black. Exposure is set for the highlights; shadows are allowed to clip. The key comes from above (Godfather top light), from behind (a street lamp or doorway backlighting silhouettes through haze), through a pattern (blinds, slats), or from a tiny practical (a lighter flame). Works in B&W and colour (amber tungsten; cool ambient with one warm spark).

**When to use.**
- Menace, power and secrets: the boss's office, interrogation, the deal in the dark.
- Moral ambiguity: the unseen half of a face says something.
- Noir and crime: stakeouts, night streets, someone in a doorway.
- Isolation: one figure in a pool of light in a huge dark space.
- Intimacy and grief at night (Moonlight's warm, barely lit embrace).
- Tension before violence; a silhouette stepping into the light.
- Making a premium product mysterious: one sculpted edge.

**Sources.**
- *Key:* one hard, small source, often 60-80 degrees above the eyeline. On faces it is top or high three-quarter, so brows put the eye sockets in shadow. For patterns, a hard sun or fresnel through blinds from 2-3 o'clock high. For night exteriors, a street lamp behind the subjects, throwing long shadows toward camera. Indoors, a blown-out doorway behind does the same.
- *Fill:* close to none; only bounce from pavement, a desk or a white shirt.
- *Back/rim:* often the only light on the subject: a thin hard edge while the face stays black, or haze glowing around a silhouette.
- *Practicals:* hanging bulbs, a street lamp in frame, a lighter flame as the entire key, out-of-focus bulbs as background accents. Always in frame or clearly implied.

**Ratio and contrast.** About 8:1 to 16:1 or more. Shadow sides and most of the set at or near black; often 60-80% of the frame within a stop or two of black. Skin highlights stay below clip; windows, lamps and blind stripes may blow. Rich deep blacks, never milky.

**Colour.** (1) B&W: silvery highlights, inky blacks. (2) Warm monochrome: 2700-3200K amber, shadows brown-black. (3) Warm against cool: a 5600-7000K teal or blue base with one small warm source (a lighter at about 1900K against rain-blue). Keep one temperature dominant; the second appears only where a named source puts it. No neon wash everywhere.

**Motivation.** Every bright area is explained by something visible or inferable: blind slats glowing behind the boss, the street lamp in the top corner, hanging warehouse bulbs, an open door, the flame in a hand. Patterned light proves the source's shape and direction. Haze makes beams visible. If you cannot point to the source, the light is wrong for this style.

**Depth and space.** Depth comes from alternating dark and light planes.
- `foreground`: usually a dark unlit silhouette or frame (over-the-shoulder heads, a tunnel mouth, a window frame).
- `subject.placement`: the only well-exposed plane, in a pool or stripe of key.
- `background_near`: falls off quickly to black, or is broken by stripes or practicals for texture without brightness.
- `background_far`: total black, or one bright opening (window, doorway, lamp in haze) to silhouette against.
- Typical order: dark foreground, lit subject, black near background, bright far point.

**Prompt phrases.** "low-key lighting" · "single hard key light from above" · "deep black shadows, no fill light" · "eye sockets falling into shadow" · "venetian blind shadows across face and wall" · "lit only by a street lamp behind them, silhouettes in haze" · "a single pool of light from a hanging bulb in a dark warehouse" · "face lit only by a lighter flame" · "thin rim light on the edge of the face, face in darkness" · "backlit doorway, figure in silhouette" · "dark foreground silhouette framing the shot" · "warm tungsten practical against cool blue night ambient" · "rich crushed blacks, motivated light" · "light haze catching the beam"

**AI failure modes and fixes.**
- *Lifted, milky blacks.* Fix: "crushed true blacks, shadows clipping to black, most of the frame in darkness".
- *Lit from everywhere:* soft beauty light on the face in a "dark" room. Fix: name one source and its side; "no fill, the right side of the face falls into black".
- *Unmotivated light.* Fix: put the source and its pattern in the prompt and frame.
- *Shadows disagree:* stripes at different angles on wall and body; shadows falling toward a backlight. Fix: state the direction ("lamp behind them, long shadows stretching toward camera"); reject frames whose shadows do not point away from the source.
- *Plastic skin.* Fix: "visible pores and skin texture, hard specular on forehead and nose, film grain".
- *Rim plus key plus fill on everything.* Fix: pick one: key only, rim only, or backlit silhouette.
- *Neon soup in colour.* Fix: one dominant temperature; the second only from a named practical.
- *Silhouettes with lit faces.* Fix: "face fully in shadow, only the outline glows, no front light".
- *Video:* key drifts off its motivation, shadows slide. Fix: lock the source position; small camera moves; stripe patterns stay fixed to the set.

**Pairs with (composition).** Frame within a frame (doors, windows, tunnels, car windows); dark foreground silhouettes and OTS; small figure in a large dark field; silhouette against a bright opening; dramatic high or low angles; leading lines made of light stripes or banisters; centred single figure in a pool; shallow focus with practical bokeh; slow push-in on a half-lit face.

**Reference frames.**
- [1130307882](https://www.cosmos.so/e/1130307882), *The Godfather* (1972): hard top light, black eye sockets, blinds behind blow out.
- [263120806](https://www.cosmos.so/e/263120806), *The Killers* (noir): street lamp behind two men, haze, long shadows toward camera.
- [177217993](https://www.cosmos.so/e/177217993), *Road to Perdition* (2002): bulb pools in a dark warehouse, dark foreground figures.
- [1527299221](https://www.cosmos.so/e/1527299221): lighter flame as the entire key, against teal rain-blue.
- [1674450177](https://www.cosmos.so/e/1674450177), unconfirmed digital B&W (reads like *Sin City*): blind stripes, window in frame.
- [185029192](https://www.cosmos.so/e/185029192), *Stranger* (2013 short): foreground profile barely edged, doorway silhouette in haze.
- [352950172](https://www.cosmos.so/e/352950172): rim only, face black; the opposite of AI's front-fill habit.
- [618865461](https://www.cosmos.so/e/618865461): cool key, red rim, one orange bokeh; two temperatures, each tied to a source.
- Board notes: two builder captions did not match their images (1392378209 is a high angle down a sewer shaft; 1445142602 is a wide Batcave silhouette, the warm backlit Batman is 1376845932). 1221872784 (a warm slatted corridor, possibly *Blade Runner 2049*) is not on this board.

---

## 7. Window light and soft side light

Board: [Window light and soft side light](https://www.cosmos.so/timmy111/window-light-and-soft-side-light)

**What it is.** One large daylight source, a window or open shutter, about 60-110 degrees off the lens axis, with the subject close to it. The light wraps the near cheek, rolls off across the nose, and lets the far side and the room fall away. The only fill is daylight bouncing off pale walls, floors and fabric. Painterly and quiet, Vermeer-like. It runs from a soft pale-room version (sheer curtain, overcast sky) to a hard chiaroscuro version (narrow opening, black room). Direct sun often adds a separate hard patch on a wall or floor.

**When to use.**
- Introspection, waiting, solitude at a window.
- Period drama and painterly portraiture.
- Intimate two-handers and quiet domestic drama that should feel unlit.
- Melancholy, longing, grief or recovery: a dark room with one opening.
- Confinement: the window as the only way out.
- Natural, analogue, expensive-looking fashion and editorial.
- Morning-after and slow-cinema moments with sheer curtains moving.

**Sources.**
- *Key:* the window, effectively 1-3 m across, at 9 or 3 o'clock (side-on) or 10-11 / 1-2 o'clock (three-quarter), at or a little above head height. Subject 0.5-2 m away: closer means faster falloff and more drama. Sheer curtains make it huge and very soft; a narrow shutter makes it smaller and harder.
- *Sun:* direct sun adds a hard trapezoid, slats or dappled pool on the wall or floor, rarely on the face.
- *Fill:* none from the lens side. Dark rooms give almost none; white rooms give a 1-2 stop lift.
- *Back/rim:* usually none. A subject sitting in the window becomes backlit (the window-seat silhouette variant).
- *Practicals:* mostly off. At most a small warm lamp deep in the background.

**Ratio and contrast.** About 4:1 in the pale-room version to 16:1+ in the chiaroscuro version. The far cheek often sits 3-5 stops below the near cheek. The window and sun patches may clip. The deciding feature is the gradient: a smooth, wide roll-off across the face, with no hard line on the skin. Deepest shadows sit furthest from the window and in the foreground nearest camera.

**Colour.** Daylight 5600-7000K, tinted by the room. North light and overcast read cool blue-teal and grey; low sun reads warm amber at 3500-4500K. A common mix: slightly warm skin against cool green-teal room shadows. Warm wood floors or red clothing add warmth back to the fill. Stay in one temperature family. A tungsten practical appears only as a small warm accent deep in the background. B&W versions show the setup is about direction and gradient.

**Motivation.** A real window, shutter, French door or glazed door. Best frames show it, or its edge: frame and mullions, a glowing or blowing curtain, an open shutter blazing white, or its shape on the wall as a sun patch. Off-screen, its direction must read from the wall gradient (bright near the window, dark away). Exterior detail may blow out but should still read as day. Dust or haze can reveal the beam. The audience should always be able to point to where the light comes in.

**Depth and space.**
- `background_far`: the window itself (brightest, often clipped, a hint of exterior) or the far wall falling to near-black. Through doorways, rooms alternate lit and unlit.
- `background_near`: the wall beside or behind the subject carries the gradient, often with a hard sun patch. A dark wall behind a lit face separates by tone alone, no rim needed.
- `subject.placement`: in the falloff zone close to the window; brightest skin in frame; lit on one side only.
- `foreground`: the darkest plane, furthest from the window: dark furniture, a door edge, a bed or chair in silhouette, or glass catching a smear of light.

**Prompt phrases.** "soft window light from the side" · "single large window as the only light source" · "natural daylight falling off across the face" · "far side of the face falling into shadow" · "no fill light, dark unlit room" · "chiaroscuro, Vermeer window light" · "sheer curtain diffusing daylight" · "patch of hard sunlight on the wall" · "dust in the window light beam" · "subject close to the window, room behind in deep shadow" · "dark foreground furniture in silhouette" · "cool daylight with warm skin tones" · "visible window frame at the edge of the frame" · "quiet, painterly interior, low-key exposure"

**AI failure modes and fixes.**
- *Flat, lit-from-everywhere room.* Fix: "only light source is the window", "no fill", "room falls into darkness away from the window", "dark foreground".
- *Face lit from the front with the window at the side.* Fix: name the side ("window at frame left, light on the left side of her face, right side in shadow"); profile or three-quarter turn toward the window.
- *Shadows disagree:* sun patches and cast shadows in two directions. Fix: one direction, repeated in the sun-patch phrase.
- *Hard specular light on skin:* a soft window rendered as a hard source. Fix: "large soft window light, gradual falloff", "through a sheer curtain"; keep hard light for wall patches.
- *Plastic skin.* Fix: "natural skin texture, pores, slight imperfections, soft grain".
- *Window that lights nothing:* a glowing rectangle behind while an invisible key lights the face. Fix: subject close to and beside the window; "the window light falls on her face and shoulder".
- *Golden hour everywhere.* Fix: neutral or cool daylight with only warm skin; warmth limited to the sun patch.
- *Video drift.* Fix: "static, consistent window light", slow moves, same window direction in every shot prompt.

**Pairs with (composition).** Frame within a frame (window, door, shutter); negative space on a big wall; profile and three-quarter close-ups toward the light; dark foreground layering; deep staging through doorways; locked-off painterly tableaux; short siding; reflections in the glass; thirds with the window on one third and the subject on the other.

**Reference frames.**
- [1615381523](https://www.cosmos.so/e/1615381523), *Girl with a Pearl Earring* (2003): Vermeer chiaroscuro, black background, no fill.
- [1351279466](https://www.cosmos.so/e/1351279466), *El Sur* (1983): narrow shutter as the only source; the hard, warm end.
- [1391073121](https://www.cosmos.so/e/1391073121), *The Handmaid's Tale* (2017): sheer curtain, haze beam, dark foreground chair.
- [99239285](https://www.cosmos.so/e/99239285): window-seat variant; dappled floor pool; darkest plane in front.
- [349107428](https://www.cosmos.so/e/349107428): short-lit profile toward an off-screen window, real black on the shadow side.
- [15171266](https://www.cosmos.so/e/15171266), *Barry Lyndon* (1975): soft low-contrast period daylight.
- [1496870235](https://www.cosmos.so/e/1496870235), B&W still: hard sun gradient on the wall, figure in soft bounce.
- [524400992](https://www.cosmos.so/e/524400992), *Doomoo*: deep staging through doorways built entirely from window light.

---

## 8. Backlight, rim and hair light

Board: [Backlight, rim and hair light](https://www.cosmos.so/timmy111/backlight-rim-and-hair-light)

**What it is.** The main or only bright light sits behind the subject, pointing toward camera. It draws a thin bright edge along hair, profile, ear, jaw and shoulders; the side facing the lens falls into shadow or silhouette. Three versions: (1) pure backlight, face fully silhouetted; (2) a rim raking from behind at 4 or 8 o'clock that also catches a sliver of cheek; (3) a hair light separating the subject from the background on top of a low frontal level. The edge makes the image; the dark front holds the mood.

**When to use.**
- Mystery or concealment: hiding who someone is.
- Isolation and introspection; quiet profile beats.
- Reverence or longing: a profile tilted up into the light.
- Golden-hour nostalgia, youth, summer: sun behind the head with flare.
- Cold-edged glamour: hair lit like a halo by a practical.
- Noir reveal of a menacing figure.
- Pulling a subject off a dark background when there is no reason for fill.
- Sensual detail inserts: neck, collar, a strand of hair.

**Sources.**
- *Key = back/rim:* between 10 and 2 o'clock with camera at 6. Directly behind gives a full halo with a dark face; offset to 1-2 or 10-11 o'clock wraps onto one cheekbone and jaw. Height at or a little above the head. Hard in almost every frame (bare fresnel, sun, bulb, window sliver): the proof is crisp individual flyaway hairs. A big window or diffused sun gives a wider, gentler glow.
- *Fill:* almost none; bounce off clothes, a wall or floor. Sometimes a very low cool ambient keeps the face readable.
- *Practicals / motivated sources:* the sun in or just outside frame, a window or curtain behind, vanity bulbs, a stage light or follow-spot through haze.
- *Haze:* part of the rig in about half the frames; makes the beam visible.

**Ratio and contrast.** Backlight to front about 8:1 to 32:1 or more; the face 4-6 stops under the edge. Studio edge-light portraits keep a truly black background. The exception: sun versions, where flare and veiling glare lift the whole frame into low contrast; milky shadows there come from flare, not fill. Rule: dark background means high-contrast graphic edge; bright sky or haze in front of the lens means low-contrast dreamy flare.

**Colour.** Warm by default: tungsten and sunset 2700-3500K make amber edges; afternoon sun 4000-5000K reads pale yellow-white. Cold version: cyan or teal backlight around 6500-9000K through blue haze (Blade Runner 2049). Mixed: warm bulbs on the hair against a cool teal fill. Keep rim and fill on opposite sides of the colour wheel, or keep the fill so dark its colour hardly matters. A warm rim and warm fill at the same level flattens the separation.

**Motivation.** Something behind the subject: low sun, a window or curtain gap, a lamp or mirror bulbs, stage lights, headlights, a doorway. Show it or its evidence: the sun in the lens, a glowing curtain, the bulbs, the beam in haze. If out of frame, imply it with haze glow on one side, flare from an edge, a bright patch in line with the rim. Pure studio edge-light on black is unmotivated: say "studio portrait" when you use it.

**Depth and space.**
- `background_far`: either crushed black (the subject floats on it) or the brightest part of the frame, where the source lives. Dark background takes a bright edge; bright background takes a dark silhouette with a glowing outline.
- `background_near`: one mid-value element (curtain, wall, mirror frame); haze between subject and background adds an aerial step and shows direction.
- `subject.placement`: separated almost entirely by the outline; the front kept dark.
- `foreground`: empty or very dark; when used, flare, a lens ghost or a dark shoulder. Flare works as a layer between lens and subject.

**Prompt phrases.** "strong backlight from behind the subject" · "glowing hair rim light, individual strands lit" · "thin bright edge light along the profile and jaw" · "face in shadow, near-silhouette" · "warm tungsten rim light against a black background" · "low-key portrait, single edge light, no fill" · "sun directly behind the head, halo of light in the hair" · "golden-hour backlight with lens flare and haze" · "cyan backlight through atmospheric haze, figure in silhouette" · "visible light beam in haze aimed toward the camera" · "hard light from behind at 10 o'clock, raking across the cheekbone" · "warm rim, cool shadow fill" · "practical lamp behind the subject lights the hair" · "glowing window behind the figure, backlit silhouette"

**AI failure modes and fixes.**
- *Rim plus a full front key:* two incompatible suns. Fix: "face in shadow", "only light source is behind the subject", "no front light, no fill".
- *Neon-sticker outline:* even rim all round, both sides. Fix: name ONE side and clock position; "the far side falls into darkness".
- *No motivation.* Fix: put the source in the prompt and, where possible, in frame.
- *Plastic skin and beauty glow.* Fix: "pores and peach fuzz catching the rim", "film grain", "slightly underexposed face"; avoid "flawless", "beautiful lighting".
- *Flat cutout or mid-grey mush.* Fix: "deep shadow on the face with faint detail from bounce"; background clearly darker (studio) or clearly brighter (sky, window).
- *Shadows and flare disagree with the source.* Fix: "shadows fall toward the camera", "flare from the top right where the sun is".
- *Hair too perfect.* Fix: "flyaway hairs backlit", "messy, individual strands glowing".
- *Uniform fog.* Fix: "light beam in haze from behind, fading off away from the source".
- *Video:* rim jumps, source moves with the subject. Fix: lock the source ("fixed sun behind, rim shifts as she turns her head"); slow head moves.

**Pairs with (composition).** Silhouette and negative space against a window, sky or haze; profile and three-quarter-back framings; frame within a frame that also motivates the light; shooting into the light with flare as a foreground layer; atmosphere for aerial depth; low-key chiaroscuro; shallow focus with backlit bokeh; low angle against the sky; thirds with subject and source on opposite thirds; tight detail inserts.

**Reference frames.**
- [1199669062](https://www.cosmos.so/e/1199669062), *Kiss of Death* still: hard warm source behind the head, face fully silhouetted.
- [287010939](https://www.cosmos.so/e/287010939), *Blade Runner 2049*: cyan backlight through heavy haze.
- [1772305431](https://www.cosmos.so/e/1772305431), *The Neon Demon*: vanity bulbs light the hair, cool teal fill.
- [386153005](https://www.cosmos.so/e/386153005): single hard warm edge from 1-2 o'clock, almost no fill.
- [730524725](https://www.cosmos.so/e/730524725): B&W hard edge from behind left on pure black.
- [1838073029](https://www.cosmos.so/e/1838073029): hard light from 10 o'clock in haze; a rim that is also a partial key.
- [1037242682](https://www.cosmos.so/e/1037242682): sun behind the head, veiling flare, low-contrast pale gold.
- [905177049](https://www.cosmos.so/e/905177049), Vimeo short: minimal warm rim on nape and collar.

---

## 9. Motivated practicals (lamps, screens, neon in frame)

Board: [Motivated practicals](https://www.cosmos.so/timmy111/motivated-practicals-lamps-screens-neon-in-frame)

**What it is.** The shaping light comes from, or plausibly comes from, a source the audience sees in frame: a table or desk lamp, oil lamp, bare bulb, phone or laptop screen, open fridge, dashboard, or neon through a window. The practical is the real key or the excuse for a hidden unit at the same angle, colour and softness. The rest of the room falls off into darkness, so pools of light and dark tell the story. The board runs from near-black single-source frames to naturalistic dim interiors (First Reformed) to saturated colour worlds (Drive, red and green motel rooms).

**When to use.**
- Night interiors that should feel lived-in, not lit.
- Isolation, insomnia, late-night work or obsession.
- Intimacy and secrets: faces leaning into a small source.
- Interrogation and noir (desk-lamp or overhead key).
- Screen-life: a face lit only by a phone or laptop.
- Night driving: dashboard glow plus city lights through glass.
- Heightened or seedy worlds tinted by neon or coloured bulbs.
- Pre-electric period: oil lamps and candles.

**Sources.**
- *Key:* the practical or a unit cheated from its direction. Lamps at table height or a little above the head, 9-10 or 2-3 o'clock, close. Small and close means soft at the shade but steep falloff: a face 30 cm away is bright, the back of the room black. Bare bulbs and clear oil lamps are hard point sources. Overhead shades give a hard cone with dark eye sockets. Screens are soft, close, low and cool, lighting only the face. Fridges are a tall soft box at waist-to-head height. Dashboards give low cool underlight; street lights through the windscreen give moving coloured edges.
- *Fill:* little or none; ambient room bounce or a dim cool night base.
- *Back/rim:* often another practical behind the subject (sign, window, hallway).
- *Practicals in frame:* bright but not a clipped blob; the shade glows, the filament or flame reads, a stop or two over the face.

**Ratio and contrast.** Low key. 8:1 to 16:1+ on faces in single-source frames; naturalistic interiors 4:1 to 8:1 with the room readable. Brightness order: practical, then face, then everything else stepping down with distance. 50-70% of the frame in shadow is correct.

**Colour.** Lamps and bulbs 2700-3200K; oil lamps and candles 1800-2000K. Screens and fridges cool or neutral (5000-7000K, cyan-blue for phones). Mixing makes the look: warm pool against a cool base, or a cool screen against warm bokeh. Saturated practicals (red bulb, green fluorescent, neon) may tint a whole room when the world is meant to feel heightened. Tie each colour to its source: warm where the lamp reaches, cool where it does not.

**Motivation.** Every bright area traces to something in the world. Show the source or its spill on a wall, table or face. Shadow direction, highlight size and skin colour must agree with it: a desk lamp lights the desk top brightest and the face from below and the side; a phone lights the face from front-below in cool light; a hanging shade lights tabletops and the tops of heads. Brightness falls off with distance. Window light, outside signs and hallway spill are secondary motivations for rim and background.

**Depth and space.**
- `background_far`: black, or a small separate practical marking distance without lighting anything (fairy lights, hallway glow, neon).
- `background_near`: the wall behind catches the key's falloff as a soft gradient. This gradient makes the room feel real.
- `subject.placement`: in the brightest pool, close to the practical, face turned toward it.
- `foreground`: a dark shape (door frame, silhouetted shoulders, dashboard and wheel) or the practical itself near camera.

**Prompt phrases.** "lit only by a table lamp in frame" · "practical lighting, motivated light source" · "warm tungsten lamp light falling off into darkness" · "single oil lamp illuminating her face, the rest of the room in shadow" · "face lit by the cool glow of a phone screen in a dark bedroom" · "bare light bulb, hard shadows, steep falloff" · "pool of warm light on the desk, dim room around him" · "warm lamp against cool blue moonlight from the window" · "teal dashboard glow, city lights through the windscreen" · "neon sign light spilling into the room" · "red bulb wash, room tinted red" · "light from the open refrigerator on his face" · "glowing lampshade, visible filament, not clipped"

**AI failure modes and fixes.**
- *Lamp in frame, face lit by an invisible softbox.* Fix: "lit from the left by the table lamp, right side of face in shadow", "only light source".
- *Room evenly exposed.* Fix: "the room falls off into darkness", "pool of light", "deep shadows in the corners".
- *Practical that lights nothing.* Fix: name the surfaces it hits ("warm light across the desk and onto his hands").
- *Wrong or multiple shadow directions.* Fix: one source and its side; avoid "cinematic lighting" and "studio lighting", which invite extra lights.
- *Practical blown to a white blob or starburst.* Fix: "glowing lampshade", "visible filament", "soft glow, not clipped".
- *Plastic skin under beauty light.* Fix: "natural skin texture, pores, film grain"; keep the shadow side dark.
- *Colour wrong for the source:* cool light from a tungsten lamp, an orange phone glow. Fix: pair each source with its colour and name the ambient colour.
- *Neon oversaturated into a uniform synthwave grade.* Fix: "neon spill on one side of the face, the rest in shadow", "motivated by the sign outside the window".
- *Video: light ignores a moving source.* Fix: "flickering flame light", "light shifts as the screen changes", "street lights pass across his face".

**Pairs with (composition).** Frame within a frame (doorways, windscreens); negative space with a small lit figure in a dark room; silhouette against a lit background; OTS with dark shoulders; close-ups leaning into the source; low or table-height camera with the lamp in foreground; practical bokeh; centred subject under a hanging lamp; locked-off naturalistic tableau.

**Reference frames.**
- [1340493413](https://www.cosmos.so/e/1340493413): B&W frosted oil lamp as the only key; soft light, steep falloff.
- [1182744566](https://www.cosmos.so/e/1182744566), *Eighth Grade* (2018): phone screen key, fairy-light bokeh.
- [1182227755](https://www.cosmos.so/e/1182227755), *Drive* (2011): dashboard glow and street lights through the windscreen.
- [1962684024](https://www.cosmos.so/e/1962684024), *First Reformed* (2017): one desk lamp pool, dark door frame in the foreground.
- [1246405430](https://www.cosmos.so/e/1246405430), *The Man Who Wasn't There* (2001): B&W hard desk-lamp key from below and the side.
- [302435366](https://www.cosmos.so/e/302435366): red lamp and warm window accents in a cool blue motel room.
- [819098336](https://www.cosmos.so/e/819098336), appears to be *The Lighthouse* (2019): one clear oil lamp between two men.
- [1704242205](https://www.cosmos.so/e/1704242205), *Breaking Bad*, "Bit by a Dead Bee" (2009): practicals layered for depth, subject dark against lit blinds.

---

## 10. Golden hour

Board: [Golden hour](https://www.cosmos.so/timmy111/golden-hour)

**What it is.** The sun within about 0-10 degrees of the horizon acts as a single low, warm key from behind or beside the subject, never from above. Three readings: (1) contre-jour backlight, hot amber rim on hair and shoulders, face lit by soft bounce, sometimes full silhouette; (2) low raking side or three-quarter key, hard and almost horizontal, long shadows, little fill; (3) afterglow, sun below the horizon, the whole sky a soft pink-orange source, faces dim and low-contrast. Haze, dust or dirty glass often diffuse the sun into a glowing wall; veiling flare is part of the look.

**When to use.**
- Nostalgia, memory, longing, "the last good day".
- Romance and tenderness: warm backlit hair, soft face.
- Endings, departures, quiet reckonings.
- Awe and smallness: silhouetted figures against a big sky.
- Unease or fragility: hard side sun on a face against a storm sky.
- Youth and summer languor: flare, haze, overexposed skies.
- Warm, real, un-lit brand and lifestyle work.

**Sources.**
- *Key:* the sun, 0-10 degrees up. Hard when clear, softened by haze, dust, glass or leaves. Behind at 11-1 o'clock gives rim, halo and silhouette. At 2-3 or 9-10 o'clock, level with the face, it rakes across one cheek. Never overhead.
- *Fill:* no lamps. Open sky opposite the sun (soft, cool), warm bounce off grass, sand, water or a white shirt, and in production a large bounce held low. Usually 1-3 stops under the rim. Sometimes none (full silhouette).
- *Back/rim:* in the backlit variant the sun IS the rim, often blooming into the face as veiling flare.
- *Practicals:* rarely. Indoors the window is the practical: sun outside, room dark, only a profile edge lit.

**Ratio and contrast.** Backlit silhouette: subject 3-6 stops under the sky, sky holds colour, rim clips. Backlit beauty with bounce: rim to face about 4:1 to 8:1, face 1-2 stops under the sky, mids milky from flare. Hard side sun: 8:1 or more, the shadow side deep. Afterglow: about 2:1, dim and soft. Shadows deep but not crushed; flare lifts blacks into a warm veil.

**Colour.** Sun 2500-3500K, amber to deep orange. Shadows lit by open sky stay cooler: pale blue-grey (6000-9000K), or dusty violet-pink after sunset. Warm light against cool shade is the look. Warm bounce off dry grass or sand can push everything to gold monochrome. Skin highlights go peach or orange, never white. No pure neutral whites in frame.

**Motivation.** The low sun. Show it: in frame, hidden behind a head or tree, flaring the lens, over water or a field, through a window. Supporting cues: long shadows toward camera or sideways, glowing backlit grass, dust or hair, a warm horizon band under a cooler sky, glitter on water, warm edges on every object on the same side.

**Depth and space.** Golden hour builds depth with atmosphere and backlight, not lamps.
- `background_far`: the sky and horizon, the brightest plane, a warm-to-cool gradient, often the sun disc or flare; distant hills soft in haze.
- `background_near`: backlit grass, water, trees or houses glow at the edges or go to silhouette.
- `subject.placement`: separated by the rim, or a dark silhouette against bright sky.
- `foreground`: the darkest plane: window frames, a horse's head, a post, a car door, tall out-of-focus grass, near-black with a warm edge.
- Order: dark foreground, rim-lit subject, glowing near background, brightest sky. The reverse of studio front-light.

**Prompt phrases.** "golden hour backlight" · "low sun behind the subject" · "warm rim light on hair" · "sun just above the horizon" · "long shadows across the grass" · "soft bounce fill on the face" · "silhouette against an orange sky" · "low raking side sunlight" · "natural lens flare" · "hazy warm atmosphere" · "warm sunlight, cool blue shadows" · "backlit grass glowing gold" · "face partly in shadow" · "sun flaring through the window" · "dust in the air catching the light"

**AI failure modes and fixes.**
- *Lit from everywhere:* sunset behind, face front-lit like a ring light. Fix: sun behind or beside; "face in soft shadow, lit by bounce" or "silhouette"; name the rim.
- *Sunset grade instead of sunset light:* orange tint with midday shadows. Fix: "sun low on the horizon", "long shadows stretching toward camera", "no overhead light", "cool blue shadows against warm highlights".
- *Shadows disagree:* sun top-left, face keyed from the right. Fix: one sun position repeated ("sun at frame left, behind her; light on the left edge of her face; shadows fall right toward camera").
- *Plastic skin.* Fix: "freckles, flyaway hair catching the light, slight film grain, soft veiling flare, lifted blacks"; let part of the face fall off.
- *Clean fake sun discs, neon skies.* Fix: "hazy, dusty atmosphere, soft veiling flare, muted warm palette, sky holds detail, film stock look".
- *Silhouettes crushed or fully detailed.* Fix: "near-silhouette, face 3 stops under the sky, thin warm edge on the profile".
- *Video:* the sun drifts or pulses; faces relight as people turn. Fix: lock the sun position in every shot; slow moves; describe how the rim changes as she turns.

**Pairs with (composition).** Silhouette against a bright horizon, subject low or off-centre; low angle against the sky; frame within a frame (windows, car windows, mullions) in dark foreground; dark out-of-focus foreground grass or posts; wide landscapes with small figures; OTS or profile close-ups toward the sun; backlit bokeh; contre-jour flare; thirds with a low horizon.

**Reference frames.**
- [1650355659](https://www.cosmos.so/e/1650355659), *To the Wonder* (2012): hard low raking sun, burnt-orange cheek, cool storm sky.
- [810094388](https://www.cosmos.so/e/810094388), *Days of Heaven* (1978): full contre-jour silhouettes against hazy orange.
- [2089251354](https://www.cosmos.so/e/2089251354), via ShotDeck: amber hair halo, face 2 stops under, real skin texture.
- [421658616](https://www.cosmos.so/e/421658616), *The Virgin Suicides* (1999): flare and milky blacks; dreamy backlight.
- [1075549359](https://www.cosmos.so/e/1075549359), *The Virgin Suicides*: backlit grass glowing gold, hair rim, field bounce.
- [920678614](https://www.cosmos.so/e/920678614), via ShotDeck: dark window frame foreground, tiny figure, sun disc far back.
- [964276859](https://www.cosmos.so/e/964276859), via MUBI: interior silhouette profile, window as practical.
- [359579257](https://www.cosmos.so/e/359579257), *Days of Heaven*: afterglow variant, dim cool faces under a pink sky.

---

## 11. Blue hour and twilight

Board: [Blue hour and twilight](https://www.cosmos.so/timmy111/blue-hour-and-twilight)

**What it is.** The 20-40 minutes after sunset or before sunrise. The sky is one huge, soft, nearly directionless source, deep blue overhead and fading to a warm band at the horizon. Its level is low and dropping, close to the level of streetlamps, windows, lamps, screens and flames, so these start to matter. The look rests on one tension: a cool, soft, low ambient filling the frame against small, hard, warm points. Three versions: pure monochrome blue ambient on skin (Moonlight); silhouette against bright sky or glass (Heat); mixed light, blue base plus one or two warm practicals carrying the story (Biutiful). Black stays a readable navy, never crushed.

**When to use.**
- Melancholy and reflection: one figure at a rail or window looking at a city.
- Endings and transitions: the last light before something changes.
- Quiet domestic unease: a house going dark with one lamp left on.
- Threat or anonymity: a silhouette in a doorway or against glass.
- Tenderness without drama: soft blue skin, no hard shadows.
- Warmth against cold: the lamp, the lighter, the laptop as the one human point.
- Calm before action: a crew under a vast dusk sky.

**Sources.**
- *Key:* usually the sky, a huge soft top-and-back source, about 10-2 o'clock high; faces toward camera read by outline. Indoors, the window: a big soft cool panel at subject height, side-back.
- *Fill:* almost none from the camera side; only blue sky bounce off pavement, water or walls, 2-4 stops under. In mixed interiors the blue window spill fills the room.
- *Back/rim:* the bright horizon or window. No added hard rim.
- *Practicals:* small, hard, warm, low: streetlamp heads 3-5 m up, table lamps at waist height throwing a shaded pool on the wall, a pendant over a table, distant lit windows, a lighter at chin height, a laptop as a cool soft key from below-front. They light only their own metre or two.
- *Last sun:* on the warm side of twilight, a hard low warm patch through a window onto a wall inside a blue room.

**Ratio and contrast.** Low-key overall with low ambient contrast (2:1 to 3:1, the sky wraps everything). Subject against sky is high: 8:1 or more, often full silhouette. Practicals are the hottest points and can bloom slightly. Shadows deep but coloured: navy or teal, never neutral black. Warm skin under a lamp about 1-2 stops over the blue room.

**Colour.** Sky ambient very cool (roughly 9000-15000K relative to a tungsten or 4300K white balance). Horizon afterglow runs orange-red to magenta to indigo in a thin band. Practicals 2000-3200K read amber against the blue. Screens are a third note, cool white to cyan around 6500K. Rule: one warm and one cool, separated in space. Warm stays in small pools near its source; cool owns the rest. Skin in a pool goes warm toward the lamp and blue toward the window. Moderate saturation; blues rich but slightly greyed in haze.

**Motivation.** The sky must be visible (above a skyline, through a window, filling a doorway) or reflected (water, wet pavement, glass). Warm light must come from a visible practical near the subject. City lights as bokeh or a dotted grid say "dusk in a lived-in place". Indoors, show the window: blue window plus amber lamps explains both colours at once.

**Depth and space.**
- `background_far`: the sky, the brightest large area, a smooth gradient darker blue at top, lighter or warm at the horizon.
- `background_near`: the city or landscape darker than the sky, a silhouetted skyline broken by warm windows, tail lights and streetlamps receding as points; haze lifts it toward blue.
- `subject.placement`: separated by shape: a dark figure against the brighter sky or window, or picked out by one warm pool.
- `foreground`: the darkest plane: railings, furniture, bed covers, branches in near-black blue, sometimes catching practical spill on top surfaces.
- Order: dark foreground, mid-dark subject, mid-dark background with warm points, bright sky.

**Prompt phrases.** "blue hour, sun just below the horizon" · "deep blue twilight sky as the only light source" · "single warm sodium streetlamp against a deep blue sky" · "figure in silhouette against the twilight sky" · "orange afterglow on the horizon fading to indigo" · "warm tungsten table lamp in a dark blue room" · "cool blue window light, warm lamp practical" · "city lights coming on in the distance" · "soft blue ambient light wrapping the skin, no hard shadows" · "face mostly in shadow, lit only by a lighter flame" · "laptop screen glow on the face in a dark room" · "low-key, deep navy shadows with detail" · "last warm sun patch on the wall of a blue room"

**AI failure modes and fixes.**
- *Softbox face with the sky behind.* Fix: "backlit by the twilight sky, face in shadow, no front fill", "silhouette".
- *Daylight exposure with a blue tint.* Fix: "low-key, underexposed, deep navy shadows, the sky is the brightest area".
- *Teal-orange smeared everywhere.* Fix: warm only in small pools tied to a named practical; the rest cool.
- *Too many lights on a lone figure.* Fix: name one source; "no rim light, no fill".
- *Practicals that light nothing, or everything.* Fix: "the light falls off within a metre, a shaded pool on the wall, the room beyond stays blue".
- *Plastic skin.* Fix: "natural skin texture, soft blue wrap, film grain, slightly soft focus".
- *Hard outdoor shadows at blue hour.* Fix: "shadowless soft skylight"; hard shadows only under practicals.
- *Sun still visible or a golden key.* Fix: "after sunset, sun below the horizon, only the afterglow band".
- *Crushed blacks or neon blue.* Fix: "muted teal-navy, detail in the shadows, moderate saturation".
- *Video: light level frozen.* Fix: a slow darkening of the sky over the shot; streetlights may flicker on.

**Pairs with (composition).** Silhouette against sky or window; frame within a frame; small figure under a big sky; OTS onto a skyline; thirds with a low horizon; dark railings, branches or furniture as foreground layers; long-lens compression of city lights; back-to-camera figures (Rückenfigur); locked-off wides; symmetric interiors around a central practical.

**Reference frames.**
- [1301050236](https://www.cosmos.so/e/1301050236), *Biutiful* (2010): teal sky, one warm streetlamp head, receding car lights.
- [1970341044](https://www.cosmos.so/e/1970341044), *MARSHA* (short): blue walls, two warm lamps, cool laptop key.
- [1090115547](https://www.cosmos.so/e/1090115547), uncredited: cool window figure, warm lamp cone on the wall, textbook layering.
- [500194916](https://www.cosmos.so/e/500194916), McNair Evans, *Confessions for a Son*: blue room with a last hard warm sun patch.
- [204647735](https://www.cosmos.so/e/204647735), *Paris, Texas* (1984): red-to-indigo band over city lights; only the cigarette is warm.
- [1834154399](https://www.cosmos.so/e/1834154399), *Moonlight* (2016): pure soft blue on skin, navy shadows with detail.
- [2009894773](https://www.cosmos.so/e/2009894773), *Heat* (1995): full silhouette against ultramarine glass.
- [1185129722](https://www.cosmos.so/e/1185129722), *Sicario* (2015): two small figures under a huge dusk sky.

---

## 12. Night exteriors, mixed colour (sodium, neon, LED)

Board: [Night exteriors, mixed colour](https://www.cosmos.so/timmy111/night-exteriors-mixed-colour-sodium-neon-led)

**What it is.** A city night where nothing seems lit by a film light. Sodium streetlights (orange), neon and LED signs (red, magenta, cyan, green), fluorescent shopfronts (green-white), headlights and tail-lights. The frame is mostly black. Colour comes in pools, each keeping its own temperature. A wet road doubles every source as a streak, so the ground reads in near-darkness. Three types: wide street plates where the sources are the image; figures silhouetted against lit backgrounds; close faces keyed by one hard coloured spill.

**When to use.**
- Urban noir, crime, heist: people moving through a city that does not care.
- Alienation in a foreign city: a face behind glass with signs sliding over it.
- Romantic melancholy and restless youth.
- Moral queasiness: green ambient with hot red or sodium on the face.
- Establishing shots that sell a place and time of night.
- Music videos, fashion or product with a contemporary LED palette.

**Sources.**
- *Key:* almost never frontal. On faces, one hard small coloured source from the side or three-quarter back, about eye height, read as a streetlight, sign or tail-light through a car window. In walk-and-talks, a hard practical top light (awning tubes, bare bulbs) rims head and shoulders. In wides, headlights are the only frontal hard light, and they flare.
- *Fill:* very little: soft cool cyan/green city spill or dim sodium haze. Unlit sides 3-5 stops down.
- *Back/rim:* sodium lights high on poles behind the subject backlight rain, steam, hydrant spray and smoke. Signage behind gives a coloured edge or silhouette.
- *Practicals:* neon tubes and LED boards; lit shop windows and kiosks as big soft boxes spilling onto pavement; headlights and tail-lights; and the wet road as a huge mirror pushing colour back up.

**Ratio and contrast.** High contrast, low overall key. Faces 8:1 to 16:1; shadow side near black with a hint of cool colour. In wides, 60-80% of the frame in deep shadow. The bright parts are small (signs, lamps, windows, reflections) and they bloom. Blacks rich and slightly tinted, never milky. Expose for the practicals; let the subject fall off.

**Colour.** Several temperatures, none corrected. Sodium 1900-2200K, deep orange; turns rain and steam amber. Old fluorescent and mercury read green-cyan on film. Neon is saturated narrow-band red, magenta, cyan or green; modern LED is the same palette, cleaner. Tungsten bulbs and tail-lights add warm-red accents. Warm against cool: usually warm on the subject or near ground, cool in the ambient and far background, or the reverse. White balance between 3200K and 4300K so sodium stays orange and fluorescent stays green. Era cue: sodium plus green fluorescent reads 1970s-90s; magenta and cyan LED with clean white headlights reads 2010s-20s.

**Motivation.** Every light belongs to the street, and its source is visible or clearly implied: the streetlight on its pole, the sign over the door, the kiosk, the headlights. When the source is off-frame (a face in a car), its colour and hardness must match one seen in the wide. Moving cars justify light sliding across faces. Rain, wet asphalt, steam, spray and exhaust are part of the lighting: they make sources visible as beams and reflections.

**Depth and space.**
- `background_far`: dark skyline, a few lit windows, hazy sodium glow, receding.
- `background_near`: where the colour lives: signs, shopfronts, rows of streetlights, often defocused into coloured bokeh. The brightest, most saturated layer.
- `subject.placement`: usually darker than the plane behind, silhouetted or edge-lit against the sign wall, in a pool or on a reflection line. In close-ups, a hard coloured side key brings the face forward.
- `foreground`: wet road with vertical colour streaks, or dark car bodies, window frames and glass carrying reflections. Dark but reflective, repeating the background colours.

**Prompt phrases.** "night exterior city street, practical light only" · "wet asphalt reflecting neon and streetlights" · "sodium vapour streetlights, orange haze" · "mixed colour temperature, warm sodium against cool fluorescent" · "neon signs in background, out of focus coloured bokeh" · "figure silhouetted against a lit shopfront" · "hard coloured side light on face from passing streetlight" · "deep black shadows, low key, high contrast" · "light spilling from shop window onto pavement" · "steam and rain backlit by streetlight" · "headlights flaring, red tail-light reflections" · "green-tinted fluorescent ambience" · "magenta and cyan LED signage in the rain" · "shot on tungsten-balanced 500T film" · "face seen through a taxi window with signs reflected in the glass"

**AI failure modes and fixes.**
- *Studio key at night:* face evenly bright and frontal. Fix: "single hard side light from a streetlight, the other half of the face in deep shadow, low key".
- *Unmotivated colour (cyberpunk filter).* Fix: name each colour with its source; keep 2-3 colours, not a rainbow.
- *Milky blacks, detailed sky:* night looks like dusk. Fix: "deep crushed blacks, most of the frame in shadow, only practicals and their reflections are bright".
- *Reflections disagree with sources;* a dry road under rain. Fix: "wet asphalt, each sign reflected as a vertical streak directly below it"; check every streak lines up.
- *Plastic skin.* Fix: "visible skin texture and pores, hard light grazing the cheek, film grain".
- *Shadows disagree:* face lit from the left, visible light on the right. Fix: source in frame on the key side; "shadow falls away from the streetlight".
- *Neutral white balance kills the split.* Fix: "tungsten-balanced film, orange sodium, green fluorescent, colours left uncorrected".
- *Legible fake sign text.* Fix: "signs out of focus, soft bokeh, text unreadable"; in video, lock sign flicker and colour.

**Pairs with (composition).** Silhouette against the sign wall; deep staging from wet foreground to signs; frame within a frame (car windows, glass doors, awnings); shooting through glass with reflections; leading lines from road markings and light streaks; small figure in a dark frame; anamorphic shallow focus with oval bokeh; low camera on wet ground; one-point perspective with a car head-on; in-car profiles with light sliding across.

**Reference frames.**
- [1622531607](https://www.cosmos.so/e/1622531607), *Thief* (1981): head-on car, wet street, signs doubled in the road.
- [1426151321](https://www.cosmos.so/e/1426151321), *Taxi Driver* (1976): hydrant spray backlit by sodium, tail-lights smeared.
- [1125368025](https://www.cosmos.so/e/1125368025), *Heat* (1995): fluorescent awning top light, red and blue neon behind.
- [954768831](https://www.cosmos.so/e/954768831), *Heat*: fluorescent kiosk as a big soft box silhouetting figures.
- [1441153235](https://www.cosmos.so/e/1441153235), *Nightcrawler* (2014): hard red-orange spill on the cheek, green ambience.
- [2028544947](https://www.cosmos.so/e/2028544947), *Lost in Translation* (2003): face behind glass, billboards reflected over it.
- [1999073432](https://www.cosmos.so/e/1999073432), *Fallen Angels* (1995): maximum mixed colour that still reads, every colour sourced.
- [2032830301](https://www.cosmos.so/e/2032830301), *Beasts Clinging at Straws* (2020): LED karaoke frontage, silhouettes, reflections on a car.

---

## 13. Overcast and soft diffused daylight

Board: [Overcast and soft diffused daylight](https://www.cosmos.so/timmy111/overcast-and-soft-diffused-daylight)

**What it is.** The whole sky becomes one huge dim softbox. Shadows almost vanish; only soft contact shadows remain under chins, brims and feet. Contrast drops, colour turns cool and muted, and the sky is usually the brightest thing in frame. The light still has a direction: strongest from above, or from whichever side the open sky or window is. That bias stops it reading as flat. Grey coasts, cold woods, Nordic flats, snow, and interiors lit only by a grey window.

**When to use.**
- Grief, numbness, aftermath.
- Austere, sober, morally serious drama.
- Folk horror and daylight dread: nothing hidden, everything wrong.
- Loneliness: a small figure in a big grey landscape.
- Naturalistic, documentary realism; faces seen honestly.
- Winter, northern and coastal settings.
- Quiet interiors, waiting, reflection at a window.
- Period pieces that should feel lived in.

**Sources.**
- *Key:* the sky, enormous and soft, about 10-2 o'clock and 60-90 degrees high outdoors. Faces get gentle top light: foreheads and cheekbones brighter, eye sockets and under-chin a stop down, no nose shadow line. Indoors the key is the window, effectively a 2-4 m soft source, falling off with distance.
- *Fill:* ground and surroundings. Snow, pale walls, sea spray give heavy fill; dark grass, forest and mud give less, so the underside goes moodier. Indoors, room bounce only.
- *Back/rim:* none as a unit. Against a bright sky or window, the subject drops toward silhouette.
- *Practicals:* usually none; lamps off in daytime. If any, tiny, dim and slightly warm.

**Ratio and contrast.** Outdoors about 1.5:1 to 2:1 on faces. Window-only interiors 2:1 to 4:1 with gentle falloff, shadows always keeping detail. True black is rare (dark clothing, deep forest, the far side of a room). The sky is the highlight, often near white; skin a stop or more below. Midtones carry the image; the palette is compressed and desaturated. Mood comes from low exposure and muted tone, not shadow shape.

**Colour.** Cool to neutral, about 6500-8000K, often graded blue-grey or green-grey. B&W versions are silvery mid-greys. No warm key. Warmth comes only from the subject (skin, a russet coat, red flannel, autumn leaves). Indoors the window is cooler than the room. Greens olive, skies pewter or white, never cyan.

**Motivation.** Weather and windows. Show the cloud lid (heavy grey sky in the top third), fog swallowing distance, wet or snowy ground, bare trees, breath, dark coats. Indoors, put the window in frame or let it bleed white at the edge. It should feel like nobody lit it.

**Depth and space.** With no shadows, depth comes from atmosphere and value.
- `background_far`: brightest and lowest-contrast; sky near white; distant hills and tree lines lifted and blued by haze. Aerial perspective does the backlight's job.
- `background_near`: walls, trunks, fences at mid value; a pale wall or dark forest gives tonal contrast.
- `subject.placement`: separated by value and colour: a dark coat against pale sky or snow, a white bonnet against dark forest, skin warmer than the field. Often small in the landscape.
- `foreground`: darker and more textured (grass, gravestones, a table edge, a soft shoulder, a wet bank).
- Interiors reverse it: brightest at the window, falling off into the room.

**Prompt phrases.** "overcast sky, soft diffused daylight" · "flat grey cloud cover, no direct sun" · "soft top-light from the sky, no hard shadows" · "only soft contact shadows under chin and feet" · "bright white overcast sky, subject darker against it" · "cool muted colour palette, desaturated greens and greys" · "low contrast, shadows keep detail" · "atmospheric haze, distant hills fading pale" · "lit only by a large grey window, soft side light falling off into the room" · "net curtains diffusing cold daylight" · "wet ground, bare trees, winter light" · "small figure in a vast grey landscape" · "dark wool coat against a pale sky"

**AI failure modes and fixes.**
- *Face brightly front-lit while the world is grey:* pasted into the weather. Fix: "the sky is the only light, soft top-light, subject darker than the bright sky, slightly shaded eye sockets".
- *Totally flat, a render not weather.* Fix: give direction ("light from above", "window light from the left"), "gentle falloff", darker foreground than background.
- *Hidden sun sneaks in:* cast shadows, golden rims. Fix: "shadowless overcast, soft contact shadows only".
- *Grey read as moody:* crushed teal-orange. Fix: "low contrast, open shadows with detail, muted naturalistic grade"; drop "cinematic dramatic".
- *Airbrushed skin.* Fix: "natural skin texture, pores, slight redness from cold, unretouched, documentary realism".
- *Blue sky with fluffy clouds or sunset glow.* Fix: "uniform pewter or white overcast sky, heavy cloud lid".
- *Extra lamps indoors.* Fix: "lit only by the window, lamps off, room darkens away from the window".
- *Postcard greens and cyan water.* Fix: "desaturated olive greens, slate-grey water, cold muted palette".
- *Video:* light shifts between frames. Fix: one sky-dome or window direction; "the light stays constant and soft throughout".

**Pairs with (composition).** Small figure in a big landscape; low horizon with big sky; static tableaux and symmetrical two-shots; frame within a frame through windows; dark foreground framing (trees, gravestones, OTS); Rückenfigur; deep staging in soft rooms; Academy 4:3 with headroom.

**Reference frames.**
- [2010417082](https://www.cosmos.so/e/2010417082), *Manchester by the Sea* (2016): white sky and spray as source and fill.
- [909443577](https://www.cosmos.so/e/909443577), *Ida* (2013): tall window as the whole lighting plan; silvery B&W.
- [1916901725](https://www.cosmos.so/e/1916901725), *Sorry, Baby* (2025): flat cloudy exterior, clapboard bounce, documentary daylight.
- [1587848176](https://www.cosmos.so/e/1587848176), *The Witch* (2015): dense cloud lid; dread in daylight.
- [270285197](https://www.cosmos.so/e/270285197), *Autumn Sonata* (1978): gravestone foreground, small figure, pale fjord behind.
- [1086490350](https://www.cosmos.so/e/1086490350), *Evil Does Not Exist* (2023): dark figure against a pale icy pond.
- [200911563](https://www.cosmos.so/e/200911563), *Children of Men* (2006): cool window spill on a three-quarter face. Caveat: weak low sun outside, so this is window soft light rather than pure overcast.
- [1539870427](https://www.cosmos.so/e/1539870427), *The Sacrifice* (1986): overcast pushed into fog; atmosphere stacks the planes.

---

## 14. Hard sunlight and dappled light

Board: [Hard sunlight and dappled light](https://www.cosmos.so/timmy111/hard-sunlight-and-dappled-light)

**What it is.** One small, distant, hard source (the sun, or a lamp standing in for it) shines through something that breaks it up: blinds, mullions, lace, leaves, palm fronds, a door frame. The pattern lands on face, body and walls as crisp light-and-shadow shapes. Three things together: one direction, edges sharp enough to read, very little fill. Two families: interior noir (blind slats or window grids raking walls, often B&W) and warm natural daylight (leaf and frond shadows on skin, street sun cutting the frame into blocks). The pattern is part of the picture and often carries a message: a cage, being watched, hiding, heat.

**When to use.**
- Noir, thriller, interrogation, paranoia: stripes cage the character.
- Moral split: a face cut into lit and unlit bands.
- Hot summer, memory, intimacy, youth: warm leaf dapple.
- Heat and exposure in hot places at noon.
- Voyeurism: eyes caught in a single lit band behind slats.
- Gothic or giallo suspense: moonlight throwing tree shadows across a bedroom.
- Shadow play: a silhouette thrown on a wall standing in for the actor.
- Graphic beauty or fashion: a lace or floral pattern on skin.

**Sources.**
- *Key:* one hard point source and nothing else. Usually 2-3 or 9-10 o'clock (60-90 degrees off the lens) and 30-50 degrees high, which makes blind stripes slope down a wall. Some frames are nearly frontal so the pattern sits square on the face.
- *Cookie / gobo:* between key and subject. Blinds give evenly spaced parallel stripes; mullions a big diagonal grid; lace a fine filigree; leaves organic blobs and round "sun coins" (pinhole images of the sun). Edges are crisp when the cookie is near the surface, softer as the gap grows.
- *Fill:* little or none, 3-4+ stops under. Many noir frames have none.
- *Back/rim:* usually absent; separation comes from the pattern and a lit wall behind a dark figure.
- *Practicals:* sometimes a lampshade in frame as a motivator, but the real key is the sun or moon from the window.

**Ratio and contrast.** Within the pattern, lit bands at or just under clip; shadow bands 3-5+ stops down: 8:1 to 16:1+, noir effectively unfilled. Colour daylight versions keep a little more detail via warm-wall bounce (4:1 to 8:1). Street versions expose for the sunlit surface and let shade go black as a compositional shape. Expose for the highlights; never lift shadows to "see the face".

**Colour.** B&W noir has no colour cue. In colour, the sun is warm (4000-4800K at golden hour, near 5500K at midday but reading warm against shade). Shadows take the opposite temperature: open shade and skylight 6500-9000K, blue-cyan. That warm-highlight, cool-shadow split inside one frame is what makes dapple read as real. Saturated surfaces in hard sun get the most intense colour, dropping sharply across the shadow edge. Night variants use cool neutral moon or streetlight.

**Motivation.** One opening onto a bright exterior: blinds, a shutter, lace, a tree or palm, a doorway, an arcade. Show the motivator or its geometry. If off-screen, the pattern must match a plausible object at a plausible distance: parallel even stripes mean blinds; organic blobs with round coins mean leaves. All shadows in frame, including the actor's cast shadow on the wall, fall the same way.

**Depth and space.** Planes separate by alternating sun and shade, not by a rim.
- `background_far`: often the brightest, most patterned surface (a raked wall, a sunlit street beyond shade).
- `background_near`: the wall behind carries the subject's cast shadow and the pattern; the cast shadow pins the actor to the space and proves direction.
- `subject.placement`: the pattern crosses the face; one lit band across the eyes or one sun coin on a cheekbone, the rest falling off.
- `foreground`: frequently a dark unlit silhouette or shaded mass (a hatted man, a column, an out-of-focus frond).
- Dark foreground, lit middle, patterned back.

**Prompt phrases.** "hard direct sunlight through venetian blinds" · "sharp parallel slat shadows across the face and wall" · "dappled sunlight through leaves on skin" · "leaf shadow pattern on face, round sun spots" · "single hard key light from a high side window" · "deep unfilled shadows, high contrast" · "window mullion shadows raking across the wall" · "lace curtain shadow pattern on face" · "subject's cast shadow on the wall behind" · "warm golden sun patches, cool blue shade" · "film noir lighting, black and white, crisp shadows" · "hard noon sun, saturated colour, black shade" · "half the face in shadow, eyes caught in a band of light" · "palm frond shadows on bare shoulders"

**AI failure modes and fixes.**
- *Pattern pasted on, not cast:* perfectly straight stripes ignoring the nose and cheek. Fix: "shadows that wrap around the contours of the face"; reject outputs where stripes ignore 3D form.
- *Lit from everywhere:* beauty fill turns dark bands mid-grey. Fix: "no fill light, deep black shadows, single hard source", "unlit side of the face falls into darkness".
- *Disagreeing shadows:* face pattern from the left, cast shadow or wall stripes from elsewhere. Fix: one direction; ask for the cast shadow on the wall; "the same stripes continue across the wall".
- *Unmotivated pattern:* leaves indoors with no window, blinds outside. Fix: name the motivator and put it in frame.
- *Plastic skin in the lit bands.* Fix: "visible pores and fine hair catching the light, film grain"; avoid "flawless", "airbrushed".
- *Everything soft:* dapple turns into blurry blotches. Fix: "crisp-edged shadows", "hard light", cookie close to the subject; soft edges only on far foliage.
- *Wrong colour logic:* all orange, muddy warm shadows. Fix: "warm golden sunlit patches, cool blue-grey open shade".
- *Over-busy pattern.* Fix: one clear band across the eyes or cheekbone; the rest of the head falls off.
- *Video:* pattern glued to a turning head, or flicker. Fix: "the stripes stay on the wall as he moves through them"; slow moves.

**Pairs with (composition).** Silhouetted foreground figure framing a lit midground; frame within a frame (windows, arches, blinds); shadow as subject; big black shade areas as compositional blocks; tight close-ups filled by the pattern; high-angle wides on bare sets with stripes as leading lines; diagonal lines from raking slats; layered depth; scope widescreen with an off-centre face against a patterned wall.

**Reference frames.**
- [461301703](https://www.cosmos.so/e/461301703), classic noir (looks like *The Big Combo*, 1955, unconfirmed): blind gobo across a bare set, silhouetted foreground figure.
- [889605048](https://www.cosmos.so/e/889605048), Hitchcock-era still: mullion grid on a staircase wall, cast shadow in agreement.
- [1788974084](https://www.cosmos.so/e/1788974084), *High and Low* (1963): one stripe angle from shutter to face.
- [338107848](https://www.cosmos.so/e/338107848), Alan Schaller portrait: stripes bending over brow, nose and lips.
- [2098352743](https://www.cosmos.so/e/2098352743), Christopher Anderson, *Pia* (2018): warm sun coins, branch shadow, cool sky.
- [1283952904](https://www.cosmos.so/e/1283952904), Eva Green portrait: lace or floral cookie on cheek and back.
- [102212008](https://www.cosmos.so/e/102212008), Alex Webb, Boquillas, 1979: noon sun splits saturated walls and black shade.
- [111871566](https://www.cosmos.so/e/111871566), *Schindler's List* (1993): lace filigree on a face, foreground hand in silhouette.

---

## 15. Firelight and candlelight

Board: [Firelight and candlelight](https://www.cosmos.so/timmy111/firelight-and-candlelight)

**What it is.** The only light seems to come from flames in frame: candles, candelabras, lanterns, torches, campfires, burning paper. Three things real flame always does: it sits low and lights from below or the side; it is small and close, so light drops off within a metre or two; and it is very warm (about 1800-2000K). Faces are lit in pools; everything else is black, or in exteriors a dim cool night.

**When to use.**
- Period drama before electricity: dinners, card tables, bedchambers.
- Intimacy and secrecy: two people across a candle, a letter read or burned.
- Dread and folk horror: one candle in a black room, a lantern into the night, torches through a forest.
- Survival and wilderness nights.
- Ritual and procession.
- Any scene where the darkness should press in and the edge of the light matters.

**Sources.**
- *Key:* the flame, or a large soft unit standing in for it. Candles are low (table height, below the chin), in front or three-quarter, often visible in the foreground. A cluster seen from a metre away acts medium-soft; a single flame close in gives a harder edge and faster falloff. Lanterns and candelabras are side keys at hand or shoulder height. Torches are high, hard, flickering points above head height. Campfires are a low, broad key from the ground. Burning paper is a very close bright source that also bounces off the page.
- *Fill:* little or none, only flame bouncing off tablecloths, plates, white shirts, paper, pale stone. Nothing from the camera side.
- *Back/rim:* no separate rim. Separation comes from other flames behind (sconces, chandeliers, a second fire, torches), or in exteriors a cool night against a warm edge.
- *Practicals:* always in frame, always the brightest thing, often clipping to near-white cores with orange halos.

**Ratio and contrast.** On lit faces about 8:1 to 16:1+; the shadow side near black with faint warm bounce. Most of the frame in deep shadow; midtones only in the pool around each flame. Steep falloff: the face behind the candle is lit, those at the table ends fade, walls barely show. Expose for lit skin; never lift the dark.

**Colour.** Flame and everything it lights at about 1700-2000K: amber, orange, copper skin, cream going gold. Do not neutralise the flame. Flame-only interiors stay warm down into brown-black. Exteriors set the warm flame against a cool night (moonlight or blue dusk, about 5600-7000K) in the sky, snow, mist or far background. The warm/cool split happens where the flame's reach ends, never as a coloured wash on the face. Haze or smoke turns torch-lit air amber.

**Motivation.** Every visible light comes from a flame in frame or just off it, and falls off with distance. Put candles in the foreground or between characters, have a character hold the lantern or torch, let the fire sit low in a corner. Background practicals say the whole space is lit this way and give the darkness depth. A lit face with no flame nearby breaks the frame. Light moves as flame does: gentle flicker in level, slight sway in shadows for video.

**Depth and space.** Flame lights in islands; depth comes from the gaps.
- `foreground`: a dark silhouette or out-of-focus shape between camera and flame, or a bright out-of-focus candle.
- `subject.placement`: the brightest skin in frame, in the main flame's pool.
- `background_near`: falls off fast into warm dark; textures only hinted where bounce reaches.
- `background_far`: black, or small distant practicals (chandeliers, sconces, a fire, torches in haze). Exteriors: a dim cool silhouette layer (thatch, trees, skyline in blue).
- Order: dark foreground, warm lit subject, dark gap, small warm points or cool silhouettes far away.

**Prompt phrases.** "lit only by candlelight" · "single candle on the table as the only light source" · "warm low-angle flame light from below" · "deep amber shadows, rapid light falloff into darkness" · "faces glowing in pools of candlelight, background falling to black" · "candelabra held beside the face, hard warm side light" · "handheld lantern casting warm light against a cool blue night" · "torchlight in a misty forest at night, amber haze" · "campfire glow on the face, no fill light" · "visible flame practicals in frame, the brightest point in the shot" · "1800K warm firelight, cool moonlit ambient" · "high contrast chiaroscuro candlelit interior" · "flickering flame light, dark room"

**AI failure modes and fixes.**
- *Lit from everywhere:* candle in frame, face evenly front-lit, back wall bright. Fix: "the candle is the only light source", "background falls to black", "no fill light", "light reaches only the nearest face".
- *Flame too dim for the face it lights.* Fix: put the flame close and say so ("candle held at chin height, half a metre from her face"); the flame core is the brightest thing.
- *Shadows disagree:* downward nose shadow from a high key with a low candle. Fix: "lit from below and to the left by the candle", "upward shadows".
- *Muddy colour:* white or pink flame, or orange tinting the night sky. Fix: "deep orange 1800K flame light" plus "cool blue moonlit ambient" for exteriors.
- *Plastic skin.* Fix: "natural skin texture, pores, fine grain, shadow side falls into darkness", 35mm look.
- *Too many candles.* Fix: state a low count ("three candles on the table"); for grand rooms, chandeliers and sconces as background points with dim walls.
- *Lifted blacks and HDR.* Fix: "crushed blacks, low-key, chiaroscuro, most of the frame in shadow".
- *Static light in video.* Fix: "subtle flicker in the light on the faces, shadows gently swaying with the flame"; tie camera and handheld flame together.

**Pairs with (composition).** Out-of-focus foreground candles with the subject behind; silhouetted foreground against a lit midground; central symmetrical table tableau; profile close-ups with black negative space; two-shots across a candle; deep staging with distant practicals; wide shots with tiny figures in a pool of light; dark trees or doorways framing the light.

**Reference frames.**
- [1575997267](https://www.cosmos.so/e/1575997267), *Barry Lyndon* (1975): textbook candle key from three low foreground candles. (The builder attached this description to 128434107; this frame is the one that shows it.)
- [2143620238](https://www.cosmos.so/e/2143620238), *Barry Lyndon*: gaming table under candelabras, sconces behind for depth.
- [128434107](https://www.cosmos.so/e/128434107), *Barry Lyndon*: wide room lit only by chandeliers, sconces and table candles.
- [1837834499](https://www.cosmos.so/e/1837834499), *The Witch* (2015): one candle lights the family, steep falloff, silhouette in front.
- [1904770697](https://www.cosmos.so/e/1904770697), *The Witch*: handheld lantern against a grey-blue night.
- [1840021059](https://www.cosmos.so/e/1840021059), *Frankenstein* (2025): candelabra at chest height as a hard side key.
- [1786437077](https://www.cosmos.so/e/1786437077), *Nosferatu* (2024): torch as a warm accent against cold blue snow.
- [78196975](https://www.cosmos.so/e/78196975), *You Won't Be Alone* (2022): single low flame carving a profile.

---

## 16. Top light and overhead single source

Board: [Top light and overhead single source](https://www.cosmos.so/timmy111/top-light-and-overhead-single-source)

**What it is.** One hard source above the subject (lamp, tube, pendant, skylight, spot) is the only real light. It lights the top planes: crown, brow, nose bridge, cheekbones, shoulders, the table surface, a pool on the floor. Everything below or beside falls to black. Eye sockets go dark unless the subject tilts up or a bounce lifts them. Two versions: the intimate pendant low over a table (Godfather, card games, interrogation), and the isolating pool, a high source throwing a hard circle on the floor around a small figure in a big dark space. The fixture is usually in frame or clearly implied, and is part of the composition.

**When to use.**
- Power, menace and secrecy: the boss, the back-room deal.
- Interrogation, judgement, tribunal: the subject under the light, others at its edge.
- Card games, conspiracies, late-night meetings: who is inside the circle.
- Isolation: a small figure in a circle inside a black void; an empty kitchen table at night.
- Paranoia in modern spaces: garages, motel walkways, gas-station canopies.
- Revelation or the uncanny: a single shaft from above.
- Hiding a character's eyes so intent cannot be read.

**Sources.**
- *Key:* at 12 o'clock, straight above or slightly in front, 60-90 degrees down. Hard: a bare bulb under a shade, a narrow spot, a ceiling cone, a tube, a high skylight. A pendant usually hangs 50-100 cm above a table; arena, hangar and garage fixtures are 5-15 m up and throw a sharp ellipse.
- *Fill:* almost none; the lit table or floor bounces up into chins and hands. Willis keeps a faint lift so eye sockets read as deep shadow, not pure black. Nothing from the camera side.
- *Back/rim:* none as a unit; the same source rims hair, shoulders and smoke of people slightly behind it.
- *Practicals:* the fixture itself, often in frame and blown out. Secondary practicals small and dim (blind window, desk lamp, distant sign). Haze or smoke shows the cone.

**Ratio and contrast.** About 8:1 (Godfather close-ups, interrogation) to 16:1+ (spotlight circle). Under-brow, nose and chin shadows at or near black. Background 4-6 stops under the key. Falloff is fast: faces 1 m from the lamp are bright, people at the table edge 2-3 stops down.

**Colour.** Classic: warm tungsten or amber, 2700-3200K, sometimes sodium orange; shadows and ambient cooler (blue-green night, teal walls). That warm pool in a cool surround is the modern colour version. Cold version: green-cyan fluorescent tubes (the All the President's Men garage), or cyan-white walls under orange strip fixtures. Haze can pick up a cooler moonlight tone. B&W: white shade, mid-grey faces, black surroundings.

**Motivation.** Something the audience believes is hanging there: a pendant over a table, a ceiling cone over an interrogation table, motel walkway fixtures, garage tubes, arena lamps, a roof opening. Show the fixture (often blown at the top edge) or its footprint: a glowing tabletop, a hard ellipse on the floor, a cone in haze. Off-frame, the lit tabletop and the shadow pooled directly under the subject must say where it is. In the Godfather the motivation is loose; the overhead direction is what reads.

**Depth and space.**
- `background_far`: black; at most a dim cool shape or one tiny warm practical for a hint of space.
- `background_near`: catches spill as a gradient fading away from the fixture (a fan of light up the wall behind the table).
- `subject.placement`: inside the pool, the brightest plane, lit on its tops, anchored by a hard shadow straight down.
- `foreground`: dark silhouettes of others (backs of heads, shoulders at the table edge), rimmed only on top. In the isolating version, simply dark floor.

**Prompt phrases.** "single overhead light source" · "hard top light from directly above" · "shaded pendant lamp hanging over the table" · "pool of light on the tabletop, room falling into darkness" · "deep eye-socket shadows from overhead lighting" · "no fill light, crushed blacks" · "warm tungsten lamp against a cold dark room" · "visible cone of light through cigarette smoke" · "lone figure standing in a hard circle of spotlight on the floor" · "shaft of light falling straight down through haze" · "overhead fluorescent tubes in an empty parking garage" · "hard shadow pooled directly beneath the subject" · "practical lamp visible in frame"

**AI failure modes and fixes.**
- *Flat front fill:* bright eye sockets under an overhead lamp. Fix: "no fill light", "eyes in shadow from overhead light", "deep shadows under the brow and nose".
- *Lit from everywhere:* the pool means nothing. Fix: "the rest of the room falls into darkness", "black background", "only the table is lit".
- *Lamp in frame that lights nothing.* Fix: "faces lit only by the hanging lamp above them", "light pooling on the tabletop beneath the lamp".
- *Shadows disagree:* sideways cast shadows; floor pool not under the fixture. Fix: "hard shadow directly beneath the figure", "circle of light directly under the spotlight"; in video, keep the shadow under the subject.
- *Plastic skin.* Fix: "textured skin, visible pores and wrinkles, film grain, unretouched, hard light raking down over the face".
- *Soft magical god-ray.* Fix: "hard-edged shaft", "sharp-edged pool", "thin haze", "no lens flare, no bloom".
- *Colour drift:* one grade on everything. Fix: name both temperatures, or "green-tinted fluorescent overhead, no warm light".
- *Video:* light moves with the camera, eye shadows vanish on head turns. Fix: "fixed ceiling lamp", slow moves, repeat "eyes stay in shadow".

**Pairs with (composition).** Centred symmetry under the fixture; huge negative space with a tiny figure in a pool; dark foreground heads framing the lit centre; one-point perspective down repeated fixtures; fixture as an anchor at the top edge; high angle into the pool; slow push-in with eyes kept in shadow; empty table space between two figures to show distance.

**Reference frames.**
- [41357070](https://www.cosmos.so/e/41357070), *The Godfather* (1972): colour Willis top light, brow shadow over the eyes, blinds behind.
- [1041254781](https://www.cosmos.so/e/1041254781), *The Godfather*: B&W version on the board. (The builder's 642615223 is not on the board.)
- [2112813370](https://www.cosmos.so/e/2112813370): B&W noir card game under one pendant; falloff by stops with distance.
- [1554435811](https://www.cosmos.so/e/1554435811): colour poker game, warm shade, cool beam in smoke. (The builder noted it as B&W; it is colour.)
- [771177231](https://www.cosmos.so/e/771177231): interrogation table, hard wedges up the back wall.
- [1453452203](https://www.cosmos.so/e/1453452203): tiny figure in a spotlight ellipse, everything else black.
- [715557809](https://www.cosmos.so/e/715557809), *All the President's Men* (1976): green-cyan garage tubes; the cold modern version.
- [455826691](https://www.cosmos.so/e/455826691): hard warm shaft through haze in a hangar, sharp floor pool.

---

## Cross-cutting rules for every shot

### 1. One clear, motivated key

- Every card names exactly one key: what it is in the world, which side of frame, how high, how big (hard or soft). Fill, rim and practicals are described relative to it.
- The key must be something the world explains: window, lamp, sun, sky, screen, sign, flame, fixture. Put the source in frame, at the frame edge, or prove it with its footprint (a sun patch, a pool on the table, a cast shadow, a beam in haze).
- If a second light is used, give it a job and a source ("rim from the hallway bulb behind"), and keep it clearly weaker than the key, except in backlit setups where the rim is the key.
- Never write "cinematic lighting", "studio lighting", "well lit" or "beautiful lighting" on their own. They invite an invisible softbox and three extra lights.
- Say what stays dark. In 14 of the 16 setups, most of the frame is darker than the subject's face.

### 2. Light direction continuity across cuts

- Inside a scene, the key stays on the same side of frame for every shot on the same side of the 180-degree line. If the window is frame-left in the wide, the faces are lit from frame-left in the singles.
- When the camera crosses to the reverse, the key moves to the opposite side of frame because the world has not moved. Write it as "key from the window, which is now frame-right".
- Anchor the source to the set, not to the face: "fixed window on the left wall", "pendant over the table centre", "sun low behind the barn". Repeat the same anchor phrase in every shot of the scene so models without memory between shots rebuild the same light.
- Keep time of day, sun height and colour temperature constant unless the script changes them. Blue hour darkens over time and golden hour sun drops: if a scene spans time, plan the drift and write it into each card.
- Ratio continuity: a scene shot at 8:1 should not cut to a 2:1 close-up unless the story calls for it.
- Practicals in a wide must be the same practicals lighting the close-ups, with the same colour and the same side.

### 3. Mixing colour temperatures

- One temperature dominates the frame; the second appears only where a named source puts it.
- The key decides the skin colour. Ambient and background take the complementary temperature at a much lower level.
- Separate warm and cool in space, not on the same surface. Warm stays in the pool of its source; cool owns what the source does not reach. The split happens at the edge of the source's reach.
- Never give the fill a third hue, and never fill the shadow side of a face with a saturated second colour unless a practical on that side motivates it.
- Pair every source with its colour in the prompt: "warm tungsten lamp", "cool blue phone light", "orange sodium streetlight", "green fluorescent shopfront", "1800K candle".
- Leave sources uncorrected. Sodium stays orange, fluorescent stays green, flame stays deep orange. A neutral white balance kills the split.
- Avoid a global teal-and-orange grade as a substitute for motivated colour. It puts orange in shadows and teal on skin.

### 4. Using light to separate depth planes

Light, not sharpness alone, is what separates planes in these frames. Four patterns recur, and every card should commit to one:

| Pattern | Foreground | Subject | Near background | Far background | Setups |
|---|---|---|---|---|---|
| Dark-light-dark | dark silhouette or shape | brightest, in the pool | falls to black | black or one small accent | Rembrandt, split, low key, practicals, top light, firelight |
| Dark-lit-bright | dark frame or shape | rim-lit or silhouetted | glowing edges | brightest (sky, window, haze) | backlight, golden hour, blue hour, window-seat |
| Dark-lit-patterned | dark mass | crossed by the pattern | cast shadow and pattern | brightest patterned wall or sunlit street | hard sun / dappled |
| Bright recedes | clean or slightly darker | dark accent against pale | one step down | brightest, often clipped | high key, overcast |

- Fill each depth field with a value word as well as content: "`world.foreground`: dark out-of-focus door frame", "`world.background_far`: one warm lit window, otherwise black".
- Use the near background as the place that proves the source: a gradient on the wall, a sun patch, a cast shadow.
- Use haze, smoke, rain or dust when you need the beam or the planes to read. Atmosphere is a depth layer.
- `subject.interaction` should say how light from the place lands on the subject: "lamp light on her hands and the left cheek", "neon spill on one side of the face", "sun coins on his shoulder".
- For `world.parallax`, moving through alternating light and dark planes (a dark foreground sliding past a lit midground) reads as depth far better than an evenly lit move.

### 5. Avoiding the flat, evenly lit, too-perfect AI look

Models default to four habits. Each has a standing counter.

- **Lit from everywhere.** Counter: one named source, "no fill" or "low fill", and a sentence about what falls into darkness.
- **Lifted, milky shadows (HDR).** Counter: "deep shadows", "crushed blacks" for low-key setups; "shadows keep detail but stay dark" for soft setups. Ask for falloff.
- **Patterns painted on rather than cast.** Counter: describe the cause (source position and size), not the result. Check that the pattern bends over the face and matches the cast shadows.
- **Plastic, airbrushed skin.** Counter: "natural skin texture, visible pores, fine lines, film grain" on every card with a face. Avoid "flawless", "perfect skin", "ultra-detailed", "HDR", "beautiful lighting". Hard light especially must show texture.
- Use `light_look.finish` for the imperfections that make light feel real: "slightly uneven motivated light", "highlights bloom gently", "real-lens character", plus the setup-specific ones (backlit flyaway hairs, peach fuzz catching the rim, soft veiling flare, flicker in flame light).
- Prefer slight underexposure. Real low-light frames sit dark; models expose everything as if for a catalogue.
- Review rule: if you cannot point to the source of every bright area in a frame, reject it.

---

## Proposed rule changes for shotcraft

**Status: applied** (see CHANGELOG, Unreleased). Where each part went:

- A, vocab: added to `rules/taxonomy.json` `light_look`, with the new `neon lighting` gloss and the
  `direction` help asking for a side or position.
- A, negatives: the `flat_light` group in `rules/negatives.json`, added by the compiler through
  `applies_when` on low-key family setups only (not high key or overcast). Reworded: the order is "flat
  lighting", "lifted shadows", "rim light on both sides", "evenly lit", "softbox", "beauty lighting", "HDR",
  so the three the compiler adds say different things; their rewrites trim first (priority 5), before the
  card's practicals and texture. See `skills/prompt-craft/references/negatives-system.md`.
- A, presets: done as `rules/light_setups.json` (16 setups from the chooser), not as `presets.json` entries,
  because presets are per use case, not per light.
- B, cinematographer: in `agents/cinematographer.md`. Changed: the scene light plan is written by the
  director in the shot list, copied word for word by the production designer into the environment file's
  Light section (`Scene light plan (scene <n>):`), and copied from there onto every card. Logging it with
  `sc lessons add --kind project` is optional.
- C, continuity: light rows in `agents/script-supervisor.md` and checklist items DR-C04, DR-C10 to DR-C16
  (`drafts.md`), FI-10 (`finals.md`), BI-C14 and BI-C15 (`bible.md`).
- D, prompts checklist: PR-21 to PR-36 in `skills/producer/references/checklists/prompts.md`, and the light
  notes in `templates/prompt-card.md`.

### A. `rules/taxonomy.json`, `light_look` vocab

**`setup`: add terms**

| term | means |
|---|---|
| short-loop lighting | key on the far side of a three-quarter face, small nose shadow; moody |
| Paramount lighting | hard key on the lens axis, high; crisp butterfly shadow, hollow cheeks |
| top light, pendant pool | shaded lamp over a table; faces lit from above, room black |
| spotlight pool | hard circle of light on the floor around a small figure |
| window chiaroscuro | one window, subject close to it, room in deep shadow |
| contre-jour sun | low sun behind the subject; rim, halo or silhouette |
| afterglow | sun below the horizon; the whole sky as a soft back source |
| blinds gobo | hard sun through venetian blinds; stripes on face and wall |
| dappled sunlight | hard sun through leaves; organic shadows and round sun spots |
| candlelight | candle flames as the only light; low, warm, fast falloff |
| lantern light | handheld flame as a warm side key against a cool night |
| torchlight | high, hard, flickering flame light, often in haze |
| screen glow key | face lit only by a phone or laptop; cool, close, from below-front |
| dashboard glow | low cool underlight in a car at night |
| streetlamp backlight | street lamp behind the subject; silhouettes, long shadows toward camera |
| mixed night street light | sodium, neon and fluorescent pools, each keeping its colour |

**Change one existing gloss:** `neon lighting` currently says "often magenta and cyan". Proposed: "coloured light from a visible neon or LED sign; keep each colour tied to its sign". This stops the unmotivated cyberpunk wash flagged on the night-exterior board.

**`quality`: add terms** `crisp-edged shadows` (hard source, sharp terminator) · `gradual roll-off` (big soft source, wide gradient across the face) · `shadows go to black` · `shadows hold detail` · `veiling flare` (sun in or near the lens lifting the blacks) · `visible beam in haze` · `pool of light` · `flickering`.

**`direction`: add terms** `high side key` · `on-axis high` (butterfly) · `eye-height side` (split) · `rim from behind left` · `rim from behind right` · `from below (flame)` · `sky from above and behind` · `key on far side (short)` · `key on near side (broad)`. Also propose that `direction` must always include a side or a position (left, right, behind, above, below).

**`color_temp`: add terms** `low sun 2500-3500K` · `oil lamp 1800K` · `blue hour sky` · `phone screen cyan` · `LED magenta and cyan` · `warm key, cool shadows` · `warm pool, cool surround`.

**`practicals`: add terms** `oil lamp` · `bare bulb` · `lantern` · `torch` · `candelabra` · `chandelier` · `wall sconce` · `open fridge` · `dashboard` · `vanity mirror bulbs` · `fluorescent tubes` · `shop window` · `lit distant windows` · `lighter flame` · `venetian blinds (as source shape)`.

**`finish`: add terms** `faint shadow-side bounce, never fill` · `backlit flyaway hairs` · `peach fuzz catching the rim` · `soft veiling flare` · `gentle flame flicker` · `slight underexposure`.

**`palette_grade`: add terms** `uncorrected practical colours` · `navy shadows with detail` · `brown-black firelit shadows`.

**Negatives (`rules/negatives.json`) for light:** add a light group for low-key setups: "evenly lit", "flat lighting", "softbox", "beauty lighting", "rim light on both sides", "lifted shadows", "HDR". Apply it only when `setup` is low-key, split, Rembrandt, short, practicals, top light, firelight or night exterior.

**Presets (`rules/presets.json`):** consider one light preset per setup, filling `setup`, `quality`, `direction`, `color_temp`, `practicals` and a `finish` default from the chooser row in this guide.

### B. Cinematographer agent (`agents/cinematographer.md`)

- Read this guide alongside the composition guide when writing `light_look`.
- **One-key rule:** every card names one key with its world source, side of frame, height and hardness. Fill, rim and practicals are written relative to it.
- **Cause, not pattern:** write the source position and size; do not ask for "Rembrandt triangle" or "blind stripes" without the source that casts them.
- **Name the dark:** every card except high key and overcast states what falls into darkness and which planes stay dark.
- **Depth values:** fill each depth field with a value word (dark, lit, bright accent, clipped), using one of the four depth patterns above.
- **`subject.interaction` for light:** say what the source does to the subject (which cheek, which hands, what colour).
- **Colour pairing:** every source in `practicals` carries its colour temperature, and the card states the ambient colour.
- **Skin texture:** every card with a face includes natural texture wording in `finish` and avoids "flawless", "perfect", "HDR", "beautiful lighting".
- **Setup fit:** check the chosen setup against the "when to use" and "do not use" lines (for example, butterfly is wrong for gritty documentary; split is wrong when both eyes must read).
- **Scene light plan:** before the first card in a scene, write one line naming the anchored sources ("north window on the left wall, one table lamp right of the bed, blue hour outside") and reuse that anchor phrase in every card of the scene. Record it with `sc lessons add --kind project` so later stages keep it.

### C. Continuity checks (script-supervisor, light direction across shots)

Add light rows to the continuity table built before judging:

1. **Key side per shot:** from the card and from extracted frames, record the key side (frame-left, frame-right, behind, above). Flag a change within a scene unless the camera has crossed the line (then the side should flip) or the script moves the source.
2. **Nose and cast-shadow direction:** in each frame with a face, check that the nose shadow, neck shadow and any wall or floor cast shadow fall away from the same source. Flag mixed directions.
3. **Source present and consistent:** the practical or window that motivates the key appears in the wide (or is named in the scene light plan), with the same colour and side in the close-ups.
4. **Ratio band:** classify each shot as soft (about 2:1), drama (about 4:1) or hard (8:1+). Flag jumps inside a scene the script does not ask for.
5. **Colour temperature per source:** warm stays warm, cool stays cool; flag a source changing colour between shots, and flag teal-orange grades replacing motivated colour.
6. **Time-of-day drift:** golden hour sun height and blue hour sky level move in the planned direction only.
7. **Reflections and patterns:** on night exteriors, puddle streaks sit under their sources; on blinds and dapple, stripe angle matches across face, wall and the next shot.
8. **Video stability:** in drafts, flag keys that move with the head or camera, patterns glued to faces, and exposure pumping.

### D. Prompts checklist (prompt-craft skill and `templates/prompt-card.md`)

Add a "Light" block to the checklist run before handover:

- [ ] `setup` chosen from the chooser row that matches the shot's intent.
- [ ] One key named with its world source, side, height and hard/soft.
- [ ] `direction` contains a side or a position, never only "cinematic".
- [ ] The source is in frame, at the frame edge, or proven by a footprint in a depth field.
- [ ] Each practical carries its colour; the ambient colour is stated.
- [ ] What stays dark is stated (except high key and overcast).
- [ ] Every depth field has a value word, and the planes follow one of the four depth patterns.
- [ ] `subject.interaction` says where the light lands on the subject.
- [ ] Skin texture wording in `finish` on every card with a face; banned words absent ("flawless", "perfect skin", "HDR", "beautiful lighting", "studio lighting" outside studio work).
- [ ] The anchor phrase from the scene light plan is repeated word for word.
- [ ] Key side matches the previous shot in the scene, or flips correctly across the line.
- [ ] Setup-specific failure modes from this guide checked (for example: triangle closed at the bottom; butterfly shadow straight down; split line on the nose bridge; rim on one side only; reflections under their sources).
- [ ] For video: the source is fixed to the set, moves are slow, and any flicker or drift is described on purpose.
