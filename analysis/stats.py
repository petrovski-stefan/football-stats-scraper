"""Scores, intervals, shrinkage, a heterogeneity test, and the Mantel-Haenszel odds ratio with
the Holm correction, shared by the runners."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import binomtest, chi2, norm

Z95 = float(norm.ppf(0.975))


def log_loss_1x2(probs: np.ndarray, outcome: np.ndarray) -> np.ndarray:
    """Per-match log loss of a three-way forecast: minus the log of the result's probability."""
    return np.asarray(-np.log(probs[np.arange(len(outcome)), outcome]))


def brier_1x2(probs: np.ndarray, outcome: np.ndarray) -> np.ndarray:
    """Per-match Brier score of a three-way forecast: sum of (p - hit)^2, from 0 to 2."""
    hits = np.zeros_like(probs)
    hits[np.arange(len(outcome)), outcome] = 1.0
    return np.asarray(((probs - hits) ** 2).sum(axis=1))


def wilson_ci(successes: int, trials: int) -> tuple[float, float]:
    """95% Wilson score interval (scipy's), safe at small n and for rare events."""
    if trials == 0:
        return (0.0, 0.0)
    ci = binomtest(successes, trials).proportion_ci(confidence_level=0.95, method="wilson")
    return float(ci.low), float(ci.high)


def cluster_bootstrap_ci(
    values: "pd.Series[float]", clusters: "pd.Series[Any]", n_boot: int = 2000, seed: int = 0
) -> tuple[float, float]:
    """95% interval for the mean of `values`, resampling whole clusters.

    The matches of one league-season share teams and one pricing desk, so they are not
    independent. Resampling league-seasons, not matches, keeps the interval honest.
    """
    counted = values.notna().astype(float)
    return cluster_bootstrap_ratio_ci(values, counted, clusters, n_boot=n_boot, seed=seed)


def cluster_bootstrap_ratio_ci(
    numerator: "pd.Series[float]",
    denominator: "pd.Series[float]",
    clusters: "pd.Series[Any]",
    n_boot: int = 2000,
    seed: int = 0,
) -> tuple[float, float]:
    """95% interval for sum(numerator) / sum(denominator), resampling whole clusters.

    The ratio of an observed count to the count that a model expects (O/E) is one such
    ratio; a mean is another, with a denominator of ones.
    """
    tops = numerator.groupby(clusters).sum().to_numpy()
    bottoms = denominator.groupby(clusters).sum().to_numpy()
    picks = np.random.default_rng(seed).integers(0, len(tops), size=(n_boot, len(tops)))
    ratios = tops[picks].sum(axis=1) / bottoms[picks].sum(axis=1)
    low, high = np.quantile(ratios, [0.025, 0.975])
    return float(low), float(high)


def observed_expected(df: pd.DataFrame, observed: str, expected: str) -> dict[str, float]:
    """Observed and expected sums, their ratio (O/E), and its interval over `frame.cluster`."""
    obs, exp = float(df[observed].sum()), float(df[expected].sum())
    low, high = cluster_bootstrap_ratio_ci(df[observed], df[expected], df["cluster"])

    return {
        "n": float(len(df)),
        "observed": obs,
        "expected": exp,
        "oe": obs / exp,
        "low": low,
        "high": high,
    }


def observed_expected_table(
    df: pd.DataFrame, rows: tuple[tuple[str, str, str], ...]
) -> pd.DataFrame:
    """One O/E row per (observed column, expected column, label)."""
    return pd.DataFrame(
        [{"quantity": label, **observed_expected(df, o, e)} for o, e, label in rows]
    )


@dataclass(frozen=True)
class Heterogeneity:
    """Cochran's Q across units, and the between-unit spread it implies."""

    cochran_q: float
    degrees_of_freedom: int
    p_value: float
    tau_squared: float  # between-unit variance, method of moments (DerSimonian-Laird)
    pooled: float  # precision-weighted mean of the units


