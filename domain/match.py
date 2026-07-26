from datetime import datetime

from pydantic import BaseModel, computed_field

from domain import stats

_DATE_FORMATS = ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S")


def parse_match_datetime(raw: str) -> datetime | None:
    """Parse a `Match.date` string to a datetime, or None if it doesn't parse.

    Public because the kickoff ordering that assigns `match_index_in_round` has to
    read the same field the same way, in three places: the scraper
    (`scrapers/schedule.py`), the feature helper (`features/engine.py:round_position`)
    and the validator (`qa/league.py`). One parser, one definition of "when".
    """
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    return None


def round_sort_key(
    date: str, home_team_name: str, away_team_name: str
) -> tuple[bool, datetime, str, str]:
    """The canonical ordering of matches within a round: kickoff, then teams A-Z.

    The team-name tiebreak exists only to make the order *reproducible* when several
    matches kick off at the same minute — it carries no meaning, so nothing downstream
    should read significance into adjacent indices at a shared kickoff time.

    Rows whose date cannot be parsed sort last rather than raising, so one bad row
    cannot cost a whole round; `qa/league.py` reports them.
    """
    parsed = parse_match_datetime(date)
    return (parsed is None, parsed or datetime.min, home_team_name, away_team_name)


class Match(BaseModel):
    """A single finished match scraped from a nowgoal26 league schedule.

    Goals are derived from the half-time (HT) and full-time (FT) scores shown in
    the schedule row. 1X2 odds come from the schedule's odds column switched to 1X2.
    """

    # Match metadata
    season: str  # e.g. "2025-2026"
    league_id: int
    league_name: str
    stage: str  # group/stage label; "" for single-table leagues
    round: int
    match_id: str
    date: str  # UTC-ish timestamp from the row's data-t attribute, e.g. "2026-05-24 23:00"

    # Teams
    home_team_id: int
    away_team_id: int
    home_team_name: str
    away_team_name: str

    # Standings positions as of this round (None when standings unavailable)
    home_team_position: int | None
    away_team_position: int | None

    # Position of the match within its round, 1..matches_in_round, ordered by kickoff
    # time and tiebroken on team names. Assigned in `scrapers/schedule.py` because it
    # depends on the round's other rows — it cannot be a computed_field here.
    #
    # `matches_in_round` counts every *scheduled* match in the round, so it can exceed
    # the number of rows written for a partially-played round.
    #
    # Do NOT read `match_index_in_round == 1` as "first match of the round": 15.6% of
    # matches share their round's earliest kickoff and the tiebreak between them is
    # alphabetical, i.e. meaningless. Use `features/engine.py:round_position`.
    match_index_in_round: int
    matches_in_round: int

    # Raw score strings as shown on the page, e.g. ht_score "0-2", ft_score "0 - 3"
    ht_score: str
    ft_score: str

    # Goals (derived from the HT / FT scores)
    ht_home_goals: int
    ht_away_goals: int
    ft_home_goals: int
    ft_away_goals: int

    # 1X2 initial odds — filled in later by the match detail-page scrape.
    home_win_initial_odds: float | None = None
    draw_initial_odds: float | None = None
    away_win_initial_odds: float | None = None

    @computed_field
    @property
    def has_odds(self) -> bool:
        return all(
            [
                self.home_win_initial_odds is not None,
                self.draw_initial_odds is not None,
                self.away_win_initial_odds is not None,
            ]
        )

    @computed_field
    @property
    def total_goals(self) -> int:
        return self.ft_home_goals + self.ft_away_goals

    @computed_field
    @property
    def is_seven_or_more_goals(self) -> bool:
        """Over 6.5 goals market: 7 or more total goals."""
        return self.total_goals >= 7

    @computed_field
    @property
    def is_comeback(self) -> bool:
        """Comeback market (2-1 / 1-2): the team losing at half-time wins at full-time."""
        return stats.is_comeback(
            self.ht_home_goals,
            self.ht_away_goals,
            self.ft_home_goals,
            self.ft_away_goals,
        )

    @computed_field
    @property
    def is_comeback_home(self) -> bool:
        """Comeback won by the home team (losing at HT, winning at FT)."""
        return stats.is_comeback_home(
            self.ht_home_goals,
            self.ht_away_goals,
            self.ft_home_goals,
            self.ft_away_goals,
        )

    @computed_field
    @property
    def is_comeback_away(self) -> bool:
        """Comeback won by the away team (losing at HT, winning at FT)."""
        return stats.is_comeback_away(
            self.ht_home_goals,
            self.ht_away_goals,
            self.ft_home_goals,
            self.ft_away_goals,
        )

    # --- Results / half breakdowns -------------------------------------------
    @computed_field
    @property
    def ht_result(self) -> str:
        """Half-time result: '1' home, 'X' draw, '2' away."""
        return stats.one_x_two(self.ht_home_goals, self.ht_away_goals)

    @computed_field
    @property
    def ft_result(self) -> str:
        """Full-time result: '1' home, 'X' draw, '2' away."""
        return stats.one_x_two(self.ft_home_goals, self.ft_away_goals)

    @computed_field
    @property
    def ht_ft_combo(self) -> str:
        """Half-time/full-time combination, e.g. '1-1', 'X-2' (one of 9)."""
        return stats.ht_ft_combo(self.ht_result, self.ft_result)

    @computed_field
    @property
    def home_2h_goals(self) -> int:
        return self.ft_home_goals - self.ht_home_goals

    @computed_field
    @property
    def away_2h_goals(self) -> int:
        return self.ft_away_goals - self.ht_away_goals

    @computed_field
    @property
    def goals_1h(self) -> int:
        return self.ht_home_goals + self.ht_away_goals

    @computed_field
    @property
    def goals_2h(self) -> int:
        return self.total_goals - self.goals_1h

    @computed_field
    @property
    def btts(self) -> bool:
        """Both teams to score (at full time)."""
        return stats.is_btts(self.ft_home_goals, self.ft_away_goals)

    @computed_field
    @property
    def over_25(self) -> bool:
        """Over 2.5 total goals."""
        return stats.is_over(self.total_goals, 2.5)

    # --- Date-derived fields --------------------------------------------------
    @computed_field
    @property
    def day_of_week(self) -> int | None:
        """ISO weekday: Monday=1 .. Sunday=7. None if the date can't be parsed."""
        parsed = parse_match_datetime(self.date)
        return parsed.isoweekday() if parsed else None

    @computed_field
    @property
    def is_monday(self) -> bool:
        return self.day_of_week == 1

    @computed_field
    @property
    def is_midweek(self) -> bool:
        """Tuesday, Wednesday, or Thursday fixture."""
        return self.day_of_week in (2, 3, 4)

    # --- Standings / odds derivations ----------------------------------------
    @computed_field
    @property
    def position_gap(self) -> int | None:
        """Absolute league-table gap between the teams. None if a position is missing."""
        if self.home_team_position is None or self.away_team_position is None:
            return None
        return abs(self.home_team_position - self.away_team_position)

    @computed_field
    @property
    def favorite(self) -> str | None:
        """Name of the team with the lower win odds. None if odds missing or level."""
        home, away = self.home_win_initial_odds, self.away_win_initial_odds
        if home is None or away is None or home == away:
            return None
        return self.home_team_name if home < away else self.away_team_name

    @computed_field
    @property
    def favorite_odds(self) -> float | None:
        """Lower of the two win odds."""
        home, away = self.home_win_initial_odds, self.away_win_initial_odds
        if home is None or away is None:
            return None
        return min(home, away)

    @computed_field
    @property
    def underdog_odds(self) -> float | None:
        """Higher of the two win odds."""
        home, away = self.home_win_initial_odds, self.away_win_initial_odds
        if home is None or away is None:
            return None
        return max(home, away)

    @computed_field
    @property
    def implied_prob_home(self) -> float | None:
        """Implied home-win probability from the odds (1 / odds)."""
        return stats.implied_prob(self.home_win_initial_odds)

    @computed_field
    @property
    def implied_prob_away(self) -> float | None:
        """Implied away-win probability from the odds (1 / odds)."""
        return stats.implied_prob(self.away_win_initial_odds)
