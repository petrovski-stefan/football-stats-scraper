"""`domain/match.py`: the season and date parsers, and the market labels on `Match`.

The label tests go through `_labels` only. When the data refactor (IDEAS idea 2) moves the
labels out of the raw model, re-pointing that one helper re-runs every assert below against
the labels' new home, which is what makes these tests the refactor's safety net.
"""

from datetime import datetime
from typing import Any

import pytest

from domain import stats
from domain.match import Match, parse_match_datetime, round_sort_key, season_start_year

Score = tuple[int, int]


def _labels(ht: Score, ft: Score) -> dict[str, Any]:
    """The labels a match with these scores gets — the one place that knows where they live."""
    match = Match(
        season="2025-2026",
        league_id=1,
        league_name="test_league",
        stage="",
        round=1,
        match_id="1",
        date="2026-01-03 15:00",
        home_team_id=1,
        away_team_id=2,
        home_team_name="Home",
        away_team_name="Away",
        home_team_position=None,
        away_team_position=None,
        match_index_in_round=1,
        matches_in_round=1,
        ht_score=f"{ht[0]}-{ht[1]}",
        ft_score=f"{ft[0]} - {ft[1]}",
        ht_home_goals=ht[0],
        ht_away_goals=ht[1],
        ft_home_goals=ft[0],
        ft_away_goals=ft[1],
    )
    return match.model_dump()


# --- Season and date parsing --------------------------------------------------


@pytest.mark.parametrize(
    ("season", "start"),
    [
        ("2025-2026", 2025),
        ("2025", 2025),
        (" 2025 ", 2025),
        ("2025-26", None),
        ("2025/26", None),
        ("25-26", None),
        ("", None),
    ],
)
def test_season_start_year(season: str, start: int | None) -> None:
    assert season_start_year(season) == start


@pytest.mark.parametrize(
    ("raw", "parsed"),
    [
        ("2026-05-24 23:00", datetime(2026, 5, 24, 23, 0)),
        ("2026-05-24 23:00:15", datetime(2026, 5, 24, 23, 0, 15)),
        (" 2026-05-24 23:00 ", datetime(2026, 5, 24, 23, 0)),
        ("24/05/2026 23:00", None),
        ("", None),
    ],
)
def test_parse_match_datetime(raw: str, parsed: datetime | None) -> None:
    assert parse_match_datetime(raw) == parsed


def test_round_sort_key_orders_by_kickoff_then_team_names() -> None:
    rows = [
        ("not a date", "Alpha", "Beta"),
        ("2026-01-03 17:30", "Alpha", "Beta"),
        ("2026-01-03 15:00", "Delta", "Echo"),
        ("2026-01-03 15:00", "Bravo", "Zulu"),
        ("2026-01-03 15:00", "Bravo", "Charlie"),
    ]
    ordered = sorted(rows, key=lambda row: round_sort_key(*row))
    assert ordered == [
        ("2026-01-03 15:00", "Bravo", "Charlie"),
        ("2026-01-03 15:00", "Bravo", "Zulu"),
        ("2026-01-03 15:00", "Delta", "Echo"),
        ("2026-01-03 17:30", "Alpha", "Beta"),
        ("not a date", "Alpha", "Beta"),  # unparseable sorts last instead of raising
    ]


# --- Market labels on Match ---------------------------------------------------


def test_labels_for_a_home_comeback() -> None:
    labels = _labels((0, 1), (2, 1))
    assert labels["is_comeback"] is True
    assert labels["is_comeback_home"] is True
    assert labels["is_comeback_away"] is False
    assert (labels["ht_result"], labels["ft_result"], labels["ht_ft_combo"]) == ("2", "1", "2-1")
    assert labels["total_goals"] == 3
    assert (labels["goals_1h"], labels["goals_2h"]) == (1, 2)
    assert (labels["home_2h_goals"], labels["away_2h_goals"]) == (2, 0)
    assert labels["btts"] is True
    assert labels["over_25"] is True
    assert labels["is_seven_or_more_goals"] is False


@pytest.mark.parametrize(("ft", "seven_plus"), [((4, 3), True), ((3, 3), False), ((7, 0), True)])
def test_seven_or_more_goals_boundary(ft: Score, seven_plus: bool) -> None:
    assert _labels((0, 0), ft)["is_seven_or_more_goals"] is seven_plus


def test_labels_agree_with_the_kernel(score_grid: list[tuple[Score, Score]]) -> None:
    for ht, ft in score_grid:
        labels = _labels(ht, ft)
        assert labels["is_comeback"] is stats.is_comeback(*ht, *ft), (ht, ft)
        assert labels["is_comeback_home"] is stats.is_comeback_home(*ht, *ft), (ht, ft)
        assert labels["is_comeback_away"] is stats.is_comeback_away(*ht, *ft), (ht, ft)
        assert labels["ht_result"] == stats.one_x_two(*ht), (ht, ft)
        assert labels["ft_result"] == stats.one_x_two(*ft), (ht, ft)
        assert labels["btts"] is stats.is_btts(*ft), (ht, ft)
        assert labels["over_25"] is stats.is_over(sum(ft), 2.5), (ht, ft)
        assert labels["is_seven_or_more_goals"] is stats.is_over(sum(ft), 6.5), (ht, ft)
        assert labels["goals_1h"] + labels["goals_2h"] == labels["total_goals"], (ht, ft)
