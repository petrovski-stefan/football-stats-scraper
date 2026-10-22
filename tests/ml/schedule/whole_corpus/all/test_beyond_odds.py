"""`ml/schedule/whole_corpus/all/beyond_odds.py`: the rows of a split, the models, the scaled
yardstick, the SHAP table and the tuning table."""

import numpy as np
import pandas as pd
import pytest

from analysis.methods import yardstick
from ml import boosting, rows
from ml.schedule.whole_corpus.all import beyond_odds as runner

COARSE = np.round(np.arange(0.1, 4.01, 0.1), 2)


def test_split_rows_read_no_goal_of_the_test_cohort(toy_schedule: pd.DataFrame) -> None:
    grid = yardstick.build_grid(COARSE)
    side_rows, fields_b, share = runner.split_rows(toy_schedule, grid, 2024)

    train = toy_schedule[toy_schedule["season_cohort"] == 2024]
    assert share == pytest.approx(yardstick.first_half_share(yardstick.priced(train)))

    # More first-half goals in the 2025 cohort change no field of any row.
    changed = toy_schedule.copy()
    later = changed["season_cohort"] == 2025
    changed.loc[later, "s2_goals_1h"] += 3
    changed.loc[later, "s2_total_goals"] += 3

    again, _, _ = runner.split_rows(changed, grid, 2024)

    pd.testing.assert_frame_equal(side_rows[fields_b], again[fields_b])


def test_models_read_the_odds_then_every_field() -> None:
    fields_b = [*rows.ODDS, "T_ft_total_rank", rows.LEAGUE]
    models = runner.models(fields_b)
    assert models["A"] == list(rows.ODDS)
    assert models["B"] == fields_b
    assert models[runner.NO_LEAGUE] == [*rows.ODDS, "T_ft_total_rank"]


def test_yardstick_chance_is_scaled_to_the_training_rows() -> None:
    train = pd.DataFrame({rows.TARGET: [1.0, 0.0, 1.0, 0.0], runner.YARDSTICK: 0.25})
    test = pd.DataFrame({runner.YARDSTICK: [0.1, 0.2]})
    # The training rows have 2 comebacks against 1 expected: O/E 2.
    assert runner.yardstick_chance(train, test).tolist() == pytest.approx([0.2, 0.4])


def test_importance_ranks_the_fields_and_marks_the_odds() -> None:
    shap = pd.DataFrame({"p_T": [0.3, -0.3], "T_ft_total_rank": [0.1, 0.0]})
    table = runner.importance(shap)
    assert table["field"].tolist() == ["p_T", "T_ft_total_rank"]
    assert table["share"].sum() == pytest.approx(1.0)
    assert table["odds"].tolist() == [True, False]
    assert table["mean |SHAP|"].tolist() == pytest.approx([0.3, 0.05])


def test_tuning_table_shows_the_chosen_setting_of_each_model() -> None:
    setting = boosting.GRID[0]
    tuned = boosting.Tuned(
        params=boosting.BASE | setting, trees=42, cv_loss=0.118, table=pd.DataFrame()
    )

    table = runner.tuning_table({"A": tuned})

    assert table["model"].tolist() == ["A"]
    assert table["trees"].tolist() == [42]
    assert set(setting) <= set(table.columns)
    assert np.isclose(table["cv loss"].iloc[0], 0.118)
