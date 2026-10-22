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


def wilson_ci(successes: int, n: int) -> tuple[float, float]:
    """95% Wilson score interval (scipy's), safe at small n and for rare events."""
    if n == 0:
        return (0.0, 0.0)
    ci = binomtest(successes, n).proportion_ci(confidence_level=0.95, method="wilson")
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


def observed_expected(frame: pd.DataFrame, observed: str, expected: str) -> dict[str, float]:
    """Observed and expected sums, their ratio (O/E), and its interval over `frame.cluster`."""
    obs, exp = float(frame[observed].sum()), float(frame[expected].sum())
    low, high = cluster_bootstrap_ratio_ci(frame[observed], frame[expected], frame["cluster"])

    return {
        "n": float(len(frame)),
        "observed": obs,
        "expected": exp,
        "oe": obs / exp,
        "low": low,
        "high": high,
    }


def observed_expected_table(
    frame: pd.DataFrame, rows: tuple[tuple[str, str, str], ...]
) -> pd.DataFrame:
    """One O/E row per (observed column, expected column, label)."""
    return pd.DataFrame(
        [{"quantity": label, **observed_expected(frame, o, e)} for o, e, label in rows]
    )


@dataclass(frozen=True)
class Heterogeneity:
    """Cochran's Q across units, and the between-unit spread it implies."""

    q: float
    df: int
    p: float
    tau2: float  # between-unit variance, method of moments (DerSimonian-Laird)
    pooled: float  # precision-weighted mean of the units


def heterogeneity(means: "pd.Series[float]", variances: "pd.Series[float]") -> Heterogeneity:
    """One test of "do the units differ beyond noise?", in place of one test per unit."""
    weights = 1.0 / variances
    pooled = float((weights * means).sum() / weights.sum())
    q = float((weights * (means - pooled) ** 2).sum())

    df = len(means) - 1
    scale = float(weights.sum() - (weights**2).sum() / weights.sum())
    tau2 = max(0.0, (q - df) / scale) if scale > 0 else 0.0

    return Heterogeneity(q=q, df=df, p=float(chi2.sf(q, df)), tau2=tau2, pooled=pooled)


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
    v = variances.to_numpy(dtype=float)
    weights = 1.0 / v
    codes = np.zeros(len(v), dtype=int) if groups is None else pd.factorize(groups)[0]
    member = np.zeros((len(v), codes.max() + 1))
    member[np.arange(len(v)), codes] = 1.0

    z = np.random.default_rng(seed).standard_normal((draws, len(v)))
    critical = chi2.isf(0.05, len(v) - member.shape[1])

    def found(tau: float) -> float:
        values = z * np.sqrt(v + tau**2)
        means = ((values * weights) @ member) / (weights @ member)
        q = (weights * (values - means[:, codes]) ** 2).sum(axis=1)
        return float((q > critical).mean())

    low, high = 0.0, 10 * float(np.sqrt(v.max()))
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
    keep = het.tau2 / (het.tau2 + variances)
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
    p: float  # Cochran-Mantel-Haenszel chi-square, 1 df, no continuity correction
    strata: int  # strata with both a flagged and an unflagged row and both outcomes


def mantel_haenszel(
    flag: "pd.Series[bool]", event: "pd.Series[bool]", stratum: "pd.Series[Any]"
) -> MantelHaenszel:
    """The Mantel-Haenszel odds ratio of `event` for `flag` over the strata, its 95% interval
    and the CMH test. The Binding rules of `notes/ANALYSIS/CLAUDE.md` §6 ask for it: pool
    over league-season strata, never test per league. A stratum of one row tells nothing and
    is left out."""
    flagged, hit = flag.to_numpy(dtype=bool), event.to_numpy(dtype=bool)
    cells = (
        pd.DataFrame(
            {"a": flagged & hit, "b": flagged & ~hit, "c": ~flagged & hit, "d": ~flagged & ~hit}
        )
        .groupby(stratum.to_numpy())[["a", "b", "c", "d"]]
        .sum()
        .astype(float)
    )

    cells = cells[cells.sum(axis=1) >= 2]
    a, b, c, d = (cells[column].to_numpy() for column in ("a", "b", "c", "d"))

    n = a + b + c + d
    odds_ratio, low, high = _rgb(a, b, c, d, n)

    expected = (a + b) * (a + c) / n
    variance = (a + b) * (c + d) * (a + c) * (b + d) / (n**2 * (n - 1))
    total = float(variance.sum())
    statistic = float((a.sum() - expected.sum()) ** 2 / total) if total > 0 else 0.0

    return MantelHaenszel(
        flagged=int(flagged.sum()),
        flagged_events=int((flagged & hit).sum()),
        rest=int((~flagged).sum()),
        rest_events=int((~flagged & hit).sum()),
        odds_ratio=odds_ratio,
        low=low,
        high=high,
        p=float(chi2.sf(statistic, 1)),
        strata=int((variance > 0).sum()),
    )


def _rgb(
    a: np.ndarray, b: np.ndarray, c: np.ndarray, d: np.ndarray, n: np.ndarray
) -> tuple[float, float, float]:
    """The Mantel-Haenszel odds ratio and its Robins-Breslow-Greenland 95% interval; not a
    number where a sum in it is 0."""
    r, s = a * d / n, b * c / n
    together, apart = (a + d) / n, (b + c) / n
    rs, ss = float(r.sum()), float(s.sum())

    if rs <= 0 or ss <= 0:
        return (rs / ss if ss > 0 else float("nan")), float("nan"), float("nan")

    variance = (
        float((together * r).sum()) / (2 * rs**2)
        + float((together * s + apart * r).sum()) / (2 * rs * ss)
        + float((apart * s).sum()) / (2 * ss**2)
    )

    log_or, half = float(np.log(rs / ss)), Z95 * float(np.sqrt(variance))
    return rs / ss, float(np.exp(log_or - half)), float(np.exp(log_or + half))


def holm(p_values: Sequence[float]) -> list[float]:
    """Holm-adjusted p-values, in the order given."""
    order = sorted(range(len(p_values)), key=lambda i: p_values[i])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(p_values) - rank) * p_values[i]))
        adjusted[i] = running

    return adjusted
