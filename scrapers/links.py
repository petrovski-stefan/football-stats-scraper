import re

LEAGUES_FILE = "config/LEAGUES.txt"

# https://football.nowgoal26.com/league/2025-2026/36 -> season "2025-2026", id 36
_LEAGUE_URL_RE = re.compile(r"/league/(?P<season>\d{4}-\d{4})/(?P<league_id>\d+)")


def get_leagues_links() -> list[str]:
    """Read league URLs from the config file, one per line (blank lines ignored)."""
    with open(LEAGUES_FILE, encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def parse_league_url(url: str) -> tuple[str, int]:
    """Extract (season, league_id) from a nowgoal26 league URL."""
    match = _LEAGUE_URL_RE.search(url)
    if match is None:
        raise ValueError(f"Cannot parse season/league id from URL: {url!r}")
    return match.group("season"), int(match.group("league_id"))
