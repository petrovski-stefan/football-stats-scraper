"""One quantity per unit (a league, later a team), and one test across the units.

A unit's value is sum(numerator) / sum(denominator) over its matches: a rate, a mean per
match, an O/E or a share. Its variance is the one it would have if every unit had the pooled
value (`match_variance`), times the dispersion of the matches (`dispersion`). Then one
heterogeneity test across the units, shrunk unit values, the luck line and the agreement of
the two season cohorts, as `notes/ANALYSIS/CLAUDE.md` §5, rule 1 asks.
"""

import numpy as np
import pandas as pd
from scipy.stats import chi2

from analysis import stats

LUCK_DRAWS = 2000


def match_variance(
    kind: str, value: "float | pd.Series[float]", expected: "pd.Series[float]"
) -> "pd.Series[float]":
    """One match's variance of its observed value if its unit has the given value.

    "count" is a Poisson count (goals); "event" is 0/1 with the chance value x expected;
    "share" is binomial over the match's goals (`expected` holds them), each goal in the
    first half with the chance `value`.
    """
    if kind == "count":
        return value * expected
    if kind == "event":
        return value * expected * (1 - value * expected)
    if kind == "share":
        return value * (1 - value) * expected
    raise ValueError(f"unknown kind {kind!r}")


def dispersion(frame: pd.DataFrame, unit: str, observed: str, expected: str, kind: str) -> float:
    """How far the matches spread around their unit's value, against what the kind says.

    The squared residuals around each unit's own value, summed, over the summed variance
    that the kind gives at that value. 1 means that the kind's variance fits the matches.
    """
    sums = frame.groupby(unit)[[observed, expected]].transform("sum")
    own = sums[observed] / sums[expected]
    residual = frame[observed] - own * frame[expected]
    return float((residual**2).sum() / match_variance(kind, own, frame[expected]).sum())


def unit_values(
    frame: pd.DataFrame, unit: str, observed: str, expected: str, kind: str, phi: float = 1.0
) -> pd.DataFrame:
    """Per unit: the two sums, their ratio (`value`), and its variance if all were equal.

    The variance is that of the value under one pooled value for every unit, sum(observed)
    / sum(expected) over all matches, times the dispersion `phi`.
    """
    pooled = float(frame[observed].sum() / frame[expected].sum())
    parts = pd.DataFrame(
        {
            "observed": frame[observed],
            "expected": frame[expected],
            "variance": phi * match_variance(kind, pooled, frame[expected]),
        }
    )
    values = parts.groupby(frame[unit]).sum()
    values["value"] = values["observed"] / values["expected"]
    values["variance"] = values["variance"] / values["expected"] ** 2
    return values


def tested(
    frame: pd.DataFrame, unit: str, observed: str, expected: str, kind: str
) -> tuple[pd.DataFrame, stats.Heterogeneity, float]:
    """The unit values with their shrunk values, the one test, and the dispersion used."""
    phi = dispersion(frame, unit, observed, expected, kind)
    values = unit_values(frame, unit, observed, expected, kind, phi)
    het = stats.heterogeneity(values["value"], values["variance"])
    values["shrunk"] = stats.shrink(values["value"], values["variance"], het)
    return values, het, phi


def luck_line(
    expected: "pd.Series[float]", pooled: float, draws: int = LUCK_DRAWS, seed: int = 0
) -> tuple[float, float]:
    """The lowest and highest unit value if every unit had `pooled`: medians of Poisson draws."""
    means = pooled * expected.to_numpy(dtype=float)
    counts = np.random.default_rng(seed).poisson(means, size=(draws, len(means)))
    ratios = counts / expected.to_numpy(dtype=float)
    return float(np.median(ratios.min(axis=1))), float(np.median(ratios.max(axis=1)))


def cohort_agreement(
    frame: pd.DataFrame, unit: str, observed: str, expected: str
) -> tuple[float, int]:
    """Spearman correlation of the unit values between the two season cohorts, and its n."""
    sums = frame.groupby([unit, "season_cohort"])[[observed, expected]].sum()
    values = (sums[observed] / sums[expected]).unstack().dropna()
    return float(values.iloc[:, 0].corr(values.iloc[:, 1], method="spearman")), len(values)


def summary_row(
    frame: pd.DataFrame, unit: str, quantity: tuple[str, str, str, str], luck: bool = False
) -> tuple[dict[str, float | str], pd.DataFrame]:
    """One quantity's test as a row of the summary, and its unit values.

    `quantity` is (observed column, expected column, label, kind). The luck line uses
    Poisson draws, so ask for it only for counts and rare events.
    """
    observed, expected, label, kind = quantity
    values, het, phi = tested(frame, unit, observed, expected, kind)
    pooled = float(values["observed"].sum() / values["expected"].sum())
    low, high = luck_line(values["expected"], pooled) if luck else (np.nan, np.nan)
    r, n = cohort_agreement(frame, unit, observed, expected)
    tau, found = het.tau2**0.5, stats.detectable_tau(values["variance"])
    row: dict[str, float | str] = {
        "quantity": label,
        "pooled": pooled,
        "dispersion": phi,
        "Q": het.q,
        "p": f"{het.p:.3g}",
        "tau": tau,
        "tau/pooled": tau / pooled,
        "found 80%": found,
        "found/pooled": found / pooled,
        "raw min": float(values["value"].min()),
        "raw max": float(values["value"].max()),
        "luck min": low,
        "luck max": high,
        "shrunk min": float(values["shrunk"].min()),
        "shrunk median": float(values["shrunk"].median()),
        "shrunk max": float(values["shrunk"].max()),
        "cohorts r": r,
        "cohorts n": float(n),
    }
    return row, values


def within_test(
    frame: pd.DataFrame, unit: str, part: str, observed: str, expected: str, kind: str
) -> tuple[float, int, float]:
    """Do the parts of a unit (its seasons) differ by more than noise? One test for all units.

    Each unit's Cochran's Q of its parts around their own mean, summed over the units with
    two parts or more, on the summed degrees of freedom. Returns Q, its df and p.
    """
    phi = dispersion(frame, part, observed, expected, kind)
    values = unit_values(frame, part, observed, expected, kind, phi)
    owner = frame.groupby(part)[unit].first()
    q, df = 0.0, 0
    for _, group in values.groupby(owner):
        if len(group) > 1:
            het = stats.heterogeneity(group["value"], group["variance"])
            q, df = q + het.q, df + het.df
    return q, df, float(chi2.sf(q, df))
