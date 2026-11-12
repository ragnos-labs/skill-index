"""Isolated tests with a fake Infisical CLI and a pseudo-terminal; no real accounts or secrets."""
import os
from pathlib import Path
import pty
import select
import signal
import sys
import tempfile
import time
import unittest

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().parents[1] / "skills/infisical-secret-add/scripts/store_secret.py"

FAKE_CLI = r'''#!/usr/bin/env python3
import json, os, stat, sys, time
state = os.environ["FAKE_STATE"]
data = json.load(open(state)) if os.path.exists(state) else {}
with open(os.environ["FAKE_ARGV_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\n")
args = sys.argv[1:]
def opt(flag):
    return args[args.index(flag) + 1]
if args[:3] == ["user", "get", "token"]:
    sys.exit(0 if data.get("signed_in", True) else 1)
if os.environ.get("FAKE_BAD_PROJECT") and "--projectId" in args:
    print("Project with ID 'x' not found during bot lookup.", file=sys.stderr); sys.exit(1)
key = lambda name: opt("--env") + ":" + opt("--path") + ":" + name
if args[:2] == ["secrets", "get"]:
    if os.environ.get("FAKE_READ_FAIL"):
        print("403 forbidden", file=sys.stderr); sys.exit(1)
    assert "--output" in args and opt("--output") == "json"
    value = data.get("secrets", {}).get(key(args[2]), "*not found*")
    print(json.dumps([{"secretKey": args[2], "secretValue": value}])); sys.exit(0)
if args[:2] == ["secrets", "set"]:
    name, ref = args[2].split("=", 1)
    path = ref[1:]
    if os.stat(path).st_mode & 0o077 or os.stat(os.path.dirname(path)).st_mode & 0o077:
        print("temp file too open", file=sys.stderr); sys.exit(3)
    value = open(path).read()
    if os.environ.get("FAKE_HANG"):
        open(os.environ["FAKE_HANG"], "w").write(path); time.sleep(30)
    if os.environ.get("FAKE_ECHO_FAIL"):
        print("parse error near '" + value[3:12] + "'", file=sys.stderr); sys.exit(1)
    if os.environ.get("FAKE_CORRUPT"):
        value = value + "x"
    data.setdefault("secrets", {})[key(name)] = value
    json.dump(data, open(state, "w")); sys.exit(0)
sys.exit(9)
'''

VALUE = "test-value-not-a-key"
TRICKY = 'https://u:p@db.example//x?a=1 # note ${HOME} "quoted" =eq '


class AddTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.cli = self.root / "infisical"
        self.cli.write_text(FAKE_CLI)
        self.cli.chmod(0o700)
        self.state = self.root / "state.json"
        self.argv_log = self.root / "argv.log"
        self.argv_log.write_text("")
        self.env = dict(os.environ, FAKE_STATE=str(self.state), FAKE_ARGV_LOG=str(self.argv_log),
                        TMPDIR=str(self.root))

    def tearDown(self):
        self.tmp.cleanup()

    def cmd(self, extra=()):
        return [sys.executable, str(SCRIPT), "--name", "EXAMPLE_API_KEY", "--project-id", "p1",
                "--env", "prod", "--path", "/ai-llm", "--domain", "https://vault.example/api",
                "--cli", str(self.cli), *extra]

    def run_add(self, value=VALUE, extra=(), signal_after=None, **env):
        """Run the script on a pseudo-terminal, answer the hidden prompt, return (code, output)."""
        pid, fd = pty.fork()
        if pid == 0:
            os.execve(sys.executable, self.cmd(extra), dict(self.env, **env))
        out, sent, deadline = b"", False, time.time() + 20
        while time.time() < deadline:
            if signal_after and sent and os.path.exists(signal_after):
                os.kill(pid, signal.SIGHUP); signal_after = None
            r, _, _ = select.select([fd], [], [], 0.1)
            if not r:
                if os.waitpid(pid, os.WNOHANG)[0]:
                    break
                continue
            try:
                chunk = os.read(fd, 4096)
            except OSError:
                break
            if not chunk:
                break
            out += chunk
            if not sent and b"Paste the value" in out:
                os.write(fd, value.encode() + b"\r"); sent = True
        _, status = os.waitpid(pid, 0)
        os.close(fd)
        code = os.waitstatus_to_exitcode(status)
        return code, out.decode(errors="replace")

    def stored(self):
        import json
        return json.loads(self.state.read_text())["secrets"]["prod:/ai-llm:EXAMPLE_API_KEY"]

    def leftovers(self):
        return [p for p in self.root.iterdir() if p.name.startswith("secret-add-")]

    def assert_not_exposed(self, value, out):
        self.assertNotIn(value, out)
        self.assertNotIn(value, self.argv_log.read_text())
        self.assertEqual(self.leftovers(), [])

    def test_stores_and_verifies_without_exposing_value(self):
        code, out = self.run_add()
        self.assertEqual(code, 0, out)
        self.assertIn("verified: EXAMPLE_API_KEY stored at prod:/ai-llm", out)
        self.assert_not_exposed(VALUE, out)
        self.assertEqual(self.stored(), VALUE)

    def test_tricky_value_is_stored_byte_for_byte(self):
        code, out = self.run_add(TRICKY)
        self.assertEqual(code, 0, out)
        self.assertEqual(self.stored(), TRICKY)
        self.assert_not_exposed(TRICKY, out)

    def test_reads_are_raw(self):
        self.run_add()
        gets = [l for l in self.argv_log.read_text().splitlines() if '"get", "EXAMPLE' in l]
        self.assertTrue(gets)
        for flag in ("--expand=false", "--include-imports=false", "--secret-overriding=false"):
            self.assertTrue(all(flag in l for l in gets), flag)

    def test_refuses_overwrite_unless_asked(self):
        self.assertEqual(self.run_add()[0], 0)
        code, out = self.run_add("other-value")
        self.assertNotEqual(code, 0)
        self.assertIn("--overwrite", out)
        self.assertEqual(self.stored(), VALUE)
        code, out = self.run_add("other-value", extra=["--overwrite"])
        self.assertEqual(code, 0, out)
        self.assertEqual(self.stored(), "other-value")

    def test_empty_value_stores_nothing(self):
        code, _ = self.run_add("")
        self.assertNotEqual(code, 0)
        self.assertFalse(self.state.exists())

    def test_requires_sign_in(self):
        self.state.write_text('{"signed_in": false}')
        code, out = self.run_add()
        self.assertNotEqual(code, 0)
        self.assertIn("login --domain", out)

    def test_stale_project_is_classified(self):
        code, out = self.run_add(FAKE_BAD_PROJECT="1")
        self.assertNotEqual(code, 0)
        self.assertIn("project not found", out)

    def test_cli_error_text_is_withheld(self):
        code, out = self.run_add(FAKE_ECHO_FAIL="1")
        self.assertNotEqual(code, 0)
        self.assertNotIn(VALUE[3:12], out)
        self.assert_not_exposed(VALUE, out)

    def test_read_error_never_overwrites(self):
        self.assertEqual(self.run_add()[0], 0)
        code, out = self.run_add("replacement", FAKE_READ_FAIL="1")
        self.assertNotEqual(code, 0)
        self.assertIn("nothing was stored", out)
        self.assertNotIn("Paste the value", out)
        self.assertEqual(self.stored(), VALUE)

    def test_read_back_mismatch_fails(self):
        code, out = self.run_add(FAKE_CORRUPT="1")
        self.assertNotEqual(code, 0)
        self.assertIn("mismatch", out)
        self.assert_not_exposed(VALUE, out)

    def test_hangup_during_store_removes_temp_value(self):
        marker = self.root / "hang-marker"
        code, _ = self.run_add(signal_after=str(marker), FAKE_HANG=str(marker))
        self.assertNotEqual(code, 0)
        self.assertEqual(self.leftovers(), [])

    def test_non_terminal_stdin_is_refused(self):
        import subprocess
        r = subprocess.run(self.cmd(), input=VALUE + "\n", capture_output=True, text=True, env=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("interactive terminal", r.stderr)
        self.assertFalse(self.state.exists())

    def test_rejects_hostile_arguments(self):
        import subprocess
        bad = (["--name", "bad name"], ["--path", "/../x"], ["--path", "/a//b"],
               ["--domain", "http://evil.example/api"], ["--domain", "http://localhost.evil.example/api"],
               ["--domain", "https://vault.example/"], ["--env", "Prod;rm"], ["--project-id", "p 1"])
        for extra in bad:
            r = subprocess.run(self.cmd(extra), capture_output=True, text=True, env=self.env)
            self.assertEqual(r.returncode, 2, extra)
        self.assertEqual(self.argv_log.read_text(), "")


if __name__ == "__main__":
    unittest.main()
