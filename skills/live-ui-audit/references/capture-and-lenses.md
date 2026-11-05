# Capture checks and lens questions

## In-page capture

Run one read-only script per surface and matrix cell. It must not click, type,
submit, or change storage. Store its output privately beside the screenshot.

| Check | Method | Known false positives |
| --- | --- | --- |
| Controls | Count native controls and elements with interactive roles; list those without an accessible name | Controls hidden off-screen on purpose |
| Small targets | Visible interactive elements under 24 by 24 CSS pixels; touch-first surfaces may use 44 as a stricter bar | Inline links inside running text |
| Contrast | Text color against the first opaque ancestor background; flag below 4.5 to 1 for body text and 3 to 1 for large text | Text over images or gradients; visually hidden text |
| Duplicate ids | Id values that occur more than once | Rarely harmless; they often break labels and references |
| Overflow | Document scroll width above viewport width; elements whose right edge passes the viewport | Intentionally scrolling carousels or tables |
| Console and network | Errors, warnings, and failed or slow requests during the walk | Browser extension noise |

Also note time to first content, long tasks, and the largest transfers.

## Lens questions

- Structure and wording: does each surface say what it is and what to do
  next? Are labels consistent across surfaces? Is internal jargon or debug text
  visible?
- Visual layout: alignment, spacing, truncation, wrapping at narrow widths,
  overflow, parity between themes, and visible focus.
- Accessibility: names, roles, keyboard order, focus trapping and return in
  dialogs, announcements for asynchronous results, contrast, target size, and
  reduced motion.
- Content and data: wrong, stale, duplicate, or placeholder data; private data
  shown where it should not be; counts that disagree between surfaces.
- Interaction and state: loading, empty, error, and success states; errors
  rendered where the user cannot see them; controls offered where the server
  will refuse the action; state lost on navigation.
- Performance: slow first content, oversized images, repeated requests, layout
  shift, and long tasks.
