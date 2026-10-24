"""Dataset-agnostic checks — the ones that hold for any table this project writes,
whatever its columns happen to mean.

These are the checks that were previously duplicated (and had drifted apart: the base
CSV's key check compared raw values while the detail CSV's compared `astype(str)`, so
an int64 id and a str id were being validated differently). Anything that needs to know
what a column *means* belongs in `qa/league.py` or `qa/detail.py` instead.
"""

from collections.abc import Collection, Mapping, Sequence

import pandas as pd

from qa.report import Report

# A parser whose selector broke does not raise — the section is best-effort and nullable,
# so it silently yields a column of None. Any column this empty is treated as breakage.
# Legitimately sparse columns sit far below it (the deepest history blocks reach ~44%).
DEAD_COLUMN_THRESHOLD = 0.95


def check_not_empty(report: Report, df: pd.DataFrame) -> None:
    """The file exists but holds no rows — a scrape that produced nothing."""

    report.check(not df.empty, "file has no rows")


def check_required_columns(report: Report, df: pd.DataFrame, expected: Sequence[str]) -> None:
    """Every column the schema declares is present.

    `scrapers/csv_io.py:write_ordered_csv` filters to the columns present in the frame,
    so a field that stops being produced disappears from the CSV without complaint.
    """

    missing = [c for c in expected if c not in df.columns]
    report.check(
        not missing,
        f"{len(missing)} declared column(s) missing: {missing[:8]}"
        + (" ..." if len(missing) > 8 else ""),
    )


def check_primary_key(report: Report, df: pd.DataFrame, key: str = "match_id") -> None:
    """The key column exists, is fully populated, and identifies rows uniquely.

    Values are normalised to stripped strings first so the same id compares equal
    whatever dtype pandas inferred for a given file.
    """

    if key not in df.columns:
        report.check(False, f"missing primary key column {key!r}")
        return

    column = df[key]
    null_count = int(column.isna().sum())
    report.check(null_count == 0, f"{null_count} rows with a null {key}")

    normalised = column.dropna().astype(str).str.strip()
    blank_count = int((normalised == "").sum())
    report.check(blank_count == 0, f"{blank_count} rows with a blank {key}")

    duplicate_count = int(normalised.duplicated().sum())
    report.check(duplicate_count == 0, f"{duplicate_count} duplicate {key}")


def check_unique_across(
    report: Report, ids: Mapping[str, Collection[str]], key: str = "match_id"
) -> None:
    """No id appears in more than one file. `ids` maps each file's name to its ids; a repeat
    inside one file is `check_primary_key`'s job.

    A match stored in two files is counted twice by anything that reads them together.
    """

    files: dict[str, list[str]] = {}
    for name, values in ids.items():
        for value in set(values):
            files.setdefault(value, []).append(name)

    shared = sorted((value, names) for value, names in files.items() if len(names) > 1)
    example = f", e.g. {shared[0][0]} in {shared[0][1]}" if shared else ""
    report.check(not shared, f"{len(shared)} {key} values in more than one file{example}")


def check_declared(
    report: Report, found: Mapping[str, Collection[str]], declared: Collection[str], what: str
) -> None:
    """Every file holds only declared values. `found` maps each file's name to its values;
    `what` names a stray value in the message.

    A file left behind when its entry was taken out of the declaration (a league removed
    from the config) would still be read with the rest.
    """

    allowed = set(declared)
    stray = sorted(name for name, values in found.items() if not set(values) <= allowed)
    report.check(not stray, f"{len(stray)} files with a {what} {stray[:3]}")


def check_no_dead_columns(
    report: Report,
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
    report.check(
        not dead,
        f"{len(dead)} column(s) >= {threshold:.0%} empty (parser canary): {dead[:8]}"
        + (" ..." if len(dead) > 8 else ""),
    )


def check_ids_covered(
    report: Report, expected: Collection[str], actual: Collection[str], subject: str
) -> None:
    """Every id in `expected` appears in `actual` — join/coverage completeness."""

    missing = set(expected) - set(actual)
    report.check(not missing, f"{len(missing)} ids missing from {subject}")


def check_attempt_log(
    report: Report, store_df: pd.DataFrame, attempt_log_df: pd.DataFrame, count_field: str
) -> None:
    """A global store and its attempt log agree, in all three ways they can disagree.

    Both `data/archived/raw/goals.csv` and `data/archived/raw/events.csv` are append-only stores
    whose resume key is a separate log, because a match can legitimately produce zero rows — a 0-0
    has no goals, a clean match has no cards. That makes the log load-bearing: if it drifts from the
    store, either work is silently repeated forever or rows are orphaned.

    The three failures, in increasing subtlety: a duplicated id (the match is re-scraped
    every run), a store row with no log entry (written outside the lock, or a crash between
    the two appends), and a log entry whose claimed count disagrees with the rows actually
    present (a partial write).
    """

    dupes = int(attempt_log_df["match_id"].duplicated().sum())
    report.check(dupes == 0, f"{dupes} duplicate match_id in the attempt log (would re-scrape)")

    logged = set(attempt_log_df["match_id"].astype(str))
    orphans = set(store_df["match_id"].astype(str)) - logged
    report.check(not orphans, f"{len(orphans)} matches have rows but no attempt-log entry")

    counted = store_df.groupby(store_df["match_id"].astype(str)).size().to_dict()
    claimed = dict(
        zip(
            attempt_log_df["match_id"].astype(str),
            [int(v) for v in attempt_log_df[count_field]],
            strict=True,
        )
    )
    mismatched = [m for m, n in claimed.items() if int(counted.get(m, 0)) != n]
    report.check(
        not mismatched,
        f"{len(mismatched)} matches where the attempt log's {count_field} disagrees with the rows",
    )
