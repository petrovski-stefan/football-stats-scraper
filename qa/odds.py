"""Odds checks for any schedule table, given its column names.

Shared by the old base league CSVs (`qa/league.py`) and the staged schedule files
(`qa/schedule.py`), which hold the same three markets under different names. A row counts
as having a market when all of its prices (and line) are present.
"""

from dataclasses import dataclass
from itertools import chain

import pandas as pd

from qa.report import Report


@dataclass(frozen=True)
class LineBand:
    """The largest AH size and O/U line for a 1X2 favourite priced from `favourite_from` up."""

    favourite_from: float
    largest_ah: float
    largest_ou: float


# A 1X2 book below 1.00 is arbitrage-free-impossible; above 1.20 means the column is not
# 1X2 at all — most likely Asian Handicap, which is what the schedule page defaults to.
OVERROUND_MIN = 1.00
OVERROUND_MAX = 1.20
# Two-way Asian books run much tighter than a three-way 1X2 book.
TWO_WAY_OVERROUND_MAX = 1.12
# A goal line below 1.5 means the OU column was misread.
OU_LINE_MIN = 1.5
# The largest plausible lines grow as the 1X2 favourite gets shorter (the user, 2026-10-10):
# a 1.02 favourite carries a 4.5 handicap and a 6.5 total, a 1.60 favourite nothing near
# either. Each band runs from its favourite price up to the next band's. The middle band keeps
# the fixed limits used before; on the 2026-10-09 corpus (58,772 matches) the largest lines
# were 6 and 7 in the first band and a 2.5 handicap in the last. A row without both 1X2 win
# prices uses the band holding NO_PRICE_BAND.
LINE_LIMITS: tuple[LineBand, ...] = (
    LineBand(favourite_from=1.00, largest_ah=7.0, largest_ou=8.5),
    LineBand(favourite_from=1.10, largest_ah=4.0, largest_ou=5.5),
    LineBand(favourite_from=1.35, largest_ah=3.0, largest_ou=5.5),
)
NO_PRICE_BAND = 1.10
# Asian lines move in quarter-goal steps, so every line is a multiple of 0.25.
QUARTER = 0.25
# Slack for float rounding when a line is held to that grid; a misread line is off by far more.
GRID_TOLERANCE = 1e-9
# Share of rows whose AH sign may disagree with the 1X2 favourite before it is a finding.
AH_SIGN_TOLERANCE = 0.02
# The smallest share of a table's rows that must carry all three markets (the user,
# 2026-10-10). The kept leagues price every match but the rare one the bookmaker skipped,
# such as an awarded match; a round the page did not show odds for takes a season below it.
COVERAGE_FLOOR = 0.99


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

    def markets(self) -> dict[str, tuple[str, str, str]]:
        """Each market's three cells, under the name the reports use."""

        return {
            "1X2": (self.home, self.draw, self.away),
            "OU": (self.ou_line, self.over, self.under),
            "AH": (self.ah_line, self.ah_home, self.ah_away),
        }

    def cells(self) -> list[str]:
        """All nine cells, market by market."""

        return list(chain.from_iterable(self.markets().values()))


def _present(df: pd.DataFrame, *columns: str) -> pd.DataFrame:
    """The rows holding every one of `columns`. A table without one of the columns has no
    such rows: a missing column is reported once, by `universal.check_required_columns`."""

    if not set(columns) <= set(df.columns):
        return df.iloc[0:0]

    return df[df[list(columns)].notna().all(axis=1)]


def check_1x2(report: Report, df: pd.DataFrame, odds_columns: OddsColumns) -> None:
    """The 1X2 prices are real prices, and the column really is 1X2."""

    present_df = _present(df, odds_columns.home, odds_columns.draw, odds_columns.away)
    if present_df.empty:
        return

    impossible_df = present_df[
        (present_df[odds_columns.home] <= 1)
        | (present_df[odds_columns.draw] <= 1)
        | (present_df[odds_columns.away] <= 1)
    ]
    report.check(impossible_df.empty, f"{len(impossible_df)} rows with a 1X2 price <= 1")

    overround = (
        1 / present_df[odds_columns.home]
        + 1 / present_df[odds_columns.draw]
        + 1 / present_df[odds_columns.away]
    )
    out_of_band_df = present_df[(overround < OVERROUND_MIN) | (overround > OVERROUND_MAX)]
    report.check(
        out_of_band_df.empty,
        f"{len(out_of_band_df)} rows with an implausible overround "
        f"(outside {OVERROUND_MIN:.2f}-{OVERROUND_MAX:.2f}) — is the column really 1X2?",
    )


