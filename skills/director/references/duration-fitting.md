# Duration fitting

Durations are exact. The shot list holds the length each shot **plays in the edit**. The generation is slightly
longer (handles) and fitted to the lengths each model allows. Never generate longer than needed: video credits
scale with seconds.

## 1. Fit the shots to the delivery

- The delivery length comes from the job card (Delivery line) and the preset's `duration` (typical, min, max).
- The `duration_s` values must add up to the delivery length, within 0.5 s.
- Fit in this order: the beats first (hook, setup, turn, payoff, CTA), then the shots inside each beat.
- If the script runs long, cut a shot or a beat before squeezing every shot. Under 1 s a shot rarely reads,
  except for flash cuts that are the style.
- End cards and logo holds count toward the length. Hold the last frame at least 1 s.

## 2. Handles

- Handles are extra seconds at each end so the editor can trim and add transitions. The preset sets `handles_s`
  (for example 0.5 s for social, more for b-roll inserts that go into someone else's edit).
- Generated length needed = `duration_s + 2 x handles_s`.
- Stills (`kind: image`) have no handles; their `duration_s` is the hold time in the edit.

## 3. Fit to what the model allows

Models allow either a list of lengths (for example 4, 6 or 8 s) or a range (for example 4 to 15 s). Check the
current limits live; they change:

```
sc.py route --use-case <use case or need> --tier draft --kind video --duration <duration_s>
```

It adds the handles and picks, for each candidate model, the shortest allowed length that covers the shot. It
shows the length per candidate, and a plan when one take is too short. When you compile a card
(`sc.py card compile`), the compiler fits the length again for the exact model and reports any adjustment.

How to read the result:

| case | what to do |
|---|---|
| The needed length is allowed | Use it. |
| Between two allowed lengths | The next longer one; trim in the edit. A 2.5 s shot on a 4/6/8 s model is a 4 s take. |
| Shorter than the model's minimum | Use the minimum and trim. Short shots on a model with a 4 s minimum still cost 4 s. Group very short shots so that one take can serve two cuts when the action allows. |
| Longer than the model's maximum | Pick a model with a longer maximum, or split the shot into two takes (`S040A`, `S040B`) joined on a cut, a match cut, or an end frame -> start frame chain. Mark both image-first. |

## 4. Speed changes

- Slow motion: models generate at normal speed. A 50% slow-down needs a take twice as long as the screen time
  (or a model or utility that interpolates frames). Plan the take length from the screen time x 2.
- Speed ramps and fast motion: generate at normal speed and retime in the edit; note it in the shot list.
- Frame rate is not a generation setting on most models. The delivery frame rate is set in the edit.

## 5. Dialogue, voice-over and music

- A spoken line sets the minimum length: count about 2.5 words a second (calm) to 3 (fast), plus 0.3 s of air.
- Lip-synced shots must cover the whole line in one take; check the model's maximum before writing the line.
- With music, round shot lengths to the beat grid: one bar in 4/4 = `240 / BPM` seconds.

## 6. Write the rationale

For each video shot, the card's `rationale.duration` should say, in one line: the edit length, the handles, the
model length chosen and why (for example "2.5 s in the edit + 0.5 s handles each side = 3.5 s; model allows
4-15 s, so a 4 s take, trimmed in the edit").
