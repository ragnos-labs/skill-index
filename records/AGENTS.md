# Record instructions

Each JSON file describes one skill or domain. Records are maintained inputs;
generated indexes are projections.

## Skill records

- Use one file at `records/skills/<skill-name>.json`.
- Keep `name`, folder name, frontmatter name, and path aligned.
- Use `active`, `experimental`, or `deprecated` lifecycle status.
- Use `bootstrap`, `routable`, `explicit`, or `retired` load mode.
- State concise positive triggers and exclusions that improve routing.
- Reference external evidence as `<packet-id>:<source-id>`.
- Active records require a current review receipt.

## Domain records

- Use one file at `records/domains/<domain-name>.json`.
- Domain documentation lives below `domains/<domain-name>/`.
- An active domain must contain at least one active skill.

Run `make index` and `make check` after changing records.