def heterogeneity(means: "pd.Series[float]", variances: "pd.Series[float]") -> Heterogeneity:
    """One test of "do the units differ beyond noise?", in place of one test per unit."""
    weights = 1.0 / variances
    pooled = float((weights * means).sum() / weights.sum())
    cochran_q = float((weights * (means - pooled) ** 2).sum())

    degrees_of_freedom = len(means) - 1
    scale = float(weights.sum() - (weights**2).sum() / weights.sum())
    tau_squared = max(0.0, (cochran_q - degrees_of_freedom) / scale) if scale > 0 else 0.0

    return Heterogeneity(
        cochran_q=cochran_q,
        degrees_of_freedom=degrees_of_freedom,
        p_value=float(chi2.sf(cochran_q, degrees_of_freedom)),
        tau_squared=tau_squared,
        pooled=pooled,
    )


def detectable_tau(
    variances: "pd.Series[float]",
    power: float = 0.8,
    draws: int = 2000,
    seed: int = 0,
    groups: "pd.Series[Any] | None" = None,
) -> float:
    """The between-unit sd that `heterogeneity` finds at p < 0.05 with the given power.

    Simulated under the normal random-effects model: each unit's value is normal around one
    mean, with its own variance plus tau^2. The same draws serve every tau, and a bisection
    finds the tau at which the share of draws with p < 0.05 reaches `power`. With `groups`
    (such as the league of each team), Q sums each group's units around the group's own
    mean, as in `analysis/units.py:within_tested`.
    """
    unit_variances = variances.to_numpy(dtype=float)
    weights = 1.0 / unit_variances
    codes = np.zeros(len(unit_variances), dtype=int) if groups is None else pd.factorize(groups)[0]
    member = np.zeros((len(unit_variances), codes.max() + 1))
    member[np.arange(len(unit_variances)), codes] = 1.0

    normal_draws = np.random.default_rng(seed).standard_normal((draws, len(unit_variances)))
    critical = chi2.isf(0.05, len(unit_variances) - member.shape[1])

    def found(between_unit_sd: float) -> float:
        values = normal_draws * np.sqrt(unit_variances + between_unit_sd**2)
        means = ((values * weights) @ member) / (weights @ member)
        cochran_q = (weights * (values - means[:, codes]) ** 2).sum(axis=1)
        return float((cochran_q > critical).mean())

    low, high = 0.0, 10 * float(np.sqrt(unit_variances.max()))
    for _ in range(40):
        middle = (low + high) / 2
        low, high = (middle, high) if found(middle) < power else (low, middle)

    return high


def shrink(
    means: "pd.Series[float]", variances: "pd.Series[float]", het: Heterogeneity
) -> "pd.Series[float]":
    """Empirical-Bayes normal shrinkage of each unit's mean toward the pooled mean.

    The continuous counterpart of the Beta-Binomial rule in
    `notes/REFERENCE/STATS_PRIMER.md` §1: a unit keeps the share tau^2 / (tau^2 + its
    variance) of its own deviation. With tau^2 = 0 every unit gets the pooled mean.
    """
    keep = het.tau_squared / (het.tau_squared + variances)
    return het.pooled + keep * (means - het.pooled)


@dataclass(frozen=True)
class MantelHaenszel:
    """The odds of an event with a flag against without it, pooled over strata."""

    flagged: int
    flagged_events: int
    rest: int
    rest_events: int
    odds_ratio: float
    low: float  # 95% interval, Robins-Breslow-Greenland
    high: float
    p_value: float  # Cochran-Mantel-Haenszel chi-square, 1 df, no continuity correction
    strata: int  # strata with both a flagged and an unflagged row and both outcomes


