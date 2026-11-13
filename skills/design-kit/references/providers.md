# Design kit providers

Provider operations below were collected on 2026-11-12; selected routes were
tested again on 2026-11-13. Dated observations are evidence, not permanent
availability or pricing guarantees. Inspect the executing host's current schema
before using a tool. An unknown option ends that invocation approach; rediscover
the supported interface rather than guessing.

## Mobbin (MCP)

- Access: Mobbin's MCP server, signed in with the user's Mobbin account. No
  key in the environment.
- Read tools: `search_screens` (one screen; `platform` ios or web; up to 30
  results; `mode` deep or standard), `search_flows` (one journey; up to 10
  per page), `search_sections` (website sections such as pricing or footer),
  `list_collections`, `get_collection_contents`.
- Write tools: `create_collection`, `save_content`, `add_comment`. Use only
  when the user asked to save or comment.
- Keep `task_intent` and `output_destination` consistent for the task.
  `output_destination` is `code` for implementation, `design_tool` for a canvas,
  or `doc` for a spec. `output_tool`, when supported, identifies an actual
  product/tool; do not duplicate the destination value there. Inspect the schema.
- Cite each reference by its `mobbin_url`. Download from `image_url` when an
  image must be kept under its permitted use; media URLs may expire. If a result carries an
  `ai_usage_notice`, show its text to the user unchanged.
- Seen once on 2026-11-12: a host reported the server as connected while
  the working session had no Mobbin tools. Judge access by the session's
  own tool list. When tools are absent, discover the existing same-account
  route before asking for setup. A supported headless host that already holds
  the connection can perform searches within the assignment's existing effects
  and account scope. Allow only the needed reads and read back the result. Ask
  for a real human login/account action only when the supported route needs it.
- Seen on 2026-11-12: returned links carried tracking parameters. Remove those
  parameters when citing, preserving any query required to identify the resource.
- Seen on 2026-11-13: one host exposed native Mobbin tools and another did not.
  When handing a search to the host that has them, scope the handoff to the
  required reads, retain exact tool output, and inspect the returned images.
  Avoid large results that truncate URLs or `ai_usage_notice`; a truncated
  result is incomplete.
- A follow-up with `limit: 1` returned complete metadata and a retrievable image.
  Start small; larger default image responses can exceed the host's output limit.
  For headless tasks, admit the search required by the medium (`search_screens`,
  `search_flows`, or `search_sections`) in that run's tool permissions. A runner
  allowing only screens cannot perform a sections search. Respect an actual
  refusal; distinguish runner/tool scope from provider authentication.

## DesignMD (MCP)

- Access: remote MCP at `https://www.designmd.co/api/mcp` with a bearer
  token. Hosts bind it from `DESIGNMD_TOKEN`; the same key may be stored as
  `DESIGNMD_API_KEY`. Resolve the name the host's MCP config actually reads
  before reporting the key missing.
- Free access check: `list_categories`.
- Find: `search_designs`, `compare_designs`, `get_design`,
  `get_full_system`, `search_blocks`, `list_blocks`, `recommend_blocks`,
  `get_block`, `search_patterns`, `get_pattern`, `search_experiences`,
  `get_experience`, `list_motion_systems`, `get_motion`.
- Plan: `plan_build`, `get_skill`, `get_prompt_pack`,
  `get_experience_prompt`.
- Export to code: `generate_css_variables`, `generate_tailwind_config`,
  `generate_shadcn_theme`. Prefer these over hand-copying tokens.
- Check: `certify_conformance` grades a build against a chosen system.
- Writes: `install_block`, `install_experience`, and
  `record_design_decision` change the project or the account. Use them
  only when the user asked.
- Seen on 2026-11-12: `search_designs` matched loosely, and a phrase with
  no matching tag returned unrelated well-known systems. Query with the tag words the results show
  (for example editorial, terminal, luxury, playful, minimal) and check the
  tags of each hit before treating it as a fit.
- Seen on 2026-11-12: not every slug that search returned could be
  exported, and one export was unusable (text and background the same
  color). Read the output; use
  `get_design` when an export fails.
