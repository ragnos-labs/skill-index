from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from search_skills import list_skills, load_index, rank_skills, resolve, search  # noqa: E402


class SearchTests(unittest.TestCase):
    def test_documented_wiki_lab_scope_is_preserved(self) -> None:
        self.assertEqual(search("Prepare a Wiki Lab draft")["matches"][0]["name"], "wikipedia-workflow")

    def test_general_review_does_not_rank_encyclopedia_specialist(self) -> None:
        matches = search("Review a completed onboarding guide against its intended audience and outcome with exact file and line citations")["matches"]
        self.assertEqual(matches[0]["name"], "writing-review")
        self.assertFalse(any(item["domain"] == "wikipedia" for item in matches))

    def test_general_research_does_not_claim_wikipedia_fit(self) -> None:
        matches = search("Research managed or self-hosted retrieval with authoritative sources and an evidence-backed recommendation")["matches"]
        self.assertFalse(any(item["domain"] == "wikipedia" for item in matches))

    def test_alias_and_minor_typo(self) -> None:
        self.assertEqual(search("editorial review")["matches"][0]["name"], "writing-review")
        self.assertEqual(search("review writting draft")["matches"][0]["name"], "writing-review")

    def test_exact_names_remain_discoverable(self) -> None:
        for skill in load_index()["skills"]:
            if skill["load_mode"] == "routable":
                self.assertEqual(search(skill["name"])["matches"][0]["name"], skill["name"])

    def test_external_metadata_preserves_invocation_and_exclusions(self) -> None:
        skill = dict(load_index()["skills"][0], name="publish-package", aliases=["publish release"], load_mode="explicit", exclusions=["credentials are not authority"])
        result = rank_skills("publish release", [skill])["matches"][0]
        self.assertEqual(result["load_mode"], "explicit")
        self.assertEqual(result["exclusions"], skill["exclusions"])
        self.assertEqual(rank_skills("publish release", [dict(skill, load_mode="retired")])["matches"], [])

    def test_bounded_query_and_limit(self) -> None:
        for query, limit in [("x" * 4097, 3), ("review", 0), ("review", True)]:
            with self.assertRaises(ValueError):
                rank_skills(query, [], limit)

    def test_routes_clear_writing_intent(self) -> None:
        matches = search("review a writing draft")["matches"]
        self.assertTrue(matches)
        self.assertEqual(matches[0]["name"], "writing-review")

    def test_routes_expanded_agent_paraphrase(self) -> None:
        matches = search(
            "clean up a wordy draft sentence by removing cliches, filler, "
            "and unnecessary emphasis"
        )["matches"]
        self.assertTrue(matches)
        self.assertEqual(matches[0]["name"], "writing-cleanup")

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

    def test_resolve_exposes_composition_without_resolving_dependencies(self) -> None:
        result = resolve("wikipedia-workflow")
        self.assertEqual(
            result["composes"],
            [
                "wikipedia-research",
                "wikipedia-writing",
                "wikipedia-review",
                "ai-writing-review",
            ],
        )
        self.assertNotIn("resources", result)

    def test_schema_one_index_without_composes_resolves_as_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "library"
            (copied_root / "index").mkdir(parents=True)
            (copied_root / "reviews").mkdir()
            index = json.loads((ROOT / "index" / "skills.json").read_text())
            skill = next(
                item for item in index["skills"] if item["name"] == "writing-review"
            )
            skill.pop("composes")
            (copied_root / "index" / "skills.json").write_text(
                json.dumps(index), encoding="utf-8"
            )
            shutil.copy2(
                ROOT / "reviews" / "writing-review.json", copied_root / "reviews"
            )
            shutil.copytree(
                ROOT / "skills" / "writing-review",
                copied_root / "skills" / "writing-review",
            )
            result = resolve("writing-review", copied_root)
        self.assertEqual(result["composes"], [])

    def test_unsupported_index_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            copied_root = Path(temporary) / "library"
            (copied_root / "index").mkdir(parents=True)
            (copied_root / "index" / "skills.json").write_text(
                json.dumps({"schema_version": 99, "skills": []}), encoding="utf-8"
            )
            with self.assertRaisesRegex(ValueError, "unsupported skill index schema"):
                load_index(copied_root)

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