def check_asian(report: Report, df: pd.DataFrame, odds_columns: OddsColumns) -> None:
    """The O/U and AH columns hold real two-way Asian markets: an overround far tighter than
    the 1X2 one, and lines on the quarter-goal grid (a line off it means `parse_line` mis-split
    a fraction). The size of a line is `check_line_size`'s job.
    """

    markets = (
        ("OU", odds_columns.ou_line, odds_columns.over, odds_columns.under),
        ("AH", odds_columns.ah_line, odds_columns.ah_home, odds_columns.ah_away),
    )

    for kind, line, price_a, price_b in markets:
        present_df = _present(df, line, price_a, price_b)
        if present_df.empty:
            continue

        bad_price_df = present_df[(present_df[price_a] <= 1) | (present_df[price_b] <= 1)]
        report.check(bad_price_df.empty, f"{len(bad_price_df)} {kind} rows with a price <= 1")

        overround = 1 / present_df[price_a] + 1 / present_df[price_b]
        wide_df = present_df[(overround < OVERROUND_MIN) | (overround > TWO_WAY_OVERROUND_MAX)]
        report.check(
            wide_df.empty,
            f"{len(wide_df)} {kind} rows with a two-way overround outside "
            f"{OVERROUND_MIN:.2f}-{TWO_WAY_OVERROUND_MAX:.2f}",
        )

        quarters = present_df[line] / QUARTER
        off_grid_df = present_df[(quarters - quarters.round()).abs() > GRID_TOLERANCE]
        report.check(
            off_grid_df.empty,
            f"{len(off_grid_df)} {kind} rows with a line off the quarter-goal grid "
            f"(parse_line mis-split a fraction?)",
        )


def _line_limits(
    df: pd.DataFrame, odds_columns: OddsColumns
) -> tuple["pd.Series[float]", "pd.Series[float]"]:
    """Each row's largest AH size and OU line, from its 1X2 favourite's band."""

    if {odds_columns.home, odds_columns.away} <= set(df.columns):
        prices_df = df[[odds_columns.home, odds_columns.away]].astype(float)
        favourite = prices_df.min(axis=1, skipna=False).fillna(NO_PRICE_BAND)
    else:
        favourite = pd.Series(NO_PRICE_BAND, index=df.index)

    ah_max = pd.Series(LINE_LIMITS[0].largest_ah, index=df.index)
    ou_max = pd.Series(LINE_LIMITS[0].largest_ou, index=df.index)
    for band in LINE_LIMITS[1:]:
        ah_max = ah_max.mask(favourite >= band.favourite_from, band.largest_ah)
        ou_max = ou_max.mask(favourite >= band.favourite_from, band.largest_ou)

    return ah_max, ou_max


def check_line_size(report: Report, df: pd.DataFrame, odds_columns: OddsColumns) -> None:
    """No line is bigger than its 1X2 favourite's price allows (`LINE_LIMITS`): a line past
    its band's limit means a misread column, or a line from another match.
    """

    ah_max, ou_max = _line_limits(df, odds_columns)

    ou_present_df = _present(df, odds_columns.ou_line, odds_columns.over, odds_columns.under)
    if not ou_present_df.empty:
        ou_off_limit_df = ou_present_df[
            (ou_present_df[odds_columns.ou_line] < OU_LINE_MIN)
            | (ou_present_df[odds_columns.ou_line] > ou_max[ou_present_df.index])
        ]
        report.check(
            ou_off_limit_df.empty,
            f"{len(ou_off_limit_df)} OU rows with a line below "
            f"{OU_LINE_MIN} or above its favourite's limit",
        )

    ah_present_df = _present(df, odds_columns.ah_line, odds_columns.ah_home, odds_columns.ah_away)
    if not ah_present_df.empty:
        ah_off_limit_df = ah_present_df[
            ah_present_df[odds_columns.ah_line].abs() > ah_max[ah_present_df.index]
        ]
        report.check(
            ah_off_limit_df.empty,
            f"{len(ah_off_limit_df)} AH rows with a line bigger than its favourite's limit",
        )


