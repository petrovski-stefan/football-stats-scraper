"""`features/schedule_multi.py`: round positions and offsets, the round so far, the table as it
stood at each kickoff, what is at stake, and that no score or odds of an unfinished match
reaches a row, on a made-up season and on generated ones."""

import random
from datetime import UTC, datetime, timedelta
from typing import Any

import pandas as pd
import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.clock import BERLIN, parse_instant, to_berlin
from domain.columns import HTFT_RESULTS, STANDING_SIDES, STANDING_VENUES
from features.schedule_multi import (
    FINISHED_AFTER,
    OPEN_LEAD,
    RESCHEDULED_AFTER_DAYS,
    ROUND_LOOK_BACK,
    SEVEN_PLUS_GOALS,
    derive,
    pre_kickoff_tables,
    round_offsets,
    round_positions,
    round_so_far,
)
from features.schedule_row import derive as derive_row

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
    schedule_df = _frame(
        _match("a", _START + timedelta(hours=2), (1, 2), (0, 0)),
        _match("b", _START, (5, 6), (0, 0)),
        _match("c", _START, (3, 4), (0, 0)),  # same kickoff as b: names break the tie
        _match("d", _START, (7, 8), (0, 0), round_number=2),
    )

    positions_df = round_positions(schedule_df)

    assert [positions_df.at[m, "s3_match_index_in_round"] for m in ("c", "b", "a")] == [1, 2, 3]
    assert positions_df.loc["a", "s3_matches_in_round"] == 3
    assert positions_df.loc["d", "s3_match_index_in_round"] == 1
    assert positions_df.loc["d", "s3_matches_in_round"] == 1


def test_round_offsets_leave_a_friday_to_monday_round_alone() -> None:
    schedule_df = _frame(
        _match("fri", _START - timedelta(hours=19), (1, 2), (0, 0)),
        _match("sat", _START, (3, 4), (0, 0)),
        _match("sun", _START + timedelta(days=1), (5, 6), (0, 0)),
        _match("mon", _START + timedelta(days=2, hours=5), (7, 8), (0, 0)),
    )

    offsets_df = round_offsets(schedule_df)

    assert not offsets_df["s3_is_rescheduled"].any()
    assert offsets_df.at["fri", "s3_days_off_round"] < 0 < offsets_df.at["mon", "s3_days_off_round"]


@pytest.mark.parametrize(
    ("late", "flagged"),
    [
        (timedelta(days=RESCHEDULED_AFTER_DAYS), True),
        (timedelta(days=RESCHEDULED_AFTER_DAYS) - timedelta(minutes=1), False),
    ],
)
def test_round_offsets_flag_a_match_played_off_its_round(late: timedelta, flagged: bool) -> None:
    schedule_df = _frame(
        *(_match(f"on{k}", _START, (2 * k, 2 * k + 1), (0, 0)) for k in range(1, 4)),
        _match("late", _START + late, (90, 91), (0, 0)),
        _match("early", _START - timedelta(days=30), (92, 93), (0, 0)),
    )

    offsets_df = round_offsets(schedule_df)

    assert offsets_df.at["late", "s3_days_off_round"] == pytest.approx(late / timedelta(days=1))
    assert bool(offsets_df.at["late", "s3_is_rescheduled"]) is flagged
    assert offsets_df.at["early", "s3_days_off_round"] == pytest.approx(-30)
    assert bool(offsets_df.at["early", "s3_is_rescheduled"])
    assert not any(offsets_df.at[m, "s3_is_rescheduled"] for m in ("on1", "on2", "on3"))


def test_round_offsets_keep_each_stages_round_apart() -> None:
    schedule_df = _frame(
        _match("a", _START, (1, 2), (0, 0), stage="Apertura"),
        _match("b", _START + timedelta(hours=2), (3, 4), (0, 0), stage="Apertura"),
        _match("c", _START + timedelta(days=180), (1, 3), (0, 0), stage="Clausura"),
        _match("d", _START + timedelta(days=180, hours=2), (2, 4), (0, 0), stage="Clausura"),
    )

    assert not round_offsets(schedule_df)["s3_is_rescheduled"].any()


