"""The pre-match exclusion filter study (notes/RECORD/PREREGISTRATION_FILTER.md).

Not a prediction study. The question is whether a large subset of matches can be
identified pre-match in which a comeback is effectively impossible — judged on
**miss rate**, not lift, which is the opposite metric from `modelling/experiment.py`.

    Bar: exclude >= 30% of matches with the excluded set's comeback rate at a
         Wilson 95% UPPER bound below 2%.

Everything is walk-forward: each round is predicted from strictly earlier matches
only. No clean holdout remains (see PREREGISTRATION_FILTER.md S6), so the closed
feature list and the fixed bar are the compensating controls.

Run: `uv run python -m modelling.filter_study --curve` then `--bar`.
"""

import argparse

import numpy as np
import pandas as pd

from features import engine
from modelling import runs, scoreline
from modelling.experiment import MIN_TRAIN, wilson_ci

BAR_COVERAGE = 0.30
BAR_UPPER_BOUND = 0.02
CURVE_POINTS = (0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50, 0.55, 0.60)
SEED = 0


def walk_forward_scoreline(df: pd.DataFrame) -> pd.DataFrame:
    """Predict each round's scoreline distribution from strictly earlier matches."""
    df = df.sort_values("date").reset_index(drop=True)
    chunks = []
    for _, block in df.groupby(["league_name", "season", "round"], sort=False):
        train = df[df["date"] < block["date"].min()]
        if len(train) < MIN_TRAIN:
            continue
        model = scoreline.ScorelineModel().fit(train)
        predicted = model.predict(block)
        chunks.append(
            block.assign(
                p_comeback=predicted["p_comeback"].to_numpy(),
                p_total_le2=predicted["p_total_le2"].to_numpy(),
                p_ft_draw=predicted["p_ft_draw"].to_numpy(),
            )
        )
    if not chunks:
        raise RuntimeError("walk-forward produced no predictions — check MIN_TRAIN")
    return pd.concat(chunks, ignore_index=True)


def _exclude(scores: np.ndarray, y: np.ndarray, frac: float) -> tuple[int, int, float, float]:
    """Exclude the `frac` lowest-scoring matches; return (n, hits, wilson lo, hi)."""
    n = int(len(scores) * frac)
    picked = y[np.argsort(scores, kind="stable")[:n]]
    hits = int(picked.sum())
    lo, hi = wilson_ci(hits, n)
    return n, hits, lo, hi


def coverage_curve(predictions: pd.DataFrame) -> list[tuple[float, int, int, float]]:
    y = predictions["is_comeback"].to_numpy().astype(float)
    base = float(y.mean())
    scores = predictions["p_comeback"].to_numpy()

    print()
    print("  ## Coverage vs miss rate — the filter (ranked by model P(comeback))")
    print(f"     corpus n={len(y)}  comebacks={int(y.sum())}  base rate={base:.2%}")
    print("     coverage      n   missed   miss rate   95% CI            expected if useless")
    rows = []
    for frac in CURVE_POINTS:
        n, hits, lo, hi = _exclude(scores, y, frac)
        rows.append((frac, n, hits, hi))
        print(
            f"       {frac:5.0%}    {n:5d}   {hits:5d}   {hits / n:8.2%}   "
            f"[{lo:5.2%},{hi:6.2%}]        {n * base:6.1f}"
        )
    return rows


