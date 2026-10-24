"""The whole corpus at stage 3, as every runner reads it.

Every runner prints `corpus_line` first, and its doc copies that line, so each claim names
the corpus it was measured on (`analysis/CLAUDE.md` §2).
"""

from datetime import date

import numpy as np
import pandas as pd

from domain import paths
from domain.schedule import season_start_year
from features.stage_io import read_stage_csv

LEAGUE_SEASON = ["s1_league_id", "s1_season"]

# The opening Asian handicap market: the line (S1.22), the home price and the away price.
AH = ["s1_odds_ah_open_line", "s1_odds_ah_open_home", "s1_odds_ah_open_away"]

# Outcome codes of the 1X2 market: the column order of every three-way probability array.
HOME, DRAW, AWAY = 0, 1, 2


def load() -> pd.DataFrame:
    """Every stage-3 schedule file, one row per finished match, plus `season_cohort`.

    `season_cohort` is the year a season began (`domain/schedule.py:season_start_year`), so
    a calendar-year 2025 season and a 2025-2026 season share a cohort.
    """

    frames = [read_stage_csv(path) for path in paths.schedule_csvs(3)]
    if not frames:
        raise FileNotFoundError(f"no stage-3 schedule files in {paths.stage_dir(3)}")

    corpus_df = pd.concat(frames, ignore_index=True)
    corpus_df["season_cohort"] = corpus_df["s1_season"].map(season_start_year)

    return corpus_df


def corpus_line(corpus_df: pd.DataFrame, day: date | None = None) -> str:
    """`Corpus 2026-10-16: 144 league-seasons, 36,238 matches`: the line each doc copies."""

    league_seasons = corpus_df.groupby(LEAGUE_SEASON).ngroups
    when = (day or date.today()).isoformat()

    return f"Corpus {when}: {league_seasons} league-seasons, {len(corpus_df):,} matches"


def round_key(matches_df: pd.DataFrame) -> "pd.Series[str]":
    """One key per round: the league, the season, the stage and the round of each match."""

    return (
        matches_df["s1_league_id"].astype(str)
        + " "
        + matches_df["s1_season"]
        + " "
        + matches_df["s1_stage"].fillna("")
        + " "
        + matches_df["s1_round"].astype(str)
    )


def outcome_1x2(matches_df: pd.DataFrame) -> np.ndarray:
    """`HOME`, `DRAW` or `AWAY` per match, from the full-time goals."""

    diff = matches_df["s1_ft_home_goals"].to_numpy() - matches_df["s1_ft_away_goals"].to_numpy()

    return np.where(diff > 0, HOME, np.where(diff == 0, DRAW, AWAY))
