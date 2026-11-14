# Brand sources

A team that designs only from outside references produces competent
templates. The owner's own brand specification, tokens, components and
approved assets set the direction; outside references fill a named gap.

## Resolve the brand before choosing a direction

Do this before choosing the direction or making the first render.

1. Name the brand the deliverable belongs to. One deliverable has one brand.
   If the assignment does not make the brand clear, ask; never blend brands.
2. Look for the brand's own design skill through the host's skill index
   (search for the brand name with "design" or "brand"). A brand owner
   may keep one with its design system, for example a `SKILL.md` beside
   its brand specification, with its own read order.
3. If the index has a match whose load mode allows loading, read its required
   files in its stated order. If loading needs explicit authority, report the
   match and ask. If the brand skill routes this surface to a different brand
   skill, use that one instead and record only it.
4. If the index has no match, look in the working project for a design
   record, a brand specification, token files, a component catalog or
   registry, preview pages and an assets folder. Use what exists.
5. If neither exists and the owner has live pages, make the record from
   them as in "Brand from an existing site" below. Only when there is no
   brand skill, no project record and no existing material, record the brand
   as `none` and proceed from the assignment's supplied assets. Do not invent
   brand values or borrow another brand's.

Order of authority on brand matters, highest first: the CMS client record
(brand values, learned corrections, client scope) for a CMS asset; then the
brand skill or project brand files; then this kit's defaults; then outside
references. A brand skill adds the owner's tokens, components and assets; it
does not override what the CMS records for that client.

## Brand from an existing site

When a client or prospect has live pages and no brand record, make the record
from what exists before choosing a direction. Do not record brand `none` while
real pages are available.

1. Capture the home page and two other representative pages at desktop and
   phone widths, and collect the logo files the site serves. The capture
   is complete when those pages, the logo files and the styles read in step 2
   are in hand; a single value no tool can measure does not make it
   incomplete.
2. Read the actual styles with the host's browser automation: colors with
   their roles, type families, weights and sizes, spacing, corner and border
   habits, image treatment and motion. Record computed values, not guesses
   from a screenshot; where no tool can measure a value, mark it unknown.
3. Note what the owner or the assignment says they like and what they want
   changed. A liked existing identity is a fixed requirement, not a starting
   point to replace.
4. Fill [the brand record template](../assets/brand-record.template.md),
   marking each entry observed with the page it came from. Mark anything you
   add as proposed.
5. Keep the record with the client's project and name it in the pack's
   `brand` block with origin `project`.

When the capture is incomplete (for example HTML with no stylesheet, fonts,
logo files or page pixels) and cannot be completed within the job's access,
record what is observed, mark every missing value unknown in the brand
record, or proposed where the draft needs a stand-in, and proceed only for an
internal draft, saying so in the pack
and the recommendation. Work meant to be shown outside or to stand as the
client's brand holds until the capture is complete.

The same record, once a person confirms it, is the brand kit the client can
be handed.

## Approved asset libraries

A brand skill or project may name an approved asset library with a read-only
reader. Look up assets by their stable ID through that reader when an
assignment needs an existing approved asset. A returned record is evidence of
what exists, not a reuse right; check the record's ownership and limits. Get
the real file from the brand's own assets folder or a path the record names,
and open it before use. Do not download originals from the library app,
create accounts, or open its web app to work around a missing reader binding;
report the missing binding once and continue with supplied assets.

## Record what was used

The design pack's `brand` block records the brand name, where its sources came
from (`skill`, `repository`, `project`, `cms` or `none`), the skill's digest or
the repository's revision when there is one, and the files or records read.
Each library asset used is a `brand_asset` resource with its stable ID. Without
this, "what informed this design" cannot be answered later. See the design
pack in [project-record.md](project-record.md).

## Boundaries

- Brand sources are private to their owner. Read them in place; do not copy a
  brand's files into another brand's project or into a public export.
- Never use one client's brand material for another client.
- A brand skill grants no provider, spend or publication authority beyond the
  assignment.
