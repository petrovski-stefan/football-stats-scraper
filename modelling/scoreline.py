"""Generative scoreline model for the exclusion filter (notes/PREREGISTRATION_FILTER.md).

Comeback rate is non-monotone in total goals — zero below 3, peaking at exactly 3
(14.6%), collapsing on even totals because a comeback needs a *decisive* result. A
discriminative model on a goal-richness proxy cannot express that shape; a pilot
that tried it pointed the wrong way. So the filter forecasts the scoreline
distribution instead and reads P(comeback) off it by summation, which makes the
mechanics structural rather than learned.

    P(comeback) = SUM over (HT scoreline, 2H scoreline) of
                  P(HT) x P(2H | HT)  where the half-time leader loses at full time

Four parts: Poisson rates for each half, second-half rates conditioned on the
half-time state, a Dixon-Coles low-score correction (load-bearing here — the
even-goal collapse *is* the draw effect), and explicit enumeration.

The half-time state is an observed feature at FIT time only. At predict time it is
never read: the model sums over every half-time scoreline weighted by the
first-half model. `--leak-check` enforces this.

Run: `uv run python -m modelling.scoreline --self-check` / `--leak-check`.
"""

import argparse
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.stats import poisson

from features import engine
from features.ratepair import RatePair

# Goals per team per half considered in the enumeration. Fitted second-half rates
# reach ~2.0 on the highest-scoring fixtures, where Poisson mass above 5 is ~1.7% —
# too much to renormalise away honestly, so the grid runs to 8 (residual < 1e-4).
MAX_GOALS = 8
# Dixon-Coles dependence parameter, fitted by grid-search MLE per half.
RHO_GRID = np.linspace(-0.25, 0.25, 101)


def _pmf_matrix(mu: np.ndarray) -> np.ndarray:
    """(MAX_GOALS+1, n) Poisson pmf table."""
    return np.vstack([poisson.pmf(k, mu) for k in range(MAX_GOALS + 1)])


def dixon_coles_tau(
    home_goals: int, away_goals: int, mu_home: np.ndarray, mu_away: np.ndarray, rho: float
) -> np.ndarray:
    """Dixon-Coles low-score correction; 1 everywhere outside the four 0/1 cells."""
    if home_goals == 0 and away_goals == 0:
        return np.asarray(1.0 - mu_home * mu_away * rho, dtype=float)
    if home_goals == 0 and away_goals == 1:
        return np.asarray(1.0 + mu_home * rho, dtype=float)
    if home_goals == 1 and away_goals == 0:
        return np.asarray(1.0 + mu_away * rho, dtype=float)
    if home_goals == 1 and away_goals == 1:
        return np.full_like(mu_home, 1.0 - rho)
    return np.ones_like(mu_home)


def _fit_rho(
    goals_home: np.ndarray, goals_away: np.ndarray, mu_home: np.ndarray, mu_away: np.ndarray
) -> float:
    """Grid-search MLE for the dependence parameter on observed scorelines."""
    base = poisson.pmf(goals_home, mu_home) * poisson.pmf(goals_away, mu_away)
    low = (goals_home <= 1) & (goals_away <= 1)
    best_rho, best_ll = 0.0, -np.inf
    for rho in RHO_GRID:
        tau = np.ones_like(base)
        for h in (0, 1):
            for a in (0, 1):
                mask = low & (goals_home == h) & (goals_away == a)
                if mask.any():
                    tau[mask] = dixon_coles_tau(h, a, mu_home[mask], mu_away[mask], float(rho))
        if np.any(tau <= 0):
            continue
        ll = float(np.sum(np.log(np.clip(base * tau, 1e-300, None))))
        if ll > best_ll:
            best_rho, best_ll = float(rho), ll
    return best_rho


# Half-time state, as the second-half model sees it. Two columns carry both
# direction and magnitude; at predict time they are set to a hypothetical scoreline.
HT_STATE_COLUMNS = ["ht_lead_home", "ht_lead_away"]
# Half-time leads bigger than this are vanishingly rare, so the game-state effect is
# not estimated there. Enumeration still visits those scorelines — only the state fed
# to the second-half model is clipped, which stops it extrapolating a 5-0 half-time
# into an absurd second-half rate (and blowing up the truncated mass).
MAX_HT_LEAD = 3.0


def _ht_state_frame(x: pd.DataFrame, lead_home: np.ndarray, lead_away: np.ndarray) -> pd.DataFrame:
    return x.assign(
        ht_lead_home=np.clip(lead_home, 0.0, MAX_HT_LEAD),
        ht_lead_away=np.clip(lead_away, 0.0, MAX_HT_LEAD),
    )


