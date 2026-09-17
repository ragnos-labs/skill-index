# Beat policy

Music cues bias timing. They never control it. Story, readability and pacing win
every conflict.

## Cue sources

Get a cue source before locking anything:

- A precomputed cue file for the track (tempo, `beats[]` with intensity,
  `strongCues[]` with `kind` of `strong_beat` or `onset_peak`).
- A beat detector over the chosen track (for example `hyperframes beats`, which
  writes a beat grid with a per-beat `strength` but no strong-cue array; derive
  strong cues from the highest strengths).
- Nothing. Then write "cue guidance unavailable, natural timing" in the plan and
  move on. Do not pretend to sync.

## Double time

Detectors often report double the authored tempo (an 80 BPM track reads as 160).
Check the detected tempo against the track's own record or against a bar count by
ear. Lock to the authored pulse; use the finer grid only for accents.

## Tolerances

| Event | Snap to | Within | How many |
| --- | --- | --- | --- |
| Major reveal (hook image, hero card, wordmark) | a strong cue | 0.15s | one to three per cut |
| Small entrance (label, glow, accent) | the nearest beat | 0.10s | as many as feel natural |
| Sequential readable lines | every other beat or slower | 0.10s | never consecutive beats under 1.2s apart |

Scene cuts land on bar or half-bar lines when the music has a clear bar; a cut on
the wrong half of a bar reads as sloppy even when nobody can say why.

## Mark the locks

Write every lock into the plan and into the composition source where the timing
lives, so review can diff intent against the build:

```
// beat-locked: 18.384s (wordmark; detected beat, strength 0.70)
// beat-grid: rows at 12.384 / 13.884 / 15.384 (every 4th detected beat, 1.5s)
```

## What beat sync is not

It is not audio-reactive motion (references/audio-policy.md); that breathes with
energy, this lands on time. It is not a reason to reveal text faster than the
reading floor (references/reading-time.md). It is not a claim of exact sync when
no detector ran.
