"""Isolated tests with a fake Infisical CLI; no real accounts or secrets."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "skills/infisical-secret-intake/scripts/store_secret.py"

FAKE_CLI = r'''#!/usr/bin/env python3
import json, os, sys
state = os.environ["FAKE_STATE"]
data = json.load(open(state)) if os.path.exists(state) else {}
with open(os.environ["FAKE_ARGV_LOG"], "a") as log:
    log.write(" ".join(sys.argv[1:]) + "\n")
args = sys.argv[1:]
def opt(flag):
    return args[args.index(flag) + 1]
if args[:3] == ["user", "get", "token"]:
    sys.exit(0 if data.get("signed_in", True) else 1)
if os.environ.get("FAKE_BAD_PROJECT") and "--projectId" in args:
    print("Project with ID 'x' not found during bot lookup.", file=sys.stderr); sys.exit(1)
key = lambda name: opt("--env") + ":" + opt("--path") + ":" + name
if args[:2] == ["secrets", "get"]:
    k = key(args[2])
    if k not in data.get("secrets", {}):
        print("secret not found", file=sys.stderr); sys.exit(1)
    print(data["secrets"][k]); sys.exit(0)
if args[:2] == ["secrets", "set"]:
    path = opt("--file")
    if os.stat(path).st_mode & 0o077:
        print("temp file too open", file=sys.stderr); sys.exit(3)
    name, value = open(path).read().rstrip("\n").split("=", 1)
    if os.environ.get("FAKE_CORRUPT"):
        value = value + "x"
    data.setdefault("secrets", {})[key(name)] = value
    json.dump(data, open(state, "w")); sys.exit(0)
sys.exit(9)
'''

SECRET = "sk-test-0123456789abcdef"


class IntakeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.cli = root / "infisical"
        self.cli.write_text(FAKE_CLI)
        self.cli.chmod(0o700)
        self.state = root / "state.json"
        self.argv_log = root / "argv.log"
        self.argv_log.write_text("")
        self.env = dict(os.environ, FAKE_STATE=str(self.state), FAKE_ARGV_LOG=str(self.argv_log),
                        TMPDIR=str(root))

    def tearDown(self):
        self.tmp.cleanup()

    def run_intake(self, stdin=SECRET + "\n", extra=(), **env):
        cmd = [sys.executable, str(SCRIPT), "--name", "EXAMPLE_API_KEY", "--project-id", "p1",
               "--env", "prod", "--path", "/ai-llm", "--domain", "https://vault.example/api",
               "--cli", str(self.cli), *extra]
        return subprocess.run(cmd, input=stdin, capture_output=True, text=True,
                              env=dict(self.env, **env))

    def leftovers(self):
        return [p for p in Path(self.tmp.name).iterdir() if p.name.startswith("secret-intake-")]

    def test_stores_and_verifies_without_exposing_value(self):
        r = self.run_intake()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("verified: EXAMPLE_API_KEY stored at prod:/ai-llm", r.stdout)
        self.assertNotIn(SECRET, r.stdout + r.stderr)
        self.assertNotIn(SECRET, self.argv_log.read_text())
        self.assertEqual(self.leftovers(), [])

    def test_refuses_overwrite_unless_asked(self):
        self.assertEqual(self.run_intake().returncode, 0)
        r = self.run_intake(stdin="other-value\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--overwrite", r.stderr)
        r = self.run_intake(stdin="other-value\n", extra=["--overwrite"])
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_empty_value_stores_nothing(self):
        r = self.run_intake(stdin="\n")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(self.state.exists())

    def test_requires_sign_in(self):
        self.state.write_text('{"signed_in": false}')
        r = self.run_intake()
        self.assertIn("login --domain", r.stderr)

    def test_stale_project_hint_and_redaction(self):
        r = self.run_intake(FAKE_BAD_PROJECT="1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("stale", r.stderr)
        self.assertNotIn(SECRET, r.stdout + r.stderr)
        self.assertEqual(self.leftovers(), [])

    def test_read_back_mismatch_fails(self):
        r = self.run_intake(FAKE_CORRUPT="1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("mismatch", r.stderr)
        self.assertNotIn(SECRET, r.stdout + r.stderr)

    def test_rejects_hostile_arguments(self):
        for extra in (["--name", "bad name"], ["--path", "/../x"], ["--domain", "http://evil/api"]):
            cmd = [sys.executable, str(SCRIPT), "--name", "EXAMPLE_API_KEY", "--project-id", "p1",
                   "--env", "prod", "--path", "/ai-llm", "--domain", "https://vault.example/api",
                   "--cli", str(self.cli), *extra]
            r = subprocess.run(cmd, input=SECRET, capture_output=True, text=True, env=self.env)
            self.assertEqual(r.returncode, 2, extra)
        self.assertEqual(self.argv_log.read_text(), "")


if __name__ == "__main__":
    unittest.main()
