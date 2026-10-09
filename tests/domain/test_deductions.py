"""`domain/deductions.py`: the declared points deductions, looked up by league-season stage.

The entries are read from `deductions.POINTS_DEDUCTIONS`, not restated here.
"""

from domain import deductions


def test_deducted_returns_the_stages_entries() -> None:
    (league, season, stage, team), points = next(iter(deductions.POINTS_DEDUCTIONS.items()))
    found = deductions.deducted(league, season, stage)
    assert found[team] == points
    assert all((league, season, stage, other) in deductions.POINTS_DEDUCTIONS for other in found)


def test_another_stage_of_the_same_season_has_none_of_them() -> None:
    (league, season, stage, team), _ = next(iter(deductions.POINTS_DEDUCTIONS.items()))
    assert team not in deductions.deducted(league, season, f"not {stage}")


def test_a_league_season_without_entries_has_none() -> None:
    assert deductions.deducted(0, "1900-1901", "League") == {}


def test_every_entry_is_a_deduction() -> None:
    assert all(points < 0 for points in deductions.POINTS_DEDUCTIONS.values())
