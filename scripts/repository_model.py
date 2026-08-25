#!/usr/bin/env python3
"""Shared deterministic model helpers for the reviewed skill library."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
NAME_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object in {path}")
    return value


def dump_json(value: Any) -> str:
    return json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def load_records(kind: str, root: Path = ROOT) -> list[dict[str, Any]]:
    directory = root / "records" / kind
    return [load_json(path) for path in sorted(directory.glob("*.json"))]


def load_packets(root: Path = ROOT) -> list[dict[str, Any]]:
    directory = root / "research" / "packets"
    return [load_json(path) for path in sorted(directory.glob("*.json"))]


def parse_frontmatter(path: Path) -> dict[str, str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        return {}
    try:
        end = lines.index("---", 1)
    except ValueError:
        return {}
    values: dict[str, str] = {}
    for line in lines[1:end]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def skill_resources(skill_dir: Path) -> list[dict[str, str]]:
    resources: list[dict[str, str]] = []
    for path in sorted(skill_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(skill_dir).as_posix()
        resources.append({"path": relative, "sha256": sha256_file(path)})
    return resources


def bundle_digest(skill_dir: Path) -> str:
    digest = hashlib.sha256()
    for resource in skill_resources(skill_dir):
        digest.update(resource["path"].encode("utf-8"))
        digest.update(b"\0")
        digest.update(resource["sha256"].encode("ascii"))
        digest.update(b"\n")
    return "sha256:" + digest.hexdigest()


def source_reference_map(root: Path = ROOT) -> dict[str, dict[str, Any]]:
    references: dict[str, dict[str, Any]] = {}
    for packet in load_packets(root):
        packet_id = packet.get("id")
        for source in packet.get("sources", []):
            if isinstance(packet_id, str) and isinstance(source, dict):
                source_id = source.get("id")
                if isinstance(source_id, str):
                    references[f"{packet_id}:{source_id}"] = source
    return references


def build_skill_index(root: Path = ROOT) -> dict[str, Any]:
    records = load_records("skills", root)
    skills: list[dict[str, Any]] = []
    for record in sorted(records, key=lambda item: (item["domain"], item["name"])):
        skill_dir = root / record["path"]
        review = load_json(root / record["review_path"])
        item = dict(record)
        item["composes"] = list(record.get("composes", []))
        item["bundle_digest"] = bundle_digest(skill_dir)
        item["resources"] = skill_resources(skill_dir)
        item["review"] = {
            "reviewed_at": review.get("reviewed_at"),
            "status": review.get("status"),
        }
        skills.append(item)
    return {
        "generated_by": "scripts/render_indexes.py",
        "schema_version": 1,
        "skills": skills,
    }


def composition_errors(records: list[dict[str, Any]]) -> list[str]:
    """Return deterministic validation errors for composition metadata."""

    errors: list[str] = []
    names = {
        record.get("name")
        for record in records
        if isinstance(record.get("name"), str)
    }
    graph: dict[str, list[str]] = {}
    for record in sorted(records, key=lambda item: str(item.get("name", ""))):
        name = record.get("name")
        if not isinstance(name, str):
            continue
        composes = record.get("composes", [])
        if not isinstance(composes, list) or not all(
            isinstance(item, str) and item.strip() for item in composes
        ):
            errors.append(f"skill {name} has invalid composes")
            graph[name] = []
            continue
        if len(composes) != len(set(composes)):
            errors.append(f"skill {name} has duplicate composes entries")
        graph[name] = [item for item in composes if item in names and item != name]
        for target in composes:
            if target == name:
                errors.append(f"skill {name} composes itself")
            elif target not in names:
                errors.append(f"skill {name} composes unknown skill {target}")

    state: dict[str, int] = {}
    stack: list[str] = []
    reported: set[tuple[str, ...]] = set()

    def visit(name: str) -> None:
        state[name] = 1
        stack.append(name)
        for target in graph.get(name, []):
            if state.get(target, 0) == 0:
                visit(target)
            elif state.get(target) == 1:
                start = stack.index(target)
                cycle = tuple(stack[start:] + [target])
                if cycle not in reported:
                    errors.append("composition cycle: " + " -> ".join(cycle))
                    reported.add(cycle)
        stack.pop()
        state[name] = 2

    for name in sorted(graph):
        if state.get(name, 0) == 0:
            visit(name)
    return errors


def _stem(token: str) -> str:
    if len(token) > 4 and token.endswith("ies"):
        return token[:-3] + "y"
    if len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
        return token[:-1]
    return token


def tokens(value: str | Iterable[str]) -> set[str]:
    text = value if isinstance(value, str) else " ".join(value)
    return {_stem(token) for token in TOKEN_PATTERN.findall(text.lower())}
