# R2C recovery QA

The skill now separates failure diagnosis, native recovery and save completion.
It adds no pipeline, scheduler or runtime mutation operation.

## Diagnosis

| Finding | Owner and correction |
| --- | --- |
| Undefined unit for the prior two-repair instruction | Skill: use one task-wide plan, counting newly started native regeneration transactions across checkpoints and resumes; choose a finite ceiling under actual task/native and spending limits. Two is a conservative fallback, not a native cap. |
| Both repairs allocated to a broad inadequate source while narrow defects remained | Coordinator: triage every available review, reserve independent useful repairs and change strategy after no convergence. Source count alone does not justify more retries. |
| Further routine repair framed as requiring new user authority | Coordinator: reuse standing/task authorization within scope and costs; explicit task/native limits and expanded effects still bind. |
| Claim/citation defects versus source-level coverage omissions | Native semantic review: keep support, adequacy and exact citations intact; diagnose each remedy instead of weakening review. |
| Missing checkout and historical runtime assumptions | Installation owner: resolve current source/executor/contracts; a configured image does not prove a live save. |
| Unsafe or ambiguous L1 publication | Product owner: use current native transaction boundaries, preserve owner content and keep each publication/readback stage distinct. |

The inspected native contract retries all five passes plus review, preserves
failed evidence and resumes committed passes through ordinary generation.
It exposes no targeted pass or citation editing operation. Support/citation
review spans all passes; adequacy concerns the final card against native source
evidence. Retained supplementary originals do not necessarily feed that reader.
These are version-specific findings, not permanent portable guarantees.

At the inspected source revision, the newer source-index parser already handles
recognizable legacy/editorial content. That is a reason to recheck the prior
hold once through the authorized save owner, not evidence of successful
publication. Owner-mode standing-map publication still needs the previous-content
guard. Product repairs belong in Cairns baseline; pins, binding refresh and
live verification belong in Cairns deploy. This skill change performs neither.

## Repeatable behavior checks

Use [the synthetic cases](../tests/fixtures/r2c_recovery.json) in a fresh session
with the exact candidate bundle. Cases supply mock client contracts and states,
not authority to call providers or write Cairns. Return the requested operation
sequence, accounting, per-stage states and resume condition for each case.
The reviewer evaluates actual decisions against the native mock response, task
limits and failure cause, rather than matching words in the skill file.

Check allocation and numeric budgets, narrowly supported corrections versus
whole-cycle retries, full-source adequacy, extraction, explicit exhaustion,
no progress, privacy/no-save, denied writes, revision/digest drift, partial
publication, incompatible readers, concurrency recovery, interrupted saved-pass
resume, runtime drift, index ambiguity and authorized fallback replanning.
A passing offline run proves those decisions only; it does not prove live
provider access, authorization, publication or durable execution.
