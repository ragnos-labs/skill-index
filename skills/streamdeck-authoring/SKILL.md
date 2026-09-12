---
name: streamdeck-authoring
description: Create and safely update Stream Deck buttons, dials, pages, and native Multi Action sequences using a local recipe and captured plugin controls. Use for Stream Deck authoring or hardening its profile workflow; not for pairing devices, activating MCP, publishing plugins, or diagnosing unrelated hardware.
---

# Stream Deck authoring

Use the adjacent `scripts/streamdeck.py` with filesystem and shell access. The
first supported target is Stream Deck + on macOS, profile format 3.0. Other
models and formats require implementation and validation before installation.

## Choose and capture

Start with the requested result, target device/group, placement, and visible
outcome. Prefer a configured native plugin action for device control, an Open
action for an app/file, and an explicit command for custom logic. A scene label
is not evidence of a room name or a working bridge.

Inspect the selected profile with `inspect --profile /absolute/profile.sdProfile`.
For first use, `adopt --profile ... --workspace /absolute/private/workspace`
captures its current controls and resources without changing the profile. Keep
this workspace, pairing-related settings, icons from installed plugins, and
receipts private. Never put a personal profile or catalog into shared source.
Existing managed workspaces retain their baseline; do not re-adopt to hide drift.

Read [the recipe format](references/recipe.md) when authoring. Use stable IDs,
explicit action references, and only the changes requested by the user. Native
plugin settings are opaque unless their installed interface is understood.

## Build and install

1. Edit the private recipe/catalog. Validate with `validate --workspace ...
   --plugins /absolute/plugin-directory`. Validation does not press buttons.
2. Build into a new directory outside the workspace and installed profiles:
   `build --workspace ... --output /absolute/build-directory`.
3. Create an installation plan with `plan --workspace ... --candidate ...
   --plugins ... --output /absolute/plan-directory`. Inspect its changed control
   list and staged profile. Preserve manual edits. Resolve a reported overlap
   from the user's actual intent; do not reset the baseline or force overwrite.
4. For an authorized profile update, close Stream Deck normally through available
   app controls, then `apply --plan ...`. Never force-kill the app or bypass the
   running-process guard. Reopen it and inspect the updated page and properties.
5. Test a harmless command directly, then a physical button when available.
   Report configuration validity, installation, command execution, and device
   outcomes separately. Editor selection does not prove a hardware press worked.

Every command supports global `--json` before the command. Build output contains
an importable profile, but command buttons reference a private immutable runtime
installed by `apply`. Do not import a command-bearing archive alone or imply it
is portable to another machine.

Read [installation and recovery](references/recovery.md) before a first apply or
any rollback. Stop on changed inputs, conflicting manual edits, a running app,
a missing plugin, or an outstanding transaction. Do not retry unchanged errors.

## Macros and effect boundaries

Use native Multi Actions for an ordered sequence of action references and
optional delays. Reject nested Multi Actions. Validate each component before
combining it. The sequence does not verify device completion, automatically
retry, or reverse physical effects when a later step fails. Command timeout and
exit status are local observations, not device acceptance.

This skill authors controls. It does not grant authority to pair devices, change
credentials, activate MCP, record, broadcast, or execute newly configured effects.
Use the user's existing task authorization for installation and scoped testing.
Do not claim an installed but disconnected light control is operational.
