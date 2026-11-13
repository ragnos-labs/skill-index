# How Design Kit works

The entry file states the rules; this diagram shows the flow. The producer is the maker or builder.

```mermaid
flowchart TD
  U["Ask for Design Kit"] --> S
  subgraph KIT["Design Kit, one skill"]
    S["Scope, audience, deliverable and existing project"] --> R["Select one route and load relevant helpers"]
    RES["Shared resources<br/>Project assets, scoped CMS references<br/>Mobbin, DesignMD, 21st"] --> M["Inspect actual sources<br/>Choose direction, map sources to output"]
    SDK["UI SDK for interface work<br/>Version-matched components<br/>Keyboard, focus and agent controls"] --> M
    CMS["CMS methods when assigned<br/>Brand, learned corrections, client scope<br/>Exact revisions, authorized output rounds"] --> M
    M --> P["Design pack<br/>Kit digest, tokens, assets, copy<br/>Layouts, states, acceptance checks"]
    Q["Quality methods<br/>Actual renders, behavior checks<br/>Independent critique, focused repair"]
    R --> M
  end
  R --> L["Local Creative Director<br/>Website and product UI"]
  R --> C["CMS Creative Director<br/>CMS graphics and campaigns"]
  L --> P
  C --> P
  P --> B["Builder<br/>Editable UI and applicable SDK behavior"]
  P --> V["CMS Visual Maker<br/>Same kit and admitted resources<br/>Editable graphics and output formats"]
  B --> Q
  V --> Q
  Q --> F["Finished source, renders and evidence"]
  Q -. "Actionable defect to producer" .-> B
  Q -. "Actionable defect to producer" .-> V
```

Provider retrieval is targeted, not a required checklist. CMS account effects, publication and scheduling require their own task authority.
