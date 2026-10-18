"""`analysis/methods/yardstick.py`: the fair O/U price, the rate fit and the model's chances."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats as sps

from analysis.methods import yardstick

COARSE = np.round(np.arange(0.1, 4.01, 0.1), 2)


def test_fair_over_at_a_half_line_is_the_poisson_tail() -> None:
    total = np.array([2.5, 3.1])
    assert yardstick.fair_over(total, 2.5) == pytest.approx(sps.poisson.sf(2, total))


def test_fair_over_at_an_integer_line_leaves_out_the_push() -> None:
    total = np.array([2.4])
    win, loss = sps.poisson.sf(2, total), sps.poisson.cdf(1, total)
    assert yardstick.fair_over(total, 2.0) == pytest.approx(win / (win + loss))


def test_fair_over_at_a_quarter_line_splits_the_stake() -> None:
    total = np.array([2.4])
    win = sps.poisson.sf(2, total) * 2  # over 2.0 and over 2.5 both need 3 goals or more
    loss = sps.poisson.cdf(1, total) + sps.poisson.cdf(2, total)
    assert yardstick.fair_over(total, 2.25) == pytest.approx(win / (win + loss))


def test_grid_win_chances_are_valid_and_symmetric() -> None:
    grid = yardstick.build_grid(np.array([0.5, 1.0, 1.5]))
    assert np.all(grid.p_home + grid.p_away < 1.0)
    equal = grid.home == grid.away
    assert grid.p_home[equal] == pytest.approx(grid.p_away[equal])
    away_one = grid.away == 1.0
    assert np.all(np.diff(grid.p_home[away_one]) > 0)


def test_fit_recovers_the_rates_that_made_the_market() -> None:
    grid = yardstick.build_grid(COARSE)
    point = np.flatnonzero((grid.home == 1.4) & (grid.away == 1.0))
    over = yardstick.fair_over(np.array([2.4]), 2.5)
    lam_home, lam_away, error = yardstick.fit_rates(
        grid, grid.p_home[point], grid.p_away[point], over, np.array([2.5])
    )
    assert (lam_home[0], lam_away[0]) == pytest.approx((1.4, 1.0))
    assert error[0] == pytest.approx(0.0, abs=1e-12)


def test_equal_rates_give_equal_comeback_chances() -> None:
    model = yardstick.implied(np.array([1.2]), np.array([1.2]), 0.45)
    assert model["m_cb_home"][0] == pytest.approx(model["m_cb_away"][0])
    assert model["m_cb"][0] == pytest.approx(model["m_cb_home"][0] * 2)


def test_a_comeback_needs_a_decisive_half_time() -> None:
    model = yardstick.implied(np.array([0.6, 1.4, 2.5]), np.array([1.8, 1.1, 0.4]), 0.45)
    assert np.all((model["m_cb"] > 0) & (model["m_cb"] < model["m_ht_decisive"]))
    assert np.all(model["m_ht_decisive"] < 1.0)


def test_almost_no_first_half_goals_leave_almost_no_comebacks() -> None:
    model = yardstick.implied(np.array([1.5]), np.array([1.2]), 1e-6)
    assert model["m_cb"][0] < 1e-5


def test_score_and_total_chances_follow_the_poisson_formulas() -> None:
    home, away = np.array([1.3]), np.array([0.9])
    model = yardstick.implied(home, away, 0.45)
    assert model["m_00"][0] == pytest.approx(np.exp(-2.2))
    assert model["m_11"][0] == pytest.approx(1.3 * 0.9 * np.exp(-2.2))
    assert model["m_seven"][0] == pytest.approx(sps.poisson.sf(6, 2.2))
    assert model["m_goals_1h"][0] == pytest.approx(0.45 * 2.2)


def test_completion_from_each_half_time_score() -> None:
    home, away, share = np.full(3, 1.3), np.full(3, 1.1), 0.45
    h2, a2 = 0.55 * 1.3, 0.55 * 1.1
    out = yardstick.completion_given_ht(home, away, share, np.array([0, -1, 2]))
    assert out[0] == 0.0
    assert out[1] == pytest.approx(sps.skellam.sf(1, h2, a2))
    assert out[2] == pytest.approx(sps.skellam.cdf(-3, h2, a2))


def test_completions_over_every_half_time_score_add_up_to_the_comeback_chance() -> None:
    home, away, share = 1.3, 1.1, 0.45
    margins = np.arange(-yardstick.MAX_DEFICIT, yardstick.MAX_DEFICIT + 1)
    weights = sps.skellam.pmf(margins, share * home, share * away)
    completion = yardstick.completion_given_ht(
        np.full(len(margins), home), np.full(len(margins), away), share, margins
    )
    model = yardstick.implied(np.array([home]), np.array([away]), share)
    assert (weights * completion).sum() == pytest.approx(model["m_cb"][0])


def test_priced_keeps_the_matches_with_both_markets(toy_priced_matches: pd.DataFrame) -> None:
    assert yardstick.priced(toy_priced_matches)["match_id"].tolist() == ["m1", "m2", "m3", "m4"]


def test_first_half_share_is_one_number(toy_priced_matches: pd.DataFrame) -> None:
    assert yardstick.first_half_share(toy_priced_matches) == pytest.approx(3 / 8)


def test_frame_scores_every_priced_match(toy_priced_matches: pd.DataFrame) -> None:
    out = yardstick.frame(toy_priced_matches, yardstick.build_grid(COARSE))
    assert out["match_id"].tolist() == ["m1", "m2", "m3", "m4"]
    assert out["cluster"].tolist() == ["1 2024", "1 2025", "2 2024-2025", "2 2025-2026"]
    assert out["m_goals_1h"].to_numpy() == pytest.approx((2 / 6) * out["m_goals"].to_numpy())
    assert out.loc[out["ht_margin"] == 0, "m_completion"].tolist() == [0.0, 0.0]
    assert out["is_comeback"].tolist() == [0.0, 0.0, 0.0, 1.0]
    assert out["fav_p"].to_numpy() == pytest.approx(
        out[["shin_p_home", "shin_p_away"]].max(axis=1).to_numpy()
    )
    assert out["fav_is_home"].tolist() == [True, False, True, False]


def test_frame_can_remove_the_margin_proportionally(toy_priced_matches: pd.DataFrame) -> None:
    out = yardstick.frame(toy_priced_matches, yardstick.build_grid(COARSE), proportional=True)
    priced = yardstick.priced(toy_priced_matches)
    assert out["shin_p_home"].to_numpy() == pytest.approx(priced["s2_mkt_p_home"].to_numpy())
