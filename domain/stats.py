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


def ht_ft_combo(ht_result: str, ft_result: str) -> str:
    """Half-time/full-time combination, e.g. '1-1', 'X-2' (one of 9)."""
    return f"{ht_result}-{ft_result}"


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
