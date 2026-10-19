"""`analysis/schedule/whole_corpus/per_team/odds_yardstick.py`: the team chances and the
calibration by strength."""

import numpy as np
import pandas as pd
import pytest

from analysis.methods import yardstick
from analysis.schedule.whole_corpus.per_team import odds_yardstick as runner

COARSE = np.round(np.arange(0.1, 4.01, 0.1), 2)


@pytest.fixture
def team_rows(toy_priced_matches: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The team rows of the four priced toy matches, and the yardstick frame they come from."""
    frame = yardstick.frame(toy_priced_matches, yardstick.build_grid(COARSE))
    return runner.team_yardstick_rows(toy_priced_matches, frame), frame


def test_each_team_gets_the_chances_of_its_own_side(
    team_rows: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    rows, frame = team_rows
    assert len(rows) == 2 * len(frame)
    home, away = rows[rows["home"] == 1.0], rows[rows["home"] == 0.0]
    assert home["m_comes_back"].tolist() == pytest.approx(frame["m_cb_home"].tolist())
    assert away["m_comes_back"].tolist() == pytest.approx(frame["m_cb_away"].tolist())
    assert home["m_loses_lead"].tolist() == pytest.approx(frame["m_cb_away"].tolist())
    assert away["m_ahead"].tolist() == pytest.approx(frame["m_home_behind"].tolist())
    assert home["m_goals_against"].tolist() == pytest.approx(frame["lam_away"].tolist())
    assert home["win_chance"].tolist() == pytest.approx(frame["shin_p_home"].tolist())


def test_the_completion_counts_only_from_the_right_half_time_state(
    team_rows: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    rows, _ = team_rows
    assert (rows.loc[rows["behind"] == 0.0, "m_wins_from_behind"] == 0.0).all()
    assert (rows.loc[rows["ahead"] == 0.0, "m_loses_from_ahead"] == 0.0).all()
    behind = rows[rows["behind"] == 1.0]
    assert behind["m_wins_from_behind"].tolist() == pytest.approx(behind["m_completion"].tolist())
    for observed, expected, _, _ in runner.QUANTITIES:
        assert {observed, expected} <= set(rows.columns)


def test_calibration_has_the_calibrated_quantities_by_win_chance(
    team_rows: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    rows, _ = team_rows
    table = runner.calibration(rows)
    assert set(table["quantity"]) == set(runner.CALIBRATED)
    assert table.groupby("win chance")["n"].first().sum() == len(rows)
