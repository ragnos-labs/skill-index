# Domain instructions

Domain folders explain how independently usable skills compose into a complete
writing system.

- Use a literal lowercase, hyphenated folder name.
- Keep human-facing brand names in prose only.
- Describe scope, skill routing, shared artifacts, workflow boundaries, and
  completion criteria.
- Link to skills and the generated index instead of copying full skill
  instructions or maintaining another skill list.
- Put reusable execution guidance in skills, not only in domain documentation.
- Add or update `records/domains/<domain-name>.json`.
- An active domain must contain at least one active skill.
- Run `make index` and `make check` after domain or record changes.
