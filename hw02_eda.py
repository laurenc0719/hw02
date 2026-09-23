#!/usr/bin/env python3
# =============================================================================
# Script      : hw02_eda.py
# Purpose     : HW02 - Exploratory Data Analysis profile of the transactions
#               fact table. Performs all 17 required steps in a SINGLE run:
#               load, profile, aggregate, correlate, chart, and export.
# Course      : MIS3060 - Business Intelligence with AI
#               Villanova School of Business, Fall 2026
# Dataset     : fact_transactions.csv
#               (expected shape: 298,772 rows x 9 columns)
#               Columns: txn_id, client_id, advisor_id, security_id,
#                        txn_date, txn_type, shares, price, amount
# Author      : Lauren Curley (laurenc0719)
# Generated   : 2026-09-22
# Python      : 3.13 | pandas 3.x | numpy 2.x | matplotlib 3.x
#
# Usage       : python hw02_eda.py
#
# Outputs     : hw02/charts/hist_amount.png
#               hw02/charts/box_amount_by_type.png
#               hw02/charts/scatter_shares_amount.png
#               hw02/hw02_profile.txt
# =============================================================================

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless backend: never tries to open a GUI window

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# CONFIGURATION
# -----------------------------------------------------------------------------

EXPECTED_SHAPE = (298772, 9)

# The assignment names the dataset as data/raw/fact_transactions.csv, but the
# course folder template ships it under 02_Data/Raw/. Search both (and a few
# other sane spots) so the script runs from anywhere without editing paths.
CANDIDATE_DATA_PATHS = [
    "data/raw/fact_transactions.csv",
    "02_Data/Raw/fact_transactions.csv",
    "hw02/data/raw/fact_transactions.csv",
    "hw02/02_Data/Raw/fact_transactions.csv",
    "fact_transactions.csv",
]

SCRIPT_DIR = Path(__file__).resolve().parent

# Deliverables belong in hw02/. If the script already lives inside a folder
# named hw02, that folder IS the target -- otherwise create hw02/ beneath it.
OUT_BASE = SCRIPT_DIR if SCRIPT_DIR.name.lower() == "hw02" else SCRIPT_DIR / "hw02"
CHART_DIR = OUT_BASE / "charts"
PROFILE_TXT = OUT_BASE / "hw02_profile.txt"

NUMERIC_TRIO = ["shares", "price", "amount"]

# -----------------------------------------------------------------------------
# OUTPUT HELPERS
# -----------------------------------------------------------------------------

_buffer: list[str] = []
_capture = True  # items 2-13 are captured for the .txt export; 14+ are not


def out(text: str = "") -> None:
    """Print to console and (while capturing) record for the text export."""
    print(text)
    if _capture:
        _buffer.append(text)


def header(title: str) -> None:
    out("")
    out("=" * 78)
    out(title)
    out("=" * 78)


def resolve_data_path() -> Path:
    """Find the dataset by checking candidate paths relative to cwd and script."""
    roots = [Path.cwd(), SCRIPT_DIR, SCRIPT_DIR.parent]
    seen: set[Path] = set()
    for root in roots:
        for rel in CANDIDATE_DATA_PATHS:
            candidate = (root / rel).resolve()
            if candidate in seen:
                continue
            seen.add(candidate)
            if candidate.is_file():
                return candidate

    tried = "\n".join(f"  - {p}" for p in sorted(seen))
    sys.exit(
        "ERROR: could not locate fact_transactions.csv.\n"
        f"Looked in:\n{tried}\n"
        "Fix: place the CSV at data/raw/fact_transactions.csv (or "
        "02_Data/Raw/fact_transactions.csv) relative to this script."
    )


# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------


