"""The standings table, rebuilt from results. Pure and stdlib only.

Decided by the user on 2026-10-06 (`notes/FIELDS/SCHEDULE_3_MULTI.md` §B): the project
builds its own tables instead of scraping them, because the page's `Round N` table counts
by round number and so can hold results played after a match. A table here holds exactly
the results it is given; which results those are (the 2 h 30 min rule) is the caller's.

One `Standings` holds three tables at once: every match (`total`), each team's home
matches only (`home`) and its away matches only (`away`). Feed it full-time goals for the
FT table and half-time goals for the HT one.

`HalfTimeFullTime` holds each team's half-time / full-time record, split the same three
ways: how its matches ended given how it stood at the break, from its own side (the
"team view", the user's choice on 2026-10-07).
"""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass

from domain.stats import team_result

VENUES = ("total", "home", "away")


@dataclass
class Line:
    """One team's row: P, W, D, L and goals, with points and goal difference derived."""

    played: int = 0
    won: int = 0
    drawn: int = 0
    lost: int = 0
    goals_for: int = 0
    goals_against: int = 0

    @property
    def points(self) -> int:
        """League points: 3 for a win, 1 for a draw."""

        return 3 * self.won + self.drawn

    @property
    def goal_diff(self) -> int:
        """Goals for minus goals against."""

        return self.goals_for - self.goals_against

    def add(self, goals_for: int, goals_against: int) -> None:
        """Count one result, from this team's side."""

        self.played += 1
        self.goals_for += goals_for
        self.goals_against += goals_against
        if goals_for > goals_against:
            self.won += 1
        elif goals_for == goals_against:
            self.drawn += 1
        else:
            self.lost += 1


class Standings:
    """The total, home and away tables of one competition, built one result at a time."""

    def __init__(self, teams: Iterable[int]) -> None:
        """Start the total, home and away tables with one empty line per team id."""

        ids = sorted(set(teams))
        self._lines = {venue: {team: Line() for team in ids} for venue in VENUES}

    def add(self, home: int, away: int, home_goals: int, away_goals: int) -> None:
        """Count one result. Both teams must be among those the table was made with."""

        self._lines["total"][home].add(home_goals, away_goals)
        self._lines["total"][away].add(away_goals, home_goals)
        self._lines["home"][home].add(home_goals, away_goals)
        self._lines["away"][away].add(away_goals, home_goals)

    def line(self, venue: str, team: int) -> Line:
        """The team's line in one table: "total", "home" or "away"."""

        return self._lines[venue][team]

    def ranks(self, venue: str) -> dict[int, int]:
        """Each team's position in one table; empty while the table holds no result.

        Points, then goal difference, then goals for, in every league. Teams equal on all three
        share a position and the next team skips past them (1, 2, 2, 4): no order is invented.
        """

        lines = self._lines[venue]
        if not any(line.played for line in lines.values()):
            return {}

        keys = {team: (line.points, line.goal_diff, line.goals_for) for team, line in lines.items()}

        return {team: 1 + sum(other > key for other in keys.values()) for team, key in keys.items()}

    def points_gaps(self, venue: str, team: int) -> tuple[int | None, int | None]:
        """How far the team trails the nearest team above and leads the nearest below, in points.

        None where no team has more (or fewer). By points only, so a team level on points is
        neither above nor below and no tie-break, head-to-head included, enters the gaps.
        """

        lines = self._lines[venue].values()
        own = self._lines[venue][team].points
        above = [line.points - own for line in lines if line.points > own]
        below = [own - line.points for line in lines if line.points < own]

        return min(above, default=None), min(below, default=None)


class HalfTimeFullTime:
    """Each team's (half-time, full-time) result pairs, "W", "D" or "L", from its own side.

    ("L", "W") is a match the team trailed at half-time and won; the same match is ("W", "L")
    for the other team. By venue, and the total is always home plus away.
    """

    def __init__(self, teams: Iterable[int]) -> None:
        """Start every team's record at zero in all three venues."""

        ids = sorted(set(teams))
        self._pairs: dict[str, dict[int, Counter[tuple[str, str]]]] = {
            venue: {team: Counter() for team in ids} for venue in VENUES
        }

    def add(self, home: int, away: int, ht: tuple[int, int], ft: tuple[int, int]) -> None:
        """Count one match: `ht` and `ft` are (home goals, away goals)."""

        home_pair = (team_result(*ht), team_result(*ft))
        away_pair = (team_result(ht[1], ht[0]), team_result(ft[1], ft[0]))
        self._pairs["total"][home][home_pair] += 1
        self._pairs["home"][home][home_pair] += 1
        self._pairs["total"][away][away_pair] += 1
        self._pairs["away"][away][away_pair] += 1

    def count(self, venue: str, team: int, ht_result: str, ft_result: str) -> int:
        """How many of the team's matches went `ht_result` at HT and `ft_result` at FT."""

        return self._pairs[venue][team][(ht_result, ft_result)]