def test_the_first_match_sees_an_empty_table() -> None:
    pre_kickoff_df = pre_kickoff_tables(_frame(_match("a", _START, (1, 2), (1, 0))))

    rank = pre_kickoff_df.at["a", "s3_home_pre_ft_total_rank"]
    played = pre_kickoff_df.at["a", "s3_home_pre_ft_total_played"]
    gap = pre_kickoff_df.at["a", "s3_pre_rank_gap"]

    assert pd.isna(rank)
    assert played == 0
    assert pd.isna(gap)


@pytest.mark.parametrize(
    ("gap", "counted"), [(FINISHED_AFTER, 1), (FINISHED_AFTER - timedelta(minutes=1), 0)]
)
def test_a_match_counts_only_once_it_has_surely_finished(gap: timedelta, counted: int) -> None:
    schedule_df = _frame(
        _match("early", _START, (1, 2), (2, 0)),
        _match("later", _START + gap, (1, 3), (0, 0)),
    )
    pre_kickoff_df = pre_kickoff_tables(schedule_df)
    assert pre_kickoff_df.loc["later", "s3_home_pre_ft_total_played"] == counted


def test_a_postponed_match_counts_only_from_when_it_is_played() -> None:
    # Round 1's A v B is postponed until after round 2.
    day = timedelta(days=7)
    schedule_df = _frame(
        _match("r1_cd", _START, (3, 4), (1, 0), round_number=1),
        _match("r2_ac", _START + day, (1, 3), (2, 0), round_number=2),
        _match("r1_ab", _START + 2 * day, (1, 2), (0, 1), round_number=1),
        _match("r3_ad", _START + 3 * day, (1, 4), (0, 0), round_number=3),
    )

    pre_kickoff_df = pre_kickoff_tables(schedule_df)

    # Before round 2, team 1 has played nothing: its round-1 match has not happened.
    assert pre_kickoff_df.loc["r2_ac", "s3_home_pre_ft_total_played"] == 0
    # The postponed match itself sees round 2's result.
    assert pre_kickoff_df.loc["r1_ab", "s3_home_pre_ft_total_played"] == 1
    assert pre_kickoff_df.loc["r1_ab", "s3_home_pre_ft_total_points"] == 3
    # Round 3 sees both of team 1's matches.
    assert pre_kickoff_df.loc["r3_ad", "s3_home_pre_ft_total_played"] == 2


def test_venue_tables_count_only_that_venue() -> None:
    schedule_df = _frame(
        _match("a", _START, (1, 2), (1, 0)),
        _match("b", _START + timedelta(days=7), (2, 1), (0, 0)),
    )

    pre_kickoff_df = pre_kickoff_tables(schedule_df)

    # Team 2 is home in b; it has played one away match and no home match.
    assert pre_kickoff_df.loc["b", "s3_home_pre_ft_away_played"] == 1
    assert pre_kickoff_df.loc["b", "s3_home_pre_ft_home_played"] == 0
    assert pre_kickoff_df.loc["b", "s3_away_pre_ft_home_points"] == 3


def test_stages_keep_separate_tables() -> None:
    schedule_df = _frame(
        _match("a", _START, (1, 2), (1, 0), stage="Apertura"),
        _match("b", _START + timedelta(days=7), (1, 2), (0, 0), stage="Clausura"),
    )
    pre_kickoff_df = pre_kickoff_tables(schedule_df)
    assert pre_kickoff_df.loc["b", "s3_home_pre_ft_total_played"] == 0


def test_rank_gap() -> None:
    schedule_df = _frame(
        _match("a", _START, (1, 2), (3, 0)),
        _match("b", _START, (3, 4), (1, 1)),
        _match("c", _START + timedelta(days=7), (1, 2), (0, 0)),
    )

    pre_kickoff_df = pre_kickoff_tables(schedule_df)

    # Team 1 is first, team 2 last (4th); teams 3 and 4 share 2nd.
    assert pre_kickoff_df.loc["c", "s3_home_pre_ft_total_rank"] == 1
    assert pre_kickoff_df.loc["c", "s3_away_pre_ft_total_rank"] == 4
    assert pre_kickoff_df.loc["c", "s3_pre_rank_gap"] == 3


# --- The half-time / full-time record -------------------------------------------------


