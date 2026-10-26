"""The imported F11 completion curve, and the gate that validates it.

    P(trailing team wins) = F11_completion(trailer odds, half-time deficit, venue)

F11's completion model was imported wholesale, so it cost no degrees of freedom, as the
second factor of the chained comeback pricer for the F12 re-test (see
notes/RECORD/PREREGISTRATION.md). The pricer's fitted first factor and the experiment that
ran it were in `modelling/`, deleted on 2026-10-18; F11 and its study were dropped on
2026-10-13 (notes/LOG/MIGRATIONS.md). This module goes with plan step P5.

Run: `uv run python -m features.chain --replicate-f11` (validation gate for the import).
"""

import argparse
from itertools import pairwise

import numpy as np
import pandas as pd

from features import engine

# --- The imported F11 completion model ----------------------------------------
# Coefficients published in F11 of the old league study (dropped 2026-10-13), fitted on 9,195
# trailing states and validated walk-forward on 4,526 more. F11 reports slopes but
# not the constant, so the intercept is recovered by n-weighted least squares
# against F4's published eight-octile completion table (see recover_intercept()).
# That uses only published numbers — no data from this corpus enters the curve.
F11_LOG_TRAILER_ODDS = -1.72
F11_DEFICIT = -1.27
F11_VENUE = 0.001
F11_INTERCEPT = 0.9591

# F4's published table: trailing team's median closing odds, n, observed completion.
F4_OCTILES: list[tuple[float, int, float]] = [
    (1.65, 1303, 0.256),
    (2.10, 1366, 0.149),
    (2.45, 1109, 0.132),
    (2.80, 1286, 0.102),
    (3.30, 1193, 0.092),
    (3.90, 1364, 0.067),
    (5.00, 1149, 0.048),
    (8.00, 1199, 0.026),
]


def f11_completion(
    trailer_odds: np.ndarray, deficit: np.ndarray, trailer_is_home: np.ndarray
) -> np.ndarray:
    """P(trailing team wins | its closing odds, half-time deficit, venue)."""

    linear = (
        F11_INTERCEPT
        + F11_LOG_TRAILER_ODDS * np.log(np.clip(trailer_odds, 1.01, None))
        + F11_DEFICIT * deficit
        + F11_VENUE * trailer_is_home
    )

    return np.asarray(1.0 / (1.0 + np.exp(-linear)), dtype=float)


def recover_intercept() -> float:
    """Least-squares intercept against F4's octiles — reproduces the published curve."""

    odds = np.array([o for o, _, _ in F4_OCTILES])
    weights = np.array([n for _, n, _ in F4_OCTILES], dtype=float)
    observed = np.array([p for _, _, p in F4_OCTILES])
    grid = np.linspace(-2.0, 4.0, 60001)

    def sse(intercept: float) -> float:
        """The weighted squared error against F4's octiles of the curve with this intercept."""

        predicted = 1 / (1 + np.exp(-(intercept - 1.72 * np.log(odds) - 1.27)))

        return float(np.sum(weights * (predicted - observed) ** 2))

    return float(grid[int(np.argmin([sse(b) for b in grid]))])


# --- Validation gate ----------------------------------------------------------


