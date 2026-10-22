"""`analysis/schedule/whole_corpus/all/season_phase.py`: the phases, the readings and the tests."""

import numpy as np
import pandas as pd
import pytest

from analysis.schedule.whole_corpus.all import season_phase as runner


def stage_matches(rounds: int, stage: object = "League") -> pd.DataFrame:
    """One match per round of one stage, kicked off a week apart in round order."""
    return pd.DataFrame(
        {
            "s1_league_id": 1,
            "s1_season": "2024-2025",
            "s1_stage": stage,
            "s1_round": range(1, rounds + 1),
            "s1_date": [f"2024-08-{day:02d}T15:00:00+02:00" for day in range(1, rounds + 1)],
        }
    )


@pytest.fixture
def frame() -> pd.DataFrame:
    """Four league-seasons in two cohorts, 330 random matches each, in the columns that the
    runner reads: outcomes, yardstick chances, the phase and the round (1 and 2 for 650
    matches each, 3 for the other 20)."""
    rng = np.random.default_rng(0)
    size = 4 * 330
    ht_decisive = rng.random(size) < 0.6
    out = pd.DataFrame(
        {
            "is_comeback": (rng.random(size) < 0.08) & ht_decisive,
            "ht_decisive": ht_decisive,
            "seven": rng.random(size) < 0.05,
            "goals": rng.poisson(2.7, size),
            "m_cb": 0.04,
            "m_ht_decisive": 0.6,
            "m_completion": 0.07 * ht_decisive,
            "m_seven": 0.04,
            "m_goals": 2.7,
            "one": 1.0,
        }
    ).astype(float)

    out["cluster"] = np.repeat(["a 2024", "b 2024", "a 2025", "b 2025"], 330)
    out["season_cohort"] = np.repeat([2024, 2024, 2025, 2025], 330)
    out["third"] = np.tile(np.repeat([1, 2, 3], 110), 4)
    out["round"] = np.r_[np.repeat([1, 2], 650), np.full(20, 3)]

    return runner.with_league_season(out)


def test_phases_split_a_stage_into_thirds_by_round_and_by_kickoff() -> None:
    matches = stage_matches(9)
    # Round 1's match was put off until after round 9.
    matches.loc[0, "s1_date"] = "2024-08-20T15:00:00+02:00"

    phases = runner.phases(matches)

    assert phases["rounds"].tolist() == [9] * 9
    assert phases["third"].tolist() == [1, 1, 1, 2, 2, 2, 3, 3, 3]
    assert phases["third_kickoff"].tolist() == [3, 1, 1, 1, 2, 2, 2, 3, 3]
    first, middle, last = runner.EDGES
    assert phases["edge"].tolist() == [first] * 3 + [middle] * 3 + [last] * 3


def test_phases_count_the_rounds_of_each_stage_on_its_own() -> None:
    apertura = stage_matches(3, "Apertura")
    clausura = stage_matches(6, "Clausura")
    no_tabs = stage_matches(2, np.nan).assign(s1_league_id=2)
    phases = runner.phases(pd.concat([apertura, clausura, no_tabs], ignore_index=True))
    assert phases["rounds"].tolist() == [3] * 3 + [6] * 6 + [2] * 2
    assert phases["third"].tolist() == [1, 2, 3, 1, 1, 2, 2, 3, 3, 2, 3]


def test_the_league_season_reading_expects_what_each_league_season_has(
    frame: pd.DataFrame,
) -> None:
    for quantity in runner.QUANTITIES:
        observed, denominator, _, label, _ = quantity
        expected = frame[runner.league_season_column(label)]
        sums = pd.DataFrame({"observed": frame[observed], "expected": expected})
        sums = sums.groupby(frame["cluster"]).sum()

        assert sums["expected"].to_numpy() == pytest.approx(sums["observed"].to_numpy())
        assert (expected[frame[denominator] == 0] == 0).all()


def test_readings_are_raw_then_the_league_season_then_the_odds() -> None:
    link_2 = runner.QUANTITIES[2]
    assert runner.readings(link_2) == (
        ("raw", "ht_decisive"),
        ("league-season", "league-season link 2: the team behind wins"),
        ("odds", "m_completion"),
    )


def test_phase_values_give_each_reading_per_phase(frame: pd.DataFrame) -> None:
    comeback = runner.QUANTITIES[0]
    table = runner.phase_values(frame, "third", comeback).set_index("phase")

    assert table.index.tolist() == [1, 2, 3]

    part = frame[frame["third"] == 1]
    assert float(table.at[1, "count"]) == part["is_comeback"].sum()
    assert float(table.at[1, "raw"]) == pytest.approx(part["is_comeback"].mean())
    assert float(table.at[1, "odds"]) == pytest.approx(
        part["is_comeback"].sum() / part["m_cb"].sum()
    )
    assert (table["raw low"] <= table["raw"]).all()
    assert (table["odds"] <= table["odds high"]).all()


def test_phase_tests_give_one_test_per_quantity_and_reading(frame: pd.DataFrame) -> None:
    table = runner.phase_tests(frame, "third")
    assert len(table) == 3 * len(runner.QUANTITIES)
    assert (table["df"] == 2).all()


def test_phase_tests_find_nothing_when_the_phases_are_equal(frame: pd.DataFrame) -> None:
    # Each phase gets the outcomes of the first one, so every phase value is the same.
    first = frame[frame["third"] == 1].reset_index(drop=True)
    equal = pd.concat([first.assign(third=third) for third in (1, 2, 3)], ignore_index=True)
    table = runner.phase_tests(equal, "third")
    assert table["Q"].to_numpy() == pytest.approx(0.0, abs=1e-9)


def test_common_rounds_leave_out_the_rounds_of_few_matches(frame: pd.DataFrame) -> None:
    assert runner.common_rounds(frame)["round"].unique().tolist() == [1, 2]


def test_round_summary_reads_each_round_quantity_three_ways(frame: pd.DataFrame) -> None:
    table = runner.round_summary(runner.common_rounds(frame))
    assert len(table) == 3 * len(runner.ROUND_QUANTITIES)
    assert table["quantity"].iloc[0] == "comeback, raw"