def _with_ht(match: dict[str, object], ht: tuple[int, int]) -> dict[str, object]:
    return {**match, "s1_ht_home_goals": ht[0], "s1_ht_away_goals": ht[1]}


def _season() -> pd.DataFrame:
    week = timedelta(days=7)

    return _frame(
        _with_ht(_match("a", _START, (1, 2), (3, 2)), (0, 2)),  # 1 comes back, 2 blows a lead
        _with_ht(_match("b", _START, (3, 4), (1, 1)), (1, 0)),
        _with_ht(_match("c", _START + week, (2, 3), (0, 2)), (0, 0)),
        _with_ht(_match("d", _START + week, (4, 1), (2, 2)), (2, 1)),
        _with_ht(_match("e", _START + 2 * week, (1, 3), (1, 0)), (1, 0)),
    )


def test_htft_record_is_from_each_teams_own_side() -> None:
    pre_kickoff_df = pre_kickoff_tables(_season())
    # Before match e, team 1 (home in e) has one comeback, team 3 (away in e) has none.
    assert pre_kickoff_df.at["e", "s3_home_pre_htft_total_l_w"] == 1
    assert pre_kickoff_df.at["e", "s3_home_pre_htft_home_l_w"] == 1
    assert (
        pre_kickoff_df.at["c", "s3_home_pre_htft_away_w_l"] == 1
    )  # team 2 blew its lead away in a


def test_a_match_never_counts_in_its_own_record() -> None:
    pre_kickoff_df = pre_kickoff_tables(_season())
    assert pre_kickoff_df.at["a", "s3_home_pre_htft_total_l_w"] == 0


def _cells(
    pre_kickoff_df: pd.DataFrame,
    side: str,
    venue: str,
    ht_results: tuple[str, ...],
    ft_results: tuple[str, ...],
) -> "pd.Series[Any]":
    """The sum of some HT/FT cells, row by row."""

    names = [f"s3_{side}_pre_htft_{venue}_{ht}_{ft}" for ht in ht_results for ft in ft_results]

    return pre_kickoff_df[names].sum(axis=1)


def test_htft_counts_agree_with_the_standings() -> None:
    pre_kickoff_df = pre_kickoff_tables(_season())
    every = HTFT_RESULTS

    for side in STANDING_SIDES:
        for venue in STANDING_VENUES:
            played = pre_kickoff_df[f"s3_{side}_pre_ft_{venue}_played"]
            assert (_cells(pre_kickoff_df, side, venue, every, every) == played).all()
            for result, stat in zip(HTFT_RESULTS, ("won", "drawn", "lost"), strict=True):
                by_ht = _cells(pre_kickoff_df, side, venue, (result,), every)
                by_ft = _cells(pre_kickoff_df, side, venue, every, (result,))
                assert (by_ht == pre_kickoff_df[f"s3_{side}_pre_ht_{venue}_{stat}"]).all()
                assert (by_ft == pre_kickoff_df[f"s3_{side}_pre_ft_{venue}_{stat}"]).all()


# --- What is at stake ------------------------------------------------------------------


def test_matches_left_count_this_match_and_the_later_ones() -> None:
    week = timedelta(days=7)
    schedule_df = _frame(
        _match("a", _START, (1, 2), (0, 0)),
        _match("b", _START + week, (1, 3), (0, 0)),
        _match("c", _START + 2 * week, (2, 1), (0, 0)),
        _match("d", _START + 3 * week, (1, 3), (0, 0), stage="Clausura"),
    )

    pre_kickoff_df = pre_kickoff_tables(schedule_df)

    # Team 1 plays a, b and c in the first stage; d belongs to another stage.
    assert pre_kickoff_df.at["a", "s3_home_pre_matches_left"] == 3
    assert pre_kickoff_df.at["b", "s3_home_pre_matches_left"] == 2
    assert pre_kickoff_df.at["c", "s3_away_pre_matches_left"] == 1
    assert pre_kickoff_df.at["d", "s3_home_pre_matches_left"] == 1


