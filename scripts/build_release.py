#!/usr/bin/env python3
"""Build a deterministic release archive from one clean Git tree."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import re
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

from repository_model import ROOT, dump_json, sha256_file


VERSION_PATTERN = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
REQUIRED_NOTICES = {
    "LICENSE",
    "THIRD_PARTY.md",
    "third_party/MIT-NOTICES.md",
}
GIT_MODES = {"100644": "0644", "100755": "0755"}


def _git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def safe_relative_path(value: str) -> PurePosixPath:
    if not value or "\\" in value:
        raise ValueError(f"unsafe release path: {value!r}")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"unsafe release path: {value!r}")
    path = PurePosixPath(value)
    if path.is_absolute() or path.as_posix() != value:
        raise ValueError(f"unsafe release path: {value!r}")
    return path


def source_path(root: Path, relative: PurePosixPath) -> Path:
    source = root.joinpath(*relative.parts)
    try:
        source.resolve().relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"release path escapes source root: {relative}") from exc
    return source


def tracked_files(root: Path) -> list[dict[str, str]]:
    output = _git(root, "ls-files", "--stage", "-z")
    entries: list[dict[str, str]] = []
    for raw_entry in output.split("\0"):
        if not raw_entry:
            continue
        try:
            metadata, path_value = raw_entry.split("\t", 1)
            git_mode, _object_id, stage = metadata.split(" ", 2)
        except ValueError as exc:
            raise ValueError("invalid Git index entry") from exc
        if stage != "0":
            raise ValueError(f"unmerged Git index entry: {path_value}")
        if git_mode not in GIT_MODES:
            raise ValueError(f"unsupported Git mode {git_mode}: {path_value}")
        relative = safe_relative_path(path_value)
        source = source_path(root, relative)
        if source.is_symlink():
            raise ValueError(f"release cannot contain symlink: {relative}")
        if not source.is_file():
            raise ValueError(f"tracked release file is missing: {relative}")
        entries.append(
            {
                "git_mode": git_mode,
                "mode": GIT_MODES[git_mode],
                "path": relative.as_posix(),
            }
        )
    entries.sort(key=lambda item: item["path"])
    paths = [entry["path"] for entry in entries]
    if len(paths) != len(set(paths)):
        raise ValueError("Git index contains duplicate release paths")
    missing = sorted(REQUIRED_NOTICES - set(paths))
    if missing:
        raise ValueError("release is missing required notices: " + ", ".join(missing))
    return entries


def release_manifest(root: Path, version: str, entries: list[dict[str, str]]) -> dict:
    return {
        "files": [
            {
                "mode": entry["mode"],
                "path": entry["path"],
                "sha256": sha256_file(
                    source_path(root, safe_relative_path(entry["path"]))
                ),
            }
            for entry in entries
        ],
        "release": version,
        "schema_version": 1,
        "source_tree": _git(root, "rev-parse", "HEAD^{tree}"),
    }


def build_archive(root: Path, version: str, destination: Path) -> str:
    if not VERSION_PATTERN.fullmatch(version):
        raise ValueError("version must be vMAJOR.MINOR.PATCH")
    entries = tracked_files(root)
    manifest = dump_json(release_manifest(root, version, entries)).encode("ascii")
    prefix = f"skill-index-{version}"
    tar_buffer = io.BytesIO()
    with tarfile.open(fileobj=tar_buffer, mode="w", format=tarfile.PAX_FORMAT) as archive:
        for entry in entries:
            relative = safe_relative_path(entry["path"])
            source = source_path(root, relative)
            data = source.read_bytes()
            info = tarfile.TarInfo(f"{prefix}/{relative.as_posix()}")
            info.size = len(data)
            info.mode = int(entry["mode"], 8)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            archive.addfile(info, io.BytesIO(data))
        manifest_info = tarfile.TarInfo(f"{prefix}/RELEASE-MANIFEST.json")
        manifest_info.size = len(manifest)
        manifest_info.mode = 0o644
        manifest_info.mtime = 0
        manifest_info.uid = 0
        manifest_info.gid = 0
        manifest_info.uname = ""
        manifest_info.gname = ""
        archive.addfile(manifest_info, io.BytesIO(manifest))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as output:
        with gzip.GzipFile(filename="", mode="wb", fileobj=output, mtime=0) as compressed:
            compressed.write(tar_buffer.getvalue())
    return hashlib.sha256(destination.read_bytes()).hexdigest()


def require_clean(root: Path) -> None:
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("release assembly requires a clean Git tree")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        require_clean(ROOT)
        output_dir = args.output_dir.resolve()
        archive = output_dir / f"skill-index-{args.version}.tar.gz"
        digest = build_archive(ROOT, args.version, archive)
        checksums = output_dir / "SHA256SUMS"
        checksums.write_text(f"{digest}  {archive.name}\n", encoding="ascii")
    except (OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"ERROR: {exc}")
        return 1
    print(f"built {archive.name} sha256:{digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
