"""`qa/odds.py`: the odds checks, on any table given its column names."""

from collections.abc import Callable

import pandas as pd
import pytest

from qa import odds
from qa.odds import LineBand, OddsColumns, check_all, check_coverage, check_whole_markets
from qa.report import Report

_COLUMNS = OddsColumns("h", "d", "a", "ou", "over", "under", "ah", "ah_h", "ah_a")
# Two bands of our own, so the line-size tests do not depend on the project's limits.
_BANDS = (
    LineBand(favourite_from=1.00, largest_ah=6.0, largest_ou=7.0),
    LineBand(favourite_from=1.20, largest_ah=3.0, largest_ou=5.0),
)


def _row(**overrides: float | None) -> dict[str, float | None]:
    row: dict[str, float | None] = {
        "h": 1.5, "d": 4.0, "a": 6.0,
        "ou": 2.75, "over": 1.9, "under": 1.95,
        "ah": 1.25, "ah_h": 1.9, "ah_a": 1.95,
    }  # fmt: skip

    row.update(overrides)

    return row


def _issues(*rows: dict[str, float | None]) -> list[str]:
    return _issues_of(check_all, *rows)


def _issues_of(
    check: Callable[[Report, pd.DataFrame, OddsColumns], None], *rows: dict[str, float | None]
) -> list[str]:
    report = Report("test")
    check(report, pd.DataFrame(list(rows)), _COLUMNS)

    return report.issues


def test_plausible_odds_pass() -> None:
    assert _issues(_row()) == []


def test_a_row_without_a_market_is_not_checked_for_it() -> None:
    assert _issues(_row(h=None, ou=None, ah=None)) == []


def test_a_table_without_a_markets_columns_is_not_checked_for_it() -> None:
    # `universal.check_required_columns` reports the missing columns, once.
    row = {cell: value for cell, value in _row().items() if not cell.startswith("ah")}
    assert _issues(row) == []
    assert _issues_of(check_whole_markets, row) == []


def test_a_three_way_book_that_is_not_1x2_fails() -> None:
    assert any("overround" in issue for issue in _issues(_row(h=1.9, d=1.9, a=1.9)))


@pytest.fixture
def bands(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(odds, "LINE_LIMITS", _BANDS)
    monkeypatch.setattr(odds, "NO_PRICE_BAND", _BANDS[1].favourite_from)


def test_a_goal_line_below_the_minimum_fails() -> None:
    assert any("OU rows with a line below" in issue for issue in _issues(_row(ou=0.25)))


@pytest.mark.usefixtures("bands")
@pytest.mark.parametrize(
    ("home_price", "away_price", "ah"), [(1.05, 26.0, 5.5), (26.0, 1.05, -5.5)]
)
def test_a_short_favourite_may_carry_big_lines(
    home_price: float, away_price: float, ah: float
) -> None:
    assert _issues(_row(h=home_price, d=11.0, a=away_price, ah=ah, ou=6.5)) == []


@pytest.mark.usefixtures("bands")
def test_a_big_handicap_on_a_longer_favourite_fails() -> None:
    issues = _issues(_row(ah=3.5, ou=4.5))
    assert any("AH rows with a line bigger" in issue for issue in issues)


@pytest.mark.usefixtures("bands")
def test_a_big_goal_line_on_a_longer_favourite_fails() -> None:
    issues = _issues(_row(ou=5.5))
    assert any("OU rows with a line below" in issue for issue in issues)


@pytest.mark.usefixtures("bands")
def test_a_row_without_1x2_prices_uses_the_no_price_band() -> None:
    issues = _issues(_row(h=None, ah=5.5, ou=6.5))
    assert any("AH rows with a line bigger" in issue for issue in issues)


@pytest.mark.usefixtures("bands")
def test_a_table_without_the_1x2_columns_uses_the_no_price_band() -> None:
    row = {
        cell: value for cell, value in _row(ah=5.5, ou=6.5).items() if cell not in ("h", "d", "a")
    }
    assert any("AH rows with a line bigger" in issue for issue in _issues(row))


def test_line_limits_cover_every_price_and_shrink_as_the_favourite_lengthens() -> None:
    starts = [band.favourite_from for band in odds.LINE_LIMITS]
    ah_limits = [band.largest_ah for band in odds.LINE_LIMITS]
    ou_limits = [band.largest_ou for band in odds.LINE_LIMITS]

    assert starts[0] <= 1.0
    assert starts == sorted(starts)
    assert ah_limits == sorted(ah_limits, reverse=True)
    assert ou_limits == sorted(ou_limits, reverse=True)


def test_a_line_off_the_quarter_grid_fails() -> None:
    assert any("quarter-goal grid" in issue for issue in _issues(_row(ou=2.6)))


@pytest.mark.parametrize("ah", [2.75, -2.75, 3.0])
def test_a_goal_line_not_above_the_handicap_fails(ah: float) -> None:
    issues = _issues(_row(h=1.07, d=11.0, a=26.0, ou=2.75, ah=ah))
    assert any("not above the AH line" in issue for issue in issues)


def test_a_goal_line_above_the_handicap_passes() -> None:
    issues = _issues(_row(h=1.07, d=11.0, a=26.0, ou=3.0, ah=2.75))
    assert not any("not above the AH line" in issue for issue in issues)


def test_an_ah_sign_against_the_favourite_fails() -> None:
    # Home is the 1X2 favourite (1.5 vs 6.0), so a negative AH line contradicts it.
    assert any("AH sign" in issue for issue in _issues(_row(ah=-1.25)))


def test_a_level_handicap_is_not_held_to_the_favourite() -> None:
    # A 0 line names no favourite, so the 1X2 favourite cannot contradict it.
    assert _issues_of(odds.check_ah_sign, _row(ah=0.0)) == []


def test_markets_hold_every_cell_once() -> None:
    assert list(_COLUMNS.markets()) == ["1X2", "OU", "AH"]
    assert _COLUMNS.cells() == ["h", "d", "a", "ou", "over", "under", "ah", "ah_h", "ah_a"]


@pytest.mark.parametrize("cell", ["ou", "over", "under"])
def test_a_part_filled_market_fails(cell: str) -> None:
    issues = _issues_of(check_whole_markets, _row(**{cell: None}))
    assert issues == ["1 OU rows with only part of the market filled"]


def test_a_market_missing_whole_passes() -> None:
    assert _issues_of(check_whole_markets, _row(h=None, d=None, a=None)) == []


@pytest.fixture
def half_floor(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(odds, "COVERAGE_FLOOR", 0.5)


@pytest.mark.usefixtures("half_floor")
def test_coverage_at_the_floor_passes() -> None:
    assert _issues_of(check_coverage, _row(), _row(ah=None, ah_h=None, ah_a=None)) == []


@pytest.mark.usefixtures("half_floor")
def test_coverage_below_the_floor_fails() -> None:
    unpriced = _row(h=None, d=None, a=None)
    issues = _issues_of(check_coverage, _row(), unpriced, unpriced)
    assert issues == ["1/3 rows (33.3%) carry all three markets, below the 50% floor"]


def test_coverage_skips_a_table_without_the_odds_columns() -> None:
    report = Report("test")
    check_coverage(report, pd.DataFrame({"match_id": ["1"]}), _COLUMNS)
    assert report.ok


def test_the_coverage_floor_is_a_share() -> None:
    assert 0 < odds.COVERAGE_FLOOR <= 1
