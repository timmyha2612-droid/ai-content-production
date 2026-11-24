# Camera movement cookbook

One move per shot, named plainly, with a speed. That is the rule that saves the most credits. This page
lists the moves in `rules/taxonomy.json` (camera.movement), what each one says to the viewer, when to use it,
wording that renders, and how models tend to get it wrong.

Write the move in the card's `camera.movement` and the speed in `camera.movement_speed`. Put direction and
end point in the move ("slow dolly in, ending on her eyes"). With a start frame, the move plus the subject's
motion is the whole prompt.

## Speeds (camera.movement_speed)

| Term | Use for |
|---|---|
| very slow, slow, drift | Calm, luxury, contemplation, product reveals. Safest for clean renders |
| steady, real time | Neutral coverage, documentary |
| fast, rapid, snap | Energy, sport, social hooks. More artefacts: keep the shot short |
| ease in, ease out, ease in-out | Moves that start or stop gently; reads as "operated", not robotic |
| linear | Mechanical, motion-control feel |
| speed ramp, slow motion | Action beats. Cinema Studio 3.0 / 3.5 have a `speedramp` parameter: use it instead of words |

## The moves

### Still

| Move | Says | Use when | Wording that renders | Watch for |
|---|---|---|---|---|
| static shot / locked-off tripod | Observe, let the action speak | The subject moves a lot; dialogue; product hero | "locked-off tripod shot, static frame" | Models add drift: add the `locked_off` avoid category |
| motion control / tabletop slider | Precise, premium | Products, food | "smooth motion-control slide left across the bottles" | Keep the distance small |

### Rotate in place

| Move | Says | Use when | Wording that renders | Watch for |
|---|---|---|---|---|
| pan left / pan right | Reveal what is beside, follow across | Landscapes, following a walker | "slow pan right across the harbour" | Fast pans smear; keep slow unless it is a whip |
| tilt up / tilt down | Scale, height, reveal top to bottom | Buildings, people head to toe | "slow tilt up from the boots to her face" | Name start and end |
| whip pan | Energy, a transition between beats | Social hooks, transitions | "whip pan right to the next scene" | Use as a transition at the start or end of a shot |
| roll | Disorientation, dream, action | Music videos, fantasy | "camera slowly rolls 90 degrees" | Easily turns into morphing; short shots only |

### Move through space

| Move | Says | Use when | Wording that renders | Watch for |
|---|---|---|---|---|
| dolly in / push-in | Focus, importance, tension | A realisation, a product hero | "slow dolly in toward the ring on the table" | The most reliable move on most models |
| dolly out / pull-out | Reveal context, loneliness, ending | Ends of pieces, reveals | "slow pull-out revealing the empty stadium" | New content appears at the edges: describe it |
| truck left / truck right | Travel alongside, parallax | Shelves, street fronts | "camera trucks left past the shopfronts, steady" | Say "camera" so the subject does not slide instead |
| tracking shot / lead shot | Follow or lead a moving subject | Walking, running, vehicles | "tracking shot following the cyclist from the side" | Keep the subject's speed and the camera's the same |
| pedestal up / down, crane up / down, jib arm, boom shot | Rise into scale, descend into the scene | Openings, endings, establishing | "crane up from the market stalls to reveal the city" | Long cranes take time: 5 s or more |
| arc shot / orbit / 360 orbit | Hero moment, admire a subject | Products, a character's turn | "slow 90-degree orbit around the sneaker" | Faces and products warp on full 360s: use 90-180 degrees and image first |
| Steadicam / gimbal | Smooth immersion, following through spaces | Walkthroughs, real estate | "smooth gimbal walkthrough into the kitchen" | Good on Seedance and Kling; describe the path |
| handheld | Urgency, documentary, intimacy | UGC, drama, behind the scenes | "handheld, subtle natural sway" | Too much becomes shake: say "subtle" and add a motion guard |
| snorricam | Character-locked unease, intoxication | Music videos, thrillers | "snorricam rig, camera locked to his chest as he stumbles" | Hard for most models; image first |

### Lens moves

| Move | Says | Use when | Wording that renders | Watch for |
|---|---|---|---|---|
| zoom in / zoom out | Attention without moving (feels like a lens, not a body) | Observational, retro | "slow optical zoom in on the window" | Models often dolly instead; accept it or say "optical zoom" |
| crash zoom / snap zoom | Shock, comedy, punch | Hooks, reactions | "sudden crash zoom onto his face" | Short shots only; pair with a beat |
| dolly zoom | Vertigo, a realisation | One key moment per piece | "dolly zoom: the background stretches away while she stays the same size" | Many models fail it; describe the effect, use image first, keep it 3-4 s |
| rack focus | Shift attention between planes | Two subjects at different depths | "rack focus from the glass in the foreground to the man behind" | Name both planes in order |

### Aerial and special

| Move | Says | Use when | Wording that renders | Watch for |
|---|---|---|---|---|
| drone flyover / drone reveal | Scale, place, opening | Locations, real estate, travel | "drone rises over the ridge to reveal the valley at dawn" | Altitude and direction help |
| aerial top-down | Pattern, graphic design of a place | Crowds, roads, food from above | "top-down aerial view, camera slowly rotating" | Keep it simple: one slow rotation or one slide |
| FPV drone | Speed, thrill, flowing through spaces | Action, sport, showreels | "FPV drone dives down the cliff face and skims the water" | High artefact risk; short, image first, check physics models |
| bullet time | Frozen moment, spectacle | One hero beat | "bullet time: the splash freezes as the camera arcs around it" | Rarely clean; Cinema Studio's camera styles or a board help |
| hyperlapse | Travel through time and space | City, journeys | "hyperlapse moving forward along the busy street" | Not every model gets the time compression |
| timelapse | Time passing, locked-off | Clouds, crowds, sunsets | "locked-off timelapse, clouds racing over the peaks" | Pair with a static camera, not a move |

## Matching move to purpose

| The shot must | Reach for |
|---|---|
| Hook in the first second | crash zoom, whip pan, fast push-in, FPV |
| Reveal a place | drone reveal, crane up, pull-out |
| Make a product feel premium | slow orbit (90-180 degrees), slider, slow push-in, locked-off with moving light |
| Build tension | very slow push-in, static with a held beat, dolly zoom (once) |
| Feel real and personal | handheld (subtle), tracking at eye level |
| End the piece | pull-out, crane up, static hold on the end card |

## Combining moves

Do not, in one generated shot. If the story needs "orbit then push in", make two shots and cut, or use the
one move that matters. Exceptions that read as one move: "dolly in with a slight crane up" and "tracking shot
with a slow pan" usually render as one gesture; still check the take.

## Lens and angle partners

- Wide lens (14-24 mm) plus a push-in exaggerates speed and depth: energy.
- Long lens (85-200 mm) plus a truck gives strong parallax and compression: premium, cinematic.
- Low angle plus crane up: power and scale. High angle plus pull-out: smallness, loneliness.
- Macro plus slider: product and food detail.

## Platform notes

- Vertical (9:16): moves along the vertical axis (tilt, pedestal, crane) use the frame's height well; wide
  pans lose their sides.
- Loops: the last frame must match the first. Use a static camera or a full, even orbit, and add the `loop`
  avoid category. Plan an end frame equal to the start frame where the model takes one.
