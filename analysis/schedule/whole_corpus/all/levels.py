"""Which level the differences sit at: the league, the league-season, the team or the round.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/LEVELS.md`. Each level is tested around the
level above it (`units.level_row`): the leagues around all matches, the league-seasons around
their league, the rounds around their league-season, and the teams of a league-season around
it. Each quantity is read raw and against the odds yardstick. The spread that a test finds is
a share of a match's variance, next to the share that the yardstick carries (`odds_share`).
The match levels read the card (`card.ODDS_CARD`); the team level reads the team card, two
rows per match (`notes/ANALYSIS/CLAUDE.md` §2). Then the tests against the odds in each
season cohort.

Run: `uv run python -m analysis.schedule.whole_corpus.all.levels`
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd

from analysis import card, corpus, report, units
from analysis.methods import yardstick


@dataclass(frozen=True)
class Level:
    """One level: its parts tested around their unit, on the "match" rows (the yardstick's
    frame) or the "team" rows (its team rows)."""

    name: str
    unit: str
    part: str
    rows: str


EVERYTHING = "all"  # the column of one unit that holds every match
LEAGUE = "league"
LEAGUE_SEASON = "cluster"
ROUND = "round"
TEAM_SEASON = "team_season"
# The team card, on the rows of `card.team_yardstick_rows`. Each row:
# card.OddsQuantity(observed column, denominator column, yardstick column, label, kind).
TEAM_QUANTITIES = (
    card.OddsQuantity("comes_back", "one", "m_comes_back", "comes back", "event"),
    card.OddsQuantity("loses_lead", "one", "m_loses_lead", "loses a lead", "event"),
    card.OddsQuantity("behind", "one", "m_behind", "behind at half-time", "event"),
    card.OddsQuantity("comes_back", "behind", "m_wins_from_behind", "behind, then wins", "event"),
    card.OddsQuantity("goals_for", "one", "m_goals_for", "goals scored", "count"),
    card.OddsQuantity("goals_against", "one", "m_goals_against", "goals conceded", "count"),
)
# Each level's parts around their unit: Level(name, unit, part, rows).
LEVELS = (
    Level("league", EVERYTHING, LEAGUE, "match"),
    Level("league-season", LEAGUE, LEAGUE_SEASON, "match"),
    Level("round", LEAGUE_SEASON, ROUND, "match"),
    Level("team-season", LEAGUE_SEASON, TEAM_SEASON, "team"),
)
COHORT_LEVELS = ("league", "round", "team-season")  # a league has one season in each cohort
READINGS = ("raw", "odds")


def odds_share(df: pd.DataFrame, observed: str, denominator: str, model: str) -> float:
    """The share of a match's variance that the yardstick carries: 1 - SSE / SST, with the
    yardstick's expected values times the pooled O/E as the fit, over the matches that count
    (denominator above 0)."""

    counted_df = df[df[denominator] > 0]
    observed_values, expected = counted_df[observed], counted_df[model]
    fitted = expected * observed_values.sum() / expected.sum()
    error = ((observed_values - fitted) ** 2).sum()

    return float(1.0 - error / ((observed_values - observed_values.mean()) ** 2).sum())


def level_tests(
    rows: dict[str, pd.DataFrame],
    levels: tuple[str, ...],
    readings: tuple[str, ...] = READINGS,
    draws: int = units.NULL_DRAWS,
) -> pd.DataFrame:
    """One test for each level, quantity and reading; `rows` maps "match" and "team" to the
    frames that the levels read."""

    quantities = {"match": card.ODDS_CARD, "team": TEAM_QUANTITIES}

    table = []
    for level in LEVELS:
        if level.name not in levels:
            continue

        level_rows_df = rows[level.rows]
        for quantity in quantities[level.rows]:
            for reading in readings:
                expected = quantity.denominator if reading == "raw" else quantity.yardstick
                row = units.level_row(
                    level_rows_df, level.unit, level.part, quantity.against(expected), draws
                )
                table.append({"level": level.name, "reading": reading, **row})

    return pd.DataFrame(table)


def odds_shares(rows: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """For each quantity of the two cards: the share of a match's variance that the yardstick
    carries, and the variance itself."""

    table = []
    for kind_of_rows, quantities in (("match", card.ODDS_CARD), ("team", TEAM_QUANTITIES)):
        level_rows_df = rows[kind_of_rows]
        for quantity in quantities:
            counted = level_rows_df.loc[level_rows_df[quantity.denominator] > 0, quantity.observed]
            table.append(
                {
                    "rows": kind_of_rows,
                    "quantity": quantity.label,
                    "counted": float(len(counted)),
                    "variance": float(np.var(counted.to_numpy(dtype=float), ddof=1)),
                    "odds share": odds_share(
                        level_rows_df, quantity.observed, quantity.denominator, quantity.yardstick
                    ),
                }
            )

    return pd.DataFrame(table)


def main() -> None:
    """Entry point: print which level the differences sit at."""

    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid())
    yardstick_df["one"] = 1.0
    yardstick_df[EVERYTHING] = EVERYTHING
    yardstick_df[LEAGUE] = matches_df["s1_league_id"]
    yardstick_df[ROUND] = corpus.round_key(matches_df)
    yardstick_df["season_cohort"] = matches_df["season_cohort"]

    team_rows_df = card.team_yardstick_rows(matches_df, yardstick_df)
    team_rows_df[TEAM_SEASON] = team_rows_df[LEAGUE_SEASON] + " " + team_rows_df["team"].astype(str)
    rows = {"match": yardstick_df, "team": team_rows_df}

    print(
        f"priced matches (both opening markets): {len(yardstick_df):,}; leagues "
        f"{yardstick_df[LEAGUE].nunique()}; league-seasons "
        f"{yardstick_df[LEAGUE_SEASON].nunique()}; rounds "
        f"{yardstick_df[ROUND].nunique():,}; team-seasons {team_rows_df[TEAM_SEASON].nunique():,} "
        f"({len(team_rows_df):,} team-matches)"
    )

    print(f"each p: {units.NULL_DRAWS} shuffles of the parts inside their units")
    report.show("The share of a match's variance that the odds carry", odds_shares(rows))

    every = tuple(level.name for level in LEVELS)
    report.show("One test of each level around the level above it", level_tests(rows, every))

    for cohort in sorted(yardstick_df["season_cohort"].unique()):
        in_cohort = {
            name: kind_rows_df[kind_rows_df["season_cohort"] == cohort]
            for name, kind_rows_df in rows.items()
        }
        report.show(
            f"Against the odds: season cohort {cohort} ({len(in_cohort['match']):,} matches)",
            level_tests(in_cohort, COHORT_LEVELS, readings=("odds",)),
        )


if __name__ == "__main__":
    main()