def benchmarks(predictions: pd.DataFrame) -> None:
    y = predictions["is_comeback"].to_numpy().astype(float)
    n_bar = int(len(y) * BAR_COVERAGE)

    print()
    print(f"  ## Benchmarks at the bar's {BAR_COVERAGE:.0%} coverage (n={n_bar})")

    # 1. Random exclusion — the null.
    rng = np.random.default_rng(SEED)
    draws = [float(y[rng.choice(len(y), size=n_bar, replace=False)].sum()) for _ in range(2000)]
    print(
        f"     random exclusion        missed {np.mean(draws):6.1f} on average "
        f"(5th-95th pct {np.percentile(draws, 5):.0f}-{np.percentile(draws, 95):.0f})"
    )

    # 2. The strawman the pilot effectively ran: exclude the lowest implied totals.
    n, hits, _, hi = _exclude(predictions["mkt_tot"].to_numpy(), y, BAR_COVERAGE)
    print(f"     naive lowest mkt_tot    missed {hits:6d}   rate={hits / n:.2%}  UB={hi:.2%}")

    # 3. The model.
    n, hits, _, hi = _exclude(predictions["p_comeback"].to_numpy(), y, BAR_COVERAGE)
    print(f"     scoreline filter        missed {hits:6d}   rate={hits / n:.2%}  UB={hi:.2%}")

    # 4. The oracle — post-match by construction, hence a ceiling and not a filter.
    oracle_scores = predictions["total_goals"].to_numpy().astype(float)
    n_or, hits_or, _, hi_or = _exclude(oracle_scores, y, BAR_COVERAGE)
    print(
        f"     ORACLE (knows the total) missed {hits_or:5d}   rate={hits_or / n_or:.2%}  "
        f"UB={hi_or:.2%}"
    )
    full = predictions[predictions["total_goals"] <= 2]
    _, hi_f = wilson_ci(int(full["is_comeback"].sum()), len(full))
    print(
        f"     ORACLE at its natural cut (<=2 goals): coverage={len(full) / len(y):.1%}  "
        f"missed={int(full['is_comeback'].sum())}  UB={hi_f:.2%}"
    )

    # How much of the oracle's achievable exclusion does the model actually find?
    excluded = np.argsort(predictions["p_comeback"].to_numpy(), kind="stable")[:n_bar]
    truly_impossible = (predictions["total_goals"].to_numpy()[excluded] <= 2).mean()
    baseline_share = float((predictions["total_goals"] <= 2).mean())
    print()
    print("  ## Oracle recovery")
    print("     matches that genuinely could not produce a comeback (<=2 goals):")
    print(f"       corpus-wide          {baseline_share:.1%}")
    print(f"       inside the filter's excluded set  {truly_impossible:.1%}")
    lift = truly_impossible / baseline_share if baseline_share else float("nan")
    print(
        f"       enrichment           {lift:.2f}x  "
        f"(1.00x = the filter finds impossible matches no better than chance)"
    )


def sanity(predictions: pd.DataFrame) -> None:
    """Is the filter even finding low-scoring matches? Distinguishes a broken filter
    from a true null."""
    n_bar = int(len(predictions) * BAR_COVERAGE)
    order = np.argsort(predictions["p_comeback"].to_numpy(), kind="stable")
    excluded = predictions.iloc[order[:n_bar]]
    kept = predictions.iloc[order[n_bar:]]
    print()
    print("  ## Sanity — does the excluded set actually look low-scoring?")
    print("                        excluded   kept")
    for label, column in (
        ("mean total goals", "total_goals"),
        ("model P(total<=2)", "p_total_le2"),
        ("model P(FT draw)", "p_ft_draw"),
        ("model P(comeback)", "p_comeback"),
    ):
        print(f"     {label:20s} {excluded[column].mean():8.3f}  {kept[column].mean():6.3f}")
    draw_ex = (excluded["ft_home_goals"] == excluded["ft_away_goals"]).mean()
    draw_kept = (kept["ft_home_goals"] == kept["ft_away_goals"]).mean()
    print(f"     {'actual FT draw rate':20s} {draw_ex:8.3f}  {draw_kept:6.3f}")


def evaluate_bar(predictions: pd.DataFrame) -> bool:
    y = predictions["is_comeback"].to_numpy().astype(float)
    n, hits, _, hi = _exclude(predictions["p_comeback"].to_numpy(), y, BAR_COVERAGE)
    passed = hi < BAR_UPPER_BOUND
    print()
    print("  ## THE BAR")
    print(f"     exclude >= {BAR_COVERAGE:.0%} of matches with the excluded set's comeback rate")
    print(f"     at a Wilson 95% upper bound below {BAR_UPPER_BOUND:.0%}")
    print(
        f"       excluded n={n}  comebacks missed={hits}  rate={hits / n:.2%}  upper bound={hi:.2%}"
    )
    print(f"     **{'PASSED' if passed else 'NOT PASSED'}**")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--curve", action="store_true", help="coverage/miss curve + benchmarks")
    parser.add_argument(
        "--bar", action="store_true", help="the curve + the preregistered pass/fail"
    )
    args = parser.parse_args()
    if not (args.curve or args.bar):
        parser.print_help()
        return

    matrix = engine.build_features()
    usable = matrix[~engine.in_burn_in(matrix)].copy()

    with runs.recorded(f"filter_study_{'bar' if args.bar else 'curve'}"):
        if not scoreline.self_check(usable):
            raise SystemExit("scoreline self-check failed — see PREREGISTRATION_FILTER.md S8")
        if not scoreline.leak_check(usable):
            raise SystemExit("leak check failed — post-match data reached the prediction path")

        print("\nrunning walk-forward…")
        predictions = walk_forward_scoreline(usable)

        print("=" * 78)
        print("PRE-MATCH EXCLUSION FILTER")
        print("=" * 78)
        coverage_curve(predictions)
        benchmarks(predictions)
        sanity(predictions)
        if args.bar:
            evaluate_bar(predictions)


if __name__ == "__main__":
    main()
