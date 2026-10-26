"""`analysis/methods/shin.py`: Shin's probabilities and z per match, and the scored frame."""

import math

import numpy as np
import pandas as pd
import pytest

from analysis.methods import shin


def test_probabilities_sum_to_one_and_z_is_not_negative() -> None:
    p_home, p_draw, p_away, shin_z = shin.shin_row(1.5, 4.0, 6.0)
    assert p_home + p_draw + p_away == pytest.approx(1.0)
    assert shin_z >= 0


def test_equal_prices_give_equal_probabilities() -> None:
    p_home, p_draw, p_away, _ = shin.shin_row(2.7, 2.7, 2.7)
    assert [p_home, p_draw, p_away] == pytest.approx([1 / 3, 1 / 3, 1 / 3])


def test_a_missing_price_gives_nan() -> None:
    assert all(math.isnan(value) for value in shin.shin_row(1.5, math.nan, 6.0))


def test_shin_frame_keeps_the_index(toy_matches_df: pd.DataFrame) -> None:
    reindexed_df = toy_matches_df.set_index(pd.Index([10, 20, 30, 40, 50]))
    shin_df = shin.shin_frame(reindexed_df)
    assert shin_df.index.tolist() == [10, 20, 30, 40, 50]
    assert shin_df.columns.tolist() == [*shin.PROBABILITIES, "shin_z"]


def test_scored_drops_unpriced_matches_and_defines_the_gain(toy_matches_df: pd.DataFrame) -> None:
    scored_df = shin.scored(toy_matches_df)
    assert scored_df["match_id"].tolist() == ["m1", "m2", "m3", "m4"]
    assert np.allclose(scored_df["ll_gain"], scored_df["ll_prop"] - scored_df["ll_shin"])
    assert np.allclose(scored_df["brier_gain"], scored_df["brier_prop"] - scored_df["brier_shin"])
    assert scored_df["cluster"].tolist() == ["1 2024", "1 2025", "2 2024-2025", "2 2025-2026"]
    assert shin.sum_error(scored_df) < 1e-9


def test_outcome_rows_give_each_match_three_sides_and_one_hit(toy_matches_df: pd.DataFrame) -> None:
    scored_df = shin.scored(toy_matches_df)
    outcome_rows_df = shin.outcome_rows(scored_df)

    assert len(outcome_rows_df) == 3 * len(scored_df)
    assert outcome_rows_df["side"].tolist() == ["home"] * 4 + ["draw"] * 4 + ["away"] * 4
    assert int(outcome_rows_df["hit"].sum()) == len(scored_df)
    assert outcome_rows_df["price"].tolist()[:4] == scored_df[shin.ODDS[0]].tolist()
    assert outcome_rows_df["cluster"].tolist()[:4] == scored_df["cluster"].tolist()
