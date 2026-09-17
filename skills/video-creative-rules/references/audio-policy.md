# Audio policy

Include audio by default: one bed and a few well-placed cues. Silence is a choice
the plan makes on purpose, never a default.

## Levels are starting points; loudness is the standard

Author gains so the mix sits right relative to itself, then let the delivery gate
normalize the whole render (references/delivery-gates.md). Do not chase loudness
with clip gains.

| Element | Starting gain | Notes |
| --- | --- | --- |
| Music bed | 0.30 to 0.40 | quiet or restrained beds 0.15 to 0.25; never above 0.50 |
| SFX | 0.55 to 0.85 | softer for polished or quiet cuts; nothing above 0.85 |
| Voice | 1.0 | bed ducks to 0.12 to 0.15 under speech and returns after |

Put the bed on a low track. Give each overlapping cue its own track; two cues on
one track may not overlap in time. Every audio element has an id.

## Prefer the product's own sound

If the product has its own music, cues or voices and the rights line allows it,
use them. They are the most specific choice available. A library bed is the
fallback, not the default.

## Moment to sound

| Moment | Sound family | Note |
| --- | --- | --- |
| Sequential items | card slide or place, soft drop | accent the first, last or strongest, not every one |
| Big reveal or payoff | one short announcement cue (bell, soft impact) | one, brief |
| Typed or popping text | randomized key taps, soft drop | thin out when copy is dense |
| Simulated user action | click, select, switch | must match the visible action |
| Success or landing | bell, chime, the product's own completion sound | positive, once |

Fewer cues with better timing beat a grab bag of cute sounds. Keep one sonic
palette per cut. Align a cue to the start of the motion it supports, not the end.

## Curating a library

Analyze every SFX file once (spectral centroid, high-frequency energy weighted by
level and duration, envelope shape, transient sharpness, duration) and record a
high-frequency risk of low, medium or high. Use low and medium risk for repeated
or polished moments; save high-risk bright files for tiny isolated accents. Keep
the analysis beside the library and regenerate it when the library changes.

## Audio-reactive visuals: content, not medium

Audio supplies timing and intensity; the visual vocabulary comes from the story.
Pre-extract per-frame RMS and band energy; sample it per frame on the same paused
timeline as everything else. No runtime analysis, no Web Audio at render.

- Good: warmth swells with bass, contrast sharpens with treble, a lantern glow or
  a card's presence breathes with RMS.
- Never: waveforms, equalizer bars, musical-note clip art, generic particles,
  rainbow cycling, strobing on beats.
- Text scale variation stays within 3 to 6%. Backgrounds and shapes may swing
  10 to 30%.

## Restraint

No stingers, risers or whooshes on every cut. If the edit is already busy, drop
cues rather than add them. When in doubt, the quieter version.
