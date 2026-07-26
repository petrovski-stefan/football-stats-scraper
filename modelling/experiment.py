"""Evaluation harness for the F12 re-test (see notes/PREREGISTRATION.md).

Two modes, and the order matters:

  `--dev`      expanding-window walk-forward over the development seasons. All
               screening, tuning and family selection happen here. Rerunnable.
  `--holdout`  fit on all of dev, predict the untouched 2025-26 season, apply both
               preregistered bars, write notes/RESULTS.md. **Run once.**

Metrics are reported at three levels because their power differs by an order of
magnitude: factor 1 (the half-time state, ~591 holdout trials at 61%), factor 2
(completion, 361 trials / 33 positives) and the product (591 / 33).

Run: `uv run python -m modelling.experiment --dev`
"""

import argparse
import math
import os
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from features import chain, engine
from features.engine import FAMILIES

RESULTS_PATH = os.path.join("notes", "RESULTS.md")
RAW_OUTPUT_PATH = os.path.join("notes", "results_holdout_raw.txt")
MIN_TRAIN = 200
BOOTSTRAP_DRAWS = 10000
SEED = 0
# Preregistered L2 grid, tuned on dev only.
ALPHA_GRID = (0.1, 0.3, 1.0, 3.0, 10.0)


@dataclass
class ScreenResult:
    """What the dev screen decides, and the only thing the holdout is allowed to use."""

    alpha: float
    base_rate: float
    survivors: list[str] = field(default_factory=list)
    adjusted: dict[str, tuple[float, bool]] = field(default_factory=dict)


# --- Metrics ------------------------------------------------------------------


def brier(p: np.ndarray, y: np.ndarray) -> float:
    return float(np.mean((p - y) ** 2))


def log_loss(p: np.ndarray, y: np.ndarray) -> float:
    q = np.clip(p, 1e-9, 1 - 1e-9)
    return float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q)))


