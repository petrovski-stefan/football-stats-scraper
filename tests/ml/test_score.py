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
    y = np.array([1, 0, 0, 1, 0, 0, 1, 0, 0, 0], dtype=float)
    scores = {"flat": -np.arange(10, dtype=float), "perfect": y + np.linspace(0, 0.1, 10)}
    clusters = pd.Series(np.repeat(["a", "b", "c", "d", "e"], 2))
    return y, scores, clusters


def test_top_n_table_counts_the_hits_and_the_difference(
    ranked: tuple[np.ndarray, dict[str, np.ndarray], "pd.Series[str]"],
) -> None:
    y, scores, clusters = ranked
    table = score.top_n_table(y, scores, clusters, (3,), "flat", draws=200).set_index("ranking")

    assert table.at["perfect", "comebacks"] == 3.0
    assert table.at["flat", "comebacks"] == 1.0  # rows 0, 1 and 2
    assert table.at["perfect", "- flat"] == pytest.approx(2 / 3)
    assert table.at["flat", "- flat"] == 0.0
    assert table.at["flat", "chance"] == pytest.approx(0.9)
    assert table.at["perfect", "low"] <= table.at["perfect", "share"] <= table.at["perfect", "high"]


def test_log_loss_rows_and_the_loss_table(
    ranked: tuple[np.ndarray, dict[str, np.ndarray], "pd.Series[str]"],
) -> None:
    y, _, clusters = ranked
    assert score.log_loss_rows(np.array([1.0, 0.0]), np.array([0.5, 0.5])) == pytest.approx(
        [np.log(2), np.log(2)]
    )

    chances = {"base": np.full(10, 0.3), "better": np.where(y == 1, 0.6, 0.15)}
    table = score.loss_table(y, chances, clusters, "base", draws=200).set_index("model")
    assert table.at["better", "- base"] < 0
    assert table.at["base", "O/E"] == pytest.approx(1.0)
    assert table.at["base", "- base"] == 0.0


def test_calibration_table_has_groups_of_equal_size() -> None:
    p = np.linspace(0.01, 0.2, 20)
    y = np.zeros(20)
    y[-2:] = 1.0

    table = score.calibration_table(y, p, bins=4)

    assert table["rows"].tolist() == [5, 5, 5, 5]
    assert table["rate"].tolist() == [0.0, 0.0, 0.0, 0.4]
    assert table["chance"].is_monotonic_increasing
