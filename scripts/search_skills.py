#!/usr/bin/env python3
"""Search and resolve reviewed skills without loading full instructions."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from repository_model import ROOT, bundle_digest, load_json, tokens


STOP_WORDS = {
    "a",
    "an",
    "and",
    "for",
    "how",
    "i",
    "in",
    "of",
    "on",
    "the",
    "to",
    "use",
    "with",
}


def load_index(root: Path = ROOT) -> dict[str, Any]:
    path = root / "index" / "skills.json"
    if not path.is_file():
        raise ValueError("generated skill index is missing; run make index")
    return load_json(path)


def _score(query: str, skill: dict[str, Any]) -> tuple[int, float, list[str]]:
    query_tokens = tokens(query) - STOP_WORDS
    if not query_tokens:
        return 0, 0.0, []
    name_tokens = tokens(skill["name"])
    trigger_tokens = tokens(skill.get("triggers", []))
    summary_tokens = tokens(skill.get("summary", ""))
    domain_tokens = tokens(skill.get("domain", ""))
    all_tokens = name_tokens | trigger_tokens | summary_tokens | domain_tokens
    matched = sorted(query_tokens & all_tokens)
    score = (
        5 * len(query_tokens & name_tokens)
        + 3 * len(query_tokens & trigger_tokens)
        + 2 * len(query_tokens & summary_tokens)
        + len(query_tokens & domain_tokens)
    )
    normalized_query = "-".join(query.lower().split())
    if normalized_query == skill["name"]:
        score += 100
    coverage = len(matched) / len(query_tokens)
    return score, coverage, matched


def search(query: str, limit: int = 3, root: Path = ROOT) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for skill in load_index(root).get("skills", []):
        if skill.get("load_mode") in {"bootstrap", "retired"}:
            continue
        if skill.get("status") not in {"active", "experimental"}:
            continue
        score, coverage, matched = _score(query, skill)
        if score < 4:
            continue
        if coverage < 0.34 and (score < 6 or len(matched) < 2):
            continue
        results.append(
            {
                "domain": skill["domain"],
                "load_mode": skill["load_mode"],
                "match_terms": matched,
                "name": skill["name"],
                "risk": skill["risk"],
                "score": score,
                "status": skill["status"],
                "summary": skill["summary"],
            }
        )
    results.sort(key=lambda item: (-item["score"], item["name"]))
    return {"matches": results[:limit], "query": query}


def list_skills(root: Path = ROOT) -> dict[str, Any]:
    skills = []
    for skill in load_index(root).get("skills", []):
        skills.append(
            {
                "domain": skill["domain"],
                "load_mode": skill["load_mode"],
                "name": skill["name"],
                "status": skill["status"],
                "summary": skill["summary"],
            }
        )
    return {"skills": skills}


def resolve(name: str, root: Path = ROOT) -> dict[str, Any]:
    matches = [
        item for item in load_index(root).get("skills", []) if item.get("name") == name
    ]
    if len(matches) != 1:
        raise ValueError(f"unknown skill: {name}")
    skill = matches[0]
    if skill.get("load_mode") == "retired" or skill.get("status") == "deprecated":
        raise ValueError(f"skill is retired: {name}")
    path = (root / skill["path"]).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"skill path escapes repository: {name}") from exc
    if not path.is_dir() or not (path / "SKILL.md").is_file():
        raise ValueError(f"skill bundle is missing: {name}")
    actual_digest = bundle_digest(path)
    if actual_digest != skill.get("bundle_digest"):
        raise ValueError(f"skill bundle changed after index generation: {name}")
    review = load_json(root / skill["review_path"])
    if review.get("status") != "reviewed" or review.get("bundle_digest") != actual_digest:
        raise ValueError(f"skill review binding is invalid: {name}")
    return {
        "bundle_digest": actual_digest,
        "load_mode": skill["load_mode"],
        "name": name,
        "path": str(path),
        "risk": skill["risk"],
        "side_effects": skill["side_effects"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=3, choices=range(1, 11))
    subparsers.add_parser("list")
    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("name")
    args = parser.parse_args()
    try:
        if args.command == "search":
            result = search(args.query, args.limit)
        elif args.command == "list":
            result = list_skills()
        else:
            result = resolve(args.name)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
