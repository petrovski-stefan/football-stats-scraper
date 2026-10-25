"""`domain/stats.py`: the market-label kernel."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain import stats

Score = tuple[int, int]
# Decimal prices as a book could quote them.
_PRICES = st.floats(1.01, 1000.0)


@pytest.mark.parametrize(
    ("ht", "ft", "home", "away"),
    [
        ((0, 1), (2, 1), True, False),  # home trailed at HT, won
        ((1, 0), (1, 2), False, True),  # away trailed at HT, won
        ((0, 2), (3, 2), True, False),  # a two-goal deficit overturned
        ((0, 1), (1, 1), False, False),  # the trailer only drew
        ((0, 0), (2, 1), False, False),  # nobody trailed at HT
        ((1, 0), (2, 0), False, False),  # the HT leader stayed ahead
    ],
)
def test_a_comeback_is_a_half_time_loser_who_wins(
    ht: Score, ft: Score, home: bool, away: bool
) -> None:
    assert stats.is_comeback_home(*ht, *ft) is home
    assert stats.is_comeback_away(*ht, *ft) is away
    assert stats.is_comeback(*ht, *ft) is (home or away)


def test_no_score_is_a_comeback_for_both_sides(score_grid: list[tuple[Score, Score]]) -> None:
    for ht, ft in score_grid:
        home = stats.is_comeback_home(*ht, *ft)
        away = stats.is_comeback_away(*ht, *ft)
        assert not (home and away), (ht, ft)
        assert stats.is_comeback(*ht, *ft) is (home or away), (ht, ft)


@pytest.mark.parametrize(("home", "away", "result"), [(2, 1, "1"), (1, 1, "X"), (0, 3, "2")])
def test_one_x_two_gives_1_x_or_2(home: int, away: int, result: str) -> None:
    assert stats.one_x_two(home, away) == result


@pytest.mark.parametrize(
    ("goals_for", "goals_against", "result"), [(2, 1, "W"), (1, 1, "D"), (0, 3, "L")]
)
def test_team_result_gives_w_d_or_l_from_the_team_side(
    goals_for: int, goals_against: int, result: str
) -> None:
    assert stats.team_result(goals_for, goals_against) == result


@pytest.mark.parametrize(
    ("total", "line", "over"),
    [(3, 2.5, True), (2, 2.5, False), (7, 6.5, True), (6, 6.5, False)],
)
def test_is_over_means_more_goals_than_the_line(total: int, line: float, over: bool) -> None:
    assert stats.is_over(total, line) is over


def test_is_over_defaults_to_two_and_a_half() -> None:
    assert stats.is_over(3) is True
    assert stats.is_over(2) is False


@pytest.mark.parametrize(
    ("home", "away", "btts"), [(1, 1, True), (1, 0, False), (0, 2, False), (0, 0, False)]
)
def test_is_btts_needs_a_goal_from_each_side(home: int, away: int, btts: bool) -> None:
    assert stats.is_btts(home, away) is btts


@pytest.mark.parametrize(
    ("goals_for", "goals_against", "points"), [(2, 1, 3), (1, 1, 1), (0, 1, 0)]
)
def test_points_are_3_for_a_win_and_1_for_a_draw(
    goals_for: int, goals_against: int, points: int
) -> None:
    assert stats.points(goals_for, goals_against) == points


@pytest.mark.parametrize(("odds", "prob"), [(2.0, 0.5), (4.0, 0.25), (None, None), (0.0, None)])
def test_implied_prob_is_one_over_the_price_and_none_without_one(
    odds: float | None, prob: float | None
) -> None:
    assert stats.implied_prob(odds) == prob


@pytest.mark.parametrize(
    ("odds_for", "odds_against", "prob"),
    [
        (1.9, 1.9, 0.5),  # equal prices: the overround cancels to an even split
        (1.5, 3.0, 2 / 3),
        (None, 1.9, None),
        (1.9, 0.0, None),
    ],
)
def test_two_way_prob_cancels_the_overround_and_is_none_without_a_price(
    odds_for: float | None, odds_against: float | None, prob: float | None
) -> None:
    result = stats.two_way_prob(odds_for, odds_against)
    if prob is None:
        assert result is None
    else:
        assert result == pytest.approx(prob)


def test_vig_free_1x2_sums_to_one_and_keeps_the_order() -> None:
    probs = stats.vig_free_1x2(1.5, 4.0, 6.0)
    assert probs is not None
    assert sum(probs) == pytest.approx(1.0)
    assert probs[0] > probs[1] > probs[2]


@given(_PRICES, _PRICES, _PRICES)
def test_any_three_prices_give_three_chances_that_sum_to_one(
    home: float, draw: float, away: float
) -> None:
    chances = stats.vig_free_1x2(home, draw, away)
    assert chances is not None
    assert sum(chances) == pytest.approx(1.0)
    assert all(0 < chance < 1 for chance in chances)


@pytest.mark.parametrize("prices", [(None, 3.0, 3.0), (2.0, 0.0, 3.0), (2.0, 3.0, None)])
def test_vig_free_1x2_needs_all_three_prices(prices: tuple[float | None, ...]) -> None:
    assert stats.vig_free_1x2(*prices) is None
