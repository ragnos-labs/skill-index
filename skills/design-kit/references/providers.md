# Design kit providers

Facts verified on 2026-11-12. Provider surfaces change; when a call fails
with an unknown tool or option, list the provider's tools again before
guessing.

## Mobbin (MCP)

- Access: Mobbin's MCP server, signed in with the user's Mobbin account. No
  key in the environment.
- Read tools: `search_screens` (one screen; `platform` ios or web; up to 30
  results; `mode` deep or standard), `search_flows` (one journey; up to 10
  per page), `search_sections` (website sections such as pricing or footer),
  `list_collections`, `get_collection_contents`.
- Write tools: `create_collection`, `save_content`, `add_comment`. Use only
  when the user asked to save or comment.
- Pass the same `task_intent`, `output_destination`, and `output_tool` on
  every call in one task. `output_destination` is `code` when the results
  feed implementation, `design_tool` for a canvas, `doc` for a spec.
- Cite each reference by its `mobbin_url`. Download from `image_url` when an
  image must be kept; image URLs expire after 30 days. If a result carries an
  `ai_usage_notice`, show its text to the user unchanged.

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
- Strong for inspectable tokens, type hierarchy, spacing, components, and
  rationale. `plan_build` can choose a candidate that conflicts with the
  brief or add unrequested blocks; review its pick and fall back to a
  targeted `search_designs`.
- Plan quota and rate limits are not exposed by the content tools. Do not
  assume unlimited access from a successful call.

## 21st.dev (CLI)

- Access: `21st` (`npx @21st-dev/cli`). Credential is a login session
  (`21st login`) or an API key in `API_KEY_21ST` or `TWENTYFIRST_TOKEN`.
  When a working login session exists, prefer it and leave those variables
  unset so a stale key does not override it.
- Free: `21st whoami`, `21st usage`, `21st search`, `21st theme <id>`,
  `21st logo <name>`.
- Daily quota: `21st get <id>` and `21st add <user>/<slug>` retrieve code.
- Separate AI access and credits: `21st generate`, `iterate`, `take`. Check
  `21st usage --json` first; do not retry after `ai_subscription_required`.
- Use `--type component`, `--type theme`, or `--type template`, and `--json`
  for machine output. Full template archives are not available from the CLI;
  use the author's linked source when one exists.
- Hosts may provide deeper 21st skills for building, exploring, reviewing,
  and publishing UI; prefer those when present for single-provider work.

## v0 (API)

- Access: v0 Platform API at `https://api.v0.dev`, key in `V0_API_KEY`,
  TypeScript SDK `v0-sdk`.
- Create: `POST /v1/chats` (SDK `v0.chats.create`) with the prompt; the
  response carries the chat ID, a web URL, and generated files. Continue a
  revision in the same chat rather than creating a new one.
- `POST /v1/deployments` (SDK `v0.deployments.create`) publishes a live
  deployment. It is a publish: only on the user's explicit yes.
- Chats can attach custom MCP servers (`v0.mcpServers.create`). Do not
  attach a server that carries the user's credentials unless asked.
- v0 also offers an OpenAI-compatible model endpoint for code generation;
  prefer the Platform API when you need files and a shareable chat.
- Hosts may wrap the key in a client command that injects it at run time;
  use that wrapper when present instead of exporting the key.
- Every generation is metered. Batch the brief into one well-formed prompt
  instead of many small ones.

## Optional sources

- Brand.dev: style guide, fonts, simplified brand (logos and colors), and
  page screenshots for a domain. Often reached through a tool gateway; search
  the gateway catalog for `brand.styleguide`, `brand.fonts`, and
  `brand.retrieve-simplified`, inspect the endpoint, then call it. Each call
  is metered.
- Figma MCP: read a file's design context and variables, or write a design
  into a file. Writing to a user's file is a change to their work; do it only
  on request and in the file they named.
- Front-end checklist MCP: static review of changed code and an audit of a
  public URL. Treat a clean result as no provable issue, not a pass.
- Image, icon, and illustration generators (for example Recraft or
  Ideogram) are out of scope for this skill; use an image or brand skill.
