"""Odds checks for any schedule table, given its column names.

Shared by the old base league CSVs (`qa/league.py`) and the staged schedule files
(`qa/schedule.py`), which hold the same three markets under different names. A row counts
as having a market when all of its prices (and line) are present.
"""

from dataclasses import dataclass

import pandas as pd

from qa.report import Report

# A 1X2 book below 1.00 is arbitrage-free-impossible; above 1.20 means the column is not
# 1X2 at all — most likely Asian Handicap, which is what the schedule page defaults to.
OVERROUND_MIN = 1.00
OVERROUND_MAX = 1.20
# Two-way Asian books run much tighter than a three-way 1X2 book.
TWO_WAY_OVERROUND_MAX = 1.12
# Plausible goal lines. Below 1.5 or above 5.5 means the OU column was misread.
OU_LINE_MIN, OU_LINE_MAX = 1.5, 5.5
# Asian handicaps beyond +/- 4 goals do not occur in league football.
AH_LINE_ABS_MAX = 4.0
# Asian lines move in quarter-goal steps, so every line is a multiple of 0.25.
QUARTER = 0.25
# Share of rows whose AH sign may disagree with the 1X2 favourite before it is a finding.
AH_SIGN_TOLERANCE = 0.02


@dataclass(frozen=True)
class OddsColumns:
    """Where a table keeps its three markets."""

    home: str
    draw: str
    away: str
    ou_line: str
    over: str
    under: str
    ah_line: str
    ah_home: str
    ah_away: str


def _present(df: pd.DataFrame, *columns: str) -> pd.DataFrame:
    """The rows holding every one of `columns`. A table without one of the columns has no
    such rows: a missing column is reported once, by `universal.check_required_columns`."""
    if not set(columns) <= set(df.columns):
        return df.iloc[0:0]
    return df[df[list(columns)].notna().all(axis=1)]


def check_1x2(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    """The 1X2 prices are real prices, and the column really is 1X2."""
    sub = _present(df, c.home, c.draw, c.away)
    if sub.empty:
        return
    impossible = sub[(sub[c.home] <= 1) | (sub[c.draw] <= 1) | (sub[c.away] <= 1)]
    r.check(impossible.empty, f"{len(impossible)} rows with a 1X2 price <= 1")
    overround = 1 / sub[c.home] + 1 / sub[c.draw] + 1 / sub[c.away]
    out_of_band = sub[(overround < OVERROUND_MIN) | (overround > OVERROUND_MAX)]
    r.check(
        out_of_band.empty,
        f"{len(out_of_band)} rows with an implausible overround "
        f"(outside {OVERROUND_MIN:.2f}-{OVERROUND_MAX:.2f}) — is the column really 1X2?",
    )


def check_asian(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    """The O/U and AH columns hold real two-way Asian markets.

    Their vig is far tighter than the 1X2 column's, and both lines move in quarter-goal
    steps. A line off the quarter grid means `parse_line` mis-split a fraction; an
    out-of-range line means the wrong column was read.
    """
    markets = (
        ("OU", c.ou_line, c.over, c.under, OU_LINE_MIN, OU_LINE_MAX),
        ("AH", c.ah_line, c.ah_home, c.ah_away, -AH_LINE_ABS_MAX, AH_LINE_ABS_MAX),
    )
    for kind, line, price_a, price_b, lo, hi in markets:
        sub = _present(df, line, price_a, price_b)
        if sub.empty:
            continue
        bad_price = sub[(sub[price_a] <= 1) | (sub[price_b] <= 1)]
        r.check(bad_price.empty, f"{len(bad_price)} {kind} rows with a price <= 1")
        overround = 1 / sub[price_a] + 1 / sub[price_b]
        wide = sub[(overround < OVERROUND_MIN) | (overround > TWO_WAY_OVERROUND_MAX)]
        r.check(
            wide.empty,
            f"{len(wide)} {kind} rows with a two-way overround outside "
            f"{OVERROUND_MIN:.2f}-{TWO_WAY_OVERROUND_MAX:.2f}",
        )
        off_range = sub[(sub[line] < lo) | (sub[line] > hi)]
        r.check(off_range.empty, f"{len(off_range)} {kind} rows with a line outside {lo}..{hi}")
        off_grid = sub[((sub[line] / QUARTER).round() - sub[line] / QUARTER).abs() > 1e-9]
        r.check(
            off_grid.empty,
            f"{len(off_grid)} {kind} rows with a line off the quarter-goal grid "
            f"(parse_line mis-split a fraction?)",
        )


def check_ah_sign(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    """A positive AH line must mean the home side is the 1X2 favourite."""
    sub = _present(df, c.ah_line, c.home, c.away)
    if sub.empty:
        return
    sub = sub[sub[c.ah_line] != 0]
    if sub.empty:
        return
    home_fav = sub[c.home] < sub[c.away]
    disagree = sub[(sub[c.ah_line] > 0) != home_fav]
    share = len(disagree) / len(sub)
    r.check(
        share <= AH_SIGN_TOLERANCE,
        f"{len(disagree)}/{len(sub)} ({share:.1%}) rows where the AH sign contradicts the "
        f"1X2 favourite — sign convention broken?",
    )


def check_all(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    check_1x2(r, df, c)
    check_asian(r, df, c)
    check_ah_sign(r, df, c)
