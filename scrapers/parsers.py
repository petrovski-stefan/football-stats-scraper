"""Parsers for the league page: each turns a rendered row or table into values read from the
page, parsed and nothing computed (stage 1, `notes/FIELDS/SCHEDULE_1_RAW.md`).
"""

import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup, Tag

from domain.clock import to_berlin
from scrapers.constants import (
    LEAGUE_PAGE_CLOCK,
    PORTUGUESE_TO_ENGLISH_LETTERS,
    ROW_ODDS_CELLS,
    STANDING_ROWS,
    STANDING_TITLE_ROW,
)

_KICKOFF_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")
# "0 - 3", "1-2", "10 : 0" -> (home, away)
_SCORE_RE = re.compile(r"^\s*(\d{1,2})\s*[-:]\s*(\d{1,2})\s*$")
# toTeam('60') / toTeam(60) -> 60
_TEAM_ID_RE = re.compile(r"toTeam\(\s*'?(\d+)'?\s*\)")


def clean_string(string: str) -> str:
    """The text with each accented letter of `PORTUGUESE_TO_ENGLISH_LETTERS` made plain."""

    return "".join([(PORTUGUESE_TO_ENGLISH_LETTERS.get(char, char)) for char in string])


def parse_score(raw: str | None) -> tuple[int, int] | None:
    """Parse a score like '0 - 3' or '0-2' into (home, away). None if not a real score."""

    if not raw:
        return None

    found = _SCORE_RE.match(raw)
    if found is None:
        return None

    return int(found.group(1)), int(found.group(2))


def parse_float(raw: str | None) -> float | None:
    """Parse an odds cell to float; None for blanks/dashes/non-numeric text."""

    if not raw:
        return None

    try:
        return float(raw.strip())
    except ValueError:
        return None


def _odds_cells(row: Tag) -> tuple[str, str, str] | None:
    """The row's three raw odds-cell strings, whichever odds type is displayed."""

    cells = row.select(ROW_ODDS_CELLS)
    if len(cells) < 3:
        return None

    return tag_text(cells[0]), tag_text(cells[1]), tag_text(cells[2])


def parse_1x2_odds(row: Tag) -> tuple[float | None, float | None, float | None]:
    """Read the row's 1X2 odds cells as (home_win, draw, away_win).

    Assumes the schedule odds display has already been switched to 1X2, whose
    three cells are always ordered home / draw / away.
    """

    cells = _odds_cells(row)
    if cells is None:
        return None, None, None

    return parse_float(cells[0]), parse_float(cells[1]), parse_float(cells[2])


def parse_line(raw: str) -> float | None:
    """Parse an Asian line, a single value or a split quarter-line; None when it holds no number.

    The one minus sign belongs to the whole expression, wherever it hangs: `0/-0.5` -> -0.25,
    `-1/1.5` -> -1.25 (`scrapers/CLAUDE.md` §5; checked on a full round of rows, 2026-09-22).
    """

    text = (raw or "").strip()
    if not text:
        return None

    negative = "-" in text
    try:
        parts = [float(p) for p in text.replace("-", "").split("/") if p != ""]
    except ValueError:
        return None
    if not parts:
        return None

    magnitude = sum(parts) / len(parts)

    return -magnitude if negative else magnitude


def parse_ou_odds(row: Tag) -> tuple[float | None, float | None, float | None]:
    """Read the row's Over/Under cells as (over_odds, goal_line, under_odds).

    The goal line is Asian and variable — nowgoal moves the line and holds both prices
    near 1.90, so the *line* is the forecast and the prices only carry a sub-quarter tilt.
    """

    cells = _odds_cells(row)
    if cells is None:
        return None, None, None

    return parse_float(cells[0]), parse_line(cells[1]), parse_float(cells[2])


def parse_ah_odds(row: Tag) -> tuple[float | None, float | None, float | None]:
    """Read the row's Asian Handicap cells as (home_odds, handicap_line, away_odds).

    Sign convention, verified 10/10 against the 1X2 favourite on live rows:
    **positive means the home side is favoured** and gives the handicap.
    """

    cells = _odds_cells(row)
    if cells is None:
        return None, None, None

    return parse_float(cells[0]), parse_line(cells[1]), parse_float(cells[2])


def attr(tag: Tag | None, name: str) -> str | None:
    """Return a single-valued attribute as a str (bs4 attrs can be list-typed)."""

    if tag is None:
        return None

    value = tag.get(name)

    return value if isinstance(value, str) else None


