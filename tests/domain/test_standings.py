"""`domain/standings.py`: lines, the three venue tables, and the rank order."""

from domain.standings import VENUES, Line, Standings


def test_line_counts_a_win_a_draw_and_a_loss() -> None:
    line = Line()
    line.add(3, 1)
    line.add(2, 2)
    line.add(0, 1)
    assert (line.played, line.won, line.drawn, line.lost) == (3, 1, 1, 1)
    assert (line.goals_for, line.goals_against) == (5, 4)
    assert line.points == 4
    assert line.goal_diff == 1


def test_a_result_feeds_total_and_each_teams_own_venue() -> None:
    table = Standings([1, 2])
    table.add(home=1, away=2, home_goals=2, away_goals=0)
    assert table.line("total", 1).won == 1
    assert table.line("total", 2).lost == 1
    assert table.line("home", 1).played == 1
    assert table.line("away", 2).played == 1
    # Neither team played in the other venue.
    assert table.line("away", 1).played == 0
    assert table.line("home", 2).played == 0


def test_an_empty_table_has_no_ranks() -> None:
    table = Standings([1, 2, 3])
    assert all(table.ranks(venue) == {} for venue in VENUES)


def test_ranks_order_by_points_then_goal_difference_then_goals_for() -> None:
    table = Standings([1, 2, 3, 4])
    table.add(1, 2, 3, 0)  # team 1: 3 pts, GD +3, GF 3
    table.add(3, 4, 1, 0)  # team 3: 3 pts, GD +1, GF 1
    table.add(2, 4, 2, 2)  # teams 2 and 4: 1 pt each
    ranks = table.ranks("total")
    assert ranks[1] == 1
    assert ranks[3] == 2
    # Team 2: GD -3, GF 2. Team 4: GD -1, GF 2. Goal difference separates them.
    assert (ranks[4], ranks[2]) == (3, 4)


def test_teams_level_on_every_key_share_a_rank() -> None:
    table = Standings([1, 2, 3, 4])
    table.add(1, 2, 1, 1)
    table.add(3, 4, 1, 1)
    # All four: 1 pt, GD 0, GF 1.
    assert set(table.ranks("total").values()) == {1}


def test_a_team_that_has_not_played_is_still_ranked() -> None:
    table = Standings([1, 2, 3])
    table.add(1, 2, 0, 1)
    ranks = table.ranks("total")
    # 2 has 3 pts; 3 has 0 pts and GD 0; 1 has 0 pts and GD -1.
    assert (ranks[2], ranks[3], ranks[1]) == (1, 2, 3)
