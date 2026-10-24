"""`qa/final_table.py`: the page's final table against the table rebuilt from results."""

import pandas as pd
import pytest

from domain import deductions
from qa.final_table import check
from qa.report import Report

# No league in `domain/deductions.py` has id 0.
_LEAGUE, _SEASON = 0, "2025-2026"


def _schedule(*matches: tuple[str, int, int, int, int]) -> pd.DataFrame:
    return pd.DataFrame(
        matches,
        columns=[
            "s1_stage",
            "s1_home_team_id",
            "s1_away_team_id",
            "s1_ft_home_goals",
            "s1_ft_away_goals",
        ],
    )


def _line(team: int, rank: int, counts: tuple[int, ...], stage: str = "") -> dict[str, object]:
    played, won, drawn, lost, goal_diff, points = counts

    return {
        "season": _SEASON,
        "league_id": _LEAGUE,
        "stage": stage,
        "team_id": team,
        "s1_team_name": f"Team {team}",
        "s1_rank": rank,
        "s1_played": played,
        "s1_won": won,
        "s1_drawn": drawn,
        "s1_lost": lost,
        "s1_goal_diff": goal_diff,
        "s1_points": points,
    }


# Team 1 beat team 2 2-0; teams 3 and 4 drew 1-1.
_SCHEDULE_DF = _schedule(("", 1, 2, 2, 0), ("", 3, 4, 1, 1))
_PAGE = [
    _line(1, 1, (1, 1, 0, 0, 2, 3)),
    _line(3, 2, (1, 0, 1, 0, 0, 1)),
    _line(4, 3, (1, 0, 1, 0, 0, 1)),
    _line(2, 4, (1, 0, 0, 1, -2, 0)),
]


def _run(schedule_df: pd.DataFrame, page: list[dict[str, object]]) -> Report:
    report = Report("test")
    check(report, schedule_df, pd.DataFrame(page))
    return report


def test_an_equal_table_passes() -> None:
    assert _run(_SCHEDULE_DF, _PAGE).ok


def test_tied_teams_may_appear_in_either_order() -> None:
    swapped = [_PAGE[0], {**_PAGE[1], "s1_rank": 3}, {**_PAGE[2], "s1_rank": 2}, _PAGE[3]]
    assert _run(_SCHEDULE_DF, swapped).ok


def test_teams_level_on_points_may_appear_in_either_order() -> None:
    """The page may break a tie on points by its league's rule, not by goal difference."""
    schedule_df = _schedule(("", 1, 2, 3, 0), ("", 3, 4, 1, 0))
    page = [
        _line(3, 1, (1, 1, 0, 0, 1, 3)),
        _line(1, 2, (1, 1, 0, 0, 3, 3)),
        _line(4, 3, (1, 0, 0, 1, -1, 0)),
        _line(2, 4, (1, 0, 0, 1, -3, 0)),
    ]

    assert _run(schedule_df, page).ok


def test_a_points_deduction_fails() -> None:
    deducted = [{**_PAGE[0], "s1_points": 0}, *_PAGE[1:]]
    report = _run(_SCHEDULE_DF, deducted)
    assert not report.ok
    assert "Team 1" in report.issues[0]


def test_a_declared_deduction_passes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deductions, "POINTS_DEDUCTIONS", {(_LEAGUE, _SEASON, "", 1): -3})
    # Team 1 drops from 3 points to 0, below teams 3 and 4.
    page = [
        _line(3, 1, (1, 0, 1, 0, 0, 1)),
        _line(4, 2, (1, 0, 1, 0, 0, 1)),
        _line(1, 3, (1, 1, 0, 0, 2, 0)),
        _line(2, 4, (1, 0, 0, 1, -2, 0)),
    ]

    assert _run(_SCHEDULE_DF, page).ok


def test_a_deduction_declared_with_the_wrong_amount_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deductions, "POINTS_DEDUCTIONS", {(_LEAGUE, _SEASON, "", 1): -1})
    deducted = [{**_PAGE[0], "s1_points": 0}, *_PAGE[1:]]
    assert not _run(_SCHEDULE_DF, deducted).ok


def test_the_pages_own_total_is_what_the_page_is_held_to(monkeypatch: pytest.MonkeyPatch) -> None:
    key = (_LEAGUE, _SEASON, "", 1)
    monkeypatch.setattr(deductions, "POINTS_DEDUCTIONS", {key: -3})
    monkeypatch.setattr(deductions, "PAGE_TOTALS", {key: -1})

    # The page takes 1 of the 3 points off team 1, which stays top.
    partly = [{**_PAGE[0], "s1_points": 2}, *_PAGE[1:]]
    assert _run(_SCHEDULE_DF, partly).ok

    fully = [{**_PAGE[0], "s1_points": 0}, *_PAGE[1:]]
    assert not _run(_SCHEDULE_DF, fully).ok


def test_a_rank_outside_the_block_level_on_points_fails() -> None:
    wrong = [{**_PAGE[0], "s1_rank": 2}, *_PAGE[1:]]
    assert not _run(_SCHEDULE_DF, wrong).ok


def test_a_missing_match_shows_as_a_team_missing_from_the_page() -> None:
    report = _run(_schedule(*_SCHEDULE_DF.itertuples(index=False), ("", 5, 6, 0, 0)), _PAGE)
    assert any("missing from the page" in issue for issue in report.issues)


def test_no_final_table_fails() -> None:
    report = Report("test")
    check(report, _SCHEDULE_DF, pd.DataFrame())
    assert not report.ok


def test_a_stage_with_a_table_but_no_matches_fails() -> None:
    page = [*_PAGE, _line(1, 1, (1, 1, 0, 0, 2, 3), "Clausura")]
    issues = _run(_SCHEDULE_DF, page).issues
    assert "stage 'Clausura': a final table but no stored matches" in issues


def test_each_stage_is_held_against_its_own_matches() -> None:
    schedule_df = _schedule(("Apertura", 1, 2, 1, 0), ("Clausura", 1, 2, 0, 1))
    page = [
        _line(1, 1, (1, 1, 0, 0, 1, 3), "Apertura"),
        _line(2, 2, (1, 0, 0, 1, -1, 0), "Apertura"),
        _line(2, 1, (1, 1, 0, 0, 1, 3), "Clausura"),
        _line(1, 2, (1, 0, 0, 1, -1, 0), "Clausura"),
    ]

    assert _run(schedule_df, page).ok


def test_a_deduction_counts_only_in_its_own_stage(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(deductions, "POINTS_DEDUCTIONS", {(_LEAGUE, _SEASON, "Apertura", 1): -3})

    # Team 1 wins both stages; only its Apertura win is cancelled by the deduction.
    schedule_df = _schedule(("Apertura", 1, 2, 1, 0), ("Clausura", 1, 2, 1, 0))
    page = [
        _line(1, 1, (1, 1, 0, 0, 1, 0), "Apertura"),
        _line(2, 2, (1, 0, 0, 1, -1, 0), "Apertura"),
        _line(1, 1, (1, 1, 0, 0, 1, 3), "Clausura"),
        _line(2, 2, (1, 0, 0, 1, -1, 0), "Clausura"),
    ]

    assert _run(schedule_df, page).ok
