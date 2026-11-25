# Depth planes and the natural finish

Two things make a generated frame look generated: a subject pasted flat in front of a backdrop, and a
picture that is too clean to be real. This page covers the fix for each.

## Part A: depth planes

### The idea

Build the frame like a multiplane set-up in classic cel animation: painted layers stacked at different
distances from the camera. The gaps between them read as depth. Given only "a woman in a cafe", a model
puts her in front of a flat wall; given the layers, it puts her inside the place.

### The planes (card fields)

| Plane | Field | What it is for | Typical content |
|---|---|---|---|
| Far background | `world.background_far` | Sets the wider world. Often soft, hazy and slow | Sky, skyline, hills, the far end of a street |
| Near background | `world.background_near` | Gives the place its identity, just behind the subject. Can hold several layers itself | Shopfront, back wall, bar shelves, a lit doorway |
| Midground | `subject.placement` | Where the subject stands: which plane, which part of frame, what is around them | "seated at the window counter, left third" |
| Foreground | `world.foreground` | What sits between camera and subject. Usually out of focus. What makes a frame feel shot rather than generated | Rain on glass, a cup edge, leaves, a doorframe |
| Depth motion | `world.parallax` | How each plane moves and how fast (video only) | "foreground slides past faster than the background" |

Plus `subject.interaction`, which ties the subject to all of them (below). Vocabulary and help for each
field: `rules/taxonomy.json` (lookup command in `taxonomy-guide.md`).

### How the compiler writes them

- The planes become one **depth sentence**, after the world sentence and before camera, in this order:
  far background; background; midground; foreground; depth motion. Parts are joined with "; ".
- Each part is labelled ("far background: ...") so the model knows where it goes, unless your text already
  names the plane (for example it contains "foreground" or "in the distance").
- `subject.interaction` prints in the subject sentence, right after the action.
- Image cards skip `parallax`.
- With a start frame (image to video, motion only) the static planes are dropped, because the frame
  already shows them. `interaction` and `parallax` stay: they describe what changes over time.
- If `world.environment` is set but none of foreground, near background or far background is, the compiler
  warns "No depth planes". Fill at least a foreground and one background.
- Trim priorities (higher is kept longer): placement 75, interaction 73, foreground 67, background_near 61,
  background_far 53, parallax 49.

### Worked example: rainy night cafe (video, 5 s, 9:16)

```json
"subject": {"subject": "a woman in her 30s in a dark wool coat",
            "action": "wraps both hands around a cup and looks out at the street",
            "placement": "seated at the window counter, left third",
            "interaction": "neon spill on her cheek, steam from the cup curling past her face"},
"world":   {"environment": "small corner cafe at night", "weather_season": "steady rain",
            "background_far": "blurred city lights",
            "background_near": "rain-streaked shop signs across the street",
            "foreground": "raindrops on the window glass",
            "parallax": "foreground drops slide past faster than the street behind"}
```

Compiled (subject, world and depth sentences):

> A woman in her 30s in a dark wool coat, wraps both hands around a cup and looks out at the street, neon
> spill on her cheek, steam from the cup curling past her face. Small corner cafe at night, steady rain.
> Far background: blurred city lights; background: rain-streaked shop signs across the street; midground:
> seated at the window counter, left third; foreground: raindrops on the window glass; foreground drops
> slide past faster than the street behind.

The parallax part has no label because it already says "faster", which names the motion.

### Parallax rules

- **Near moves faster than far.** On a truck, dolly or crane, the foreground slides past quickly, the near
  background slower, the far background barely moves. Say it in that order.
- **It needs a camera move or moving things.** On a locked-off shot, parallax is motion inside a plane:
  rain in the foreground, traffic in the background, a still subject.
- **One idea, matching the camera field.** "Foreground wipes across the frame" is enough. "Planes
  separate as the camera pushes in" needs a push-in in `camera.movement`.

### Subject and environment: interaction patterns

Models get this wrong most often; a subject that ignores its surroundings looks pasted in. Write it as
physical cause and effect:

| Pattern | Examples |
|---|---|
| Light from the place on the subject | neon spill on the face, window light across the face, firelight flicker on skin |
| Weather and air on the subject | wet hair, rain beading on the jacket, breath fogging in the cold, coat moving in the wind |
| Contact with the world | footprint in a puddle, hand on misted glass, leans on the counter with real weight |
| The subject changes the place | splashes, dust kicked up by each step, casts a long shadow across the floor |
| Scale | small against the street, dwarfed by the architecture |
| Props and people react | steam from the cup drifting past the face, crowd parts around them |

One or two per shot. Pick the one the audience would notice if it were missing.

## Part B: the natural finish

### What makes a frame look too perfect

Spotless sets, mirror-symmetric faces, airbrushed skin, everything sharp, flat even light, stock-photo
posing, and audio that drops to dead silence between cuts. Real cameras and places never produce that. The
fix is a little controlled imperfection, not lower quality: resolution, a sharp subject and clean motion
all stay.

### The finish field

`light_look.finish` holds real-world imperfection: lived-in wear, motivated light, real-lens behaviour
(slight vignetting, gentle focus falloff, highlights that bloom a little), slight handheld life.

