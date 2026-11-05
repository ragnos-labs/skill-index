# Plan and ledger fields

Read this when writing the plan generator, the apply loop, or the reconcile
step. Field names are suggestions; keep whatever names the tool already uses.

## Plan header

- Run id, creation time read from the clock, environment, and tool revision.
- Selection rule and the baseline counts from step 1.
- Freshness window and the baseline drift tolerance.
- Operation count per kind, and estimated external calls and cost.
- The reviewed plan digest and review reference, added by the review step.

## Operation

- `op`: position in apply order.
- `kind`: for example update text, recompute derived state, or archive.
- `record_id`, plus the parent id when the write depends on a parent revision.
- `expected_revision`: read live during planning.
- `before_digest` and `after_digest`, with sizes when useful for review.
- `after_value`, or a pointer to it inside the private run directory.
- `request_id`: derived from kind, record id, and expected revision, so an
  unchanged record yields the same id on regeneration and a changed record
  yields a new one.
- `depends_on`: earlier operations whose writes change this record's revision.

When a parent record mirrors its children's revisions, write the children
first and re-read the parent revision just before the parent write.

## Ledger entry

Append one JSON line per attempt and flush it before the next operation:
`op`, `request_id`, attempt time, `state`, resulting revision, error class,
a short error summary, retry count, and any job or call ids the system returns.
Never rewrite earlier lines; a later line supersedes an earlier one for the
same `op`.

## Final states

| State | Meaning | Next action |
| --- | --- | --- |
| applied | Written and read back as expected | None |
| already-done | The record already held the after value | None |
| stale | The record changed after planning and was not written | New plan cycle |
| refused | A guard blocked the write, such as a lock, archived record, or permission | Investigate; new plan if still wanted |
| failed | The write or a derived step errored; error class recorded | Classify, then a new plan or a paced retry |
| superseded | A later attempt for the same record and revision succeeded | None; keep for history |

Every planned operation ends in exactly one state. Counts per state must sum
to the plan's operation count.
