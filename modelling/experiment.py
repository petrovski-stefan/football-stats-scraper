"""Evaluation harness for the F12 re-test (see notes/PREREGISTRATION.md).

`--dev` runs an expanding-window walk-forward over the development seasons: all
screening, tuning and family selection happen here. Rerunnable. The run's output is
saved to `notes/runs/` (`modelling/runs.py`).

The holdout mode, which opened 2025-26, was deleted 2026-10-02: that season is spent
(PREREGISTRATION.md A9), and the next confirmatory test needs a new holdout definition.

The screen reports two levels because their power differs by an order of magnitude:
factor 1 (the half-time state, P(HT non-draw)) and the product, P(comeback).

Run: `uv run python -m modelling.experiment --dev`
"""

import argparse
import math

import numpy as np
import pandas as pd

from features import chain, engine
from features.engine import FAMILIES
from modelling import runs

MIN_TRAIN = 200
BOOTSTRAP_DRAWS = 10000
SEED = 0
# Preregistered L2 grid, tuned on dev only.
ALPHA_GRID = (0.1, 0.3, 1.0, 3.0, 10.0)


# --- Metrics ------------------------------------------------------------------


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def log_loss(p: np.ndarray, y: np.ndarray) -> float:
    q = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q)))


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — safe at small n / rare events.

    Originally in `modelling/analysis.py`, which was deleted 2026-09-20.
    """
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = p + z**2 / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return ((center - margin) / denom, (center + margin) / denom)


def required_n(base_rate: float, target_rate: float) -> int:
    """Approx n to detect base_rate -> target_rate at 80% power, alpha .05 (Cohen's h).

    Kept from `modelling/analysis.py` (deleted 2026-09-20): the rare-event power check
    HANDOFF S6 demands before any claim that a gate "works" or "fails".
    """
    h = 2 * math.asin(math.sqrt(target_rate)) - 2 * math.asin(math.sqrt(base_rate))
    if h == 0:
        return 10**9
    z_alpha, z_beta = 1.96, 0.84
    return math.ceil(((z_alpha + z_beta) / h) ** 2)


def paired_bootstrap(
    p_a: np.ndarray, p_b: np.ndarray, y: np.ndarray, draws: int = BOOTSTRAP_DRAWS
) -> tuple[float, float, float]:
    """Paired bootstrap on Brier(a) - Brier(b), returning (mean, lo, hi).

    Negative means model `a` is better; the bar is met when hi < 0.
    """
    rng = np.random.default_rng(SEED)
    n = len(y)
    idx = rng.integers(0, n, size=(draws, n))
    loss_a = (p_a - y) ** 2
    loss_b = (p_b - y) ** 2
    diffs = loss_a[idx].mean(axis=1) - loss_b[idx].mean(axis=1)
    lo, hi = np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)
    return float(np.mean(diffs)), float(lo), float(hi)


def holm(pvalues: dict[str, float]) -> dict[str, tuple[float, bool]]:
    """Holm-Bonferroni: returns {name: (adjusted p, significant at .05)}."""
    ordered = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(ordered)
    out: dict[str, tuple[float, bool]] = {}
    running = 0.0
    for i, (name, p) in enumerate(ordered):
        adjusted = min(1.0, max(running, (m - i) * p))
        running = adjusted
        out[name] = (adjusted, adjusted < 0.05)
    return out


# --- Walk-forward -------------------------------------------------------------


def walk_forward(df: pd.DataFrame, feature_names: list[str], alpha: float) -> pd.DataFrame:
    """Expanding-window walk-forward: predict each round from strictly earlier matches.

    Training pools across leagues, but is
    always cut off by date, so no future match ever informs a prediction.
    """
    df = df.sort_values("date").reset_index(drop=True)
    chunks = []
    for (league, season, rnd), block in df.groupby(["league_name", "season", "round"], sort=False):
        cutoff = block["date"].min()
        train = df[df["date"] < cutoff]
        if len(train) < MIN_TRAIN:
            continue
        probability, mu_home, mu_away = chain.fit_predict(train, block, feature_names, alpha)
        chunks.append(
            block.assign(
                p_comeback=probability,
                mu_home=mu_home,
                mu_away=mu_away,
                p_ht_nondraw=1.0 - _p_ht_draw(mu_home, mu_away),
                _league=league,
                _season=season,
                _round=rnd,
            )
        )
    if not chunks:
        raise RuntimeError("walk-forward produced no predictions — check MIN_TRAIN")
    return pd.concat(chunks, ignore_index=True)


def _p_ht_draw(mu_home: np.ndarray, mu_away: np.ndarray) -> np.ndarray:
    from scipy.stats import skellam

    return np.asarray(skellam.pmf(0, mu_home, mu_away), dtype=float)


def _targets(df: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    y_comeback = df["is_comeback"].to_numpy().astype(float)
    y_nondraw = (df["ht_home_goals"] != df["ht_away_goals"]).to_numpy().astype(float)
    return y_comeback, y_nondraw


# --- Dev screening ------------------------------------------------------------


def tune_alpha(dev: pd.DataFrame, feature_names: list[str]) -> tuple[float, float]:
    """Pick L2 strength by walk-forward Brier on dev. Never sees the holdout."""
    best_alpha, best_score = ALPHA_GRID[0], float("inf")
    for alpha in ALPHA_GRID:
        predictions = walk_forward(dev, feature_names, alpha)
        y, _ = _targets(predictions)
        score = brier(predictions["p_comeback"].to_numpy(), y)
        print(f"      alpha={alpha:5.1f}  dev walk-forward Brier={score:.6f}")
        if score < best_score:
            best_alpha, best_score = alpha, score
    return best_alpha, best_score


def dev_screen(dev: pd.DataFrame) -> None:
    print("=" * 78)
    print("DEV SCREEN — expanding-window walk-forward, 2023-24 + 2024-25")
    print("=" * 78)
    print(f"  n={len(dev)}  comebacks={int(dev['is_comeback'].sum())}")

    print("\n  Tuning L2 on the baseline feature set:")
    alpha, _ = tune_alpha(dev, chain.baseline_feature_set())
    print(f"    chosen alpha={alpha}")

    baseline = walk_forward(dev, chain.baseline_feature_set(), alpha)
    y_cb, y_nd = _targets(baseline)
    base_rate = float(dev["is_comeback"].mean())
    p_const = np.full(len(baseline), base_rate)

    print("\n  Reference Briers (product level):")
    print(f"    constant             {brier(p_const, y_cb):.6f}")
    print(f"    baseline_chain_odds  {brier(baseline['p_comeback'].to_numpy(), y_cb):.6f}")
    print("\n  Reference Briers (factor 1, P(HT non-draw)):")
    print(f"    constant             {brier(np.full(len(baseline), float(y_nd.mean())), y_nd):.6f}")
    print(f"    baseline_chain_odds  {brier(baseline['p_ht_nondraw'].to_numpy(), y_nd):.6f}")

    print("\n  Per-family screen (baseline + one family), Holm-corrected:")
    pvalues: dict[str, float] = {}
    family_rows: list[tuple[str, float, float, float, float]] = []
    for family in FAMILIES:
        predictions = walk_forward(dev, chain.family_feature_set(family), alpha)
        y_f, y_fnd = _targets(predictions)
        p_family = predictions["p_comeback"].to_numpy()
        p_base = baseline["p_comeback"].to_numpy()
        mean, lo, hi = paired_bootstrap(p_family, p_base, y_f)
        # One-sided: how often does the family fail to beat the baseline?
        p_value = _bootstrap_pvalue(p_family, p_base, y_f)
        pvalues[family] = p_value
        f1 = brier(predictions["p_ht_nondraw"].to_numpy(), y_fnd)
        family_rows.append((family, brier(p_family, y_f), f1, mean, p_value))
        print(
            f"    {family:16s} product Brier={brier(p_family, y_f):.6f}  "
            f"factor1={f1:.6f}  dBrier={mean:+.6f} [{lo:+.6f},{hi:+.6f}]  p={p_value:.3f}"
        )

    adjusted = holm(pvalues)
    print("\n  Holm-corrected (6 tests):")
    for family, (p_adj, significant) in sorted(adjusted.items(), key=lambda kv: kv[1][0]):
        print(f"    {family:16s} p_adj={p_adj:.3f}  {'SURVIVES' if significant else 'dead'}")

    print("\n  Full candidate (all families):")
    candidate = walk_forward(dev, chain.candidate_feature_set(), alpha)
    y_c, y_cnd = _targets(candidate)
    mean, lo, hi = paired_bootstrap(
        candidate["p_comeback"].to_numpy(), baseline["p_comeback"].to_numpy(), y_c
    )
    print(
        f"    product Brier={brier(candidate['p_comeback'].to_numpy(), y_c):.6f}  "
        f"factor1={brier(candidate['p_ht_nondraw'].to_numpy(), y_cnd):.6f}"
    )
    print(f"    vs baseline: dBrier={mean:+.6f} [{lo:+.6f}, {hi:+.6f}]")


def _bootstrap_pvalue(p_a: np.ndarray, p_b: np.ndarray, y: np.ndarray) -> float:
    """One-sided bootstrap p: P(model a fails to beat model b)."""
    rng = np.random.default_rng(SEED)
    n = len(y)
    idx = rng.integers(0, n, size=(BOOTSTRAP_DRAWS, n))
    diffs = ((p_a - y) ** 2)[idx].mean(axis=1) - ((p_b - y) ** 2)[idx].mean(axis=1)
    return float(np.mean(diffs >= 0))


# --- Leakage regression -------------------------------------------------------


def leakage_check(raw: pd.DataFrame) -> bool:
    """Standing regression: the 'live' odds column must behave as a pre-kickoff price.

    A settled/in-play price would predict the result far better than the opening
    price. PREREGISTRATION.md S9 cleared it corpus-wide; this reruns per league.
    """
    print("\n" + "=" * 78)
    print("LEAKAGE REGRESSION — odds1x2_live_* must not know the result")
    print("=" * 78)
    ok = True
    for league, block in raw.groupby("league_name"):
        block = block.dropna(subset=["odds1x2_init_home", "odds1x2_live_home"])
        y = (block["ft_home_goals"] > block["ft_away_goals"]).to_numpy().astype(float)
        init = _normalised(block, "init")
        live = _normalised(block, "live")
        b_init, b_live = brier(init, y), brier(live, y)
        # A post-match price would collapse Brier; a pre-kickoff drift barely moves it.
        suspicious = b_live < b_init - 0.05
        ok = ok and not suspicious
        print(
            f"  {league:26s} Brier init={b_init:.4f}  live={b_live:.4f}  "
            f"{'SUSPICIOUS' if suspicious else 'ok'}"
        )
    print(f"  {'PASS' if ok else 'FAIL — quarantine close_odds_* and rerun'}")
    return ok


def _normalised(df: pd.DataFrame, kind: str) -> np.ndarray:
    inv_h = 1.0 / df[f"odds1x2_{kind}_home"]
    inv_d = 1.0 / df[f"odds1x2_{kind}_draw"]
    inv_a = 1.0 / df[f"odds1x2_{kind}_away"]
    return (inv_h / (inv_h + inv_d + inv_a)).to_numpy(dtype=float)


# --- Entry point --------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", action="store_true", help="walk-forward screen on dev seasons")
    args = parser.parse_args()
    if not args.dev:
        parser.print_help()
        return

    raw = engine.load_enriched()
    matrix = engine.build_features(raw)
    usable = matrix[~engine.in_burn_in(matrix)]
    dev = usable[usable["split"] == "dev"].copy()

    with runs.recorded("experiment_dev"):
        if not chain.replicate_f11(usable):
            raise SystemExit("F11 import invalid — see notes/PREREGISTRATION.md A3")
        if not leakage_check(raw):
            raise SystemExit("leakage regression failed")
        dev_screen(dev)


if __name__ == "__main__":
    main()
