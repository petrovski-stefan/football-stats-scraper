"""`domain/standings.py`: lines, the three venue tables, and the rank order."""

from itertools import permutations

from hypothesis import given
from hypothesis import strategies as st

from domain.standings import VENUES, HalfTimeFullTime, Line, Standings

_TEAMS = range(1, 7)
# Any run of results between two different teams: (home, away, home goals, away goals).
_RESULTS = st.lists(
    st.tuples(
        st.sampled_from(_TEAMS), st.sampled_from(_TEAMS), st.integers(0, 9), st.integers(0, 9)
    ).filter(lambda match: match[0] != match[1]),
    max_size=40,
)


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


def test_points_gaps_count_only_teams_with_more_or_fewer_points() -> None:
    table = Standings([1, 2, 3, 4])
    table.add(1, 2, 1, 0)
    table.add(3, 4, 0, 0)
    table.add(1, 3, 2, 0)
    table.add(2, 4, 1, 0)

    # Points: 1 has 6, 2 has 3, 3 and 4 have 1 each.
    assert table.points_gaps("total", 1) == (None, 3)
    assert table.points_gaps("total", 2) == (3, 2)

    # 3 ranks below 4 on goal difference, but a team level on points is neither side.
    assert table.points_gaps("total", 3) == (2, None)
    assert table.points_gaps("total", 4) == (2, None)


def test_points_gaps_are_empty_on_an_empty_table() -> None:
    table = Standings([1, 2])
    assert table.points_gaps("total", 1) == (None, None)


@given(_RESULTS)
def test_any_run_of_results_keeps_the_tables_consistent(
    results: list[tuple[int, int, int, int]],
) -> None:
    table = Standings(_TEAMS)
    for match in results:
        table.add(*match)

    lines = {team: table.line("total", team) for team in _TEAMS}
    assert sum(line.played for line in lines.values()) == 2 * len(results)
    assert sum(line.won for line in lines.values()) == sum(line.lost for line in lines.values())
    assert sum(line.goal_diff for line in lines.values()) == 0

    for team, total in lines.items():
        home, away = table.line("home", team), table.line("away", team)
        assert total.played == home.played + away.played, (team, total)
        assert total.points == home.points + away.points, (team, total)

    if results:  # an empty table has no ranks
        ranks = table.ranks("total")
        keys = {team: (line.points, line.goal_diff, line.goals_for) for team, line in lines.items()}
        assert min(ranks.values()) == 1

        # Ahead exactly when better on the keys; level on every key, level in rank.
        assert all((ranks[a] < ranks[b]) == (keys[a] > keys[b]) for a, b in permutations(_TEAMS, 2))


# --- The half-time / full-time record (team view) --------------------------------------


def test_one_comeback_is_l_w_for_one_team_and_w_l_for_the_other() -> None:
    record = HalfTimeFullTime([1, 2])
    record.add(home=1, away=2, ht=(0, 2), ft=(3, 2))  # the home team came back

    assert record.count("home", 1, "L", "W") == 1
    assert record.count("total", 1, "L", "W") == 1
    assert record.count("away", 2, "W", "L") == 1
    assert record.count("total", 2, "W", "L") == 1

    # Nothing lands in the other venue.
    assert record.count("away", 1, "L", "W") == 0
    assert record.count("home", 2, "W", "L") == 0


def test_total_is_home_plus_away() -> None:
    record = HalfTimeFullTime([1, 2])
    record.add(1, 2, (1, 0), (1, 0))  # team 1 at home: W/W
    record.add(2, 1, (0, 1), (2, 1))  # team 1 away: W at half-time, L at full time

    pairs = [(ht, ft) for ht in "WDL" for ft in "WDL"]
    for ht, ft in pairs:
        total = record.count("total", 1, ht, ft)
        assert total == record.count("home", 1, ht, ft) + record.count("away", 1, ht, ft), (ht, ft)

    assert record.count("total", 1, "W", "W") == 1
    assert record.count("total", 1, "W", "L") == 1