def test_points_gaps_read_the_table_at_kickoff() -> None:
    schedule_df = _frame(
        _match("a", _START, (1, 2), (1, 0)),
        _match("b", _START, (3, 4), (0, 0)),
        _match("c", _START + timedelta(days=7), (1, 3), (0, 0)),
    )

    pre_kickoff_df = pre_kickoff_tables(schedule_df)

    # Before c: 1 has 3 points, 3 and 4 have 1, 2 has none.
    assert pd.isna(pre_kickoff_df.at["c", "s3_home_pre_pts_to_above"])
    assert pre_kickoff_df.at["c", "s3_home_pre_pts_to_below"] == 2
    assert pre_kickoff_df.at["c", "s3_away_pre_pts_to_above"] == 2
    assert pre_kickoff_df.at["c", "s3_away_pre_pts_to_below"] == 1

    # The first matches see an empty table.
    assert pd.isna(pre_kickoff_df.at["a", "s3_home_pre_pts_to_above"])
    assert pd.isna(pre_kickoff_df.at["a", "s3_home_pre_pts_to_below"])


def test_rank_change_since_open_counts_the_results_after_the_opening_odds() -> None:
    schedule_df = _frame(
        _match("a", _START, (1, 2), (1, 0)),
        _match("b", _START, (3, 4), (0, 0)),
        _match("c", _START + timedelta(days=5), (2, 4), (3, 0)),
        _match("d", _START + timedelta(days=8), (2, 3), (0, 0)),
    )

    pre_kickoff_df = pre_kickoff_tables(schedule_df)

    # When d's odds opened only a and b had been played: 1 first, 3 and 4 joint second, 2
    # last. By kickoff c lifted 2 to first (3 points, GD +2) and 3 fell to third.
    assert pre_kickoff_df.at["d", "s3_home_rank_change_since_open"] == -3
    assert pre_kickoff_df.at["d", "s3_away_rank_change_since_open"] == 1

    # Nothing had been played when a's odds opened.
    assert pd.isna(pre_kickoff_df.at["a", "s3_home_rank_change_since_open"])


@pytest.mark.parametrize(
    ("gap", "change"),
    [(OPEN_LEAD + FINISHED_AFTER, 0), (OPEN_LEAD + FINISHED_AFTER - timedelta(minutes=1), 1)],
)
def test_a_result_is_news_only_after_the_odds_opened(gap: timedelta, change: int) -> None:
    played = _START + timedelta(days=1)
    schedule_df = _frame(
        _match("first", _START, (1, 2), (1, 0)),
        _match("news", played, (3, 4), (2, 0)),
        _match("target", played + gap, (1, 3), (0, 0)),
    )

    pre_kickoff_df = pre_kickoff_tables(schedule_df)

    # "news" lifts 3 above 1. It is in the table at the open only if it had surely finished.
    assert pre_kickoff_df.at["target", "s3_home_rank_change_since_open"] == change


# --- The round so far ------------------------------------------------------------------


def _with_events(
    match: dict[str, object], comeback: bool = False, goals: int = 2, line: float = 2.5
) -> dict[str, object]:
    return {
        **match,
        "s2_is_comeback": comeback,
        "s2_total_goals": goals,
        "s1_odds_ou_open_line": line,
    }


def _counts(round_so_far_df: pd.DataFrame, match_id: str) -> list[int]:
    """Finished, comebacks, 7+ goals and rare events, in that order."""

    names = ("finished", "comebacks", "seven_plus", "rare_events")

    return [int(round_so_far_df.at[match_id, f"s3_round_pre_{name}"]) for name in names]


def test_round_so_far_counts_the_finished_round_mates() -> None:
    schedule_df = _frame(
        _with_events(_match("a", _START, (1, 2), (3, 2)), comeback=True, goals=5),
        _with_events(_match("b", _START, (3, 4), (5, 2)), goals=SEVEN_PLUS_GOALS),
        _with_events(_match("c", _START + FINISHED_AFTER, (5, 6), (0, 0))),
        _with_events(_match("d", _START + timedelta(hours=1), (7, 8), (0, 0))),
        _with_events(_match("e", _START + FINISHED_AFTER, (9, 10), (0, 0), round_number=2)),
    )

    round_so_far_df = round_so_far(schedule_df)

    assert _counts(round_so_far_df, "c") == [2, 1, 1, 2]

    # The first kickoff, a match kicking off before anything finished, another round.
    for match in ("a", "b", "d", "e"):
        assert _counts(round_so_far_df, match) == [0, 0, 0, 0]


