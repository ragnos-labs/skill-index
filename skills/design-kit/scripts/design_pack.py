#!/usr/bin/env python3
"""Check a Design Kit design pack and summarize what informed the design.

check PACK [--kit-digest DIGEST] [--brand-digest DIGEST] [--final]
    Validate PACK against references/design-pack.schema.json and the pack
    rules. A producer passes the digests its own skill index resolved; a
    differing kit or brand digest is a hold. Any failure goes back to the
    Director with the reasons printed. PACK may be - for standard input.
    A pack with an unverified claim or a missing release is draft only:
    it passes with a note, and fails with --final, which a producer passes
    before output leaves draft.
    Exit 0 when the pack is usable, 1 when it is not, 2 on a usage error.

summary PACK
    Print the kit, brand and resource sources a valid pack records.

Uses only the standard library. Reads one file; never fetches, writes or runs
anything named in a pack.
"""
import argparse
import json
import os
from pathlib import Path
import re
import stat
import sys
import unicodedata

MAX_BYTES = 1_000_000
MAX_ERRORS = 50
SCHEMA_PATH = Path(__file__).resolve().parent.parent / "references" / "design-pack.schema.json"
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}
BRAND_SOURCE_FIELDS = ("skill", "digest", "no_digest_reason", "repository", "revision")


def safe(text):
    """Escape control and format characters so untrusted text cannot drive the terminal."""
    return "".join(
        char.encode("unicode_escape").decode("ascii") if unicodedata.category(char) in ("Cc", "Cf") else char
        for char in str(text)
    )


def validate(value, schema, path="pack"):
    """Return schema errors for the subset of JSON Schema the pack schema uses."""
    if "const" in schema and (type(value) is not type(schema["const"]) or value != schema["const"]):
        return [f"{path}: must be {json.dumps(schema['const'])}"]
    if "enum" in schema and (type(value) is not str or value not in schema["enum"]):
        return [f"{path}: must be one of {', '.join(schema['enum'])}"]
    if "type" in schema:
        names = schema["type"] if isinstance(schema["type"], list) else [schema["type"]]
        if not any(type(value) is TYPES[name] for name in names):
            return [f"{path}: must be {' or '.join(names)}"]
    errors = []
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"{path}: must not be empty")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            errors.append(f"{path}: does not match {schema['pattern']}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"{path}: needs at least {schema['minItems']} item(s)")
        for index, item in enumerate(value):
            errors.extend(validate(item, schema.get("items", {}), f"{path}[{index}]"))
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in value:
                errors.append(f"{path}.{key}: required")
        for key, item in value.items():
            if key in properties:
                errors.extend(validate(item, properties[key], f"{path}.{key}"))
            elif schema.get("additionalProperties") is False:
                errors.append(f"{path}.{safe(key)}: unknown field")
    return errors


def brand_rules(brand):
    origin, present = brand["origin"], {key for key in BRAND_SOURCE_FIELDS if key in brand}
    allowed = {
        "skill": {"skill", "digest", "no_digest_reason"},
        "repository": {"repository", "revision"},
        "project": {"revision"},
        "cms": set(),
        "none": set(),
    }[origin]
    errors = [f"pack.brand.{key}: not used when origin is {origin}" for key in sorted(present - allowed)]
    if origin == "skill":
        if "skill" not in brand:
            errors.append("pack.brand.skill: required when origin is skill")
        if ("digest" in brand) == ("no_digest_reason" in brand):
            errors.append("pack.brand: give a digest or no_digest_reason, exactly one")
    if origin == "repository" and not {"repository", "revision"} <= present:
        errors.append("pack.brand: origin repository needs repository and revision")
    if origin == "none" and brand["files_read"]:
        errors.append("pack.brand.files_read: must be empty when origin is none")
    if origin != "none" and not brand["files_read"]:
        errors.append("pack.brand.files_read: list the brand files or records read")
    return errors


def rules(pack):
    """Rules a schema cannot express. Assumes the pack passed the schema."""
    errors = []
    kit = pack["kit"]
    if (kit["digest"] is None) == ("no_digest_reason" not in kit):
        errors.append("pack.kit: give a digest or no_digest_reason, exactly one")
    errors.extend(brand_rules(pack["brand"]))
    if pack["deliverable"]["kind"] == "cms_asset" and "cms" not in pack:
        errors.append("pack.cms: required for a cms_asset")
    if "cms" in pack and not pack["cms"]["learned"]["read"]:
        errors.append("pack.cms.learned.read: hold until the client's learned corrections are read")
    return errors


def draft_only(pack):
    """Claims that keep the pack draft only: unverified wording or a missing release."""
    reasons = []
    for index, claim in enumerate(pack["claims"]):
        if not claim["verified"]:
            reasons.append(f"pack.claims[{index}]: not verified against its source")
        if claim["release"] == "missing":
            reasons.append(f"pack.claims[{index}]: release missing")
    return reasons


def load(path):
    try:
        if path == "-":
            data = sys.stdin.buffer.read(MAX_BYTES + 1)
        else:
            if not stat.S_ISREG(os.stat(path).st_mode):
                raise ValueError(f"{safe(path)}: not a regular file")
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0))
            with os.fdopen(fd, "rb") as handle:
                if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                    raise ValueError(f"{safe(path)}: not a regular file")
                data = handle.read(MAX_BYTES + 1)
    except OSError as exc:
        raise ValueError(f"cannot read {safe(path)}: {exc.strerror}") from None
    if len(data) > MAX_BYTES:
        raise ValueError(f"{safe(path)}: larger than {MAX_BYTES} bytes")
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError(f"{safe(path)}: not valid UTF-8 JSON ({exc.__class__.__name__})") from None


