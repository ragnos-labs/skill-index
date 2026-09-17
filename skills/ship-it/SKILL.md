---
name: ship-it
description: Complete a named software change through its requested source or authorized live outcome when the user asks to ship, merge, deploy, make it live, or finish established delivery. Do not execute for audits, status, planning, or quoted examples.
---

# Ship it

Use the owning repository's delivery contract when present. Otherwise use this
completion contract with its existing validation, release, deployment, recovery,
and cleanup procedures. Do not introduce another command implementation.

## Resolve the requested outcome

| Request and context | Endpoint |
| --- | --- |
| Named implementation, fix, build, or change | Validated source delivery through commit, push, PR, exact-head merge, default-branch verification, and safe task cleanup. |
| A request clearly requiring a live result on an established service, including "ship it" or "make it live"; or "merge it" when a live endpoint was already established | Source delivery plus necessary release, deployment, activation, live verification, and safe task cleanup. |
| "Finish", "continue", or "work until complete" | Retain the established endpoint and limits through retries, waits, and route changes. |
| Source-only, merge-only, draft-only, preview-only, staging-only, do-not-deploy, or preservation limits | Honor the narrower endpoint, target, and effects. |
| Audit, review, status, recommendation, planning, or a quoted example | Read-only; do not start delivery. |

Infer the repository, task, exact revision, environment, and intended effects
from the user's request and current task evidence. A prototype or a repository
with no runtime need not acquire a production target. When live delivery is
requested but the target or owning deployment path remains ambiguous, complete
independent work and ask only for that missing choice. Credentials and client
defaults do not choose the target. An explicit user-defined meaning overrides
the vocabulary above. Do not reapprove an outcome already authorized in this task.

## Deliver with evidence

- Preserve unrelated work. Reuse existing results and checkpoint coherent work;
  isolate Git changes where needed. Use one final validation owner and the
  repository's exact-revision merge procedure. Required gates remain binding.
- For an authorized live outcome, use the owning release and deployment path.
  Bind the artifact to the merged revision, confirm the target and documented
  recovery path, then install, configure, activate, or restart only as necessary.
  Do not deploy a dirty checkout or silently substitute another artifact.
- For live endpoints only, read back the running revision and exercise the
  changed user behavior with a bounded probe inside the authorized effects.
  Health alone does not prove the outcome. Keep an unperformed or failed
  user-path check unverified.
- Diagnose recoverable failures before retrying. Re-bind the target, effect,
  and revision after a route change; stop a repeated unchanged failure pending
  new evidence. Reconcile ambiguous external results and never repeat a
  completed merge because runtime evidence is missing.

## Ask only at a material boundary

Retain authorization while the target, effects, access, cost limits, and risk
remain in scope. New infrastructure, spending commitments, permissions,
destructive data changes, public disclosure, and external communications need
explicit coverage in the user's authorization. Installation or activation of
an automation that introduces such effects is subject to the same boundary.
Do not infer those effects from a generic instruction to finish.

Ask only for missing coverage, a material choice, or unavoidable human action.
State the exact missing decision or binding guard, prepare the authorized work,
and continue independent work. Never bypass a failed required gate or a tool
guard, disclose credentials, or treat available access as action authority.

## Close out

After the requested endpoint is verified and task users, workers, and terminals
have released the target, invoke the owning cleanup procedure from a safe
checkout with the exact task and merge evidence, plus runtime evidence for a
live endpoint. Let that owner coordinate worktree and branch retirement.
Preserve active, dirty, ignored, ambiguous, unmerged, or recovery-needed work.
Remove ordinary leftovers only through its verified preservation procedure.
Treat accepted or queued cleanup as pending until removal is independently
verified; reconcile uncertain results before retrying. A cleanup hold does not
undo a successful merge or justify force deletion.

Report the source revision and merge; release, deployment, installation, and
activation separately; the running artifact and observed behavior; acceptance
when in scope; and cleanup or preserved work. Mark unrequested stages as not
applicable and unresolved stages as held. Never equate these states.
