"""`qa/final_table.py`: the page's final table against the table rebuilt from results."""

import pandas as pd

from qa.final_table import check
from qa.report import Report


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
_SCHEDULE = _schedule(("", 1, 2, 2, 0), ("", 3, 4, 1, 1))
_PAGE = [
    _line(1, 1, (1, 1, 0, 0, 2, 3)),
    _line(3, 2, (1, 0, 1, 0, 0, 1)),
    _line(4, 3, (1, 0, 1, 0, 0, 1)),
    _line(2, 4, (1, 0, 0, 1, -2, 0)),
]


def _run(schedule: pd.DataFrame, page: list[dict[str, object]]) -> Report:
    report = Report("test")
    check(report, schedule, pd.DataFrame(page))
    return report


def test_an_equal_table_passes() -> None:
    assert _run(_SCHEDULE, _PAGE).ok


def test_tied_teams_may_appear_in_either_order() -> None:
    swapped = [_PAGE[0], {**_PAGE[1], "s1_rank": 3}, {**_PAGE[2], "s1_rank": 2}, _PAGE[3]]
    assert _run(_SCHEDULE, swapped).ok


def test_a_points_deduction_fails() -> None:
    deducted = [{**_PAGE[0], "s1_points": 0}, *_PAGE[1:]]
    report = _run(_SCHEDULE, deducted)
    assert not report.ok
    assert "Team 1" in report.issues[0]


def test_a_rank_outside_the_tied_block_fails() -> None:
    wrong = [{**_PAGE[0], "s1_rank": 2}, *_PAGE[1:]]
    assert not _run(_SCHEDULE, wrong).ok


def test_a_missing_match_shows_as_a_team_missing_from_the_page() -> None:
    report = _run(_schedule(*_SCHEDULE.itertuples(index=False), ("", 5, 6, 0, 0)), _PAGE)
    assert any("missing from the page" in issue for issue in report.issues)


def test_no_final_table_fails() -> None:
    report = Report("test")
    check(report, _SCHEDULE, pd.DataFrame())
    assert not report.ok


def test_each_stage_is_held_against_its_own_matches() -> None:
    schedule = _schedule(("Apertura", 1, 2, 1, 0), ("Clausura", 1, 2, 0, 1))
    page = [
        _line(1, 1, (1, 1, 0, 0, 1, 3), "Apertura"),
        _line(2, 2, (1, 0, 0, 1, -1, 0), "Apertura"),
        _line(2, 1, (1, 1, 0, 0, 1, 3), "Clausura"),
        _line(1, 2, (1, 0, 0, 1, -1, 0), "Clausura"),
    ]
    assert _run(schedule, page).ok
