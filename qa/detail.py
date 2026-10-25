"""Checks specific to a detail-scrape CSV (`data/archived/raw/<league>_<season>_detail.csv`).

The dataset-agnostic checks (key, schema, dead columns) are applied by `qa/validate.py`
from `qa/universal.py`. What is specific here is the shape of the per-match history
blocks that `scrapers/detail_parsers.py:flatten_history` writes: `last1` is the most
recent match, counting backwards to `MATCHES_PER_SECTION`.

That ordering is load-bearing. Every `*_lastN_*` feature is positional, so a shifted or
swapped index silently attaches the wrong game's goals, corners and odds to a match —
which no other check would notice, because the values stay individually plausible.
"""

from itertools import pairwise

import pandas as pd

from domain.columns import MATCHES_PER_SECTION, PER_MATCH_SECTIONS
from qa.report import Report

# Slack on the populated-rate gradient: a team with exactly N prior matches makes a
# small non-monotonicity legitimate. A real indexing bug inverts the ordering outright.
DEPTH_TOLERANCE = 0.02


def validate(report: Report, detail_df: pd.DataFrame) -> None:
    """Run every detail-file check."""

    _check_history_recency_ordering(report, detail_df)
    _check_history_depth_ordering(report, detail_df)


def _section_columns(detail_df: pd.DataFrame, section: str, field: str) -> list[str]:
    """One section's `field` columns, newest block first; a column the file lacks is left out."""

    return [
        column
        for slot in range(1, MATCHES_PER_SECTION + 1)
        if (column := f"{section}_last{slot}_{field}") in detail_df.columns
    ]


def _check_history_recency_ordering(report: Report, detail_df: pd.DataFrame) -> None:
    """`last1` is newer than `last2`, and so on, in every row and section: this catches a
    swapped or off-by-one history index even where every slot is filled. A date that does
    not parse fails, rather than dropping out of the comparison.
    """

    if detail_df.empty:
        return

    for section in PER_MATCH_SECTIONS:
        columns = _section_columns(detail_df, section, "date")
        parsed = {c: pd.to_datetime(detail_df[c], errors="coerce") for c in columns}

        unparseable = sum(int((detail_df[c].notna() & parsed[c].isna()).sum()) for c in columns)
        report.check(
            unparseable == 0,
            f"{unparseable} {section} history dates that do not parse "
            f"(left out of the order check)",
        )

        for newer, older in pairwise(columns):
            comparable = parsed[newer].notna() & parsed[older].notna()
            out_of_order = int((parsed[newer][comparable] < parsed[older][comparable]).sum())
            report.check(
                out_of_order == 0,
                f"{out_of_order} rows where {newer} predates {older} — "
                f"per-match history blocks are out of recency order",
            )


def _check_history_depth_ordering(report: Report, detail_df: pd.DataFrame) -> None:
    """Deeper history slots are no more populated than shallower ones, since a team either has
    that many prior matches or not. Only the h2h section has a real gradient (100% to 82%);
    the home and away sections are always full, so the check has nothing to test there.
    """

    if detail_df.empty:
        return

    for section in PER_MATCH_SECTIONS:
        rates = [
            (column, float(detail_df[column].notna().mean()))
            for column in _section_columns(detail_df, section, "ft_score")
        ]

        for (shallow, shallow_rate), (deep, deep_rate) in pairwise(rates):
            report.check(
                deep_rate <= shallow_rate + DEPTH_TOLERANCE,
                f"{deep} is more populated ({deep_rate:.0%}) than {shallow} "
                f"({shallow_rate:.0%}) — per-match history blocks are misaligned",
            )
