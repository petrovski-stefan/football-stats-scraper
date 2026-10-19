"""Shin's method on the whole corpus, all matches pooled.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`. Prints the corpus line; z and the margin;
Shin against proportional margin removal, scored on the full-time result, for all matches
and per season cohort; and observed against implied rates by price band.

Run: `uv run python -m analysis.schedule.whole_corpus.all.shin`
"""

import pandas as pd

from analysis import corpus, stats
from analysis.methods import shin


def summary(frame: pd.DataFrame) -> dict[str, float]:
    """z, the margin, and both methods' mean scores with Shin's gain and its cluster CI."""
    z = frame["shin_z"]
    out = {
        "matches": float(len(frame)),
        "z_median": float(z.median()),
        "z_q1": float(z.quantile(0.25)),
        "z_q3": float(z.quantile(0.75)),
        "z_mean": float(z.mean()),
        "margin_median": float(frame["margin"].median()),
        "z_margin_spearman": float(z.corr(frame["margin"], method="spearman")),
    }
    for score in ("ll", "brier"):
        low, high = stats.cluster_bootstrap_ci(frame[f"{score}_gain"], frame["cluster"])
        out |= {
            f"{score}_prop": float(frame[f"{score}_prop"].mean()),
            f"{score}_shin": float(frame[f"{score}_shin"].mean()),
            f"{score}_gain": float(frame[f"{score}_gain"].mean()),
            f"{score}_gain_low": low,
            f"{score}_gain_high": high,
        }
    return out


def price_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Per price band: outcomes, the observed rate with its Wilson CI, and each method's mean."""
    rows = shin.outcome_rows(frame)
    rows["band"] = pd.cut(rows["price"], shin.PRICE_EDGES)
    table = []
    for band, group in rows.groupby("band", observed=True):
        hits, n = int(group["hit"].sum()), len(group)
        low, high = stats.wilson_ci(hits, n)
        table.append(
            {
                "band": str(band),
                "outcomes": n,
                "observed": hits / n,
                "low": low,
                "high": high,
                "prop": float(group["prop"].mean()),
                "shin": float(group["shin"].mean()),
            }
        )
    return pd.DataFrame(table)


def show(title: str, values: dict[str, float]) -> None:
    """Print one summary block."""
    print(f"\n== {title}: {int(values['matches']):,} matches")
    print(
        f"z: median {values['z_median']:.5f} (IQR {values['z_q1']:.5f} to "
        f"{values['z_q3']:.5f}), mean {values['z_mean']:.5f}"
    )
    print(
        f"margin: median {values['margin_median']:.5f}; "
        f"Spearman(z, margin) {values['z_margin_spearman']:.3f}"
    )
    for score, label in (("ll", "log loss"), ("brier", "Brier")):
        print(
            f"{label}: proportional {values[f'{score}_prop']:.6f}, "
            f"Shin {values[f'{score}_shin']:.6f}, gain {values[f'{score}_gain']:.6f} "
            f"[{values[f'{score}_gain_low']:.6f}, {values[f'{score}_gain_high']:.6f}]"
        )


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    frame = shin.scored(matches)
    print(f"Priced: {len(frame):,} of {len(matches):,} matches have all three opening 1X2 prices")
    print(f"Largest |sum of Shin probabilities - 1|: {shin.sum_error(frame):.1e}")
    show("All matches", summary(frame))
    for cohort, group in frame.groupby("season_cohort"):
        show(f"Season cohort {cohort}", summary(group))
    print("\n== Observed vs implied rate by price band (every outcome of every match)")
    print(price_table(frame).to_string(index=False, float_format=lambda v: f"{v:.4f}"))


if __name__ == "__main__":
    main()
