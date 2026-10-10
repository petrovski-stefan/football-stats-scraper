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
# A goal line below 1.5 means the OU column was misread.
OU_LINE_MIN = 1.5
# The largest plausible lines grow as the 1X2 favourite gets shorter (the user, 2026-10-10):
# a 1.02 favourite carries a 4.5 handicap and a 6.5 total, a 1.60 favourite nothing near
# either. Each band runs from its favourite price up to the next band's. The middle band keeps
# the fixed limits used before; on the 2026-10-09 corpus (58,772 matches) the largest lines
# were 6 and 7 in the first band and a 2.5 handicap in the last. A row without both 1X2 win
# prices uses the band holding NO_PRICE_BAND.
# (favourite price from, largest AH size, largest OU line)
LINE_LIMITS: tuple[tuple[float, float, float], ...] = (
    (1.00, 7.0, 8.5),
    (1.10, 4.0, 5.5),
    (1.35, 3.0, 5.5),
)
NO_PRICE_BAND = 1.10
# Asian lines move in quarter-goal steps, so every line is a multiple of 0.25.
QUARTER = 0.25
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
        return [cell for market in self.markets().values() for cell in market]


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
    steps. A line off the quarter grid means `parse_line` mis-split a fraction. The size of
    a line is `check_line_size`'s job.
    """
    markets = (
        ("OU", c.ou_line, c.over, c.under),
        ("AH", c.ah_line, c.ah_home, c.ah_away),
    )
    for kind, line, price_a, price_b in markets:
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
        off_grid = sub[((sub[line] / QUARTER).round() - sub[line] / QUARTER).abs() > 1e-9]
        r.check(
            off_grid.empty,
            f"{len(off_grid)} {kind} rows with a line off the quarter-goal grid "
            f"(parse_line mis-split a fraction?)",
        )


def _line_limits(df: pd.DataFrame, c: OddsColumns) -> tuple["pd.Series[float]", "pd.Series[float]"]:
    """Each row's largest AH size and OU line, from its 1X2 favourite's band."""
    if {c.home, c.away} <= set(df.columns):
        prices = df[[c.home, c.away]].astype(float)
        favourite = prices.min(axis=1, skipna=False).fillna(NO_PRICE_BAND)
    else:
        favourite = pd.Series(NO_PRICE_BAND, index=df.index)
    ah_max = pd.Series(LINE_LIMITS[0][1], index=df.index)
    ou_max = pd.Series(LINE_LIMITS[0][2], index=df.index)
    for start, ah_limit, ou_limit in LINE_LIMITS[1:]:
        ah_max = ah_max.mask(favourite >= start, ah_limit)
        ou_max = ou_max.mask(favourite >= start, ou_limit)
    return ah_max, ou_max


def check_line_size(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    """No line is bigger than its 1X2 favourite's price allows (`LINE_LIMITS`).

    A line past its band's limit means a column was misread, or the line belongs to another
    match. The fixed limits used before 2026-10-10 (a 4-goal handicap, a 5.5 total) failed
    real mismatches, where a 1.01-1.04 favourite carries a 4.25-6 handicap and a total up to 7.
    """
    ah_max, ou_max = _line_limits(df, c)
    ou = _present(df, c.ou_line, c.over, c.under)
    if not ou.empty:
        off = ou[(ou[c.ou_line] < OU_LINE_MIN) | (ou[c.ou_line] > ou_max[ou.index])]
        r.check(
            off.empty,
            f"{len(off)} OU rows with a line below {OU_LINE_MIN} or above its favourite's limit",
        )
    ah = _present(df, c.ah_line, c.ah_home, c.ah_away)
    if not ah.empty:
        big = ah[ah[c.ah_line].abs() > ah_max[ah.index]]
        r.check(big.empty, f"{len(big)} AH rows with a line bigger than its favourite's limit")


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


def check_goal_line_above_handicap(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    """The O/U goal line is above the AH line's size.

    A total no larger than the expected margin would mean the favourite scores every goal.
    The page opened some O/U lines at exactly the AH line's size on 6 and 19 Oct 2024 (found
    2026-10-08). When that size is 1.5 or more, the line passes every other check, so only
    this one sees it.
    """
    sub = _present(df, c.ou_line, c.ah_line)
    if sub.empty:
        return
    flat = sub[sub[c.ou_line] <= sub[c.ah_line].abs()]
    r.check(flat.empty, f"{len(flat)} rows whose OU line is not above the AH line's size")


def check_whole_markets(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    """Each market is all or nothing: a row holds all three of its cells or none.

    The page shows a market's line and prices together, and `scrapers/schedule.py:
    drop_stale_odds` empties whole markets only, so a part-filled market is a misread cell.
    """
    for kind, cells in c.markets().items():
        if not set(cells) <= set(df.columns):
            continue
        filled = df[list(cells)].notna().sum(axis=1)
        part = int(((filled > 0) & (filled < len(cells))).sum())
        r.check(part == 0, f"{part} {kind} rows with only part of the market filled")


def check_coverage(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    """At least `COVERAGE_FLOOR` of the rows carry all three markets.

    A table without one of the columns is skipped: `universal.check_required_columns`
    reports the column once.
    """
    if df.empty or not set(c.cells()) <= set(df.columns):
        return
    full = len(_present(df, *c.cells()))
    share = full / len(df)
    r.check(
        share >= COVERAGE_FLOOR,
        f"{full}/{len(df)} rows ({share:.1%}) carry all three markets, "
        f"below the {COVERAGE_FLOOR:.0%} floor",
    )


def check_all(r: Report, df: pd.DataFrame, c: OddsColumns) -> None:
    """The checks every table gets. The staged schedule adds `check_whole_markets` and
    `check_coverage` (`qa/schedule.py`); the archived files predate both."""
    check_1x2(r, df, c)
    check_asian(r, df, c)
    check_line_size(r, df, c)
    check_ah_sign(r, df, c)
    check_goal_line_above_handicap(r, df, c)
