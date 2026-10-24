"""Pure football-stat helpers shared by the Match model and the detail-page
mini-records, so the derived-market logic lives in exactly one place.
"""


def one_x_two(home_goals: int, away_goals: int) -> str:
    """Home win -> '1', draw -> 'X', away win -> '2'."""

    if home_goals > away_goals:
        return "1"
    if home_goals < away_goals:
        return "2"

    return "X"


def team_result(goals_for: int, goals_against: int) -> str:
    """'W', 'D' or 'L' from one team's side: the team view of a result."""

    if goals_for > goals_against:
        return "W"

    return "D" if goals_for == goals_against else "L"


def is_over(total_goals: int, line: float = 2.5) -> bool:
    """Total goals over the given line (default 2.5)."""

    return total_goals > line


def is_btts(home_goals: int, away_goals: int) -> bool:
    """Both teams to score (full time)."""

    return home_goals > 0 and away_goals > 0


def is_comeback_home(ht_home: int, ht_away: int, ft_home: int, ft_away: int) -> bool:
    """Home team was losing at half-time and won at full-time."""

    return ht_home < ht_away and ft_home > ft_away


def is_comeback_away(ht_home: int, ht_away: int, ft_home: int, ft_away: int) -> bool:
    """Away team was losing at half-time and won at full-time."""

    return ht_home > ht_away and ft_home < ft_away


def is_comeback(ht_home: int, ht_away: int, ft_home: int, ft_away: int) -> bool:
    """Either team came back (HT loser wins at FT)."""

    return is_comeback_home(ht_home, ht_away, ft_home, ft_away) or is_comeback_away(
        ht_home, ht_away, ft_home, ft_away
    )


def points(goals_for: int, goals_against: int) -> int:
    """League points from one result (win 3, draw 1, loss 0)."""

    if goals_for > goals_against:
        return 3
    if goals_for == goals_against:
        return 1

    return 0


def implied_prob(odds: float | None) -> float | None:
    """Implied probability from decimal odds (1 / odds). None for missing/zero odds."""

    return 1 / odds if odds else None


def vig_free_1x2(
    home: float | None, draw: float | None, away: float | None
) -> tuple[float, float, float] | None:
    """Home, draw and away probabilities with the bookmaker's margin removed.

    Proportional normalisation over the three inverse prices, so they sum to 1. None when
    any price is missing or zero.
    """

    if not home or not draw or not away:
        return None
    inverse = (1 / home, 1 / draw, 1 / away)
    total = sum(inverse)

    return inverse[0] / total, inverse[1] / total, inverse[2] / total


def two_way_prob(odds_for: float | None, odds_against: float | None) -> float | None:
    """Vig-free probability of the first side in a two-way market.

    Proportional normalisation over the two inverse prices, so the bookmaker's overround
    cancels instead of inflating both sides. None when either price is missing or zero.
    """

    if not odds_for or not odds_against:
        return None
    implied_for, implied_against = 1 / odds_for, 1 / odds_against

    return implied_for / (implied_for + implied_against)
