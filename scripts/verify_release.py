#!/usr/bin/env python3
"""Verify a deterministic release archive against its source tree."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

from build_release import (
    VERSION_PATTERN,
    release_manifest,
    require_clean,
    safe_relative_path,
    tracked_files,
)
from repository_model import ROOT


def _tree(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD^{tree}"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def verify(
    archive_path: Path,
    checksums_path: Path,
    version: str,
    root: Path = ROOT,
) -> None:
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("version must be vMAJOR.MINOR.PATCH")
    expected_line = checksums_path.read_text(encoding="ascii").strip()
    expected_digest, expected_name = expected_line.split("  ", 1)
    if expected_name != archive_path.name:
        raise ValueError("checksum filename does not match archive")
    actual_digest = hashlib.sha256(archive_path.read_bytes()).hexdigest()
    if actual_digest != expected_digest:
        raise ValueError("archive checksum mismatch")

    prefix = f"skill-index-{version}"
    with tarfile.open(archive_path, mode="r:gz") as archive:
        members = archive.getmembers()
        member_names = [member.name for member in members]
        if len(member_names) != len(set(member_names)):
            raise ValueError("release contains duplicate archive members")
        for member in members:
            path = safe_relative_path(member.name)
            if len(path.parts) < 2 or path.parts[0] != prefix:
                raise ValueError(f"unsafe archive path: {member.name}")
            if not member.isfile():
                raise ValueError(f"release contains non-file member: {member.name}")
        manifest_member = archive.getmember(f"{prefix}/RELEASE-MANIFEST.json")
        manifest_handle = archive.extractfile(manifest_member)
        if manifest_handle is None:
            raise ValueError("release manifest is unreadable")
        manifest = json.loads(manifest_handle.read())
        file_entries = manifest.get("files")
        if not isinstance(file_entries, list):
            raise ValueError("release manifest files are invalid")
        listed_paths: list[str] = []
        for entry in file_entries:
            if not isinstance(entry, dict) or set(entry) != {"mode", "path", "sha256"}:
                raise ValueError("release manifest file entry is invalid")
            if not isinstance(entry.get("path"), str):
                raise ValueError("release manifest file path is invalid")
            listed_paths.append(safe_relative_path(entry["path"]).as_posix())
        if len(listed_paths) != len(set(listed_paths)):
            raise ValueError("release manifest contains duplicate paths")

        expected_manifest = release_manifest(root, version, tracked_files(root))
        if manifest != expected_manifest:
            raise ValueError("release manifest differs from tracked source")
        expected_members = {
            f"{prefix}/{entry['path']}" for entry in expected_manifest["files"]
        }
        expected_members.add(f"{prefix}/RELEASE-MANIFEST.json")
        actual_members = set(member_names)
        if actual_members != expected_members:
            raise ValueError("release members differ from manifest")
        for entry in expected_manifest["files"]:
            relative = entry["path"]
            member = archive.getmember(f"{prefix}/{relative}")
            handle = archive.extractfile(member)
            if handle is None:
                raise ValueError(f"release member is unreadable: {relative}")
            digest = hashlib.sha256(handle.read()).hexdigest()
            if digest != entry.get("sha256"):
                raise ValueError(f"release member digest differs: {relative}")
            if member.mode != int(entry["mode"], 8):
                raise ValueError(f"release member mode differs: {relative}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--checksums", required=True, type=Path)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    try:
        require_clean(ROOT)
        verify(args.archive.resolve(), args.checksums.resolve(), args.version)
    except (
        OSError,
        KeyError,
        json.JSONDecodeError,
        subprocess.CalledProcessError,
        ValueError,
    ) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"verified {args.archive.name} against {args.version} and {_tree(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
