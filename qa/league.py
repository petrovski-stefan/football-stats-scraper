"""Checks specific to a base league CSV (`data/archived/raw/<league>_<season>.csv`).

These need to know what the columns mean: what a round is, that half-time goals cannot
exceed full-time goals, what a plausible 1X2 overround looks like. Dataset-agnostic
checks (key, schema, dead columns) are applied by `qa/validate.py` from `qa/universal.py`.
"""

from typing import TYPE_CHECKING, Any

import pandas as pd

from domain import stats
from qa import odds
from qa.odds import OddsColumns
from qa.report import Report

if TYPE_CHECKING:
    from pandas.core.groupby.generic import DataFrameGroupBy

# Where the base league CSV keeps its three markets (`qa/odds.py` holds the checks).
BASE_ODDS = OddsColumns(
    home="home_win_initial_odds",
    draw="draw_initial_odds",
    away="away_win_initial_odds",
    ou_line="ou_line",
    over="over_odds",
    under="under_odds",
    ah_line="ah_line",
    ah_home="ah_home_odds",
    ah_away="ah_away_odds",
)


def validate(report: Report, base_df: pd.DataFrame) -> None:
    """Run every base-file check."""

    _check_round_row_counts(report, base_df)
    _check_round_index(report, base_df)
    _check_score_sanity(report, base_df)
    _check_derived_columns(report, base_df)
    _check_standings_positions(report, base_df)
    odds.check_all(report, base_df, BASE_ODDS)


def _rounds(base_df: pd.DataFrame) -> "DataFrameGroupBy[Any, Any]":
    """Group by the round's full key. Rounds restart at 1 in each stage, so `round` alone
    is not a key; `stage` is "" on pages without stage tabs."""

    keys = [c for c in ("stage", "round") if c in base_df.columns]

    return base_df.groupby(keys, dropna=False)


def _round_label(key: Any) -> str:
    """Readable name for a groupby key, hiding the empty `stage` single-table leagues use."""

    parts = key if isinstance(key, tuple) else (key,)
    stage, number = (parts[0], parts[-1]) if len(parts) > 1 else ("", parts[0])
    prefix = "" if pd.isna(stage) or not str(stage).strip() else f"{stage} "

    return f"{prefix}round {number}"


def _check_round_row_counts(report: Report, base_df: pd.DataFrame) -> None:
    """No round holds more rows than its `matches_in_round` (a click that did not re-render
    scrapes a round twice); the median round size would misfire on split and playoff formats.
    A round with fewer rows is partly played, and `_check_round_index` reports it.
    """

    if "matches_in_round" not in base_df.columns:
        return

    overfull = {
        _round_label(key): (len(round_df), int(round_df["matches_in_round"].iloc[0]))
        for key, round_df in _rounds(base_df)
        if len(round_df) > int(round_df["matches_in_round"].iloc[0])
    }
    report.check(not overfull, f"rounds with more rows than scheduled matches: {overfull}")


def _check_round_index(report: Report, base_df: pd.DataFrame) -> None:
    """`match_index_in_round` orders each round by kickoff, in four checks of rising strength
    (checks 1-4 below). An index of 0 means the old scraper could not place the match. Gaps
    in 1..N are allowed: a partly played round lacks its unplayed matches.
    """

    if "match_index_in_round" not in base_df.columns or base_df.empty:
        return

    dates = pd.to_datetime(base_df["date"], errors="coerce")
    unparseable = int(dates.isna().sum())
    report.check(unparseable == 0, f"{unparseable} rows with an unparseable date (they sort last)")

    partial: dict[str, str] = {}
    for key, round_df in _rounds(base_df.assign(_dt=dates)):
        label = _round_label(key)
        total = _round_size(report, label, round_df)
        if total is None:
            continue

        _check_index_range(report, label, round_df["match_index_in_round"], total)
        ordered_df = round_df.sort_values(["_dt", "home_team_name", "away_team_name"])
        _check_index_order(report, label, ordered_df)
        _check_tied_kickoff_blocks(report, label, ordered_df)

        if len(round_df) < total:
            partial[label] = f"{len(round_df)}/{total}"

    if partial:
        print(f"    (info) partially-played rounds (rows/scheduled): {partial}")


def _round_size(report: Report, label: str, round_df: pd.DataFrame) -> int | None:
    """Check 1: `matches_in_round` is constant within the round, and return it.

    None means the round disagrees with itself, so the remaining checks have no
    trustworthy denominator to run against.
    """

    sizes = round_df["matches_in_round"].unique()
    if len(sizes) != 1:
        report.fail(f"{label}: matches_in_round is not constant ({sizes.tolist()})")
        return None

    return int(sizes[0])