- **Fill it** for live-action looks.
- **Leave it empty** for clean graphics, icons and products that should look pristine.
- Presets carry a `finish` setting, and the taxonomy holds one default per value (`defaults`):
  - "natural" (social-vertical, social-square, social-landscape, youtube, youtube-short, broll-insert):
    "subtle real-world imperfection: lived-in detail, real-lens character".
  - "true_to_life" (real-estate): "true-to-life colour, slightly uneven motivated light, real-lens
    character". No wear and no lens softness: a home for sale should look real, not worn.
  - "clean" (thumbnail, icon-ui, logo-animation, web-hero, banner-ad, product-shot, storyboard-animatic,
    billboard-print, presentation): no default; the field stays empty.
- On natural and true-to-life presets `sc card new` fills `finish` from the default and adds "cgi look" and
  "too perfect" to `avoid`.
- The defaults do not ask for asymmetry. When `camera.composition` asks for symmetry (symmetry, centred,
  centre-punch), the compiler drops any asymmetry wording from the finish and the "perfect symmetry" guard,
  and warns. A symmetric frame you asked for wins over the generic finish.
- Trim priority 47: below the depth planes (a plane you wrote outranks the generic finish), above texture
  and practicals.

### The too_perfect guards

`negatives.json` `by_category.too_perfect`, each with a positive rewrite (see `negatives-system.md`):

| Avoid term | Positive rewrite |
|---|---|
| cgi look | photographed on a real camera, real-world materials |
| too perfect | subtle real-world imperfection |
| airbrushed skin | natural skin texture with visible pores and fine lines |
| perfect symmetry | natural, slightly asymmetric composition (dropped when the composition asks for symmetry) |
| sterile spotless set | lived-in set with small signs of use |
| hyper-sharp everywhere | natural depth of field, softer edges away from focus |
| flat even lighting | motivated light that falls off naturally |
| stock-photo posing | candid, unposed moment |

Add only the ones that fit the shot; two or three is plenty.

"blurry" is focus-aware. On a shallow-focus shot (a natural or true-to-life finish, or a depth of field or
plane that says shallow, bokeh, soft or out of focus) it is rewritten through `blurry (shallow focus)` as
"sharp focus on the subject", not "tack-sharp focus, crisp fine detail", which would fight the soft
background.

### The grain clash rule

If `light_look.texture` or `finish` asks for grain or film stock (grain, film stock, 35mm, 16mm, super 8,
halation), the compiler drops the "noise", "grain" and "film grain" avoid guards and warns. A
"noise-free" guard would fight the look you asked for.

### In post: texture and room tone

```bash
sc finish texture 08_assembly/reel.mp4 --grain subtle --out 08_assembly/reel_tex.mp4
sc finish roomtone 08_assembly/reel_tex.mp4 --out 09_delivery/<slug>_<preset>_<WxH>_v1.mp4
```

Chain them: `texture` writes a work file outside `09_delivery/` (here `08_assembly/`), then `roomtone` runs on that file and writes the
final file into `09_delivery/`. Paths are relative to the current directory. Without `--out`, finish refuses
a file inside `09_delivery/`: work files left there fail the delivery check.

- **texture** adds fine film grain at one matched strength (use the same setting on every shot of a job,
  so cuts do not jump) and an optional mild vignette. The setting (`off`, `subtle` or `film`, vignette yes
  or no) is decided at intake and recorded on the job card as `Grain:`; the producer passes it to the
  delivery agent. With grain off and no vignette, skip texture. The re-encode keeps the codec family:
  H.264 stays H.264 (CRF 14); ProRes becomes ProRes 422 HQ, and ProRes 4444 stays 4444 with its alpha
  kept. The grain and vignette filters work in 8-bit, so a 10-bit source is filtered at 8-bit precision.
  JPEG and WebP stills are written at high quality. Audio is copied untouched.
- **roomtone** is a single-bed safety floor. The per-scene room tone and ambience beds are laid by the sound
  stage in the mix or the assembly. If a deliverable still fails the digital-silence check, roomtone lays one
  bed under the whole file at a very low level (dBFS, decibels below full scale): generated pink noise, or
  one neutral `--bed` (it loops). The picture is copied untouched.

### The silence check

`sc delivery check` fails a file whose audio has stretches of pure digital silence (below -90 dB for 0.5 s
or longer) and lists the time ranges. Fix: a missing scene bed goes back to the sound mix; as a safety
floor, `sc finish roomtone` lays one bed under the whole file. Real
recordings never fall to absolute zero; silence between cuts sounds dead even when viewers cannot say why.
A preset or the project's delivery block can set `"allow_digital_silence": true` to skip the check.

A second check fails a file whose audio is shorter than its picture: the end would play in dead silence.
Fix the mix length or the export, not the room tone.

### What the finish is not

The natural finish is a craft fix for a natural look. It is not a way to get past AI detectors, and it
never crops, blurs or covers a watermark. Content Credentials (C2PA) do not survive an edit or an ffmpeg
re-encode (the finish pass included), so the disclosure is the platform's AI label: realistic AI content
still needs it when posted. The delivery note (`09_delivery/delivery-notes.md`, written by the delivery
agent) always carries that AI-label line for realistic AI content, whether or not the finish ran.
