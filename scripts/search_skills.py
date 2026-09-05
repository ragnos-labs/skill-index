#!/usr/bin/env python3
"""Search and resolve reviewed skills without loading full instructions."""

from __future__ import annotations

import argparse
import difflib
import json
import re
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
    index = load_json(path)
    if index.get("schema_version") != 1:
        raise ValueError(
            f"unsupported skill index schema: {index.get('schema_version')!r}"
        )
    if not isinstance(index.get("skills"), list):
        raise ValueError("skill index skills must be a list")
    return index


def _phrase(value: str) -> str:
    return " ".join(re.findall(r"[a-z0-9]+", value.lower()))


def _score(query: str, skill: dict[str, Any]) -> tuple[int, float, list[str]]:
    query_tokens = tokens(query) - STOP_WORDS
    if not query_tokens:
        return 0, 0.0, []
    name_tokens = tokens(skill["name"])
    trigger_tokens = tokens(skill.get("triggers", []))
    summary_tokens = tokens(skill.get("summary", ""))
    domain_tokens = tokens(skill.get("domain", ""))
    alias_tokens = tokens(skill.get("aliases", []))
    all_tokens = name_tokens | trigger_tokens | summary_tokens | domain_tokens | alias_tokens
    # Correct only long, closely matching words; never fuzzy-match names on resolve.
    query_tokens = {
        word if word in all_tokens or len(word) < 5 else
        next(iter(difflib.get_close_matches(word, sorted(all_tokens), n=1, cutoff=0.86)), word)
        for word in query_tokens
    }
    matched = sorted(query_tokens & all_tokens)
    score = (
        5 * len(query_tokens & name_tokens)
        + 3 * len(query_tokens & trigger_tokens)
        + 2 * len(query_tokens & summary_tokens)
        + len(query_tokens & domain_tokens)
        + 3 * len(query_tokens & alias_tokens)
    )
    identities = [skill["name"], *skill.get("aliases", [])]
    normalized_query = _phrase(query)
    exact = normalized_query in {_phrase(value) for value in identities}
    scope_terms = skill.get("scope_terms", [])
    if scope_terms and not exact and not (tokens(scope_terms) & query_tokens):
        return 0, 0.0, []
    if exact:
        score += 100
    elif any(f" {_phrase(value)} " in f" {normalized_query} " for value in skill.get("aliases", [])):
        score += 16
    coverage = len(matched) / len(query_tokens)
    return score, coverage, matched


def rank_skills(query: str, skills: list[dict[str, Any]], limit: int = 3) -> dict[str, Any]:
    """Rank supplied metadata without opening bundles or executing their contents."""
    if not isinstance(query, str) or len(query) > 4096:
        raise ValueError("query must be at most 4096 characters")
    if type(limit) is not int or not 1 <= limit <= 10:
        raise ValueError("limit must be between 1 and 10")
    results: list[dict[str, Any]] = []
    for skill in skills:
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
                "exclusions": skill.get("exclusions", []),
            }
        )
    results.sort(key=lambda item: (-item["score"], item["name"]))
    return {"matches": results[:limit], "query": query}


def search(query: str, limit: int = 3, root: Path = ROOT) -> dict[str, Any]:
    return rank_skills(query, load_index(root)["skills"], limit)


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
        "composes": skill.get("composes", []),
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
