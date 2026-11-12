#!/usr/bin/env python3
"""Store one secret in Infisical from hidden input, then verify it by comparison.

The value is read with a hidden prompt (or one line from a non-terminal
stdin), handed to the Infisical CLI through a mode-600 temporary file, and
never placed in argv, environment, logs, or output. Verification reads the
stored value back and compares it in memory; only "verified" or "mismatch" is
printed.
"""
import argparse
import getpass
import os
import re
import subprocess
import sys
import tempfile

NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")
PATH_RE = re.compile(r"^/[A-Za-z0-9_./-]*$")


def fail(message, code=1):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def parse(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--name", required=True, help="secret name, UPPER_SNAKE_CASE")
    p.add_argument("--project-id", required=True)
    p.add_argument("--env", required=True, help="environment slug, such as prod")
    p.add_argument("--path", default="/", help="folder path, such as /ai-llm")
    p.add_argument("--domain", required=True, help="Infisical API URL, ending in /api")
    p.add_argument("--cli", default="infisical", help="Infisical CLI executable")
    p.add_argument("--overwrite", action="store_true",
                   help="allow replacing an existing value")
    args = p.parse_args(argv)
    if not NAME_RE.match(args.name):
        fail("name must be UPPER_SNAKE_CASE", 2)
    if not PATH_RE.match(args.path) or ".." in args.path:
        fail("path must be an absolute folder path without '..'", 2)
    if not args.domain.startswith("https://") and not args.domain.startswith("http://localhost"):
        fail("domain must use https", 2)
    return args


def common(args):
    return ["--env", args.env, "--path", args.path,
            "--projectId", args.project_id, "--domain", args.domain]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def read_back(args):
    r = run([args.cli, "secrets", "get", args.name, "--plain", "--silent"] + common(args))
    if r.returncode != 0:
        return None, r.stderr
    return r.stdout.rstrip("\n"), ""


def read_value(name):
    if sys.stdin.isatty():
        value = getpass.getpass(f"Paste the value for {name}, then press Return: ")
    else:
        value = sys.stdin.readline().rstrip("\r\n")
    if not value:
        fail("no value entered; nothing stored")
    if "\n" in value or "\r" in value:
        fail("value must be a single line")
    return value


def main(argv=None):
    args = parse(sys.argv[1:] if argv is None else argv)

    if run([args.cli, "user", "get", "token", "--domain", args.domain]).returncode != 0:
        fail(f"not signed in; run: {args.cli} login --domain {args.domain}")

    existing, _ = read_back(args)
    if existing and not args.overwrite:
        fail(f"{args.name} already has a value at {args.env}:{args.path}; "
             "rerun with --overwrite to replace it")

    value = read_value(args.name)
    fd, tmp = tempfile.mkstemp(prefix="secret-intake-")
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(f"{args.name}={value}\n")
        r = run([args.cli, "secrets", "set", "--file", tmp, "--silent"] + common(args))
    finally:
        os.unlink(tmp)
    if r.returncode != 0:
        detail = r.stderr.replace(value, "<redacted>").strip().splitlines()
        hint = ""
        if "not found" in r.stderr.lower() and "project" in r.stderr.lower():
            hint = " (the project ID is wrong or stale; list projects you can see and retry)"
        fail(f"store failed{hint}: {detail[-1] if detail else 'no detail'}")

    stored, err = read_back(args)
    if stored != value:
        fail("read-back mismatch; the stored value differs or could not be read")
    print(f"verified: {args.name} stored at {args.env}:{args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
