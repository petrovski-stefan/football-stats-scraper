"""`domain/schedule.py`: the stage-1 models accept page values and nothing computed."""

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from domain.schedule import FinalTableRow, ScheduleRow, season_start_year


def _row(**overrides: Any) -> dict[str, Any]:
    row: dict[str, Any] = {
        "match_id": "1",
        "s1_season": "2025-2026",
        "s1_league_id": 1,
        "s1_league_name": "test_league",
        "s1_stage": "",
        "s1_round": 1,
        "s1_date": "2026-01-31 18:30+01:00",
        "s1_home_team_id": 1,
        "s1_away_team_id": 2,
        "s1_home_team_name": "Home",
        "s1_away_team_name": "Away",
        "s1_ht_home_goals": 0,
        "s1_ht_away_goals": 1,
        "s1_ft_home_goals": 2,
        "s1_ft_away_goals": 1,
    }

    row.update(overrides)

    return row


def test_a_row_without_odds_is_valid() -> None:
    model = ScheduleRow(**_row())
    assert model.s1_odds_1x2_open_home is None


def test_a_kickoff_without_offset_is_refused() -> None:
    with pytest.raises(ValidationError):
        ScheduleRow(**_row(s1_date="2026-02-01 01:30"))


def test_a_computed_field_is_refused() -> None:
    # Stage 1 holds page values only; a derived field belongs to stage 2.
    with pytest.raises(ValidationError):
        ScheduleRow(**_row(s2_total_goals=3))


def test_negative_goals_are_refused() -> None:
    with pytest.raises(ValidationError):
        ScheduleRow(**_row(s1_ft_home_goals=-1))


def test_final_table_row() -> None:
    line = FinalTableRow(
        season="2025",
        league_id=1,
        stage="",
        team_id=7,
        s1_team_name="Team",
        s1_rank=1,
        s1_played=30,
        s1_won=20,
        s1_drawn=5,
        s1_lost=5,
        s1_goal_diff=-3,
        s1_points=65,
    )

    assert line.s1_goal_diff == -3


# --- Season labels --------------------------------------------------------------------


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


@given(st.integers(1900, 2100), st.booleans())
def test_season_start_year_reads_any_year_in_both_label_forms(year: int, cross_year: bool) -> None:
    label = f"{year}-{year + 1}" if cross_year else str(year)
    assert season_start_year(label) == year
