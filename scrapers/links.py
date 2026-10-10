import json
import re
from dataclasses import dataclass

from pydantic import BaseModel, model_validator

from domain.schedule import season_start_year

LEAGUES_FILE = "config/leagues.json"

# https://football.nowgoal26.com/league/2025-2026/36 -> season "2025-2026", id 36
# https://football.nowgoal26.com/league/2025/71      -> season "2025",      id 71
#
# Two season conventions, both kept verbatim. European leagues run across two calendar
# years and nowgoal labels them "2025-2026"; calendar-year leagues (Scandinavia, Brazil,
# Japan, MLS, Russia's summer format...) play inside one year and are labelled "2025".
# Normalising the second into a range would state something false, so anything that needs
# to order or split seasons compares `domain.schedule.season_start_year`, not the string.
_LEAGUE_URL_RE = re.compile(r"/league/(?P<season>\d{4}(?:-\d{4})?)/(?P<league_id>\d+)")


class SeasonConfig(BaseModel):
    season: str
    url: str
    enabled: bool


class LeagueConfig(BaseModel):
    """One league in `config/leagues.json`.

    `stages` is every stage tab the league page showed under "Schedule" (`[]` when it has
    none) and `keep` is the subset to scrape. Both live on the league, not the season,
    because a league keeps its format from season to season.
    """

    name: str
    code: str
    continent: str
    country: str
    league_id: int
    stages: list[str]
    keep: list[str]
    seasons: list[SeasonConfig]

    @model_validator(mode="after")
    def _consistent(self) -> "LeagueConfig":
        unknown = set(self.keep) - set(self.stages)
        if unknown:
            raise ValueError(f"{self.name}: keep {sorted(unknown)} is not in stages")
        for s in self.seasons:
            if parse_league_url(s.url) != (s.season, self.league_id):
                raise ValueError(
                    f"{self.name}: {s.url} is not season {s.season} of id {self.league_id}"
                )
        return self


@dataclass(frozen=True)
class LeagueSeason:
    """One scrape job: a single league-season and the stages to click on it."""

    url: str
    season: str
    league_id: int
    keep: tuple[str, ...]
    code: str  # the config's short code, e.g. "SCO PR"
    name: str  # the config's name, for logs
    country: str  # the config's country, the first part of the file names


@dataclass(frozen=True)
class Selection:
    """Which league-seasons a run takes.

    By default, the seasons marked `enabled: true`. Naming leagues (`leagues`, by config
    code) or taking them all (`all_leagues`) ignores the flags. `before_year` then keeps only
    seasons that started before that year, in either label convention.
    """

    leagues: tuple[str, ...] = ()
    all_leagues: bool = False
    before_year: int | None = None


def load_leagues(path: str = LEAGUES_FILE) -> list[LeagueConfig]:
    """Read and validate the whole league config. Raises on any invalid entry.

    Failing the run beats skipping a bad entry: a typo in `keep` would otherwise scrape
    the wrong stage, or none, without anyone noticing.
    """
    with open(path, encoding="utf-8") as f:
        return [LeagueConfig.model_validate(entry) for entry in json.load(f)]


def get_league_seasons(
    selection: Selection | None = None, path: str = LEAGUES_FILE
) -> list[LeagueSeason]:
    """The chosen league-seasons, in file order. An unknown league code is an error.

    The file is the record of which league-seasons the corpus is meant to contain;
    `enabled` parks a season without deleting it.
    """
    chosen = selection or Selection()
    leagues = load_leagues(path)
    unknown = sorted(set(chosen.leagues) - {league.code for league in leagues})
    if unknown:
        raise ValueError(f"league codes not in {path}: {unknown}")
    return [
        LeagueSeason(
            s.url,
            s.season,
            league.league_id,
            tuple(league.keep),
            league.code,
            league.name,
            league.country,
        )
        for league in leagues
        for s in league.seasons
        if _chosen(chosen, league, s)
    ]


def _chosen(selection: Selection, league: LeagueConfig, season: SeasonConfig) -> bool:
    if selection.all_leagues or selection.leagues:
        picked = selection.all_leagues or league.code in selection.leagues
    else:
        picked = season.enabled
    if not picked or selection.before_year is None:
        return picked
    start = season_start_year(season.season)
    return start is not None and start < selection.before_year


def parse_league_url(url: str) -> tuple[str, int]:
    """Extract (season, league_id) from a nowgoal26 league URL."""
    match = _LEAGUE_URL_RE.search(url)
    if match is None:
        raise ValueError(f"Cannot parse season/league id from URL: {url!r}")
    return match.group("season"), int(match.group("league_id"))