def _check_index_range(
    report: Report, label: str, match_index: "pd.Series[Any]", total: int
) -> None:
    """Check 2: indices are unique and lie in 1..matches_in_round."""

    if match_index.duplicated().any():
        report.fail(f"{label}: duplicate match_index_in_round")

    out_of_range = match_index[(match_index < 1) | (match_index > total)]
    if len(out_of_range):
        report.fail(f"{label}: {len(out_of_range)} index outside 1..{total}")


def _check_index_order(report: Report, label: str, ordered_df: pd.DataFrame) -> None:
    """Check 3 — the real test: (kickoff, home, away) order reproduces ascending index."""

    if not ordered_df["match_index_in_round"].is_monotonic_increasing:
        report.fail(f"{label}: index disagrees with (kickoff, home, away) order")


def _check_tied_kickoff_blocks(report: Report, label: str, ordered_df: pd.DataFrame) -> None:
    """Check 4: matches sharing a kickoff occupy a contiguous index block.

    Follows from sorting on kickoff first, and cross-checks the stored index against
    the tie structure `features/engine.py:round_position` derives independently.
    """

    for kickoff, tied_df in ordered_df.groupby("_dt", dropna=False):
        span = tied_df["match_index_in_round"]
        if len(tied_df) > 1 and int(span.max()) - int(span.min()) + 1 != len(tied_df):
            report.fail(
                f"{label}: matches at {kickoff} do not occupy a contiguous "
                f"index block ({sorted(span.tolist())})"
            )


def _check_score_sanity(report: Report, base_df: pd.DataFrame) -> None:
    """Half-time goals never exceed full-time goals, and no score is negative."""

    impossible_df = base_df[
        (base_df["ht_home_goals"] > base_df["ft_home_goals"])
        | (base_df["ht_away_goals"] > base_df["ft_away_goals"])
        | (base_df["ht_home_goals"] < 0)
        | (base_df["ht_away_goals"] < 0)
    ]
    report.check(impossible_df.empty, f"{len(impossible_df)} rows with impossible HT/FT scores")


def _row_is_comeback(row: "pd.Series[Any]") -> bool:
    """Whether the row's HT and FT scores make a comeback, by `domain/stats.py`."""

    return stats.is_comeback(
        row.ht_home_goals, row.ht_away_goals, row.ft_home_goals, row.ft_away_goals
    )


def _check_derived_columns(report: Report, base_df: pd.DataFrame) -> None:
    """Stored derived columns still agree with the raw scores. They are recomputed with the
    `domain/stats.py` functions that wrote them, so only damage between write and read (a
    shifted column, a dtype change) fails here; nothing else would notice it.
    """

    bad_total_df = base_df[
        base_df["total_goals"] != base_df["ft_home_goals"] + base_df["ft_away_goals"]
    ]
    report.check(bad_total_df.empty, f"{len(bad_total_df)} rows where total_goals != FT sum")

    recomputed_comeback = base_df.apply(_row_is_comeback, axis=1)
    mismatch_df = base_df[base_df["is_comeback"] != recomputed_comeback]
    report.check(
        mismatch_df.empty, f"{len(mismatch_df)} rows where is_comeback disagrees with raw scores"
    )

    is_seven_plus = base_df["total_goals"] >= stats.SEVEN_PLUS_GOALS
    mismatch_7plus_df = base_df[base_df["is_seven_or_more_goals"] != is_seven_plus]
    report.check(
        mismatch_7plus_df.empty,
        f"{len(mismatch_7plus_df)} rows where is_seven_or_more_goals disagrees with total_goals",
    )


def _check_standings_positions(report: Report, base_df: pd.DataFrame) -> None:
    """Positions fall within the league's actual team count.

    Catches the standings dropdown failing to sync to the scraped round, or a rank read
    from the wrong element.
    """

    num_teams = len(set(base_df["home_team_id"]) | set(base_df["away_team_id"]))
    positions_df = base_df[["home_team_position", "away_team_position"]].dropna()
    out_of_range_df = positions_df[
        (positions_df < 1).any(axis=1) | (positions_df > num_teams).any(axis=1)
    ]

    report.check(
        out_of_range_df.empty,
        f"{len(out_of_range_df)} rows with a standings position outside 1..{num_teams}",
    )
