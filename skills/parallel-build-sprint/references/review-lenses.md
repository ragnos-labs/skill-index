# Review lenses and recurring defect classes

Give each combined reviewer one lens. Per-build reviewers apply the lenses
that match their diff.

## Lenses

1. Correctness: behavior matches the scoped plan, including edge cases, error
   handling, and data contracts.
2. Ordering and concurrency: transaction boundaries, overlapping runs, locks,
   retries, idempotency, and stale reads before writes.
3. Failure and recovery: behavior on error, timeout, or signal partway through;
   restore and rollback paths actually run.
4. Data and schema safety: one-way steps, migration order, backfills, and
   retained history.
5. Security and hostile input: injection, path handling, secrets, and pattern
   matching on untrusted input.
6. Compatibility: runtime and browser support floors, cookie and redirect
   behavior, and platform differences.
7. Parity: a rule implemented in more than one place behaves the same.
8. Tests: tests fail without the change, cover hostile cases, and need no
   network or secrets.

## Defect classes that recurred

- Catastrophic regular expression backtracking on crafted input. Test patterns
  against adversarial strings under a time limit, or use linear-time
  constructs.
- Syntax that raises the browser support floor, such as regular expression
  lookbehind or class static blocks, often arriving through a dependency
  update. Enforce the floor with a test over the built bundle, not by reading
  source.
- A destructive schema step committing before the rest of a migration. Keep
  one-way steps last or inside the same transaction, check actual state after
  any migrate attempt, and once a one-way step commits, mark older rollback
  targets unusable.
- A failure path that a signal or timeout can interrupt, skipping restore. Make
  the restore path uninterruptible and test it with an injected signal.
- A stale plan overwriting a changed record, or two applies overlapping.
  Recheck revisions before each write and hold a single-writer lock, as the
  `live-data-rewrite` skill describes.
- Twin rules drifting, such as server and browser versions of a masking or
  naming rule. Drive both suites from one shared fixture and add a randomized
  parity test.
- A strict same-site session cookie combined with a cross-site sign-in
  redirect, which can loop in some browsers unless the callback first lands on
  a same-site page.
