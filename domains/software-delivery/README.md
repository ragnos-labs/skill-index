# Software delivery

Use `ship-it` to finish a named software task at its authorized source or live
endpoint. It composes the owning project's validation, merge, deployment, and
cleanup procedures without maintaining a second implementation of those tools.

When several changes are built by parallel agent builders and ship together,
`parallel-build-sprint` coordinates scoping, file ownership, review rounds,
and merge, then hands the single batch to the owning delivery procedure or
`ship-it`. `live-ui-audit` produces read-only findings that can seed such a
sprint. `live-data-rewrite` governs bulk writes to live records, whether run
alone or as one step of a sprint.

Before a new agent joins a team, `agent-necessity-check` asks whether the agent
is needed at all; it makes no change and hands any build to the owning procedure.

The [generated skill index](../../index/README.md) owns the skill inventory.
Completion requires exact source evidence, live behavior proof when requested,
and an explicit result for cleanup, including anything safely preserved.
