#!/usr/bin/env python3
"""
Generate compact, aggregated datasets that power the Streamlit dashboard.

Usage:
    python precompute_stats.py --source MHCLD_PUF_2023_clean.csv --output-dir data
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List

import pandas as pd


DIAGNOSIS_COLS: List[str] = [
    "TRAUSTREFLG",
    "ANXIETYFLG",
    "ADHDFLG",
    "CONDUCTFLG",
    "DELIRDEMFLG",
    "BIPOLARFLG",
    "DEPRESSFLG",
    "ODDFLG",
    "PDDFLG",
    "PERSONFLG",
    "SCHIZOFLG",
    "ALCSUBFLG",
    "OTHERDISFLG",
]

SERVICE_COLS: List[str] = [
    "SPHSERVICE",
    "CMPSERVICE",
    "OPISERVICE",
    "RTCSERVICE",
    "IJSSERVICE",
]

DEMO_KEYS: List[str] = [
    "AGE",
    "RACE",
    "SEX",
    "EMPLOY",
    "LIVARAG",
    "STATEFIP",
    "STATEFIP_code",
]

SUBSTANCE_KEYS: List[str] = [
    "AGE",
    "RACE",
    "SEX",
    "EMPLOY",
    "LIVARAG",
    "SUB_dia",
    "SUB",
    "SAP",
]

USECOLS: List[str] = sorted(
    set(DIAGNOSIS_COLS + SERVICE_COLS + DEMO_KEYS + ["SUB", "SAP"])
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pre-aggregate MHCLD data.")
    parser.add_argument(
        "--source",
        required=True,
        type=Path,
        help="Path to the MHCLD_PUF_2023_clean.csv file.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Directory to store aggregated CSV files.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=250_000,
        help="Number of rows to process per chunk when streaming the source CSV.",
    )
    return parser.parse_args()


def preprocess(chunk: pd.DataFrame) -> pd.DataFrame:
    chunk = chunk.copy()
    chunk["SUB_dia"] = chunk["SUB"].notna().map({True: "YES", False: "NO"})
    chunk["SAP"] = chunk["SAP"].apply(
        lambda val: "missing" if pd.isna(val) else str(val)
    )
    return chunk


def aggregate_chunks(
    source: Path, chunk_size: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    demo_frames: List[pd.DataFrame] = []
    substance_frames: List[pd.DataFrame] = []

    for chunk in pd.read_csv(
        source, chunksize=chunk_size, usecols=USECOLS, low_memory=False
    ):
        chunk = preprocess(chunk)

        demo_frames.append(
            chunk.groupby(DEMO_KEYS, dropna=False)[DIAGNOSIS_COLS + SERVICE_COLS]
            .sum()
            .reset_index()
        )

        substance_frames.append(
            chunk.groupby(SUBSTANCE_KEYS, dropna=False)[DIAGNOSIS_COLS]
            .sum()
            .reset_index()
        )

    demo_df = (
        pd.concat(demo_frames)
        .groupby(DEMO_KEYS, dropna=False)[DIAGNOSIS_COLS + SERVICE_COLS]
        .sum()
        .reset_index()
    )

    substance_df = (
        pd.concat(substance_frames)
        .groupby(SUBSTANCE_KEYS, dropna=False)[DIAGNOSIS_COLS]
        .sum()
        .reset_index()
    )

    return demo_df, substance_df


def main() -> None:
    args = parse_args()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    demo_df, substance_df = aggregate_chunks(args.source, args.chunk_size)

    demo_path = output_dir / "demographic_service_stats.csv"
    substance_path = output_dir / "substance_stats.csv"

    demo_df.to_csv(demo_path, index=False)
    substance_df.to_csv(substance_path, index=False)

    print(f"Saved demographic/service aggregates to {demo_path}")
    print(f"Saved substance aggregates to {substance_path}")


if __name__ == "__main__":
    main()
