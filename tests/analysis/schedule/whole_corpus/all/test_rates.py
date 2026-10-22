"""`analysis/schedule/whole_corpus/all/rates.py`: the card, the deficits and the goal totals."""

import pandas as pd
import pytest

from analysis import card
from analysis.schedule.whole_corpus.all import rates as runner


@pytest.fixture
def card_frame() -> pd.DataFrame:
    """Six matches in two league-seasons, in the shape `card_frame` gives.

    Half-time to full time: 0-1 to 2-1 (home comeback), 1-0 to 1-0, 0-0 to 1-1, 0-1 to 0-2,
    2-0 to 2-3 (away comeback) and 0-0 to 4-3. Each league-season has a home team and an
    away team behind at half-time.
    """
    frame = pd.DataFrame(
        {
            "is_comeback": [1, 0, 0, 0, 1, 0],
            "is_comeback_home": [1, 0, 0, 0, 0, 0],
            "is_comeback_away": [0, 0, 0, 0, 1, 0],
            "ht_decisive": [1, 1, 0, 1, 1, 0],
            "home_behind": [1, 0, 0, 1, 0, 0],
            "away_behind": [0, 1, 0, 0, 1, 0],
            "seven": [0, 0, 0, 0, 0, 1],
            "goals": [3, 1, 2, 2, 5, 7],
            "goals_1h": [1, 1, 0, 1, 2, 0],
            "goals_2h": [2, 0, 2, 1, 3, 7],
            "ht_deficit": [1, 1, 0, 1, 2, 0],
        }
    ).astype(float)

    frame["one"] = 1.0
    frame["cluster"] = ["a", "a", "a", "b", "b", "b"]

    return frame


def test_card_table_has_one_row_per_quantity_as_a_ratio_of_sums(card_frame: pd.DataFrame) -> None:
    table = runner.card_table(card_frame).set_index("quantity")

    assert list(table.index) == [label for _, _, label, _ in card.CARD]
    assert table.loc["comeback", "value"] == pytest.approx(2 / 6)
    assert table.loc["link 1: a team is behind at half-time", "value"] == pytest.approx(4 / 6)
    assert table.loc["link 2: the team behind wins", "value"] == pytest.approx(2 / 4)
    assert table.loc["home team behind wins", "value"] == pytest.approx(1 / 2)
    assert table.loc["7+ goals", "value"] == pytest.approx(1 / 6)
    assert table.loc["goals in the second half", "value"] == pytest.approx(15 / 6)
    assert (table["low"] <= table["value"]).all()
    assert (table["value"] <= table["high"]).all()


def test_by_deficit_gives_the_completion_of_each_band(card_frame: pd.DataFrame) -> None:
    table = runner.by_deficit(card_frame).set_index("deficit")
    assert list(table.index) == ["1", "2"]  # no half-time with a deficit of 3 or more
    assert table.loc["1", "half-times"] == 3.0
    assert table.loc["1", "completion"] == pytest.approx(1 / 3)
    assert table.loc["2", "completion"] == pytest.approx(1.0)
    assert table.loc["1", "share of matches"] == pytest.approx(3 / 6)


def test_goal_totals_share_the_large_totals_in_one_row() -> None:
    frame = pd.DataFrame({"goals": [0.0, 2.0, 2.0, 11.0, 13.0]})
    table = runner.goal_totals(frame)
    assert table["goals"].tolist() == ["0", "2", f"{runner.MANY_GOALS}+"]
    assert table["matches"].tolist() == [1, 2, 2]
    assert table["share"].sum() == pytest.approx(1.0)
