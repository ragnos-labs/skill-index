# Wiki Lab

Wiki Lab is the human-facing name for the Wikipedia drafting and review system
implemented by the plain-named `wikipedia-*` skills.

## North star

Given a topic and a body of sources, Wiki Lab produces an expertly researched,
fully cited Wikipedia-style working article and, when needed, the accompanying
platform-request draft. A human can inspect, rewrite, compare, and explain each
artifact claim by claim.

## Drafting capability

Wiki Lab supports full research, outlining, drafting, rewriting, citation work,
grading, and review. It can produce complete article prose, wikitext, and
complete request copy for workflows such as Articles for Creation,
undeletion/restoration, deletion review, or an edit request. These are working
artifacts for expert human review and rewriting, not placeholders that stop at
an outline or partial example.

## Skill composition

```text
wikipedia-research
  -> source packet
  -> claim ledger
  -> article scope

wikipedia-writing
  -> outline options
  -> complete article variants
  -> citations, wikitext, and platform-request drafts

wikipedia-review
  -> evidence review
  -> article and request review
  -> gold draft scores

wikipedia-workflow
  -> coordinates the complete Wiki Lab run
```

The general `ai-writing-review` and `writing-cleanup` skills provide a separate
prose-quality pass without replacing evidence review.

## Gold draft

A gold draft has:

- a visible source landscape;
- important claims mapped to direct support;
- correct citation identity and placement;
- neutral, source-proportional framing;
- useful article scope and structure;
- genuine paraphrase;
- clear, specific, non-generic prose;
- valid requested formatting; and
- enough review history to teach from.

## Engineering boundary

Wiki Lab imports selected ideas from audited upstream revisions, not whole
repositories. The initial version intentionally excludes the citation shell
scripts, direct arbitrary-URL scanner, runtime tool interception, and generic
taskgraph execution found in the larger upstream stack.

Those implementation choices protect the repository without narrowing the
complete prose or request copy that Wiki Lab can produce.
