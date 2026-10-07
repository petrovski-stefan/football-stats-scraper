"""The standings table, rebuilt from results. Pure and stdlib only.

Decided by the user on 2026-10-06 (`notes/fields/schedule_3_multi.md` §B): the project
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
        return 3 * self.won + self.drawn

    @property
    def goal_diff(self) -> int:
        return self.goals_for - self.goals_against

    def add(self, goals_for: int, goals_against: int) -> None:
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
        ids = sorted(set(teams))
        self._lines = {venue: {team: Line() for team in ids} for venue in VENUES}

    def add(self, home: int, away: int, home_goals: int, away_goals: int) -> None:
        """Count one result. Both teams must be among those the table was made with."""
        self._lines["total"][home].add(home_goals, away_goals)
        self._lines["total"][away].add(away_goals, home_goals)
        self._lines["home"][home].add(home_goals, away_goals)
        self._lines["away"][away].add(away_goals, home_goals)

    def line(self, venue: str, team: int) -> Line:
        return self._lines[venue][team]

    def ranks(self, venue: str) -> dict[int, int]:
        """Each team's position in one table; empty while the table holds no result.

        Ordered by points, then goal difference, then goals for, in every league. Teams
        equal on all three share a position, and the next team's position skips past them
        (1, 2, 2, 4): no order is invented between teams the table cannot separate.
        """
        lines = self._lines[venue]
        if not any(line.played for line in lines.values()):
            return {}
        keys = {team: (line.points, line.goal_diff, line.goals_for) for team, line in lines.items()}
        return {team: 1 + sum(other > key for other in keys.values()) for team, key in keys.items()}


class HalfTimeFullTime:
    """Each team's (half-time result, full-time result) pairs from its own side, by venue.

    A pair is two letters, "W", "D" or "L": ("L", "W") is a match the team trailed at
    half-time and won, ("W", "L") one it led and lost. The same match counts as ("L", "W")
    for one team and ("W", "L") for the other, and Total is always Home + Away.
    """

    def __init__(self, teams: Iterable[int]) -> None:
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

    def count(self, venue: str, team: int, ht: str, ft: str) -> int:
        """How many of the team's matches went `ht` at half-time and `ft` at full time."""
        return self._pairs[venue][team][(ht, ft)]
