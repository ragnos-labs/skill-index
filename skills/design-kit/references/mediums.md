# Mediums and routes

The kit directs every medium below. It produces websites, product UI,
components, static graphics and carousels itself. For the others the Director
still writes the direction and the design pack, and production goes to the
method that owns that medium on the host. "Report the gap" is the answer only
when the host has no such method; name the missing method once and continue the
parts that do not depend on it.

| Medium (pack `deliverable.kind`) | Producer and method | Review evidence |
| --- | --- | --- |
| `website`, `landing_page`, `product_ui`, `component` | Builder; "Web and React" in [production.md](production.md) | Three widths, primary action, states |
| `static_graphic`, `cms_asset` | Maker or builder; "Static marketing graphics" in [production.md](production.md) | Full resolution and intended viewing size |
| `carousel` | Maker or builder; "Carousel" below | Every slide, read in order at phone size |
| `video`, `motion_graphic` | The host's video composition method or the owner's video project tool; "Video and motion" below | Frames over time, audio, captions |
| `document` | The host's document or slides method; "Documents and decks" below | Every page rendered |
| `brand_kit` | "Brand kit" below, with [brand-record.template.md](../assets/brand-record.template.md) | Tokens applied to two real surfaces |
| `copy` | The host's marketing copy role or copy skill; "Copy" below | Claims checked against sources |

A campaign is several deliverables under one direction. Write one pack per
deliverable kind and share the brief, brand block and direction across them.
Review the set together as well as each piece: one voice, one type system,
one image treatment.

## Landing pages

A landing page has one audience, one offer and one action. Before layout, the
pack states the offer in one sentence, the objection the page must answer and
the proof available. Copy comes from the copy route below, not from the
builder. Review adds: the action is visible without scrolling at 390 pixels,
every claim on the page is in `claims`, and the form or link works.

## Carousel

A carousel is one argument in a fixed number of frames, not several posters.

1. Write the sequence first: the cover's promise, one point per slide, and the
   last slide's action. Each slide carries one idea and the fewest words that
   carry it.
2. Fix the system on the cover: grid, type roles, image treatment and where a
   page marker or continuation cue sits. Later slides vary content inside that
   system; they do not introduce a new layout without a reason.
3. The cover must stand alone in a feed at phone size. The second slide must
   reward the swipe.
4. Keep text inside the platform's safe area and away from interface overlays.
5. Export every slide at the pack's size with ordered file names, and keep one
   editable source for the set.

Review reads the slides in order at phone size, then each at full resolution.
A finding names the slide number.

## Video and motion

The kit writes the direction; the host's video method owns timelines, renders
and audio. Do not build a video by hand inside this kit.

The pack states the format and length, the first two seconds (what holds a
viewer with the sound off), the beat list with the words on screen for each
beat, the type and colour roles from the brand record, the motion character
(how things enter, hold and leave, and how fast), captions and their safe
area, the audio source, and the end card. Footage, quotes and music are
`client_asset` or `brand_asset` resources with their rights; every spoken or
on-screen quote is in `claims`.

Hand the pack to the video method with the brand record. Ask for a still of
the hardest frame before the full render. Review samples frames across the
whole length, checks reading time for every text beat, watches once with sound
and once without, and checks the first frame as a thumbnail. Follow the video
method's own review and loudness rules where it has them.

## Documents and decks

State the reader, the decision the document serves and the page count. Build
the page system first (grid, type roles, running elements), then one content
page, one data page and the cover, and review those before the rest. Use the
host's document or slides method for the file format. Review renders every
page; a page that only repeats the previous page's layout with more text is a
finding.

## Brand kit

A brand kit is a brand record a person or an agent can design from without
asking. Fill [brand-record.template.md](../assets/brand-record.template.md).
Take values from the owner's existing material first, as in "Brand from an
existing site" in [brand-sources.md](brand-sources.md); propose new values
only for named gaps and mark each one proposed until a person confirms it.
Prove the record on two real surfaces of different kinds (for example one page
section and one graphic) before delivery. A delivered kit includes the record,
the token file, the logo files as supplied, the two proofs and short reuse
instructions.

## Copy

The kit never writes final copy. Route copy to the host's marketing copy role
or copy skill with the brief, the audience, the offer and the client's own
source material. Draft copy returns with a `claims` entry for every quote,
testimonial, statistic and factual claim. Copy and visual are recommended
together; a visual built around placeholder words is not ready for review.
