"""`analysis/schedule/whole_corpus/all/stakes.py`: the trailing states, the flags and the bar."""

import math

import numpy as np
import pandas as pd
import pytest

from analysis.schedule.whole_corpus.all import stakes as runner


@pytest.fixture
def matches_df() -> pd.DataFrame:
    """Four matches of one league-season. Half-time 0-1 (home behind, wins), 2-0 (away behind
    by 2), 1-1 (no one behind) and 0-1 with no odds."""

    league_season_df = pd.DataFrame(
        {
            "s1_league_id": 7,
            "s1_season": "2024-2025",
            "season_cohort": 2024,
            "s1_ht_home_goals": [0, 2, 1, 0],
            "s1_ht_away_goals": [1, 0, 1, 1],
            "s2_mkt_p_home": [0.6, 0.5, 0.4, np.nan],
            "s2_mkt_p_away": [0.2, 0.3, 0.35, np.nan],
            "s2_is_comeback_home": [True, False, False, False],
            "s2_is_comeback_away": [False, False, False, False],
        }
    )

    for side, left, above, change in (
        ("home", [4, 9, 9, 3], [2, 1, 1, 1], [3, 0, 0, 0]),
        ("away", [12, 5, 5, 3], [8, np.nan, 1, 1], [0, np.nan, 0, 0]),
    ):
        league_season_df[f"s3_{side}_pre_matches_left"] = left
        league_season_df[f"s3_{side}_pre_pts_to_above"] = above
        league_season_df[f"s3_{side}_rank_change_since_open"] = change

    return league_season_df


def test_fifth_cuts_pool_the_home_and_away_chances_of_priced_matches(
    matches_df: pd.DataFrame,
) -> None:
    chances = [0.6, 0.5, 0.4, 0.2, 0.3, 0.35]
    assert runner.fifth_cuts(matches_df) == pytest.approx(np.quantile(chances, runner.FIFTHS))


def test_trailing_states_read_the_side_behind(matches_df: pd.DataFrame) -> None:
    cuts = np.array([0.25, 0.35, 0.45, 0.55])

    states_df = runner.trailing_states(matches_df, cuts)

    assert states_df.index.tolist() == [0, 1]  # no one behind in match 2, no odds in match 3
    assert states_df["p_win"].tolist() == [0.6, 0.3]
    assert states_df["win"].tolist() == [True, False]
    assert states_df["deficit"].tolist() == ["1", "2+"]
    assert states_df["left"].tolist() == [4, 5]
    assert states_df["stratum"].tolist() == ["7 2024-2025|4|1", "7 2024-2025|1|2+"]


def test_late_and_close_needs_both_and_a_team_above() -> None:
    states_df = pd.DataFrame({"left": [5, 6, 5, 5], "above": [3, 3, 4, np.nan]}, index=[0, 1, 2, 3])
    assert runner.late_and_close(states_df)["flag"].tolist() == [True, False, False, False]


def test_fell_since_open_leaves_out_the_rows_without_a_rank_change() -> None:
    states_df = pd.DataFrame({"change": [2.0, 1.0, np.nan, -3.0]})
    flagged_df = runner.fell_since_open(states_df)
    assert flagged_df.index.tolist() == [0, 1, 3]
    assert flagged_df["flag"].tolist() == [True, False, False]


def _states(cohort: int, flag: list[bool], win: list[bool]) -> pd.DataFrame:
    return pd.DataFrame(
        {"season_cohort": cohort, "flag": flag, "win": win, "stratum": f"s{cohort}"}
    )


def test_mh_table_gives_each_cohort_then_all_pooled() -> None:
    states_df = pd.concat(
        [
            _states(2024, [True] * 4 + [False] * 4, [True, False, False, False] * 2),
            _states(2025, [True] * 4 + [False] * 4, [True, True, False, False, True] + [False] * 3),
        ],
        ignore_index=True,
    )

    mh_table_df = runner.mh_table(states_df)

    assert mh_table_df["states"].tolist() == ["2024", "2025", "pooled"]
    assert mh_table_df["flagged"].tolist() == [4, 4, 8]
    assert float(mh_table_df.at[0, "MH OR"]) == pytest.approx(1.0)
    assert float(mh_table_df.at[1, "MH OR"]) == pytest.approx((2 * 3) / (2 * 1))
    assert float(mh_table_df.at[2, "rest rate"]) == pytest.approx(2 / 8)


def test_the_bar_needs_a_small_holm_p_and_the_same_side_in_both_cohorts() -> None:
    def table(first: float, second: float, p_value: float) -> pd.DataFrame:
        return pd.DataFrame({"MH OR": [first, second, math.nan], "CMH p": [0.5, 0.5, p_value]})

    tables = {
        "both up": table(1.4, 1.2, 0.01),
        "split": table(1.4, 0.9, 0.001),
        "weak": table(1.1, 1.1, 0.4),
    }

    bar_df = runner.the_bar(tables).set_index("flag")

    assert bar_df["Holm p"].tolist() == pytest.approx([0.02, 0.003, 0.4])
    assert bar_df["same side"].tolist() == [True, False, True]
    assert bar_df["met"].tolist() == [True, False, False]


def test_against_odds_reads_the_flagged_and_the_rest_against_the_yardstick() -> None:
    states_df = pd.DataFrame(
        {
            "flag": [True, True, False, False, False],
            "win": [True, False, True, False, False],
            "cluster": ["a", "b", "a", "b", "b"],
        }
    )
    chance = pd.Series([0.25, 0.25, 0.1, 0.1, np.nan])

    against_odds_df = runner.against_odds(states_df, chance).set_index("states")

    assert float(against_odds_df.at["flagged", "oe"]) == pytest.approx(1 / 0.5)
    assert float(against_odds_df.at["rest", "oe"]) == pytest.approx(1 / 0.2)
    assert float(against_odds_df.at["rest", "n"]) == 2.0
