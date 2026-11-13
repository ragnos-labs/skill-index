# UI SDK inside Design Kit

UI SDK here means the interface component library a project already uses,
with its own installed skill or package docs. It is not a model-calling SDK.
Use this contract when the project already depends on that library, or a new
suitable interface has opted into it. Keep the owner's framework and package
manager. Follow the library's installed skill and its version-matched package
docs for component choice, setup, behavior, agent access,
and tests. Do not modify the upstream skill.

Design Kit owns the visual direction: hierarchy, typography, spacing, color,
imagery, responsive composition, compatible code assets, and visual critique.
UI SDK owns the interaction behavior it supplies, including semantics, keyboard,
focus, selection, dismissal, and relevant agent interfaces. Use its primitives
for overlapping behavior. Keep established project architecture and existing
components where appropriate.

21st component code may still contribute layouts, styles, and motion. Retrieve
actual source for a named need, inspect preview, source, dependencies, framework
assumptions, and license or reuse terms, then adapt suitable visual elements to
the project. Recompose overlapping interactive parts using SDK primitives rather
than importing a second competing behavior. Record what was used or rejected
and why; a search result alone is not source inspection or code reuse. Provider
availability and asset suitability are not guaranteed.

The Creative Director supplies one concise direction and a design pack, as
defined in [project-record.md](project-record.md), to the builder. Extend the
project's `DESIGN.md` or existing record. Identify SDK behavior boundaries and
unresolved gaps. Web/UI work does not create CMS records or posts, and shared
method guidance grants no CMS write authority to the local role.

The builder follows the installed SDK documentation and implements the requested
actions and states. Test relevant user and agent actions according to that skill;
inspect actual desktop and mobile pixels, including visual states affected by the
behavior. Review and repair consequential defects.
Record actual retrieval, fallback, visual and functional coverage separately.

Use an independent visual critic for substantial visual judgments when available
and authorized. When that role is unavailable, give the existing reviewer the
explicit visual review method and actual pixels, and label the review
accordingly. Marketing and brand-voice copy stays with the role the host
authorizes for it; the builder does not write campaign copy.
