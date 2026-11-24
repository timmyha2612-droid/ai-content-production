# Coverage and pacing

Notes for planning shots that cut together, hold attention and stay within what AI video models do well.

## Every shot has one purpose

Name what the viewer must get from the shot. Common purposes:

| purpose | what it does | typical shot |
|---|---|---|
| hook | stops the scroll in the first 1 to 2 s | a striking close detail, motion in frame from frame one, a question |
| establish | where and when we are | wide or extreme wide, slow move |
| inform | the fact or product feature | medium or close, clean background, steady camera |
| emotion | how it feels | close-up on a face or hands, shallow depth of field |
| proof | shows it working | insert, POV, before/after |
| transition | carries the eye to the next idea | whip, match cut, push through, end frame that matches the next start |
| payoff | the hero moment | the most considered shot, often the longest |
| call to action | what to do now | logo or product with space for text added in motion graphics |

If two shots have the same purpose in a row, cut one, or give it a different job.

## One main action per shot

AI video models handle one clear action and one camera move well. Two actions in sequence ("she picks up the cup,
turns, then smiles") often fail or blend. Split them into two shots, or keep the second for a later shot.

## Size progression

- Vary shot size from cut to cut: wide to medium to close, or close to wide for a reveal. Two cuts at the same size
  and angle on the same subject look like a mistake (a jump cut) unless that is the style.
- Move closer as the emotion rises; open up for the payoff or the end.
- Inserts (hands, product details, textures) are cheap insurance: short, simple, easy to generate, and they cover
  a cut that doesn't work.

## Pacing by format (average shot length, a starting point only)

| format | average shot | notes |
|---|---|---|
| social vertical (reel, story, TikTok) | 1 to 2.5 s | hook in the first 1.5 s; captions and safe zones matter |
| ad, 15 to 30 s | 1.5 to 3 s | the product appears early and at the end |
| YouTube long form b-roll | 3 to 5 s | under a voice; follow the sentence, not the beat |
| cinematic or brand film | 3 to 6 s | longer holds, slower moves |
| b-roll insert for an edit | 3 to 5 s plus handles | match the edit's frame rate and aspect |
| logo animation | 3 to 6 s total | one idea, ends on a clean hold of at least 1 s |

Music sets the grid when there is a track: one bar at a given BPM lasts `240 / BPM` seconds (4/4 time). At
120 BPM a bar is 2 s, so cuts land on 1 s, 2 s or 4 s. Voice sets it when there is narration: about 2.5 words a
second for a calm read, 3 for a fast one.

## Continuity for AI shots

AI models don't remember the previous shot. Continuity has to be planned:

- **Recurring people and products**: flag them for the bible and for image-first. Approved stills become start
  frames or references, so the look carries over.
- **Screen direction**: if something moves left to right in one shot, keep it left to right in the next, or show
  the turn. Write the direction in the continuity column.
- **Light and time of day**: one light direction and colour temperature per scene. Write it once in the
  continuity column; the bible's `look.md` will repeat it.
- **Match cuts and seamless joins**: plan the end frame of shot A as the start frame of shot B. Mark both shots
  image-first and note "ends on the frame S050 opens on".
- **Loops**: the last frame must match the first. Needs a model with an end frame; mark it image-first.

## Coverage in AI production

There is no camera crew shooting extra angles, so coverage means:

- **Variants** on risky shots (2 takes at the draft tier) instead of extra angles everywhere.
- **A spare insert** per scene that could cover a failed shot.
- **Stills first** where a wrong guess is expensive.
- **The user's own material** where it is better than a generation: a real product shot, a real location, a
  Blender render used as a start frame. Mark it in the `source` column.

## Things that cost more and fail more

Readable text in the picture, logos, hands doing precise tasks, many people interacting, fast complex moves
(orbit plus crane plus focus pull), long continuous takes (over 8 s), crowds, and mirror reflections. Keep them
few, short and image-first, or move the text and logos to motion graphics.
