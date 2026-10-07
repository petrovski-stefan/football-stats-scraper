"""`features/schedule_multi.py`: round positions and the table as it stood at each kickoff."""

from datetime import datetime, timedelta

import pandas as pd
import pytest

from domain.clock import BERLIN, to_berlin
from features.schedule_multi import FINISHED_AFTER, pre_kickoff_tables, round_positions

_START = datetime(2026, 1, 3, 15, 0, tzinfo=BERLIN)


def _match(
    match_id: str,
    kickoff: datetime,
    teams: tuple[int, int],
    ft: tuple[int, int],
    round_number: int = 1,
    stage: str = "",
) -> dict[str, object]:
    return {
        "match_id": match_id,
        "s1_stage": stage,
        "s1_round": round_number,
        "s1_date": to_berlin(kickoff),
        "s1_home_team_id": teams[0],
        "s1_away_team_id": teams[1],
        "s1_home_team_name": f"Team {teams[0]}",
        "s1_away_team_name": f"Team {teams[1]}",
        "s1_ft_home_goals": ft[0],
        "s1_ft_away_goals": ft[1],
        "s1_ht_home_goals": 0,
        "s1_ht_away_goals": 0,
    }


def _frame(*matches: dict[str, object]) -> pd.DataFrame:
    return pd.DataFrame(list(matches)).set_index("match_id", drop=False)


def test_round_positions_order_by_kickoff_then_names() -> None:
    frame = _frame(
        _match("a", _START + timedelta(hours=2), (1, 2), (0, 0)),
        _match("b", _START, (5, 6), (0, 0)),
        _match("c", _START, (3, 4), (0, 0)),  # same kickoff as b: names break the tie
        _match("d", _START, (7, 8), (0, 0), round_number=2),
    )
    pos = round_positions(frame)
    assert [pos.at[m, "s3_match_index_in_round"] for m in ("c", "b", "a")] == [1, 2, 3]
    assert pos.loc["a", "s3_matches_in_round"] == 3
    assert pos.loc["d", "s3_match_index_in_round"] == 1
    assert pos.loc["d", "s3_matches_in_round"] == 1


def test_the_first_match_sees_an_empty_table() -> None:
    tables = pre_kickoff_tables(_frame(_match("a", _START, (1, 2), (1, 0))))
    rank = tables.at["a", "s3_home_pre_ft_total_rank"]
    played = tables.at["a", "s3_home_pre_ft_total_played"]
    gap = tables.at["a", "s3_pre_rank_gap"]
    assert pd.isna(rank)
    assert played == 0
    assert pd.isna(gap)


@pytest.mark.parametrize(
    ("gap", "counted"), [(FINISHED_AFTER, 1), (FINISHED_AFTER - timedelta(minutes=1), 0)]
)
def test_a_match_counts_only_once_it_has_surely_finished(gap: timedelta, counted: int) -> None:
    frame = _frame(
        _match("early", _START, (1, 2), (2, 0)),
        _match("later", _START + gap, (1, 3), (0, 0)),
    )
    tables = pre_kickoff_tables(frame)
    assert tables.loc["later", "s3_home_pre_ft_total_played"] == counted


def test_a_postponed_match_counts_only_from_when_it_is_played() -> None:
    # Round 1's A v B is postponed until after round 2.
    day = timedelta(days=7)
    frame = _frame(
        _match("r1_cd", _START, (3, 4), (1, 0), round_number=1),
        _match("r2_ac", _START + day, (1, 3), (2, 0), round_number=2),
        _match("r1_ab", _START + 2 * day, (1, 2), (0, 1), round_number=1),
        _match("r3_ad", _START + 3 * day, (1, 4), (0, 0), round_number=3),
    )
    tables = pre_kickoff_tables(frame)
    # Before round 2, team 1 has played nothing: its round-1 match has not happened.
    assert tables.loc["r2_ac", "s3_home_pre_ft_total_played"] == 0
    # The postponed match itself sees round 2's result.
    assert tables.loc["r1_ab", "s3_home_pre_ft_total_played"] == 1
    assert tables.loc["r1_ab", "s3_home_pre_ft_total_points"] == 3
    # Round 3 sees both of team 1's matches.
    assert tables.loc["r3_ad", "s3_home_pre_ft_total_played"] == 2


def test_venue_tables_count_only_that_venue() -> None:
    frame = _frame(
        _match("a", _START, (1, 2), (1, 0)),
        _match("b", _START + timedelta(days=7), (2, 1), (0, 0)),
    )
    tables = pre_kickoff_tables(frame)
    # Team 2 is home in b; it has played one away match and no home match.
    assert tables.loc["b", "s3_home_pre_ft_away_played"] == 1
    assert tables.loc["b", "s3_home_pre_ft_home_played"] == 0
    assert tables.loc["b", "s3_away_pre_ft_home_points"] == 3


def test_stages_keep_separate_tables() -> None:
    frame = _frame(
        _match("a", _START, (1, 2), (1, 0), stage="Apertura"),
        _match("b", _START + timedelta(days=7), (1, 2), (0, 0), stage="Clausura"),
    )
    tables = pre_kickoff_tables(frame)
    assert tables.loc["b", "s3_home_pre_ft_total_played"] == 0


def test_rank_gap() -> None:
    frame = _frame(
        _match("a", _START, (1, 2), (3, 0)),
        _match("b", _START, (3, 4), (1, 1)),
        _match("c", _START + timedelta(days=7), (1, 2), (0, 0)),
    )
    tables = pre_kickoff_tables(frame)
    # Team 1 is first, team 2 last (4th); teams 3 and 4 share 2nd.
    assert tables.loc["c", "s3_home_pre_ft_total_rank"] == 1
    assert tables.loc["c", "s3_away_pre_ft_total_rank"] == 4
    assert tables.loc["c", "s3_pre_rank_gap"] == 3
