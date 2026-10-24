"""`analysis/schedule/whole_corpus/per_league/odds_yardstick.py`: the own share and the tables.

The league values and the tests across the leagues are `analysis/units.py`, tested in
`tests/analysis/test_units.py`.
"""

import numpy as np
import pandas as pd
import pytest

from analysis.methods import yardstick
from analysis.schedule.whole_corpus.per_league import odds_yardstick as runner


@pytest.fixture
def toy_yardstick_df() -> pd.DataFrame:
    """Six matches in two leagues and both cohorts, in the shape `yardstick.frame` gives."""

    return pd.DataFrame(
        {
            "s1_league_id": [1, 1, 1, 2, 2, 2],
            "s1_league_name": ["A", "A", "A", "B", "B", "B"],
            "season_cohort": [2024, 2024, 2025, 2024, 2025, 2025],
            "goals": [3.0, 1.0, 2.0, 4.0, 0.0, 3.0],
            "goals_1h": [1.0, 1.0, 0.0, 2.0, 0.0, 1.0],
            "lam_home": [1.5, 1.2, 1.4, 1.8, 1.0, 1.3],
            "lam_away": [1.0, 0.8, 1.1, 1.2, 1.0, 1.2],
            "ht_margin": [-1, 1, 0, 1, 0, 1],
        }
    )


def test_with_own_share_uses_each_league_share(toy_yardstick_df: pd.DataFrame) -> None:
    with_own_share_df = runner.with_own_share(toy_yardstick_df)
    league = toy_yardstick_df["s1_league_id"] == 1
    share = 2 / 6  # league 1: 2 first-half goals of 6
    lam_home, lam_away = toy_yardstick_df["lam_home"][league], toy_yardstick_df["lam_away"][league]
    implied_df = yardstick.implied(lam_home.to_numpy(), lam_away.to_numpy(), share)
    assert with_own_share_df["m_cb"][league].to_numpy() == pytest.approx(
        implied_df["m_cb"].to_numpy()
    )
    completion = yardstick.completion_given_ht(
        lam_home.to_numpy(),
        lam_away.to_numpy(),
        share,
        toy_yardstick_df["ht_margin"][league].to_numpy(),
    )
    assert with_own_share_df["m_completion"][league].to_numpy() == pytest.approx(completion)


def test_league_table_is_in_the_order_of_the_names(toy_yardstick_df: pd.DataFrame) -> None:
    values = {"x": pd.DataFrame({"value": [0.9, 1.1]}, index=pd.Index([2, 1]))}
    league_table_df = runner.league_table(toy_yardstick_df, values, (("x", "value", "x O/E"),))
    assert league_table_df["league"].tolist() == ["A", "B"]
    assert league_table_df["matches"].tolist() == [3, 3]
    assert league_table_df["x O/E"].tolist() == [1.1, 0.9]
    assert np.all(league_table_df.columns == ["league", "matches", "x O/E"])
