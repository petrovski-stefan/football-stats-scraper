"""`analysis/stats.py`: scores, intervals, shrinkage and the heterogeneity test."""

import math

import numpy as np
import pandas as pd
import pytest

from analysis import stats


def test_log_loss_1x2_is_minus_the_log_of_the_result() -> None:
    probs = np.array([[0.5, 0.3, 0.2], [0.2, 0.3, 0.5]])
    losses = stats.log_loss_1x2(probs, np.array([0, 2]))
    assert losses.tolist() == pytest.approx([math.log(2), math.log(2)])


def test_brier_1x2_runs_from_zero_to_two() -> None:
    sure = np.array([[1.0, 0.0, 0.0]])
    assert stats.brier_1x2(sure, np.array([0]))[0] == 0.0
    assert stats.brier_1x2(sure, np.array([2]))[0] == 2.0


def test_wilson_ci_known_value() -> None:
    low, high = stats.wilson_ci(5, 10)
    assert low == pytest.approx(0.2366, abs=1e-4)
    assert high == pytest.approx(0.7634, abs=1e-4)


def test_wilson_ci_of_nothing() -> None:
    assert stats.wilson_ci(0, 0) == (0.0, 0.0)


def test_cluster_bootstrap_of_a_constant_is_that_constant() -> None:
    values = pd.Series([0.25] * 6)
    clusters = pd.Series(["a", "a", "b", "b", "c", "c"])
    assert stats.cluster_bootstrap_ci(values, clusters) == pytest.approx((0.25, 0.25))


def test_equal_units_show_no_heterogeneity() -> None:
    het = stats.heterogeneity(pd.Series([0.5, 0.5, 0.5]), pd.Series([0.01, 0.02, 0.04]))
    assert (het.q, het.df, het.tau2) == (0.0, 2, 0.0)
    assert het.p == pytest.approx(1.0)
    assert het.pooled == pytest.approx(0.5)


def test_spread_units_show_heterogeneity() -> None:
    het = stats.heterogeneity(pd.Series([0.0, 1.0, 2.0]), pd.Series([0.01, 0.01, 0.01]))
    assert het.p < 1e-6
    assert het.tau2 > 0


def test_shrink_without_spread_gives_the_pooled_mean() -> None:
    het = stats.Heterogeneity(q=0.0, df=1, p=1.0, tau2=0.0, pooled=0.3)
    shrunk = stats.shrink(pd.Series([0.2, 0.4]), pd.Series([0.01, 0.01]), het)
    assert shrunk.tolist() == pytest.approx([0.3, 0.3])


def test_shrink_keeps_a_precise_unit_near_its_own_mean() -> None:
    het = stats.Heterogeneity(q=0.0, df=1, p=1.0, tau2=0.01, pooled=0.3)
    shrunk = stats.shrink(pd.Series([0.2, 0.4]), pd.Series([1e-9, 1.0]), het)
    assert shrunk[0] == pytest.approx(0.2, abs=1e-6)
    assert abs(shrunk[1] - 0.3) < abs(0.4 - 0.3)
