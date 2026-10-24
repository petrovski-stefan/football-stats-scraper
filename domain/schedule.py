"""The stage-1 contracts of the league page: what the scraper may write, and nothing else.

Every field is a value read from the page and only parsed (`notes/FIELDS/SCHEDULE_1_RAW.md`).
Nothing here is computed: derived fields live in the stage-2 and stage-3 builders
(`features/schedule_row.py`, `features/schedule_multi.py`). Field names are the column
names, so a row dumps straight to the CSV in `domain/columns.py` order.
"""

import re

from pydantic import BaseModel, ConfigDict, Field, field_validator

from domain.clock import parse_berlin

# "2025-2026" (European, cross-year) or "2025" (calendar-year league).
_SEASON_RE = re.compile(r"^(?P<start>\d{4})(?:-(?P<end>\d{4}))?$")


def season_start_year(season: str) -> int | None:
    """The calendar year a season began, for either label convention. None if unparseable.

    Season labels come from the nowgoal URL and are stored verbatim, because the two
    conventions describe genuinely different things: an English "2025-2026" runs Aug-May,
    a Norwegian "2025" runs Mar-Nov. Rewriting the latter as a range would invent a fact.

    Sorting is safe either way (the start year is a fixed-width prefix, so lexicographic
    order already agrees). What is *not* safe is **equality across conventions**: "2025"
    and "2025-2026" describe seasons starting in the same year but never compare equal, so
    `groupby("season")` splits them and an `isin([...])` season list silently matches
    neither. Anything asking "which seasons are contemporaneous?" must compare this.
    """

    match = _SEASON_RE.match(season.strip())

    return int(match.group("start")) if match else None


class ScheduleRow(BaseModel):
    """One finished match, as its row on the league page shows it."""

    model_config = ConfigDict(extra="forbid")

    match_id: str = Field(min_length=1)
    s1_season: str  # verbatim from the URL: "2025-2026" or "2025"
    s1_league_id: int
    s1_league_name: str
    s1_stage: str  # the stage tab's name; "" on a page without tabs
    s1_round: int = Field(ge=1)
    s1_date: str  # Berlin time with its offset, e.g. "2026-01-31 18:30+01:00"

    s1_home_team_id: int
    s1_away_team_id: int
    s1_home_team_name: str
    s1_away_team_name: str

    s1_ht_home_goals: int = Field(ge=0)
    s1_ht_away_goals: int = Field(ge=0)
    s1_ft_home_goals: int = Field(ge=0)
    s1_ft_away_goals: int = Field(ge=0)

    # Opening prices, decimal. The two Asian lines are quarter-line averages ("3/3.5" ->
    # 3.25); a positive AH line means the home team gives the handicap.
    s1_odds_1x2_open_home: float | None = None
    s1_odds_1x2_open_draw: float | None = None
    s1_odds_1x2_open_away: float | None = None
    s1_odds_ou_open_line: float | None = None
    s1_odds_ou_open_over: float | None = None
    s1_odds_ou_open_under: float | None = None
    s1_odds_ah_open_line: float | None = None
    s1_odds_ah_open_home: float | None = None
    s1_odds_ah_open_away: float | None = None

    @field_validator("s1_date")
    @classmethod
    def _has_offset(cls, value: str) -> str:
        parse_berlin(value)  # raises on a value with no offset

        return value


class FinalTableRow(BaseModel):
    """One team's line in the page's final table: read once per stage, as a check only."""

    model_config = ConfigDict(extra="forbid")

    season: str
    league_id: int
    stage: str
    team_id: int
    s1_team_name: str
    s1_rank: int = Field(ge=1)
    s1_played: int = Field(ge=0)
    s1_won: int = Field(ge=0)
    s1_drawn: int = Field(ge=0)
    s1_lost: int = Field(ge=0)
    s1_goal_diff: int
    s1_points: int
