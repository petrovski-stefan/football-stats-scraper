"""`ml/score.py`: the top N, the resampled sums, the log loss and the calibration."""

import numpy as np
import pandas as pd
import pytest

from ml import score


def test_top_mask_takes_the_highest_scores_and_keeps_the_row_order_in_a_tie() -> None:
    mask = score.top_mask(np.array([0.1, 0.9, 0.5, 0.9, 0.2]), 2)
    assert mask.tolist() == [False, True, False, True, False]
    tie = score.top_mask(np.array([0.5, 0.5, 0.5]), 1)
    assert tie.tolist() == [True, False, False]


def test_resampled_sums_resample_whole_clusters() -> None:
    values = np.array([[1.0, 1.0], [2.0, 1.0], [3.0, 1.0]])
    one = score.resampled_sums(values, pd.Series(["a", "a", "a"]), draws=5)
    assert one.tolist() == [[6.0, 3.0]] * 5

    two = score.resampled_sums(values, pd.Series(["a", "a", "b"]), draws=200)
    # Each resample holds two clusters: a + a, a + b, b + a or b + b.
    assert set(map(tuple, two.tolist())) <= {(6.0, 4.0), (6.0, 3.0), (6.0, 2.0)}
    assert set(two[:, 0].tolist()) == {6.0}


@pytest.fixture
def ranked() -> tuple[np.ndarray, dict[str, np.ndarray], "pd.Series[str]"]:
    """Ten rows in five clusters, three events. "perfect" ranks the events first, "flat"
    ranks by row order."""

    outcomes = np.array([1, 0, 0, 1, 0, 0, 1, 0, 0, 0], dtype=float)
    scores = {"flat": -np.arange(10, dtype=float), "perfect": outcomes + np.linspace(0, 0.1, 10)}
    clusters = pd.Series(np.repeat(["a", "b", "c", "d", "e"], 2))

    return outcomes, scores, clusters


def test_top_n_table_counts_the_hits_and_the_difference(
    ranked: tuple[np.ndarray, dict[str, np.ndarray], "pd.Series[str]"],
) -> None:
    outcomes, scores, clusters = ranked
    top_n_df = score.top_n_table(outcomes, scores, clusters, (3,), "flat", draws=200).set_index(
        "ranking"
    )

    assert top_n_df.at["perfect", "comebacks"] == 3.0
    assert top_n_df.at["flat", "comebacks"] == 1.0  # rows 0, 1 and 2
    assert top_n_df.at["perfect", "- flat"] == pytest.approx(2 / 3)
    assert top_n_df.at["flat", "- flat"] == 0.0
    assert top_n_df.at["flat", "random"] == pytest.approx(0.9)
    assert (
        top_n_df.at["perfect", "low"]
        <= top_n_df.at["perfect", "share"]
        <= top_n_df.at["perfect", "high"]
    )


def test_log_loss_rows_and_the_loss_table(
    ranked: tuple[np.ndarray, dict[str, np.ndarray], "pd.Series[str]"],
) -> None:
    outcomes, _, clusters = ranked
    assert score.log_loss_rows(np.array([1.0, 0.0]), np.array([0.5, 0.5])) == pytest.approx(
        [np.log(2), np.log(2)]
    )

    chances = {"base": np.full(10, 0.3), "better": np.where(outcomes == 1, 0.6, 0.15)}
    loss_df = score.loss_table(outcomes, chances, clusters, "base", draws=200).set_index("model")
    assert loss_df.at["better", "- base"] < 0
    assert loss_df.at["base", "O/E"] == pytest.approx(1.0)
    assert loss_df.at["base", "- base"] == 0.0


def test_calibration_table_has_groups_of_equal_size() -> None:
    chances = np.linspace(0.01, 0.2, 20)
    outcomes = np.zeros(20)
    outcomes[-2:] = 1.0

    calibration_df = score.calibration_table(outcomes, chances, bins=4)

    assert calibration_df["rows"].tolist() == [5, 5, 5, 5]
    assert calibration_df["rate"].tolist() == [0.0, 0.0, 0.0, 0.4]
    assert calibration_df["chance"].is_monotonic_increasing
