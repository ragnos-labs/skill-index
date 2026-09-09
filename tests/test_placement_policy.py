from __future__ import annotations

import json
import re
import unittest
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONTROL_DIRECTORY = "." + "rag" + "nos"
POLICY_PATH = ROOT / CONTROL_DIRECTORY / "placement.json"
SKILL_NAME_PATTERN = r"[a-z0-9]+(?:-[a-z0-9]+)*"


def load_policy() -> dict[str, Any]:
    value = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError("placement policy must be an object")
    return value


def template_matches(template: str, destination: str) -> bool:
    token = re.escape("{skill_name}")
    pattern = re.escape(template).replace(token, SKILL_NAME_PATTERN)
    return re.fullmatch(pattern, destination) is not None


def placement_allowed(
    policy: dict[str, Any],
    *,
    scope: str,
    destination: str,
    material: object = "public",
    producer: str | None = None,
) -> bool:
    if scope not in policy["admission"]["accepted"]:
        return False
    if (
        not isinstance(material, str)
        or material not in policy["material_allowlist"]
    ):
        return False

    generated = policy["destinations"]["generated_indexes"]
    forbidden = policy["forbidden_roots"]
    for root in forbidden["runtime"]:
        if destination.startswith(root):
            return False
    for root in forbidden["generated"]:
        if destination.startswith(root):
            return (
                destination in generated["paths"]
                and producer == generated["command"]
                and generated["direct_write"] is False
            )

    return any(
        template_matches(item["path"], destination)
        for item in policy["destinations"]["maintained"]
    )


class PlacementPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = load_policy()

    def test_exact_policy_contract(self) -> None:
        self.assertEqual(
            self.policy,
            {
                "admission": {
                    "accepted": ["reusable_cross_repository_agent_skill"],
                    "rejected": ["repository_specific_agent_skill"],
                },
                "destinations": {
                    "generated_indexes": {
                        "command": "make index",
                        "direct_write": False,
                        "owner": "repository",
                        "paths": ["index/skills.json", "index/README.md"],
                    },
                    "maintained": [
                        {
                            "kind": "skill",
                            "owner": "repository",
                            "path": "skills/{skill_name}/",
                        },
                        {
                            "kind": "record",
                            "owner": "repository",
                            "path": "records/skills/{skill_name}.json",
                        },
                        {
                            "kind": "review",
                            "owner": "repository",
                            "path": "reviews/{skill_name}.json",
                        },
                    ],
                },
                "forbidden_roots": {
                    "generated": ["dist/", "index/"],
                    "runtime": ["runs/"],
                },
                "material_allowlist": ["public"],
                "material_dispositions": {
                    "private": {
                        "custody": "external_state",
                        "git": "never_git",
                    },
                    "sensitive": {
                        "custody": "external_state",
                        "git": "never_git",
                    },
                },
                "policy_id": "portable-agent-skill-placement",
                "schema_version": 1,
                "validation": {"command": "make check"},
            },
        )

    def assert_material_rejected(self, material: object) -> None:
        self.assertFalse(
            placement_allowed(
                self.policy,
                scope="reusable_cross_repository_agent_skill",
                destination="skills/repository-placement/",
                material=material,
            )
        )

    def test_public_material_allowlist_is_explicit(self) -> None:
        self.assertEqual(self.policy["material_allowlist"], ["public"])
        self.assertTrue(
            placement_allowed(
                self.policy,
                scope="reusable_cross_repository_agent_skill",
                destination="skills/repository-placement/",
                material="public",
            )
        )

    def test_unknown_material_labels_are_rejected(self) -> None:
        for material in ("confidential", "internal", "unknown"):
            with self.subTest(material=material):
                self.assert_material_rejected(material)

    def test_material_label_casing_drift_is_rejected(self) -> None:
        for material in ("Public", "PUBLIC", "pUbLiC"):
            with self.subTest(material=material):
                self.assert_material_rejected(material)

    def test_empty_material_labels_are_rejected(self) -> None:
        for material in ("", " ", "\t"):
            with self.subTest(material=material):
                self.assert_material_rejected(material)

    def test_non_string_material_labels_are_rejected(self) -> None:
        for material in ([], {}, ("public",)):
            with self.subTest(material=material):
                self.assert_material_rejected(material)

    def test_null_material_label_is_rejected(self) -> None:
        self.assert_material_rejected(None)

    def test_boolean_material_labels_are_rejected(self) -> None:
        for material in (False, True):
            with self.subTest(material=material):
                self.assert_material_rejected(material)

    def test_number_material_labels_are_rejected(self) -> None:
        for material in (-1, 0, 1, 1.5):
            with self.subTest(material=material):
                self.assert_material_rejected(material)

    def test_reusable_skill_destinations_are_accepted(self) -> None:
        scope = "reusable_cross_repository_agent_skill"
        for destination in (
            "skills/repository-placement/",
            "records/skills/repository-placement.json",
            "reviews/repository-placement.json",
        ):
            with self.subTest(destination=destination):
                self.assertTrue(
                    placement_allowed(
                        self.policy,
                        scope=scope,
                        destination=destination,
                    )
                )

        for destination in ("index/skills.json", "index/README.md"):
            with self.subTest(destination=destination):
                self.assertTrue(
                    placement_allowed(
                        self.policy,
                        scope=scope,
                        destination=destination,
                        producer="make index",
                    )
                )

    def test_repository_specific_skills_are_rejected(self) -> None:
        for destination in (
            "skills/repository-placement/",
            "records/skills/repository-placement.json",
            "reviews/repository-placement.json",
            "index/skills.json",
        ):
            with self.subTest(destination=destination):
                self.assertFalse(
                    placement_allowed(
                        self.policy,
                        scope="repository_specific_agent_skill",
                        destination=destination,
                        producer="make index",
                    )
                )

    def test_private_and_sensitive_material_stays_out_of_git(self) -> None:
        scope = "reusable_cross_repository_agent_skill"
        for material in ("private", "sensitive"):
            with self.subTest(material=material):
                disposition = self.policy["material_dispositions"][material]
                self.assertEqual(disposition["git"], "never_git")
                self.assertEqual(disposition["custody"], "external_state")
                self.assertFalse(
                    placement_allowed(
                        self.policy,
                        scope=scope,
                        destination="skills/repository-placement/",
                        material=material,
                    )
                )

    def test_generated_and_runtime_roots_reject_direct_placement(self) -> None:
        scope = "reusable_cross_repository_agent_skill"
        cases = (
            ("dist/skill-index.tar.gz", None),
            ("index/skills.json", None),
            ("index/unowned.json", "make index"),
            ("runs/session.json", None),
        )
        for destination, producer in cases:
            with self.subTest(destination=destination, producer=producer):
                self.assertFalse(
                    placement_allowed(
                        self.policy,
                        scope=scope,
                        destination=destination,
                        producer=producer,
                    )
                )

    def test_unowned_and_malformed_destinations_are_rejected(self) -> None:
        scope = "reusable_cross_repository_agent_skill"
        for destination in (
            "docs/repository-placement.md",
            "skills/Repository_Placement/",
            "skills/../private/",
            "records/domains/repository-placement.json",
        ):
            with self.subTest(destination=destination):
                self.assertFalse(
                    placement_allowed(
                        self.policy,
                        scope=scope,
                        destination=destination,
                    )
                )


if __name__ == "__main__":
    unittest.main()
