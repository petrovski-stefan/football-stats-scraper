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
    return "".join([(PORTUGUESE_TO_ENGLISH_LETTERS.get(char, char)) for char in string])


def parse_score(raw: str | None) -> tuple[int, int] | None:
    """Parse a score like '0 - 3' or '0-2' into (home, away). None if not a real score."""
    if not raw:
        return None
    match = _SCORE_RE.match(raw)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


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
    """Parse an Asian line: a single value, or a split quarter-line, with an optional sign.

    nowgoal writes a quarter line as two halves and hangs one minus sign off whichever
    half it reaches first, so the sign belongs to the whole expression, not to one part:

        "3"        ->  3.0      "2.5/3"    ->  2.75
        "-0.5"     -> -0.5      "0/0.5"    ->  0.25
        "0/-0.5"   -> -0.25     "-1/1.5"   -> -1.25

    Verified against a full round of live rows on 2026-09-22: every observed string
    (`-0.5`, `-1/1.5`, `0`, `0.5/1`, `0/-0.5`, `0/0.5`, `1.5`) round-trips under this rule.
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
    **positive means the home side is favoured** and gives the handicap. Note this is
    the opposite of football-data.co.uk's `AHh`, where negative means home gives.
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
    onclick = attr(tag, "onclick")
    if onclick is None:
        return None
    match = _TEAM_ID_RE.search(onclick)
    return int(match.group(1)) if match else None


# The standings table's columns, as its title row names them (measured 2026-10-06).
_FINAL_TABLE_HEADER = ("R", "Team", "P", "W", "D", "L", "GD", "PTS")


def _parse_int(text: str) -> int | None:
    try:
        return int(text.strip())
    except ValueError:
        return None


def parse_final_table(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """The standings table on screen, one dict per team; [] if its columns are not R, Team,
    P, W, D, L, GD, PTS.

    Each `li.standlis` row has eight `span` children in the title row's order. The counts
    sit inside nested tags (`<span><span>26</span></span>`, `<b>85</b>`), so each cell is
    read by its text. A row that does not parse is skipped; the caller compares the table
    with the one rebuilt from our own results, so a missing team shows up there.
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

    The league page gives kickoffs in UTC+8 (China time), with no offset written: the EPL's
    Saturday 31 Jan 2026, 17:30 UK kickoff reads "2026-02-01 01:30". Every schedule file
    before the staged pipeline stored that text unconverted (`notes/fields/schedule_1_raw.md`
    S1.07).
    """
    text = (raw or "").strip()
    for fmt in _KICKOFF_FORMATS:
        try:
            naive = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return to_berlin(naive.replace(tzinfo=LEAGUE_PAGE_CLOCK))
    return None


def parse_schedulis_row(row: Tag) -> dict[str, Any] | None:
    """Parse one finished `div.schedulis` row into its stage-1 fields; None if unplayed.

    Only what the row itself shows: ids, teams, kickoff, goals and the 1X2 prices (the
    caller adds the league context and the O/U and AH prices, read with the header switched).
    Nothing is computed here: `notes/fields/schedule_1_raw.md`.
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
    return tag.get_text(strip=True) if tag is not None else ""