def mantel_haenszel(
    flag: "pd.Series[bool]", event: "pd.Series[bool]", stratum: "pd.Series[Any]"
) -> MantelHaenszel:
    """The Mantel-Haenszel odds ratio of `event` for `flag` over the strata, its 95% interval
    and the CMH test. The Binding rules of `notes/ANALYSIS/CLAUDE.md` §6 ask for it: pool
    over league-season strata, never test per league. A stratum of one row tells nothing and
    is left out."""
    flagged, hit = flag.to_numpy(dtype=bool), event.to_numpy(dtype=bool)
    cells_df = (
        pd.DataFrame(
            {"a": flagged & hit, "b": flagged & ~hit, "c": ~flagged & hit, "d": ~flagged & ~hit}
        )
        .groupby(stratum.to_numpy())[["a", "b", "c", "d"]]
        .sum()
        .astype(float)
    )

    cells_df = cells_df[cells_df.sum(axis=1) >= 2]
    flagged_hits, flagged_misses, rest_hits, rest_misses = (
        cells_df[column].to_numpy() for column in ("a", "b", "c", "d")
    )

    stratum_size = flagged_hits + flagged_misses + rest_hits + rest_misses
    odds_ratio, low, high = _rgb(flagged_hits, flagged_misses, rest_hits, rest_misses, stratum_size)

    expected = (flagged_hits + flagged_misses) * (flagged_hits + rest_hits) / stratum_size
    variance = (
        (flagged_hits + flagged_misses)
        * (rest_hits + rest_misses)
        * (flagged_hits + rest_hits)
        * (flagged_misses + rest_misses)
        / (stratum_size**2 * (stratum_size - 1))
    )
    total = float(variance.sum())
    statistic = float((flagged_hits.sum() - expected.sum()) ** 2 / total) if total > 0 else 0.0

    return MantelHaenszel(
        flagged=int(flagged.sum()),
        flagged_events=int((flagged & hit).sum()),
        rest=int((~flagged).sum()),
        rest_events=int((~flagged & hit).sum()),
        odds_ratio=odds_ratio,
        low=low,
        high=high,
        p_value=float(chi2.sf(statistic, 1)),
        strata=int((variance > 0).sum()),
    )


def _rgb(
    flagged_hits: np.ndarray,
    flagged_misses: np.ndarray,
    rest_hits: np.ndarray,
    rest_misses: np.ndarray,
    stratum_size: np.ndarray,
) -> tuple[float, float, float]:
    """The Mantel-Haenszel odds ratio and its Robins-Breslow-Greenland 95% interval; not a
    number where a sum in it is 0."""
    or_numerator, or_denominator = (
        flagged_hits * rest_misses / stratum_size,
        flagged_misses * rest_hits / stratum_size,
    )
    together, apart = (
        (flagged_hits + rest_misses) / stratum_size,
        (flagged_misses + rest_hits) / stratum_size,
    )
    or_numerator_sum, or_denominator_sum = float(or_numerator.sum()), float(or_denominator.sum())

    if or_numerator_sum <= 0 or or_denominator_sum <= 0:
        return (
            (or_numerator_sum / or_denominator_sum if or_denominator_sum > 0 else float("nan")),
            float("nan"),
            float("nan"),
        )

    variance = (
        float((together * or_numerator).sum()) / (2 * or_numerator_sum**2)
        + float((together * or_denominator + apart * or_numerator).sum())
        / (2 * or_numerator_sum * or_denominator_sum)
        + float((apart * or_denominator).sum()) / (2 * or_denominator_sum**2)
    )

    log_or, half = (
        float(np.log(or_numerator_sum / or_denominator_sum)),
        Z95 * float(np.sqrt(variance)),
    )
    return (
        or_numerator_sum / or_denominator_sum,
        float(np.exp(log_or - half)),
        float(np.exp(log_or + half)),
    )


def holm(p_values: Sequence[float]) -> list[float]:
    """Holm-adjusted p-values, in the order given."""
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[i]))
        adjusted[i] = running

    return adjusted
