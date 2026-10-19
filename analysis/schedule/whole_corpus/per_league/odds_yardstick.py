"""The odds yardstick per league: one heterogeneity test per quantity, and shrunk league values.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/ODDS_YARDSTICK.md`. With the yardstick of
`ALL/ODDS_YARDSTICK.md`, prints one test across the leagues for each quantity: the raw goal,
comeback and 7+ rates, the same observed against expected (O/E), the two links, and the
first-half share of the goals. Then the comeback O/E again, with each league's own share;
then the league tables, in the order of the league names. No league is tested on its own:
per-league testing is Dead in `notes/WORKING/STATE.md`.

Run: `uv run python -m analysis.schedule.whole_corpus.per_league.odds_yardstick`
"""

import numpy as np
import pandas as pd

from analysis import corpus, report, stats
from analysis.methods import yardstick

LEAGUE = "s1_league_id"
# (observed column, expected column, label, kind). A league's value is sum(observed) /
# sum(expected): against `one` a raw rate, against `goals` the first-half share, else an O/E.
# The kind gives one match's variance if every league had the pooled value (`match_variance`).
QUANTITIES = (
    ("goals", "one", "goals per match", "count"),
    ("goals", "m_goals", "goals O/E", "count"),
    ("is_comeback", "one", "comeback rate", "event"),
    ("is_comeback", "m_cb", "comeback O/E", "event"),
    ("ht_decisive", "m_ht_decisive", "link 1 O/E", "event"),
    ("is_comeback", "m_completion", "link 2 O/E", "event"),
    ("seven", "one", "7+ rate", "event"),
    ("seven", "m_seven", "7+ O/E", "event"),
    ("goals_1h", "goals", "first-half share", "share"),
)
LUCK = ("goals O/E", "comeback O/E", "7+ O/E")  # counts and rare events: Poisson draws fit them
LUCK_DRAWS = 2000
# (quantity, column of its league values, header) for the two league tables.
MAIN_COLUMNS = (
    ("goals O/E", "value", "goals O/E"),
    ("goals O/E", "shrunk", "goals shrunk"),
    ("comeback O/E", "observed", "cb obs"),
    ("comeback O/E", "expected", "cb exp"),
    ("comeback O/E", "value", "cb O/E"),
    ("comeback O/E", "shrunk", "cb shrunk"),
    ("7+ O/E", "observed", "7+ obs"),
    ("7+ O/E", "expected", "7+ exp"),
    ("7+ O/E", "value", "7+ O/E"),
    ("7+ O/E", "shrunk", "7+ shrunk"),
    ("first-half share", "value", "share"),
    ("first-half share", "shrunk", "share shrunk"),
)
LINK_COLUMNS = (
    ("link 1 O/E", "value", "link 1 O/E"),
    ("link 1 O/E", "shrunk", "link 1 shrunk"),
    ("link 2 O/E", "value", "link 2 O/E"),
    ("link 2 O/E", "shrunk", "link 2 shrunk"),
)


def match_variance(
    kind: str, value: "float | pd.Series[float]", expected: "pd.Series[float]"
) -> "pd.Series[float]":
    """One match's variance of its observed value if its league has the given value.

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


def dispersion(frame: pd.DataFrame, observed: str, expected: str, kind: str) -> float:
    """How far the matches spread around their league's value, against what the kind says.

    The squared residuals around each league's own value, summed, over the summed variance
    that the kind gives at that value. 1 means that the kind's variance fits the matches.
    """
    sums = frame.groupby(LEAGUE)[[observed, expected]].transform("sum")
    own = sums[observed] / sums[expected]
    residual = frame[observed] - own * frame[expected]
    return float((residual**2).sum() / match_variance(kind, own, frame[expected]).sum())


def league_values(
    frame: pd.DataFrame, observed: str, expected: str, kind: str, phi: float = 1.0
) -> pd.DataFrame:
    """Per league: the two sums, their ratio (`value`), and its variance if all were equal.

    The variance is that of the value under one pooled value for every league, sum(observed)
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
    values = parts.groupby(frame[LEAGUE]).sum()
    values["value"] = values["observed"] / values["expected"]
    values["variance"] = values["variance"] / values["expected"] ** 2
    return values


