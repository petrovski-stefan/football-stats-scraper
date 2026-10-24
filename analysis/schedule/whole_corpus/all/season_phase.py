"""Comebacks and 7+ by season phase: the per-round slice of the ALL level.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SEASON_PHASE.md`. A match's phase is its round
as a share of its stage's rounds, because leagues play different numbers of rounds
(`notes/ANALYSIS/CLAUDE.md` §2, slices): the third of the stage by round, the third by kickoff
order, and the first and last rounds. Then the round number itself. Each quantity is read
three ways: raw; against its league-season, where each match expects the value of its own
league-season; and against the odds yardstick (`analysis/methods/yardstick.py`). One test
across the phases for each quantity and reading.

Run: `uv run python -m analysis.schedule.whole_corpus.all.season_phase`
"""

import numpy as np
import pandas as pd

from analysis import card, corpus, report, stats, units
from analysis.methods import yardstick

# (observed column, denominator column, yardstick column, label, kind)
QUANTITIES = card.ODDS_CARD
# The quantities of the round-number section: the luck line there needs counts or rare events.
ROUND_QUANTITIES = ("comeback", "7+ goals", "goals per match")
THIRDS = 3
EDGE_ROUNDS = 3  # the first and the last rounds of a stage
EDGES = ("1: first 3 rounds", "2: middle", "3: last 3 rounds")
MIN_ROUND_MATCHES = 600  # a round number played in fewer matches is a mix of a few leagues


