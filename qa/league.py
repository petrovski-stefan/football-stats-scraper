"""Checks specific to a base league CSV (`data/raw/<league>_<season>.csv`).

These need to know what the columns mean: what a round is, that half-time goals cannot
exceed full-time goals, what a plausible 1X2 overround looks like. Dataset-agnostic
checks (key, schema, dead columns) are applied by `qa/validate.py` from `qa/universal.py`.
"""

from typing import TYPE_CHECKING, Any

import pandas as pd

from domain import stats
from qa.report import Report

if TYPE_CHECKING:
    from pandas.core.groupby.generic import DataFrameGroupBy

# A 1X2 book below 1.00 is arbitrage-free-impossible; above 1.20 means the column is not
# 1X2 at all — most likely Asian Handicap, which is what the schedule page defaults to.
OVERROUND_MIN = 1.00
OVERROUND_MAX = 1.20


def validate(r: Report, df: pd.DataFrame) -> None:
    _check_round_row_counts(r, df)
    _check_round_index(r, df)
    _check_score_sanity(r, df)
    _check_derived_columns(r, df)
    _check_standings_positions(r, df)
    _check_odds(r, df)


def _rounds(df: pd.DataFrame) -> "DataFrameGroupBy[Any, Any]":
    """Group by the round's full key. `stage` is "" today but grouped formats are coming."""
    keys = [c for c in ("stage", "round") if c in df.columns]
    return df.groupby(keys, dropna=False)


def _round_label(key: Any) -> str:
    """Readable name for a groupby key, hiding the empty `stage` single-table leagues use."""
    parts = key if isinstance(key, tuple) else (key,)
    stage, number = (parts[0], parts[-1]) if len(parts) > 1 else ("", parts[0])
    prefix = "" if pd.isna(stage) or not str(stage).strip() else f"{stage} "
    return f"{prefix}round {number}"


def _check_round_row_counts(r: Report, df: pd.DataFrame) -> None:
    """No round holds more rows than it has scheduled matches.

    Catches a round whose click did not re-render, so the previous round's rows were
    scraped twice. Compared against `matches_in_round` rather than the median round
    size, which mis-fires wholesale on split/playoff formats
    (notes/PLAN_2026-07-25_environment_filter.md Phase 2). A round with *fewer* rows is
    legitimate — it is partially played — and is reported by `_check_round_index`.
    """
    if "matches_in_round" not in df.columns:
        return
    overfull = {
        _round_label(key): (len(g), int(g["matches_in_round"].iloc[0]))
        for key, g in _rounds(df)
        if len(g) > int(g["matches_in_round"].iloc[0])
    }
    r.check(not overfull, f"rounds with more rows than scheduled matches: {overfull}")


def _check_round_index(r: Report, df: pd.DataFrame) -> None:
    """`match_index_in_round` is a real ordering of the round by kickoff time.

    Four assertions in increasing strength, one per `_round_size` / `_check_index_range`
    / `_check_index_order` / `_check_tied_kickoff_blocks`. An index of 0 means the
    scraper could not place the match — see scrapers/schedule.py.

    Indices are NOT required to be contiguous 1..N: a partially-played round is missing
    its unplayed matches and so legitimately has gaps.
    """
    if "match_index_in_round" not in df.columns or df.empty:
        return

    dates = pd.to_datetime(df["date"], errors="coerce")
    unparseable = int(dates.isna().sum())
    r.check(unparseable == 0, f"{unparseable} rows with an unparseable date (they sort last)")

    partial: dict[str, str] = {}
    for key, g in _rounds(df.assign(_dt=dates)):
        label = _round_label(key)
        total = _round_size(r, label, g)
        if total is None:
            continue

        _check_index_range(r, label, g["match_index_in_round"], total)
        ordered = g.sort_values(["_dt", "home_team_name", "away_team_name"])
        _check_index_order(r, label, ordered)
        _check_tied_kickoff_blocks(r, label, ordered)

        if len(g) < total:
            partial[label] = f"{len(g)}/{total}"

    if partial:
        print(f"    (info) partially-played rounds (rows/scheduled): {partial}")


def _round_size(r: Report, label: str, g: pd.DataFrame) -> int | None:
    """Check 1: `matches_in_round` is constant within the round, and return it.

    None means the round disagrees with itself, so the remaining checks have no
    trustworthy denominator to run against.
    """
    sizes = g["matches_in_round"].unique()
    if len(sizes) != 1:
        r.check(False, f"{label}: matches_in_round is not constant ({sizes.tolist()})")
        return None
    return int(sizes[0])


def _check_index_range(r: Report, label: str, idx: "pd.Series[Any]", total: int) -> None:
    """Check 2: indices are unique and lie in 1..matches_in_round."""
    if idx.duplicated().any():
        r.check(False, f"{label}: duplicate match_index_in_round")
    out_of_range = idx[(idx < 1) | (idx > total)]
    if len(out_of_range):
        r.check(False, f"{label}: {len(out_of_range)} index outside 1..{total}")


