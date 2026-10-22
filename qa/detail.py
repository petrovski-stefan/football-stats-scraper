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


def validate(r: Report, df: pd.DataFrame) -> None:
    _check_history_recency_ordering(r, df)
    _check_history_depth_ordering(r, df)


def _section_columns(df: pd.DataFrame, section: str, field: str) -> list[str]:
    return [
        column
        for n in range(1, MATCHES_PER_SECTION + 1)
        if (column := f"{section}_last{n}_{field}") in df.columns
    ]


def _check_history_recency_ordering(r: Report, df: pd.DataFrame) -> None:
    """`last1` is newer than `last2`, and so on, for every row and every section.

    This is the direct test of the positional contract. It catches a swapped or
    off-by-one history index, which the populated-rate check below cannot see whenever
    every slot is filled (true of the home/away sections, where teams always have a
    full six prior matches).
    """
    if df.empty:
        return

    for section in PER_MATCH_SECTIONS:
        columns = _section_columns(df, section, "date")
        parsed = {c: pd.to_datetime(df[c], errors="coerce") for c in columns}

        for newer, older in pairwise(columns):
            comparable = parsed[newer].notna() & parsed[older].notna()
            out_of_order = int((parsed[newer][comparable] < parsed[older][comparable]).sum())
            r.check(
                out_of_order == 0,
                f"{out_of_order} rows where {newer} predates {older} — "
                f"per-match history blocks are out of recency order",
            )


def _check_history_depth_ordering(r: Report, df: pd.DataFrame) -> None:
    """Deeper history slots are no more populated than shallower ones.

    A team either has that many prior matches or it does not, so the populated rate can
    only decay with depth. Has teeth on the h2h section, where the gradient is real
    (100% -> 82%); the home/away sections are fully populated and so unconstrained here.
    """
    if df.empty:
        return

    for section in PER_MATCH_SECTIONS:
        rates = [
            (column, float(df[column].notna().mean()))
            for column in _section_columns(df, section, "ft_score")
        ]

        for (shallow, shallow_rate), (deep, deep_rate) in pairwise(rates):
            r.check(
                deep_rate <= shallow_rate + DEPTH_TOLERANCE,
                f"{deep} is more populated ({deep_rate:.0%}) than {shallow} "
                f"({shallow_rate:.0%}) — per-match history blocks are misaligned",
            )
