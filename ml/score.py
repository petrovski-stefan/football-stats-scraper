"""Scores of the ML test: the comebacks in the top N of a ranking, the log loss and the
calibration. Each interval resamples whole league-seasons, because the matches of one
league-season are not independent (`notes/ANALYSIS/CLAUDE.md` §5, rule 5).
"""

from typing import Any

import numpy as np
import pandas as pd

from analysis import stats

DRAWS = 2000


def top_mask(score: np.ndarray, top_n: int) -> np.ndarray:
    """The `top_n` rows with the highest score. Equal scores keep the order of the rows."""

    mask = np.zeros(len(score), dtype=bool)
    mask[np.argsort(-score, kind="stable")[:top_n]] = True

    return mask


def resampled_sums(
    values: np.ndarray, clusters: "pd.Series[Any]", draws: int = DRAWS, seed: int = 0
) -> np.ndarray:
    """The column sums of `values` (rows by columns) in each of `draws` resamples of whole
    clusters: an array of draws by columns. All columns share each resample, so a difference
    of two columns stays paired; `analysis/stats.py:cluster_bootstrap_ratio_ci` takes one."""

    codes = pd.factorize(clusters)[0]
    per_cluster = np.zeros((codes.max() + 1, values.shape[1]))
    np.add.at(per_cluster, codes, values)

    picks = np.random.default_rng(seed).integers(0, len(per_cluster), (draws, len(per_cluster)))

    return np.asarray(per_cluster[picks].sum(axis=1))


def interval(values: np.ndarray) -> tuple[float, float]:
    """The 95% interval of resampled values."""

    low, high = np.nanquantile(values, [stats.INTERVAL_LOW, stats.INTERVAL_HIGH])

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
    reference_index = names.index(reference)
    table_rows = []
    for top_n in top_n_sizes:
        masks = [top_mask(scores[name], top_n) for name in names]
        hit_columns = [outcomes * mask for mask in masks]
        size_columns = [mask.astype(float) for mask in masks]
        sums = resampled_sums(np.column_stack(hit_columns + size_columns), clusters, draws)

        # A resample can hold none of a ranking's top N rows. Its share is then 0/0 (NaN), and
        # `interval` leaves it out.
        with np.errstate(divide="ignore", invalid="ignore"):
            shares = sums[:, : len(names)] / sums[:, len(names) :]

        reference_share = float(hit_columns[reference_index].sum()) / top_n
        for i, name in enumerate(names):
            hits = float(hit_columns[i].sum())
            low, high = interval(shares[:, i])
            diff_low, diff_high = interval(shares[:, i] - shares[:, reference_index])
            table_rows.append(
                {
                    "N": top_n,
                    "ranking": name,
                    "comebacks": hits,
                    "share": hits / top_n,
                    "low": low,
                    "high": high,
                    f"- {reference}": hits / top_n - reference_share,
                    "diff low": diff_low,
                    "diff high": diff_high,
                    "random": top_n * float(np.mean(outcomes)),
                }
            )

    return pd.DataFrame(table_rows)


def log_loss_rows(outcomes: np.ndarray, chances: np.ndarray) -> np.ndarray:
    """The log loss of each row's chance, with the chance kept inside (1e-12, 1 - 1e-12)."""

    clipped = np.clip(chances, stats.LOG_LOSS_CLIP, 1.0 - stats.LOG_LOSS_CLIP)

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
    loss_sums, row_counts = sums[:, :-1], sums[:, -1:]
    means = loss_sums / row_counts

    reference_index = names.index(reference)
    table_rows = []
    for i, name in enumerate(names):
        low, high = interval(means[:, i] - means[:, reference_index])
        table_rows.append(
            {
                "model": name,
                "log loss": float(losses[:, i].mean()),
                "O/E": float(outcomes.sum() / chances[name].sum()),
                f"- {reference}": float(losses[:, i].mean() - losses[:, reference_index].mean()),
                "low": low,
                "high": high,
            }
        )

    return pd.DataFrame(table_rows)


def calibration_table(outcomes: np.ndarray, chances: np.ndarray, bins: int = 10) -> pd.DataFrame:
    """The rows in `bins` groups of equal size by their chance: the mean chance, the observed
    rate and their ratio (O/E) in each."""

    group = pd.qcut(pd.Series(chances).rank(method="first"), bins, labels=False)
    grouped_chances_df = pd.DataFrame({"group": group, "outcome": outcomes, "chance": chances})
    calibration_df = grouped_chances_df.groupby("group").agg(
        rows=("outcome", "size"), chance=("chance", "mean"), rate=("outcome", "mean")
    )

    calibration_df["O/E"] = calibration_df["rate"] / calibration_df["chance"]

    return calibration_df.reset_index()
