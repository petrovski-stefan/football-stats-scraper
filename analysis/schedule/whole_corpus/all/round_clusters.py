"""Comebacks and 7+ in one round: do they collect there, beyond the league-season and the odds?

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ROUND_CLUSTERS.md`. A round is one round of one
stage of a league-season (`corpus.round_key`). For each quantity of the card, one test of the
rounds (`units.level_row`), read three ways: raw around all matches, where the league-season
makes clusters too; raw around the league-season of the round; and against the odds yardstick
around the league-season, where the prices of the matches of a round change nothing. Then the
test against the odds on the matches played near the date of their round, and the tests around
the league-season in each season cohort, with all rounds and without the first rounds of each
stage (`ALL/SEASON_PHASE.md` C5). Then the rounds that carry the largest part of Q against
the odds, and the rounds by their count of comebacks and of 7+ matches, against the count
that the odds and the league-season expect.

Run: `uv run python -m analysis.schedule.whole_corpus.all.round_clusters`
"""

import numpy as np
import pandas as pd

from analysis import card, corpus, report, units
from analysis.methods import yardstick

ROUND = "round"
LEAGUE_SEASON = "cluster"
EVERYTHING = "all"  # the column of one unit that holds every match
NEAR_DAYS = 3.0  # a match more days than this from the median kickoff of its round is far
COUNTED = ("comeback", "7+ goals")  # the quantities of the count tables
MOST = 4  # the last row of a count table holds this count and more
LARGEST = ("7+ goals", "goals per match")  # the quantities of the tables of the largest rounds
TOP_ROUNDS = 5
FIRST_ROUNDS = 3  # the first rounds of a stage, where goals fall short of the odds
RAW_READING = "raw, around its league-season"
ODDS_READING = "odds, around its league-season"


def readings(quantity: tuple[str, str, str, str, str]) -> tuple[tuple[str, str, str], ...]:
    """(reading, unit, expected column) of each way to read a quantity of `card.ODDS_CARD`."""
    _, denominator, model, _, _ = quantity
    return (
        ("raw, around all matches", EVERYTHING, denominator),
        (RAW_READING, LEAGUE_SEASON, denominator),
        (ODDS_READING, LEAGUE_SEASON, model),
    )


def tests(
    yardstick_df: pd.DataFrame, only: tuple[str, ...] = (), draws: int = units.NULL_DRAWS
) -> pd.DataFrame:
    """One test of the rounds for each quantity and reading (only the readings named in
    `only`, if it names any)."""
    rows = []
    for quantity in card.ODDS_CARD:
        observed, _, _, label, kind = quantity
        for reading, unit, expected in readings(quantity):
            if only and reading not in only:
                continue
            row = units.level_row(
                yardstick_df, unit, ROUND, (observed, expected, label, kind), draws
            )
            rows.append({"reading": reading, **row})

    return pd.DataFrame(rows)


def largest_rounds(
    yardstick_df: pd.DataFrame, quantity: tuple[str, str, str, str, str], top: int = TOP_ROUNDS
) -> pd.DataFrame:
    """The rounds with the largest part of Q against the odds: each round's squared distance
    from its league-season, over its variance (`units.within_tested`)."""
    observed, _, model, _, kind = quantity
    part_values_df = units.within_tested(
        yardstick_df, LEAGUE_SEASON, ROUND, observed, model, kind
    ).part_values_df

    rounds = yardstick_df.groupby(ROUND)
    largest_rounds_df = pd.DataFrame(
        {
            "league": rounds["league"].first(),
            "matches": rounds.size(),
            "observed": part_values_df["observed"],
            "expected": part_values_df["expected"],
            "O/E": part_values_df["value"],
            "league-season O/E": part_values_df["owner_mean"],
            "part of Q": (part_values_df["value"] - part_values_df["owner_mean"]) ** 2
            / part_values_df["variance"],
        }
    ).dropna(subset=["part of Q"])

    return largest_rounds_df.sort_values("part of Q", ascending=False).head(top).reset_index()


def days_from_round(
    kickoff: "pd.Series[pd.Timestamp]", rounds: "pd.Series[str]"
) -> "pd.Series[float]":
    """How many days each match kicked off from the median kickoff of its round."""
    days = (kickoff - pd.Timestamp(0, tz="UTC")) / pd.Timedelta(days=1)
    return (days - days.groupby(rounds).transform("median")).abs()


