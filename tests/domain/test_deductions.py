"""`domain/deductions.py`: the declared points deductions, looked up by league-season stage.

The entries are read from `deductions.POINTS_DEDUCTIONS` and `PAGE_TOTALS`, not restated here.
"""

import pytest

from domain import deductions

_KEY = (0, "1900-1901", "League", 1)


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


def test_on_page_takes_the_pages_own_figure_where_one_is_held(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    other = (*_KEY[:3], 2)
    monkeypatch.setattr(deductions, "POINTS_DEDUCTIONS", {_KEY: -9, other: -3})
    monkeypatch.setattr(deductions, "PAGE_TOTALS", {_KEY: -6})
    assert deductions.on_page(*_KEY[:3]) == {1: -6, 2: -3}
    assert deductions.deducted(*_KEY[:3]) == {1: -9, 2: -3}


def test_every_page_total_falls_short_of_a_declared_deduction() -> None:
    for key, points in deductions.PAGE_TOTALS.items():
        assert deductions.POINTS_DEDUCTIONS[key] < points <= 0
