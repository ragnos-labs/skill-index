---
name: ai-writing-review
description: Find, grade, and explain common AI-like writing patterns in supplied text and recommend repairs. Use for the user's own drafts or client writing; this is a prose-pattern review, not proof of authorship. Use writing-cleanup when the primary request is a rewrite.
---

# AI Writing Review

Identify writing patterns that often make generated or heavily templated prose
feel generic. Improve the text without flattening it into another house style.

## Choose the mode

- **Detect**: mark passages and explain the patterns present.
- **Grade**: score pattern families and identify the highest-impact repairs.
- **Compare**: evaluate before and after versions for real improvement and lost
  information.
- **Review and clean**: record the findings, then apply `writing-cleanup` when
  the user requests a revised artifact.

This skill cannot establish whether a person used AI from prose alone. Do not
report an authorship probability or accuse a writer. Report observable language
patterns, confidence in each finding, and the effect on the reader.

## Inspect the text

Read [references/pattern-catalog.md](references/pattern-catalog.md) for the full
catalog. Look for clusters rather than treating one phrase as proof.

Evaluate:

- generic framing and unsupported significance;
- predictable structure and repetitive section jobs;
- sentence rhythm, variation, and over-regularity;
- vague attribution, empty authority, or fabricated specificity;
- unnecessary signposting, recaps, and conclusion repetition;
- inflated, abstract, promotional, or synthetic-sounding diction;
- excessive hedging, qualification, or balanced-sounding filler;
- canned contrasts, triplets, fragments, and rhetorical questions;
- publication residue such as prompts, notes, or meta-commentary; and
- factual, citation, quotation, or meaning drift introduced by prior rewrites.

## Grade

Score each applicable family from 0 to 4:

- 0: absent or negligible;
- 1: occasional and harmless;
- 2: noticeable but localized;
- 3: frequent and distracting; and
- 4: dominant enough to make the piece feel generic or unreliable.

Do not average the scores into an "AI probability." Lead with the two or three
families that most affect quality.

## Recommend repairs

1. Lock names, facts, quantities, dates, quotations, citations, links, and
   commitments.
2. Repair structure before polishing sentences.
3. Replace generic claims with supported specifics or remove them.
4. Vary rhythm by following the thought, not by randomly changing sentence
   length.
5. Restore the author's real directness, warmth, technical depth, humor, or
   rough edges when evidence of that voice exists.
6. Compare the revision with the original for lost meaning or support.

Do not add anecdotes, personal experiences, quotations, sources, or results to
make the writing seem human. Do not deliberately insert errors, slang, or
awkwardness to evade a detector.

## Deliver

For detection or grading, return:

1. overall prose-quality judgment;
2. highest-impact pattern findings with excerpts;
3. dimensional scores;
4. recommended repair order; and
5. an authorship caveat only if the user asked whether AI wrote it.

When cleaning is requested, apply the repair plan through `writing-cleanup` and
return the revised text first, followed by a compact change note and any factual
or source questions that remain.
