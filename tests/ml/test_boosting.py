"""`ml/boosting.py`: the folds of whole groups, the tuning, the fit and the SHAP values."""

import numpy as np
import pandas as pd
import pytest

from ml import boosting

SMALL_GRID = ({"num_leaves": 4, "min_data_in_leaf": 50, "feature_fraction": 1.0},)


@pytest.fixture
def signal_df() -> pd.DataFrame:
    """3,000 rows in 20 groups. The event has the chance 0.4 when `x` is above 0.8, and 0.02
    otherwise. `noise` tells nothing."""
    rng = np.random.default_rng(0)
    size = 3000
    signal_feature = rng.random(size)
    signal_rows_df = pd.DataFrame({"x": signal_feature, "noise": rng.random(size)})
    signal_rows_df["y"] = (rng.random(size) < np.where(signal_feature > 0.8, 0.4, 0.02)).astype(
        float
    )
    signal_rows_df["group"] = np.repeat([f"g{i:02d}" for i in range(20)], size // 20)

    return signal_rows_df


def test_group_folds_put_each_group_in_one_test_fold() -> None:
    groups = pd.Series(["a", "a", "b", "c", "c", "d", "e"])

    folds = boosting.group_folds(groups, fold_count=2)

    assert len(folds) == 2
    tested = np.concatenate([test for _, test in folds])
    assert sorted(tested.tolist()) == list(range(len(groups)))
    for train, test in folds:
        assert not set(groups.iloc[train]) & set(groups.iloc[test])


def test_tune_fit_and_predict_find_a_clear_signal(signal_df: pd.DataFrame) -> None:
    fields = ["x", "noise"]
    tuned = boosting.tune(
        signal_df, fields, "y", signal_df["group"], grid=SMALL_GRID, max_trees=300
    )

    assert tuned.trees > 0
    assert tuned.params["num_leaves"] == 4
    assert len(tuned.table) == len(SMALL_GRID)

    booster = boosting.fit(signal_df, fields, "y", tuned)
    chance = boosting.predict(booster, signal_df, fields)
    high = signal_df["x"].to_numpy() > 0.8

    assert chance[high].mean() > 5 * chance[~high].mean()


def test_contributions_name_the_field_that_carries_the_signal(signal_df: pd.DataFrame) -> None:
    fields = ["x", "noise"]
    tuned = boosting.tune(
        signal_df, fields, "y", signal_df["group"], grid=SMALL_GRID, max_trees=300
    )
    booster = boosting.fit(signal_df, fields, "y", tuned)
    shap_df = boosting.contributions(booster, signal_df, fields)

    assert list(shap_df.columns) == fields
    assert shap_df["x"].abs().mean() > 5 * shap_df["noise"].abs().mean()

    # With LightGBM's constant, the values sum to the log odds of each row's chance.
    chance = boosting.predict(booster, signal_df, fields)
    log_odds = np.log(chance / (1 - chance))
    constant = log_odds - shap_df.sum(axis=1).to_numpy()
    assert np.allclose(constant, constant[0])