@dataclass(frozen=True)
class _Grid:
    """Second-half grid geometry: each cell's goal difference and total goals.

    Fixed by MAX_GOALS, so it is built once rather than per prediction. Grouped into
    one object because the two arrays are only ever used together, to index the same
    (home goals, away goals) grid.
    """

    diff: np.ndarray
    total: np.ndarray


def _build_grid() -> _Grid:
    axis = np.arange(MAX_GOALS + 1)
    return _Grid(diff=axis[:, None] - axis[None, :], total=axis[:, None] + axis[None, :])


_SECOND_HALF_GRID = _build_grid()


def _comeback_mask(margin: int) -> np.ndarray:
    """Second-half grid cells in which the half-time leader ends up losing.

    With the half-time margin fixed, "the leader finishes behind" is a fixed region of
    the second-half grid. A level half-time can produce no comeback by definition.
    """
    if margin > 0:
        return _SECOND_HALF_GRID.diff < -margin
    if margin < 0:
        return _SECOND_HALF_GRID.diff > -margin
    return np.zeros_like(_SECOND_HALF_GRID.diff, dtype=bool)


@dataclass
class _Totals:
    """Running totals as the enumeration walks every half-time scoreline.

    One object rather than seven loose arrays, so a half-time scoreline's contribution
    can be folded in by a single call instead of unpacking a seven-tuple per cell.
    """

    mass: np.ndarray
    p_comeback: np.ndarray
    p_total_le2: np.ndarray
    p_ft_draw: np.ndarray
    # Structural audit: comeback mass arriving from scorelines under 3 goals. Must stay
    # exactly zero — that is the mechanical floor being respected.
    p_comeback_impossible: np.ndarray
    p_by_total: np.ndarray
    cb_by_total: np.ndarray

    @classmethod
    def zeros(cls, n: int) -> "_Totals":
        bands = 4 * MAX_GOALS + 2
        return cls(
            mass=np.zeros(n),
            p_comeback=np.zeros(n),
            p_total_le2=np.zeros(n),
            p_ft_draw=np.zeros(n),
            p_comeback_impossible=np.zeros(n),
            p_by_total=np.zeros((bands, n)),
            cb_by_total=np.zeros((bands, n)),
        )

    def add(self, p_ht: np.ndarray, joint: np.ndarray, h1: int, a1: int) -> None:
        """Fold one half-time scoreline's contribution into the totals.

        `p_ht` is that scoreline's probability per match; `joint` is the second-half
        distribution conditioned on it, indexed (home goals, away goals, match).
        """
        margin, ht_total = h1 - a1, h1 + a1
        cb_mask = _comeback_mask(margin)

        self.mass += p_ht * joint.sum(axis=(0, 1))
        if cb_mask.any():
            self.p_comeback += p_ht * joint[cb_mask].sum(axis=0)
        self.p_ft_draw += p_ht * joint[_SECOND_HALF_GRID.diff == -margin].sum(axis=0)

        le2_mask = (_SECOND_HALF_GRID.total + ht_total) <= 2
        if le2_mask.any():
            self.p_total_le2 += p_ht * joint[le2_mask].sum(axis=0)
            overlap = le2_mask & cb_mask
            if overlap.any():
                self.p_comeback_impossible += p_ht * joint[overlap].sum(axis=0)

        for k in range(2 * MAX_GOALS + 1):
            band = _SECOND_HALF_GRID.total == k
            self.p_by_total[ht_total + k] += p_ht * joint[band].sum(axis=0)
            both = band & cb_mask
            if both.any():
                self.cb_by_total[ht_total + k] += p_ht * joint[both].sum(axis=0)


