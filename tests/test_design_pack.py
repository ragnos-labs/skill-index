"""Behavioral tests for the Design Kit design pack checker."""
import contextlib
import copy
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

sys_path = Path(__file__).resolve().parents[1] / "skills/design-kit"
spec = importlib.util.spec_from_file_location("design_pack", sys_path / "scripts/design_pack.py")
dp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dp)
EXAMPLE = json.loads((sys_path / "assets/design-pack.example.json").read_text())
SCHEMA = dp.load(dp.SCHEMA_PATH)
DIGEST = EXAMPLE["kit"]["digest"]
BRAND = EXAMPLE["brand"]["digest"]


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = dp.main(list(argv))
    return code, out.getvalue(), err.getvalue()


class DesignPackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self, value, raw=None):
        path = self.dir / "pack.json"
        path.write_bytes(raw if raw is not None else json.dumps(value).encode())
        return str(path)

    def errors(self, pack, digest=None):
        return dp.check(pack, SCHEMA, digest)

    def test_example_is_valid_and_matches_its_digest(self):
        self.assertEqual(self.errors(EXAMPLE, DIGEST), [])
        code, out, _ = run("check", self.write(EXAMPLE), "--kit-digest", DIGEST, "--brand-digest", BRAND)
        self.assertEqual((code, out.strip()), (0, "pack ok"))
        code, out, _ = run("check", self.write(EXAMPLE), "--kit-digest", DIGEST)
        self.assertIn("brand digest not compared", out)

    def test_summary_lists_kit_brand_and_resources(self):
        code, out, _ = run("summary", self.write(EXAMPLE))
        self.assertEqual(code, 0)
        self.assertIn("Brand: Example Brand from skill example-brand-design", out)
        self.assertIn("brand_asset: brand-library Asset 101", out)
        self.assertIn("visual_reference: cms reference-12@3", out)
        self.assertIn("CMS project: example-project, round round-1", out)

    def test_differing_digest_holds(self):
        other = "sha256:" + "f" * 64
        code, _, err = run("check", self.write(EXAMPLE), "--kit-digest", other)
        self.assertEqual(code, 1)
        self.assertIn("hold until the Director reconciles it", err)

    def test_missing_digest_needs_reason(self):
        pack = copy.deepcopy(EXAMPLE)
        pack["kit"]["digest"] = None
        self.assertIn("pack.kit: give a digest or no_digest_reason, exactly one", self.errors(pack))
        pack["kit"]["no_digest_reason"] = "skill index returns no digest on this host"
        self.assertEqual(self.errors(pack, DIGEST), [])

    def test_digest_and_reason_together_rejected(self):
        pack = copy.deepcopy(EXAMPLE)
        pack["kit"]["no_digest_reason"] = "x"
        self.assertTrue(self.errors(pack))

    def test_skill_brand_without_digest_summarizes(self):
        pack = copy.deepcopy(EXAMPLE)
        del pack["brand"]["digest"]
        self.assertTrue(self.errors(pack))
        pack["brand"]["no_digest_reason"] = "index gave none"
        code, out, _ = run("summary", self.write(pack))
        self.assertEqual(code, 0)
        self.assertIn("no digest: index gave none", out)

    def test_brand_origins(self):
        good = [
            {"name": "B", "origin": "skill", "skill": "b-design", "no_digest_reason": "index gave none", "files_read": ["SKILL.md"]},
            {"name": "B", "origin": "repository", "repository": "owner/design", "revision": "abc1234", "files_read": ["BRAND-SPEC.md"]},
            {"name": "B", "origin": "project", "files_read": ["DESIGN.md", "tokens.css"]},
            {"name": "B", "origin": "cms", "files_read": ["brand starter"]},
            {"name": "B", "origin": "none", "files_read": []},
        ]
        bad = [
            {"name": "B", "origin": "skill", "skill": "b-design", "files_read": ["SKILL.md"]},
            {"name": "B", "origin": "skill", "digest": DIGEST, "files_read": ["SKILL.md"]},
            {"name": "B", "origin": "skill", "skill": "b", "digest": DIGEST, "no_digest_reason": "x", "files_read": ["SKILL.md"]},
            {"name": "B", "origin": "repository", "repository": "owner/design", "files_read": ["x"]},
            {"name": "B", "origin": "project", "files_read": []},
            {"name": "B", "origin": "none", "skill": "b-design", "files_read": []},
            {"name": "B", "origin": "none", "files_read": ["x"]},
            {"name": "B", "origin": "cms", "repository": "r", "files_read": ["x"]},
        ]
        for brand in good:
            pack = copy.deepcopy(EXAMPLE); pack["brand"] = brand
            self.assertEqual(self.errors(pack), [], brand)
            code, out, err = run("summary", self.write(pack))
            self.assertEqual((code, err), (0, ""), brand)
        for brand in bad:
            pack = copy.deepcopy(EXAMPLE); pack["brand"] = brand
            self.assertTrue(self.errors(pack), brand)

    def test_differing_brand_digest_holds(self):
        other = "sha256:" + "e" * 64
        code, _, err = run("check", self.write(EXAMPLE), "--kit-digest", DIGEST, "--brand-digest", other)
        self.assertEqual(code, 1)
        self.assertIn("pack.brand.digest", err)
        code, _, _ = run("check", self.write(EXAMPLE), "--kit-digest", DIGEST,
                         "--brand-digest", EXAMPLE["brand"]["digest"])
        self.assertEqual(code, 0)

    def test_check_without_digest_says_not_compared(self):
        code, out, _ = run("check", self.write(EXAMPLE))
        self.assertEqual(code, 0)
        self.assertIn("kit digest not compared", out)

    def test_stdin_input(self):
        import sys
        from unittest.mock import patch
        fake = io.TextIOWrapper(io.BytesIO(json.dumps(EXAMPLE).encode()))
        with patch.object(sys, "stdin", fake):
            code, out, _ = run("check", "-", "--kit-digest", DIGEST, "--brand-digest", BRAND)
        self.assertEqual((code, out.strip()), (0, "pack ok"))

    def test_untrusted_text_is_escaped(self):
        pack = copy.deepcopy(EXAMPLE)
        pack["resources"][0]["decision"] = "kept \x1b[31mred"
        code, out, _ = run("summary", self.write(pack))
        self.assertEqual(code, 0)
        self.assertNotIn("\x1b[31m", out)
        pack["\x1b]0;title\x07"] = 1
        code, _, err = run("check", self.write(pack))
        self.assertEqual(code, 1)
        self.assertNotIn("\x1b", err)

    def test_special_files_rejected_without_blocking(self):
        code, _, err = run("check", str(self.dir))
        self.assertEqual(code, 1)
        self.assertTrue(err)
        fifo = self.dir / "pipe"
        os.mkfifo(fifo)
        code, _, err = run("check", str(fifo))
        self.assertEqual(code, 1)
        self.assertIn("not a regular file", err)

    def test_ordinary_unicode_is_kept(self):
        pack = copy.deepcopy(EXAMPLE)
        pack["brand"]["name"] = "Caf\u00e9 Co"
        code, out, _ = run("summary", self.write(pack))
        self.assertEqual(code, 0)
        self.assertIn("Caf\u00e9 Co", out)

    def test_cms_pack_names_its_brand_record(self):
        pack = copy.deepcopy(EXAMPLE)
        del pack["cms"]["brand_record"]
        self.assertIn("pack.cms.brand_record: required", self.errors(pack))
        code, out, _ = run("summary", self.write(EXAMPLE))
        self.assertIn("CMS brand record (outranks the brand above)", out)

    def test_schema_rejects_unknown_fields_bad_enums_and_types(self):
        pack = copy.deepcopy(EXAMPLE)
        pack["extra"] = 1
        pack["resources"][0]["use"] = "inspiration"
        pack["resources"][1]["inspected"] = "yes"
        pack["kit"]["digest"] = "sha256:short"
        pack["review_criteria"] = []
        errors = self.errors(pack)
        for fragment in ("pack.extra: unknown field", "resources[0].use", "resources[1].inspected",
                         "pack.kit.digest", "review_criteria: needs at least 1"):
            self.assertTrue(any(fragment in e for e in errors), fragment)

    def test_hostile_inputs_fail_cleanly(self):
        cases = [b"", b"\xff\xfe", b"[]", b"null", b"{" * 5000 + b"}" * 5000,
                 b'"' + b"a" * (dp.MAX_BYTES + 1) + b'"']
        for raw in cases:
            code, out, err = run("check", self.write(None, raw))
            self.assertEqual(code, 1, raw[:20])
            self.assertEqual(out, "")
            self.assertTrue(err)
        too_many = {f"field{i}": 1 for i in range(200)}
        code, _, err = run("check", self.write(too_many))
        self.assertEqual(code, 1)
        self.assertIn("more", err.splitlines()[-1])
        code, _, err = run("check", str(self.dir / "missing.json"))
        self.assertEqual(code, 1)
        self.assertIn("cannot read", err)

    def test_boolean_is_not_accepted_as_string_or_integer(self):
        pack = copy.deepcopy(EXAMPLE)
        pack["schema_version"] = True
        self.assertTrue(self.errors(pack))


if __name__ == "__main__":
    unittest.main()
