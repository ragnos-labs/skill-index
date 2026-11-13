# One project design record

Extend the existing record. Otherwise create `DESIGN.md` with the owning project
for public/synthetic decisions; keep private inputs and restricted captures in
its approved private storage. Never save credentials or signed URLs in Git.

## Design pack

The design pack is the one handoff from Director to maker or builder. It is
this record plus the actual tokens, assets, and components the producer can
open, and it starts with:

- kit name, the digest the skill index returned, and the list of kit files read;
- the direction below, exact copy, dimensions or viewports, and fixed requirements;
- each admitted resource with its ID or revision and the decision it supports;
- allowed effects, reuse limits, and the review criteria.

A CMS pack adds the project, admitted reference revisions and permitted output
round. Named provider resources do not replace real files or pixels.

Provide actionable visual guidance and source-to-output decisions, not metadata
alone. Identify the chosen behavior primitives and implementation ownership
when [UI SDK integration](ui-sdk.md) applies.

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
