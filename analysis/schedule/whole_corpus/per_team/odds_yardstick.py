"""The odds yardstick per team: each team against what the odds expect, read against its league.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_TEAM/ODDS_YARDSTICK.md`. In each match, the
yardstick of `ALL/ODDS_YARDSTICK.md` gives each team a chance of each role, from the opening
prices, which carry the strength of both teams (`notes/ANALYSIS/CLAUDE.md` §5, rule 7). First
the calibration of the yardstick by the team's own win chance: a repeat can come from a
yardstick that is wrong by strength (rule 8). Then, for each quantity of the team card as
observed against expected (O/E), one test of the teams around their league, the shrunk
values, the spread that the test can find, and the repeat test. The two goal tests also run
against shuffles of the team-matches inside their league (`units.level_row`): for a count, the
dispersion measured around each team makes the chi-square p too small. Then the luck line and
the teams most above their league. No team is tested on its own.

Run: `uv run python -m analysis.schedule.whole_corpus.per_team.odds_yardstick`
"""

import pandas as pd

from analysis import card, corpus, report, stats, units
from analysis.methods import yardstick

UNIT = card.TEAM_UNIT  # a team in one league
LEAGUE = card.TEAM_LEAGUE
# (observed column, expected column, label, kind): a team's O/E is sum(observed) /
# sum(expected) over its rows. The expected columns are the yardstick's chances for the team.
QUANTITIES = (
    ("comes_back", "m_comes_back", "comes back", "event"),
    ("comes_back_home", "m_comes_back_home", "comes back at home", "event"),
    ("comes_back_away", "m_comes_back_away", "comes back away", "event"),
    ("behind", "m_behind", "behind at half-time", "event"),
    ("comes_back", "m_wins_from_behind", "behind, then wins", "event"),
    ("loses_lead", "m_loses_lead", "loses a lead", "event"),
    ("loses_lead_home", "m_loses_lead_home", "loses a lead at home", "event"),
    ("loses_lead_away", "m_loses_lead_away", "loses a lead away", "event"),
    ("ahead", "m_ahead", "ahead at half-time", "event"),
    ("loses_lead", "m_loses_from_ahead", "ahead, then loses", "event"),
    ("goals_for", "m_goals_for", "goals scored", "count"),
    ("goals_against", "m_goals_against", "goals conceded", "count"),
)
RANKED = ("comes back", "loses a lead")
GOALS = ("goals scored", "goals conceded")  # the counts, tested against shuffles too
# The role quantities whose Q is also checked against the test's own null.
ROLES = (
    "comes back",
    "comes back at home",
    "comes back away",
    "behind, then wins",
    "loses a lead",
    "loses a lead at home",
    "loses a lead away",
    "ahead, then loses",
)
# The calibration by strength: the team's own Shin win chance, and the quantities it checks.
WIN_EDGES = (0.0, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 1.0)
CALIBRATED = (
    "comes back",
    "loses a lead",
    "behind at half-time",
    "ahead at half-time",
    "goals scored",
    "goals conceded",
)
TOP = 20


def calibration(team_rows_df: pd.DataFrame) -> pd.DataFrame:
    """O/E of the calibrated quantities by the team's own win chance, with the interval over
    league-seasons."""
    bands = pd.cut(team_rows_df["win_chance"], WIN_EDGES)

    table = []
    for band, band_df in team_rows_df.groupby(bands, observed=True):
        for observed, expected, label, _ in QUANTITIES:
            if label in CALIBRATED:
                table.append(
                    {
                        "win chance": str(band),
                        "quantity": label,
                        **stats.observed_expected(band_df, observed, expected),
                    }
                )

    return pd.DataFrame(table)


def shuffle_table(team_rows_df: pd.DataFrame) -> pd.DataFrame:
    """The goal tests of the teams around their league against shuffles of the team-matches
    inside their league (`units.level_row`)."""
    return pd.DataFrame(
        [
            units.level_row(team_rows_df, LEAGUE, UNIT, quantity)
            for quantity in QUANTITIES
            if quantity[2] in GOALS
        ]
    )


def null_table(team_rows_df: pd.DataFrame, results: dict[str, units.Within]) -> pd.DataFrame:
    """For each role quantity: its real Q, and Q when the outcomes come from the test's own
    null (`units.null_q`), in sds of the null draws."""
    table = []
    for quantity in QUANTITIES:
        label = quantity[2]
        if label not in ROLES:
            continue

        mean, sd = units.null_q(team_rows_df, LEAGUE, UNIT, quantity)
        real = results[label].cochran_q
        table.append(
            {
                "quantity": label,
                "Q": real,
                "df": float(results[label].degrees_of_freedom),
                "null Q mean": mean,
                "null Q sd": sd,
                "real - null, in sd": (real - mean) / sd,
            }
        )

    return pd.DataFrame(table)


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    share = yardstick.first_half_share(yardstick.priced(matches_df))
    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid(), share=share)
    team_rows_df = card.team_yardstick_rows(matches_df, yardstick_df)
    print(f"Priced: {len(yardstick_df):,} matches; first-half share {share:.4f}")
    print(card.team_line(team_rows_df))

    report.show("Calibration by the team's own win chance (O/E)", calibration(team_rows_df))

    summary, results = [], {}
    for quantity in QUANTITIES:
        row, results[quantity[2]] = units.within_row(team_rows_df, LEAGUE, UNIT, quantity)
        summary.append(row)

    report.show("One test of the teams around their league, for each O/E", pd.DataFrame(summary))
    report.show("Q against the test's own null (100 draws)", null_table(team_rows_df, results))
    report.show(
        f"The goal tests against {units.NULL_DRAWS} shuffles of the team-matches in their league",
        shuffle_table(team_rows_df),
    )
    report.show(
        "The luck line of the two roles",
        pd.DataFrame([units.within_luck_row(label, results[label]) for label in RANKED]),
    )

    for label in RANKED:
        report.show(
            f"Teams most above their league: {label}",
            card.top_teams(
                team_rows_df,
                results[label].part_values_df,
                TOP,
                names=("observed", "expected", "O/E"),
            ),
        )


if __name__ == "__main__":
    main()
