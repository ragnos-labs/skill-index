#!/usr/bin/env python3
"""Store one secret in Infisical from a hidden prompt, then verify it by comparison.

The value is read from a hidden terminal prompt and handed to the Infisical CLI
as raw file contents (NAME=@file) from a private temporary directory that is
removed on exit, Ctrl-C, hangup, or termination. It never reaches argv,
environment, logs, or output. Verification reads the stored value back without
expansion, imports, or personal overrides and compares it in memory; only
"verified" or a classified error is printed, never CLI error text.
"""
import argparse
import getpass
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
from urllib.parse import urlparse

NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,127}$")
PATH_RE = re.compile(r"^/[A-Za-z0-9_/-]*$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
PROJECT_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")
LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
NOT_FOUND = "*not found*"
RAW_READ = ["--expand=false", "--include-imports=false", "--secret-overriding=false"]


def fail(message, code=1):
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def valid_domain(domain):
    u = urlparse(domain)
    if u.scheme == "https":
        ok_scheme = True
    else:
        ok_scheme = u.scheme == "http" and u.hostname in LOCAL_HOSTS
    return ok_scheme and bool(u.hostname) and u.path.rstrip("/").endswith("/api") \
        and not u.query and not u.fragment and not u.username


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
    if not PATH_RE.match(args.path) or "//" in args.path:
        fail("path must be an absolute folder path of letters, digits, '_', '-' and '/'", 2)
    if not SLUG_RE.match(args.env):
        fail("env must be a lowercase environment slug", 2)
    if not PROJECT_RE.match(args.project_id):
        fail("project ID has unexpected characters", 2)
    if not valid_domain(args.domain):
        fail("domain must be an https URL ending in /api (http only for localhost)", 2)
    return args


def common(args):
    return ["--env", args.env, "--path", args.path,
            "--projectId", args.project_id, "--domain", args.domain]


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True, stdin=subprocess.DEVNULL)


class ReadError(Exception):
    """The stored value could not be read; its existence is unknown."""


def read_back(args):
    """Return the stored value, or None only when the CLI reports the name absent.

    The CLI exits 0 for a missing name and reports the value as NOT_FOUND, so
    JSON output is parsed. Any other failure raises ReadError: absence is never
    inferred from an error, so an unreadable secret is never overwritten.
    """
    r = run([args.cli, "secrets", "get", args.name, "--output", "json", "--silent"]
            + RAW_READ + common(args))
    if r.returncode != 0:
        raise ReadError(classify(r.stderr))
    try:
        rows = json.loads(r.stdout)
    except ValueError:
        raise ReadError("unreadable CLI output")
    if not isinstance(rows, list):
        raise ReadError("unexpected CLI output")
    for row in rows:
        if isinstance(row, dict) and row.get("secretKey") == args.name:
            value = row.get("secretValue")
            if value == NOT_FOUND:
                return None
            if not isinstance(value, str):
                raise ReadError("unexpected CLI output")
            return value
    return None


def classify(stderr):
    s = stderr.lower()
    if "project" in s and "not found" in s:
        return "project not found (the project ID is wrong or stale; list projects you can see)"
    if "401" in s or "unauthorized" in s or "invalid credentials" in s:
        return "not authorized (sign in again or check access to this project)"
    if "403" in s or "permission" in s or "forbidden" in s:
        return "permission denied for this environment or folder"
    if "folder" in s and "not found" in s:
        return "folder not found (create it or choose an existing folder)"
    return "the Infisical CLI reported an error (details withheld because they may echo the value)"


def read_value(name):
    if not sys.stdin.isatty():
        fail("run this in an interactive terminal; the value is read only from a hidden prompt")
    value = getpass.getpass(f"Paste the value for {name}, then press Return: ")
    if not value:
        fail("no value entered; nothing stored")
    return value


def main(argv=None):
    args = parse(sys.argv[1:] if argv is None else argv)

    if run([args.cli, "user", "get", "token", "--domain", args.domain]).returncode != 0:
        fail(f"not signed in; run: {args.cli} login --domain {args.domain}")

    try:
        existing = read_back(args)
    except ReadError as e:
        fail(f"could not check whether {args.name} exists, so nothing was stored: {e}")
    if existing is not None and not args.overwrite:
        fail(f"{args.name} already has a value at {args.env}:{args.path}; "
             "rerun with --overwrite to replace it")

    value = read_value(args.name)
    workdir = tempfile.mkdtemp(prefix="secret-add-")
    cleanup = lambda *_: (shutil.rmtree(workdir, ignore_errors=True), sys.exit(130))
    for sig in (signal.SIGHUP, signal.SIGTERM):
        signal.signal(sig, cleanup)
    try:
        path = os.path.join(workdir, "value")
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "w") as f:
            f.write(value)
        r = run([args.cli, "secrets", "set", f"{args.name}=@{path}", "--silent"] + common(args))
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    if r.returncode != 0:
        fail(f"store failed: {classify(r.stderr)}")

    try:
        stored = read_back(args)
    except ReadError:
        stored = None
    if stored != value:
        fail("read-back mismatch; the stored value differs or could not be read")
    print(f"verified: {args.name} stored at {args.env}:{args.path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
