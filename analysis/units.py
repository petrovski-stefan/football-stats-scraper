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


def dispersion(df: pd.DataFrame, unit: str, observed: str, expected: str, kind: str) -> float:
    """How far the matches spread around their unit's value, against what the kind says.

    The squared residuals around each unit's own value, summed, over the summed variance
    that the kind gives at that value. 1 means that the kind's variance fits the matches.
    """
    sums_df = df.groupby(unit)[[observed, expected]].transform("sum")
    own = sums_df[observed] / sums_df[expected]
    residual = df[observed] - own * df[expected]
    return float((residual**2).sum() / match_variance(kind, own, df[expected]).sum())


def unit_values(
    df: pd.DataFrame,
    unit: str,
    observed: str,
    expected: str,
    kind: str,
    dispersion_factor: float = 1.0,
    within: str | None = None,
) -> pd.DataFrame:
    """Per unit: the two sums, their ratio (`value`), and its variance if all were equal.

    The variance is that of the value under one pooled value for every unit, sum(observed)
    / sum(expected) over all matches, times the `dispersion_factor`. With `within` (such as the
    league of a team), each match takes the pooled value of its `within` group instead.
    """
    if within is None:
        null: float | pd.Series[float] = float(df[observed].sum() / df[expected].sum())
    else:
        sums_df = df.groupby(within)[[observed, expected]].transform("sum")
        null = sums_df[observed] / sums_df[expected]

    parts_df = pd.DataFrame(
        {
            "observed": df[observed],
            "expected": df[expected],
            "variance": dispersion_factor * match_variance(kind, null, df[expected]),
        }
    )

    unit_values_df = parts_df.groupby(df[unit]).sum()
    unit_values_df["value"] = unit_values_df["observed"] / unit_values_df["expected"]
    unit_values_df["variance"] = unit_values_df["variance"] / unit_values_df["expected"] ** 2

    return unit_values_df


def tested(
    df: pd.DataFrame, unit: str, observed: str, expected: str, kind: str
) -> tuple[pd.DataFrame, stats.Heterogeneity, float]:
    """The unit values with their shrunk values, the one test, and the dispersion used."""
    dispersion_factor = dispersion(df, unit, observed, expected, kind)
    unit_values_df = unit_values(df, unit, observed, expected, kind, dispersion_factor)
    het = stats.heterogeneity(unit_values_df["value"], unit_values_df["variance"])
    unit_values_df["shrunk"] = stats.shrink(
        unit_values_df["value"], unit_values_df["variance"], het
    )
    return unit_values_df, het, dispersion_factor


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
    df: pd.DataFrame, unit: str, observed: str, expected: str, against: str | None = None
) -> pd.DataFrame:
    """The unit values of each season cohort, one column per cohort, for the units in both.

    With `against` (such as the league of a team), each value is taken relative to the value
    of its `against` group in the same cohort.
    """
    sums_df = df.groupby([unit, "season_cohort"])[[observed, expected]].sum()
    values = sums_df[observed] / sums_df[expected]

    if against is not None:
        group_sums_df = df.groupby([against, "season_cohort"])[[observed, expected]].sum()
        group_values = group_sums_df[observed] / group_sums_df[expected]
        owner = df.groupby(unit)[against].first()
        units, cohorts = values.index.get_level_values(0), values.index.get_level_values(1)
        keys = list(zip(owner.loc[units], cohorts, strict=True))
        values = values - group_values.loc[keys].to_numpy()

    return values.unstack().dropna()


def cohort_agreement(
    df: pd.DataFrame, unit: str, observed: str, expected: str
) -> tuple[float, int]:
    """Spearman correlation of the unit values between the two season cohorts, and its n."""
    cohort_values_df = cohort_values(df, unit, observed, expected)
    return float(
        cohort_values_df.iloc[:, 0].corr(cohort_values_df.iloc[:, 1], method="spearman")
    ), len(cohort_values_df)


def repeat_test(
    df: pd.DataFrame, unit: str, observed: str, expected: str, against: str
) -> tuple[float, int, float]:
    """The repeat test: does a unit's value in one season cohort predict its value in the
    other, both relative to its `against` group? Spearman's r, its n, and the p of r = 0."""
    cohort_values_df = cohort_values(df, unit, observed, expected, against)
    result = spearmanr(cohort_values_df.iloc[:, 0], cohort_values_df.iloc[:, 1])
    return float(result.statistic), len(cohort_values_df), float(result.pvalue)


