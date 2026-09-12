# Recipe and catalog, version 1

The private workspace contains `recipe.json`, `catalog.json`, assets, an authored
baseline, immutable releases, and installation receipts. Python 3.9 or later is
required. Use absolute local paths; symlinks and parent traversal are rejected.

`recipe.json` has `version: 1`, a UUID `profile_id`, `name`, and ordered `pages`.
Each page has a stable lowercase hyphenated `id`, `name`, and `controls` list.
Each control has a stable `id`, `controller` (`Keypad` or `Encoder`), `position`
(`x,y`), and catalog `action` reference. Optional `title` and workspace-relative
`icon` override the captured appearance. Stream Deck + has a 4x2 keypad and four
encoders at positions `0,0` through `3,0`. IDs do not change when titles change.

`catalog.json` has `version: 1`, captured `device`, and an `actions` object keyed
by reusable action names. Use these forms:

```json
{
  "open-editor": {"kind": "open", "path": "/Applications/TextEdit.app"},
  "status": {
    "kind": "command",
    "argv": ["/usr/bin/python3", "{runtime}/assets/status.py"],
    "files": ["assets/status.py"],
    "cwd": "/absolute/working-directory",
    "timeout": 20,
    "title": "Local status"
  },
  "next": {"kind": "navigation", "direction": "next"},
  "prepare": {
    "kind": "multi",
    "steps": [{"action": "open-editor"}, {"delay_ms": 300}, {"action": "status"}]
  }
}
```

Replace the example working directory with an existing absolute non-symlink path.
`files` are workspace-relative paths under `assets/`. Each must have a
corresponding exact `{runtime}/...` argv argument; the builder copies those files
into the immutable runtime. Other arguments pass literally through subprocess
with no shell expansion. The executable must exist and be executable. Timeout is
positive and no greater than 3600 seconds. Commands are never executed during
inspect, validation, build, or planning.

A captured native entry has `controllers`, a complete `action` object, and
`resources` mapping profile-relative image paths to workspace-relative assets.
Generated entries may also retain a captured `states` list and `resources` map
to preserve appearance when converting an existing launcher to a command.
Keep unknown settings and plugin metadata. `adopt` creates these entries from the
actual profile. Default controller support for generated entries is Keypad;
only a native entry explicitly supporting Encoder may populate a dial.

Generated native macros use the observed version-3 routine container with an
ordered first action list and empty second list. Delay is in milliseconds. No
nested macros, loops, retries, or completion polling are supplied. Captured
macros are also validated recursively for nesting.

The recipe controls additions, removals, names, placement, and content. Updates
preserve the installed profile name and existing page ordering; new pages append.
Profile renaming and existing-page reordering are manual operations in v1.
Unknown ancillary pages and metadata are retained. Removing a managed page that
still contains manually retained controls is a conflict.

Only the observed selected `State` field on action objects is excluded from
authored comparisons. Unknown settings remain conservative conflict inputs.
Do not add broad ignore rules merely to make an update pass.
