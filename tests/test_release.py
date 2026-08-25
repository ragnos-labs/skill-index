from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from build_release import build_archive  # noqa: E402
from verify_release import verify  # noqa: E402


class ReleaseTests(unittest.TestCase):
    @staticmethod
    def write_checksums(archive: Path, checksums: Path) -> None:
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        checksums.write_text(f"{digest}  {archive.name}\n", encoding="ascii")

    @staticmethod
    def rewrite_archive(
        source: Path,
        destination: Path,
        mutate_manifest=None,
        duplicate_first: bool = False,
    ) -> None:
        with tarfile.open(source, mode="r:gz") as archive:
            records = []
            for member in archive.getmembers():
                handle = archive.extractfile(member)
                if handle is None:
                    raise AssertionError(member.name)
                records.append((copy.copy(member), handle.read()))
        for index, (member, data) in enumerate(records):
            if member.name.endswith("/RELEASE-MANIFEST.json") and mutate_manifest:
                manifest = json.loads(data)
                mutate_manifest(manifest)
                data = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode(
                    "ascii"
                )
                member.size = len(data)
                records[index] = (member, data)
        with tarfile.open(destination, mode="w:gz") as archive:
            for member, data in records:
                archive.addfile(member, fileobj=io.BytesIO(data))
            if duplicate_first:
                member, data = records[0]
                archive.addfile(copy.copy(member), fileobj=io.BytesIO(data))

    def test_release_archive_is_deterministic_and_preserves_notices(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            first = Path(temporary) / "first.tar.gz"
            second = Path(temporary) / "second.tar.gz"
            build_archive(ROOT, "v0.0.10", first)
            build_archive(ROOT, "v0.0.10", second)
            self.assertEqual(
                hashlib.sha256(first.read_bytes()).hexdigest(),
                hashlib.sha256(second.read_bytes()).hexdigest(),
            )
            with tarfile.open(first, mode="r:gz") as archive:
                names = set(archive.getnames())
            prefix = "skill-index-v0.0.10"
            self.assertIn(f"{prefix}/LICENSE", names)
            self.assertIn(f"{prefix}/THIRD_PARTY.md", names)
            self.assertIn(f"{prefix}/third_party/MIT-NOTICES.md", names)
            self.assertIn(f"{prefix}/RELEASE-MANIFEST.json", names)

    def test_release_rejects_invalid_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "vMAJOR.MINOR.PATCH"):
                build_archive(ROOT, "main", Path(temporary) / "release.tar.gz")

    def test_release_verification_rejects_bad_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            archive = Path(temporary) / "skill-index-v0.0.10.tar.gz"
            build_archive(ROOT, "v0.0.10", archive)
            checksums = Path(temporary) / "SHA256SUMS"
            checksums.write_text(f"{'0' * 64}  {archive.name}\n", encoding="ascii")
            with self.assertRaisesRegex(ValueError, "checksum mismatch"):
                verify(archive, checksums, "v0.0.10")

    def test_release_verification_rejects_unsafe_manifest_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            original = base / "original.tar.gz"
            changed = base / "skill-index-v0.0.10.tar.gz"
            checksums = base / "SHA256SUMS"
            build_archive(ROOT, "v0.0.10", original)

            def mutate(manifest: dict) -> None:
                manifest["files"][0]["path"] = "/etc/passwd"

            self.rewrite_archive(original, changed, mutate_manifest=mutate)
            self.write_checksums(changed, checksums)
            with self.assertRaisesRegex(ValueError, "unsafe release path"):
                verify(changed, checksums, "v0.0.10")

    def test_release_verification_rejects_duplicate_manifest_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            original = base / "original.tar.gz"
            changed = base / "skill-index-v0.0.10.tar.gz"
            checksums = base / "SHA256SUMS"
            build_archive(ROOT, "v0.0.10", original)

            def mutate(manifest: dict) -> None:
                manifest["files"].append(copy.deepcopy(manifest["files"][0]))

            self.rewrite_archive(original, changed, mutate_manifest=mutate)
            self.write_checksums(changed, checksums)
            with self.assertRaisesRegex(ValueError, "duplicate paths"):
                verify(changed, checksums, "v0.0.10")

    def test_release_verification_rejects_duplicate_archive_members(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            original = base / "original.tar.gz"
            changed = base / "skill-index-v0.0.10.tar.gz"
            checksums = base / "SHA256SUMS"
            build_archive(ROOT, "v0.0.10", original)
            self.rewrite_archive(original, changed, duplicate_first=True)
            self.write_checksums(changed, checksums)
            with self.assertRaisesRegex(ValueError, "duplicate archive members"):
                verify(changed, checksums, "v0.0.10")

    def test_filesystem_mode_drift_does_not_change_release(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            clone = base / "source"
            subprocess.run(
                ["git", "clone", "--quiet", "--shared", str(ROOT), str(clone)],
                check=True,
            )
            first = base / "first.tar.gz"
            second = base / "second.tar.gz"
            build_archive(clone, "v0.0.10", first)
            license_path = clone / "LICENSE"
            os.chmod(license_path, license_path.stat().st_mode | 0o111)
            build_archive(clone, "v0.0.10", second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            checksums = base / "SHA256SUMS"
            self.write_checksums(second, checksums)
            verify(second, checksums, "v0.0.10", root=clone)


if __name__ == "__main__":
    unittest.main()
