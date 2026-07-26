"""SUPERSEDED (2026-07-25) — kept only until it is committed, then delete.

Replaced by `modelling/experiment.py`, which tests the same question with a preregistered
family list, Holm correction over six tests, a single holdout opening, and metrics
at all three levels of the chain. This module runs ~15 uncorrected bucket tests
against `is_comeback`, most of them re-testing LEAGUE_STUDY F10's graveyard on a
corpus 11x smaller than the one that established it — a false-discovery generator.
Its reusable helpers (`wilson_ci`, `required_n`) now live in `modelling/experiment.py`.
For the verdict see `notes/RESULTS.md`.

Original docstring follows.

Feature-engineering pass over the scraped corpus: which pre-match features
move is_comeback / is_seven_or_more_goals off the base rate, walk-forward tested
(train = 2023-24 + 2024-25, test = 2025-26), pooled across leagues (justified by
LEAGUE_STUDY.md F1: leagues don't differ in comeback rate).

All feature families are valid pre-match inputs: the detail page's history
widgets are match-anchored (validated July 2026 on all 36,597 history records —
every record predates its target match; see HANDOFF.md S4), so recent-form and
H2H columns carry no post-match information. Labels are the feature's source:
league scraper, detail odds/strength/guess, or detail form/h2h.

Run: `uv run python -m modelling.analysis`
"""

import glob
import math
import os

import pandas as pd

DATA_DIR = "data"
TRAIN_SEASONS = {"2023-2024", "2024-2025"}
TEST_SEASONS = {"2025-2026"}


def _enriched_csvs() -> list[str]:
    return sorted(glob.glob(os.path.join(DATA_DIR, "*_enriched.csv")))


def load_corpus() -> pd.DataFrame:
    frames = []
    for path in _enriched_csvs():
        df = pd.read_csv(path)
        df["split"] = df["season"].map(
            lambda s: "train" if s in TRAIN_SEASONS else ("test" if s in TEST_SEASONS else None)
        )
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval for a binomial rate — safe at small n / rare events."""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = p + z**2 / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return ((center - margin) / denom, (center + margin) / denom)


def required_n(base_rate: float, target_rate: float, power: float = 0.8) -> int:
    """Approx sample size (one-sample proportion test, alpha=.05) to detect
    base_rate -> target_rate via Cohen's h effect size."""
    h = 2 * math.asin(math.sqrt(target_rate)) - 2 * math.asin(math.sqrt(base_rate))
    if h == 0:
        return 10**9
    z_alpha, z_beta = 1.96, 0.84  # power ~0.8
    return math.ceil(((z_alpha + z_beta) / h) ** 2)


def bucket_report(df: pd.DataFrame, feature: str, target: str, source: str, bins: int = 3) -> None:
    train = df[df["split"] == "train"].dropna(subset=[feature, target])
    test = df[df["split"] == "test"].dropna(subset=[feature, target])
    if len(train) < 30 or len(test) < 10:
        print(
            f"  [{feature}] skipped: insufficient non-null rows "
            f"(train={len(train)}, test={len(test)})"
        )
        return

    try:
        _, edges_arr = pd.qcut(train[feature], bins, retbins=True, duplicates="drop")
    except ValueError:
        print(f"  [{feature}] skipped: could not form {bins} distinct buckets")
        return
    edges: list[float] = list(edges_arr)
    edges[0], edges[-1] = -float("inf"), float("inf")

    test_base = test[target].mean()
    header = f"test n={len(test)}, test base rate={test_base:.3%}"
    print(f"\n  [{source}] {feature}  (train n={len(train)}, {header})")

    test_bucketed = pd.cut(test[feature], edges)
    for label, group in test.groupby(test_bucketed, observed=True):
        n = len(group)
        if n == 0:
            continue
        k = int(group[target].sum())
        rate = k / n
        lo, hi = wilson_ci(k, n)
        lift = rate / test_base if test_base else float("nan")
        flag = " <-- CI excludes base rate" if (lo > test_base or hi < test_base) else ""
        print(
            f"      {label!s:>22}  n={n:4d}  rate={rate:6.2%}  "
            f"95% CI [{lo:5.2%}, {hi:5.2%}]  lift={lift:4.2f}x{flag}"
        )


def categorical_report(df: pd.DataFrame, feature: str, target: str, source: str) -> None:
    train = df[df["split"] == "train"].dropna(subset=[feature, target])
    test = df[df["split"] == "test"].dropna(subset=[feature, target])
    if len(train) < 30 or len(test) < 10:
        print(f"  [{feature}] skipped: insufficient non-null rows")
        return
    test_base = test[target].mean()
    header = f"test n={len(test)}, test base rate={test_base:.3%}"
    print(f"\n  [{source}] {feature}  (train n={len(train)}, {header})")
    for label, group in test.groupby(feature, observed=True):
        n = len(group)
        k = int(group[target].sum())
        rate = k / n
        lo, hi = wilson_ci(k, n)
        lift = rate / test_base if test_base else float("nan")
        flag = " <-- CI excludes base rate" if (lo > test_base or hi < test_base) else ""
        print(
            f"      {label!s:>22}  n={n:4d}  rate={rate:6.2%}  "
            f"95% CI [{lo:5.2%}, {hi:5.2%}]  lift={lift:4.2f}x{flag}"
        )