def _team_id_from_onclick(tag: Tag | None) -> int | None:
    """The team id in a tag's `onclick="toTeam(...)"`; None when it has none."""

    onclick = attr(tag, "onclick")
    if onclick is None:
        return None

    found = _TEAM_ID_RE.search(onclick)

    return int(found.group(1)) if found else None


# The standings table's columns, as its title row names them (measured 2026-10-06).
_FINAL_TABLE_HEADER = ("R", "Team", "P", "W", "D", "L", "GD", "PTS")


def _parse_int(text: str) -> int | None:
    """The text as an int; None when it is not one."""

    try:
        return int(text.strip())
    except ValueError:
        return None


def parse_final_table(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """The standings table on screen, one dict per team; [] if its columns are not R, Team, P, W,
    D, L, GD, PTS. Each cell is read by its text (layout: `scrapers/CLAUDE.md` §2). A row that
    does not parse is skipped: the check against our rebuilt table shows the missing team.
    """

    title = soup.select_one(STANDING_TITLE_ROW)
    header = tuple(tag_text(s) for s in title.find_all("span", recursive=False)) if title else ()
    if header != _FINAL_TABLE_HEADER:
        return []

    lines: list[dict[str, Any]] = []
    for row in soup.select(STANDING_ROWS):
        cells = row.find_all("span", recursive=False)
        if len(cells) != len(_FINAL_TABLE_HEADER):
            continue

        team_id = _team_id_from_onclick(cells[1])
        numbers = [_parse_int(tag_text(cell)) for cell in (cells[0], *cells[2:])]
        if team_id is None or None in numbers:
            continue

        rank, played, won, drawn, lost, goal_diff, points = numbers
        lines.append(
            {
                "team_id": team_id,
                "s1_team_name": clean_string(
                    tag_text(cells[1].select_one("span.name") or cells[1])
                ),
                "s1_rank": rank,
                "s1_played": played,
                "s1_won": won,
                "s1_drawn": drawn,
                "s1_lost": lost,
                "s1_goal_diff": goal_diff,
                "s1_points": points,
            }
        )

    return lines


def parse_kickoff(raw: str | None) -> str | None:
    """A row's `data-t` kickoff as Berlin time with its offset; None if it does not parse.

    The page writes UTC+8 with no offset (`LEAGUE_PAGE_CLOCK`): the EPL's 17:30 UK kickoff on
    Saturday 31 Jan 2026 reads "2026-02-01 01:30" (`notes/FIELDS/SCHEDULE_1_RAW.md` S1.07).
    """

    text = (raw or "").strip()
    for kickoff_format in _KICKOFF_FORMATS:
        try:
            naive = datetime.strptime(text, kickoff_format)
        except ValueError:
            continue
        return to_berlin(naive.replace(tzinfo=LEAGUE_PAGE_CLOCK))

    return None


def parse_schedulis_row(row: Tag) -> dict[str, Any] | None:
    """Parse one finished `div.schedulis` row into its stage-1 fields; None if unplayed.

    Only what the row shows, nothing computed (`notes/FIELDS/SCHEDULE_1_RAW.md`): the caller
    adds the league context and the O/U and AH prices, read with the header switched.
    """

    ft = parse_score(attr(row, "score") or tag_text(row.select_one("span.score")))
    ht = parse_score(tag_text(row.select_one("span.ht")))
    if ft is None or ht is None:
        return None  # not played yet -> skip

    home_tag = row.select_one("span.home span[onclick]")
    away_tag = row.select_one("span.away span[onclick]")
    date_tag = row.select_one("span.date")
    home_odds, draw_odds, away_odds = parse_1x2_odds(row)

    return {
        "match_id": (attr(row, "matchid") or "").strip(),
        "s1_date": parse_kickoff(attr(date_tag, "data-t") or tag_text(date_tag)),
        "s1_home_team_id": _team_id_from_onclick(home_tag),
        "s1_away_team_id": _team_id_from_onclick(away_tag),
        "s1_home_team_name": clean_string(tag_text(home_tag)),
        "s1_away_team_name": clean_string(tag_text(away_tag)),
        "s1_ht_home_goals": ht[0],
        "s1_ht_away_goals": ht[1],
        "s1_ft_home_goals": ft[0],
        "s1_ft_away_goals": ft[1],
        "s1_odds_1x2_open_home": home_odds,
        "s1_odds_1x2_open_draw": draw_odds,
        "s1_odds_1x2_open_away": away_odds,
    }


def tag_text(tag: Tag | None) -> str:
    """The tag's stripped text; "" for no tag."""

    return tag.get_text(strip=True) if tag is not None else ""
