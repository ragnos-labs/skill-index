# Installation and recovery

`build` only writes to a fresh explicit output directory. `plan` merges the
candidate against the current profile and last authored baseline, without
modifying either. Both reject output inside the private workspace or installed
profiles. Build and plan directories are private artifacts, not shared bundles.

The baseline records authored intent. An unrelated manual edit is retained; a
requested change to the same edited, moved, removed, or occupied control stops.
Control swaps are evaluated together. A no-op preserves the exact installed files.

`apply` verifies target, baseline, recipe, catalog, referenced resources,
candidate, staged profile, runtime, and installed plugin availability. It takes
an exclusive workspace lock and requires Stream Deck to be closed. Use the
existing adopted workspace for a profile; do not intentionally race an editor.

Each transaction retains a complete verified backup and both baseline states.
A staged replacement is swapped into place only after validation. Immutable
command runtimes are not rewritten. The receipt reports installation only;
inspect the reopened app and test outcomes separately.

For a failed apply, retain all transaction files and run:

```sh
python3 scripts/streamdeck.py --json rollback --receipt /absolute/workspace/pending.json
```

For a completed installation, use the receipt path returned by apply. Close
Stream Deck first. Recovery refuses later manual changes or a different pending
transaction. It does not depend on disposable build output. Interrupted rollback
can be retried with the same receipt because recovery paths are journaled.

Rollback restores the profile and baseline exactly. Previously referenced
command files remain available because releases are immutable and retained.
Restoration does not undo commands or physical effects previously triggered by
buttons. Backups and old releases are retained; no automatic pruning is performed.

If a running plugin rewrites profile files after reopen, exact rollback may stop
on drift. Inspect and reconcile that change rather than weakening the guard.
Do not delete pending journals, replace baselines, or force overwrite to recover.
