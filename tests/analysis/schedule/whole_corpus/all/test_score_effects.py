"""`analysis/schedule/whole_corpus/all/score_effects.py`: states, team rows and the gap table."""

import numpy as np
import pandas as pd
import pytest

from analysis.methods import yardstick
from analysis.schedule.whole_corpus.all import score_effects as runner

SHARE = 0.4


@pytest.fixture
def toy_frame() -> pd.DataFrame:
    """Four matches in the shape `yardstick.frame` gives: HT 1-0, 0-2, 0-0 and 1-1."""
    frame = pd.DataFrame(
        {
            "ht_margin": [1, -2, 0, 0],
            "fav_is_home": [True, False, True, False],
            "goals_home_1h": [1.0, 0.0, 0.0, 1.0],
            "goals_away_1h": [0.0, 2.0, 0.0, 1.0],
            "goals_home": [2.0, 1.0, 0.0, 2.0],
            "goals_away": [0.0, 3.0, 1.0, 1.0],
            "lam_home": [1.5, 1.0, 1.2, 1.4],
            "lam_away": [1.0, 1.4, 1.1, 1.3],
            "is_comeback": [0.0, 0.0, 0.0, 0.0],
            "season_cohort": [2024, 2024, 2025, 2025],
            "cluster": ["a", "a", "b", "b"],
        }
    )
    frame["goals_1h"] = frame["goals_home_1h"] + frame["goals_away_1h"]
    frame["goals_2h"] = frame["goals_home"] + frame["goals_away"] - frame["goals_1h"]
    frame["m_goals_2h"] = (1 - SHARE) * (frame["lam_home"] + frame["lam_away"])
    return frame


def test_state_of_names_each_margin() -> None:
    names = runner.state_of(np.array([-5, -2, -1, 0, 1, 2, 4]))
    assert names.tolist() == list(runner.STATES)


def test_team_halves_mirror_each_match(toy_frame: pd.DataFrame) -> None:
    teams = runner.team_halves(toy_frame, SHARE)
    assert len(teams) == 8
    assert teams["state"].tolist()[:2] == ["ahead by 1", "behind by 2"]
    assert teams["state"].tolist()[4:6] == ["behind by 1", "ahead by 2"]
    assert teams["goals_2h"].tolist() == [1.0, 1.0, 0.0, 1.0, 0.0, 1.0, 1.0, 0.0]
    assert teams["expected_2h"].tolist()[0] == pytest.approx(0.6 * 1.5)
    assert teams["is_favourite"].tolist() == [True, False, True, False, False, True, False, True]


def test_by_state_keeps_the_order_and_skips_empty_states(toy_frame: pd.DataFrame) -> None:
    table = runner.by_state(runner.team_halves(toy_frame, SHARE))
    assert table["state"].tolist() == [
        "behind by 2",
        "behind by 1",
        "level",
        "ahead by 1",
        "ahead by 2",
    ]
    assert table.loc[table["state"] == "level", "n"].tolist() == [4.0]


def test_by_state_and_side_splits_favourite_and_underdog(toy_frame: pd.DataFrame) -> None:
    table = runner.by_state_and_side(runner.team_halves(toy_frame, SHARE))
    assert set(table["side"]) == {"favourite", "underdog"}
    assert table["n"].sum() == 8


def test_by_ht_score_covers_the_scores_that_occurred(toy_frame: pd.DataFrame) -> None:
    table = runner.by_ht_score(toy_frame, SHARE)
    assert table["score"].tolist() == ["0-0", "1-0", "1-1", "0-2"]
    one_nil = table[table["score"] == "1-0"].iloc[0]
    assert one_nil["home O/E"] == pytest.approx(1.0 / (0.6 * 1.5))


def test_by_first_half_goals_caps_the_groups(toy_frame: pd.DataFrame) -> None:
    capped = toy_frame.assign(goals_1h=[0.0, 2.0, 6.0, 4.0])
    table = runner.by_first_half_goals(capped)
    assert table["first-half goals"].tolist() == [0, 2, runner.FIRST_HALF_CAP]


def test_no_factors_give_the_basic_model(toy_frame: pd.DataFrame) -> None:
    basic = yardstick.completion_given_ht(
        toy_frame["lam_home"].to_numpy(),
        toy_frame["lam_away"].to_numpy(),
        SHARE,
        toy_frame["ht_margin"].to_numpy(),
    ).sum()
    assert runner.scaled_completions(toy_frame, SHARE, {}) == pytest.approx(basic)


def test_a_faster_trailing_side_completes_more_often(toy_frame: pd.DataFrame) -> None:
    basic = runner.scaled_completions(toy_frame, SHARE, {})
    faster = runner.scaled_completions(toy_frame, SHARE, {"behind by 1": 1.2, "behind by 2": 1.2})
    assert faster > basic


def test_gap_table_measures_against_the_basic_model(toy_frame: pd.DataFrame) -> None:
    frame = toy_frame.assign(is_comeback=[0.0, 1.0, 0.0, 0.0])
    table = runner.gap_table(frame, SHARE, {"behind by 2": 1.1, "ahead by 2": 0.9})
    assert table["factors"].tolist()[0] == "basic model"
    assert table["gap explained"].tolist()[0] == 0.0
    assert table["gap explained"].tolist()[3] > 0
