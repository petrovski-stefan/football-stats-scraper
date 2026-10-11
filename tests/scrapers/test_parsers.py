"""`scrapers/parsers.py`: the helpers that turn one table cell into one value, and the row
and table parsers on small hand-written fragments shaped like the league page.

Tests on a saved, trimmed copy of the real page are a later batch (IDEAS idea 11).
"""

import pytest
from bs4 import BeautifulSoup

from scrapers.parsers import (
    attr,
    clean_string,
    parse_final_table,
    parse_float,
    parse_kickoff,
    parse_line,
    parse_schedulis_row,
    parse_score,
    tag_text,
)

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


# --- Kickoff: the league page's UTC+8 to Berlin time --------------------------------


@pytest.mark.parametrize(
    ("raw", "berlin"),
    [
        # A Saturday 17:30 UK kickoff in winter is written as Sunday 01:30 on the page.
        ("2026-02-01 01:30", "2026-01-31 18:30+01:00"),
        # A Friday 20:00 UK kickoff in summer.
        ("2025-08-16 03:00", "2025-08-15 21:00+02:00"),
        ("2025-08-16 03:00:00", "2025-08-15 21:00+02:00"),
        # The user's page check, 2026-10-11: shown as Sunday 21:00 Berlin, `data-t` holds
        # Monday 03:00. The site's Time_Zone cookie moves the shown text, never `data-t`.
        ("2026-07-20 03:00", "2026-07-19 21:00+02:00"),
        (" 2026-02-01 01:30 ", "2026-01-31 18:30+01:00"),
        ("", None),
        (None, None),
        ("01/02/2026 01:30", None),
    ],
)
def test_parse_kickoff(raw: str | None, berlin: str | None) -> None:
    assert parse_kickoff(raw) == berlin


# --- One schedule row --------------------------------------------------------------


def _schedule_row(score: str, ht: str) -> str:
    return f"""
    <div class="schedulis" matchid="11" score="{score}">
      <span class="date" data-t="2026-02-01 01:30"></span>
      <span class="home"><span onclick="toTeam('5')">Home FC</span></span>
      <span class="score">{score}</span>
      <span class="ht">{ht}</span>
      <span class="away"><span onclick="toTeam(6)">Away FC</span></span>
      <span class="odds"><span>1.40</span><span>4.75</span><span>7.00</span></span>
    </div>"""


def test_parse_schedulis_row_reads_page_values_only() -> None:
    row = BeautifulSoup(_schedule_row("3 - 2", "0-2"), "html.parser").select_one("div")
    assert row is not None
    assert parse_schedulis_row(row) == {
        "match_id": "11",
        "s1_date": "2026-01-31 18:30+01:00",
        "s1_home_team_id": 5,
        "s1_away_team_id": 6,
        "s1_home_team_name": "Home FC",
        "s1_away_team_name": "Away FC",
        "s1_ht_home_goals": 0,
        "s1_ht_away_goals": 2,
        "s1_ft_home_goals": 3,
        "s1_ft_away_goals": 2,
        "s1_odds_1x2_open_home": 1.40,
        "s1_odds_1x2_open_draw": 4.75,
        "s1_odds_1x2_open_away": 7.00,
    }


def test_parse_schedulis_row_skips_an_unplayed_match() -> None:
    row = BeautifulSoup(_schedule_row("-", ""), "html.parser").select_one("div")
    assert row is not None
    assert parse_schedulis_row(row) is None


# --- The final table -----------------------------------------------------------------

_TITLE = (
    '<li class="title"><span class="rank">R</span><span class="team">Team</span>'
    "<span>P</span><span>W</span><span>D</span><span>L</span><span>GD</span>"
    '<span class="key">PTS</span></li>'
)


def _standing(rank: int, team: int, name: str, counts: tuple[int, ...]) -> str:
    played, won, drawn, lost, goal_diff, points = counts
    return (
        f'<li class="standlis"><span class="rank"><em>{rank}</em></span>'
        f'<span class="team" onclick="toTeam({team})"><span class="name">{name}</span></span>'
        f"<span>{played}</span><span><span>{won}</span></span><span><span>{drawn}</span></span>"
        f"<span><span>{lost}</span></span><span><span>{goal_diff}</span></span>"
        f'<span class="key blue"><b>{points}</b></span></li>'
    )


def _table(*rows: str, title: str = _TITLE) -> BeautifulSoup:
    html = f'<div id="standingPlates"><ul id="standingList">{title}{"".join(rows)}</ul></div>'
    return BeautifulSoup(html, "html.parser")


def test_parse_final_table() -> None:
    soup = _table(
        _standing(1, 19, "First FC", (38, 26, 7, 5, 44, 85)),
        _standing(20, 7, "Last FC", (38, 3, 5, 30, -61, 14)),
    )
    first, last = parse_final_table(soup)
    assert first == {
        "team_id": 19,
        "s1_team_name": "First FC",
        "s1_rank": 1,
        "s1_played": 38,
        "s1_won": 26,
        "s1_drawn": 7,
        "s1_lost": 5,
        "s1_goal_diff": 44,
        "s1_points": 85,
    }
    assert (last["s1_rank"], last["s1_goal_diff"]) == (20, -61)


def test_parse_final_table_refuses_unexpected_columns() -> None:
    title = _TITLE.replace("<span>GD</span>", "<span>GF</span>")
    assert (
        parse_final_table(_table(_standing(1, 19, "First FC", (1, 1, 0, 0, 2, 3)), title=title))
        == []
    )


def test_parse_final_table_skips_a_row_that_does_not_parse() -> None:
    broken = _standing(2, 8, "Broken FC", (1, 1, 0, 0, 2, 3)).replace("<em>2</em>", "<em>-</em>")
    rows = parse_final_table(_table(_standing(1, 19, "First FC", (1, 1, 0, 0, 2, 3)), broken))
    assert [r["team_id"] for r in rows] == [19]
