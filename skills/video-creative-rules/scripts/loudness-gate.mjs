#!/usr/bin/env node
// Two-pass loudness normalization for a delivered render. No dependencies beyond
// ffmpeg on PATH (or FFMPEG_BINARY).
//
//   node loudness-gate.mjs <input> <output> [target LUFS] [true peak dBTP]
//
// Defaults: -16 LUFS integrated, -1.5 dBTP, linear (no dynamic pumping). The video
// stream is copied untouched; only audio is re-encoded. Prints one JSON report with
// the measured loudness before and after.

import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";

export const DEFAULT_TARGET_LUFS = -16;
export const DEFAULT_TRUE_PEAK_DBTP = -1.5;

function ffmpeg(binary, args) {
  const run = spawnSync(binary, args, {
    encoding: "utf8",
    maxBuffer: 64 * 1024 * 1024,
  });
  if (run.error)
    throw new Error("ffmpeg could not start: " + run.error.message);
  return run;
}

// ffmpeg prints the ebur128 summary on stderr.
export function parseEbur128(stderr) {
  const summary = stderr.slice(stderr.lastIndexOf("Integrated loudness"));
  const integrated = /I:\s*(-?[\d.]+|-inf)\s*LUFS/.exec(summary);
  const peak = /Peak:\s*(-?[\d.]+|-inf)\s*dBFS/.exec(summary);
  if (!integrated || !peak) throw new Error("Loudness could not be measured");
  const number = (value) => (value === "-inf" ? -Infinity : Number(value));
  return {
    integratedLufs: number(integrated[1]),
    truePeakDbfs: number(peak[1]),
  };
}

export function measure(binary, file) {
  const run = ffmpeg(binary, [
    "-hide_banner",
    "-nostats",
    "-i",
    file,
    "-vn",
    "-af",
    "ebur128=peak=true",
    "-f",
    "null",
    "-",
  ]);
  if (run.status !== 0) throw new Error("Loudness measurement failed");
  return parseEbur128(run.stderr);
}

// The loudnorm analysis pass prints a JSON object at the end of stderr.
export function parseLoudnormAnalysis(stderr) {
  const start = stderr.lastIndexOf("{"),
    end = stderr.lastIndexOf("}");
  if (start < 0 || end < start) throw new Error("loudnorm analysis failed");
  const value = JSON.parse(stderr.slice(start, end + 1));
  for (const key of [
    "input_i",
    "input_tp",
    "input_lra",
    "input_thresh",
    "target_offset",
  ])
    if (typeof value[key] !== "string")
      throw new Error("loudnorm analysis is missing " + key);
  return value;
}

export function normalize({
  input,
  output,
  target = DEFAULT_TARGET_LUFS,
  peak = DEFAULT_TRUE_PEAK_DBTP,
  binary = process.env.FFMPEG_BINARY || "ffmpeg",
}) {
  if (!existsSync(input)) throw new Error("input not found: " + input);
  if (!Number.isFinite(target) || !Number.isFinite(peak))
    throw new Error("target and true peak must be numbers");
  const before = measure(binary, input);
  if (before.integratedLufs === -Infinity)
    throw new Error("input has no measurable audio");
  const filter = `loudnorm=I=${target}:TP=${peak}:LRA=11`;
  const analysis = ffmpeg(binary, [
    "-hide_banner",
    "-nostats",
    "-i",
    input,
    "-vn",
    "-af",
    filter + ":print_format=json",
    "-f",
    "null",
    "-",
  ]);
  if (analysis.status !== 0) throw new Error("loudnorm analysis failed");
  const m = parseLoudnormAnalysis(analysis.stderr);
  const apply = ffmpeg(binary, [
    "-y",
    "-hide_banner",
    "-nostats",
    "-v",
    "error",
    "-i",
    input,
    "-map",
    "0:v?",
    "-map",
    "0:a",
    "-af",
    `${filter}:measured_I=${m.input_i}:measured_TP=${m.input_tp}:measured_LRA=${m.input_lra}:measured_thresh=${m.input_thresh}:offset=${m.target_offset}:linear=true`,
    "-c:v",
    "copy",
    "-c:a",
    "aac",
    "-b:a",
    "192k",
    "-movflags",
    "+faststart",
    output,
  ]);
  if (apply.status !== 0)
    throw new Error("loudness normalization failed: " + apply.stderr.trim());
  return {
    input,
    output,
    target: { integratedLufs: target, truePeakDbfs: peak },
    before,
    after: measure(binary, output),
  };
}

function main(argv) {
  const [input, output, target, peak] = argv;
  if (!input || !output) {
    process.stderr.write(
      "usage: loudness-gate.mjs <input> <output> [target LUFS] [true peak dBTP]\n",
    );
    return 2;
  }
  try {
    const report = normalize({
      input,
      output,
      target: target === undefined ? DEFAULT_TARGET_LUFS : Number(target),
      peak: peak === undefined ? DEFAULT_TRUE_PEAK_DBTP : Number(peak),
    });
    process.stdout.write(JSON.stringify(report) + "\n");
    return 0;
  } catch (error) {
    process.stderr.write(
      String(error && error.message ? error.message : error) + "\n",
    );
    return 1;
  }
}

if (
  process.argv[1] &&
  import.meta.url === new URL("file://" + process.argv[1]).href
) {
  process.exitCode = main(process.argv.slice(2));
}
