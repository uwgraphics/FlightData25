#!/usr/bin/env python3
"""Create a reduced CSV with only rows where DAY_OF_MONTH is even and <= 28
and both ORIGIN and DEST are among the top 100(105) most common combined codes.

The top-k airports are computed separately for each input (each month, and
again for the combined data), so the airport set can differ between files.

Writes output to ReducedData/<original-stem>-reduced.csv (creates the directory if needed).
Prints original and resulting row counts.

Usage:
  python3 scripts/reduce_to_reduced.py [path/to/input.csv]

This script was written by GitHub Co-Pilot in "agent mode" as prompted
by Michael Gleicher in October 2025.
"""
import argparse
from pathlib import Path
import sys
import pandas as pd


def find_column_case_insensitive(df, target):
    target_up = target.upper()
    for c in df.columns:
        if c.upper() == target_up:
            return c
    return None


def reduce_csv(input_path: Path, out_dir: Path, top_k: int = 105) -> int:
    if not input_path.exists():
        print(f"Input file not found: {input_path}")
        return 2

    df = pd.read_csv(input_path)
    n_orig = df.shape[0]

    # Find relevant columns
    origin_col = find_column_case_insensitive(df, "ORIGIN")
    dest_col = find_column_case_insensitive(df, "DEST")
    day_col = find_column_case_insensitive(df, "DAY_OF_MONTH")

    if origin_col is None or dest_col is None or day_col is None:
        print("Required columns not found. Need ORIGIN, DEST, and DAY_OF_MONTH (case-insensitive).")
        return 3

    # Compute top-k combined codes from full dataset
    origin_series = df[origin_col].dropna().astype(str)
    dest_series = df[dest_col].dropna().astype(str)
    combined = pd.concat([origin_series, dest_series], ignore_index=True)
    combined_counts = combined.value_counts()
    topk = set(combined_counts.head(top_k).index.tolist())

    # DAY_OF_MONTH filter: even and <= 28 (changed from odd to even)
    day_series = pd.to_numeric(df[day_col], errors="coerce")
    day_mask = day_series.notna() & ((day_series % 2) == 0) & (day_series <= 28)

    # Both ORIGIN and DEST in top-k
    origin_in_topk = df[origin_col].astype(str).isin(topk)
    dest_in_topk = df[dest_col].astype(str).isin(topk)
    both_mask = origin_in_topk & dest_in_topk

    # Combined filter
    final_mask = day_mask & both_mask
    reduced_df = df.loc[final_mask].copy()
    n_reduced = reduced_df.shape[0]

    # Ensure output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build output filename
    stem = input_path.stem
    suffix = input_path.suffix or ".csv"
    out_name = f"{stem}-reduced{suffix}"
    out_path = out_dir / out_name

    # Write reduced CSV (preserve index False)
    reduced_df.to_csv(out_path, index=False)

    # Percentage reduction
    pct_reduction = (1.0 - (n_reduced / n_orig)) * 100 if n_orig > 0 else 0.0

    # Rank of 'MSN' in combined counts (1-based); show 'not present' if absent
    try:
        msn_rank = None
        if "MSN" in combined_counts.index:
            # +1 to convert zero-based index to 1-based rank
            msn_rank = int(combined_counts.index.get_loc("MSN") + 1)
    except Exception:
        msn_rank = None

    print(f"Input file: {input_path}")
    print(f"Original rows: {n_orig}")
    print(f"Reduced rows: {n_reduced}")
    print(f"Percentage reduction: {pct_reduction:.2f}%")
    if msn_rank is not None:
        print(f"Rank of 'MSN' in combined ORIGIN+DEST counts: {msn_rank}")
    else:
        print("'MSN' not present in combined ORIGIN+DEST counts for this file")
    print(f"Wrote reduced file: {out_path}")

    return 0


