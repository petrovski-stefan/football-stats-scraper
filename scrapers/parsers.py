import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from scrapers.constants import PORTUGUESE_TO_ENGLISH_LETTERS, ROW_ODDS_CELLS, STANDING_ROWS

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


def parse_1x2_odds(row: Tag) -> tuple[float | None, float | None, float | None]:
    """Read the row's 1X2 odds cells as (home_win, draw, away_win).

    Assumes the schedule odds display has already been switched to 1X2, whose
    three cells are always ordered home / draw / away.
    """
    cells = row.select(ROW_ODDS_CELLS)
    if len(cells) < 3:
        return None, None, None
    return (
        parse_float(tag_text(cells[0])),
        parse_float(tag_text(cells[1])),
        parse_float(tag_text(cells[2])),
    )


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


def parse_standings(standings_soup: BeautifulSoup) -> dict[int, int]:
    """Map team_id -> rank from the standings list, for the currently selected round."""
    positions: dict[int, int] = {}
    for row in standings_soup.select(STANDING_ROWS):
        rank_tag = row.select_one("span.rank em")
        team_tag = row.select_one("span.team")
        team_id = _team_id_from_onclick(team_tag)
        if rank_tag is None or team_id is None:
            continue
        rank_text = rank_tag.get_text(strip=True)
        if rank_text.isdigit():
            positions[team_id] = int(rank_text)
    return positions


def parse_row_identity(row: Tag) -> dict[str, Any]:
    """Identify a `div.schedulis` row: who is playing, when, and its match id.

    Unlike `parse_schedulis_row` this works on **unfinished** rows too, which is what
    lets `scrapers/schedule.py` order a round over every scheduled match rather than
    only the played ones. Returns team ids/tags as well so the caller can build the
    full record without re-selecting.
    """
    home_tag = row.select_one("span.home span[onclick]")
    away_tag = row.select_one("span.away span[onclick]")
    date_tag = row.select_one("span.date")

    return {
        "match_id": (attr(row, "matchid") or "").strip(),
        "date": attr(date_tag, "data-t") or tag_text(date_tag),
        "home_team_id": _team_id_from_onclick(home_tag),
        "away_team_id": _team_id_from_onclick(away_tag),
        "home_team_name": clean_string(tag_text(home_tag)),
        "away_team_name": clean_string(tag_text(away_tag)),
    }


def parse_schedulis_row(row: Tag, *, positions: dict[int, int]) -> dict[str, Any] | None:
    """Parse a single `div.schedulis` schedule row into a match dict.

    Returns None for matches that are not finished (no parseable HT + FT score).
    `match_index_in_round` / `matches_in_round` are *not* set here — they depend on the
    round's other rows and are attached by `scrapers/schedule.py`.
    """
    ft_raw = attr(row, "score") or tag_text(row.select_one("span.score"))
    ht_raw = tag_text(row.select_one("span.ht"))
    ft = parse_score(ft_raw)
    ht = parse_score(ht_raw)
    if ft is None or ht is None:
        return None  # not played yet -> skip

    identity = parse_row_identity(row)
    home_team_id = identity["home_team_id"]
    away_team_id = identity["away_team_id"]

    home_win_odds, draw_odds, away_win_odds = parse_1x2_odds(row)

    return {
        **identity,
        "home_team_position": positions.get(home_team_id) if home_team_id else None,
        "away_team_position": positions.get(away_team_id) if away_team_id else None,
        "ht_score": ht_raw,
        "ft_score": ft_raw,
        "ht_home_goals": ht[0],
        "ht_away_goals": ht[1],
        "ft_home_goals": ft[0],
        "ft_away_goals": ft[1],
        "home_win_initial_odds": home_win_odds,
        "draw_initial_odds": draw_odds,
        "away_win_initial_odds": away_win_odds,
    }


def tag_text(tag: Tag | None) -> str:
    return tag.get_text(strip=True) if tag is not None else ""
