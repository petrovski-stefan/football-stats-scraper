"""Scores of the ML test: the comebacks in the top N of a ranking, the log loss and the
calibration. Each interval resamples whole league-seasons, because the matches of one
league-season are not independent (`notes/ANALYSIS/CLAUDE.md` §5, rule 5).
"""

from typing import Any

import numpy as np
import pandas as pd

DRAWS = 2000
EPSILON = 1e-12


def top_mask(score: np.ndarray, n: int) -> np.ndarray:
    """The n rows with the highest score. Equal scores keep the order of the rows."""
    mask = np.zeros(len(score), dtype=bool)
    mask[np.argsort(-score, kind="stable")[:n]] = True
    return mask


def resampled_sums(
    values: np.ndarray, clusters: "pd.Series[Any]", draws: int = DRAWS, seed: int = 0
) -> np.ndarray:
    """The column sums of `values` (rows by columns) in each of `draws` resamples of whole
    clusters: an array of draws by columns."""
    codes = pd.factorize(clusters)[0]
    per_cluster = np.zeros((codes.max() + 1, values.shape[1]))
    np.add.at(per_cluster, codes, values)
    picks = np.random.default_rng(seed).integers(0, len(per_cluster), (draws, len(per_cluster)))
    return np.asarray(per_cluster[picks].sum(axis=1))


def interval(values: np.ndarray) -> tuple[float, float]:
    """The 95% interval of resampled values."""
    low, high = np.nanquantile(values, [0.025, 0.975])
    return float(low), float(high)


def top_n_table(
    y: np.ndarray,
    scores: dict[str, np.ndarray],
    clusters: "pd.Series[Any]",
    ns: tuple[int, ...],
    reference: str,
    draws: int = DRAWS,
) -> pd.DataFrame:
    """For each N and each ranking: the comebacks in its top N, their share with its interval,
    and the difference to the share of the `reference` ranking with its interval. Each
    resample keeps the rows that the full set put in the top N."""
    names = list(scores)
    table = []
    for n in ns:
        masks = [top_mask(scores[name], n) for name in names]
        columns = [column for mask in masks for column in (y * mask, mask.astype(float))]
        sums = resampled_sums(np.column_stack(columns), clusters, draws)
        with np.errstate(divide="ignore", invalid="ignore"):
            shares = sums[:, 0::2] / sums[:, 1::2]
        at = names.index(reference)
        for i, name in enumerate(names):
            hits = float((y * masks[i]).sum())
            difference = hits / n - float((y * masks[at]).sum()) / n
            table.append(
                {
                    "N": n,
                    "ranking": name,
                    "comebacks": hits,
                    "share": hits / n,
                    "low": interval(shares[:, i])[0],
                    "high": interval(shares[:, i])[1],
                    f"- {reference}": difference,
                    "diff low": interval(shares[:, i] - shares[:, at])[0],
                    "diff high": interval(shares[:, i] - shares[:, at])[1],
                    "chance": n * float(np.mean(y)),
                }
            )
    return pd.DataFrame(table)


def log_loss_rows(y: np.ndarray, p: np.ndarray) -> np.ndarray:
    """The log loss of each row's chance, with the chance kept inside (1e-12, 1 - 1e-12)."""
    clipped = np.clip(p, EPSILON, 1.0 - EPSILON)
    return np.asarray(-(y * np.log(clipped) + (1.0 - y) * np.log(1.0 - clipped)))


def loss_table(
    y: np.ndarray,
    chances: dict[str, np.ndarray],
    clusters: "pd.Series[Any]",
    reference: str,
    draws: int = DRAWS,
) -> pd.DataFrame:
    """For each model: its mean log loss, its observed over expected count (O/E), and its
    log loss minus that of the `reference` model, with the interval of the difference."""
    names = list(chances)
    losses = np.column_stack([log_loss_rows(y, chances[name]) for name in names])
    sums = resampled_sums(np.column_stack([losses, np.ones(len(y))]), clusters, draws)
    means = sums[:, :-1] / sums[:, -1:]
    at = names.index(reference)
    table = []
    for i, name in enumerate(names):
        low, high = interval(means[:, i] - means[:, at])
        table.append(
            {
                "model": name,
                "log loss": float(losses[:, i].mean()),
                "O/E": float(y.sum() / chances[name].sum()),
                f"- {reference}": float(losses[:, i].mean() - losses[:, at].mean()),
                "low": low,
                "high": high,
            }
        )
    return pd.DataFrame(table)


def calibration_table(y: np.ndarray, p: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """The rows in `bins` groups of equal size by their chance: the mean chance, the observed
    rate and their ratio (O/E) in each."""
    group = pd.qcut(pd.Series(p).rank(method="first"), bins, labels=False)
    frame = pd.DataFrame({"group": group, "y": y, "p": p})
    table = frame.groupby("group").agg(rows=("y", "size"), chance=("p", "mean"), rate=("y", "mean"))
    table["O/E"] = table["rate"] / table["chance"]
    return table.reset_index()
