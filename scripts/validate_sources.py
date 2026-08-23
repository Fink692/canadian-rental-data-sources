#!/usr/bin/env python3
"""Validate the structure of the public rental-source directory."""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
from urllib.parse import urlparse


EXPECTED_COLUMNS = [
    "city",
    "province",
    "question",
    "source_name",
    "authority",
    "source_url",
    "coverage",
    "checked_on",
    "limitations",
]


def validate(csv_path: Path) -> list[str]:
    errors: list[str] = []
    seen: set[tuple[str, str, str]] = set()

    with csv_path.open(encoding="utf-8-sig", newline="") as source_file:
        reader = csv.DictReader(source_file)
        if reader.fieldnames != EXPECTED_COLUMNS:
            return [
                "unexpected CSV columns: "
                f"expected {EXPECTED_COLUMNS}, found {reader.fieldnames or []}"
            ]

        row_count = 0
        for line_number, row in enumerate(reader, start=2):
            row_count += 1

            for column in EXPECTED_COLUMNS:
                if not (row.get(column) or "").strip():
                    errors.append(f"line {line_number}: {column} is empty")

            parsed_url = urlparse(row["source_url"])
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                errors.append(f"line {line_number}: source_url is not an HTTP(S) URL")

            try:
                date.fromisoformat(row["checked_on"])
            except ValueError:
                errors.append(f"line {line_number}: checked_on must use YYYY-MM-DD")

            identity = (row["city"], row["question"], row["source_url"])
            if identity in seen:
                errors.append(f"line {line_number}: duplicate city/question/source URL")
            seen.add(identity)

        if row_count == 0:
            errors.append("the directory has no source rows")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "csv_path",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "data" / "sources.csv",
        help="path to sources.csv (defaults to data/sources.csv)",
    )
    args = parser.parse_args()

    errors = validate(args.csv_path)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    with args.csv_path.open(encoding="utf-8-sig", newline="") as source_file:
        row_count = sum(1 for _ in csv.DictReader(source_file))
    print(f"Validated {row_count} source rows in {args.csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
