"""Toy matches shared by the analysis tests."""

import math

import pandas as pd
import pytest

from analysis.methods import shin


@pytest.fixture
def toy_matches() -> pd.DataFrame:
    """Five matches in two leagues and two season cohorts; the last has no draw price."""
    rows = [
        # league, name, season, cohort, home, draw, away odds, FT home, FT away goals
        (1, "A", "2024", 2024, 1.5, 4.0, 6.0, 2, 0),
        (1, "A", "2025", 2025, 2.7, 3.2, 2.6, 0, 0),
        (2, "B", "2024-2025", 2024, 1.25, 6.0, 11.0, 0, 1),
        (2, "B", "2025-2026", 2025, 3.0, 3.3, 2.4, 1, 2),
        (2, "B", "2025-2026", 2025, 2.0, math.nan, 3.0, 1, 1),
    ]
    columns = [
        "s1_league_id",
        "s1_league_name",
        "s1_season",
        "season_cohort",
        *shin.ODDS,
        "s1_ft_home_goals",
        "s1_ft_away_goals",
    ]
    frame = pd.DataFrame(rows, columns=columns)
    frame.insert(0, "match_id", [f"m{i}" for i in range(1, len(frame) + 1)])
    inverse = 1.0 / frame[shin.ODDS]
    proportional = inverse.div(inverse.sum(axis=1), axis=0)
    for odds_column, column in zip(shin.ODDS, shin.PROPORTIONAL, strict=True):
        frame[column] = proportional[odds_column]
    return frame
