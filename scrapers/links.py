import re

LEAGUES_FILE = "config/LEAGUES.txt"

# https://football.nowgoal26.com/league/2025-2026/36 -> season "2025-2026", id 36
# https://football.nowgoal26.com/league/2025/71      -> season "2025",      id 71
#
# Two season conventions, both kept verbatim. European leagues run across two calendar
# years and nowgoal labels them "2025-2026"; calendar-year leagues (Scandinavia, Brazil,
# Japan, MLS, Russia's summer format...) play inside one year and are labelled "2025".
# Normalising the second into a range would state something false, so anything that needs
# to order or split seasons compares `domain.match.season_start_year`, not the string.
_LEAGUE_URL_RE = re.compile(r"/league/(?P<season>\d{4}(?:-\d{4})?)/(?P<league_id>\d+)")


def get_leagues_links() -> list[str]:
    """Read league URLs from the config file, one per line.

    Blank lines and `#` comments are ignored, so a league can be parked in the file
    instead of deleted while the schema is still moving — the list is the record of
    which league-seasons the corpus is meant to contain.
    """
    with open(LEAGUES_FILE, encoding="utf-8") as f:
        lines = (line.strip() for line in f)
        return [line for line in lines if line and not line.startswith("#")]


def parse_league_url(url: str) -> tuple[str, int]:
    """Extract (season, league_id) from a nowgoal26 league URL."""
    match = _LEAGUE_URL_RE.search(url)
    if match is None:
        raise ValueError(f"Cannot parse season/league id from URL: {url!r}")
    return match.group("season"), int(match.group("league_id"))
