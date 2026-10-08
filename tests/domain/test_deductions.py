"""`domain/deductions.py`: the declared points deductions, looked up by league-season.

The entries are read from `deductions.POINTS_DEDUCTIONS`, not restated here.
"""

from domain import deductions


def test_deducted_returns_the_league_seasons_entries() -> None:
    (league, season, team), points = next(iter(deductions.POINTS_DEDUCTIONS.items()))
    found = deductions.deducted(league, season)
    assert found[team] == points
    assert all((league, season, other) in deductions.POINTS_DEDUCTIONS for other in found)


def test_a_league_season_without_entries_has_none() -> None:
    assert deductions.deducted(0, "1900-1901") == {}


def test_every_entry_is_a_deduction() -> None:
    assert all(points < 0 for points in deductions.POINTS_DEDUCTIONS.values())