def summary_row(
    df: pd.DataFrame, unit: str, quantity: tuple[str, str, str, str], luck: bool = False
) -> tuple[dict[str, float | str], pd.DataFrame]:
    """One quantity's test as a row of the summary, and its unit values.

    `quantity` is (observed column, expected column, label, kind). The luck line uses
    Poisson draws, so ask for it only for counts and rare events.
    """
    observed, expected, label, kind = quantity
    unit_values_df, het, dispersion_factor = tested(df, unit, observed, expected, kind)

    pooled = float(unit_values_df["observed"].sum() / unit_values_df["expected"].sum())
    low, high = luck_line(unit_values_df["expected"], pooled) if luck else (np.nan, np.nan)
    cohort_correlation, cohort_count = cohort_agreement(df, unit, observed, expected)
    between_unit_sd, found = het.tau_squared**0.5, stats.detectable_tau(unit_values_df["variance"])

    row: dict[str, float | str] = {
        "quantity": label,
        "pooled": pooled,
        "dispersion": dispersion_factor,
        "Q": het.cochran_q,
        "p": f"{het.p_value:.3g}",
        "tau": between_unit_sd,
        "tau/pooled": between_unit_sd / pooled,
        "found 80%": found,
        "found/pooled": found / pooled,
        "raw min": float(unit_values_df["value"].min()),
        "raw max": float(unit_values_df["value"].max()),
        "luck min": low,
        "luck max": high,
        "shrunk min": float(unit_values_df["shrunk"].min()),
        "shrunk median": float(unit_values_df["shrunk"].median()),
        "shrunk max": float(unit_values_df["shrunk"].max()),
        "cohorts r": cohort_correlation,
        "cohorts n": float(cohort_count),
    }

    return row, unit_values_df


@dataclass(frozen=True)
class Within:
    """One test of the parts of each unit around the unit's own value, pooled over the units."""

    part_values_df: pd.DataFrame  # per part: the sums, value, variance, owner, owner_mean, shrunk
    cochran_q: float
    degrees_of_freedom: int
    p_value: float
    tau_squared: float  # the variance of the parts inside a unit, pooled over the units
    scale: float  # tau^2 = (Q - df) / scale, the method of moments (DerSimonian-Laird)


def within_tested(
    df: pd.DataFrame, unit: str, part: str, observed: str, expected: str, kind: str
) -> Within:
    """Do the parts of a unit (its seasons, or its teams) differ by more than noise?

    Each unit's Cochran's Q of its parts around their precision-weighted mean, summed over
    the units, on the summed degrees of freedom. A part's variance uses the value of its own
    unit. tau^2 comes from the summed Q (DerSimonian-Laird), and each part is shrunk toward
    the mean of its unit.
    """
    dispersion_factor = dispersion(df, part, observed, expected, kind)
    part_values_df = unit_values(df, part, observed, expected, kind, dispersion_factor, within=unit)
    part_values_df["owner"] = df.groupby(part)[unit].first()

    # A part that expects nothing, or of a unit with no events, tells nothing: it leaves the
    # test, with its degree of freedom.
    part_values_df = part_values_df[
        (part_values_df["expected"] > 0) & (part_values_df["variance"] > 0)
    ].copy()

    weights = 1.0 / part_values_df["variance"]
    by_owner = part_values_df["owner"]
    weight_sums = weights.groupby(by_owner).transform("sum")
    part_values_df["owner_mean"] = (weights * part_values_df["value"]).groupby(by_owner).transform(
        "sum"
    ) / (weight_sums)

    cochran_q = float(
        (weights * (part_values_df["value"] - part_values_df["owner_mean"]) ** 2).sum()
    )
    degrees_of_freedom = len(part_values_df) - by_owner.nunique()
    scale = float(weights.sum() - (weights**2 / weight_sums).sum())
    tau_squared = max(0.0, (cochran_q - degrees_of_freedom) / scale) if scale > 0 else 0.0

    keep = tau_squared / (tau_squared + part_values_df["variance"])
    part_values_df["shrunk"] = part_values_df["owner_mean"] + keep * (
        part_values_df["value"] - part_values_df["owner_mean"]
    )

    return Within(
        part_values_df=part_values_df,
        cochran_q=cochran_q,
        degrees_of_freedom=degrees_of_freedom,
        p_value=float(chi2.sf(cochran_q, degrees_of_freedom)),
        tau_squared=tau_squared,
        scale=scale,
    )


def within_test(
    df: pd.DataFrame, unit: str, part: str, observed: str, expected: str, kind: str
) -> tuple[float, int, float]:
    """`within_tested`, as Q, its df and p only."""
    result = within_tested(df, unit, part, observed, expected, kind)
    return result.cochran_q, result.degrees_of_freedom, result.p_value


