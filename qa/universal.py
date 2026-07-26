"""Dataset-agnostic checks — the ones that hold for any table this project writes,
whatever its columns happen to mean.

These are the checks that were previously duplicated (and had drifted apart: the base
CSV's key check compared raw values while the detail CSV's compared `astype(str)`, so
an int64 id and a str id were being validated differently). Anything that needs to know
what a column *means* belongs in `qa/league.py` or `qa/detail.py` instead.
"""

from collections.abc import Collection, Sequence

import pandas as pd

from qa.report import Report

# A parser whose selector broke does not raise — the section is best-effort and nullable,
# so it silently yields a column of None. Any column this empty is treated as breakage.
# Legitimately sparse columns sit far below it (the deepest history blocks reach ~44%).
DEAD_COLUMN_THRESHOLD = 0.95


def check_not_empty(r: Report, df: pd.DataFrame) -> None:
    """The file exists but holds no rows — a scrape that produced nothing."""
    r.check(not df.empty, "file has no rows")


def check_required_columns(r: Report, df: pd.DataFrame, expected: Sequence[str]) -> None:
    """Every column the schema declares is present.

    `scrapers/csv_io.py:write_ordered_csv` filters to the columns present in the frame,
    so a field that stops being produced disappears from the CSV without complaint.
    """
    missing = [c for c in expected if c not in df.columns]
    r.check(
        not missing,
        f"{len(missing)} declared column(s) missing: {missing[:8]}"
        + (" ..." if len(missing) > 8 else ""),
    )


def check_primary_key(r: Report, df: pd.DataFrame, key: str = "match_id") -> None:
    """The key column exists, is fully populated, and identifies rows uniquely.

    Values are normalised to stripped strings first so the same id compares equal
    whatever dtype pandas inferred for a given file.
    """
    if key not in df.columns:
        r.check(False, f"missing primary key column {key!r}")
        return

    column = df[key]
    null_count = int(column.isna().sum())
    r.check(null_count == 0, f"{null_count} rows with a null {key}")

    normalised = column.dropna().astype(str).str.strip()
    blank_count = int((normalised == "").sum())
    r.check(blank_count == 0, f"{blank_count} rows with a blank {key}")

    duplicate_count = int(normalised.duplicated().sum())
    r.check(duplicate_count == 0, f"{duplicate_count} duplicate {key}")


def check_no_dead_columns(
    r: Report,
    df: pd.DataFrame,
    *,
    optional: Collection[str] = (),
    threshold: float = DEAD_COLUMN_THRESHOLD,
) -> None:
    """No column is empty enough to indicate a broken parser selector.

    `optional` names columns the schema declares may legitimately be empty; it is a
    contract statement, not a place to park known-broken columns.
    """
    if df.empty:
        return
    empty_rate = df.isna().mean()
    dead = sorted(
        str(name)
        for name, rate in empty_rate.items()
        if rate >= threshold and str(name) not in optional
    )
    r.check(
        not dead,
        f"{len(dead)} column(s) >= {threshold:.0%} empty (parser canary): {dead[:8]}"
        + (" ..." if len(dead) > 8 else ""),
    )


def check_ids_covered(
    r: Report, expected: Collection[str], actual: Collection[str], subject: str
) -> None:
    """Every id in `expected` appears in `actual` — join/coverage completeness."""
    missing = set(expected) - set(actual)
    r.check(not missing, f"{len(missing)} ids missing from {subject}")