def main() -> None:
    global _capture

    pd.set_option("display.width", 160)
    pd.set_option("display.max_columns", 50)

    CHART_DIR.mkdir(parents=True, exist_ok=True)

    # ---- ITEM 1: load the dataset -------------------------------------------
    data_path = resolve_data_path()
    df = pd.read_csv(data_path, parse_dates=["txn_date"])

    out("=" * 78)
    out("HW02 - EXPLORATORY DATA ANALYSIS PROFILE")
    out("MIS3060 Business Intelligence with AI | Lauren Curley")
    out("=" * 78)
    out(f"Source file : {data_path}")
    out(f"Run at      : {datetime.now():%Y-%m-%d %H:%M:%S}")

    # ---- ITEM 2: shape ------------------------------------------------------
    header("[2] DATASET SHAPE")
    n_rows, n_cols = df.shape
    out(f"Rows    : {n_rows:,}")
    out(f"Columns : {n_cols:,}")
    out(f"Shape   : {df.shape}")

    # ---- ITEM 3: columns and dtypes -----------------------------------------
    header("[3] COLUMNS AND DATA TYPES")
    dtypes = pd.DataFrame(
        {"column": df.columns, "dtype": [str(t) for t in df.dtypes]}
    )
    out(dtypes.to_string(index=False))

    # ---- ITEM 4: missing values ---------------------------------------------
    header("[4] MISSING VALUES BY COLUMN")
    missing = df.isna().sum()
    miss_tbl = pd.DataFrame(
        {
            "column": missing.index,
            "missing": missing.to_numpy(),
            "pct_missing": (missing.to_numpy() / len(df) * 100).round(2),
        }
    )
    out(miss_tbl.to_string(index=False))
    out(f"\nTotal missing cells: {int(missing.sum()):,}")

    # ---- ITEM 5: descriptive statistics -------------------------------------
    header("[5] DESCRIPTIVE STATISTICS (NUMERIC COLUMNS)")
    desc = df.select_dtypes(include="number").describe()
    out(desc.round(4).to_string())

    # ---- ITEM 6: txn_type value counts and percentages ----------------------
    header("[6] TXN_TYPE VALUE COUNTS AND PERCENTAGES")
    counts = df["txn_type"].value_counts(dropna=False).sort_values(ascending=False)
    pct = (counts / len(df) * 100).round(2)
    vc_tbl = pd.DataFrame(
        {"txn_type": counts.index.astype(str), "count": counts.to_numpy(),
         "percent": pct.to_numpy()}
    )
    out(vc_tbl.to_string(index=False))
    out(f"\nDistinct txn_type values: {df['txn_type'].nunique(dropna=True):,}")

    # ---- ITEM 7: unique entity counts ---------------------------------------
    header("[7] UNIQUE ENTITY COUNTS")
    out(f"Unique clients    (client_id)   : {df['client_id'].nunique():,}")
    out(f"Unique advisors   (advisor_id)  : {df['advisor_id'].nunique():,}")
    out(f"Unique securities (security_id) : {df['security_id'].nunique():,}")
    out(
        "\nNote: nunique() excludes nulls. security_id is null for "
        f"{int(df['security_id'].isna().sum()):,} non-security transactions "
        "(e.g. Deposit / Withdrawal)."
    )

    # ---- ITEM 8: date range -------------------------------------------------
    header("[8] TXN_DATE RANGE")
    d_min, d_max = df["txn_date"].min(), df["txn_date"].max()
    out(f"Earliest txn_date : {d_min:%Y-%m-%d}")
    out(f"Latest   txn_date : {d_max:%Y-%m-%d}")
    out(f"Span              : {(d_max - d_min).days:,} days")
    out(f"Null dates        : {int(df['txn_date'].isna().sum()):,}")

    # ---- ITEM 9: duplicate txn_id -------------------------------------------
    header("[9] DUPLICATE CHECK ON txn_id")
    dup_mask = df["txn_id"].duplicated(keep="first")
    dup_count = int(dup_mask.sum())
    out(f"Duplicate txn_id rows (beyond first occurrence) : {dup_count:,}")
    out(f"Unique txn_id values                            : {df['txn_id'].nunique():,}")
    out(f"Fully duplicated rows (all 9 columns)           : {int(df.duplicated().sum()):,}")
    if dup_count == 0:
        out("\nResult: txn_id is a valid unique primary key.")
    else:
        out("\nWARNING: txn_id is NOT unique -- investigate before joining.")

    # ---- ITEM 10: amount mean / median / skewness ---------------------------
    header("[10] AMOUNT - CENTRAL TENDENCY AND SKEWNESS")
    amt = df["amount"]
    amt_mean, amt_median, amt_skew = amt.mean(), amt.median(), amt.skew()
    out(f"Mean     : {amt_mean:,.2f}")
    out(f"Median   : {amt_median:,.2f}")
    out(f"Skewness : {amt_skew:,.4f}")
    if amt_skew > 0.5:
        shape_note = "right-skewed (long tail of large transactions)"
    elif amt_skew < -0.5:
        shape_note = "left-skewed (long tail of small/negative transactions)"
    else:
        shape_note = "approximately symmetric"
    out(f"Interpretation: distribution is {shape_note}.")

    # ---- ITEM 11: group by txn_type -----------------------------------------
    header("[11] AMOUNT BY TXN_TYPE (SORTED BY MEAN AMOUNT DESC)")
    grp = (
        df.groupby("txn_type", dropna=False)["amount"]
        .agg(count="count", mean_amount="mean", median_amount="median")
        .round({"mean_amount": 2, "median_amount": 2})
        .sort_values("mean_amount", ascending=False)
    )
    out(grp.to_string())

    # ---- ITEM 12: correlation matrix ----------------------------------------
    header("[12] CORRELATION MATRIX: shares / price / amount")
    corr = df[NUMERIC_TRIO].corr().round(2)
    out(corr.to_string())

    pairs = []
    for i in range(len(NUMERIC_TRIO)):
        for j in range(i + 1, len(NUMERIC_TRIO)):
            a, b = NUMERIC_TRIO[i], NUMERIC_TRIO[j]
            r = corr.loc[a, b]
            if pd.notna(r):
                pairs.append((a, b, float(r)))
    pairs.sort(key=lambda t: abs(t[2]), reverse=True)

    out("\nThree strongest correlations (by absolute value, self-pairs excluded):")
    if not pairs:
        out("  (no valid pairs -- correlations could not be computed)")
    for rank, (a, b, r) in enumerate(pairs[:3], start=1):
        direction = "positive" if r >= 0 else "negative"
        if abs(r) >= 0.7:
            strength = "strong"
        elif abs(r) >= 0.3:
            strength = "moderate"
        else:
            strength = "weak"
        out(f"  {rank}. {a:<6} <-> {b:<6}  r = {r:>6.2f}  ({strength} {direction})")

    # ---- ITEM 13: shares min / max / negatives by txn_type ------------------
    header("[13] SHARES - MIN, MAX, AND NEGATIVE COUNT BY TXN_TYPE")
    shares_tbl = df.groupby("txn_type", dropna=False)["shares"].agg(
        non_null="count",
        min_shares="min",
        max_shares="max",
        negative_count=lambda s: int((s < 0).sum()),
    )
    shares_tbl = shares_tbl.round({"min_shares": 4, "max_shares": 4})
    out(shares_tbl.to_string())
    out(
        f"\nOverall -- min: {amt_fmt(df['shares'].min())} | "
        f"max: {amt_fmt(df['shares'].max())} | "
        f"negative values: {int((df['shares'] < 0).sum()):,} | "
        f"nulls: {int(df['shares'].isna().sum()):,}"
    )

    # ---- ITEM 16: write the text profile (items 2-13) ----------------------
    _capture = False  # everything after this point is console-only
    PROFILE_TXT.write_text("\n".join(_buffer) + "\n", encoding="utf-8")

    # ---- ITEM 14: shape validation warning ---------------------------------
    header("[14] SHAPE VALIDATION")
    if df.shape != EXPECTED_SHAPE:
        out(
            f"*** WARNING: unexpected shape {df.shape} -- "
            f"expected {EXPECTED_SHAPE}. ***\n"
            "    The dataset may be filtered, truncated, or a different version."
        )
    else:
        out(f"OK: shape matches expected {EXPECTED_SHAPE}.")

    # ---- ITEM 15: charts ----------------------------------------------------
    header("[15] BUILDING CHARTS")
    build_hist(df, amt_mean, amt_median)
    build_boxplot(df)
    build_scatter(df)

    # ---- wrap up ------------------------------------------------------------
    header("[16] TEXT PROFILE SAVED")
    out(f"Wrote profile of items 2-13 -> {PROFILE_TXT}")

    out("")
    out("=" * 78)
    out("ALL 17 STEPS COMPLETE")
    out("=" * 78)
    out(f"  Charts  : {CHART_DIR}")
    out(f"  Profile : {PROFILE_TXT}")
    out("=" * 78)


