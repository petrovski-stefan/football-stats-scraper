"""`analysis/schedule/whole_corpus/all/odds_groups.py`: the groups, the null and the tests."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import poisson

from analysis import corpus
from analysis.methods import shin, yardstick
from analysis.schedule.whole_corpus.all import odds_groups as runner

PRICES = [1.9, 3.5, 4.0, 2.5, 1.9, 1.9, 0.5, 1.9, 1.9]  # 1X2, O/U, AH


def priced_matches() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Four matches and the yardstick frame of the first three of them.

    Matches 1 and 2 have the same nine prices. Match 3 has their 1X2 prices but another AH
    price, and a home chance in the next band. Match 4 has no AH market.
    """
    rows = [PRICES, PRICES, [*PRICES[:8], 2.0], PRICES]
    matches = pd.DataFrame(rows, columns=[*shin.ODDS, *yardstick.OU, *corpus.AH])
    matches.loc[3, corpus.AH] = np.nan
    matches["s2_mkt_p_home"] = [0.52, 0.52, 0.54, 0.52]
    matches["s2_mkt_p_away"] = 0.25
    matches["season_cohort"] = [2024, 2024, 2025, 2025]
    matches["s1_league_name"] = ["a", "b", "a", "b"]
    model = pd.DataFrame(
        {
            "is_comeback": [1.0, 0.0, 1.0, 0.0],
            "m_cb": 0.05,
            "seven": 0.0,
            "m_seven": 0.02,
            "cluster": ["a 2024", "b 2024", "a 2025", "b 2025"],
        }
    )
    return matches, model


def test_group_frame_keeps_the_matches_with_an_ah_market_and_groups_them() -> None:
    matches, model = priced_matches()
    frame = runner.group_frame(matches, model)
    assert frame.index.tolist() == [0, 1, 2]
    exact_1x2, exact_9, near = (
        frame[name]
        for name in ("exact 1X2 prices", "exact 9 prices", "1X2 chances to 0.05 and O/U line")
    )
    assert exact_1x2.nunique() == 1
    assert exact_9[0] == exact_9[1] != exact_9[2]
    assert near[0] == near[1] != near[2]  # 0.52 is band 10, 0.54 band 11
    assert frame["AH line and O/U line"].nunique() == 1
    assert frame["league"].tolist() == ["a", "b", "a"]


def test_the_null_chances_add_up_to_the_observed_count() -> None:
    events = pd.Series([1.0, 0.0, 1.0, 1.0])
    expected = pd.Series([0.1, 0.2, 0.3, 0.4])
    chance = runner.null_chance(events, expected)
    assert chance.sum() == pytest.approx(3.0)
    assert chance / expected.to_numpy() == pytest.approx(np.full(4, 3.0))


def test_group_sizes_count_the_groups_and_their_shared_matches() -> None:
    frame = pd.DataFrame({name: [0, 0, 0, 1, 2] for name, _ in runner.GROUPINGS})
    table = runner.group_sizes(frame)
    assert table.iloc[0].to_dict() == {
        "grouping": "exact 1X2 prices",
        "groups": 3,
        "groups of 2+": 1,
        "matches in them": 3,
        "largest": 3,
    }


def test_group_stats_count_crowded_groups_and_the_smallest_tail() -> None:
    groups = np.array([0, 0, 0, 1, 1, 2])
    events = np.array([1.0, 1.0, 1.0, 1.0, 1.0, 0.0])
    expected = np.array([0.5, 1.0, 0.2])
    stats = runner.group_stats(groups, events, expected)
    assert stats["2 or more"] == 2.0
    assert stats["3 or more"] == 1.0
    assert stats[runner.SMALLEST_TAIL] == pytest.approx(float(poisson.sf(2, 0.5)))
    no_events = runner.group_stats(groups, np.zeros(6), expected)
    assert no_events[runner.SMALLEST_TAIL] == 1.0


def test_against_null_finds_nothing_when_the_outcomes_are_certain() -> None:
    groups = np.array([0, 0, 1, 1, 2])
    chance = np.array([1.0, 1.0, 1.0, 0.0, 0.0])
    table = runner.against_null(groups, chance.copy(), chance, draws=20).set_index("statistic")
    assert table["observed"].tolist() == [1.0, 0.0, float(poisson.sf(1, 2.0))]
    assert (table["null low"] == table["observed"]).all()
    assert (table["p"] == 1.0).all()


def test_group_table_gives_each_group_its_prices_counts_and_leagues() -> None:
    frame = pd.DataFrame(
        {
            "g": [0, 0, 1],
            shin.ODDS[0]: [1.9, 1.9, 2.5],
            shin.ODDS[1]: [3.5, 3.5, 3.2],
            shin.ODDS[2]: [4.0, 4.0, 2.8],
            "is_comeback": [1.0, 1.0, 0.0],
            "league": ["b", "a", "a"],
        }
    )
    frame["exact 1X2 prices"] = frame["g"]
    table = runner.group_table(frame, "exact 1X2 prices", "is_comeback", np.array([0.1, 0.2, 0.3]))
    first = table.loc[0]
    assert float(first[shin.ODDS[0]]) == 1.9
    assert (int(first["matches"]), float(first["events"])) == (2, 2.0)
    assert float(first["expected"]) == pytest.approx(0.3)
    assert float(first["tail p"]) == pytest.approx(float(poisson.sf(1, 0.3)))
    assert (int(first["leagues"]), first["league names"]) == (2, "a, b")
    assert float(table.at[1, "tail p"]) == 1.0


def test_large_groups_keep_the_groups_with_enough_expected_events() -> None:
    frame = pd.DataFrame({"g": [0, 0, 1], "m_cb": [3.0, 2.0, 4.9]})
    assert runner.large_groups(frame, "g", "m_cb").index.tolist() == [0, 1]


def test_carry_over_reads_the_top_groups_of_one_cohort_in_the_other() -> None:
    # Five groups with 4 expected events in each cohort; group 0 runs hot in both. Group 5
    # has too few expected events in 2025 to count.
    observed = {2024: [8, 4, 4, 4, 4, 9], 2025: [6, 4, 4, 4, 4, 1]}
    expected = {2024: [4.0] * 6, 2025: [4.0] * 5 + [1.0]}
    frame = pd.DataFrame(
        [
            {
                "g": g,
                "season_cohort": cohort,
                "obs": observed[cohort][g],
                "exp": expected[cohort][g],
            }
            for cohort in (2024, 2025)
            for g in range(6)
        ]
    )
    table = runner.carry_over(frame, "g", "obs", "exp").set_index("chosen in")
    first = table.loc[2024]
    assert (int(first["groups"]), int(first["chosen"])) == (5, 1)
    assert float(first["O/E where chosen"]) == pytest.approx(2.0)
    assert float(first["O/E in the other"]) == pytest.approx(1.5)
    assert float(first["O/E of all in the other"]) == pytest.approx(22 / 20)
    assert float(table.at[2025, "O/E in the other"]) == pytest.approx(2.0)


def test_carry_over_needs_two_cohorts() -> None:
    frame = pd.DataFrame({"g": [0], "season_cohort": [2024], "obs": [1.0], "exp": [4.0]})
    assert runner.carry_over(frame, "g", "obs", "exp").empty
