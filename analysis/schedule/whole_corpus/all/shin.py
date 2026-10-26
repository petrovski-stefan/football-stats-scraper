"""Shin's method on the whole corpus, all matches pooled.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`. Prints the corpus line; z and the margin;
Shin against proportional margin removal, scored on the full-time result, for all matches
and per season cohort; and observed against implied rates by price band.

Run: `uv run python -m analysis.schedule.whole_corpus.all.shin`
"""

import pandas as pd

from analysis import corpus, stats
from analysis.methods import shin


def summary(scored_df: pd.DataFrame) -> dict[str, float]:
    """z, the margin, and both methods' mean scores with Shin's gain and its cluster CI."""

    shin_z = scored_df["shin_z"]
    out = {
        "matches": float(len(scored_df)),
        "z_median": float(shin_z.median()),
        "z_q1": float(shin_z.quantile(0.25)),
        "z_q3": float(shin_z.quantile(0.75)),
        "z_mean": float(shin_z.mean()),
        "margin_median": float(scored_df["margin"].median()),
        "z_margin_spearman": float(shin_z.corr(scored_df["margin"], method="spearman")),
    }

    for score in ("ll", "brier"):
        low, high = stats.cluster_bootstrap_ci(scored_df[f"{score}_gain"], scored_df["cluster"])
        out |= {
            f"{score}_prop": float(scored_df[f"{score}_prop"].mean()),
            f"{score}_shin": float(scored_df[f"{score}_shin"].mean()),
            f"{score}_gain": float(scored_df[f"{score}_gain"].mean()),
            f"{score}_gain_low": low,
            f"{score}_gain_high": high,
        }

    return out


def price_table(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Per price band: outcomes, the observed rate with its Wilson CI, and each method's mean."""

    outcome_rows_df = shin.outcome_rows(scored_df)
    outcome_rows_df["band"] = pd.cut(outcome_rows_df["price"], shin.PRICE_EDGES)

    table = []
    for band, band_df in outcome_rows_df.groupby("band", observed=True):
        hits, outcome_count = int(band_df["hit"].sum()), len(band_df)
        low, high = stats.wilson_ci(hits, outcome_count)

        table.append(
            {
                "band": str(band),
                "outcomes": outcome_count,
                "observed": hits / outcome_count,
                "low": low,
                "high": high,
                "prop": float(band_df["prop"].mean()),
                "shin": float(band_df["shin"].mean()),
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
    """Entry point: print Shin's method on the whole corpus."""

    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    scored_df = shin.scored(matches_df)
    print(
        f"Priced: {len(scored_df):,} of "
        f"{len(matches_df):,} matches have all three opening 1X2 prices"
    )
    print(f"Largest |sum of Shin probabilities - 1|: {shin.sum_error(scored_df):.1e}")

    show("All matches", summary(scored_df))
    for cohort, cohort_df in scored_df.groupby("season_cohort"):
        show(f"Season cohort {cohort}", summary(cohort_df))

    print("\n== Observed vs implied rate by price band (every outcome of every match)")
    print(price_table(scored_df).to_string(index=False, float_format=lambda value: f"{value:.4f}"))


if __name__ == "__main__":
    main()
