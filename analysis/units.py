"""One quantity per unit (a league, later a team), and one test across the units.

A unit's value is sum(numerator) / sum(denominator) over its matches: a rate, a mean per
match, an O/E or a share. Its variance is the one it would have if every unit had the pooled
value (`match_variance`), times the dispersion of the matches (`dispersion`). Then one
heterogeneity test across the units, shrunk unit values, the luck line and the agreement of
the two season cohorts, as `notes/ANALYSIS/CLAUDE.md` §5, rule 1 asks. `level_row` gives the
test of the parts of a unit (its seasons, its teams or its rounds) as one row, with its p
from shuffles of the parts inside their units and its spread as a share of a match's
variance.
"""

from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import chi2, spearmanr

from analysis import stats

LUCK_DRAWS = 2000
NULL_DRAWS = 200  # the shuffles of `level_row` (`permuted_qs`)


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
    frame: pd.DataFrame,
    unit: str,
    observed: str,
    expected: str,
    kind: str,
    phi: float = 1.0,
    within: str | None = None,
) -> pd.DataFrame:
    """Per unit: the two sums, their ratio (`value`), and its variance if all were equal.

    The variance is that of the value under one pooled value for every unit, sum(observed)
    / sum(expected) over all matches, times the dispersion `phi`. With `within` (such as the
    league of a team), each match takes the pooled value of its `within` group instead.
    """
    if within is None:
        null: float | pd.Series[float] = float(frame[observed].sum() / frame[expected].sum())
    else:
        sums = frame.groupby(within)[[observed, expected]].transform("sum")
        null = sums[observed] / sums[expected]

    parts = pd.DataFrame(
        {
            "observed": frame[observed],
            "expected": frame[expected],
            "variance": phi * match_variance(kind, null, frame[expected]),
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
    expected: "pd.Series[float]",
    pooled: "float | np.ndarray",
    draws: int = LUCK_DRAWS,
    seed: int = 0,
) -> tuple[float, float]:
    """The lowest and highest unit value if every unit had `pooled` (one value, or one per
    unit, such as the value of its league): medians of Poisson draws."""
    means = pooled * expected.to_numpy(dtype=float)
    counts = np.random.default_rng(seed).poisson(means, size=(draws, len(means)))
    ratios = counts / expected.to_numpy(dtype=float)
    return float(np.median(ratios.min(axis=1))), float(np.median(ratios.max(axis=1)))


def cohort_values(
    frame: pd.DataFrame, unit: str, observed: str, expected: str, against: str | None = None
) -> pd.DataFrame:
    """The unit values of each season cohort, one column per cohort, for the units in both.

    With `against` (such as the league of a team), each value is taken relative to the value
    of its `against` group in the same cohort.
    """
    sums = frame.groupby([unit, "season_cohort"])[[observed, expected]].sum()
    values = sums[observed] / sums[expected]

    if against is not None:
        group_sums = frame.groupby([against, "season_cohort"])[[observed, expected]].sum()
        group_values = group_sums[observed] / group_sums[expected]
        owner = frame.groupby(unit)[against].first()
        units, cohorts = values.index.get_level_values(0), values.index.get_level_values(1)
        keys = list(zip(owner.loc[units], cohorts, strict=True))
        values = values - group_values.loc[keys].to_numpy()

    return values.unstack().dropna()


def cohort_agreement(
    frame: pd.DataFrame, unit: str, observed: str, expected: str
) -> tuple[float, int]:
    """Spearman correlation of the unit values between the two season cohorts, and its n."""
    values = cohort_values(frame, unit, observed, expected)
    return float(values.iloc[:, 0].corr(values.iloc[:, 1], method="spearman")), len(values)


def repeat_test(
    frame: pd.DataFrame, unit: str, observed: str, expected: str, against: str
) -> tuple[float, int, float]:
    """The repeat test: does a unit's value in one season cohort predict its value in the
    other, both relative to its `against` group? Spearman's r, its n, and the p of r = 0."""
    values = cohort_values(frame, unit, observed, expected, against)
    result = spearmanr(values.iloc[:, 0], values.iloc[:, 1])
    return float(result.statistic), len(values), float(result.pvalue)


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


@dataclass(frozen=True)
class Within:
    """One test of the parts of each unit around the unit's own value, pooled over the units."""

    values: pd.DataFrame  # per part: the sums, value, variance, owner, owner_mean, shrunk
    q: float
    df: int
    p: float
    tau2: float  # the variance of the parts inside a unit, pooled over the units
    scale: float  # tau^2 = (Q - df) / scale, the method of moments (DerSimonian-Laird)


def within_tested(
    frame: pd.DataFrame, unit: str, part: str, observed: str, expected: str, kind: str
) -> Within:
    """Do the parts of a unit (its seasons, or its teams) differ by more than noise?

    Each unit's Cochran's Q of its parts around their precision-weighted mean, summed over
    the units, on the summed degrees of freedom. A part's variance uses the value of its own
    unit. tau^2 comes from the summed Q (DerSimonian-Laird), and each part is shrunk toward
    the mean of its unit.
    """
    phi = dispersion(frame, part, observed, expected, kind)
    values = unit_values(frame, part, observed, expected, kind, phi, within=unit)
    values["owner"] = frame.groupby(part)[unit].first()

    # A part that expects nothing, or of a unit with no events, tells nothing: it leaves the
    # test, with its degree of freedom.
    values = values[(values["expected"] > 0) & (values["variance"] > 0)].copy()

    weights = 1.0 / values["variance"]
    by_owner = values["owner"]
    weight_sums = weights.groupby(by_owner).transform("sum")
    values["owner_mean"] = (weights * values["value"]).groupby(by_owner).transform("sum") / (
        weight_sums
    )

    q = float((weights * (values["value"] - values["owner_mean"]) ** 2).sum())
    df = len(values) - by_owner.nunique()
    scale = float(weights.sum() - (weights**2 / weight_sums).sum())
    tau2 = max(0.0, (q - df) / scale) if scale > 0 else 0.0

    keep = tau2 / (tau2 + values["variance"])
    values["shrunk"] = values["owner_mean"] + keep * (values["value"] - values["owner_mean"])

    return Within(values=values, q=q, df=df, p=float(chi2.sf(q, df)), tau2=tau2, scale=scale)


def within_test(
    frame: pd.DataFrame, unit: str, part: str, observed: str, expected: str, kind: str
) -> tuple[float, int, float]:
    """`within_tested`, as Q, its df and p only."""
    result = within_tested(frame, unit, part, observed, expected, kind)
    return result.q, result.df, result.p


def within_row(
    frame: pd.DataFrame, unit: str, part: str, quantity: tuple[str, str, str, str]
) -> tuple[dict[str, float | str], Within]:
    """One quantity's test of the parts around their unit (`within_tested`) as a row of a
    summary, and its result: the spread that the test finds at 80%, the median share that a
    part keeps after shrinkage, and the repeat test of the parts against their unit.

    `quantity` is (observed column, expected column, label, kind).
    """
    observed, expected, label, kind = quantity
    result = within_tested(frame, unit, part, observed, expected, kind)
    r, n, p = repeat_test(frame, part, observed, expected, unit)

    values = result.values
    pooled = float(values["observed"].sum() / values["expected"].sum())
    against = values["shrunk"] - values["owner_mean"]
    keep = result.tau2 / (result.tau2 + values["variance"])
    found = stats.detectable_tau(values["variance"], groups=values["owner"])

    row: dict[str, float | str] = {
        "quantity": label,
        "pooled": pooled,
        "Q": result.q,
        "df": float(result.df),
        "p": f"{result.p:.3g}",
        "tau": result.tau2**0.5,
        "tau/pooled": result.tau2**0.5 / pooled,
        "found 80%": found,
        "found/pooled": found / pooled,
        "keep median": float(keep.median()),
        "shrunk - league min": float(against.min()),
        "shrunk - league max": float(against.max()),
        "repeat r": r,
        "repeat n": float(n),
        "repeat p": f"{p:.3g}",
    }

    return row, result


def within_luck_row(label: str, result: Within) -> dict[str, float | str]:
    """How far the raw part values reach, and how far they would reach by luck alone if every
    part had the value of its unit."""
    values = result.values
    low, high = luck_line(values["expected"], values["owner_mean"].to_numpy())

    return {
        "quantity": label,
        "events, median": float(values["observed"].median()),
        "raw min": float(values["value"].min()),
        "raw max": float(values["value"].max()),
        "luck min": low,
        "luck max": high,
    }


def null_q(
    frame: pd.DataFrame,
    unit: str,
    part: str,
    quantity: tuple[str, str, str, str],
    draws: int = 100,
    seed: int = 0,
) -> tuple[float, float]:
    """The mean and sd of Q of `within_tested` when the outcomes come from the test's own null.

    Each match gets the value of its unit: a 0/1 outcome with the chance unit value x
    expected, or a Poisson count with that mean. If the method is right, the mean is near
    the df. A real Q far from this mean is a property of the data, not of the method.
    """
    observed, expected, _, kind = quantity
    if kind not in ("event", "count"):
        raise ValueError(f"no null draws for kind {kind!r}")

    sums = frame.groupby(unit)[[observed, expected]].transform("sum")
    means = (sums[observed] / sums[expected] * frame[expected]).to_numpy(dtype=float)

    rng = np.random.default_rng(seed)
    qs = []
    for _ in range(draws):
        if kind == "event":
            drawn = (rng.random(len(means)) < np.clip(means, 0.0, 1.0)).astype(float)
        else:
            drawn = rng.poisson(means).astype(float)

        drawn_frame = frame.assign(drawn=drawn)
        qs.append(within_tested(drawn_frame, unit, part, "drawn", expected, kind).q)

    return float(np.mean(qs)), float(np.std(qs))


def permuted_qs(
    frame: pd.DataFrame,
    unit: str,
    part: str,
    quantity: tuple[str, str, str, str],
    draws: int = NULL_DRAWS,
    seed: int = 0,
) -> np.ndarray:
    """Q of `within_tested` in each draw with the parts shuffled inside their units.

    Each match takes the part of a random match of its own unit, so each part keeps its
    size and each unit its matches. The outcomes and the expected values stay together.
    This is the null "the part tells nothing beyond the unit", with no model of the
    outcomes. The real Q and the shuffled ones come from the same method, so a bias of
    the method (such as a dispersion measured around small parts) is in both.
    """
    observed, expected, _, kind = quantity

    rng = np.random.default_rng(seed)
    qs = []
    for _ in range(draws):
        moved = frame.assign(**{part: shuffled_parts(frame[unit], frame[part], rng)})
        qs.append(within_tested(moved, unit, part, observed, expected, kind).q)

    return np.asarray(qs)


def shuffled_parts(
    unit: "pd.Series[Any]", part: "pd.Series[Any]", rng: np.random.Generator
) -> np.ndarray:
    """The parts of the matches in a random order inside each unit: each match takes the
    part of a random match of its unit, and each part keeps its count of matches."""
    codes = pd.factorize(unit)[0]
    labels = part.to_numpy()

    by_unit = np.argsort(codes, kind="stable")
    shuffled = np.lexsort((rng.random(len(codes)), codes))

    moved = np.empty_like(labels)
    moved[by_unit] = labels[shuffled]

    return moved


def variance_share(frame: pd.DataFrame, observed: str, expected: str, tau2: float) -> float:
    """The share of a match's variance that a spread tau^2 of the unit values makes.

    A unit's value scales the expected value of each of its matches, so a spread tau^2 of
    the values spreads a match's chance (or mean) by tau^2 x expected^2. The mean of that
    over the matches that count (expected above 0), against the variance of their observed
    values.
    """
    counted = frame[frame[expected] > 0]
    spread = float(np.var(counted[observed].to_numpy(dtype=float), ddof=1))
    return float(tau2 * (counted[expected] ** 2).mean() / spread)


def level_row(
    frame: pd.DataFrame,
    unit: str,
    part: str,
    quantity: tuple[str, str, str, str],
    draws: int = NULL_DRAWS,
) -> dict[str, float | str]:
    """One test of the parts around their unit (`within_tested`) as a row of a summary.

    Q with its chi-square p, and Q in `draws` shuffles of the parts inside their units
    (`permuted_qs`): its mean, its sd and the p of the shuffles, the share of them with a Q
    at least the real one. The spread tau of the parts comes from the excess of Q over the
    mean of the shuffles, not over the df, so a bias of Q is out of it. tau and the spread
    that the test finds at 80% are given against the pooled value and as a share of a
    match's variance (`variance_share`).
    """
    observed, expected, label, kind = quantity
    result = within_tested(frame, unit, part, observed, expected, kind)
    values = result.values
    pooled = float(values["observed"].sum() / values["expected"].sum())

    qs = permuted_qs(frame, unit, part, quantity, draws)
    null_mean = float(qs.mean())
    tau2 = max(0.0, (result.q - null_mean) / result.scale) if result.scale > 0 else 0.0
    found = stats.detectable_tau(values["variance"], groups=values["owner"])

    return {
        "quantity": label,
        "parts": float(len(values)),
        "pooled": pooled,
        "Q": result.q,
        "df": float(result.df),
        "p chi2": f"{result.p:.3g}",
        "shuffled mean": null_mean,
        "shuffled sd": float(qs.std()),
        "p": f"{(1 + (qs >= result.q).sum()) / (1 + draws):.3g}",
        "tau/pooled": tau2**0.5 / pooled,
        "found/pooled": found / pooled,
        "share": variance_share(frame, observed, expected, tau2),
        "found share": variance_share(frame, observed, expected, found**2),
    }