def within_row(
    df: pd.DataFrame, unit: str, part: str, quantity: tuple[str, str, str, str]
) -> tuple[dict[str, float | str], Within]:
    """One quantity's test of the parts around their unit (`within_tested`) as a row of a
    summary, and its result: the spread that the test finds at 80%, the median share that a
    part keeps after shrinkage, and the repeat test of the parts against their unit.

    `quantity` is (observed column, expected column, label, kind).
    """
    observed, expected, label, kind = quantity
    result = within_tested(df, unit, part, observed, expected, kind)
    repeat_correlation, repeat_count, repeat_p_value = repeat_test(
        df, part, observed, expected, unit
    )

    part_values_df = result.part_values_df
    pooled = float(part_values_df["observed"].sum() / part_values_df["expected"].sum())
    against = part_values_df["shrunk"] - part_values_df["owner_mean"]
    keep = result.tau_squared / (result.tau_squared + part_values_df["variance"])
    found = stats.detectable_tau(part_values_df["variance"], groups=part_values_df["owner"])

    row: dict[str, float | str] = {
        "quantity": label,
        "pooled": pooled,
        "Q": result.cochran_q,
        "df": float(result.degrees_of_freedom),
        "p": f"{result.p_value:.3g}",
        "tau": result.tau_squared**0.5,
        "tau/pooled": result.tau_squared**0.5 / pooled,
        "found 80%": found,
        "found/pooled": found / pooled,
        "keep median": float(keep.median()),
        "shrunk - league min": float(against.min()),
        "shrunk - league max": float(against.max()),
        "repeat r": repeat_correlation,
        "repeat n": float(repeat_count),
        "repeat p": f"{repeat_p_value:.3g}",
    }

    return row, result


def within_luck_row(label: str, result: Within) -> dict[str, float | str]:
    """How far the raw part values reach, and how far they would reach by luck alone if every
    part had the value of its unit."""
    part_values_df = result.part_values_df
    low, high = luck_line(part_values_df["expected"], part_values_df["owner_mean"].to_numpy())

    return {
        "quantity": label,
        "events, median": float(part_values_df["observed"].median()),
        "raw min": float(part_values_df["value"].min()),
        "raw max": float(part_values_df["value"].max()),
        "luck min": low,
        "luck max": high,
    }


def null_q(
    df: pd.DataFrame,
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

    sums_df = df.groupby(unit)[[observed, expected]].transform("sum")
    means = (sums_df[observed] / sums_df[expected] * df[expected]).to_numpy(dtype=float)

    rng = np.random.default_rng(seed)
    cochran_qs = []
    for _ in range(draws):
        if kind == "event":
            drawn = (rng.random(len(means)) < np.clip(means, 0.0, 1.0)).astype(float)
        else:
            drawn = rng.poisson(means).astype(float)

        drawn_df = df.assign(drawn=drawn)
        cochran_qs.append(within_tested(drawn_df, unit, part, "drawn", expected, kind).cochran_q)

    return float(np.mean(cochran_qs)), float(np.std(cochran_qs))


def permuted_qs(
    df: pd.DataFrame,
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
    cochran_qs = []
    for _ in range(draws):
        shuffled_df = df.assign(**{part: shuffled_parts(df[unit], df[part], rng)})
        cochran_qs.append(
            within_tested(shuffled_df, unit, part, observed, expected, kind).cochran_q
        )

    return np.asarray(cochran_qs)


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


def variance_share(df: pd.DataFrame, observed: str, expected: str, tau_squared: float) -> float:
    """The share of a match's variance that a spread tau^2 of the unit values makes.

    A unit's value scales the expected value of each of its matches, so a spread tau^2 of
    the values spreads a match's chance (or mean) by tau^2 x expected^2. The mean of that
    over the matches that count (expected above 0), against the variance of their observed
    values.
    """
    counted_df = df[df[expected] > 0]
    spread = float(np.var(counted_df[observed].to_numpy(dtype=float), ddof=1))
    return float(tau_squared * (counted_df[expected] ** 2).mean() / spread)


def level_row(
    df: pd.DataFrame,
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
    result = within_tested(df, unit, part, observed, expected, kind)
    part_values_df = result.part_values_df
    pooled = float(part_values_df["observed"].sum() / part_values_df["expected"].sum())

    cochran_qs = permuted_qs(df, unit, part, quantity, draws)
    null_mean = float(cochran_qs.mean())
    tau_squared = (
        max(0.0, (result.cochran_q - null_mean) / result.scale) if result.scale > 0 else 0.0
    )
    found = stats.detectable_tau(part_values_df["variance"], groups=part_values_df["owner"])

    return {
        "quantity": label,
        "parts": float(len(part_values_df)),
        "pooled": pooled,
        "Q": result.cochran_q,
        "df": float(result.degrees_of_freedom),
        "p chi2": f"{result.p_value:.3g}",
        "shuffled mean": null_mean,
        "shuffled sd": float(cochran_qs.std()),
        "p": f"{(1 + (cochran_qs >= result.cochran_q).sum()) / (1 + draws):.3g}",
        "tau/pooled": tau_squared**0.5 / pooled,
        "found/pooled": found / pooled,
        "share": variance_share(df, observed, expected, tau_squared),
        "found share": variance_share(df, observed, expected, found**2),
    }
