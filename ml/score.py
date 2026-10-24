"""Scores of the ML test: the comebacks in the top N of a ranking, the log loss and the
calibration. Each interval resamples whole league-seasons, because the matches of one
league-season are not independent (`notes/ANALYSIS/CLAUDE.md` §5, rule 5).
"""

from typing import Any

import numpy as np
import pandas as pd

DRAWS = 2000
EPSILON = 1e-12


def top_mask(score: np.ndarray, top_n: int) -> np.ndarray:
    """The `top_n` rows with the highest score. Equal scores keep the order of the rows."""

    mask = np.zeros(len(score), dtype=bool)
    mask[np.argsort(-score, kind="stable")[:top_n]] = True

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
    outcomes: np.ndarray,
    scores: dict[str, np.ndarray],
    clusters: "pd.Series[Any]",
    top_n_sizes: tuple[int, ...],
    reference: str,
    draws: int = DRAWS,
) -> pd.DataFrame:
    """For each N and each ranking: the comebacks in its top N, their share with its interval,
    and the difference to the share of the `reference` ranking with its interval. Each
    resample keeps the rows that the full set put in the top N."""

    names = list(scores)
    table = []
    for top_n in top_n_sizes:
        masks = [top_mask(scores[name], top_n) for name in names]
        columns = [column for mask in masks for column in (outcomes * mask, mask.astype(float))]
        sums = resampled_sums(np.column_stack(columns), clusters, draws)
        with np.errstate(divide="ignore", invalid="ignore"):
            shares = sums[:, 0::2] / sums[:, 1::2]

        at = names.index(reference)
        for i, name in enumerate(names):
            hits = float((outcomes * masks[i]).sum())
            difference = hits / top_n - float((outcomes * masks[at]).sum()) / top_n
            table.append(
                {
                    "N": top_n,
                    "ranking": name,
                    "comebacks": hits,
                    "share": hits / top_n,
                    "low": interval(shares[:, i])[0],
                    "high": interval(shares[:, i])[1],
                    f"- {reference}": difference,
                    "diff low": interval(shares[:, i] - shares[:, at])[0],
                    "diff high": interval(shares[:, i] - shares[:, at])[1],
                    "chance": top_n * float(np.mean(outcomes)),
                }
            )

    return pd.DataFrame(table)


def log_loss_rows(outcomes: np.ndarray, chances: np.ndarray) -> np.ndarray:
    """The log loss of each row's chance, with the chance kept inside (1e-12, 1 - 1e-12)."""

    clipped = np.clip(chances, EPSILON, 1.0 - EPSILON)

    return np.asarray(-(outcomes * np.log(clipped) + (1.0 - outcomes) * np.log(1.0 - clipped)))


def loss_table(
    outcomes: np.ndarray,
    chances: dict[str, np.ndarray],
    clusters: "pd.Series[Any]",
    reference: str,
    draws: int = DRAWS,
) -> pd.DataFrame:
    """For each model: its mean log loss, its observed over expected count (O/E), and its
    log loss minus that of the `reference` model, with the interval of the difference."""

    names = list(chances)
    losses = np.column_stack([log_loss_rows(outcomes, chances[name]) for name in names])
    sums = resampled_sums(np.column_stack([losses, np.ones(len(outcomes))]), clusters, draws)
    means = sums[:, :-1] / sums[:, -1:]

    at = names.index(reference)
    table = []
    for i, name in enumerate(names):
        low, high = interval(means[:, i] - means[:, at])
        table.append(
            {
                "model": name,
                "log loss": float(losses[:, i].mean()),
                "O/E": float(outcomes.sum() / chances[name].sum()),
                f"- {reference}": float(losses[:, i].mean() - losses[:, at].mean()),
                "low": low,
                "high": high,
            }
        )

    return pd.DataFrame(table)


def calibration_table(outcomes: np.ndarray, chances: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """The rows in `bins` groups of equal size by their chance: the mean chance, the observed
    rate and their ratio (O/E) in each."""

    group = pd.qcut(pd.Series(chances).rank(method="first"), bins, labels=False)
    grouped_chances_df = pd.DataFrame({"group": group, "y": outcomes, "p": chances})
    calibration_df = grouped_chances_df.groupby("group").agg(
        rows=("y", "size"), chance=("p", "mean"), rate=("y", "mean")
    )

    calibration_df["O/E"] = calibration_df["rate"] / calibration_df["chance"]

    return calibration_df.reset_index()
