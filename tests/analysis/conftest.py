"""Toy data of the analysis tests. The toy matches of every test package are in
`tests/conftest.py`."""

from itertools import permutations, product

import numpy as np
import pandas as pd
import pytest


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


@pytest.fixture
def toy_rounds() -> pd.DataFrame:
    """Two leagues in two cohorts, 10 rounds of 8 random matches in each league-season, in
    the columns of the yardstick's frame that `card.ODDS_CARD` reads, with the keys of the
    levels: all, league, league-season (`cluster`) and round."""
    rng = np.random.default_rng(0)
    size = 4 * 80
    ht_decisive = rng.random(size) < 0.6

    out = pd.DataFrame(
        {
            "is_comeback": (rng.random(size) < 0.1) & ht_decisive,
            "ht_decisive": ht_decisive,
            "seven": rng.random(size) < 0.05,
            "goals": rng.poisson(2.7, size),
            "m_cb": 0.05,
            "m_ht_decisive": 0.6,
            "m_completion": 0.08 * ht_decisive,
            "m_seven": 0.04,
            "m_goals": rng.uniform(2.0, 3.4, size),
            "one": 1.0,
        }
    ).astype(float)

    out["all"] = "all"
    out["league"] = np.repeat([1, 2, 1, 2], 80)
    out["cluster"] = np.repeat(["1 2024", "2 2024", "1 2025", "2 2025"], 80)
    out["season_cohort"] = np.repeat([2024, 2024, 2025, 2025], 80)

    rounds = np.tile(np.repeat(np.arange(1, 11), 8), 4)
    out["round"] = out["cluster"] + " " + pd.Series(rounds).astype(str)

    return out
