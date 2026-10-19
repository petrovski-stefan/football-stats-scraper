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

import numpy as np
import pandas as pd

from analysis import card, corpus, report, units
from analysis.methods import yardstick

EVERYTHING = "all"  # the column of one unit that holds every match
LEAGUE = "league"
LEAGUE_SEASON = "cluster"
ROUND = "round"
TEAM_SEASON = "team_season"
# (observed column, denominator column, yardstick column, label, kind): the team card, on the
# rows of `card.team_yardstick_rows`.
TEAM_QUANTITIES = (
    ("comes_back", "one", "m_comes_back", "comes back", "event"),
    ("loses_lead", "one", "m_loses_lead", "loses a lead", "event"),
    ("behind", "one", "m_behind", "behind at half-time", "event"),
    ("comes_back", "behind", "m_wins_from_behind", "behind, then wins", "event"),
    ("goals_for", "one", "m_goals_for", "goals scored", "count"),
    ("goals_against", "one", "m_goals_against", "goals conceded", "count"),
)
# (level, unit, part, rows): each level's parts around their unit. "match" rows are the
# yardstick's frame, "team" rows its team rows.
LEVELS = (
    ("league", EVERYTHING, LEAGUE, "match"),
    ("league-season", LEAGUE, LEAGUE_SEASON, "match"),
    ("round", LEAGUE_SEASON, ROUND, "match"),
    ("team-season", LEAGUE_SEASON, TEAM_SEASON, "team"),
)
COHORT_LEVELS = ("league", "round", "team-season")  # a league has one season in each cohort
READINGS = ("raw", "odds")


def odds_share(frame: pd.DataFrame, observed: str, denominator: str, model: str) -> float:
    """The share of a match's variance that the yardstick carries: 1 - SSE / SST, with the
    yardstick's expected values times the pooled O/E as the fit, over the matches that count
    (denominator above 0)."""
    counted = frame[frame[denominator] > 0]
    observed_values, expected = counted[observed], counted[model]
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
    for level, unit, part, kind_of_rows in LEVELS:
        if level not in levels:
            continue
        frame = rows[kind_of_rows]
        for observed, denominator, model, label, kind in quantities[kind_of_rows]:
            for reading in readings:
                expected = denominator if reading == "raw" else model
                quantity = (observed, expected, label, kind)
                row = units.level_row(frame, unit, part, quantity, draws)
                table.append({"level": level, "reading": reading, **row})
    return pd.DataFrame(table)


def odds_shares(rows: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """For each quantity of the two cards: the share of a match's variance that the yardstick
    carries, and the variance itself."""
    table = []
    for kind_of_rows, quantities in (("match", card.ODDS_CARD), ("team", TEAM_QUANTITIES)):
        frame = rows[kind_of_rows]
        for observed, denominator, model, label, _ in quantities:
            counted = frame.loc[frame[denominator] > 0, observed]
            table.append(
                {
                    "rows": kind_of_rows,
                    "quantity": label,
                    "counted": float(len(counted)),
                    "variance": float(np.var(counted.to_numpy(dtype=float), ddof=1)),
                    "odds share": odds_share(frame, observed, denominator, model),
                }
            )
    return pd.DataFrame(table)


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    frame = yardstick.frame(matches, yardstick.build_grid())
    frame["one"] = 1.0
    frame[EVERYTHING] = EVERYTHING
    frame[LEAGUE] = matches["s1_league_id"]
    frame[ROUND] = corpus.round_key(matches)
    frame["season_cohort"] = matches["season_cohort"]
    teams = card.team_yardstick_rows(matches, frame)
    teams[TEAM_SEASON] = teams[LEAGUE_SEASON] + " " + teams["team"].astype(str)
    rows = {"match": frame, "team": teams}
    print(
        f"priced matches (both opening markets): {len(frame):,}; leagues "
        f"{frame[LEAGUE].nunique()}; league-seasons {frame[LEAGUE_SEASON].nunique()}; rounds "
        f"{frame[ROUND].nunique():,}; team-seasons {teams[TEAM_SEASON].nunique():,} "
        f"({len(teams):,} team-matches)"
    )
    print(f"each p: {units.NULL_DRAWS} shuffles of the parts inside their units")
    report.show("The share of a match's variance that the odds carry", odds_shares(rows))
    every = tuple(level for level, *_ in LEVELS)
    report.show("One test of each level around the level above it", level_tests(rows, every))
    for cohort in sorted(frame["season_cohort"].unique()):
        in_cohort = {name: part[part["season_cohort"] == cohort] for name, part in rows.items()}
        report.show(
            f"Against the odds: season cohort {cohort} ({len(in_cohort['match']):,} matches)",
            level_tests(in_cohort, COHORT_LEVELS, readings=("odds",)),
        )


if __name__ == "__main__":
    main()
