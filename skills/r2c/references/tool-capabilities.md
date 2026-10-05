# Select a research operation

These are routing hints from official documentation inspected on 2026-10-05,
not a fixed tool allowlist or a claim of live availability. Read the relevant
current schema/help before using an unfamiliar operation. Discovery should be
bounded to the next evidence gap; do not invoke every provider.

| Need | Candidate operation | Check before execution |
| --- | --- | --- |
| Discover recent or semantically related sources | Exa search; native web search; Firecrawl search | Date/domain filters, result limit, original URLs and returned content |
| Read known pages | Exa contents/web fetch; Firecrawl scrape; native browser/web read | Actual readable evidence, extraction completeness and redirects |
| Similar sources or bounded multi-step research | Exa findSimilar, answer, deep search or agent | Underlying citations, cost, asynchronous completion and source independence |
| A named website collection | Firecrawl map/crawl/extract | Exact scope, page cap, total credit ceiling and task status |
| Specialized external datasets | Firecrawl Alexandria or Exa Connect | Exact provider, operation schema, availability, rights, upstream source and price |
| Social video/posts, profiles, captions or comments | ScrapeCreators platform-specific endpoint | Native ID, pagination, caption language/time offsets, deleted/private/pending state |
| A future research tool | Installed host discovery and official contract | Same evidence, privacy, authority, cost and completion checks |

## Firecrawl and Alexandria

Use normal search/scrape for web discovery and page extraction. Alexandria
adds provider datasets through Firecrawl. Inspect its relevant categories and
provider tools, refine the query, then inspect the selected tool's required
options, response structure, pagination and per-operation price. Execute only
through a supported installed client. Do not invent options from the label.

Discovery and execution are different stages. The inspected discovery calls
were free; dataset execution can exceed ordinary scrape costs. One inspected
Particle podcast transcript tool required an episode ID and listed 15 credits
for a full transcript. That exceeds a host's 5-credit default ceiling. An
excerpt is affordable only if its actual quote confirms that. Do not accept
organization terms, switch identities or relax privacy requirements to unlock
an endpoint. Verify current zero-retention availability where required.

Official references: [Alexandria](https://docs.firecrawl.dev/features/alexandria),
[web search](https://docs.firecrawl.dev/features/search).

## Exa

The current MCP documentation names search, web fetch, advanced search and
agent tools; installed clients expose different subsets. Inspect the actual
client instead of assuming a documentation tool name is callable. The inspected
CLI supported bounded search and a generic authenticated API route for contents,
findSimilar, answer, research, agent, monitors, batches and websets. Help proved
a client contract, not successful endpoint access.

Use search/contents for small jobs. Deep search or an agent can resolve a bounded
multi-step question when the additional cost is justified. Preserve returned
job IDs privately; poll the exact job until terminal and verify its evidence.
Exa Connect lets an agent choose specified premium data sources. Inspect the
supported data-source identifiers and limits; do not enable all providers by
default. Reused underlying data is not independent corroboration.

Websets, monitors and batches are distinct operations that can persist state,
consume recurring credits or expand research volume. Ordinary research does
not authorize creating those jobs. Never infer subscription or write authority
from an API route existing.

Official references: [MCP tools](https://exa.ai/docs/get-started/exa-mcp),
[Connect](https://exa.ai/docs/agent/connect/overview),
[deep search](https://exa.ai/docs/search/deep-search),
[Websets](https://exa.ai/docs/websets/quickstart).

## ScrapeCreators

Use the current [endpoint catalogue](https://docs.scrapecreators.com/llms.txt)
and [OpenAPI schema](https://docs.scrapecreators.com/openapi.json) to choose the
specific platform operation. The catalogue includes video/post data, platform
search, profile/feed data, transcripts, comments and advertising-library data.
A native endpoint catalogue is not proof of a universal semantic search API.

Use a qualified existing adapter/client. Broader documentation coverage does
not mean every operation is installed or enabled. Inspect native IDs, request
parameters, pagination and credit cost before calling. For YouTube transcripts,
preserve original caption JSON and timing fields such as startMs/endMs and
startTimeText, plus language/audio metadata. Parse units and nulls according to
the current schema. Provider transcripts and generated summaries are separate
artifacts; preserve provenance for both.

Official reference: [YouTube transcript](https://docs.scrapecreators.com/v1/youtube/video/transcript/).