def league_season_chance(
    yardstick_df: pd.DataFrame, observed: str, model: str
) -> "pd.Series[float]":
    """Each match's chance of the event from the odds, times the O/E of its league-season."""
    sums_df = yardstick_df.groupby(LEAGUE_SEASON)[[observed, model]].transform("sum")
    return (yardstick_df[model] * sums_df[observed] / sums_df[model]).clip(0.0, 1.0)


def count_table(
    events: "pd.Series[float]", chances: "pd.Series[float]", rounds: "pd.Series[str]"
) -> pd.DataFrame:
    """The rounds by their count of events: observed, and expected if each match has its own
    chance, apart from the other matches of its round (a Poisson-binomial count per round)."""
    expected = np.zeros(MOST + 1)
    for _, group in chances.groupby(rounds):
        distribution = np.array([1.0])
        for chance in group.to_numpy(dtype=float):
            distribution = np.convolve(distribution, [1.0 - chance, chance])

        head = distribution[:MOST]
        expected[: len(head)] += head
        expected[MOST] += distribution[MOST:].sum()

    counts = events.groupby(rounds).sum().clip(upper=MOST).astype(int).to_numpy()
    return pd.DataFrame(
        {
            "events": [*(str(count) for count in range(MOST)), f"{MOST}+"],
            "rounds": np.bincount(counts, minlength=MOST + 1),
            "expected": expected,
        }
    )


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid())
    yardstick_df["one"] = 1.0
    yardstick_df[EVERYTHING] = EVERYTHING
    yardstick_df[ROUND] = corpus.round_key(matches_df)
    yardstick_df["league"] = matches_df["s1_league_name"]
    yardstick_df["round_number"] = matches_df["s1_round"]
    yardstick_df["season_cohort"] = matches_df["season_cohort"]

    kickoff = pd.to_datetime(matches_df.loc[yardstick_df.index, "s1_date"], utc=True)
    yardstick_df["days"] = days_from_round(kickoff, yardstick_df[ROUND])

    sizes = yardstick_df.groupby(ROUND).size()
    print(
        f"priced matches (both opening markets): {len(yardstick_df):,}; rounds: {len(sizes):,}; "
        f"matches per round: median {sizes.median():.0f}, {sizes.min()} to {sizes.max()}"
    )

    far = yardstick_df["days"] > NEAR_DAYS
    print(
        f"matches more than {NEAR_DAYS:.0f} days from the median kickoff of their round: "
        f"{far.sum():,} ({far.mean():.4f}), in {yardstick_df.loc[far, ROUND].nunique():,} rounds"
    )

    print(f"each p: {units.NULL_DRAWS} shuffles of the parts inside their units")
    report.show("One test of the rounds for each quantity and reading", tests(yardstick_df))
    report.show(
        f"Against the odds: only the matches within {NEAR_DAYS:.0f} days of their round",
        tests(yardstick_df[~far], only=(ODDS_READING,)),
    )

    for cohort, cohort_df in yardstick_df.groupby("season_cohort"):
        report.show(
            f"Around the league-season: season cohort {cohort} ({len(cohort_df):,} matches)",
            tests(cohort_df, only=(RAW_READING, ODDS_READING)),
        )

        later_rounds_df = cohort_df[cohort_df["round_number"] > FIRST_ROUNDS]
        report.show(
            f"Around the league-season: season cohort {cohort}, rounds {FIRST_ROUNDS + 1} and "
            f"later ({len(later_rounds_df):,} matches)",
            tests(later_rounds_df, only=(RAW_READING, ODDS_READING)),
        )

    for quantity in card.ODDS_CARD:
        if quantity[3] in LARGEST:
            report.show(
                f"The rounds with the largest part of Q against the odds: {quantity[3]}",
                largest_rounds(yardstick_df, quantity),
            )

    for observed, _, model, label, _ in card.ODDS_CARD:
        if label in COUNTED:
            chances = league_season_chance(yardstick_df, observed, model)
            report.show(
                f"Rounds by their count of {label}: expected from the odds and the league-season",
                count_table(yardstick_df[observed], chances, yardstick_df[ROUND]),
            )


if __name__ == "__main__":
    main()
