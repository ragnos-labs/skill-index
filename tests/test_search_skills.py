from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from search_skills import list_skills, resolve, search  # noqa: E402


class SearchTests(unittest.TestCase):
    def test_routes_clear_writing_intent(self) -> None:
        matches = search("review a writing draft")["matches"]
        self.assertTrue(matches)
        self.assertEqual(matches[0]["name"], "writing-review")

    def test_routes_clear_wikipedia_research_intent(self) -> None:
        matches = search("Wikipedia source landscape and claim ledger")["matches"]
        self.assertTrue(matches)
        self.assertEqual(matches[0]["name"], "wikipedia-research")

    def test_weak_unanswerable_query_returns_no_match(self) -> None:
        result = search("rotate kubernetes encryption keys")
        self.assertEqual(result["matches"], [])

    def test_bootstrap_skill_is_not_a_search_result(self) -> None:
        result = search("search available skills and load a hidden skill")
        self.assertNotIn("skill-index", [item["name"] for item in result["matches"]])

    def test_list_includes_bootstrap_metadata(self) -> None:
        items = list_skills()["skills"]
        bootstrap = [item for item in items if item["load_mode"] == "bootstrap"]
        self.assertEqual([item["name"] for item in bootstrap], ["skill-index"])

    def test_resolve_returns_reviewed_exact_bundle(self) -> None:
        result = resolve("writing-review")
        self.assertEqual(result["name"], "writing-review")
        self.assertRegex(result["bundle_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertTrue(Path(result["path"]).is_dir())

    def test_resolve_rejects_bundle_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "library"
            (copied_root / "index").mkdir(parents=True)
            (copied_root / "reviews").mkdir()
            shutil.copy2(ROOT / "index" / "skills.json", copied_root / "index")
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
            with self.assertRaisesRegex(ValueError, "changed after index generation"):
                resolve("writing-review", copied_root)

    def test_unknown_skill_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unknown skill"):
            resolve("does-not-exist")


if __name__ == "__main__":
    unittest.main()