def corpus_overview(df: pd.DataFrame) -> None:
    print("=" * 78)
    print("CORPUS OVERVIEW")
    print("=" * 78)
    for (league, season), group in df.groupby(["league_name", "season"]):
        n = len(group)
        cb = int(group["is_comeback"].sum())
        sp = int(group["is_seven_or_more_goals"].sum())
        print(
            f"  {league:26s} {season}  n={n:4d}  comeback={cb:3d} ({cb / n:5.2%})  "
            f"7+={sp:3d} ({sp / n:5.2%})"
        )
    total_n = len(df)
    total_cb = int(df["is_comeback"].sum())
    pooled_rate = total_cb / total_n
    print(f"\n  POOLED (all leagues/seasons): n={total_n}  comeback={total_cb} ({pooled_rate:.3%})")
    for split in ("train", "test"):
        sub = df[df["split"] == split]
        cb = int(sub["is_comeback"].sum())
        print(f"    {split}: n={len(sub)}  comeback={cb} ({cb / len(sub):.3%})")

    print("\n  Power check (rare-event math, HANDOFF S6):")
    test_n = len(df[df["split"] == "test"])
    base = df[df["split"] == "train"]["is_comeback"].mean()
    for target_rate in (0.08, 0.10):
        n_needed = required_n(base, target_rate)
        print(
            f"    detecting {base:.1%} -> {target_rate:.0%} at 80% power needs n~{n_needed} "
            f"(test set has {test_n})"
        )


def league_split_check(df: pd.DataFrame) -> None:
    print("\n" + "=" * 78)
    print("F1 PREREGISTERED BAR CHECK (LEAGUE_STUDY.md): Ekstraklasa as comeback-candidate?")
    print("=" * 78)
    for league, group in df.groupby("league_name"):
        n = len(group)
        cb = int(group["is_comeback"].sum())
        rate = cb / n
        lo, hi = wilson_ci(cb, n)
        print(f"  {league}: n={n}  comeback={cb}  rate={rate:.2%}  95% CI [{lo:.2%}, {hi:.2%}]")
    print("  Bar (F1): >=8% over >=600 matches, persistence-tested, with a mechanism story.")
    eks = df[df["league_name"] == "poland_ekstraklasa"]
    train_rate = eks[eks["split"] == "train"]["is_comeback"].mean()
    test_rate = eks[eks["split"] == "test"]["is_comeback"].mean()
    print(
        f"  Ekstraklasa persistence check: train (23-24+24-25) rate={train_rate:.2%} "
        f"vs test (25-26) rate={test_rate:.2%}"
    )


def main() -> None:
    df = load_corpus()
    corpus_overview(df)
    league_split_check(df)

    print("\n" + "=" * 78)
    print("FEATURE ENGINEERING: is_comeback")
    print("=" * 78)
    print("(bucket edges from train quantiles, evaluated on held-out test season)")

    bucket_report(df, "position_gap", "is_comeback", "league")
    bucket_report(df, "round", "is_comeback", "league")
    bucket_report(df, "favorite_odds", "is_comeback", "league")
    bucket_report(df, "underdog_odds", "is_comeback", "league")
    df["odds_skew"] = (df["implied_prob_home"] - df["implied_prob_away"]).abs()
    bucket_report(df, "odds_skew", "is_comeback", "league (engineered)")
    categorical_report(df, "is_monday", "is_comeback", "league")
    categorical_report(df, "is_midweek", "is_comeback", "league")
    categorical_report(df, "favorite", "is_comeback", "league (categorical)")

    bucket_report(df, "odds1x2_init_home", "is_comeback", "detail odds")
    df["strength_gap"] = (df["strength_home"] - df["strength_away"]).abs()
    bucket_report(df, "strength_gap", "is_comeback", "detail strength")
    df["guess_skew"] = (df["guess_home_pct"] - df["guess_away_pct"]).abs()
    bucket_report(df, "guess_skew", "is_comeback", "detail crowd guess")

    df["combined_recent_gf"] = df["home_recent_gf_avg"] + df["away_recent_gf_avg"]
    bucket_report(df, "combined_recent_gf", "is_comeback", "detail form/h2h")
    bucket_report(df, "h2h_avg_total_goals", "is_comeback", "detail form/h2h")
    bucket_report(df, "home_recent_ppg", "is_comeback", "detail form/h2h")
    bucket_report(df, "away_recent_ppg", "is_comeback", "detail form/h2h")

    print("\n" + "=" * 78)
    print("FEATURE ENGINEERING: is_seven_or_more_goals (secondary target)")
    print("=" * 78)
    bucket_report(df, "odds_skew", "is_seven_or_more_goals", "league (engineered)")
    bucket_report(df, "favorite_odds", "is_seven_or_more_goals", "league")
    bucket_report(df, "combined_recent_gf", "is_seven_or_more_goals", "detail form/h2h")
    bucket_report(df, "h2h_avg_total_goals", "is_seven_or_more_goals", "detail form/h2h")


if __name__ == "__main__":
    main()
