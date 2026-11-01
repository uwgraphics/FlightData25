#!/usr/bin/env python3
"""Create reduced CSVs with only rows where DAY_OF_MONTH is even and <= 28
and both ORIGIN and DEST are among the top 105 airports.

The top airports are ranked by flights (departures + arrivals) over ALL the
input files together, and the same list is used for every output file.
105 was chosen so that MSN (Madison) is always included: it ranks 98th in the
2024 data.

Writes ReducedData/<original-stem>-reduced.csv for each input, plus
ReducedData/combined-reduced.csv (all inputs together).
Prints original and resulting row counts.

Usage:
  python3 scripts/reduce_to_reduced.py [path/to/input.csv or directory]

This script was written by GitHub Co-Pilot in "agent mode" as prompted
by Michael Gleicher in October 2025.

2026 fixes (by Claude Code, as prompted by Michael Gleicher, November 2026):
  - The 2025 version picked the top airports separately for each file, so the
    monthly files did not all use the same airports (14 airports were in some
    months but not others), and the monthly files did not add up to the
    combined file. Now one list, computed from all files together, is used
    everywhere. The combined file is unchanged; the monthly files change by a
    few hundred rows each.
  - The per-file and combined code paths (which were duplicates) were merged.
"""
import argparse
from pathlib import Path
import sys
import pandas as pd


def top_airports(dfs, top_k):
    """rank airports by departures + arrivals over all the data frames."""
    codes = pd.concat([s for df in dfs for s in (df["ORIGIN"], df["DEST"])], ignore_index=True)
    counts = codes.dropna().astype(str).value_counts()
    return counts, set(counts.head(top_k).index)


def reduce_df(df: pd.DataFrame, name: str, out_dir: Path, topk: set) -> None:
    """keep even days <= 28 and flights between airports in topk; write <name>-reduced.csv."""
    day = pd.to_numeric(df["DAY_OF_MONTH"], errors="coerce")
    day_mask = day.notna() & ((day % 2) == 0) & (day <= 28)
    both_mask = df["ORIGIN"].astype(str).isin(topk) & df["DEST"].astype(str).isin(topk)
    reduced = df.loc[day_mask & both_mask]

    out_path = out_dir / f"{name}-reduced.csv"
    reduced.to_csv(out_path, index=False)

    n_orig, n_reduced = len(df), len(reduced)
    print("------------------------------------------------------------")
    print(f"Input: {name}")
    print(f"Original rows: {n_orig}")
    print(f"Reduced rows: {n_reduced}")
    print(f"Percentage reduction: {(1 - n_reduced / n_orig) * 100:.2f}%")
    print(f"Wrote reduced file: {out_path}")


def main(argv):
    parser = argparse.ArgumentParser(description="Create reduced CSVs with specific filters")
    parser.add_argument("input", nargs="?", help="Input CSV or directory (defaults to OriginalData/)")
    parser.add_argument("--out-dir", default="ReducedData", help="Directory to write reduced CSVs")
    parser.add_argument("--top-k", type=int, default=105, help="Number of top airports to keep (default 105)")
    args = parser.parse_args(argv[1:])

    if args.input:
        input_path = Path(args.input)
        files = sorted(input_path.glob("*.csv")) if input_path.is_dir() else [input_path]
    else:
        files = sorted((Path(__file__).resolve().parents[1] / "OriginalData").glob("*.csv"))
    if not files:
        print("No CSV files found to process.")
        return 4

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dfs = {f.stem: pd.read_csv(f) for f in files}
    counts, topk = top_airports(dfs.values(), args.top_k)
    cutoff = counts.iloc[args.top_k - 1]
    print(f"Top {args.top_k} airports: at least {cutoff} departures + arrivals over {len(files)} file(s)")
    if "MSN" in counts.index:
        print(f"Rank of 'MSN': {counts.index.get_loc('MSN') + 1}")

    for name, df in dfs.items():
        reduce_df(df, name, out_dir, topk)
    if len(dfs) > 1:
        reduce_df(pd.concat(dfs.values(), ignore_index=True), "combined", out_dir, topk)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
