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
    """No round holds more rows than it has scheduled matches.

    Catches a round whose click did not re-render, so the previous round's rows were
    scraped twice. Compared against `matches_in_round` rather than the median round
    size, which mis-fires wholesale on split/playoff formats
    (notes/WORKING/IDEAS_2026-10-01.md idea 4, Phase 1). A round with *fewer* rows is
    legitimate — it is partially played — and is reported by `_check_round_index`.
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
    """`match_index_in_round` is a real ordering of the round by kickoff time.

    Four assertions in increasing strength, one per `_round_size` / `_check_index_range`
    / `_check_index_order` / `_check_tied_kickoff_blocks`. An index of 0 means the
    scraper could not place the match — see scrapers/schedule.py.

    Indices are NOT required to be contiguous 1..N: a partially-played round is missing
    its unplayed matches and so legitimately has gaps.
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
        report.check(False, f"{label}: matches_in_round is not constant ({sizes.tolist()})")
        return None
    return int(sizes[0])


def _check_index_range(report: Report, label: str, idx: "pd.Series[Any]", total: int) -> None:
    """Check 2: indices are unique and lie in 1..matches_in_round."""
    if idx.duplicated().any():
        report.check(False, f"{label}: duplicate match_index_in_round")

    out_of_range = idx[(idx < 1) | (idx > total)]
    if len(out_of_range):
        report.check(False, f"{label}: {len(out_of_range)} index outside 1..{total}")


def _check_index_order(report: Report, label: str, ordered_df: pd.DataFrame) -> None:
    """Check 3 — the real test: (kickoff, home, away) order reproduces ascending index."""
    if not ordered_df["match_index_in_round"].is_monotonic_increasing:
        report.check(False, f"{label}: index disagrees with (kickoff, home, away) order")


def _check_tied_kickoff_blocks(report: Report, label: str, ordered_df: pd.DataFrame) -> None:
    """Check 4: matches sharing a kickoff occupy a contiguous index block.

    Follows from sorting on kickoff first, and cross-checks the stored index against
    the tie structure `features/engine.py:round_position` derives independently.
    """
    for kickoff, tied_df in ordered_df.groupby("_dt", dropna=False):
        span = tied_df["match_index_in_round"]
        if len(tied_df) > 1 and int(span.max()) - int(span.min()) + 1 != len(tied_df):
            report.check(
                False,
                f"{label}: matches at {kickoff} do not occupy a contiguous "
                f"index block ({sorted(span.tolist())})",
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


def _check_derived_columns(report: Report, base_df: pd.DataFrame) -> None:
    """Stored derived columns still agree with the raw scores they came from.

    Low yield by construction — these recompute with the same `domain/stats.py` functions
    that produced them, so they can only catch damage between write and read (a shifted
    column, a dtype coercion). Kept because that damage is silent otherwise.
    """
    bad_total_df = base_df[
        base_df["total_goals"] != base_df["ft_home_goals"] + base_df["ft_away_goals"]
    ]
    report.check(bad_total_df.empty, f"{len(bad_total_df)} rows where total_goals != FT sum")

    recomputed_comeback = base_df.apply(
        lambda row: stats.is_comeback(
            row.ht_home_goals, row.ht_away_goals, row.ft_home_goals, row.ft_away_goals
        ),
        axis=1,
    )
    mismatch_df = base_df[base_df["is_comeback"] != recomputed_comeback]
    report.check(
        mismatch_df.empty, f"{len(mismatch_df)} rows where is_comeback disagrees with raw scores"
    )

    mismatch_7plus_df = base_df[base_df["is_seven_or_more_goals"] != (base_df["total_goals"] >= 7)]
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