def amt_fmt(value) -> str:
    """Format a possibly-NaN number for console output."""
    return "n/a" if pd.isna(value) else f"{value:,.4f}"


# -----------------------------------------------------------------------------
# ITEM 15 - CHART BUILDERS
# -----------------------------------------------------------------------------


def build_hist(df: pd.DataFrame, mean_val: float, median_val: float) -> None:
    """Histogram of amount with labeled mean and median reference lines."""
    path = CHART_DIR / "hist_amount.png"
    data = df["amount"].dropna()

    fig, ax = plt.subplots(figsize=(11, 6.5))
    ax.hist(data, bins=80, color="#4C72B0", edgecolor="white", linewidth=0.4)

    ax.axvline(mean_val, color="#C44E52", linestyle="--", linewidth=2,
               label=f"Mean = {mean_val:,.2f}")
    ax.axvline(median_val, color="#55A868", linestyle="-.", linewidth=2,
               label=f"Median = {median_val:,.2f}")

    ax.set_title("Distribution of Transaction Amount", fontsize=14, fontweight="bold")
    ax.set_xlabel("Amount ($)")
    ax.set_ylabel("Number of Transactions")
    ax.legend(frameon=True)
    ax.grid(axis="y", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved -> {path}")


def build_boxplot(df: pd.DataFrame) -> None:
    """Horizontal box plot of amount, one box per txn_type."""
    path = CHART_DIR / "box_amount_by_type.png"

    # Order categories by median amount so the chart reads cleanly.
    order = (
        df.groupby("txn_type", dropna=True)["amount"]
        .median()
        .sort_values()
        .index.tolist()
    )
    series = [df.loc[df["txn_type"] == t, "amount"].dropna().to_numpy() for t in order]

    fig, ax = plt.subplots(figsize=(11, 6.5))

    # matplotlib renamed labels -> tick_labels (3.9+) and vert -> orientation
    # (3.10+); the old names are removed in 3.11. Try new API, fall back to old.
    try:
        bp = ax.boxplot(series, tick_labels=order, orientation="horizontal",
                        patch_artist=True, showfliers=False)
    except TypeError:
        bp = ax.boxplot(series, labels=order, vert=False,
                        patch_artist=True, showfliers=False)

    palette = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860"]
    for patch, color in zip(bp["boxes"], palette * 5):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)
    for median in bp["medians"]:
        median.set_color("black")
        median.set_linewidth(1.8)

    ax.set_title("Transaction Amount by Transaction Type",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Amount ($)")
    ax.set_ylabel("Transaction Type")
    ax.grid(axis="x", alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved -> {path}")


def build_scatter(df: pd.DataFrame) -> None:
    """Scatter of shares (x) vs amount (y), colored by txn_type."""
    path = CHART_DIR / "scatter_shares_amount.png"

    sub = df[["shares", "amount", "txn_type"]].dropna(subset=["shares", "amount"])
    palette = ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860"]

    fig, ax = plt.subplots(figsize=(11, 6.5))
    for i, t in enumerate(sorted(sub["txn_type"].dropna().unique().tolist())):
        chunk = sub[sub["txn_type"] == t]
        ax.scatter(
            chunk["shares"], chunk["amount"],
            s=6, alpha=0.35, linewidths=0,
            color=palette[i % len(palette)], label=str(t), rasterized=True,
        )

    ax.set_title("Shares vs. Amount by Transaction Type",
                 fontsize=14, fontweight="bold")
    ax.set_xlabel("Shares")
    ax.set_ylabel("Amount ($)")
    legend = ax.legend(title="Transaction Type", frameon=True, markerscale=3)
    legend.get_title().set_fontweight("bold")
    ax.grid(alpha=0.3)
    ax.spines[["top", "right"]].set_visible(False)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    print(f"  saved -> {path}")
    if sub.empty:
        print("  note: no rows had both shares and amount populated.")


if __name__ == "__main__":
    main()
