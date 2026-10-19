"""Toy matches shared by the analysis tests."""

import math
from itertools import permutations, product

import numpy as np
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
    # League 1: teams 11 and 12. League 2: teams 21, 22 and 23.
    frame["s1_home_team_id"] = [11, 12, 21, 22, 21]
    frame["s1_away_team_id"] = [12, 11, 22, 21, 23]
    frame["s1_home_team_name"] = frame["s1_home_team_id"].map(lambda team: f"t{team}")
    frame["s1_away_team_name"] = frame["s1_away_team_id"].map(lambda team: f"t{team}")
    inverse = 1.0 / frame[shin.ODDS]
    proportional = inverse.div(inverse.sum(axis=1), axis=0)
    for odds_column, column in zip(shin.ODDS, shin.PROPORTIONAL, strict=True):
        frame[column] = proportional[odds_column]
    return frame


@pytest.fixture
def toy_priced_matches(toy_matches: pd.DataFrame) -> pd.DataFrame:
    """The toy matches with half-time goals, an opening O/U market and the stage-2 labels.

    Half-time scores 1-0, 0-0, 0-0, 1-0 and 0-1 against full-time 2-0, 0-0, 0-1, 1-2 and
    1-1: the fourth match is an away comeback, by team 21 against team 22.
    """
    frame = toy_matches.copy()
    frame["s1_ht_home_goals"] = [1, 0, 0, 1, 0]
    frame["s1_ht_away_goals"] = [0, 0, 0, 0, 1]
    frame["s1_odds_ou_open_line"] = [2.5, 2.25, 2.0, 3.0, 2.5]
    frame["s1_odds_ou_open_over"] = [1.9, 2.0, 1.8, 2.1, 1.95]
    frame["s1_odds_ou_open_under"] = [1.9, 1.8, 2.0, 1.75, 1.85]
    inverse_over = 1.0 / frame["s1_odds_ou_open_over"]
    frame["s2_implied_over"] = inverse_over / (inverse_over + 1.0 / frame["s1_odds_ou_open_under"])
    frame["s2_total_goals"] = frame["s1_ft_home_goals"] + frame["s1_ft_away_goals"]
    frame["s2_goals_1h"] = frame["s1_ht_home_goals"] + frame["s1_ht_away_goals"]
    frame["s2_goals_2h"] = frame["s2_total_goals"] - frame["s2_goals_1h"]
    frame["s2_is_comeback_home"] = [False] * 5
    frame["s2_is_comeback_away"] = [False, False, False, True, False]
    frame["s2_is_comeback"] = frame["s2_is_comeback_home"] | frame["s2_is_comeback_away"]
    frame["s2_ht_decisive"] = frame["s1_ht_home_goals"] != frame["s1_ht_away_goals"]
    return frame


@pytest.fixture
def round_robin() -> pd.DataFrame:
    """Two leagues of four teams; every pair meets home and away in each of two cohorts.

    Random half-time and full-time scores, the same on each run.
    """
    rng = np.random.default_rng(0)
    rows = []
    for league, cohort in product((1, 2), (2024, 2025)):
        for home, away in permutations([10 * league + t for t in range(4)], 2):
            ht = rng.integers(0, 3, size=2)
            ft = ht + rng.integers(0, 3, size=2)
            rows.append(
                {
                    "s1_home_team_id": home,
                    "s1_away_team_id": away,
                    "s1_home_team_name": f"t{home}",
                    "s1_away_team_name": f"t{away}",
                    "s1_league_id": league,
                    "s1_league_name": f"league {league}",
                    "s1_season": str(cohort),
                    "season_cohort": cohort,
                    "s1_ht_home_goals": ht[0],
                    "s1_ht_away_goals": ht[1],
                    "s1_ft_home_goals": ft[0],
                    "s1_ft_away_goals": ft[1],
                }
            )
    return pd.DataFrame(rows)
