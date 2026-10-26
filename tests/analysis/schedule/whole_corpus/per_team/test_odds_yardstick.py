"""`analysis/schedule/whole_corpus/per_team/odds_yardstick.py`: the quantities and the
calibration by strength."""

import numpy as np
import pandas as pd
import pytest

from analysis import card, units
from analysis.methods import yardstick
from analysis.schedule.whole_corpus.per_team import odds_yardstick as runner

COARSE = np.round(np.arange(0.1, 4.01, 0.1), 2)


@pytest.fixture
def team_rows_df(toy_priced_matches_df: pd.DataFrame) -> pd.DataFrame:
    """The team rows of the four priced toy matches, with the yardstick's chances."""

    yardstick_df = yardstick.frame(toy_priced_matches_df, yardstick.build_grid(COARSE))

    return card.team_yardstick_rows(toy_priced_matches_df, yardstick_df)


def test_the_quantities_read_columns_of_the_team_rows(team_rows_df: pd.DataFrame) -> None:
    for quantity in runner.QUANTITIES:
        assert {quantity.observed, quantity.expected} <= set(team_rows_df.columns), quantity


def test_calibration_has_the_calibrated_quantities_by_win_chance(
    team_rows_df: pd.DataFrame,
) -> None:
    calibration_df = runner.calibration(team_rows_df)
    assert set(calibration_df["quantity"]) == set(runner.CALIBRATED)
    assert calibration_df.groupby("win chance")["n"].first().sum() == len(team_rows_df)


@pytest.fixture
def role_rows_df() -> pd.DataFrame:
    """240 made-up team-matches of 8 teams in 2 leagues: each role happens with the chance
    0.3, and the yardstick expects 0.3."""

    rng = np.random.default_rng(0)
    role_rows_df = pd.DataFrame(
        {runner.UNIT: np.repeat(np.arange(8), 30), runner.LEAGUE: np.repeat([1, 2], 120)}
    )
    for quantity in runner.QUANTITIES:
        role_rows_df[quantity.observed] = (rng.random(len(role_rows_df)) < 0.3).astype(float)
        role_rows_df[quantity.expected] = 0.3

    return role_rows_df


def test_null_table_has_one_row_per_role_with_its_real_q(role_rows_df: pd.DataFrame) -> None:
    results = {}
    for quantity in runner.QUANTITIES:
        results[quantity.label] = units.within_tested(
            role_rows_df, runner.LEAGUE, runner.UNIT, quantity
        )

    null_table_df = runner.null_table(role_rows_df, results)

    assert null_table_df["quantity"].tolist() == list(runner.ROLES)
    real = [results[label].cochran_q for label in runner.ROLES]
    assert null_table_df["Q"].tolist() == pytest.approx(real)


def test_shuffle_table_tests_the_two_goal_counts(team_rows_df: pd.DataFrame) -> None:
    shuffle_table_df = runner.shuffle_table(team_rows_df)
    assert shuffle_table_df["quantity"].tolist() == list(runner.GOALS)
    assert {"Q", "df", "p", "shuffled mean", "tau/pooled"} <= set(shuffle_table_df.columns)
