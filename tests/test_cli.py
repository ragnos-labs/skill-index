from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "bin" / "skill-index"


class CliTests(unittest.TestCase):
    def run_cli(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        with tempfile.TemporaryDirectory() as temporary:
            return subprocess.run(
                [str(CLI), *arguments],
                cwd=temporary,
                check=False,
                capture_output=True,
                text=True,
            )

    def test_entrypoint_is_executable(self) -> None:
        self.assertTrue(os.access(CLI, os.X_OK))

    def test_search_works_outside_repository(self) -> None:
        result = self.run_cli("search", "Clean up this draft", "--limit", "3")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["matches"][0]["name"], "writing-cleanup")

    def test_resolve_works_outside_repository(self) -> None:
        result = self.run_cli("resolve", "wikipedia-research")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["name"], "wikipedia-research")
        self.assertTrue(Path(payload["path"]).is_dir())

    def test_resolve_command_rejects_bundle_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "library"
            shutil.copytree(ROOT / "bin", copied_root / "bin")
            shutil.copytree(ROOT / "scripts", copied_root / "scripts")
            (copied_root / "index").mkdir()
            shutil.copy2(ROOT / "index" / "skills.json", copied_root / "index")
            (copied_root / "reviews").mkdir()
            shutil.copy2(
                ROOT / "reviews" / "writing-review.json", copied_root / "reviews"
            )
            shutil.copytree(
                ROOT / "skills" / "writing-review",
                copied_root / "skills" / "writing-review",
            )
            skill_file = copied_root / "skills" / "writing-review" / "SKILL.md"
            skill_file.write_text(
                skill_file.read_text(encoding="utf-8") + "\nUnexpected drift.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [str(copied_root / "bin" / "skill-index"), "resolve", "writing-review"],
                cwd=temporary,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 2)
        self.assertIn("changed after index generation", result.stderr)


if __name__ == "__main__":
    unittest.main()