def phases(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Per match: its round, the rounds of its stage, and its phase in three ways.

    `third` is the third of the stage by round number, `third_kickoff` the third by kickoff
    order inside the stage (a match played late counts where it was played), and `edge` the
    first or last `EDGE_ROUNDS` rounds of the stage, or the middle.
    """

    keys = [matches_df["s1_league_id"], matches_df["s1_season"], matches_df["s1_stage"].fillna("")]
    rounds = matches_df["s1_round"].groupby(keys).transform("max")

    kickoff = pd.to_datetime(matches_df["s1_date"], utc=True)
    order = kickoff.groupby(keys).rank(method="first", pct=True)

    edge = np.select(
        [matches_df["s1_round"] <= EDGE_ROUNDS, matches_df["s1_round"] > rounds - EDGE_ROUNDS],
        [EDGES[0], EDGES[2]],
        EDGES[1],
    )

    return pd.DataFrame(
        {
            "round": matches_df["s1_round"],
            "rounds": rounds,
            "third": np.ceil(THIRDS * matches_df["s1_round"] / rounds).clip(1, THIRDS).astype(int),
            "third_kickoff": np.ceil(THIRDS * order).clip(1, THIRDS).astype(int),
            "edge": edge,
        },
        index=matches_df.index,
    )


def league_season_column(label: str) -> str:
    """The column of a quantity's expected values against its league-season."""

    return f"league-season {label}"


def with_league_season(phased_df: pd.DataFrame) -> pd.DataFrame:
    """The frame with each quantity's expected value against its league-season: the match's
    denominator times its league-season's value, so phase changes nothing inside it."""

    with_league_season_df = phased_df.copy()
    for observed, denominator, _, label, _ in QUANTITIES:
        sums_df = phased_df.groupby("cluster")[[observed, denominator]].transform("sum")
        with_league_season_df[league_season_column(label)] = (
            phased_df[denominator] * sums_df[observed] / sums_df[denominator]
        )
    return with_league_season_df


def readings(quantity: tuple[str, str, str, str, str]) -> tuple[tuple[str, str], ...]:
    """(reading, expected column) of each way to read a quantity: raw, against its
    league-season, and against the odds."""

    _, denominator, model, label, _ = quantity
    return (
        ("raw", denominator),
        ("league-season", league_season_column(label)),
        ("odds", model),
    )


def phase_values(
    phased_df: pd.DataFrame, phase: str, quantity: tuple[str, str, str, str, str]
) -> pd.DataFrame:
    """Per phase: the matches, the count, and the value of each reading (an O/E but for the
    raw one); the raw and odds values with their intervals over league-seasons."""

    observed = quantity[0]

    rows = []
    for key, phase_df in phased_df.groupby(phase):
        row: dict[str, object] = {
            "phase": key,
            "matches": len(phase_df),
            "count": phase_df[observed].sum(),
        }

        for reading, expected in readings(quantity):
            ratio = stats.observed_expected(phase_df, observed, expected)
            row[reading] = ratio["oe"]
            if reading != "league-season":
                row[f"{reading} low"], row[f"{reading} high"] = ratio["low"], ratio["high"]

        rows.append(row)

    return pd.DataFrame(rows)


def phase_tests(phased_df: pd.DataFrame, phase: str) -> pd.DataFrame:
    """One test across the phases for each quantity and reading: Cochran's Q of the phase
    values, each with the variance of its kind times the dispersion (`analysis/units.py`)."""

    rows = []
    for quantity in QUANTITIES:
        observed, _, _, label, kind = quantity
        for reading, expected in readings(quantity):
            dispersion_factor = units.dispersion(phased_df, phase, observed, expected, kind)
            phase_values_df = units.unit_values(
                phased_df, phase, observed, expected, kind, dispersion_factor
            )
            het = stats.heterogeneity(phase_values_df["value"], phase_values_df["variance"])

            rows.append(
                {
                    "quantity": label,
                    "reading": reading,
                    "dispersion": dispersion_factor,
                    "Q": het.cochran_q,
                    "df": het.degrees_of_freedom,
                    "p": f"{het.p_value:.3g}",
                }
            )

    return pd.DataFrame(rows)


def common_rounds(phased_df: pd.DataFrame) -> pd.DataFrame:
    """The matches of the round numbers played in at least `MIN_ROUND_MATCHES` matches."""

    sizes = phased_df.groupby("round")["one"].transform("sum")
    return phased_df[sizes >= MIN_ROUND_MATCHES]


def round_summary(common_rounds_df: pd.DataFrame) -> pd.DataFrame:
    """The round numbers as units (`units.summary_row`): one test, the luck line and the
    agreement of the cohorts."""

    rows = []
    for quantity in QUANTITIES:
        observed, _, _, label, kind = quantity
        if label not in ROUND_QUANTITIES:
            continue

        for reading, expected in readings(quantity):
            row, _ = units.summary_row(
                common_rounds_df,
                "round",
                (observed, expected, f"{label}, {reading}", kind),
                luck=True,
            )
            rows.append(row)

    return pd.DataFrame(rows)


def show_phase(phased_df: pd.DataFrame, phase: str, title: str, labels: tuple[str, ...]) -> None:
    """The values of the quantities named in `labels` by phase, then the tests of all."""

    for quantity in QUANTITIES:
        if quantity[3] in labels:
            report.show(f"{title}: {quantity[3]}", phase_values(phased_df, phase, quantity))
    report.show(f"{title}: one test across the phases", phase_tests(phased_df, phase))


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid())
    yardstick_df["one"] = 1.0
    phased_df = with_league_season(yardstick_df.join(phases(matches_df)))
    phased_df["season_cohort"] = matches_df["season_cohort"]

    print(f"priced matches (both opening markets): {len(phased_df):,}")
    every = tuple(quantity[3] for quantity in QUANTITIES)
    show_phase(phased_df, "third", "Thirds by round", every)
    show_phase(phased_df, "third_kickoff", "Thirds by kickoff order", ROUND_QUANTITIES)
    show_phase(phased_df, "edge", "First and last rounds", ROUND_QUANTITIES)

    for cohort, cohort_df in phased_df.groupby("season_cohort"):
        size = f"season cohort {cohort} ({len(cohort_df):,} matches)"
        show_phase(cohort_df, "third", f"Thirds by round, {size}", ROUND_QUANTITIES)
        show_phase(cohort_df, "edge", f"First and last rounds, {size}", ROUND_QUANTITIES)

    common_rounds_df = common_rounds(phased_df)
    rounds = sorted(common_rounds_df["round"].unique())
    print(
        f"\nround numbers with {MIN_ROUND_MATCHES}+ matches: {rounds[0]} to {rounds[-1]}, "
        f"{len(rounds)} of them, {len(common_rounds_df):,} matches"
    )
    report.show("The round number as a unit", round_summary(common_rounds_df))


if __name__ == "__main__":
    main()