def _check_index_order(r: Report, label: str, ordered: pd.DataFrame) -> None:
    """Check 3 — the real test: (kickoff, home, away) order reproduces ascending index."""
    if not ordered["match_index_in_round"].is_monotonic_increasing:
        r.check(False, f"{label}: index disagrees with (kickoff, home, away) order")


def _check_tied_kickoff_blocks(r: Report, label: str, ordered: pd.DataFrame) -> None:
    """Check 4: matches sharing a kickoff occupy a contiguous index block.

    Follows from sorting on kickoff first, and cross-checks the stored index against
    the tie structure `features/engine.py:round_position` derives independently.
    """
    for kickoff, tied in ordered.groupby("_dt", dropna=False):
        span = tied["match_index_in_round"]
        if len(tied) > 1 and int(span.max()) - int(span.min()) + 1 != len(tied):
            r.check(
                False,
                f"{label}: matches at {kickoff} do not occupy a contiguous "
                f"index block ({sorted(span.tolist())})",
            )


def _check_score_sanity(r: Report, df: pd.DataFrame) -> None:
    """Half-time goals never exceed full-time goals, and no score is negative."""
    impossible = df[
        (df["ht_home_goals"] > df["ft_home_goals"])
        | (df["ht_away_goals"] > df["ft_away_goals"])
        | (df["ht_home_goals"] < 0)
        | (df["ht_away_goals"] < 0)
    ]
    r.check(impossible.empty, f"{len(impossible)} rows with impossible HT/FT scores")


def _check_derived_columns(r: Report, df: pd.DataFrame) -> None:
    """Stored derived columns still agree with the raw scores they came from.

    Low yield by construction — these recompute with the same `domain/stats.py` functions
    that produced them, so they can only catch damage between write and read (a shifted
    column, a dtype coercion). Kept because that damage is silent otherwise.
    """
    bad_total = df[df["total_goals"] != df["ft_home_goals"] + df["ft_away_goals"]]
    r.check(bad_total.empty, f"{len(bad_total)} rows where total_goals != FT sum")

    recomputed_comeback = df.apply(
        lambda row: stats.is_comeback(
            row.ht_home_goals, row.ht_away_goals, row.ft_home_goals, row.ft_away_goals
        ),
        axis=1,
    )
    mismatch = df[df["is_comeback"] != recomputed_comeback]
    r.check(mismatch.empty, f"{len(mismatch)} rows where is_comeback disagrees with raw scores")

    mismatch_7plus = df[df["is_seven_or_more_goals"] != (df["total_goals"] >= 7)]
    r.check(
        mismatch_7plus.empty,
        f"{len(mismatch_7plus)} rows where is_seven_or_more_goals disagrees with total_goals",
    )


def _check_standings_positions(r: Report, df: pd.DataFrame) -> None:
    """Positions fall within the league's actual team count.

    Catches the standings dropdown failing to sync to the scraped round, or a rank read
    from the wrong element.
    """
    num_teams = len(set(df["home_team_id"]) | set(df["away_team_id"]))
    positions = df[["home_team_position", "away_team_position"]].dropna()
    out_of_range = positions[(positions < 1).any(axis=1) | (positions > num_teams).any(axis=1)]
    r.check(
        out_of_range.empty,
        f"{len(out_of_range)} rows with a standings position outside 1..{num_teams}",
    )


def _check_odds(r: Report, df: pd.DataFrame) -> None:
    """Odds are real prices and the column really is 1X2.

    A wholesale odds failure is caught upstream by the dead-column canary: the three
    odds columns are not declared optional, so an empty column fails there rather than
    being silently skipped here.
    """
    with_odds = df[df["has_odds"]]
    if not len(with_odds):
        return

    impossible = with_odds[
        (with_odds["home_win_initial_odds"] <= 1)
        | (with_odds["draw_initial_odds"] <= 1)
        | (with_odds["away_win_initial_odds"] <= 1)
    ]
    r.check(impossible.empty, f"{len(impossible)} rows with has_odds=True but an odd <= 1")

    overround = (
        1 / with_odds["home_win_initial_odds"]
        + 1 / with_odds["draw_initial_odds"]
        + 1 / with_odds["away_win_initial_odds"]
    )
    out_of_band = with_odds[(overround < OVERROUND_MIN) | (overround > OVERROUND_MAX)]
    r.check(
        out_of_band.empty,
        f"{len(out_of_band)} rows with an implausible overround "
        f"(outside {OVERROUND_MIN:.2f}-{OVERROUND_MAX:.2f}) — is the column really 1X2?",
    )