def wilson_ci(successes: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval — safe at small n / rare events. (from analysis.py)"""
    if n == 0:
        return (0.0, 0.0)
    p = successes / n
    denom = 1 + z**2 / n
    center = p + z**2 / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))
    return ((center - margin) / denom, (center + margin) / denom)


def required_n(base_rate: float, target_rate: float) -> int:
    """Approx n to detect base_rate -> target_rate at 80% power, alpha .05 (Cohen's h).

    Kept from the retired analysis.py: the rare-event power check HANDOFF S6 demands
    before any claim that a gate "works" or "fails".
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


def calibration_table(
    p: np.ndarray, y: np.ndarray, bins: int = 5
) -> list[tuple[int, float, float]]:
    """(n, mean predicted, observed) per quantile bin of predicted risk."""
    ranks = pd.qcut(pd.Series(p).rank(method="first"), bins, labels=False)
    rows = []
    for b in range(bins):
        mask = (ranks == b).to_numpy()
        if mask.sum():
            rows.append((int(mask.sum()), float(p[mask].mean()), float(y[mask].mean())))
    return rows


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

    Training pools across leagues (LEAGUE_STUDY F1: leagues don't differ), but is
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


def dev_screen(dev: pd.DataFrame) -> ScreenResult:
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
    survivors = []
    for family, (p_adj, significant) in sorted(adjusted.items(), key=lambda kv: kv[1][0]):
        print(f"    {family:16s} p_adj={p_adj:.3f}  {'SURVIVES' if significant else 'dead'}")
        if significant:
            survivors.append(family)

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

    return ScreenResult(alpha=alpha, base_rate=base_rate, survivors=survivors, adjusted=adjusted)


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


# --- Holdout ------------------------------------------------------------------


def holdout_run(dev: pd.DataFrame, holdout: pd.DataFrame, screen: ScreenResult) -> str:
    alpha = screen.alpha
    survivors = screen.survivors
    base_rate = screen.base_rate

    lines: list[str] = []

    def emit(text: str = "") -> None:
        print(text)
        lines.append(text)

    emit("=" * 78)
    emit("HOLDOUT — 2025-26, opened once")
    emit("=" * 78)
    emit(
        f"  n={len(holdout)}  comebacks={int(holdout['is_comeback'].sum())} "
        f"({holdout['is_comeback'].mean():.2%})"
    )

    y_cb, y_nd = _targets(holdout)
    p_const = np.full(len(holdout), base_rate)

    p_base, mu_bh, mu_ba = chain.fit_predict(dev, holdout, chain.baseline_feature_set(), alpha)
    p_cand, mu_ch, mu_ca = chain.fit_predict(dev, holdout, chain.candidate_feature_set(), alpha)
    nd_base = 1.0 - _p_ht_draw(mu_bh, mu_ba)
    nd_cand = 1.0 - _p_ht_draw(mu_ch, mu_ca)

    restricted_features = list(engine.CONTROLS) + [
        name for family in survivors for name in FAMILIES[family]
    ]
    p_restricted, _, _ = chain.fit_predict(dev, holdout, restricted_features, alpha)

    emit("")
    emit("  ## Level 1 — factor 1: the half-time state (well powered)")
    nd_const = np.full(len(holdout), float(y_nd.mean()))
    emit(f"    Brier P(HT non-draw), constant  {brier(nd_const, y_nd):.6f}")
    emit(f"    Brier P(HT non-draw), baseline  {brier(nd_base, y_nd):.6f}")
    emit(f"    Brier P(HT non-draw), candidate {brier(nd_cand, y_nd):.6f}")
    mean, lo, hi = paired_bootstrap(nd_cand, nd_base, y_nd)
    emit(
        f"    candidate vs baseline: dBrier={mean:+.6f}  95% CI [{lo:+.6f}, {hi:+.6f}]  "
        f"{'CANDIDATE BETTER' if hi < 0 else 'inconclusive'}"
    )
    mean_c, lo_c, hi_c = paired_bootstrap(nd_cand, nd_const, y_nd)
    emit(f"    candidate vs constant: dBrier={mean_c:+.6f}  95% CI [{lo_c:+.6f}, {hi_c:+.6f}]")

    emit("")
    emit("  ## Level 2 — factor 2: completion, the imported F11 curve")
    trailing = chain.trailing_states(holdout)
    y_comp = trailing["completed"].to_numpy(dtype=float)
    p_comp = chain.f11_completion(
        trailing["trailer_odds"].to_numpy(dtype=float),
        trailing["deficit"].to_numpy(dtype=float),
        trailing["trailer_is_home"].to_numpy(dtype=float),
    )
    comp_const = np.full(len(trailing), float(y_comp.mean()))
    emit(
        f"    trailing states n={len(trailing)}  completions={int(y_comp.sum())} "
        f"({y_comp.mean():.2%})"
    )
    emit(f"    Brier, constant       {brier(comp_const, y_comp):.6f}")
    emit(f"    Brier, imported F11   {brier(p_comp, y_comp):.6f}")
    mean_f2, lo_f2, hi_f2 = paired_bootstrap(p_comp, comp_const, y_comp)
    emit(
        f"    F11 vs constant: dBrier={mean_f2:+.6f}  95% CI [{lo_f2:+.6f}, {hi_f2:+.6f}]  "
        f"{'F11 BETTER' if hi_f2 < 0 else 'inconclusive'}"
    )

    emit("")
    emit("  ## Level 3 — the product: P(comeback)  [Bar 1]")
    emit(f"    constant             Brier={brier(p_const, y_cb):.6f}")
    emit(f"    baseline_chain_odds  Brier={brier(p_base, y_cb):.6f}")
    emit(f"    candidate_chain      Brier={brier(p_cand, y_cb):.6f}")
    emit(
        f"    restricted variant   Brier={brier(p_restricted, y_cb):.6f}  "
        f"(families: {', '.join(survivors) if survivors else 'none survived'})"
    )

    m1, l1, h1 = paired_bootstrap(p_cand, p_const, y_cb)
    m2, l2, h2 = paired_bootstrap(p_cand, p_base, y_cb)
    emit(f"    candidate vs constant: dBrier={m1:+.6f} [{l1:+.6f}, {h1:+.6f}]")
    emit(f"    candidate vs baseline: dBrier={m2:+.6f} [{l2:+.6f}, {h2:+.6f}]")
    bar1 = h1 < 0 and h2 < 0
    emit(
        f"    **BAR 1: {'PASSED' if bar1 else 'NOT PASSED'}** (needs both CIs strictly below zero)"
    )

    emit("")
    emit("  ## Calibration (candidate, quintiles of predicted risk)")
    emit("     n     predicted   observed")
    for n, pred, obs in calibration_table(p_cand, y_cb):
        emit(f"     {n:4d}   {pred:8.2%}   {obs:8.2%}")

    emit("")
    emit("  ## Bar 2 — slate lift")
    bar2 = _slate_report(p_cand, y_cb, emit)

    emit("")
    emit("  ## Verdict")
    emit(f"    Bar 1 (scientific, Brier): {'PASSED' if bar1 else 'NOT PASSED'}")
    emit(f"    Bar 2 (practical, slate):  {'PASSED' if bar2 else 'NOT PASSED'}")
    return "\n".join(lines)


def _slate_report(p: np.ndarray, y: np.ndarray, emit: object) -> bool:
    assert callable(emit)
    order = np.argsort(-p)
    base = float(y.mean())
    passed = False
    emit(f"     base rate {base:.2%}; a slate passes when its Wilson lower bound exceeds it")
    slates = (
        (0.10, "top decile"),
        (0.20, "top quintile (primary)"),
        (0.33, "top third"),
    )
    for frac, label in slates:
        n = int(len(p) * frac)
        picked = y[order[:n]]
        k = int(picked.sum())
        lo, hi = wilson_ci(k, n)
        ok = lo > base
        if "primary" in label:
            passed = ok
        emit(
            f"     {label:24s} n={n:3d}  hits={k:2d}  rate={k / n:6.2%}  "
            f"lift={k / n / base:4.2f}x  CI[{lo:.2%}, {hi:.2%}]  {'PASS' if ok else 'fail'}"
        )
    return passed


# --- Entry point --------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dev", action="store_true", help="walk-forward screen on dev seasons")
    parser.add_argument("--holdout", action="store_true", help="open the holdout — run once")
    args = parser.parse_args()

    raw = engine.load_enriched()
    matrix = engine.build_features(raw)
    usable = matrix[~engine.in_burn_in(matrix)]
    dev = usable[usable["split"] == "dev"].copy()
    holdout = usable[usable["split"] == "holdout"].copy()

    if not chain.replicate_f11(usable):
        raise SystemExit("F11 import invalid — see notes/PREREGISTRATION.md A3")
    if not leakage_check(raw):
        raise SystemExit("leakage regression failed")

    if args.dev:
        dev_screen(dev)
        return
    if args.holdout:
        screen = dev_screen(dev)
        print()
        report = holdout_run(dev, holdout, screen)
        # Raw transcript only. The written-up verdict lives in notes/RESULTS.md and is
        # deliberately not machine-generated, so a rerun cannot silently overwrite it.
        with open(RAW_OUTPUT_PATH, "w", encoding="utf-8") as fh:
            fh.write(report)
            fh.write("\n")
        print(f"\nwrote {RAW_OUTPUT_PATH} (interpretation: {RESULTS_PATH})")
        return
    parser.print_help()


if __name__ == "__main__":
    main()
