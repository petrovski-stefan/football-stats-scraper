"""`domain/scope.py`: which referenced history matches are fetched and used.

The friendly marker and the year cutoff are read from `scope.FRIENDLY_MARKER` and
`scope.HISTORY_FROM_YEAR`, not restated here, so these tests check the mechanism and not
the chosen values.
"""

import pytest

from domain import scope

MARKER = scope.FRIENDLY_MARKER
CUTOFF = scope.HISTORY_FROM_YEAR


@pytest.mark.parametrize(
    ("league", "friendly"),
    [
        (f"Test {MARKER} Cup", True),
        (f"TEST {MARKER.upper()}", True),  # case-insensitive
        ("Test League", False),
        ("", False),
        (None, False),
    ],
)
def test_is_friendly(league: str | None, friendly: bool) -> None:
    assert scope.is_friendly(league) is friendly


@pytest.mark.parametrize(
    ("date", "year"),
    [
        ("2025-08-09 10:30:00", 2025),
        (" 2025-08-09", 2025),
        ("09/08/2025", None),
        ("", None),
        (None, None),
    ],
)
def test_match_year(date: str | None, year: int | None) -> None:
    assert scope.match_year(date) == year


@pytest.mark.parametrize(
    ("league", "date", "usable"),
    [
        ("Test League", f"{CUTOFF}-01-01 15:00:00", True),
        ("Test League", f"{CUTOFF - 1}-12-31 15:00:00", False),
        (f"Test {MARKER}", f"{CUTOFF}-01-01 15:00:00", False),
        # An unreadable date is kept rather than dropped for a formatting reason.
        ("Test League", "not a date", True),
    ],
)
def test_in_scope(league: str, date: str, usable: bool) -> None:
    assert scope.in_scope(league, date) is usable


def test_is_abandoned_reads_the_list() -> None:
    listed = next(iter(scope.ABANDONED_MATCHES))
    assert scope.is_abandoned(listed)
    assert scope.is_abandoned(int(listed))  # an id read as a number still matches
    assert not scope.is_abandoned("0")
