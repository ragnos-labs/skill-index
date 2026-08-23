#!/usr/bin/env python3
"""Bind reviewed skill records to the exact current bundle digests."""

from __future__ import annotations

import sys

from repository_model import ROOT, bundle_digest, dump_json, load_json, load_records


def main() -> int:
    updated = 0
    for record in load_records("skills"):
        review_path = ROOT / record["review_path"]
        review = load_json(review_path)
        if review.get("status") != "reviewed":
            continue
        digest = bundle_digest(ROOT / record["path"])
        if review.get("bundle_digest") != digest:
            review["bundle_digest"] = digest
            review_path.write_text(dump_json(review), encoding="utf-8")
            updated += 1
    print(f"bound {updated} review digests")
    return 0


if __name__ == "__main__":
    sys.exit(main())
