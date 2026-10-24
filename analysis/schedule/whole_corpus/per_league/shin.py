"""Shin's method per league: one heterogeneity test per quantity, and shrunk league values.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/SHIN.md`. No league is tested on its own:
per-league testing is Dead in `notes/WORKING/STATE.md`. The table is sorted by league name,
not by value.

Run: `uv run python -m analysis.schedule.whole_corpus.per_league.shin`
"""

import pandas as pd

from analysis import corpus, stats
from analysis.methods import shin

# Per-league quantities: the mean insider share, and Shin's mean log-loss gain.
QUANTITIES = {"z": "shin_z", "gain": "ll_gain"}


def league_table(
    scored_df: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, stats.Heterogeneity]]:
    """Per league: matches, and each quantity's raw and shrunk mean; one test per quantity."""
    grouped = scored_df.groupby("s1_league_id")
    sizes = grouped.size()
    league_table_df = pd.DataFrame({"league": grouped["s1_league_name"].first(), "matches": sizes})

    tests: dict[str, stats.Heterogeneity] = {}
    for name, column in QUANTITIES.items():
        means = grouped[column].mean()
        variances = grouped[column].var() / sizes
        tests[name] = stats.heterogeneity(means, variances)
        league_table_df[name] = means
        league_table_df[f"{name}_shrunk"] = stats.shrink(means, variances, tests[name])

    return league_table_df.sort_values("league"), tests


def cohort_stability(scored_df: pd.DataFrame, column: str) -> tuple[float, int]:
    """Spearman correlation of the league means between the two season cohorts, and its n."""
    league_means_df = (
        scored_df.groupby(["s1_league_id", "season_cohort"])[column].mean().unstack().dropna()
    )
    return float(
        league_means_df.iloc[:, 0].corr(league_means_df.iloc[:, 1], method="spearman")
    ), len(league_means_df)


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    scored_df = shin.scored(matches_df)
    league_table_df, tests = league_table(scored_df)
    print(f"Priced: {len(scored_df):,} matches in {len(league_table_df)} leagues")

    for name, column in QUANTITIES.items():
        het, shrunk = tests[name], league_table_df[f"{name}_shrunk"]
        cohort_correlation, cohort_count = cohort_stability(scored_df, column)

        print(f"\n== {name} ({column})")
        print(
            f"pooled {het.pooled:.6f}; Cochran's Q {het.cochran_q:.1f} on "
            f"{het.degrees_of_freedom} df, "
            f"p = {het.p_value:.3g}; tau {het.tau_squared**0.5:.6f}"
        )
        print(
            f"shrunk league values: min {shrunk.min():.6f}, median {shrunk.median():.6f}, "
            f"max {shrunk.max():.6f}"
        )
        print(
            f"league means, season cohort 1 vs 2: Spearman {cohort_correlation:.3f} over "
            f"{cohort_count} leagues"
        )

    print("\n== Leagues (sorted by name)")
    print(league_table_df.to_string(index=False, float_format=lambda value: f"{value:.5f}"))


if __name__ == "__main__":
    main()
