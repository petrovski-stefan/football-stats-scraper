"""Test data shared across the test packages, and the Hypothesis settings every test runs with."""

import math
from itertools import product

import pandas as pd
import pytest
from hypothesis import settings

from analysis.methods import shin

# Hypothesis tries the same cases on every run until Hypothesis, Python or the test changes, so
# the same code gives the same result, as with every other gate. No example database: a failure
# is not saved to `.hypothesis/` and replayed later. No deadline: a slow case on a busy machine
# is not a failure.
settings.register_profile("fixed", derandomize=True, database=None, deadline=None)
settings.load_profile("fixed")


@pytest.fixture
def score_grid() -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Every reachable HT -> FT pair with up to 4 goals per side.

    A side never has fewer goals at full time than at half time.
    """

    grid: list[tuple[tuple[int, int], tuple[int, int]]] = []
    for ht_home, ht_away, ft_home, ft_away in product(range(5), repeat=4):
        is_reachable = ft_home >= ht_home and ft_away >= ht_away
        if is_reachable:
            grid.append(((ht_home, ht_away), (ft_home, ft_away)))

    return grid


@pytest.fixture
def toy_matches_df() -> pd.DataFrame:
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

    matches_df = pd.DataFrame(rows, columns=columns)
    matches_df.insert(0, "match_id", [f"m{i}" for i in range(1, len(matches_df) + 1)])

    # League 1: teams 11 and 12. League 2: teams 21, 22 and 23.
    matches_df["s1_home_team_id"] = [11, 12, 21, 22, 21]
    matches_df["s1_away_team_id"] = [12, 11, 22, 21, 23]
    matches_df["s1_home_team_name"] = matches_df["s1_home_team_id"].map(lambda team: f"t{team}")
    matches_df["s1_away_team_name"] = matches_df["s1_away_team_id"].map(lambda team: f"t{team}")

    inverse_df = 1.0 / matches_df[shin.ODDS]
    proportional_df = inverse_df.div(inverse_df.sum(axis=1), axis=0)
    for odds_column, column in zip(shin.ODDS, shin.PROPORTIONAL, strict=True):
        matches_df[column] = proportional_df[odds_column]

    return matches_df


@pytest.fixture
def toy_priced_matches_df(toy_matches_df: pd.DataFrame) -> pd.DataFrame:
    """The toy matches with half-time goals, an opening O/U market and the stage-2 labels.

    Half-time scores 1-0, 0-0, 0-0, 1-0 and 0-1 against full-time 2-0, 0-0, 0-1, 1-2 and
    1-1: the fourth match is an away comeback, by team 21 against team 22.
    """

    priced_df = toy_matches_df.copy()
    priced_df["s1_ht_home_goals"] = [1, 0, 0, 1, 0]
    priced_df["s1_ht_away_goals"] = [0, 0, 0, 0, 1]
    priced_df["s1_odds_ou_open_line"] = [2.5, 2.25, 2.0, 3.0, 2.5]
    priced_df["s1_odds_ou_open_over"] = [1.9, 2.0, 1.8, 2.1, 1.95]
    priced_df["s1_odds_ou_open_under"] = [1.9, 1.8, 2.0, 1.75, 1.85]

    inverse_over = 1.0 / priced_df["s1_odds_ou_open_over"]
    priced_df["s2_implied_over"] = inverse_over / (
        inverse_over + 1.0 / priced_df["s1_odds_ou_open_under"]
    )

    priced_df["s2_total_goals"] = priced_df["s1_ft_home_goals"] + priced_df["s1_ft_away_goals"]
    priced_df["s2_goals_1h"] = priced_df["s1_ht_home_goals"] + priced_df["s1_ht_away_goals"]
    priced_df["s2_goals_2h"] = priced_df["s2_total_goals"] - priced_df["s2_goals_1h"]

    priced_df["s2_is_comeback_home"] = [False] * 5
    priced_df["s2_is_comeback_away"] = [False, False, False, True, False]
    priced_df["s2_is_comeback"] = (
        priced_df["s2_is_comeback_home"] | priced_df["s2_is_comeback_away"]
    )
    priced_df["s2_ht_decisive"] = priced_df["s1_ht_home_goals"] != priced_df["s1_ht_away_goals"]

    return priced_df
