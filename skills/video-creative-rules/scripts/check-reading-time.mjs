#!/usr/bin/env node
// Reading-time check for a storyboard. No dependencies.
//
// Input: a storyboard JSON with scenes[].texts[]. Each text carries the copy and the
// window in which it is fully settled on screen (entered, not yet exiting).
//
//   { "scenes": [ { "id": "s1", "start": 0, "end": 4.5,
//       "texts": [ { "id": "s1-card", "text": "Ada planned it.", "kind": "line",
//                    "settledStart": 4.05, "settledEnd": 7.5 } ] } ] }
//
// Output: findings in Video Studio's review finding shape (modality visual, category
// brief) plus a summary. Exit 1 when any finding is blocking.

export const LABEL_FLOOR_SECONDS = 0.8;
export const SECONDS_PER_WORD = 0.3;
export const LINE_MINIMUM_SECONDS = 1.2;
export const SEQUENTIAL_SPACING_SECONDS = 1.2;
export const SCENE_BUDGET_RATIO = 0.85;
export const LABEL_MAX_WORDS = 3;
// Timings arrive as floats (3.0 - 2.2 is 0.7999...). Anything within a fifth of a
// frame at 30 fps counts as meeting the floor.
export const TOLERANCE_SECONDS = 0.007;

const round = (n) => Math.round(n * 100) / 100;
const fmt = (n) => round(n).toFixed(1) + "s";

export function words(text) {
  return String(text).trim().split(/\s+/).filter(Boolean).length;
}

export function kindOf(item) {
  if (item.kind === "label" || item.kind === "line") return item.kind;
  return words(item.text) <= LABEL_MAX_WORDS ? "label" : "line";
}

// The floor: how long a viewer needs the text fully settled to read it once.
export function floorSeconds(item) {
  if (kindOf(item) === "label") return LABEL_FLOOR_SECONDS;
  return Math.max(LINE_MINIMUM_SECONDS, SECONDS_PER_WORD * words(item.text));
}

function fail(message) {
  throw new Error("Storyboard is malformed: " + message);
}

function number(value, name) {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0)
    fail(name + " must be a non-negative number");
  return value;
}

export function validate(storyboard) {
  if (!storyboard || !Array.isArray(storyboard.scenes))
    fail("scenes must be an array");
  storyboard.scenes.forEach((scene, i) => {
    if (!scene || typeof scene !== "object")
      fail("scene " + i + " must be an object");
    if (typeof scene.id !== "string" || !scene.id)
      fail("scene " + i + " needs an id");
    number(scene.start, scene.id + ".start");
    number(scene.end, scene.id + ".end");
    if (scene.end <= scene.start) fail(scene.id + ".end must be after start");
    if (!Array.isArray(scene.texts)) fail(scene.id + ".texts must be an array");
    scene.texts.forEach((item, j) => {
      const name = scene.id + ".texts[" + j + "]";
      if (!item || typeof item !== "object") fail(name + " must be an object");
      if (typeof item.id !== "string" || !item.id) fail(name + " needs an id");
      if (typeof item.text !== "string" || !item.text.trim())
        fail(name + " needs text");
      number(item.settledStart, name + ".settledStart");
      number(item.settledEnd, name + ".settledEnd");
      if (item.settledEnd <= item.settledStart)
        fail(name + ".settledEnd must be after settledStart");
      if (
        item.kind !== undefined &&
        item.kind !== "label" &&
        item.kind !== "line"
      )
        fail(name + ".kind must be label or line");
      if (item.optional !== undefined && typeof item.optional !== "boolean")
        fail(name + ".optional must be a boolean");
    });
  });
  return storyboard;
}

// Review finding ids allow [a-zA-Z0-9_-] only, at most 100 characters.
export function findingId(...parts) {
  return parts
    .join("-")
    .replace(/[^a-zA-Z0-9_-]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 100);
}

function finding(id, start, end, severity, summary) {
  return {
    id: findingId(id),
    start: round(start),
    end: round(end),
    modality: "visual",
    severity,
    category: "brief",
    summary,
    repairable: false,
  };
}

