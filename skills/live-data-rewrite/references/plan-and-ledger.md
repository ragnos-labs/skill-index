# Plan and ledger fields

Read this when writing the plan generator, the apply loop, or the reconcile
step. Field names are suggestions; keep whatever names the tool already uses.

## Plan header

- Run id, creation time read from the clock, environment, and tool revision.
- Selection rule and the baseline counts from step 1.
- Freshness window and the baseline drift tolerance.
- Operation count per kind, and estimated external calls and cost.

The plan file never changes after review, so its digest stays checkable.

## Review receipt

A separate file beside the plan in the private run directory, written by the
review step: the plan digest over the plan file's exact bytes, the reviewer,
the review time, the tool revision, and the review reference. The apply step
recomputes the plan digest and compares it and the tool revision with the
receipt.

## Operation

- `op`: position in apply order.
- `kind`: for example update text, recompute derived state, or archive.
- `record_id`, plus the parent id when the write depends on a parent revision.
- `expected_revision`: read live during planning.
- `before_digest` and `after_digest`, with sizes when useful for review.
- `after_value`, or a pointer to it inside the private run directory.
- `request_id`: derived from kind, record id, expected revision, and retry
  generation. The plan holds generation 0, so an unchanged record yields the
  same id on regeneration and a changed record yields a new one. An ambiguous
  attempt is retried under the same id; only a paced retry of a throttled
  derived-state call moves to the next generation and a new id.
- `depends_on`: earlier operations whose writes change this record's revision.

When a parent record mirrors its children's revisions, write the children
first and re-read the parent revision just before the parent write.

## Ledger entry

Append one JSON line per attempt and flush it before the next operation:
`op`, `request_id`, retry generation, attempt time, `state`, resulting
revision, error class, a short error summary, and any job or call ids the
system returns. Never rewrite earlier lines. The latest line for an `op` gives
its current state; earlier lines stay as attempt history.

## Final states

| State | Meaning | Next action |
| --- | --- | --- |
| applied | Written and read back as expected | None |
| already-done | The record already held the after value | None |
| stale | The record changed after planning and was not written | New plan cycle |
| refused | A guard blocked the write, such as a lock, archived record, or permission | Investigate; new plan if still wanted |
| failed | The write or a derived step errored; error class recorded | Record write: new plan cycle. Throttled derived-state call: paced retry at the next generation |
| superseded | A success outside this run, such as a background job, already covered the same record and revision | None; keep for history |

An earlier failed attempt for an `op` whose later attempt succeeded is attempt
history; the `op` ends applied.

Every planned operation ends in exactly one state. Counts per state must sum
to the plan's operation count.