def reduce_df(df: pd.DataFrame, name: str, out_dir: Path, top_k: int = 105) -> int:
    """Reduce an in-memory DataFrame and write output named <name>-reduced.csv to out_dir.

    Returns exit code (0 ok).
    """
    n_orig = df.shape[0]

    # Find relevant columns
    origin_col = find_column_case_insensitive(df, "ORIGIN")
    dest_col = find_column_case_insensitive(df, "DEST")
    day_col = find_column_case_insensitive(df, "DAY_OF_MONTH")

    if origin_col is None or dest_col is None or day_col is None:
        print("Required columns not found in combined data. Need ORIGIN, DEST, and DAY_OF_MONTH (case-insensitive).")
        return 3

    # Compute top-k combined codes from full dataset
    origin_series = df[origin_col].dropna().astype(str)
    dest_series = df[dest_col].dropna().astype(str)
    combined = pd.concat([origin_series, dest_series], ignore_index=True)
    combined_counts = combined.value_counts()
    topk = set(combined_counts.head(top_k).index.tolist())

    # DAY_OF_MONTH filter: even and <= 28 (changed from odd to even)
    day_series = pd.to_numeric(df[day_col], errors="coerce")
    day_mask = day_series.notna() & ((day_series % 2) == 0) & (day_series <= 28)

    # Both ORIGIN and DEST in top-k
    origin_in_topk = df[origin_col].astype(str).isin(topk)
    dest_in_topk = df[dest_col].astype(str).isin(topk)
    both_mask = origin_in_topk & dest_in_topk

    # Combined filter
    final_mask = day_mask & both_mask
    reduced_df = df.loc[final_mask].copy()
    n_reduced = reduced_df.shape[0]

    # Ensure output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)

    # Build output filename
    suffix = ".csv"
    out_name = f"{name}-reduced{suffix}"
    out_path = out_dir / out_name

    # Write reduced CSV (preserve index False)
    reduced_df.to_csv(out_path, index=False)

    # Percentage reduction
    pct_reduction = (1.0 - (n_reduced / n_orig)) * 100 if n_orig > 0 else 0.0

    # Rank of 'MSN' in combined counts (1-based); show 'not present' if absent
    try:
        msn_rank = None
        if "MSN" in combined_counts.index:
            msn_rank = int(combined_counts.index.get_loc("MSN") + 1)
    except Exception:
        msn_rank = None

    print(f"Input combined: {name} (assembled from multiple files)")
    print(f"Original rows: {n_orig}")
    print(f"Reduced rows: {n_reduced}")
    print(f"Percentage reduction: {pct_reduction:.2f}%")
    if msn_rank is not None:
        print(f"Rank of 'MSN' in combined ORIGIN+DEST counts: {msn_rank}")
    else:
        print("'MSN' not present in combined ORIGIN+DEST counts for combined data")
    print(f"Wrote reduced file: {out_path}")

    return 0


def main(argv):
    parser = argparse.ArgumentParser(description="Create reduced CSV with specific filters")
    parser.add_argument("input", nargs="?", help="Path to input CSV (defaults to OriginalData/24-01.csv)")
    parser.add_argument("--out-dir", default="ReducedData", help="Directory to write reduced CSV")
    parser.add_argument("--top-k", type=int, default=105, help="Top-K combined ORIGIN/DEST codes to require (default 105)")
    args = parser.parse_args(argv[1:])

    out_dir = Path(args.out_dir)

    files_to_process = []
    if args.input:
        input_path = Path(args.input)
        if input_path.is_dir():
            files_to_process = sorted(input_path.glob("*.csv"))
        else:
            files_to_process = [input_path]
    else:
        default_dir = Path(__file__).resolve().parents[1] / "OriginalData"
        files_to_process = sorted(default_dir.glob("*.csv"))

    if not files_to_process:
        print("No CSV files found to process.")
        return 4

    # Ensure output directory exists
    out_dir.mkdir(parents=True, exist_ok=True)

    exit_code = 0
    for f in files_to_process:
        print("------------------------------------------------------------")
        code = reduce_csv(f, out_dir, top_k=args.top_k)
        if code != 0:
            exit_code = code

    # After processing individual files, also create a combined DataFrame and process it
    try:
        print("------------------------------------------------------------")
        combined_dfs = [pd.read_csv(f) for f in files_to_process]
        combined_df = pd.concat(combined_dfs, ignore_index=True)
        code = reduce_df(combined_df, "combined", out_dir, top_k=args.top_k)
        if code != 0:
            exit_code = code
    except Exception as e:
        print(f"Failed to build/process combined data: {e}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
