from __future__ import annotations

import sys
import unittest
from copy import deepcopy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from render_indexes import expected_outputs  # noqa: E402
from repository_model import (  # noqa: E402
    build_skill_index,
    composition_errors,
    load_records,
)
from validate_repository import validate  # noqa: E402


class RepositoryTests(unittest.TestCase):
    def test_repository_validates(self) -> None:
        self.assertEqual(validate(ROOT), [])

    def test_generated_outputs_are_current(self) -> None:
        for path, expected in expected_outputs(ROOT).items():
            self.assertTrue(path.is_file(), path)
            self.assertEqual(path.read_text(encoding="utf-8"), expected)

    def test_index_has_one_entry_per_skill_record(self) -> None:
        records = load_records("skills", ROOT)
        index = build_skill_index(ROOT)
        self.assertEqual(
            {record["name"] for record in records},
            {skill["name"] for skill in index["skills"]},
        )

    def test_every_indexed_resource_has_sha256(self) -> None:
        for skill in build_skill_index(ROOT)["skills"]:
            self.assertTrue(skill["resources"])
            for resource in skill["resources"]:
                self.assertRegex(resource["sha256"], r"^[0-9a-f]{64}$")

    def test_composition_graph_is_known_and_acyclic(self) -> None:
        records = load_records("skills", ROOT)
        self.assertEqual(composition_errors(records), [])
        workflow = next(
            record for record in records if record["name"] == "wikipedia-workflow"
        )
        self.assertEqual(
            workflow["composes"],
            [
                "wikipedia-research",
                "wikipedia-writing",
                "wikipedia-review",
                "ai-writing-review",
            ],
        )

    def test_composition_graph_rejects_unknown_self_and_cycles(self) -> None:
        records = [
            {"name": "alpha", "composes": ["beta", "alpha", "missing"]},
            {"name": "beta", "composes": ["alpha"]},
        ]
        errors = composition_errors(deepcopy(records))
        self.assertIn("skill alpha composes itself", errors)
        self.assertIn("skill alpha composes unknown skill missing", errors)
        self.assertIn("composition cycle: alpha -> beta -> alpha", errors)


if __name__ == "__main__":
    unittest.main()
