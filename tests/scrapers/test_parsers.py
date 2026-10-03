"""`scrapers/parsers.py`: the helpers that turn one table cell into one value.

The page-level parsers (`parse_schedulis_row`, `parse_standings`) are left to a later batch
that runs them on a saved page.
"""

import pytest
from bs4 import BeautifulSoup

from scrapers.parsers import attr, clean_string, parse_float, parse_line, parse_score, tag_text

_SPAN = BeautifulSoup(
    '<span class="date on" data-t="2026-01-03 15:00"> 3 - 1 </span>', "html.parser"
).select_one("span")


def test_attr_returns_single_valued_attributes_only() -> None:
    assert attr(_SPAN, "data-t") == "2026-01-03 15:00"
    assert attr(_SPAN, "class") is None  # multi-valued in bs4, so not a str
    assert attr(_SPAN, "missing") is None
    assert attr(None, "data-t") is None


def test_tag_text_strips_and_tolerates_none() -> None:
    assert tag_text(_SPAN) == "3 - 1"
    assert tag_text(None) == ""


@pytest.mark.parametrize(
    ("raw", "score"),
    [
        ("0 - 3", (0, 3)),
        ("1-2", (1, 2)),
        ("10 : 0", (10, 0)),
        (" 2 - 2 ", (2, 2)),
        # Not a played score: the row is skipped as unfinished.
        ("", None),
        (None, None),
        ("-", None),
        ("Postp.", None),
        ("1 - 2 - 3", None),
        ("100-1", None),
    ],
)
def test_parse_score(raw: str | None, score: tuple[int, int] | None) -> None:
    assert parse_score(raw) == score


@pytest.mark.parametrize(
    ("raw", "value"),
    [("1.85", 1.85), (" 2 ", 2.0), ("", None), (None, None), ("-", None), ("abc", None)],
)
def test_parse_float(raw: str | None, value: float | None) -> None:
    assert parse_float(raw) == value


@pytest.mark.parametrize(
    ("raw", "line"),
    [
        # The docstring's cases: one minus sign anywhere negates the whole quarter line.
        ("3", 3.0),
        ("2.5/3", 2.75),
        ("-0.5", -0.5),
        ("0/0.5", 0.25),
        ("0/-0.5", -0.25),
        ("-1/1.5", -1.25),
        # Further strings seen on live rows, 2026-09-22.
        ("0", 0.0),
        ("0.5/1", 0.75),
        ("1.5", 1.5),
        # Not a line.
        ("", None),
        ("abc", None),
        ("/", None),
    ],
)
def test_parse_line(raw: str, line: float | None) -> None:
    assert parse_line(raw) == line


def test_clean_string_transliterates_portuguese_letters() -> None:
    assert clean_string("Grêmio São Paulo") == "Gremio Sao Paulo"
    assert clean_string("Arsenal") == "Arsenal"
