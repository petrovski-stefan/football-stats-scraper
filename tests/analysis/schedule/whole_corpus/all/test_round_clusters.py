"""`analysis/schedule/whole_corpus/all/round_clusters.py`: the readings, the tests, the days
from a round and the count tables."""

import pandas as pd
import pytest

from analysis import card
from analysis.schedule.whole_corpus.all import round_clusters as runner


def test_each_quantity_is_read_three_ways() -> None:
    comeback = card.ODDS_CARD[0]
    readings = runner.readings(comeback)
    assert [unit for _, unit, _ in readings] == [
        runner.EVERYTHING,
        runner.LEAGUE_SEASON,
        runner.LEAGUE_SEASON,
    ]
    assert [expected for *_, expected in readings] == ["one", "one", "m_cb"]
    assert readings[-1][0] == runner.ODDS_READING


def test_tests_give_one_row_per_quantity_and_reading(toy_rounds: pd.DataFrame) -> None:
    table = runner.tests(toy_rounds, draws=2)
    assert len(table) == 3 * len(card.ODDS_CARD)
    assert set(table["quantity"]) == {label for *_, label, _ in card.ODDS_CARD}
    odds = runner.tests(toy_rounds, only=(runner.ODDS_READING,), draws=2)
    assert odds["reading"].tolist() == [runner.ODDS_READING] * len(card.ODDS_CARD)


def test_largest_rounds_rank_the_parts_of_q(toy_rounds: pd.DataFrame) -> None:
    frame = toy_rounds.assign(league="toy")
    # One round gets many more goals than its odds expect.
    frame.loc[frame["round"] == "1 2024 3", "goals"] = 9.0
    goals = card.ODDS_CARD[-1]
    table = runner.largest_rounds(frame, goals, top=3)
    assert len(table) == 3
    assert table.loc[0, "round"] == "1 2024 3"
    assert table.loc[0, "matches"] == 8
    parts = table["part of Q"].tolist()
    assert parts == sorted(parts, reverse=True)


def test_days_from_round_measure_from_the_median_kickoff() -> None:
    kickoff = pd.to_datetime(
        pd.Series(
            [
                "2024-08-03T15:00+02:00",
                "2024-08-04T15:00+02:00",
                "2024-08-24T15:00+02:00",
                "2024-08-10T15:00+02:00",
                "2024-08-10T18:00+02:00",
            ]
        ),
        utc=True,
    )
    rounds = pd.Series(["r1", "r1", "r1", "r2", "r2"])
    days = runner.days_from_round(kickoff, rounds)
    assert days.tolist() == pytest.approx([1.0, 0.0, 20.0, 0.0625, 0.0625])


def test_league_season_chance_scales_the_odds_by_the_league_season() -> None:
    frame = pd.DataFrame(
        {
            runner.LEAGUE_SEASON: ["a", "a", "b", "b"],
            "seven": [1.0, 1.0, 0.0, 1.0],
            "m_seven": [0.5, 0.5, 0.25, 0.75],
        }
    )
    chances = runner.league_season_chance(frame, "seven", "m_seven")
    # League-season a has O/E 2, so its chances of 0.5 reach the cap of 1.
    assert chances.tolist() == pytest.approx([1.0, 1.0, 0.25, 0.75])


def test_count_table_expects_each_round_from_its_own_chances() -> None:
    rounds = pd.Series(["r1", "r1", "r2", "r2"])
    chances = pd.Series([0.5, 0.5, 0.0, 1.0])
    events = pd.Series([1.0, 1.0, 0.0, 1.0])
    table = runner.count_table(events, chances, rounds)
    assert table["events"].tolist() == ["0", "1", "2", "3", f"{runner.MOST}+"]
    assert table["rounds"].tolist() == [0, 1, 1, 0, 0]
    assert table["expected"].tolist() == pytest.approx([0.25, 1.5, 0.25, 0.0, 0.0])


def test_count_table_puts_large_counts_in_its_last_row() -> None:
    size = runner.MOST + 2
    rounds = pd.Series(["r1"] * size)
    table = runner.count_table(pd.Series([1.0] * size), pd.Series([1.0] * size), rounds)
    assert table["rounds"].tolist() == [0] * runner.MOST + [1]
    assert table["expected"].tolist() == pytest.approx([0.0] * runner.MOST + [1.0])
