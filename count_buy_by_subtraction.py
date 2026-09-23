#!/usr/bin/env python3
# =============================================================================
# Script  : count_buy_by_subtraction.py
# Purpose : Derive the Buy count by COMPLEMENT: count all rows, then subtract
#           every non-Buy txn_type. This is the second, independent approach
#           for the HW02 cross-validation of the 83,556 figure.
#
#           NOTE: this method assumes the five subtracted types are EXHAUSTIVE.
#           The script proves that assumption instead of trusting it -- if any
#           unexpected value or null exists, the residual is NOT the Buy count.
# Course  : MIS3060 - Business Intelligence with AI | Lauren Curley
# Usage   : python count_buy_by_subtraction.py
# =============================================================================

import csv
import sys
from collections import Counter
from pathlib import Path

COLUMN = "txn_type"
SUBTRACT = ["Sell", "Deposit", "Withdrawal", "Dividend", "Advisory Fee"]

CANDIDATE_PATHS = [
    "02_Data/Raw/fact_transactions.csv",
    "data/raw/fact_transactions.csv",
    "fact_transactions.csv",
]


def resolve_csv() -> Path:
    script_dir = Path(__file__).resolve().parent
    for root in (Path.cwd(), script_dir, script_dir.parent):
        for rel in CANDIDATE_PATHS:
            p = (root / rel).resolve()
            if p.is_file():
                return p
    sys.exit("ERROR: could not find fact_transactions.csv")


def main() -> None:
    path = resolve_csv()
    print(f"Source : {path}\n")

    counts = Counter()
    total_rows = 0
    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if COLUMN not in reader.fieldnames:
            sys.exit(f"ERROR: column '{COLUMN}' not found. Got: {reader.fieldnames}")
        for row in reader:
            total_rows += 1
            counts[row[COLUMN]] += 1

    # ---- the subtraction -----------------------------------------------------
    print("STEP 1 - total data rows (header excluded)")
    print(f"  {total_rows:>10,}\n")

    print("STEP 2 - subtract each non-Buy type")
    running = total_rows
    subtracted = 0
    for t in SUBTRACT:
        n = counts.get(t, 0)
        subtracted += n
        running -= n
        flag = "" if n else "   <-- NOT FOUND IN FILE"
        print(f"  - {t:<14} {n:>8,}   running total: {running:>8,}{flag}")

    print(f"\nSTEP 3 - residual (implied Buy count)")
    print(f"  {total_rows:,} - {subtracted:,} = {running:,}\n")

    # ---- validate the exhaustiveness assumption ------------------------------
    expected = set(SUBTRACT) | {"Buy"}
    unexpected = {v: n for v, n in counts.items() if v not in expected}
    blanks = {v: n for v, n in counts.items() if v is None or str(v).strip() == ""}

    print("ASSUMPTION CHECK - are the five subtracted types exhaustive?")
    print(f"  Distinct {COLUMN} values in file : {len(counts)}")
    if unexpected:
        print("  *** FAILED: unexpected values present. The residual is NOT the Buy count. ***")
        for v, n in sorted(unexpected.items()):
            print(f"      {v!r:>16} : {n:,}")
    elif blanks:
        print("  *** FAILED: blank/null txn_type rows present. ***")
    else:
        print("  PASSED: the six known types account for every row. Residual is valid.")

    # ---- cross-validate against a direct count -------------------------------
    direct = counts.get("Buy", 0)
    status = "MATCH" if direct == running else "MISMATCH"
    print(f"\nCROSS-VALIDATION")
    print(f"  Method A - direct count  (txn_type == 'Buy') : {direct:>8,}")
    print(f"  Method B - by subtraction (total - others)   : {running:>8,}")
    print(f"  Result : {status}")

    print(f"\nFull value counts:")
    for v, n in counts.most_common():
        print(f"  {v!r:>16} : {n:>7,}  ({n / total_rows * 100:5.2f}%)")

    sys.exit(0 if status == "MATCH" else 1)


if __name__ == "__main__":
    main()