class ScorelineModel:
    """Fit goal rates per half; predict a full joint distribution over scorelines."""

    def __init__(self, feature_names: list[str] | None = None, alpha: float = 1.0):
        self.feature_names = list(feature_names or engine.filter_feature_names())
        self.first_half = RatePair(self.feature_names, alpha=alpha)
        self.second_half = RatePair(self.feature_names + HT_STATE_COLUMNS, alpha=alpha)
        self.rho_first = 0.0
        self.rho_second = 0.0

    def fit(self, train: pd.DataFrame) -> "ScorelineModel":
        h1_home = train["ht_home_goals"].to_numpy(dtype=float)
        h1_away = train["ht_away_goals"].to_numpy(dtype=float)
        self.first_half.fit(train, h1_home, h1_away)
        mu1_home, mu1_away = self.first_half.rates(train)
        self.rho_first = _fit_rho(h1_home, h1_away, mu1_home, mu1_away)

        # Second half sees the half-time state that actually occurred — training only.
        margin = h1_home - h1_away
        with_state = _ht_state_frame(train, np.clip(margin, 0, None), np.clip(-margin, 0, None))
        h2_home = train["home_2h_goals"].to_numpy(dtype=float)
        h2_away = train["away_2h_goals"].to_numpy(dtype=float)
        self.second_half.fit(with_state, h2_home, h2_away)
        mu2_home, mu2_away = self.second_half.rates(with_state)
        self.rho_second = _fit_rho(h2_home, h2_away, mu2_home, mu2_away)
        return self

    def _second_half_joint(self, x: pd.DataFrame, margin: int) -> np.ndarray:
        """Second-half distribution given a hypothetical half-time margin.

        Indexed (home goals, away goals, match). The half-time state fed to the model is
        the enumerated one, never the match's own — that is what `--leak-check` proves.
        """
        n = len(x)
        state = _ht_state_frame(x, np.full(n, float(margin)), np.full(n, float(-margin)))
        mu2_home, mu2_away = self.second_half.rates(state)
        pmf2_home, pmf2_away = _pmf_matrix(mu2_home), _pmf_matrix(mu2_away)

        joint: np.ndarray = pmf2_home[:, None, :] * pmf2_away[None, :, :]
        for gh in (0, 1):
            for ga in (0, 1):
                joint[gh, ga] *= dixon_coles_tau(gh, ga, mu2_home, mu2_away, self.rho_second)
        return joint

    def predict(self, x: pd.DataFrame) -> pd.DataFrame:
        """Enumerate the joint scoreline distribution; return the derived quantities.

        Never reads the target match's own goals: the half-time state is enumerated,
        not observed.
        """
        mu1_home, mu1_away = self.first_half.rates(x)
        pmf1_home, pmf1_away = _pmf_matrix(mu1_home), _pmf_matrix(mu1_away)
        totals = _Totals.zeros(len(x))

        for h1 in range(MAX_GOALS + 1):
            for a1 in range(MAX_GOALS + 1):
                p_ht = (
                    pmf1_home[h1]
                    * pmf1_away[a1]
                    * dixon_coles_tau(h1, a1, mu1_home, mu1_away, self.rho_first)
                )
                if not np.any(p_ht > 0):
                    continue
                totals.add(p_ht, self._second_half_joint(x, h1 - a1), h1, a1)

        out = pd.DataFrame(
            {
                "match_id": x["match_id"].to_numpy(),
                "p_comeback": totals.p_comeback / totals.mass,
                "p_total_le2": totals.p_total_le2 / totals.mass,
                "p_ft_draw": totals.p_ft_draw / totals.mass,
                "mass": totals.mass,
                "p_comeback_impossible": totals.p_comeback_impossible,
                "mu1_home": mu1_home,
                "mu1_away": mu1_away,
            },
            index=x.index,
        )
        # Diagnostics for the self-check's shape test, kept out of the columns.
        out.attrs["p_by_total"] = totals.p_by_total
        out.attrs["cb_by_total"] = totals.cb_by_total
        return out


# --- Gates --------------------------------------------------------------------


