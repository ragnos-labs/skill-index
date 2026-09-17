# Reading time

Pace is allowed to be high. Text is not allowed to be unreadable. Those are
different things, and the second is measured.

## The floor

A text element must be fully settled on screen (entered, not yet exiting) for at
least:

| Kind | Definition | Floor |
| --- | --- | --- |
| label | three words or fewer | 0.8s |
| line | four words or more | 0.3s per word, minimum 1.2s |

Entrances and exits stay fast (0.3 to 0.6s). The floor is measured between them.
The hook line gets more than its floor, because it is read while the viewer is
still deciding to watch.

Examples:

- "Tiny ants." -> label -> 0.8s
- "Four rooms. One colony." -> label (three words are not the rule; four words are a line) -> 1.2s
- "Real work you can follow and review" -> 7 words -> 2.1s
- "Play the free mini game. No account. No email." -> 9 words -> 2.7s

## The scene budget

Sum the floors of every required text in a scene. That sum may use at most 85%
of the scene's length; the rest is motion, footage and air. Over 85% is a
warning, over 100% is blocking. When a scene is over budget, cut copy or split the
scene. Never speed up reveals to fit.

A footnote or a HUD label that a viewer may skip is marked `optional: true`. It
still has to be readable on its own (its floor is checked, warning only), but it
is not required reading, so it does not count toward the budget or the spacing
rule. Marking a headline optional to make a budget pass is a lie the review will
catch on the frames.

## Sequential text

Lines revealed one after another need at least 1.2s between reveals. Beat grids at
110 BPM and above put beats about 0.5s apart, which is fine for glows, dots and
ticks and wrong for readable lines. Snap lines to every other beat, or reveal them
quickly and then hold the whole set on screen for the longest line's floor.

## The two failure modes

1. **Too much text for the scene length.** A 4.5s scene lands two or three short
   reads at the floor, not six. The fix is the copy, not the timing.
2. **Sequential text snapped to a fast beat.** Rows arriving every 0.5s outrun
   reading. Hold each to the floor, or hold the set afterwards.

## The check

```sh
node scripts/check-reading-time.mjs storyboard.json          # human readable
node scripts/check-reading-time.mjs storyboard.json --json   # review findings
```

Findings use Studio's review finding shape with `modality: visual` and
`category: brief`. Under the floor is a warning; under half the floor is blocking.
The command exits 1 on any blocking finding. These are brief findings: they ask the
human for a copy or timing decision. They are not technical repairs.
