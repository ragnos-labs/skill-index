# Delivery gates

Run these on the exact export, in this order. Each one is mechanical.

## 1. Loudness

Target -16 LUFS integrated, -1.5 dBTP true peak, two-pass linear normalization so
the mix's internal balance survives. Social platforms normalize down but never up:
a quiet render stays quiet on a phone.

```sh
node scripts/loudness-gate.mjs render.mp4 delivered.mp4 -16 -1.5
```

The video stream is copied untouched. The last line of output is a JSON report
with before and after measurements; record it with the export. A voice-led lesson
or interview may target -14 LUFS when the brief's platform asks for it; say which
target was used.

## 2. Poster frame

The poster is what every idle player and thumbnail grabber shows. Pick the
strongest settled beat (text fully in, before it exits), never frame 0 of a fade
or a mid-transition frame. Extract it at full resolution, then bake it as frame 0
of the delivered file so platforms that regenerate thumbnails from the first
frame show it too:

```sh
ffmpeg -ss 2.6 -i delivered.mp4 -frames:v 1 -q:v 2 poster.jpg
ffmpeg -y -i delivered.mp4 -i poster.jpg \
  -filter_complex "[0:v][1:v]overlay=0:0:enable='eq(n,0)'[v]" \
  -map "[v]" -map "0:a" -c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p \
  -c:a copy -movflags +faststart delivered.poster.mp4
```

At 30 fps the poster is visible for one frame, which is imperceptible on
playback. Keep `poster.jpg` beside the file for platforms that accept a custom
thumbnail.

## 3. Formats

Each required format in the brief is a reframe with its own storyboard entries,
not a crop of the landscape cut. Portrait halves the usable width, so text
budgets shrink and stacked lines replace side-by-side ones; the reading floor is
unchanged. Re-run the reading-time check per format.

## 4. Share copy

One caption, one to three sentences, postable as is, in the brief's voice, using
the source's own claim. No "excited to share". Variants for specific platforms go
in a separate file if the brief asks for them.

## 5. Candidate summary

The handoff names: what changed, why it serves the brief, every open reading-time
or budget finding with its reason, every asset whose rights status needs a human,
the loudness report, and the decision being asked for. A ready review is not
approval; a passed gate is not a final.