def tested(
    frame: pd.DataFrame, observed: str, expected: str, kind: str
) -> tuple[pd.DataFrame, stats.Heterogeneity, float]:
    """The league values with their shrunk values, the one test, and the dispersion used."""
    phi = dispersion(frame, observed, expected, kind)
    values = league_values(frame, observed, expected, kind, phi)
    het = stats.heterogeneity(values["value"], values["variance"])
    values["shrunk"] = stats.shrink(values["value"], values["variance"], het)
    return values, het, phi


def luck_line(
    expected: "pd.Series[float]", pooled: float, draws: int = LUCK_DRAWS, seed: int = 0
) -> tuple[float, float]:
    """The lowest and highest league O/E if every league had `pooled`: medians of Poisson draws."""
    means = pooled * expected.to_numpy(dtype=float)
    counts = np.random.default_rng(seed).poisson(means, size=(draws, len(means)))
    ratios = counts / expected.to_numpy(dtype=float)
    return float(np.median(ratios.min(axis=1))), float(np.median(ratios.max(axis=1)))


def cohort_agreement(frame: pd.DataFrame, observed: str, expected: str) -> tuple[float, int]:
    """Spearman correlation of the league values between the two season cohorts, and its n."""
    sums = frame.groupby([LEAGUE, "season_cohort"])[[observed, expected]].sum()
    values = (sums[observed] / sums[expected]).unstack().dropna()
    return float(values.iloc[:, 0].corr(values.iloc[:, 1], method="spearman")), len(values)


def summary_row(
    frame: pd.DataFrame, quantity: tuple[str, str, str, str]
) -> tuple[dict[str, float | str], pd.DataFrame]:
    """One quantity's test as a row of the summary, and its league values."""
    observed, expected, label, kind = quantity
    values, het, phi = tested(frame, observed, expected, kind)
    pooled = float(values["observed"].sum() / values["expected"].sum())
    low, high = luck_line(values["expected"], pooled) if label in LUCK else (np.nan, np.nan)
    r, n = cohort_agreement(frame, observed, expected)
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


def with_own_share(frame: pd.DataFrame) -> pd.DataFrame:
    """The frame with the chances that use the share made again from each league's own share."""
    sums = frame.groupby(LEAGUE)[["goals_1h", "goals"]].sum()
    share = frame[LEAGUE].map(sums["goals_1h"] / sums["goals"]).to_numpy(dtype=float)
    lam_home, lam_away = frame["lam_home"].to_numpy(), frame["lam_away"].to_numpy()
    out = frame.copy()
    model = yardstick.implied(lam_home, lam_away, share)
    out[model.columns] = model.to_numpy()
    out["m_completion"] = yardstick.completion_given_ht(
        lam_home, lam_away, share, frame["ht_margin"].to_numpy()
    )
    return out


def league_table(
    frame: pd.DataFrame,
    values: dict[str, pd.DataFrame],
    columns: tuple[tuple[str, str, str], ...],
) -> pd.DataFrame:
    """Per league, in the order of the names: its matches and each column asked for."""
    grouped = frame.groupby(LEAGUE)
    table = pd.DataFrame({"league": grouped["s1_league_name"].first(), "matches": grouped.size()})
    for label, column, header in columns:
        table[header] = values[label][column]
    return table.sort_values("league")


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    share = yardstick.first_half_share(yardstick.priced(matches))
    frame = yardstick.frame(matches, yardstick.build_grid(), share=share).assign(one=1.0)
    print(
        f"Priced: {len(frame):,} matches in {frame[LEAGUE].nunique()} leagues; "
        f"first-half share {share:.4f}"
    )
    rows, values = [], {}
    for quantity in QUANTITIES:
        row, values[quantity[2]] = summary_row(frame, quantity)
        rows.append(row)
    print(f"Each test: Cochran's Q on {len(values['goals O/E']) - 1} df")
    report.show("One test across the leagues for each quantity", pd.DataFrame(rows))
    comeback = next(q for q in QUANTITIES if q[2] == "comeback O/E")
    report.show(
        "Comeback O/E with each league's own first-half share",
        pd.DataFrame([summary_row(with_own_share(frame), comeback)[0]]),
    )
    report.show(
        "Leagues: goals, comebacks, 7+ goals and the share",
        league_table(frame, values, MAIN_COLUMNS),
    )
    report.show("Leagues: the two links", league_table(frame, values, LINK_COLUMNS))


if __name__ == "__main__":
    main()