export function checkReadingTime(storyboard) {
  validate(storyboard);
  const findings = [];
  let texts = 0;
  for (const scene of storyboard.scenes) {
    const sceneLength = scene.end - scene.start;
    let budget = 0;
    const ordered = [...scene.texts].sort(
      (a, b) => a.settledStart - b.settledStart,
    );
    // Optional text (a footnote, a HUD label) is checked against its own floor but
    // is not required reading, so it stays out of the budget and the spacing rule.
    const required = ordered.filter((item) => !item.optional);
    ordered.forEach((item) => {
      texts += 1;
      const floor = floorSeconds(item);
      if (!item.optional) budget += floor;
      const settled = item.settledEnd - item.settledStart;
      if (settled + TOLERANCE_SECONDS < floor) {
        const severity =
          !item.optional && settled < floor / 2 ? "blocking" : "warning";
        findings.push(
          finding(
            "reading-time-" + item.id,
            item.settledStart,
            item.settledEnd,
            severity,
            `"${item.text}" (${words(item.text)} words, ${kindOf(item)}) needs ${fmt(floor)} settled but holds ${fmt(settled)}. Hold it longer, cut copy, or split the scene; do not speed the reveal.`,
          ),
        );
      }
    });
    required.forEach((item, index) => {
      const previous = required[index - 1];
      if (previous && kindOf(item) === "line" && kindOf(previous) === "line") {
        const gap = item.settledStart - previous.settledStart;
        if (gap + TOLERANCE_SECONDS < SEQUENTIAL_SPACING_SECONDS)
          findings.push(
            finding(
              "reading-time-spacing-" + previous.id + "-" + item.id,
              previous.settledStart,
              item.settledStart,
              "warning",
              `"${previous.text}" and "${item.text}" reveal ${fmt(gap)} apart; readable lines need at least ${fmt(SEQUENTIAL_SPACING_SECONDS)} between reveals. Snap to every other beat or reveal fast and hold the full set.`,
            ),
          );
      }
    });
    if (budget > sceneLength * SCENE_BUDGET_RATIO + TOLERANCE_SECONDS)
      findings.push(
        finding(
          "reading-time-budget-" + scene.id,
          scene.start,
          scene.end,
          budget > sceneLength ? "blocking" : "warning",
          `Scene ${scene.id} carries ${fmt(budget)} of reading floor inside a ${fmt(sceneLength)} scene (budget ${Math.round(SCENE_BUDGET_RATIO * 100)}%). Cut copy or split the scene.`,
        ),
      );
  }
  const blocking = findings.filter((f) => f.severity === "blocking").length;
  return {
    findings,
    summary: {
      scenes: storyboard.scenes.length,
      texts,
      findings: findings.length,
      blocking,
      warnings: findings.length - blocking,
    },
  };
}

async function main(argv) {
  const { readFile } = await import("node:fs/promises");
  const file = argv.find((a) => !a.startsWith("--"));
  const json = argv.includes("--json");
  if (!file) {
    process.stderr.write(
      "usage: check-reading-time.mjs <storyboard.json> [--json]\n",
    );
    return 2;
  }
  let result;
  try {
    result = checkReadingTime(JSON.parse(await readFile(file, "utf8")));
  } catch (error) {
    process.stderr.write(
      String(error && error.message ? error.message : error) + "\n",
    );
    return 2;
  }
  if (json) process.stdout.write(JSON.stringify(result, null, 2) + "\n");
  else {
    for (const f of result.findings)
      process.stdout.write(
        `${f.severity.toUpperCase()} ${f.start}-${f.end}s ${f.summary}\n`,
      );
    const s = result.summary;
    process.stdout.write(
      `${s.texts} text(s) in ${s.scenes} scene(s): ${s.blocking} blocking, ${s.warnings} warning(s)\n`,
    );
  }
  return result.summary.blocking > 0 ? 1 : 0;
}

if (
  process.argv[1] &&
  import.meta.url === new URL("file://" + process.argv[1]).href
) {
  process.exitCode = await main(process.argv.slice(2));
}
