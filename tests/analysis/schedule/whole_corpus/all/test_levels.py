"""`analysis/schedule/whole_corpus/all/levels.py`: the share of the odds, and the tests of
each level."""

import numpy as np
import pandas as pd
import pytest

from analysis import card
from analysis.schedule.whole_corpus.all import levels as runner


def team_frame(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Two random team rows per toy match, in the columns of the team card, with four teams
    in each league-season."""

    rng = np.random.default_rng(1)
    size = 2 * len(matches_df)
    behind = rng.random(size) < 0.3
    team_rows_df = pd.DataFrame(
        {
            "comes_back": behind & (rng.random(size) < 0.1),
            "loses_lead": rng.random(size) < 0.03,
            "behind": behind,
            "goals_for": rng.poisson(1.35, size),
            "goals_against": rng.poisson(1.35, size),
            "m_comes_back": 0.025,
            "m_loses_lead": 0.025,
            "m_behind": 0.3,
            "m_wins_from_behind": 0.08 * behind,
            "m_goals_for": 1.35,
            "m_goals_against": 1.35,
            "one": 1.0,
        }
    ).astype(float)

    team_rows_df[runner.LEAGUE_SEASON] = np.tile(matches_df[runner.LEAGUE_SEASON].to_numpy(), 2)
    team_rows_df["season_cohort"] = np.tile(matches_df["season_cohort"].to_numpy(), 2)
    teams = pd.Series(np.arange(size) % 4).astype(str)
    team_rows_df[runner.TEAM_SEASON] = team_rows_df[runner.LEAGUE_SEASON] + " " + teams

    return team_rows_df


@pytest.fixture
def rows(toy_rounds_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """The toy rounds at the match level and at the team level, by level name."""

    return {"match": toy_rounds_df, "team": team_frame(toy_rounds_df)}


def test_odds_share_is_one_for_a_perfect_fit_and_zero_for_a_flat_one() -> None:
    level_rows_df = pd.DataFrame(
        {"goals": [1.0, 2.0, 3.0, 6.0], "exact": [0.5, 1.0, 1.5, 3.0], "flat": 2.0, "one": 1.0}
    )
    assert runner.odds_share(level_rows_df, "goals", "one", "exact") == pytest.approx(1.0)
    assert runner.odds_share(level_rows_df, "goals", "one", "flat") == pytest.approx(0.0)


def test_odds_share_counts_only_the_rows_with_a_denominator() -> None:
    level_rows_df = pd.DataFrame(
        {
            "won": [0.0, 1.0, 1.0, 0.0],
            "behind": [1.0, 1.0, 0.0, 0.0],
            "chance": [0.0, 1.0, 0.7, 0.2],
        }
    )

    assert runner.odds_share(level_rows_df, "won", "behind", "chance") == pytest.approx(1.0)


def test_odds_shares_cover_both_cards(rows: dict[str, pd.DataFrame]) -> None:
    odds_shares_df = runner.odds_shares(rows)
    assert len(odds_shares_df) == len(card.ODDS_CARD) + len(runner.TEAM_QUANTITIES)
    link_2_df = odds_shares_df[odds_shares_df["quantity"] == card.ODDS_CARD[2].label]
    assert float(link_2_df["counted"].iloc[0]) == rows["match"]["ht_decisive"].sum()


def test_level_tests_give_one_row_per_level_quantity_and_reading(
    rows: dict[str, pd.DataFrame],
) -> None:
    every = tuple(level for level, *_ in runner.LEVELS)
    level_tests_df = runner.level_tests(rows, every, draws=2)

    per_reading = 3 * len(card.ODDS_CARD) + len(runner.TEAM_QUANTITIES)
    assert len(level_tests_df) == len(runner.READINGS) * per_reading
    assert level_tests_df.groupby("level")["parts"].max().to_dict() == {
        "league": 2.0,
        "league-season": 4.0,
        "round": 40.0,
        "team-season": 16.0,
    }


def test_level_tests_in_a_cohort_read_the_odds_of_the_chosen_levels(
    rows: dict[str, pd.DataFrame],
) -> None:
    level_tests_df = runner.level_tests(rows, runner.COHORT_LEVELS, readings=("odds",), draws=2)
    assert set(level_tests_df["level"]) == set(runner.COHORT_LEVELS)
    assert set(level_tests_df["reading"]) == {"odds"}
