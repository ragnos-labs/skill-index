# How Design Kit works

The entry file states the rules. This diagram shows the production slice for
local and CMS work, where the producer is the maker or builder; the table
below it covers the whole job, including mediums another method produces.

```mermaid
flowchart TD
  U["Ask for Design Kit"] --> S
  subgraph KIT["Design Kit, one skill"]
    S["Scope, audience, deliverable and existing project"] --> R["Select one route and load relevant helpers"]
    BR["Brand's own design skill<br/>Spec, tokens, components<br/>Approved library assets by ID"] --> M
    RES["Shared resources<br/>Project assets, scoped CMS references<br/>Mobbin, DesignMD, 21st"] --> M["Inspect actual sources<br/>Choose direction, map sources to output"]
    SDK["UI SDK for interface work<br/>Version-matched components<br/>Keyboard, focus and agent controls"] --> M
    CMS["CMS methods when assigned<br/>Brand, learned corrections, client scope<br/>Exact revisions, authorized output rounds"] --> M
    M --> P["Design pack<br/>Kit digest, brand sources, assets, copy<br/>Layouts, states, acceptance checks"]
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

## One job, from request to recommendation

Every creative job follows this order on every host. A person does not carry
results between stages; the role finishing a stage hands the next role its
work order. Agent work ends at stage 7. Stages 8 and 9 happen only when a
person decides.

| Stage | Owner | Leaves behind |
| --- | --- | --- |
| 1. Intake | The host that received the request | One job record: the ask in the person's words, the client, the deliverables and their kinds, the destination and what the job may change |
| 2. Brief and brand | Director | The brief, the resolved brand record, and for CMS work the learned record read |
| 3. Direction | Director | A checked design pack per deliverable kind |
| 4. Production | The producer for the medium in [mediums.md](mediums.md) | Editable source, renders, and `PRODUCTION-NOTES.md` or its return (sources as used, defects seen) |
| 5. Critique | Critic | Graded findings and a verdict on the actual output |
| 6. Repair | The same producer | Changed output with before and after; two rounds at most |
| 7. Recommendation | Director | One recommendation with reasons, visual and copy together, and the list of decisions that belong to a person |
| 8. Decision | A person | Keep, reject, pick or request changes, with a reason where they give one |
| 9. Learning | The host that records outcomes | Each decision recorded where the next job for that client will read it |

Rules that hold at every stage:

- Stages 3, 4 and 5 are three different roles on substantial work. A small
  edit may skip to stage 4 with a proportionate check.
- The pack is the only handoff into production and into critique, except a
  small edit with no Director. A producer or critic that receives anything
  else on substantial work asks for the pack.
- The Director assembles stage 7 even when the critic's verdict is strong.
  Nobody else recommends, and no agent decides.
- Stage 8 is the only sign-off, and it is not a gate the agents wait on: the
  Director returns the recommendation and stops. An agent's review, a passing
  check and a finished render are not acceptance.
- At stage 9 record only decisions a person actually made, through the host's
  outcome record. Never record a decision on a person's behalf. Where the host
  has no outcome record, list the person's decisions in the return so the
  next job can be given them.
- Publishing and scheduling are separate jobs with their own authority.