def check(pack, schema, kit_digest=None, brand_digest=None, final=False):
    errors = validate(pack, schema) or rules(pack)
    if errors:
        return errors
    if final:
        errors.extend(reason + "; draft only" for reason in draft_only(pack))
    if kit_digest is not None and pack["kit"]["digest"] is not None and kit_digest != pack["kit"]["digest"]:
        errors.append("pack.kit.digest: differs from the producer's resolved kit; hold until the Director reconciles it")
    if brand_digest is not None and pack["brand"].get("digest") not in (None, brand_digest):
        errors.append("pack.brand.digest: differs from the producer's resolved brand skill; hold until the Director reconciles it")
    return errors


def summary(pack):
    kit, brand = pack["kit"], pack["brand"]
    lines = [f"Deliverable: {pack['deliverable']['kind']} ({pack['deliverable']['format']})"]
    lines.append(f"Kit: {kit['digest'] or 'no digest: ' + kit['no_digest_reason']}; read {', '.join(kit['files_read'])}")
    origin = brand["origin"]
    if origin == "none":
        lines.append(f"Brand: {brand['name']}, no brand sources found")
    else:
        detail = {
            "skill": f"skill {brand.get('skill')} {brand.get('digest') or 'no digest: ' + str(brand.get('no_digest_reason'))}",
            "repository": f"{brand.get('repository')} at {brand.get('revision')}",
            "project": "project files" + (f" at {brand['revision']}" if "revision" in brand else ""),
            "cms": "the CMS client record",
        }[origin]
        lines.append(f"Brand: {brand['name']} from {detail}; read {', '.join(brand['files_read'])}")
    if "cms" in pack:
        cms = pack["cms"]
        lines.append(f"CMS project: {cms['project']}" + (f", round {cms['output_round']}" if "output_round" in cms else ""))
        lines.append(f"CMS brand record (outranks the brand above): {cms['brand_record']}")
    held = draft_only(pack)
    lines.append(f"Claims: {len(pack['claims'])}" + (f"; draft only, {len(held)} open" if held else ""))
    if not pack["resources"]:
        lines.append("Resources: none")
    for item in pack["resources"]:
        mark = "" if item["inspected"] else " (not inspected)"
        revision = f"@{item['revision']}" if "revision" in item else ""
        lines.append(f"  {item['use']}: {item['source']} {item['id']}{revision}{mark}: {item['decision']}")
    return "\n".join(safe(line) for line in lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    check_parser = commands.add_parser("check")
    check_parser.add_argument("pack")
    check_parser.add_argument("--kit-digest")
    check_parser.add_argument("--brand-digest")
    check_parser.add_argument("--final", action="store_true")
    summary_parser = commands.add_parser("summary")
    summary_parser.add_argument("pack")
    args = parser.parse_args(argv)
    try:
        schema = load(SCHEMA_PATH)
        pack = load(args.pack)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    errors = check(pack, schema, getattr(args, "kit_digest", None), getattr(args, "brand_digest", None),
                   getattr(args, "final", False))
    if errors:
        for error in errors[:MAX_ERRORS]:
            print(error, file=sys.stderr)
        if len(errors) > MAX_ERRORS:
            print(f"... and {len(errors) - MAX_ERRORS} more", file=sys.stderr)
        return 1
    if args.command == "summary":
        print(summary(pack))
    else:
        notes = []
        if args.kit_digest is None and pack["kit"]["digest"] is not None:
            notes.append("kit digest not compared (pass --kit-digest as the producer)")
        if args.brand_digest is None and "digest" in pack["brand"]:
            notes.append("brand digest not compared (pass --brand-digest as the producer)")
        held = draft_only(pack)
        if held:
            notes.append(f"draft only: {len(held)} claim check(s) open")
        print("pack ok" + ("; " + "; ".join(notes) if notes else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
