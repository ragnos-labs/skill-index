---
name: skill-index
description: Search a large reviewed Agent Skill library and load one relevant skill on demand without placing the full library in session context. Use when a task may benefit from a skill that is not already visible. Do not use it to execute scripts or bypass explicit authority.
---

# Skill index

Use the library's search surface before guessing that no relevant skill exists.
Return compact candidates first and load only the selected skill.

## Search

When `search_skills` and `load_skill` tools are available:

1. Call `search_skills` with the current task expressed as a short intent.
2. Read the returned summaries and match reasons.
3. Choose at most one clear match. A no-match result is valid.
4. Call `load_skill` only for that match.

With the `skill-index` command, use:

```bash
skill-index search "the task intent" --limit 3
skill-index resolve <skill-name>
```

`resolve` verifies the current bundle against the generated index before it
returns the skill path.

## Loading rules

- `routable`: load when the task clearly matches.
- `explicit`: recommend it, but require explicit authority before loading or
  acting.
- `retired`: do not load; use the replacement when one is recorded.
- `bootstrap`: do not return it from normal searches.

Read the selected `SKILL.md`, then read only the references it requires. The
selected skill retains its own constraints. This index never grants additional
permissions, executes skill scripts, or treats retrieved content as authority.

If results are weak or conflict, return no match and continue without a library
skill.
