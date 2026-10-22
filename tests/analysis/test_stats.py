"""`analysis/stats.py`: scores, intervals, shrinkage and the heterogeneity test."""

import math

import numpy as np
import pandas as pd
import pytest
from scipy.stats import chi2

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


def test_cluster_bootstrap_of_a_constant_ratio_is_that_ratio() -> None:
    bottoms = pd.Series([0.5, 1.5, 2.0, 1.0])
    clusters = pd.Series(["a", "a", "b", "b"])
    assert stats.cluster_bootstrap_ratio_ci(bottoms * 3, bottoms, clusters) == pytest.approx(
        (3.0, 3.0)
    )


@pytest.fixture
def observed_frame() -> pd.DataFrame:
    """Four matches in two clusters: observed hits and two expected columns."""
    return pd.DataFrame(
        {
            "cluster": ["a", "a", "b", "b"],
            "hit": [1.0, 0.0, 1.0, 0.0],
            "chance": [0.5, 0.5, 0.25, 0.25],
            "other": [0.4, 0.0, 0.3, 0.2],
        }
    )


def test_observed_expected_is_the_ratio_of_the_sums(observed_frame: pd.DataFrame) -> None:
    row = stats.observed_expected(observed_frame, "hit", "chance")
    assert (row["n"], row["observed"], row["expected"]) == (4.0, 2.0, 1.5)
    assert row["oe"] == pytest.approx(2 / 1.5)
    assert row["low"] <= row["oe"] <= row["high"]


def test_observed_expected_table_has_one_row_per_comparison(
    observed_frame: pd.DataFrame,
) -> None:
    rows = (("hit", "chance", "one"), ("hit", "other", "two"))
    assert stats.observed_expected_table(observed_frame, rows)["quantity"].tolist() == [
        "one",
        "two",
    ]


def test_equal_units_show_no_heterogeneity() -> None:
    het = stats.heterogeneity(pd.Series([0.5, 0.5, 0.5]), pd.Series([0.01, 0.02, 0.04]))
    assert (het.q, het.df, het.tau2) == (0.0, 2, 0.0)
    assert het.p == pytest.approx(1.0)
    assert het.pooled == pytest.approx(0.5)


def test_spread_units_show_heterogeneity() -> None:
    het = stats.heterogeneity(pd.Series([0.0, 1.0, 2.0]), pd.Series([0.01, 0.01, 0.01]))
    assert het.p < 1e-6
    assert het.tau2 > 0


def test_detectable_tau_matches_the_closed_form_for_equal_variances() -> None:
    # With one variance v for every unit, Q / (1 + tau^2 / v) is chi-square on k - 1 df.
    v, units = 0.04, 30
    df = units - 1
    closed = math.sqrt(v * (chi2.isf(0.05, df) / chi2.isf(0.8, df) - 1))
    assert stats.detectable_tau(pd.Series([v] * units), draws=4000) == pytest.approx(
        closed, rel=0.05
    )


def test_detectable_tau_with_one_group_is_the_plain_one() -> None:
    variances = pd.Series([0.01, 0.02, 0.04, 0.03] * 5)
    plain = stats.detectable_tau(variances)
    grouped = stats.detectable_tau(variances, groups=pd.Series(["x"] * 20))
    assert grouped == pytest.approx(plain)
    two_groups = stats.detectable_tau(variances, groups=pd.Series(["x", "y"] * 10))
    assert two_groups > 0


def test_detectable_tau_grows_with_the_noise() -> None:
    quiet = stats.detectable_tau(pd.Series([0.01] * 20))
    noisy = stats.detectable_tau(pd.Series([0.04] * 20))
    assert noisy > quiet


def test_shrink_without_spread_gives_the_pooled_mean() -> None:
    het = stats.Heterogeneity(q=0.0, df=1, p=1.0, tau2=0.0, pooled=0.3)
    shrunk = stats.shrink(pd.Series([0.2, 0.4]), pd.Series([0.01, 0.01]), het)
    assert shrunk.tolist() == pytest.approx([0.3, 0.3])


def test_shrink_keeps_a_precise_unit_near_its_own_mean() -> None:
    het = stats.Heterogeneity(q=0.0, df=1, p=1.0, tau2=0.01, pooled=0.3)
    shrunk = stats.shrink(pd.Series([0.2, 0.4]), pd.Series([1e-9, 1.0]), het)
    assert shrunk[0] == pytest.approx(0.2, abs=1e-6)
    assert abs(shrunk[1] - 0.3) < abs(0.4 - 0.3)


def _flagged_rows(cells: list[tuple[str, int, int, int, int]]) -> pd.DataFrame:
    """Rows for (stratum, a, b, c, d): flagged with the event, flagged without, unflagged
    with, unflagged without."""
    kinds = ((True, True), (True, False), (False, True), (False, False))
    rows = [
        {"stratum": stratum, "flag": flag, "event": event}
        for stratum, *counts in cells
        for (flag, event), count in zip(kinds, counts, strict=True)
        for _ in range(count)
    ]

    return pd.DataFrame(rows)


def _mh(rows: pd.DataFrame) -> stats.MantelHaenszel:
    return stats.mantel_haenszel(rows["flag"], rows["event"], rows["stratum"])


def test_mantel_haenszel_of_one_table_is_its_odds_ratio_with_woolfs_interval() -> None:
    a, b, c, d = 10, 20, 30, 90

    result = _mh(_flagged_rows([("s", a, b, c, d)]))

    assert result.odds_ratio == pytest.approx(a * d / (b * c))
    half = stats.Z95 * math.sqrt(1 / a + 1 / b + 1 / c + 1 / d)
    assert result.low == pytest.approx(1.5 * math.exp(-half))
    assert result.high == pytest.approx(1.5 * math.exp(half))
    assert (result.flagged, result.flagged_events, result.rest, result.rest_events) == (
        30,
        10,
        120,
        30,
    )


def test_the_cmh_test_of_one_table_is_pearsons_scaled_by_n_minus_one() -> None:
    a, b, c, d = 10, 20, 30, 90
    n = a + b + c + d
    pearson = n * (a * d - b * c) ** 2 / ((a + b) * (c + d) * (a + c) * (b + d))
    result = _mh(_flagged_rows([("s", a, b, c, d)]))
    assert result.p == pytest.approx(float(chi2.sf(pearson * (n - 1) / n, 1)))


def test_mantel_haenszel_pools_strata_that_share_one_odds_ratio() -> None:
    # Both strata have an odds ratio of 2, at different base rates.
    result = _mh(_flagged_rows([("x", 20, 20, 10, 20), ("y", 4, 36, 2, 36)]))
    assert result.odds_ratio == pytest.approx(2.0)
    assert result.strata == 2


def test_mantel_haenszel_leaves_out_strata_of_one_row() -> None:
    with_single = _flagged_rows([("x", 20, 20, 10, 20), ("lone", 1, 0, 0, 0)])
    assert _mh(with_single).odds_ratio == pytest.approx(2.0)


def test_mantel_haenszel_without_flagged_events_has_no_interval() -> None:
    result = _mh(_flagged_rows([("x", 0, 10, 5, 5)]))
    assert result.odds_ratio == 0.0
    assert math.isnan(result.low)


def test_holm_scales_the_sorted_p_values_and_keeps_them_in_order() -> None:
    assert stats.holm([0.01, 0.04, 0.03]) == pytest.approx([0.03, 0.06, 0.06])
    assert stats.holm([0.5, 0.9]) == pytest.approx([1.0, 1.0])
