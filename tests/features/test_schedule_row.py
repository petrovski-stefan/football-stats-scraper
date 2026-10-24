"""`features/schedule_row.py`: the stage-2 fields of one row."""

from typing import Any

import pytest

from domain import stats
from features.schedule_row import derive


def _row(ht: tuple[int, int], ft: tuple[int, int], **overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "match_id": "1",
        "s1_date": "2026-01-31 18:30+01:00",  # a Saturday in Berlin
        "s1_ht_home_goals": ht[0],
        "s1_ht_away_goals": ht[1],
        "s1_ft_home_goals": ft[0],
        "s1_ft_away_goals": ft[1],
        "s1_odds_1x2_open_home": 1.5,
        "s1_odds_1x2_open_draw": 4.0,
        "s1_odds_1x2_open_away": 6.0,
        "s1_odds_ou_open_line": 2.75,
        "s1_odds_ou_open_over": 1.9,
        "s1_odds_ou_open_under": 1.9,
        "s1_odds_ah_open_line": 0.75,
        "s1_odds_ah_open_home": 1.8,
        "s1_odds_ah_open_away": 2.0,
    }

    row.update(overrides)

    return row


def test_goal_fields() -> None:
    out = derive(_row((0, 2), (3, 2)))
    assert out["s2_total_goals"] == 5
    assert (out["s2_goals_1h"], out["s2_goals_2h"]) == (2, 3)
    assert (out["s2_home_2h_goals"], out["s2_away_2h_goals"]) == (3, 0)
    assert (out["s2_ht_result"], out["s2_ft_result"]) == ("2", "1")


def test_comeback_fields_agree_with_the_kernel(
    score_grid: list[tuple[tuple[int, int], tuple[int, int]]],
) -> None:
    for ht, ft in score_grid:
        out = derive(_row(ht, ft))
        assert out["s2_is_comeback"] is stats.is_comeback(*ht, *ft), (ht, ft)
        assert out["s2_is_comeback_home"] is stats.is_comeback_home(*ht, *ft), (ht, ft)
        assert out["s2_is_comeback_away"] is stats.is_comeback_away(*ht, *ft), (ht, ft)
        assert out["s2_ht_decisive"] is (ht[0] != ht[1]), (ht, ft)


def test_market_fields() -> None:
    out = derive(_row((0, 0), (0, 0)))
    total = out["s2_mkt_p_home"] + out["s2_mkt_p_draw"] + out["s2_mkt_p_away"]
    assert total == pytest.approx(1.0)
    assert out["s2_mkt_sup"] > 0  # the home side is the favourite
    assert out["s2_implied_over"] == pytest.approx(0.5)  # equal prices
    assert out["s2_has_odds"] and out["s2_has_ou_odds"] and out["s2_has_ah_odds"]


def test_a_missing_price_leaves_its_market_empty() -> None:
    out = derive(_row((0, 0), (0, 0), s1_odds_1x2_open_draw=float("nan")))
    assert out["s2_has_odds"] is False
    assert out["s2_mkt_p_home"] is None
    assert out["s2_mkt_sup"] is None
    # The other markets do not depend on the 1X2 prices.
    assert out["s2_has_ou_odds"] is True