- Seen on 2026-11-12: `search_patterns` returned general component
  patterns and was weak on intent queries; searching by a pattern's own
  name (timeline, calendar view, chat interface, card grid) worked.
  `search_experiences` returned marketing-page templates, not app
  surfaces. `list_motion_systems` lists
  named motion systems to pair with a token set.
- Strong for inspectable tokens, type hierarchy, spacing, components, and
  rationale. `plan_build` can choose a candidate that conflicts with the
  brief or add unrequested blocks; review its pick and fall back to a
  targeted `search_designs`.
- Plan quota and rate limits are not exposed by the content tools. Do not
  assume unlimited access from a successful call.
- Seen on 2026-11-13: a host without native DesignMD tools still reached the
  account through its documented credential route; categories, search, detail,
  and CSS export succeeded. Native tool absence in one session does not mean
  account access is missing. Use the executor's documented credential route,
  not pasted keys or a new integration. A 429 on a light read is a rate limit:
  record it once and continue without retry loops.
- Seen on 2026-11-13: one system's CSS export was mechanically valid but replaced specified serif
  typography and square geometry with generic fonts and rounded corners.
  Compare exports to the detailed system and brief, not only valid CSS syntax.

## 21st.dev (CLI)

- When the host installs a 21st CLI skill or wrapper, load and use it rather
  than `npx`; a wrapper may preserve search filters across package updates.
- Access: `21st` (`@21st-dev/cli`). Credential is a login session
  (`21st login`) or an API key in `API_KEY_21ST` or `TWENTYFIRST_TOKEN`.
  When a working login session exists, prefer it and leave those variables
  unset so a stale key does not override it.
- Free: `21st whoami`, `21st usage`, `21st search`, `21st theme <id>`,
  `21st logo <name>`.
- Daily quota: `21st get <id>` and `21st add <user>/<slug>` retrieve code.
- Separate AI access and credits: `21st generate`, `iterate`, `take`. Check
  `21st usage --json` first; do not retry after `ai_subscription_required`.
- Seen on 2026-11-12: component search took descriptive phrases well,
  while multi-word theme queries returned nothing and single words
  returned themes. Search themes one word at a time.
- Use `--type component`, `--type theme`, or `--type template`, and `--json`
  for machine output. Full template archives are not available from the CLI;
  use the author's linked source when one exists.
- Hosts may provide deeper 21st skills for building, exploring, reviewing,
  and publishing UI; prefer those when present for single-provider work.
- Seen on 2026-11-13: search worked; usage reported paid retrieval access and
  `aiGenerationEnabled: false`. That is not permission
  to enable generation. Inspect the current result rather than assuming limits.
- Search with `--type theme`, then `21st theme <id>` retrieves actual CSS.
  `21st get <id>` retrieves component code; it does not require installing it.
  Inspect source, dependencies, preview, and reuse terms before adaptation.

## Existing project and optional sources

- Agent CMS: start with `get_library_context`, bind the assigned workspace, and
  use project/learned/brand/reference reads through its skill. Load the actual
  preview bytes before describing visual qualities. Hosted generation may not be
  configured; the context read says so. Use the local maker and upload only for
  an authorized CMS delivery.
- Image generation: use the selected host's image skill for raster assets.
  Each host must discover its own included route; do not assume parity or
  silently switch to separately paid generation.
- Static editing: prefer the existing project renderer. Editable HTML/CSS or
  SVG plus actual PNG renders are suitable for code-led stills. Do not upgrade
  software silently.
- Browser review: use the project's existing tests/browser tooling. Each
  executor verifies its own browser runtime. Inspect screenshots and test interactions separately.
- Brand.dev: style guide, fonts, simplified brand (logos and colors), and
  page screenshots for a domain. Often reached through a tool gateway; search
  the gateway catalog for `brand.styleguide`, `brand.fonts`, and
  `brand.retrieve-simplified`, inspect the endpoint, then call it. Each call
  is metered.
- Additional image/icon/illustration providers use their own skills and budgets.
  Standalone image generation is routed to the image skill; imagery used inside
  a Design Kit deliverable remains part of the design workflow.

## Not included

v0 generation, Figma, and front-end checklist servers are not part of this kit.
Use one only when the host has a verified working route and the task asks for it.
