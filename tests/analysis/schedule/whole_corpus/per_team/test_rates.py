"""`analysis/schedule/whole_corpus/per_team/rates.py`: the team rows, the tests and the tables."""

from itertools import permutations, product

import numpy as np
import pandas as pd
import pytest

from analysis.schedule.whole_corpus.per_team import rates as runner


@pytest.fixture
def three_matches() -> pd.DataFrame:
    """A against B from 0-1 to 2-1 (A comes back, B loses a lead), B against A from 1-0 to
    1-0, and A against C from 0-0 to 1-1, in one league-season."""
    return pd.DataFrame(
        {
            "s1_home_team_id": [1, 2, 1],
            "s1_away_team_id": [2, 1, 3],
            "s1_home_team_name": ["A", "B", "A"],
            "s1_away_team_name": ["B", "A", "C"],
            "s1_league_id": [9, 9, 9],
            "s1_league_name": ["x", "x", "x"],
            "s1_season": ["2024", "2024", "2024"],
            "season_cohort": [2024, 2024, 2024],
            "s1_ht_home_goals": [0, 1, 0],
            "s1_ht_away_goals": [1, 0, 0],
            "s1_ft_home_goals": [2, 1, 1],
            "s1_ft_away_goals": [1, 0, 1],
        }
    )


def test_team_frame_gives_each_team_its_roles(three_matches: pd.DataFrame) -> None:
    frame = runner.team_frame(three_matches)
    assert len(frame) == 6
    a_rows = frame[frame["team"] == 1]
    assert a_rows["comes_back"].sum() == 1.0
    assert a_rows["comes_back_home"].sum() == 1.0
    assert a_rows["behind"].sum() == 2.0  # behind 0-1 at home, and 0-1 away to B
    b_rows = frame[frame["team"] == 2]
    assert b_rows["loses_lead"].sum() == 1.0
    assert b_rows["loses_lead_away"].sum() == 1.0
    assert b_rows["ahead"].sum() == 2.0
    assert frame["home"].sum() == 3.0
    assert (frame["home"] + frame["away"]).tolist() == [1.0] * 6
    assert set(frame[runner.UNIT]) == {"1 9", "2 9", "3 9"}
    for numerator, denominator, _, _ in runner.QUANTITIES:
        assert {numerator, denominator} <= set(frame.columns)


@pytest.fixture
def two_leagues() -> pd.DataFrame:
    """Two leagues of four teams; every pair meets home and away in each of two cohorts."""
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


def test_team_summary_tests_the_teams_around_their_league(two_leagues: pd.DataFrame) -> None:
    frame = runner.team_frame(two_leagues)
    quantity = ("goals_for", "one", "goals scored", "count")
    row, result = runner.team_summary(frame, quantity)
    assert row["df"] == 8.0 - 2.0  # 8 teams in 2 leagues
    assert row["repeat n"] == 8.0
    assert isinstance(row["p"], str)
    against = result.values["shrunk"] - result.values["owner_mean"]
    assert float(row["shrunk - league min"]) == pytest.approx(against.min())
    luck = runner.luck_row("goals scored", result)
    assert float(luck["luck min"]) <= float(luck["luck max"])


def test_top_teams_rank_by_the_distance_from_the_league(two_leagues: pd.DataFrame) -> None:
    frame = runner.team_frame(two_leagues)
    _, result = runner.team_summary(frame, ("goals_for", "one", "goals scored", "count"))
    table = runner.top_teams(frame, result, top=3)
    assert len(table) == 3
    distances = table["shrunk - league"].tolist()
    assert distances == sorted(distances, reverse=True)
    assert set(table.columns) >= {"team_name", "league_name", "rate", "league", "shrunk"}
