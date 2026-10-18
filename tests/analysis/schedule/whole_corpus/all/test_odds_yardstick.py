"""`analysis/schedule/whole_corpus/all/odds_yardstick.py`: the bands, splits and tables."""

import pandas as pd
import pytest

from analysis.schedule.whole_corpus.all import odds_yardstick as runner


@pytest.fixture
def toy_frame() -> pd.DataFrame:
    """Four matches in two league-seasons, in the shape `yardstick.frame` gives."""
    return pd.DataFrame(
        {
            "cluster": ["a", "a", "b", "b"],
            "is_comeback": [1.0, 0.0, 1.0, 0.0],
            "m_cb": [0.5, 0.5, 0.25, 0.25],
            "m_completion": [0.4, 0.0, 0.3, 0.2],
            "ht_margin": [-1, 0, 2, -3],
            "fav_is_home": [True, True, True, False],
            "fav_p": [0.42, 0.48, 0.65, 0.75],
            "m_goals": [2.0, 2.6, 3.0, 3.6],
            "goals_home": [2.0, 0.0, 1.0, 3.0],
            "goals_away": [1.0, 0.0, 2.0, 1.0],
            "goals_home_1h": [0.0, 0.0, 1.0, 1.0],
            "goals_away_1h": [1.0, 0.0, 1.0, 0.0],
        }
    )


def test_banded_splits_the_rows_by_band(toy_frame: pd.DataFrame) -> None:
    table = runner.banded(toy_frame, "m_goals", (0.0, 2.8, 10.0), (("is_comeback", "m_cb", "cb"),))
    assert table["n"].tolist() == [2.0, 2.0]
    assert table["oe"].tolist() == pytest.approx([1.0, 2.0])


def test_trailer_splits_name_who_is_behind(toy_frame: pd.DataFrame) -> None:
    splits = runner.trailer_splits(toy_frame)
    assert splits["favourite behind"].tolist() == [True, False, False, False]
    assert splits["underdog behind"].tolist() == [False, False, True, True]
    assert splits["behind by 2 or more"].tolist() == [False, False, True, True]
    assert splits["away side behind"].tolist() == [False, False, True, False]


def test_excess_table_covers_every_split(toy_frame: pd.DataFrame) -> None:
    table = runner.excess_table(toy_frame)
    assert table["split"].tolist() == list(runner.trailer_splits(toy_frame))


def test_side_goals_follow_the_favourite(toy_frame: pd.DataFrame) -> None:
    sides = runner.side_goals(toy_frame)
    assert sides["fav"].tolist() == [2.0, 0.0, 1.0, 1.0]
    assert sides["dog_1h"].tolist() == [1.0, 0.0, 1.0, 1.0]


def test_pivot_counts_each_cell(toy_frame: pd.DataFrame) -> None:
    table = runner.pivot(toy_frame)
    assert table["n"].sum() == 4
    assert table["oe"].tolist() == pytest.approx((table["observed"] / table["expected"]).tolist())