def test_a_comeback_with_seven_goals_is_one_rare_event() -> None:
    schedule_df = _frame(
        _with_events(_match("a", _START, (1, 2), (4, 3)), comeback=True, goals=SEVEN_PLUS_GOALS),
        _with_events(_match("b", _START + timedelta(days=1), (3, 4), (0, 0))),
    )
    assert _counts(round_so_far(schedule_df), "b") == [1, 1, 1, 1]


@pytest.mark.parametrize(
    ("gap", "finished"),
    [
        (FINISHED_AFTER - timedelta(minutes=1), 0),
        (FINISHED_AFTER, 1),
        (ROUND_LOOK_BACK - timedelta(minutes=1), 1),
        (ROUND_LOOK_BACK, 0),
    ],
)
def test_round_so_far_looks_back_from_2h30_to_under_5_days(gap: timedelta, finished: int) -> None:
    schedule_df = _frame(
        _with_events(_match("early", _START, (1, 2), (0, 0))),
        _with_events(_match("later", _START + gap, (3, 4), (0, 0))),
    )
    assert round_so_far(schedule_df).at["later", "s3_round_pre_finished"] == finished


def test_round_so_far_averages_goals_and_lines_and_counts_both_teams_scoring() -> None:
    schedule_df = _frame(
        _with_events(_match("a", _START, (1, 2), (1, 1)), goals=2, line=2.5),
        _with_events(_match("b", _START, (3, 4), (0, 4)), goals=4, line=2.5),
        _with_events(_match("c", _START, (5, 6), (0, 2)), goals=2, line=2.75),
        _with_events(_match("d", _START + FINISHED_AFTER, (7, 8), (3, 2)), goals=5, line=3.25),
    )

    round_so_far_df = round_so_far(schedule_df)

    assert round_so_far_df.at["d", "s3_round_pre_avg_goals"] == pytest.approx(8 / 3)
    assert round_so_far_df.at["d", "s3_round_pre_avg_ou_line"] == pytest.approx(7.75 / 3)
    assert round_so_far_df.at["d", "s3_round_pre_btts"] == 1

    # Nothing had finished at the first kickoff: no average, no count.
    assert pd.isna(round_so_far_df.at["a", "s3_round_pre_avg_goals"])
    assert pd.isna(round_so_far_df.at["a", "s3_round_pre_avg_ou_line"])
    assert round_so_far_df.at["a", "s3_round_pre_btts"] == 0


def test_a_round_mate_without_a_line_counts_but_stays_out_of_both_averages() -> None:
    nan = float("nan")
    schedule_df = _frame(
        _with_events(_match("a", _START, (1, 2), (3, 3)), goals=6, line=nan),
        _with_events(_match("b", _START, (3, 4), (1, 0)), goals=1, line=2.25),
        _with_events(_match("c", _START + FINISHED_AFTER, (5, 6), (0, 0))),
        _with_events(_match("x", _START, (7, 8), (2, 2), round_number=2), goals=4, line=nan),
        _with_events(_match("y", _START + FINISHED_AFTER, (9, 10), (0, 0), round_number=2)),
    )

    round_so_far_df = round_so_far(schedule_df)

    assert round_so_far_df.at["c", "s3_round_pre_finished"] == 2
    assert round_so_far_df.at["c", "s3_round_pre_btts"] == 1
    assert round_so_far_df.at["c", "s3_round_pre_avg_goals"] == pytest.approx(1.0)
    assert round_so_far_df.at["c", "s3_round_pre_avg_ou_line"] == pytest.approx(2.25)

    # Round 2's only finished match has no line: both averages stay empty.
    assert round_so_far_df.at["y", "s3_round_pre_finished"] == 1
    assert pd.isna(round_so_far_df.at["y", "s3_round_pre_avg_goals"])
    assert pd.isna(round_so_far_df.at["y", "s3_round_pre_avg_ou_line"])


