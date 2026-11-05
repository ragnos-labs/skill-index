---
name: parallel-build-sprint
description: Coordinate a build sprint in which several agent builders work in parallel. Scouts with critics scope the work, builders own disjoint files in isolated worktrees, each build gets independent review and repair, then merge, a combined skeptic-voted review, reviewed fix rounds, a final delta check, full suites once, and one deploy. Use when several related changes ship together; do not use for a single change, research-only work, or unattended autonomy.
---

# Parallel build sprint

Every review round can find a serious defect, including reviews of fix rounds,
and parallel builders drift when coupled logic is split between them. This
procedure keeps merges cheap through disjoint file ownership and ships no
unreviewed commit.

## Roles

- Coordinator: owns the sprint brief, builder briefs, shared files such as the
  changelog, version, and top-level instructions, the merges, the decision log,
  and the report. Reads actual returns and diffs, not only summaries.
- Scouts: read-only; each scopes one area against current source.
- Critics: a second reader for each scout plan.
- Builders: one per file set, each in an isolated worktree.
- Reviewers and skeptics: fresh context, never the builder of the work.

Delegation grants no authority. The user's authorization for repositories,
endpoint, and deploy target bounds every role.

## Size the sprint first

The lean default suits a small sprint with few builders and no one-way steps:
one reviewer per build, one combined skeptic-voted review, one reviewed fix
round, a final delta check, full suites once, and one deploy.

Add an integration round, meaning a second combined review after the first fix
round, when any of these holds:

- the first combined review kept a high finding, or the fix round was large or
  touched coupled code;
- the sprint changes one-way schema or data steps, deploy or failure paths,
  locking or concurrency, parsing of untrusted input, or a rule implemented in
  two places;
- the merge needed nontrivial conflict resolution.

Give builds in those areas two reviewers. Set a round cap at the start. Stop
when a round keeps no high or medium finding or the cap is reached, and report
what remains.

## 1. Scout and critique

Each scout returns a scoped plan with files, decisions, risks, and tests,
checked against source at the base revision. A critic attacks each plan for
wrong assumptions, gaps, and coupling with other plans. The coordinator
resolves conflicts and asks the user for product decisions once, together.

## 2. Partition by file ownership

- Give each builder a disjoint file set. Overlap is a planning defect; fix the
  partition, not the merge.
- Give coupled logic to one builder: a rule implemented on server and client,
  a schema and its readers, a fixture shared by two suites.
- Keep shared files with the coordinator.
- Each builder brief states the goal, owned and forbidden files, base
  revision, worktree and branch, focused checks, private log location, return
  format (what was built, files, checks, open risks), and limits: commit on
  the branch; no push, merge, or deploy.

## 3. Build, review, repair

Builders run focused checks only. Each finished build goes to its reviewers
with the scoped plan, the exact diff, and the
[review lenses](references/review-lenses.md). The builder repairs findings and
the reviewer checks the repair. A repair is a new change and is reviewed as one.

## 4. Merge

Merge builds into one integration branch in dependency order and run focused
checks for the merged areas. Record each conflict resolution as unreviewed
delta.

## 5. Combined review with skeptic votes

Split the merged diff across reviewers by lens. Independent skeptics try to
disprove each finding from source: three for high or medium, one for low. Keep
a finding only on a majority: two of three votes for high or medium, or the
one vote for low. Record refuted findings with the reason.

## 6. Fix round

Send kept findings to the owning builder, or to one fixer when findings are
coupled. Fix rounds introduce defects too, so review each one before it
merges.

## 7. Final delta check

List every commit after the last reviewed revision: fixes to fixes, merge
resolutions, and coordinator edits. Review exactly that delta.

## 8. Full suites once, then one deploy

Run the full suites once on the final revision and do not repeat them on
unchanged inputs. Limit how many full suites run at once on one machine.
Deliver through the owning repository's delivery and release procedure, or
`ship-it` when none exists, as one batch with a health and user-path check and
a rollback route. Batching saves deploy effort, but live bugs stay up until
the batch ships; deploy earlier only for an urgent live repair.

## Report

For each build: owner, files, review result, and repairs. For the combined
review: findings kept, refuted, and fixed. Then the final revision, suites and
results, delivery stages reached (merged, released, deployed, verified) as
separate states, open risks, and the items only the user can do.
