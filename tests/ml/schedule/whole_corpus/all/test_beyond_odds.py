"""`ml/schedule/whole_corpus/all/beyond_odds.py`: the rows of a split, the models, the scaled
yardstick, the SHAP table and the tuning table."""

from functools import partial

import numpy as np
import pandas as pd
import pytest

from analysis.methods import yardstick
from ml import boosting, rows
from ml.schedule.whole_corpus.all import beyond_odds as runner

COARSE = np.round(np.arange(0.1, 4.01, 0.1), 2)
# One small setting and few trees: the real grid takes too long on a test table.
SMALL_GRID = ({"num_leaves": 4, "min_data_in_leaf": 50, "feature_fraction": 1.0},)
FIELDS_B = [*rows.ODDS, "T_ft_total_rank", rows.LEAGUE]


@pytest.fixture
def quick_tuning(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make `boosting.tune` try `SMALL_GRID` only, with at most 20 trees."""

    monkeypatch.setattr(boosting, "tune", partial(boosting.tune, grid=SMALL_GRID, max_trees=20))


@pytest.fixture
def random_side_rows_df() -> pd.DataFrame:
    """800 side rows with random values for `FIELDS_B`, a comeback rate near 0.2 and a flat
    yardstick chance. Each cohort, 2024 and 2025, has 8 league-seasons of 50 rows."""

    rng = np.random.default_rng(0)
    size = 800
    side_rows_df = pd.DataFrame(rng.random((size, len(FIELDS_B) - 1)), columns=FIELDS_B[:-1])
    side_rows_df[rows.LEAGUE] = pd.Categorical(np.tile([1, 2], size // 2))
    side_rows_df[rows.TARGET] = (rng.random(size) < 0.2).astype(float)
    side_rows_df[runner.YARDSTICK] = 0.2
    side_rows_df["cluster"] = np.repeat([f"c{i}" for i in range(16)], size // 16)
    side_rows_df["season_cohort"] = np.repeat([2024, 2025], size // 2)

    return side_rows_df


def test_split_rows_read_no_goal_of_the_test_cohort(toy_schedule_df: pd.DataFrame) -> None:
    grid = yardstick.build_grid(COARSE)
    split = runner.split_rows(toy_schedule_df, grid, 2024)

    train_df = toy_schedule_df[toy_schedule_df["season_cohort"] == 2024]
    assert split.first_half_share == pytest.approx(
        yardstick.first_half_share(yardstick.priced(train_df))
    )

    # More first-half goals in the 2025 cohort change no field of any row.
    changed_schedule_df = toy_schedule_df.copy()
    later = changed_schedule_df["season_cohort"] == 2025
    changed_schedule_df.loc[later, "s2_goals_1h"] += 3
    changed_schedule_df.loc[later, "s2_total_goals"] += 3

    rebuilt = runner.split_rows(changed_schedule_df, grid, 2024)

    pd.testing.assert_frame_equal(
        split.side_rows_df[split.fields_b], rebuilt.side_rows_df[split.fields_b]
    )


def test_models_read_the_odds_then_every_field() -> None:
    fields_b = [*rows.ODDS, "T_ft_total_rank", rows.LEAGUE]
    models = runner.models(fields_b)
    assert models["A"] == list(rows.ODDS)
    assert models["B"] == fields_b
    assert models[runner.NO_LEAGUE] == [*rows.ODDS, "T_ft_total_rank"]


@pytest.mark.usefixtures("quick_tuning")
def test_fit_models_fit_each_model_on_its_own_fields(random_side_rows_df: pd.DataFrame) -> None:
    train_df = random_side_rows_df[random_side_rows_df["season_cohort"] == 2024]

    fitted = runner.fit_models(train_df, FIELDS_B)

    assert list(fitted) == ["A", "B", runner.NO_LEAGUE]
    for name, model in fitted.items():
        assert model.booster.feature_name() == model.fields, name


@pytest.mark.usefixtures("quick_tuning")
def test_run_split_prints_every_table_of_the_split(
    random_side_rows_df: pd.DataFrame, capsys: pytest.CaptureFixture[str]
) -> None:
    runner.run_split(random_side_rows_df, FIELDS_B, 2024, 2025)

    printed = capsys.readouterr().out
    titles = [
        "the chosen settings",
        "log loss",
        "comebacks in the top N",
        "calibration of A",
        "calibration of B",
        "the fields of B by mean |SHAP|",
        f"the fields of {runner.NO_LEAGUE} by mean |SHAP|",
    ]
    for title in titles:
        assert f"fit on 2024, scored on 2025: {title}" in printed, title


def test_yardstick_chance_is_scaled_to_the_training_rows() -> None:
    train_df = pd.DataFrame({rows.TARGET: [1.0, 0.0, 1.0, 0.0], runner.YARDSTICK: 0.25})
    test_df = pd.DataFrame({runner.YARDSTICK: [0.1, 0.2]})
    # The training rows have 2 comebacks against 1 expected: O/E 2.
    assert runner.yardstick_chance(train_df, test_df).tolist() == pytest.approx([0.2, 0.4])


def test_importance_ranks_the_fields_and_marks_the_odds() -> None:
    shap_df = pd.DataFrame({"p_T": [0.3, -0.3], "T_ft_total_rank": [0.1, 0.0]})
    importance_df = runner.importance(shap_df)
    assert importance_df["field"].tolist() == ["p_T", "T_ft_total_rank"]
    assert importance_df["share"].sum() == pytest.approx(1.0)
    assert importance_df["odds"].tolist() == [True, False]
    assert importance_df["mean |SHAP|"].tolist() == pytest.approx([0.3, 0.05])


def test_tuning_table_shows_the_chosen_setting_of_each_model() -> None:
    setting = boosting.GRID[0]
    tuned = boosting.Tuned(
        params=boosting.BASE | setting, trees=42, cv_loss=0.118, settings_df=pd.DataFrame()
    )

    tuning_df = runner.tuning_table({"A": tuned})

    assert tuning_df["model"].tolist() == ["A"]
    assert tuning_df["trees"].tolist() == [42]
    assert set(setting) <= set(tuning_df.columns)
    assert np.isclose(tuning_df["cv loss"].iloc[0], 0.118)
