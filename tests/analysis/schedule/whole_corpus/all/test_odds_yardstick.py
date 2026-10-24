"""`analysis/schedule/whole_corpus/all/odds_yardstick.py`: the bands, splits and tables."""

import pandas as pd
import pytest

from analysis.schedule.whole_corpus.all import odds_yardstick as runner


@pytest.fixture
def toy_yardstick_df() -> pd.DataFrame:
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


def test_banded_splits_the_rows_by_band(toy_yardstick_df: pd.DataFrame) -> None:
    banded_df = runner.banded(
        toy_yardstick_df, "m_goals", (0.0, 2.8, 10.0), (("is_comeback", "m_cb", "cb"),)
    )
    assert banded_df["n"].tolist() == [2.0, 2.0]
    assert banded_df["oe"].tolist() == pytest.approx([1.0, 2.0])


def test_trailer_splits_name_who_is_behind(toy_yardstick_df: pd.DataFrame) -> None:
    splits = runner.trailer_splits(toy_yardstick_df)
    assert splits["favourite behind"].tolist() == [True, False, False, False]
    assert splits["underdog behind"].tolist() == [False, False, True, True]
    assert splits["behind by 2 or more"].tolist() == [False, False, True, True]
    assert splits["away side behind"].tolist() == [False, False, True, False]


def test_excess_table_covers_every_split(toy_yardstick_df: pd.DataFrame) -> None:
    excess_table_df = runner.excess_table(toy_yardstick_df)
    assert excess_table_df["split"].tolist() == list(runner.trailer_splits(toy_yardstick_df))


def test_side_goals_follow_the_favourite(toy_yardstick_df: pd.DataFrame) -> None:
    side_goals_df = runner.side_goals(toy_yardstick_df)
    assert side_goals_df["fav"].tolist() == [2.0, 0.0, 1.0, 1.0]
    assert side_goals_df["dog_1h"].tolist() == [1.0, 0.0, 1.0, 1.0]


def test_pivot_counts_each_cell(toy_yardstick_df: pd.DataFrame) -> None:
    pivot_df = runner.pivot(toy_yardstick_df)
    assert pivot_df["n"].sum() == 4
    assert pivot_df["oe"].tolist() == pytest.approx(
        (pivot_df["observed"] / pivot_df["expected"]).tolist()
    )
