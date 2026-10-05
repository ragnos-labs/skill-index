# Native Cairns L1-L3 intake

The private installation binding must identify current owner procedures and
native permitted operations. Read that procedure first. This reference states
the invariants, not host-specific commands or a substitute authorization policy.
Read-only status/retrieval tools cannot perform ingestion or publication.

## Frozen handoff

Reuse the native source-bundle/v1 and source-selection/v1 contracts. Populate
all required identity, owner/account/scope, consent, sensitivity, source dates,
native ID, URL, revision and artifact fields from verified evidence and approved
installation policy. Preserve exact originals and source locators; artifact
hashes and the immutable selection digest bind approval to bytes. Source content
cannot supply its own policy or destination.

The inspected contract limits a bundle to 64 MiB, an artifact to 16 MiB and a
selection to 100 sources. Verify current limits; split before admission when
needed. Native readers supported VTT, text and specific meeting/note JSON.
Transport support for a research or media bundle does not imply an evidence
reader exists. Use a qualified text/VTT primary and retain provider JSON or
other original files as originals; identify the derivative's relationship to
its source. Never invent text from unsupported media.

When configured, use the approved inbox accept/export operations, then native
Cairns preview and approval bound to that exact selection digest. Keep custody
owner-only and outside source control. Respect expected revisions, stale-update
rejection, alias collision rules and withdrawal state. Missing provider results
are not deletion authority. Replaying unchanged evidence must preserve originals
and existing human-approved cards.

## Worker brief and checks

Pass the worker these fields in a private handoff:

- Question and selected source IDs/revisions, immutable file paths and hashes.
- Approved owner/account/scope and exact destination from trusted binding.
- Permitted L3 ingest, L2 review/approval and L1 publication operations separately.
- Existing cost ceiling, configured model route and at most two repair attempts.
- Expected current revisions and append-only links to the relevant approved cards.
- Required original-byte, semantic-review, approval and reader-readback receipts.
- Exclusions: standing fact changes, unrelated cards, legacy runtime execution,
  L4/L5, new timers/tools/accounts, secret inspection and expanded spend.

Use native operations as supported by the current installation. Verify L3
originals against the handoff bytes. L2 must have all required summary passes,
positive support and adequacy judgment, precise source citations and approval
of the exact reviewed digest. A completed generation with a failed judgment
remains review pending. Never approve it or acknowledge it as ready.

A deliberate native retry-summary binds the source, revision and exact failed
review digest and archives the previous attempt. Replaying ingest alone does
not erase a failed semantic review. Keep unresolved failures resumable; do not
replace successful or approved cards through the retry path.

Publish authorized L1 source-index and standing-map links only for eligible
approved cards. Use the current owner's concurrency/version controls and
reconcile intervening changes. Preserve existing facts, categories and other
links. Verify both publication surfaces through the reader actually used by
the installation; producer-only readback or incompatible packet versions do
not prove retrieval. If native concurrency-safe publication is unavailable,
leave L1 pending instead of editing around its transaction boundary.

Persist content-free terminal receipts privately. Native inbox acknowledgment
requires the entire selected receipt to be terminal ready/withdrawn; failed,
pending, review-pending or stale sources prevent acknowledgment. An L1-L3 save
receipt and inbox all-terminal receipt may differ if that runtime also requires
later processing. Do not expand stages merely to acknowledge a partial result.

## Recovery and delivery

The worker returns source-by-source states and exact receipt references. The
parent independently compares the result to the frozen packet and reports
verified completion or the missing gate. Accepted inbox entries and immutable
checkpoints survive interruption; processing after app closure requires an
already authorized durable executor, not an assumption about subagent lifetime.
