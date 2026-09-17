---
name: video-creative-rules
description: Creative rules and gates for a Video Studio cut. Read before planning a cut from a confirmed brief, before revealing text or syncing to music, and before preparing an export. Owns what good looks like (rubric, reading-time floor, beat and audio policy, delivery gates); it never decides direction, chooses a final or approves a preference.
---

# Video creative rules

The confirmed brief owns direction. The human owns every creative decision. Studio
owns revisions, exact export and review evidence. This skill owns the rules the
production agent applies in between, and the checks that turn those rules into
review findings.

## Who decides what

| Layer | Owns | Never |
| --- | --- | --- |
| Confirmed brief | audience, goal, constraints, required formats, workflow template | timing, copy, music |
| Production agent (this skill) | angle, storyboard, copy, timing, music and SFX selection, cue locks, poster frame | confirming a brief, choosing a final, approving a preference, publishing |
| Studio | revision ledger, exact export, sampled visual and audio review, repair scope | creative judgment |
| Human | every creative decision, the final, reusable preferences | nothing is inferred from silence |

If a rule below conflicts with the confirmed brief, the brief wins and the conflict
is reported in the candidate summary. If a rule conflicts with a human instruction,
the instruction wins.

## The laws

1. **Short.** The cut is as long as the brief's deliverable needs and not one scene
   longer. A launch or announcement is 15 to 25 seconds. A lesson segment is as long
   as its one idea. Every scene must earn its place.
2. **Readable.** Pace comes from motion, cuts and light, never from pulling text
   before it can be read. Every line holds for its floor (references/reading-time.md).
   Fast in, then hold. Never fast in, then gone.
3. **Specific.** The cut must feel made for this exact product, person or lesson.
   Use the source's own words and claims. No copy that could belong to any video.
4. **Show the real thing.** At least one scene carries real footage, real UI or real
   copy from the source. Real frames beat recreations: capture the running product
   first, recreate only chrome. Abstract filler, stock motion and color washes are
   not scenes.
5. **The hook is the first two seconds.** Plan the hook before anything else. It is
   an image, a line or a motion, and it decides whether the rest gets watched.
6. **Restraint over decoration.** No stingers, risers, whooshes on every cut, lens
   flares, particles or visualizer graphics. Sound and motion support the story.
7. **Honest.** No claim beyond the brief and the source. Keep the source's own
   caveats when it has them. Every music, SFX and image in the plan carries a
   source and a public-distribution status.

Shape to start from, not a template: hook (2 to 3s), reveal (2 to 4s), two or three
highlights (5 to 12s), landing (2 to 4s). Adapt it to the brief's workflow
(references/tone-presets.md).

## The three gates

### 1. Plan gate (after confirmBrief, before the first edit)

Read references/plan-rubric.md. Then:

- Answer the rubric, including question 9 (entry, key action, result). If the
  source has no flow, write "no flow" and say what carries the cut instead.
- Commit to one angle and one hook.
- Write the storyboard with, per scene: what is on screen, every text line with its
  settled window, sequential or simulated interaction, audio intent, transition.
- Compute each scene's text budget (references/reading-time.md) and cut copy until
  every scene fits.
- Write a rights line for every music, SFX and image asset.
- Save the storyboard as `storyboard.json` in the work directory and register it
  with `register_artifact`. Run `scripts/check-reading-time.mjs storyboard.json`.
  A blocking finding means the plan is not done. Studio runs the same check on
  that file when it prepares a review, so its findings reach the human either way.

### 2. Cut gate (before requesting an export)

- Re-run the reading-time check against the timings you actually built.
- Beat locks: at most three strong-cue locks, marked in the plan with their time
  (references/beat-policy.md). Sequential readable lines never land on consecutive
  beats.
- Audio mix inside the policy (references/audio-policy.md); the game or product's
  own audio is preferred when its rights line allows it.
- Every reading-time or budget finding is either fixed or listed in the candidate
  summary with a reason. Findings are `category: brief`, so they need the human,
  not an unattended repair.

### 3. Delivery gate (export and handoff)

Read references/delivery-gates.md. Loudness is normalized to the target, the
poster is a settled frame baked as frame 0, each required format is planned as a
reframe with its own text budget, and the share copy is one caption in the
brief's voice.

## Files

| File | Read it to |
| --- | --- |
| references/plan-rubric.md | answer the nine questions and write the storyboard |
| references/reading-time.md | apply the floor, the budget and the two failure modes |
| references/beat-policy.md | lock reveals to music without hurting reading |
| references/audio-policy.md | set bed and SFX levels, choose cues, keep reactive visuals honest |
| references/delivery-gates.md | normalize loudness, pick and bake the poster, derive formats, write share copy |
| references/tone-presets.md | pacing, type and transition vocabulary per brief workflow |
| scripts/check-reading-time.mjs | turn the storyboard into review findings |
| scripts/loudness-gate.mjs | two-pass loudness normalization that keeps the video stream |

The storyboard format the checker reads:

```json
{
  "scenes": [
    {
      "id": "s2",
      "start": 3.0,
      "end": 7.5,
      "texts": [
        {
          "id": "s2-card",
          "text": "Ada planned it. Tuck built it. Pip checked it.",
          "kind": "line",
          "settledStart": 4.05,
          "settledEnd": 7.5
        }
      ]
    }
  ]
}
```

`settledStart` is when the text is fully in; `settledEnd` is when it starts to
leave. `kind` is `label` (three words or fewer) or `line`; it is inferred when
omitted. `optional: true` marks text that is not required reading (a footnote, a
HUD label): it is still checked against its own floor, but it does not count
toward the scene budget or the sequential spacing rule.
