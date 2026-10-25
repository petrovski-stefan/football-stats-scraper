"""`analysis/schedule/whole_corpus/per_league/rates.py`: the slices and the league table."""

import pandas as pd
import pytest

from analysis.schedule.whole_corpus.per_league import rates as runner


@pytest.fixture
def card_df() -> pd.DataFrame:
    """Eight matches of two leagues, each with two league-seasons, in the card's shape.

    League 1 keeps two stages; Apertura-B is a part of its Apertura. League 2 keeps one.
    """

    return pd.DataFrame(
        {
            "s1_league_id": [1, 1, 1, 1, 2, 2, 2, 2],
            "league": ["a", "a", "a", "a", "b", "b", "b", "b"],
            "cluster": ["1 x", "1 x", "1 y", "1 y", "2 x", "2 x", "2 y", "2 y"],
            "stage": ["Apertura", "Apertura-B", "Clausura", "Clausura", *["League"] * 4],
            "is_comeback": [1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 1.0, 0.0],
            "seven": [0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            "goals": [3.0, 7.0, 1.0, 3.0, 2.0, 0.0, 4.0, 8.0],
            "one": 1.0,
        }
    )


def test_quantity_finds_the_card_row() -> None:
    assert runner.quantity("comeback") == ("is_comeback", "one", "comeback", "event")
    with pytest.raises(StopIteration):
        runner.quantity("no such row")


def test_season_tests_give_one_row_per_sliced_quantity(card_df: pd.DataFrame) -> None:
    season_tests_df = runner.season_tests(card_df)
    assert season_tests_df["quantity"].tolist() == list(runner.SLICED)
    assert season_tests_df["df"].tolist() == [2.0, 2.0, 2.0]  # two leagues of two seasons each


def test_stage_table_puts_apertura_b_into_the_apertura(card_df: pd.DataFrame) -> None:
    with_stage_df = card_df[card_df["stage"].isin(runner.STAGES)]
    stage_table_df = runner.stage_table(with_stage_df).set_index(["stage", "quantity"])
    assert stage_table_df.loc[("Apertura", "comeback"), "matches"] == 2.0
    assert stage_table_df.loc[("Apertura", "7+ goals"), "value"] == pytest.approx(1 / 2)
    assert stage_table_df.loc[("Clausura", "goals per match"), "value"] == pytest.approx(4 / 2)


def test_league_table_ranks_by_the_shrunk_comeback_rate(card_df: pd.DataFrame) -> None:
    def values(shrunk: list[float]) -> pd.DataFrame:
        """Two leagues' observed, raw and shrunk values of one quantity."""

        return pd.DataFrame(
            {"observed": [1.0, 2.0], "value": [0.25, 0.5], "shrunk": shrunk},
            index=pd.Index([1, 2]),
        )

    by_label = {label: values([0.3, 0.4]) for label, _, _ in runner.TABLE_COLUMNS}
    by_label["comeback"] = values([0.2, 0.6])

    league_table_df = runner.league_table(card_df, by_label)

    assert league_table_df["league"].tolist() == ["b", "a"]
    assert league_table_df["shrunk"].tolist() == [0.6, 0.2]
    assert league_table_df["matches"].tolist() == [4, 4]
