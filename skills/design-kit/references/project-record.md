# One project design record

Extend the existing record. Otherwise create `DESIGN.md` with the owning project
for public/synthetic decisions; keep private inputs and restricted captures in
its approved private storage. Never save credentials or signed URLs in Git.

## Design pack

The design pack is the one handoff from Director to maker or builder. It is
this record plus the actual tokens, assets, and components the producer can
open, and it starts with:

- kit name, the digest the skill index returned, and the list of kit files read;
- the brand and its sources, resolved as in [brand-sources.md](brand-sources.md);
- the direction below with what the viewer notices first and one rejected
  alternative, exact copy, dimensions or viewports, and fixed requirements;
- every quote, testimonial, statistic and factual claim in the copy, each with
  its source, whether it was verified against that source, and its release;
- each admitted resource with its ID or revision and the decision it supports;
- allowed effects, reuse limits, and the review criteria.

A CMS pack adds the project, admitted reference revisions, permitted output
round and the learned record it read; a pack whose learned record was not read
is a hold. Named provider resources do not replace real files or pixels.

Write this start of the pack as `design-pack.json` beside the design record,
following [design-pack.schema.json](design-pack.schema.json); copy
[the synthetic example](../assets/design-pack.example.json) as a starting point.
A pack sent as a message can be checked from standard input with `-`. Where
the host can run Python, the Director checks it before handing over and the
producer checks it before the first render with its own resolved digests:

```text
python3 <kit>/scripts/design_pack.py check design-pack.json --kit-digest <kit digest> [--brand-digest <brand skill digest>]
python3 <kit>/scripts/design_pack.py summary design-pack.json
```

Pass `--brand-digest` when the brand's origin is `skill`. Pass `--final` before
output leaves draft: it fails while any claim is unverified or any release is
missing. Without it such a pack passes as draft only. Any `check` failure
goes back to the Director with the printed reasons; a differing kit or brand
digest is a hold. A CMS pack names the CMS brand record it read; it outranks
the brand block on brand matters. `summary` answers "what informed this
design". The pack's `resources` are what the Director admitted at handoff,
including CMS references; the record's "Sources and assets" table below adds
what the output actually used. `inspected` means whoever wrote the entry opened
the pixels, preview, code or file itself. The prose direction, review findings
and repairs stay in the design record. Keep a client's pack in that client's
private storage when it names private material.

## Direction

- Audience, action, deliverable, exact copy/assets, fixed requirements.
- Subject-specific visual premise and observable success conditions.
- Type and color roles, grid/spacing, imagery, motion where useful.
- Retained project conventions and deliberate changes.
- Requested alternatives and tradeoffs, without invented human selection.

## Sources and assets

| Source and ID/revision or URL | Retrieved and inspected | Decision/adaptation | Output file/component | Reuse terms or limit |
| --- | --- | --- | --- | --- |

Include actual retrieval date and relevant viewport/state. Distinguish code
reuse, token export, visual inspiration, and original implementation. Preserve
required font/icon/source attribution. Remove tracking parameters when safe,
not query parameters required to identify the resource. Keep useful resource
copies in existing project structure, subject to their permitted use.

## Meaningful review and repairs

| Output revision/state | Finding/location | Repair | Before/after evidence | Observed result |
| --- | --- | --- | --- | --- |

Separate visual judgment, technical checks, and content fidelity. Identify
independent review versus self-review. Keep unresolved findings explicit and
reuse passed checks on unchanged inputs.

## Delivery

Link runnable/editable source, exports/dimensions, required assets, run/render
commands, and the strongest preview. Report actual provider coverage, known
usage, blockers/resume conditions, and the stage reached.

For CMS delivery, reuse its direction/output-round/version fields rather than
duplicating records. Upload revisions with the CMS's lineage field. Source stays
with its owner. Create posts or record reviews only within the assignment; do
not mark agent preference as human decision. Honor person-only backend refusals.
