"""Do comebacks and 7+ matches collect on the same opening prices, beyond chance?

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ODDS_GROUPS.md`. The matches with the same
opening prices form a group, in four ways to say "the same". Under the null, each match keeps
the chance that the odds yardstick gives it (`analysis/methods/yardstick.py`), scaled so that
the chances add up to the observed count: the prices then tell all that they can. Against
draws from that null: how many groups hold 2 or 3 events, and the most surprising group. Then
one test across the groups with enough expected events (`units.summary_row`), and whether the
groups at the top in one season cohort stay above the others in the other cohort.

Run: `uv run python -m analysis.schedule.whole_corpus.all.odds_groups`
"""

import numpy as np
import pandas as pd
from scipy.stats import poisson

from analysis import corpus, report, units
from analysis.methods import shin, yardstick

BAND = 0.05  # the width of a chance band in the near grouping
# (name, the columns whose values must all be equal inside a group)
GROUPINGS = (
    ("exact 1X2 prices", shin.ODDS),
    ("exact 9 prices", [*shin.ODDS, *yardstick.OU, *corpus.AH]),
    ("AH line and O/U line", [corpus.AH[0], yardstick.OU[0]]),
    ("1X2 chances to 0.05 and O/U line", ["p_home_band", "p_away_band", yardstick.OU[0]]),
)
KEY_COLUMNS = list(dict.fromkeys(column for _, by in GROUPINGS for column in by))
LISTED = "exact 9 prices"  # its groups are small, so its groups of 2+ events are listed
# (observed column, the yardstick's expected column, label)
QUANTITIES = (("is_comeback", "m_cb", "comeback"), ("seven", "m_seven", "7+ goals"))
THRESHOLDS = (2, 3)  # groups that hold at least this many events
SMALLEST_TAIL = "smallest tail p"
NULL_DRAWS = 1000
MIN_EXPECTED = 5.0  # a group with fewer expected events gets no place in the test across groups
COHORT_FLOOR = 3.0  # the expected events a group needs in each cohort to be carried over
TOP_SHARE = 0.2  # the share of groups chosen in one cohort


