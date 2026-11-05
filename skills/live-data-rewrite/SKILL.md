---
name: live-data-rewrite
description: Plan, review, sample, apply, verify, and reconcile a bulk write to live records, especially records keyed to exact revisions or carrying derived state such as search indexes or embeddings. Use for backfills, content cleanups, re-embedding, and reindexing on a running system; do not use for single-record edits, read-only reports, or schema migrations owned by a release procedure.
---

# Live data rewrite

Bulk writes to live data fail quietly. A plan goes stale while it waits, two
applies overlap, a throttled provider drops part of a batch, or verification
counts old failures as current. Run every bulk write as six separate steps and
keep the evidence of each.

## Confirm authority and target

- The request must name the selection, the change, and the environment.
  Planning and review are read-only. The sample and apply steps write and need
  authorization that covers this change. Credentials are access, not authority.
- Permanent deletion, overwrite without history, or dropping derived state that
  is costly to rebuild needs explicit coverage and a verified backup first.
- Paid external calls need a stated budget. Estimate calls and cost before the
  sample and stop at the budget.
- Write through the system's own interface when it enforces revisions, history,
  and permissions. Do not bypass it with direct storage writes unless the
  owner's procedure requires that.

## Keep working files private

Plans, baselines, ledgers, and logs hold record identifiers, content, and
operational detail. Keep them in a private directory outside Git, one directory
per run. Commit only tooling and a summary without record content or
identifiers. Never write credentials into a plan or log.

## 1. Baseline and target

Record the selection rule and its count, counts that must not change (such as
records outside the selection), counts the change should move, failures that
already exist, and the tool revision. Write the target as checkable assertions,
for example "no selected record contains the pattern" and "every selected
record has derived state for its current revision".

## 2. Plan

Produce the plan with a dry run that reads live state and writes nothing. Each
operation carries the record id, the expected revision read live, before and
after digests, and a stable request id derived from the operation kind, record
id, and expected revision. Order dependent writes so one write cannot
invalidate a later operation's expected revision, and put operations that lock
or archive a record after every other operation on it. Use the
[plan and ledger fields](references/plan-and-ledger.md).

## 3. Review

An independent reviewer reads the plan, the tool, and sampled before and after
diffs: selection scope, transformation correctness, ordering, request id
stability, refusal paths, and retained history. Repair, regenerate, and review
again. Write the reviewed plan digest to a review receipt beside the plan, never
into the plan itself; only the plan matching the receipt may be applied.

## 4. Sample

Apply a small sample that covers each operation kind and the riskiest edge
cases. Read every sampled record back: value, revision change, history entry,
and derived state. Any difference stops the run.

## 5. Apply

- Hold an exclusive lock or lease for the run. Refuse to start while another
  apply holds it.
- Resume from the ledger and skip operations already recorded as applied.
  Retry an attempt with no recorded result under the same request id.
- Re-read each record immediately before writing. If it already holds the
  after value, mark the operation already done. If its revision otherwise
  differs from the expected revision, do not write; mark it stale.
- Write with the expected revision and the stable request id, so a retry after
  an ambiguous result cannot apply twice.
- Append each result to the ledger and flush before the next operation.
- Never re-plan during an apply. Stale operations wait for a new reviewed plan.
- Keep prior values in system history or a private backup before overwriting.
- Avoid windows when scheduled jobs or other writers touch the same records.

## Pace paid and throttled calls

Bulk changes often trigger embeddings, model calls, or third-party requests,
directly or through background jobs. A burst of about a thousand requests can
produce throttled failures that the system then marks as not retryable.

- Cap concurrency and rate below the provider limit. Submit in batches and let
  each batch's background jobs drain before the next.
- Back off with jitter on throttling; stop after a set number of consecutive
  throttled responses.
- Record the error class per item. A derived-state call that failed from
  confirmed throttling, rather than rejected content, may be retried in a later
  paced pass within the same reviewed plan, even when the system labels it
  terminal. The retry uses the next retry generation and so a new request id;
  record the generation in the ledger. Failed or stale record writes are never
  retried this way.
- Track calls, retries, and estimated cost against the budget.

## 6. Verify and reconcile

- Re-run the baseline counts and check every target assertion.
- Judge derived state by each record's latest attempt for its current
  revision, not by historical job rows. A failure that a later success
  superseded is not current; record the supersession so verification stops
  listing it.
- Give every planned operation exactly one final state from the ledger
  reference. Stale items and failed record writes return to a new plan cycle,
  never a direct write; only throttled derived-state calls take the paced retry
  above.

## Refuse or stop

Refuse to apply when the plan has no review receipt, its digest or the tool
revision differs from the receipt, it is older than its freshness window, or the
baseline drifted beyond the stated tolerance.

Stop on a sample mismatch, an error rate above the threshold, the consecutive
throttle limit, the budget, an unexpected response shape, a write outside the
selection, or a missing history entry. Do not recover by widening the
selection, switching to direct storage writes, or deleting failed items.

## Report

Report the selection and environment, plan digest and review, sample result,
counts per final state, each target assertion and its result, external call
totals with throttles, retries, and cost, residual items with next action and
owner, the rollback route, and where the private artifacts are, described
generically. Keep record content and identifiers out of shared reports.