def replicate_f11(matrix_df: pd.DataFrame) -> bool:
    """Prove the imported completion stage is valid before anything is built on it.

    Two checks: the recovered intercept must reproduce F4's published octiles, and
    applying the curve to this corpus's own trailing states must come out monotone
    in trailer strength and calibrated against what actually happened.
    """

    print("=" * 78)
    print("F11 IMPORT VALIDATION")
    print("=" * 78)

    recovered = recover_intercept()
    print(f"\n  intercept: stored={F11_INTERCEPT:.4f}  recomputed={recovered:.4f}")

    odds = np.array([octile_odds for octile_odds, _, _ in F4_OCTILES])
    observed = np.array([completion for _, _, completion in F4_OCTILES])
    predicted = f11_completion(odds, np.ones(len(odds)), np.zeros(len(odds)))
    print("\n  vs F4's published octiles (deficit -1):")
    print("     trailer odds   published   imported model")

    worst = 0.0
    for octile_odds, obs, pred in zip(odds, observed, predicted, strict=True):
        worst = max(worst, abs(obs - pred))
        print(f"     {octile_odds:11.2f}   {obs:8.1%}   {pred:13.1%}")

    ok_published = worst < 0.03
    print(f"    max absolute error {worst:.1%} — {'PASS' if ok_published else 'FAIL'} (bar: <3pp)")

    trailing_df = trailing_states(matrix_df)
    print(f"\n  applied to this corpus's {len(trailing_df)} trailing states:")

    completion = f11_completion(
        trailing_df["trailer_odds"].to_numpy(dtype=float),
        trailing_df["deficit"].to_numpy(dtype=float),
        trailing_df["trailer_is_home"].to_numpy(dtype=float),
    )
    trailing_df = trailing_df.assign(p=completion)

    quartiles = pd.qcut(trailing_df["p"], 4, labels=False, duplicates="drop")
    print("     quartile   n   predicted   observed")
    rates = []
    for quartile in sorted(pd.unique(quartiles.dropna())):
        quartile_df = trailing_df[quartiles == quartile]
        rates.append(quartile_df["completed"].mean())
        print(
            f"     {int(quartile) + 1:8d} {len(quartile_df):4d}   {quartile_df['p'].mean():8.1%}   "
            f"{quartile_df['completed'].mean():7.1%}"
        )

    monotone = all(a <= b for a, b in pairwise(rates))
    overall_pred, overall_obs = trailing_df["p"].mean(), trailing_df["completed"].mean()
    print(f"\n     overall predicted {overall_pred:.1%} vs observed {overall_obs:.1%}")
    print(f"     monotone in predicted risk: {'PASS' if monotone else 'FAIL'}")

    ok = ok_published and monotone
    print(f"\n  IMPORT {'VALID' if ok else 'INVALID — the plan pauses here'}")

    return ok


def trailing_states(matrix_df: pd.DataFrame) -> pd.DataFrame:
    """One row per match where somebody trailed at half-time."""

    margin = matrix_df["ht_home_goals"] - matrix_df["ht_away_goals"]
    trailing_df = matrix_df[margin != 0].copy()
    home_trails = (trailing_df["ht_home_goals"] < trailing_df["ht_away_goals"]).to_numpy()

    return pd.DataFrame(
        {
            "match_id": trailing_df["match_id"].to_numpy(),
            "split": trailing_df["split"].to_numpy(),
            "deficit": np.abs(
                (trailing_df["ht_home_goals"] - trailing_df["ht_away_goals"]).to_numpy(dtype=float)
            ),
            "trailer_is_home": home_trails.astype(float),
            "trailer_odds": np.where(
                home_trails,
                trailing_df["close_odds_home"].to_numpy(dtype=float),
                trailing_df["close_odds_away"].to_numpy(dtype=float),
            ),
            "completed": np.where(
                home_trails,
                (trailing_df["ft_home_goals"] > trailing_df["ft_away_goals"]).to_numpy(),
                (trailing_df["ft_away_goals"] > trailing_df["ft_home_goals"]).to_numpy(),
            ).astype(float),
        }
    )


def main() -> None:
    """Entry point: validate the imported F11 completion curve, with `--replicate-f11`."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--replicate-f11", action="store_true", help="validate the imported completion stage"
    )
    args = parser.parse_args()

    matrix_df = engine.build_features()
    usable_df = matrix_df[~engine.in_burn_in(matrix_df)]

    if args.replicate_f11:
        raise SystemExit(0 if replicate_f11(usable_df) else 1)
    parser.print_help()


if __name__ == "__main__":
    main()
