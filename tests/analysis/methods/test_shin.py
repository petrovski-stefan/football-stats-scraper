"""`analysis/methods/shin.py`: Shin's probabilities and z per match, and the scored frame."""

import math

import numpy as np
import pandas as pd
import pytest

from analysis.methods import shin


def test_probabilities_sum_to_one_and_z_is_not_negative() -> None:
    p_home, p_draw, p_away, z = shin.shin_row(1.5, 4.0, 6.0)
    assert p_home + p_draw + p_away == pytest.approx(1.0)
    assert z >= 0


def test_equal_prices_give_equal_probabilities() -> None:
    p_home, p_draw, p_away, _ = shin.shin_row(2.7, 2.7, 2.7)
    assert [p_home, p_draw, p_away] == pytest.approx([1 / 3, 1 / 3, 1 / 3])


def test_a_missing_price_gives_nan() -> None:
    assert all(math.isnan(value) for value in shin.shin_row(1.5, math.nan, 6.0))


def test_shin_frame_keeps_the_index(toy_matches: pd.DataFrame) -> None:
    matches = toy_matches.set_index(pd.Index([10, 20, 30, 40, 50]))
    out = shin.shin_frame(matches)
    assert out.index.tolist() == [10, 20, 30, 40, 50]
    assert out.columns.tolist() == [*shin.PROBS, "shin_z"]


def test_scored_drops_unpriced_matches_and_defines_the_gain(toy_matches: pd.DataFrame) -> None:
    frame = shin.scored(toy_matches)
    assert frame["match_id"].tolist() == ["m1", "m2", "m3", "m4"]
    assert np.allclose(frame["ll_gain"], frame["ll_prop"] - frame["ll_shin"])
    assert np.allclose(frame["brier_gain"], frame["brier_prop"] - frame["brier_shin"])
    assert frame["cluster"].tolist() == ["1 2024", "1 2025", "2 2024-2025", "2 2025-2026"]
    assert shin.sum_error(frame) < 1e-9


def test_outcome_rows_give_each_match_three_sides_and_one_hit(toy_matches: pd.DataFrame) -> None:
    frame = shin.scored(toy_matches)
    rows = shin.outcome_rows(frame)

    assert len(rows) == 3 * len(frame)
    assert rows["side"].tolist() == ["home"] * 4 + ["draw"] * 4 + ["away"] * 4
    assert int(rows["hit"].sum()) == len(frame)
    assert rows["price"].tolist()[:4] == frame[shin.ODDS[0]].tolist()
    assert rows["cluster"].tolist()[:4] == frame["cluster"].tolist()
