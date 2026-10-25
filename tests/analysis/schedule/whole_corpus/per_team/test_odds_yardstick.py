"""`analysis/schedule/whole_corpus/per_team/odds_yardstick.py`: the quantities and the
calibration by strength."""

import numpy as np
import pandas as pd
import pytest

from analysis import card
from analysis.methods import yardstick
from analysis.schedule.whole_corpus.per_team import odds_yardstick as runner

COARSE = np.round(np.arange(0.1, 4.01, 0.1), 2)


@pytest.fixture
def team_rows_df(toy_priced_matches_df: pd.DataFrame) -> pd.DataFrame:
    """The team rows of the four priced toy matches, with the yardstick's chances."""

    yardstick_df = yardstick.frame(toy_priced_matches_df, yardstick.build_grid(COARSE))

    return card.team_yardstick_rows(toy_priced_matches_df, yardstick_df)


def test_the_quantities_read_columns_of_the_team_rows(team_rows_df: pd.DataFrame) -> None:
    for observed, expected, _, _ in runner.QUANTITIES:
        assert {observed, expected} <= set(team_rows_df.columns), (observed, expected)


def test_calibration_has_the_calibrated_quantities_by_win_chance(
    team_rows_df: pd.DataFrame,
) -> None:
    calibration_df = runner.calibration(team_rows_df)
    assert set(calibration_df["quantity"]) == set(runner.CALIBRATED)
    assert calibration_df.groupby("win chance")["n"].first().sum() == len(team_rows_df)


def test_shuffle_table_tests_the_two_goal_counts(team_rows_df: pd.DataFrame) -> None:
    shuffle_table_df = runner.shuffle_table(team_rows_df)
    assert shuffle_table_df["quantity"].tolist() == list(runner.GOALS)
    assert {"Q", "df", "p", "shuffled mean", "tau/pooled"} <= set(shuffle_table_df.columns)
