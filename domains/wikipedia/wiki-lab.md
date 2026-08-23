# Wiki Lab

Wiki Lab is the human-facing name for the private Wikipedia-style sample system
implemented by the plain-named `wikipedia-*` skills.

## North star

Given a topic and a body of sources, Wiki Lab produces an expertly researched,
fully cited, Wikipedia-style sample article that a human can inspect, learn
from, compare, revise, and explain claim by claim.

## Sample mode

Sample Mode permits full AI research, outlining, drafting, rewriting, citation
work, grading, and review. Its purpose is to produce excellent private examples
and teach the craft of source-grounded encyclopedia writing.

Destination publishing rules can be selected as review material later. They do
not block private sample generation. Live publishing, account access, direct
editing, and submission workflows belong in separate future adapters.

## Skill composition

```text
wikipedia-research
  -> source packet
  -> claim ledger
  -> article scope

wikipedia-writing
  -> outline options
  -> complete sample variants
  -> citations and wikitext

wikipedia-review
  -> evidence review
  -> article review
  -> gold sample scores

wikipedia-workflow
  -> coordinates the complete Wiki Lab run
```

The general `ai-writing-review` and `writing-cleanup` skills provide a separate
prose-quality pass without replacing evidence review.

## Gold sample

A gold sample has:

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
scripts, direct arbitrary-URL scanner, authentication and Toolforge code, live
editing workflows, runtime tool interception, and generic taskgraph execution
found in the larger upstream stack.

That engineering boundary protects the repository. It does not narrow what a
private sample may research or write.