def test_round_so_far_keeps_each_stages_round_apart() -> None:
    schedule_df = _frame(
        _with_events(_match("a", _START, (1, 2), (3, 2), stage="Apertura"), comeback=True, goals=5),
        _with_events(_match("b", _START + timedelta(days=1), (3, 4), (0, 0), stage="Clausura")),
    )
    assert _counts(round_so_far(schedule_df), "b") == [0, 0, 0, 0]


# --- No leak: no score or odds of an unfinished match reaches a row ---------------------


def _results_and_odds(rng: random.Random) -> dict[str, object]:
    """A made-up score and opening odds for one match."""

    ht = (rng.randint(0, 2), rng.randint(0, 2))
    ft = (ht[0] + rng.randint(0, 3), ht[1] + rng.randint(0, 3))
    p_home, p_draw = rng.uniform(0.2, 0.6), rng.uniform(0.2, 0.3)

    return {
        "s1_ht_home_goals": ht[0],
        "s1_ht_away_goals": ht[1],
        "s1_ft_home_goals": ft[0],
        "s1_ft_away_goals": ft[1],
        "s1_odds_1x2_open_home": round(1 / (1.05 * p_home), 2),
        "s1_odds_1x2_open_draw": round(1 / (1.05 * p_draw), 2),
        "s1_odds_1x2_open_away": round(1 / (1.05 * (1 - p_home - p_draw)), 2),
        "s1_odds_ou_open_line": rng.choice([2.25, 2.5, 2.75, 3.0]),
        "s1_odds_ou_open_over": 1.9,
        "s1_odds_ou_open_under": 1.9,
        "s1_odds_ah_open_line": rng.choice([-0.5, 0.0, 0.25, 0.75]),
        "s1_odds_ah_open_home": 1.9,
        "s1_odds_ah_open_away": 1.95,
    }


