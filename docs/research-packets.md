# Research and source packets

Research packets answer four questions:

1. What question was investigated?
2. Which exact sources were inspected?
3. What was adopted, rejected, or skipped?
4. Which skills or repository decisions rely on the result?

## Packet shape

Each file in `research/packets/` is JSON with:

- `id`, `question`, `method`, and `researched_at`;
- `queries`, containing the bounded searches performed;
- `sources`, containing packet-scoped source records;
- `findings`, `adopted`, `rejected`, and `skipped` decision summaries;
- `open_questions` for facts that need later verification; and
- optional `supersedes` references for a later refresh.

Repository sources should pin a full 40-character commit revision. Web sources
without a revision record the access date and specific page URL. Always record
the license or state that no license was detected.

`researched_at` is the access date for the sources in the packet. A source
record contains `id`, `title`, `url`, `revision`, `license`, `inspected_paths`,
`findings`, and `disposition`. Allowed dispositions are `adopted`,
`inspiration`, `reviewed-not-used`, and `skipped`.

For example:

```json
{
  "id": "example-runtime",
  "title": "Example runtime",
  "url": "https://github.com/example/runtime",
  "revision": "0123456789abcdef0123456789abcdef01234567",
  "license": "MIT",
  "inspected_paths": ["README.md", "src/search.py"],
  "findings": ["Search returns summaries before full instructions."],
  "disposition": "inspiration"
}
```

## Source references

Skill and review records use:

```text
<packet-id>:<source-id>
```

For example:

```text
skill-index-runtime-landscape:skillport
```

The validator resolves every reference and fails on missing or duplicate IDs.
The generated research index computes `Used by` links from skill and review
records, so packets do not maintain a second destination list.

## Keep packets lightweight

Record short summaries and decisions. Link to external material instead of
copying it. Do not store raw tool output, scraped pages, screenshots, model
transcripts, or generated synthesis that is not needed to explain a decision.

When a source changes materially, create a new packet. The historical packet
continues to explain the earlier decision and exact revision.
