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
def team_rows(toy_priced_matches: pd.DataFrame) -> pd.DataFrame:
    """The team rows of the four priced toy matches, with the yardstick's chances."""
    frame = yardstick.frame(toy_priced_matches, yardstick.build_grid(COARSE))
    return card.team_yardstick_rows(toy_priced_matches, frame)


def test_the_quantities_read_columns_of_the_team_rows(team_rows: pd.DataFrame) -> None:
    for observed, expected, _, _ in runner.QUANTITIES:
        assert {observed, expected} <= set(team_rows.columns)


def test_calibration_has_the_calibrated_quantities_by_win_chance(team_rows: pd.DataFrame) -> None:
    table = runner.calibration(team_rows)
    assert set(table["quantity"]) == set(runner.CALIBRATED)
    assert table.groupby("win chance")["n"].first().sum() == len(team_rows)
