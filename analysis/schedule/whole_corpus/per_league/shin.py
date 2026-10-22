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
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, dict[str, stats.Heterogeneity]]:
    """Per league: matches, and each quantity's raw and shrunk mean; one test per quantity."""
    grouped = frame.groupby("s1_league_id")
    sizes = grouped.size()
    table = pd.DataFrame({"league": grouped["s1_league_name"].first(), "matches": sizes})

    tests: dict[str, stats.Heterogeneity] = {}
    for name, column in QUANTITIES.items():
        means = grouped[column].mean()
        variances = grouped[column].var() / sizes
        tests[name] = stats.heterogeneity(means, variances)
        table[name] = means
        table[f"{name}_shrunk"] = stats.shrink(means, variances, tests[name])

    return table.sort_values("league"), tests


def cohort_stability(frame: pd.DataFrame, column: str) -> tuple[float, int]:
    """Spearman correlation of the league means between the two season cohorts, and its n."""
    means = frame.groupby(["s1_league_id", "season_cohort"])[column].mean().unstack().dropna()
    return float(means.iloc[:, 0].corr(means.iloc[:, 1], method="spearman")), len(means)


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))

    frame = shin.scored(matches)
    table, tests = league_table(frame)
    print(f"Priced: {len(frame):,} matches in {len(table)} leagues")

    for name, column in QUANTITIES.items():
        het, shrunk = tests[name], table[f"{name}_shrunk"]
        r, n = cohort_stability(frame, column)

        print(f"\n== {name} ({column})")
        print(
            f"pooled {het.pooled:.6f}; Cochran's Q {het.q:.1f} on {het.df} df, "
            f"p = {het.p:.3g}; tau {het.tau2**0.5:.6f}"
        )
        print(
            f"shrunk league values: min {shrunk.min():.6f}, median {shrunk.median():.6f}, "
            f"max {shrunk.max():.6f}"
        )
        print(f"league means, season cohort 1 vs 2: Spearman {r:.3f} over {n} leagues")

    print("\n== Leagues (sorted by name)")
    print(table.to_string(index=False, float_format=lambda v: f"{v:.5f}"))


if __name__ == "__main__":
    main()
