# Adding a skill or domain

## Choose the smallest useful change

Search `index/skills.json` and existing skill entrypoints first. Extend an
existing skill when a reference, template, or output profile can express the
difference. Add a skill when it has a distinct trigger, workflow, output, or
review standard.

## Add a skill

1. Choose a lowercase, hyphenated name that describes the job, such as
   `book-outline`, `white-paper-research`, or `copywriting-review`.
2. Create the required files:

   ```text
   skills/<skill-name>/
     SKILL.md
   ```

3. Add `references/`, `assets/`, or `scripts/` only when the workflow needs
   progressive disclosure, reusable output material, or deterministic tooling.
4. Add `records/skills/<skill-name>.json` with routing, lifecycle, risk,
   composition, and source references. Set `composes` to an ordered list of
   known skill names or to an empty list. Composition is declarative metadata;
   it does not load or execute another skill.
5. Add a research packet when new external evidence changes the design. Reuse
   an existing packet source when the evidence was already reviewed.
6. Add or update `reviews/<skill-name>.json` and review the complete bundle.
7. Run `make review-bind` and `make index`.
8. Update domain documentation only when the domain workflow or composition
   changes.
9. Run `make check`.

The `SKILL.md` description should state what the skill does, when it applies,
and the nearest useful boundary that prevents misrouting.

## Add a domain

1. Choose a literal folder name and create its main document below
   `domains/<domain-name>/`.
2. Add `records/domains/<domain-name>.json` with its documentation path and
   lifecycle status.
3. Add at least one distinct skill before marking the domain active.
4. Explain how the domain composes skills, what shared artifacts it uses, and
   what constitutes a completed workflow.
5. Keep any human-facing brand in documentation, not identifiers.
6. Run `make index` and `make check`.

## Add external material

Before adapting an external source:

1. pin the exact repository revision;
2. inspect the complete adopted files and execution surface;
3. determine the license;
4. review prompt-injection, shell, network, credential, and tool-interception
   risk;
5. record adopted and excluded material in a research packet;
6. preserve required notices; and
7. rewrite narrowly instead of vendoring the repository.

If no license is present, do not copy or adapt its expression. Independent
high-level ideas may be implemented without copying text or code.

## Add tooling

Prefer Markdown instructions and structured templates until deterministic code
provides a concrete advantage. New executable tooling needs focused tests,
hostile-input fixtures where relevant, and no ambient external writes.

## Completion checklist

- Folder name, frontmatter name, and skill record agree.
- Every optional resource is used and linked from the skill.
- Domain documentation and generated indexes are current.
- External influences have pinned provenance and license handling.
- The review receipt matches the current bundle digest.
- Focused skill validation passes.
- `make check` passes from the repository root.