def self_check(matrix: pd.DataFrame) -> bool:
    """Calibration and structural gate. The study stops if this fails."""
    print("=" * 78)
    print("SCORELINE MODEL SELF-CHECK")
    print("=" * 78)
    model = ScorelineModel().fit(matrix)
    out = model.predict(matrix)
    ok = True

    worst_mass = float(np.max(np.abs(out["mass"].to_numpy() - 1.0)))
    mass_ok = worst_mass < 1e-3
    ok &= mass_ok
    print(
        f"\n  enumerated mass: max |sum-1| = {worst_mass:.2e}  "
        f"{'PASS' if mass_ok else 'FAIL'} (truncation at {MAX_GOALS} goals/half/team)"
    )

    leak = float(np.max(out["p_comeback_impossible"].to_numpy()))
    structural_ok = leak == 0.0
    ok &= structural_ok
    print(
        f"  comeback mass from scorelines under 3 goals: {leak:.3e}  "
        f"{'PASS' if structural_ok else 'FAIL'} (must be exactly 0)"
    )

    print(
        f"\n  Dixon-Coles rho: first half {model.rho_first:+.4f}, "
        f"second half {model.rho_second:+.4f}"
    )

    print("\n  implied vs observed base rates:")
    checks = [
        ("P(comeback)", out["p_comeback"].mean(), matrix["is_comeback"].mean(), 0.010),
        ("P(total <= 2)", out["p_total_le2"].mean(), (matrix["total_goals"] <= 2).mean(), 0.030),
        (
            "P(FT draw)",
            out["p_ft_draw"].mean(),
            (matrix["ft_home_goals"] == matrix["ft_away_goals"]).mean(),
            0.030,
        ),
        ("mean 1H home goals", out["mu1_home"].mean(), matrix["ht_home_goals"].mean(), 0.030),
        ("mean 1H away goals", out["mu1_away"].mean(), matrix["ht_away_goals"].mean(), 0.030),
    ]
    for label, implied, observed, tol in checks:
        good = abs(float(implied) - float(observed)) < tol
        ok &= good
        print(
            f"    {label:22s} implied={float(implied):7.2%}  observed={float(observed):7.2%}  "
            f"{'PASS' if good else 'FAIL'} (tol {tol:.1%})"
        )

    # The mechanics to reproduce are the zero floor and odd/even parity — a comeback
    # needs a decisive result, so even totals (full of draws) collapse. See
    # PREREGISTRATION_FILTER.md A1: the original "peak at 3 goals" gate was a
    # misreading; 7-goal games run hotter than 3-goal games in the raw data. What is
    # true of 3 goals is that it carries most comeback *mass*, not the highest rate.
    print("\n  comeback rate by total goals — zero floor and odd/even parity")
    p_by_total = out.attrs["p_by_total"]
    cb_by_total = out.attrs["cb_by_total"]
    print("     goals   model   observed")
    model_rates = []
    for g in range(8):
        weight = float(p_by_total[g].sum())
        rate = float(cb_by_total[g].sum()) / weight if weight > 0 else 0.0
        model_rates.append(rate)
        actual = matrix[matrix["total_goals"] == g]
        obs = actual["is_comeback"].mean() if len(actual) else float("nan")
        print(f"     {g:5d}   {rate:6.2%}   {obs:7.2%}")

    floor_ok = all(rate == 0.0 for rate in model_rates[:3])
    parity_ok = model_rates[3] > model_rates[4] and model_rates[5] > model_rates[6]
    ok &= floor_ok and parity_ok
    print(f"    zero below 3 goals: {'PASS' if floor_ok else 'FAIL'}")
    print(f"    odd totals above adjacent even: {'PASS' if parity_ok else 'FAIL'}")

    mass_3 = float(cb_by_total[3].sum()) / float(cb_by_total.sum())
    observed_3 = float(
        (matrix["is_comeback"] & (matrix["total_goals"] == 3)).sum() / matrix["is_comeback"].sum()
    )
    print(
        f"    share of comeback mass at exactly 3 goals: model {mass_3:.1%}, "
        f"observed {observed_3:.1%}"
    )

    print(f"\n  SELF-CHECK {'PASSED' if ok else 'FAILED — the study stops here'}")
    return bool(ok)


def leak_check(matrix: pd.DataFrame) -> bool:
    """Predictions must not change when every post-match column is destroyed."""
    print("\n" + "=" * 78)
    print("LEAK CHECK — post-match columns must not reach the prediction path")
    print("=" * 78)
    model = ScorelineModel().fit(matrix)
    clean = model.predict(matrix)

    blinded = matrix.copy()
    for column in engine.POST_MATCH_COLUMNS:
        if column in blinded.columns:
            blinded[column] = np.nan
    blinded_out = model.predict(blinded)

    identical = np.array_equal(clean["p_comeback"].to_numpy(), blinded_out["p_comeback"].to_numpy())
    print(f"  blinded columns: {', '.join(engine.POST_MATCH_COLUMNS)}")
    print(f"  predictions bit-identical: {'PASS' if identical else 'FAIL'}")
    if not identical:
        diff = np.abs(clean["p_comeback"].to_numpy() - blinded_out["p_comeback"].to_numpy())
        print(f"    max deviation {diff.max():.3e} on {(diff > 0).sum()} rows")
    return bool(identical)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true", help="calibration + structure gate")
    parser.add_argument("--leak-check", action="store_true", help="no post-match column is read")
    args = parser.parse_args()

    matrix = engine.build_features()
    usable = matrix[~engine.in_burn_in(matrix)].copy()

    ok = True
    if args.self_check:
        ok &= self_check(usable)
    if args.leak_check:
        ok &= leak_check(usable)
    if not (args.self_check or args.leak_check):
        parser.print_help()
        return
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