def _made_up_season(seed: int = 7) -> list[dict[str, object]]:
    """Six teams, a double round robin of 10 rounds. Each round has two simultaneous kickoffs
    and a third that starts exactly FINISHED_AFTER later, a minute less, 1 h or 4 h later; one
    match is played 10 days late and one a month early. The minute-less gap is what catches a
    window that counts a match too soon."""

    rng = random.Random(seed)
    teams = list(range(1, 7))
    single = []
    for _ in range(len(teams) - 1):
        single.append([(teams[i], teams[-1 - i]) for i in range(len(teams) // 2)])
        teams = [teams[0], teams[-1], *teams[1:-1]]
    rounds = single + [[(away, home) for home, away in pairs] for pairs in single]

    gaps = (
        FINISHED_AFTER,
        FINISHED_AFTER - timedelta(minutes=1),
        timedelta(hours=1),
        timedelta(hours=4),
    )
    moved = {(2, 2): timedelta(days=10), (7, 0): -timedelta(days=30)}

    rows: list[dict[str, object]] = []
    for round_index, pairs in enumerate(rounds):
        for i, (home, away) in enumerate(pairs):
            kickoff = (
                _START
                + timedelta(days=7 * round_index)
                + (gaps[round_index % 4] if i == 2 else timedelta())
            )
            rows.append(
                {
                    "match_id": f"r{round_index + 1}m{i}",
                    "s1_stage": "",
                    "s1_round": round_index + 1,
                    "s1_date": to_berlin(kickoff + moved.get((round_index, i), timedelta())),
                    "s1_home_team_id": home,
                    "s1_away_team_id": away,
                    "s1_home_team_name": f"Team {home}",
                    "s1_away_team_name": f"Team {away}",
                    **_results_and_odds(rng),
                }
            )

    return rows


def _stage_2(rows: list[dict[str, object]]) -> pd.DataFrame:
    """The rows with their stage-2 fields, as `features.schedule_row` would write them."""

    return pd.DataFrame([{**row, **derive_row(row)} for row in rows]).set_index(
        "match_id", drop=False
    )


def _kickoff(row: dict[str, object]) -> datetime:
    return parse_instant(str(row["s1_date"]))


def _differing(before_df: pd.DataFrame, after_df: pd.DataFrame, match_id: str) -> list[str]:
    """The stage-3 columns whose value for one match differs between two builds."""

    columns = []
    for column in before_df.columns:
        before_value, after_value = before_df.at[match_id, column], after_df.at[match_id, column]
        if pd.isna(before_value) or pd.isna(after_value):
            if not (pd.isna(before_value) and pd.isna(after_value)):
                columns.append(str(column))
        elif before_value != after_value:
            columns.append(str(column))

    return columns


def _leaks(rows: list[dict[str, object]], rng: random.Random) -> dict[str, list[str]]:
    """For each match, scramble the score and odds of every match that kicked off less than
    FINISHED_AFTER before it, or later, the match itself included, and keep the stage-3
    columns of the match that moved. Only those matches' fixtures (teams, kickoff, round) may
    be read, so nothing may move."""

    before_df = derive(_stage_2(rows))

    leaks: dict[str, list[str]] = {}
    for target in rows:
        cutoff = _kickoff(target) - FINISHED_AFTER
        scrambled = [
            {**row, **_results_and_odds(rng)} if _kickoff(row) > cutoff else row for row in rows
        ]

        moved = _differing(before_df, derive(_stage_2(scrambled)), str(target["match_id"]))
        if moved:
            leaks[str(target["match_id"])] = moved

    return leaks


def test_no_score_or_odds_of_an_unfinished_match_reaches_a_row() -> None:
    assert _leaks(_made_up_season(), random.Random(11)) == {}


# A double round robin of four teams: six rounds of two matches, as (round, home, away).
_FIRST_LEG = [[(1, 4), (2, 3)], [(1, 3), (4, 2)], [(1, 2), (3, 4)]]
_SECOND_LEG = [[(away, home) for home, away in pairs] for pairs in _FIRST_LEG]
_FIXTURES = [
    (number, home, away)
    for number, pairs in enumerate([*_FIRST_LEG, *_SECOND_LEG], 1)
    for home, away in pairs
]
# From one kickoff to the next: anything up to 10 days, or the last gap at which the earlier
# match is still unfinished. Only a gap under FINISHED_AFTER can show a leak: two matches
# further apart are both finished, so neither is scrambled. The unit tests above check the
# longer windows.
_LAST_UNFINISHED = FINISHED_AFTER - timedelta(minutes=1)
_GAPS = st.one_of(
    st.just(_LAST_UNFINISHED),
    st.integers(0, 10 * 24 * 60).map(lambda minutes: timedelta(minutes=minutes)),
)
_STARTS = st.datetimes(datetime(2023, 1, 1), datetime(2026, 12, 31), timezones=st.just(UTC)).map(
    lambda moment: moment.replace(second=0, microsecond=0)
)


@given(
    start=_STARTS,
    gaps=st.lists(_GAPS, min_size=len(_FIXTURES), max_size=len(_FIXTURES)),
    order=st.permutations(range(len(_FIXTURES))),
    seed=st.integers(0, 2**32 - 1),
)
def test_no_score_or_odds_of_an_unfinished_match_reaches_a_row_of_a_generated_season(
    start: datetime, gaps: list[timedelta], order: list[int], seed: int
) -> None:
    # Kickoffs a generated gap apart, dealt to the fixtures in a generated order: round-mates
    # at once or days apart, matches played out of their round, and matches one minute short
    # of finished.
    kickoffs = [start + sum(gaps[: slot + 1], timedelta()) for slot in range(len(gaps))]

    rng = random.Random(seed)
    rows = [
        {
            **_match(f"m{i}", kickoffs[slot], (home, away), (0, 0), round_number=number),
            **_results_and_odds(rng),
        }
        for i, ((number, home, away), slot) in enumerate(zip(_FIXTURES, order, strict=True))
    ]

    assert _leaks(rows, rng) == {}


def test_the_leak_check_can_fail() -> None:
    # The check above is not empty: scrambling the matches that had finished before the last
    # kickoff does move the last match's values.
    rows = _made_up_season()
    before_df = derive(_stage_2(rows))

    last = max(rows, key=_kickoff)
    cutoff = _kickoff(last) - FINISHED_AFTER

    rng = random.Random(11)
    scrambled = [
        {**row, **_results_and_odds(rng)} if _kickoff(row) <= cutoff else row for row in rows
    ]

    after_df = derive(_stage_2(scrambled))

    assert _differing(before_df, after_df, str(last["match_id"]))
