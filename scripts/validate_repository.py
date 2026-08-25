#!/usr/bin/env python3
"""Validate records, research, reviews, skills, and neutral repository rules."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

from repository_model import (
    NAME_PATTERN,
    ROOT,
    bundle_digest,
    composition_errors,
    load_json,
    load_packets,
    load_records,
    parse_frontmatter,
)


ALLOWED_STATUSES = {"active", "experimental", "deprecated"}
ALLOWED_LOAD_MODES = {"bootstrap", "routable", "explicit", "retired"}
ALLOWED_RISKS = {"low", "medium", "high"}
ALLOWED_DISPOSITIONS = {"adopted", "inspiration", "reviewed-not-used", "skipped"}
TEXT_SUFFIXES = {".json", ".md", ".py", ".txt", ".yaml", ".yml", ".toml"}
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FULL_REVISION = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def _nonempty_strings(value: Any) -> bool:
    return isinstance(value, list) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def validate(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    required_directories = (
        "skills",
        "domains",
        "records/skills",
        "records/domains",
        "research/packets",
        "reviews",
        "index",
        "tests",
    )
    for relative in required_directories:
        if not (root / relative).is_dir():
            errors.append(f"missing directory {relative}")

    try:
        domain_records = load_records("domains", root)
        skill_records = load_records("skills", root)
        packets = load_packets(root)
    except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
        return [f"invalid maintained JSON: {exc}"]

    domain_names: list[str] = []
    for record in domain_records:
        name = record.get("name")
        if record.get("schema_version") != 1:
            errors.append(f"domain {name!r} schema_version must be 1")
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name):
            errors.append(f"invalid domain name {name!r}")
            continue
        domain_names.append(name)
        if record.get("status") not in ALLOWED_STATUSES:
            errors.append(f"domain {name} has invalid status")
        for field in ("display_name", "documentation"):
            if not isinstance(record.get(field), str) or not record[field].strip():
                errors.append(f"domain {name} has invalid {field}")
        documentation = record.get("documentation")
        if isinstance(documentation, str) and not (root / documentation).is_file():
            errors.append(f"domain {name} documentation is missing")

    actual_domains = {
        path.name for path in (root / "domains").iterdir() if path.is_dir()
    }
    if set(domain_names) != actual_domains:
        errors.append("domain folders and records differ")
    if len(domain_names) != len(set(domain_names)):
        errors.append("duplicate domain records")

    packet_ids: set[str] = set()
    source_refs: set[str] = set()
    for packet in packets:
        packet_id = packet.get("id")
        if packet.get("schema_version") != 1:
            errors.append(f"packet {packet_id!r} schema_version must be 1")
        if not isinstance(packet_id, str) or not NAME_PATTERN.fullmatch(packet_id):
            errors.append(f"invalid packet id {packet_id!r}")
            continue
        if packet_id in packet_ids:
            errors.append(f"duplicate packet id {packet_id}")
        packet_ids.add(packet_id)
        for field in ("question", "method", "researched_at"):
            if not isinstance(packet.get(field), str) or not packet[field].strip():
                errors.append(f"packet {packet_id} has invalid {field}")
        for field in (
            "queries",
            "findings",
            "adopted",
            "rejected",
            "skipped",
            "open_questions",
            "supersedes",
        ):
            if not _nonempty_strings(packet.get(field)):
                if field not in {"open_questions", "supersedes"} or packet.get(field) != []:
                    errors.append(f"packet {packet_id} has invalid {field}")
        sources = packet.get("sources")
        if not isinstance(sources, list) or not sources:
            errors.append(f"packet {packet_id} must contain sources")
            continue
        local_source_ids: set[str] = set()
        for source in sources:
            if not isinstance(source, dict):
                errors.append(f"packet {packet_id} has non-object source")
                continue
            source_id = source.get("id")
            if not isinstance(source_id, str) or not NAME_PATTERN.fullmatch(source_id):
                errors.append(f"packet {packet_id} has invalid source id")
                continue
            if source_id in local_source_ids:
                errors.append(f"packet {packet_id} duplicates source {source_id}")
            local_source_ids.add(source_id)
            source_refs.add(f"{packet_id}:{source_id}")
            for field in ("title", "url", "revision", "license"):
                if not isinstance(source.get(field), str) or not source[field].strip():
                    errors.append(f"source {packet_id}:{source_id} has invalid {field}")
            if source.get("disposition") not in ALLOWED_DISPOSITIONS:
                errors.append(f"source {packet_id}:{source_id} has invalid disposition")
            if not _nonempty_strings(source.get("inspected_paths")):
                errors.append(f"source {packet_id}:{source_id} has no inspected paths")
            if not _nonempty_strings(source.get("findings")):
                errors.append(f"source {packet_id}:{source_id} has no findings")
            revision = source.get("revision")
            if not isinstance(revision, str) or not FULL_REVISION.fullmatch(revision):
                errors.append(f"source {packet_id}:{source_id} revision is not pinned")
            url = source.get("url")
            if isinstance(url, str) and not (
                url.startswith("https://") or url.startswith("local-history:")
            ):
                errors.append(f"source {packet_id}:{source_id} has unsupported URL")

    skill_names: list[str] = []
    active_by_domain = {name: 0 for name in domain_names}
    bootstrap_count = 0
    for record in skill_records:
        name = record.get("name")
        if record.get("schema_version") != 1:
            errors.append(f"skill {name!r} schema_version must be 1")
        if not isinstance(name, str) or not NAME_PATTERN.fullmatch(name) or len(name) > 64:
            errors.append(f"invalid skill name {name!r}")
            continue
        skill_names.append(name)
        domain = record.get("domain")
        if domain not in domain_names:
            errors.append(f"skill {name} uses unknown domain")
        expected_path = f"skills/{name}"
        if record.get("path") != expected_path:
            errors.append(f"skill {name} path must be {expected_path}")
        status = record.get("status")
        if status not in ALLOWED_STATUSES:
            errors.append(f"skill {name} has invalid status")
        if status == "active" and domain in active_by_domain:
            active_by_domain[domain] += 1
        load_mode = record.get("load_mode")
        if load_mode not in ALLOWED_LOAD_MODES:
            errors.append(f"skill {name} has invalid load mode")
        if load_mode == "bootstrap":
            bootstrap_count += 1
        if status == "deprecated" and load_mode != "retired":
            errors.append(f"deprecated skill {name} must be retired")
        if record.get("risk") not in ALLOWED_RISKS:
            errors.append(f"skill {name} has invalid risk")
        for field in ("side_effects", "triggers", "exclusions", "source_refs"):
            if not _nonempty_strings(record.get(field)):
                errors.append(f"skill {name} has invalid {field}")
        summary = record.get("summary")
        if not isinstance(summary, str) or len(summary) < 40 or "|" in summary or "\n" in summary:
            errors.append(f"skill {name} has invalid summary")
        for reference in record.get("source_refs", []):
            if reference not in source_refs:
                errors.append(f"skill {name} has unresolved source {reference}")

        skill_dir = root / expected_path
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            errors.append(f"skill {name} is missing SKILL.md")
            continue
        metadata = parse_frontmatter(skill_file)
        if metadata.get("name") != name:
            errors.append(f"skill {name} frontmatter name differs")
        description = metadata.get("description", "")
        if len(description) < 40 or len(description) > 1024:
            errors.append(f"skill {name} has invalid description")

        review_path = record.get("review_path")
        expected_review = f"reviews/{name}.json"
        if review_path != expected_review:
            errors.append(f"skill {name} review path must be {expected_review}")
            continue
        try:
            review = load_json(root / expected_review)
        except (FileNotFoundError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"skill {name} review is invalid: {exc}")
            continue
        if review.get("schema_version") != 1 or review.get("skill") != name:
            errors.append(f"skill {name} review identity differs")
        review_status = review.get("status")
        if status == "active" and review_status != "reviewed":
            errors.append(f"active skill {name} is not reviewed")
        if status == "experimental" and review_status not in {"pending", "reviewed"}:
            errors.append(f"experimental skill {name} has invalid review status")
        for field in ("reviewed_at", "reviewer"):
            if not isinstance(review.get(field), str) or not review[field].strip():
                errors.append(f"skill {name} review has invalid {field}")
        for field in ("evidence", "limitations", "source_refs"):
            if not _nonempty_strings(review.get(field)):
                errors.append(f"skill {name} review has invalid {field}")
        for reference in review.get("source_refs", []):
            if reference not in source_refs:
                errors.append(f"skill {name} review has unresolved source {reference}")
        digest = review.get("bundle_digest")
        if review_status == "reviewed":
            if not isinstance(digest, str) or not SHA256.fullmatch(digest):
                errors.append(f"skill {name} review has invalid bundle digest")
            elif digest != bundle_digest(skill_dir):
                errors.append(f"skill {name} review digest does not match its bundle")
        elif digest != "":
            errors.append(f"unreviewed skill {name} must have an empty bundle digest")

    actual_skills = {
        path.name for path in (root / "skills").iterdir() if path.is_dir()
    }
    if set(skill_names) != actual_skills:
        errors.append("skill folders and records differ")
    if len(skill_names) != len(set(skill_names)):
        errors.append("duplicate skill records")
    errors.extend(composition_errors(skill_records))
    if bootstrap_count != 1:
        errors.append("exactly one bootstrap skill is required")
    if "skill-index" not in skill_names:
        errors.append("skill-index bootstrap is missing")
    for domain, count in active_by_domain.items():
        if count == 0:
            errors.append(f"active domain {domain} has no active skill")

    expected_reviews = {f"{name}.json" for name in skill_names}
    actual_reviews = {path.name for path in (root / "reviews").glob("*.json")}
    if expected_reviews != actual_reviews:
        errors.append("review files and skill records differ")

    prohibited_terms = (("rag" + "nos"), ("canon" + "ical"))
    prohibited_paths = {
        ".claude",
        ".codex",
        ".pi",
        ".github",
        "CLAUDE.md",
        "agents",
        "openai.yaml",
    }
    for path in sorted(root.rglob("*")):
        if ".git" in path.parts or "runs" in path.parts:
            continue
        if path.is_symlink():
            errors.append(f"symlink is not allowed: {path.relative_to(root)}")
            continue
        relative = path.relative_to(root)
        if any(part in prohibited_paths for part in relative.parts):
            errors.append(f"provider-specific path is not allowed: {relative}")
        if not path.is_file():
            continue
        if path.suffix == ".sh":
            errors.append(f"shell files are not allowed: {relative}")
        if path.suffix in TEXT_SUFFIXES or path.name in {"Makefile", "LICENSE"}:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append(f"text file is not UTF-8: {relative}")
                continue
            if any(ord(character) > 127 for character in text):
                errors.append(f"non-ASCII text in {relative}")
            lowered = text.lower()
            for term in prohibited_terms:
                if term in lowered:
                    errors.append(f"prohibited term in {relative}")
            scaffold_markers = (("TO" + "DO:"), ("[" + "TODO"))
            if any(marker in text for marker in scaffold_markers):
                errors.append(f"unfinished scaffold marker in {relative}")
            if path.suffix == ".md":
                for target in MARKDOWN_LINK.findall(text):
                    if target.startswith(("#", "http://", "https://", "mailto:")):
                        continue
                    target_path = (path.parent / target.split("#", 1)[0]).resolve()
                    if not target_path.exists():
                        errors.append(f"broken link {target!r} in {relative}")

    return errors


def main() -> int:
    errors = validate()
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1
    print(f"validated {len(load_records('skills'))} skills and {len(load_packets())} research packets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