def group_frame(matches_df: pd.DataFrame, yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """The matches of the yardstick's frame that also have an AH market: their outcomes, the
    yardstick's chances, the league-season, cohort and league, the prices that the groupings
    read, and one group id per grouping."""

    ah_matches_df = matches_df.loc[yardstick_df.index]
    ah_matches_df = ah_matches_df[ah_matches_df[corpus.AH].notna().all(axis=1)].copy()
    ah_matches_df["p_home_band"] = (ah_matches_df["s2_mkt_p_home"] / BAND).round()
    ah_matches_df["p_away_band"] = (ah_matches_df["s2_mkt_p_away"] / BAND).round()

    columns = [column for observed, expected, _ in QUANTITIES for column in (observed, expected)]
    grouped_matches_df = yardstick_df.loc[ah_matches_df.index, [*columns, "cluster"]].copy()
    grouped_matches_df["season_cohort"] = ah_matches_df["season_cohort"]
    grouped_matches_df["league"] = ah_matches_df["s1_league_name"]
    grouped_matches_df[KEY_COLUMNS] = ah_matches_df[KEY_COLUMNS]

    for name, by in GROUPINGS:
        grouped_matches_df[name] = ah_matches_df.groupby(by, sort=False, dropna=False).ngroup()

    return grouped_matches_df


def null_chance(events: "pd.Series[float]", expected: "pd.Series[float]") -> np.ndarray:
    """Each match's chance under the null: the yardstick's, scaled to the observed total."""

    return np.asarray(expected * events.sum() / expected.sum(), dtype=float)


def group_sizes(grouped_matches_df: pd.DataFrame) -> pd.DataFrame:
    """Per grouping: how many groups, how many hold 2 or more matches, and their matches."""

    rows = []
    for name, _ in GROUPINGS:
        sizes = grouped_matches_df[name].value_counts()
        shared = sizes[sizes >= 2]
        rows.append(
            {
                "grouping": name,
                "groups": len(sizes),
                "groups of 2+": len(shared),
                "matches in them": int(shared.sum()),
                "largest": int(sizes.max()),
            }
        )

    return pd.DataFrame(rows)


def group_stats(groups: np.ndarray, events: np.ndarray, expected: np.ndarray) -> dict[str, float]:
    """For one set of outcomes: the groups with at least each of `THRESHOLDS` events, and the
    smallest Poisson tail p of a group with an event: the chance of at least its count if
    its expected count is right."""

    counts = np.bincount(groups, weights=events, minlength=len(expected))
    out: dict[str, float] = {f"{n} or more": float((counts >= n).sum()) for n in THRESHOLDS}
    hit = counts >= 1
    tails = poisson.sf(counts[hit] - 1, expected[hit])
    out[SMALLEST_TAIL] = float(tails.min()) if hit.any() else 1.0

    return out


def against_null(
    groups: np.ndarray,
    events: np.ndarray,
    chance: np.ndarray,
    draws: int = NULL_DRAWS,
    seed: int = 0,
) -> pd.DataFrame:
    """Each statistic of `group_stats` for the outcomes and for draws from the null: the
    mean, the 95% range, and the share of draws at least as extreme (one-sided)."""

    expected = np.bincount(groups, weights=chance)
    observed = group_stats(groups, events, expected)

    rng = np.random.default_rng(seed)
    null_df = pd.DataFrame(
        [
            group_stats(groups, (rng.random(len(chance)) < chance).astype(float), expected)
            for _ in range(draws)
        ]
    )

    rows = []
    for statistic, value in observed.items():
        sims = null_df[statistic]
        extreme = sims <= value if statistic == SMALLEST_TAIL else sims >= value

        rows.append(
            {
                "statistic": statistic,
                "observed": value,
                "null mean": float(sims.mean()),
                "null low": float(sims.quantile(0.025)),
                "null high": float(sims.quantile(0.975)),
                "p": (int(extreme.sum()) + 1) / (draws + 1),
            }
        )

    return pd.DataFrame(rows)


def group_table(
    grouped_matches_df: pd.DataFrame, grouping: str, observed: str, chance: np.ndarray
) -> pd.DataFrame:
    """Per group: its prices, its matches and events, the events that the null expects, the
    Poisson tail p of its count (the chance of at least that many), and its leagues."""

    grouped = grouped_matches_df.assign(null=chance).groupby(grouping)
    group_table_df = grouped[dict(GROUPINGS)[grouping]].first()

    group_table_df["matches"] = grouped.size()
    group_table_df["events"] = grouped[observed].sum()
    group_table_df["expected"] = grouped["null"].sum()
    group_table_df["tail p"] = poisson.sf(group_table_df["events"] - 1, group_table_df["expected"])
    group_table_df["leagues"] = grouped["league"].nunique()
    group_table_df["league names"] = grouped["league"].agg(_names)

    return group_table_df


def _names(leagues: "pd.Series[str]") -> str:
    """The distinct league names, sorted, in one string."""

    return ", ".join(sorted(set(leagues)))


def large_groups(grouped_matches_df: pd.DataFrame, grouping: str, expected: str) -> pd.DataFrame:
    """The matches of the groups with at least `MIN_EXPECTED` expected events."""

    sums = grouped_matches_df.groupby(grouping)[expected].transform("sum")

    return grouped_matches_df[sums >= MIN_EXPECTED]


def carry_over(
    grouped_matches_df: pd.DataFrame, grouping: str, observed: str, expected: str
) -> pd.DataFrame:
    """The `TOP_SHARE` of groups with the highest O/E in one cohort, read in the other.

    A group counts with `COHORT_FLOOR` or more expected events in each cohort. Each row adds
    the O/E of all counted groups in the other cohort, the level to compare with.
    """

    grouped = grouped_matches_df.groupby([grouping, "season_cohort"])
    events_df = grouped[observed].sum().unstack().fillna(0.0)
    chances_df = grouped[expected].sum().unstack().fillna(0.0)

    counted = chances_df.min(axis=1) >= COHORT_FLOOR
    events_df, chances_df = events_df[counted], chances_df[counted]

    cohorts = sorted(grouped_matches_df["season_cohort"].unique())
    if len(cohorts) != 2 or chances_df.empty:
        return pd.DataFrame()

    rows = []
    for chosen, other in ((cohorts[0], cohorts[1]), (cohorts[1], cohorts[0])):
        observed_over_expected = events_df[chosen] / chances_df[chosen]
        top = observed_over_expected >= observed_over_expected.quantile(1 - TOP_SHARE)

        rows.append(
            {
                "chosen in": chosen,
                "groups": len(chances_df),
                "chosen": int(top.sum()),
                "O/E where chosen": events_df[chosen][top].sum() / chances_df[chosen][top].sum(),
                "events in the other": events_df[other][top].sum(),
                "expected in the other": chances_df[other][top].sum(),
                "O/E in the other": events_df[other][top].sum() / chances_df[other][top].sum(),
                "O/E of all in the other": events_df[other].sum() / chances_df[other].sum(),
            }
        )

    return pd.DataFrame(rows)


def show_grouping(grouped_matches_df: pd.DataFrame, grouping: str, seed: int) -> None:
    """Every table of one grouping, for each quantity."""

    groups = grouped_matches_df[grouping].to_numpy()
    for observed, expected, label in QUANTITIES:
        title = f"{grouping}, {label}"
        chance = null_chance(grouped_matches_df[observed], grouped_matches_df[expected])
        events = grouped_matches_df[observed].to_numpy(dtype=float)

        report.show(f"{title}: against the null", against_null(groups, events, chance, seed=seed))

        group_table_df = group_table(grouped_matches_df, grouping, observed, chance)
        if grouping == LISTED:
            report.show(
                f"{title}: the groups of 2+ events", group_table_df[group_table_df["events"] >= 2]
            )
        else:
            surprising_df = group_table_df.nsmallest(1, "tail p").drop(columns="league names")
            report.show(f"{title}: the most surprising group", surprising_df)

        large_df = large_groups(grouped_matches_df, grouping, expected)
        if large_df[grouping].nunique() >= 2:
            quantity = (observed, expected, f"{label}, O/E", "event")
            row, _ = units.summary_row(large_df, grouping, quantity, luck=True)
            group_table_df = pd.DataFrame([row])
            group_table_df.insert(1, "groups", large_df[grouping].nunique())
            group_table_df.insert(2, "matches", len(large_df))
            report.show(
                f"{title}: one test across the groups of {MIN_EXPECTED:g}+ expected", group_table_df
            )

        carried_df = carry_over(grouped_matches_df, grouping, observed, expected)
        if not carried_df.empty:
            report.show(f"{title}: the top groups of one cohort in the other", carried_df)


def main() -> None:
    """Entry point: print whether comebacks and 7+ collect on the same opening prices."""

    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid())
    grouped_matches_df = group_frame(matches_df, yardstick_df)
    print(f"matches with all three opening markets: {len(grouped_matches_df):,}")

    report.show("The groups", group_sizes(grouped_matches_df))
    for seed, (grouping, _) in enumerate(GROUPINGS):
        show_grouping(grouped_matches_df, grouping, seed)


if __name__ == "__main__":
    main()
