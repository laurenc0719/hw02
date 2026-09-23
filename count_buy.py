#!/usr/bin/env python3
# =============================================================================
# Script  : count_buy.py
# Purpose : Count rows in fact_transactions.csv where txn_type is EXACTLY 'Buy'.
#           "Exactly" = case-sensitive, no leading/trailing whitespace.
#           Cross-validates with a pandas-free stdlib count and reports any
#           near-miss values ('buy', 'BUY', ' Buy ') that a loose match would
#           have silently swept in.
# Course  : MIS3060 - Business Intelligence with AI | Lauren Curley
# Usage   : python count_buy.py
# =============================================================================

import csv
import sys
from collections import Counter
from pathlib import Path

TARGET = "Buy"
COLUMN = "txn_type"

CANDIDATE_PATHS = [
    "02_Data/Raw/fact_transactions.csv",
    "data/raw/fact_transactions.csv",
    "fact_transactions.csv",
]


def resolve_csv() -> Path:
    """Locate the dataset relative to cwd, this script, or its parent."""
    script_dir = Path(__file__).resolve().parent
    for root in (Path.cwd(), script_dir, script_dir.parent):
        for rel in CANDIDATE_PATHS:
            p = (root / rel).resolve()
            if p.is_file():
                return p
    sys.exit("ERROR: could not find fact_transactions.csv")


def count_with_stdlib(path: Path) -> tuple[int, Counter]:
    """Exact count using only the standard library. Returns (count, all values)."""
    seen = Counter()
    exact = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if COLUMN not in reader.fieldnames:
            sys.exit(f"ERROR: column '{COLUMN}' not found. Got: {reader.fieldnames}")
        for row in reader:
            value = row[COLUMN]
            seen[value] += 1
            if value == TARGET:          # exact: case-sensitive, whitespace-sensitive
                exact += 1
    return exact, seen


def count_with_pandas(path: Path) -> int | None:
    """Independent check. Returns None if pandas isn't installed."""
    try:
        import pandas as pd
    except ImportError:
        return None
    df = pd.read_csv(path, usecols=[COLUMN])
    return int((df[COLUMN] == TARGET).sum())


def main() -> None:
    path = resolve_csv()
    print(f"Source : {path}")

    exact, seen = count_with_stdlib(path)
    total = sum(seen.values())

    print(f"Total data rows                     : {total:,}")
    print(f"Rows where {COLUMN} == '{TARGET}' (exact) : {exact:,}")
    print(f"Share of all transactions           : {exact / total * 100:.2f}%")

    # Near-miss audit: values a case-insensitive or stripped match would capture.
    near = {v: n for v, n in seen.items()
            if v != TARGET and v.strip().casefold() == TARGET.casefold()}
    if near:
        print("\nWARNING - near-miss values found (NOT counted above):")
        for v, n in sorted(near.items()):
            print(f"  {v!r:>12} : {n:,}")
        print(f"  A loose match would have returned {exact + sum(near.values()):,} instead.")
    else:
        print(f"\nNo case or whitespace variants of '{TARGET}' exist. Exact == loose.")

    # Cross-validation against a second, independent implementation.
    pandas_count = count_with_pandas(path)
    if pandas_count is None:
        print("\npandas not installed - stdlib count only.")
    else:
        status = "MATCH" if pandas_count == exact else "MISMATCH"
        print(f"\nCross-validation")
        print(f"  stdlib csv  : {exact:,}")
        print(f"  pandas      : {pandas_count:,}")
        print(f"  Result      : {status}")
        if status == "MISMATCH":
            sys.exit(1)

    print(f"\nDistinct {COLUMN} values in file: {len(seen)}")
    for v, n in seen.most_common():
        print(f"  {v!r:>16} : {n:>7,}")


if __name__ == "__main__":
    main()
