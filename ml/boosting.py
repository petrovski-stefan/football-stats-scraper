"""Gradient boosting for the ML test, with its settings tuned inside the training rows only.

LightGBM with the binary log loss (`notes/WORKING/PLAN_2026-10-19_ML_TEST.md`). `tune` picks
one setting of `GRID` and the number of trees by cross-validation over folds of whole
league-seasons of the training rows, with early stopping. `fit` then trains on all of them.
`contributions` gives the SHAP value of each field in each row (LightGBM's own TreeSHAP).
"""

from dataclasses import dataclass
from itertools import product
from typing import Any, cast

import lightgbm as lgb
import numpy as np
import pandas as pd

# The settings that `tune` does not search, chosen on 2026-10-19. The tuned models stopped after
# 54 to 146 trees, far below `MAX_TREES` (`notes/ML/SCHEDULE/WHOLE_CORPUS/ALL/BEYOND_ODDS.md`).
BASE: dict[str, Any] = {
    "objective": "binary",
    "learning_rate": 0.03,
    "lambda_l2": 10.0,
    "deterministic": True,
    "force_row_wise": True,
    "seed": 0,
    "num_threads": 4,
    "verbosity": -1,
}
# Small trees and large leaves: a comeback is a rare event (2.6% of the rows).
GRID: tuple[dict[str, Any], ...] = tuple(
    {"num_leaves": leaves, "min_data_in_leaf": leaf_rows, "feature_fraction": share}
    for leaves, leaf_rows, share in product((4, 8, 16), (300, 1000), (0.5, 1.0))
)
FOLDS = 4  # the folds of league-seasons, chosen on 2026-10-19
MAX_TREES = 3000  # the most trees of a model: see the comment of `BASE`
PATIENCE = 100  # early stopping: the trees after the best one that the search waits for
CV_LOSS = "valid binary_logloss-mean"


@dataclass(frozen=True)
class Tuned:
    """The chosen setting, its number of trees and cross-validated log loss, and every
    setting that was tried."""

    params: dict[str, Any]
    trees: int
    cv_loss: float
    settings_df: pd.DataFrame


def group_folds(
    groups: "pd.Series[Any]", fold_count: int = FOLDS
) -> list[tuple[np.ndarray, np.ndarray]]:
    """`fold_count` folds of whole groups (league-seasons). The groups go to the folds in turn,
    in the order of their names, so each group is in the test part of exactly one fold."""

    codes, names = pd.factorize(groups, sort=True)
    fold = (np.arange(len(names)) % fold_count)[codes]
    positions = np.arange(len(groups))

    return [(positions[fold != i], positions[fold == i]) for i in range(fold_count)]


def dataset(df: pd.DataFrame, fields: list[str], target: str) -> lgb.Dataset:
    """The rows as a LightGBM dataset. A categorical column stays categorical."""

    return lgb.Dataset(df[fields], label=df[target].to_numpy(dtype=float), free_raw_data=False)


def tune(
    df: pd.DataFrame,
    fields: list[str],
    target: str,
    groups: "pd.Series[Any]",
    grid: tuple[dict[str, Any], ...] = GRID,
    max_trees: int = MAX_TREES,
) -> Tuned:
    """The setting of `grid` with the lowest log loss over the folds of `groups`, and the
    number of trees where that loss was lowest."""

    train_set = dataset(df, fields, target)
    folds = group_folds(groups)

    tried = []
    for setting in grid:
        history = lgb.cv(
            BASE | setting,
            train_set,
            num_boost_round=max_trees,
            folds=folds,
            callbacks=[lgb.early_stopping(PATIENCE, verbose=False)],
        )

        # LightGBM types each value as a list of losses or a CVBooster; this key holds losses.
        losses = cast("list[float]", history[CV_LOSS])
        tried.append({**setting, "trees": len(losses), "cv loss": float(losses[-1])})

    settings_df = pd.DataFrame(tried)
    best = int(settings_df["cv loss"].idxmin())

    return Tuned(
        params=BASE | grid[best],
        trees=int(settings_df.at[best, "trees"]),
        cv_loss=float(settings_df.at[best, "cv loss"]),
        settings_df=settings_df,
    )


def fit(df: pd.DataFrame, fields: list[str], target: str, tuned: Tuned) -> lgb.Booster:
    """The model of the tuned setting, trained on all the rows."""

    return lgb.train(tuned.params, dataset(df, fields, target), num_boost_round=tuned.trees)


def predict(booster: lgb.Booster, df: pd.DataFrame, fields: list[str]) -> np.ndarray:
    """The chance of the target in each row."""

    return np.asarray(booster.predict(df[fields]), dtype=float)


def contributions(booster: lgb.Booster, df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    """The SHAP value of each field in each row, in log odds. With the constant that LightGBM
    adds (left out here), they sum to the log odds of the row's chance."""

    values = np.asarray(booster.predict(df[fields], pred_contrib=True), dtype=float)

    return pd.DataFrame(values[:, :-1], columns=fields, index=df.index)
