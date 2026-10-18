"""Scores, intervals, shrinkage and a heterogeneity test, shared by the runners."""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import binomtest, chi2


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
    sums = values.groupby(clusters).sum().to_numpy()
    counts = values.groupby(clusters).count().to_numpy()
    picks = np.random.default_rng(seed).integers(0, len(sums), size=(n_boot, len(sums)))
    means = sums[picks].sum(axis=1) / counts[picks].sum(axis=1)
    low, high = np.quantile(means, [0.025, 0.975])
    return float(low), float(high)


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
