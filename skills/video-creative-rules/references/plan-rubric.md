# Plan rubric and storyboard

Read the source before answering: the confirmed brief, the footage or captures,
the product's own copy (landing page, README, in-app text), its palette and type,
and its audio if it has any. Prefer the product in use over the product describing
itself.

## The nine questions

Answer all nine in writing before storyboarding.

1. **What is this?** One sentence. What it does or claims to do.
2. **What is the one line that earns a reaction?** The source's own words. Not a
   summary of them.
3. **What is the visual hook?** The strongest real image: a UI moment, a frame of
   footage, a palette moment. Not the logo.
4. **What must be shown from the real thing?** Which screen, clip or copy carries
   the cut. If it can be captured from the running product, capture it.
5. **What is the shortest satisfying cut?** Would 15 seconds land it? 20? What is
   the minimum for the claim or the lesson to land.
6. **Which workflow and voice?** The brief's workflow template
   (references/tone-presets.md) plus a one-phrase creative direction for this cut,
   for example "a lantern-lit tour of a colony that actually works".
7. **What should the audio feel like?** Role (warm bed, sparse accents, cinematic
   support, silence as a choice), music candidate and its rights status, SFX
   posture.
8. **What is the share caption?** One sentence in the brief's voice.
9. **What is the flow worth showing?** The two or three beats a real user goes
   through: entry, key action, result. Not the landing page's section list. If the
   source has no flow, write "no flow" and name what carries the cut instead.

## Bias toward the flow

If question 9 found a flow, the centerpiece scenes show that flow. Stat rows, hero
blocks and taglines may frame it, at most one of them, never replace it.

Good: "Upload screen, cursor drops a file, the filename appears, progress fills in
1.2s." Good: "The lift rail steps 01 to 04 while the room dissolves behind it."
Avoid: "A diagram of what the product does." Avoid: "Three stat cards."

## Sequential reveals and simulated interaction

Before writing scenes, ask: what can arrive one by one, and what action can be
simulated? Feature rows, results, profile cards, a cursor clicking, a swipe, text
being typed. Commit to them explicitly in the scene ("three rows arrive 1.5s apart
and hold together"). Vague scenes get vague motion.

## Rights lines

Every music track, SFX file and image in the plan gets one line:

```
forge-theme.ogg: product's own asset, ElevenLabs-generated, commercial terms not audited, already shipped publicly by the product
```

Public distribution of an asset whose status is unknown is a human decision.
Say so in the candidate summary rather than deciding it.

## Storyboard template

```
# Plan: <title>

What is this: ...
Angle: ...
Hook: ...
Key moments: ...
Landing: ...
Flow: entry -> key action -> result
Workflow: <interview|lesson|announcement|demo|revision>; direction: <phrase>
Format(s): <portrait|landscape|square> at <width>x<height>
Duration: <seconds>
Visual identity: background, text, accent, display font, body font, strongest element
Audio: role, music (+ rights line), treatment, cue source, reactive treatment, SFX posture
Rights: one line per asset

## Scene N: <name> (<start> to <end>)
On screen: ...
Text: "<line>" settled <from> to <to>  (one entry per line)
Sequential / interaction: ...
Audio intent: ...
Transition: ...
Text budget: <sum of floors> of <scene length> (<percent>)
```

Save the machine-readable version as `storyboard.json` (format in SKILL.md) and run
`scripts/check-reading-time.mjs` on it before the plan is called done.