def check_ah_sign(report: Report, df: pd.DataFrame, odds_columns: OddsColumns) -> None:
    """A positive AH line must mean the home side is the 1X2 favourite."""

    present_df = _present(df, odds_columns.ah_line, odds_columns.home, odds_columns.away)
    if present_df.empty:
        return

    present_df = present_df[present_df[odds_columns.ah_line] != 0]
    if present_df.empty:
        return

    home_is_favourite = present_df[odds_columns.home] < present_df[odds_columns.away]
    disagree_df = present_df[(present_df[odds_columns.ah_line] > 0) != home_is_favourite]
    share = len(disagree_df) / len(present_df)
    report.check(
        share <= AH_SIGN_TOLERANCE,
        f"{len(disagree_df)}/{len(present_df)} ("
        f"{share:.1%}) rows where the AH sign contradicts the "
        f"1X2 favourite — sign convention broken?",
    )


def check_goal_line_above_handicap(
    report: Report, df: pd.DataFrame, odds_columns: OddsColumns
) -> None:
    """The O/U goal line is above the AH line's size: a total no larger than the expected
    margin means the favourite scores every goal. The page opened some O/U lines at exactly
    the AH size (6 and 19 Oct 2024); from 1.5 up only this check sees them (`qa/CLAUDE.md` §5a).
    """

    present_df = _present(df, odds_columns.ou_line, odds_columns.ah_line)
    if present_df.empty:
        return

    flat_df = present_df[present_df[odds_columns.ou_line] <= present_df[odds_columns.ah_line].abs()]
    report.check(
        flat_df.empty, f"{len(flat_df)} rows whose OU line is not above the AH line's size"
    )


def check_whole_markets(report: Report, df: pd.DataFrame, odds_columns: OddsColumns) -> None:
    """Each market is all or nothing: a row holds all three of its cells or none.

    The page shows a market's line and prices together, and `scrapers/schedule.py:
    drop_stale_odds` empties whole markets only, so a part-filled market is a misread cell.
    """

    for kind, cells in odds_columns.markets().items():
        if not set(cells) <= set(df.columns):
            continue

        filled = df[list(cells)].notna().sum(axis=1)
        part = int(((filled > 0) & (filled < len(cells))).sum())
        report.check(part == 0, f"{part} {kind} rows with only part of the market filled")


def check_coverage(report: Report, df: pd.DataFrame, odds_columns: OddsColumns) -> None:
    """At least `COVERAGE_FLOOR` of the rows carry all three markets.

    A table without one of the columns is skipped: `universal.check_required_columns`
    reports the column once.
    """

    if df.empty or not set(odds_columns.cells()) <= set(df.columns):
        return

    full = len(_present(df, *odds_columns.cells()))
    share = full / len(df)
    report.check(
        share >= COVERAGE_FLOOR,
        f"{full}/{len(df)} rows ({share:.1%}) carry all three markets, "
        f"below the {COVERAGE_FLOOR:.0%} floor",
    )


def check_all(report: Report, df: pd.DataFrame, odds_columns: OddsColumns) -> None:
    """The checks every table gets. The staged schedule adds `check_whole_markets` and
    `check_coverage` (`qa/schedule.py`); the archived files predate both."""

    check_1x2(report, df, odds_columns)
    check_asian(report, df, odds_columns)
    check_line_size(report, df, odds_columns)
    check_ah_sign(report, df, odds_columns)
    check_goal_line_above_handicap(report, df, odds_columns)
