"""`qa/odds.py`: the odds checks, on any table given its column names."""

import pandas as pd
import pytest

from qa.odds import OddsColumns, check_all
from qa.report import Report

_COLUMNS = OddsColumns("h", "d", "a", "ou", "over", "under", "ah", "ah_h", "ah_a")


def _row(**overrides: float | None) -> dict[str, float | None]:
    row: dict[str, float | None] = {
        "h": 1.5, "d": 4.0, "a": 6.0,
        "ou": 2.75, "over": 1.9, "under": 1.95,
        "ah": 1.25, "ah_h": 1.9, "ah_a": 1.95,
    }  # fmt: skip
    row.update(overrides)
    return row


def _issues(*rows: dict[str, float | None]) -> list[str]:
    report = Report("test")
    check_all(report, pd.DataFrame(list(rows)), _COLUMNS)
    return report.issues


def test_plausible_odds_pass() -> None:
    assert _issues(_row()) == []


def test_a_row_without_a_market_is_not_checked_for_it() -> None:
    assert _issues(_row(h=None, ou=None, ah=None)) == []


def test_a_three_way_book_that_is_not_1x2_fails() -> None:
    assert any("overround" in issue for issue in _issues(_row(h=1.9, d=1.9, a=1.9)))


def test_a_goal_line_out_of_range_fails() -> None:
    assert any("OU rows with a line outside" in issue for issue in _issues(_row(ou=0.25)))


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
