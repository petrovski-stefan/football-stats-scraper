"""The card per team: a team in one league, read against its league.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_TEAM/RATES.md`. Each match gives two team rows,
one for each team (`analysis/card.py:team_rows`). For each quantity of the team card
(`notes/ANALYSIS/CLAUDE.md` §2: the two roles, each at home and away, and the goals scored and
conceded), prints one test of the teams around their own league, the spread of the shrunk team
values against their league, and the repeat test: does a team's value in one season cohort
predict its value in the other, both against its league? Then, for the two roles, the luck
line and the teams most above their league after shrinkage. No team is tested on its own.

Run: `uv run python -m analysis.schedule.whole_corpus.per_team.rates`
"""

import pandas as pd

from analysis import card, corpus, report, units

UNIT = card.TEAM_UNIT  # a team in one league
LEAGUE = card.TEAM_LEAGUE
# (numerator column, denominator column, label, kind): sum(numerator) / sum(denominator) over
# the rows of a team. The two roles: the team comes back (behind at half-time, then wins),
# and the team loses a lead (ahead at half-time, then loses).
QUANTITIES = (
    ("comes_back", "one", "comes back", "event"),
    ("comes_back_home", "home", "comes back at home", "event"),
    ("comes_back_away", "away", "comes back away", "event"),
    ("behind", "one", "behind at half-time", "event"),
    ("comes_back", "behind", "behind, then wins", "event"),
    ("loses_lead", "one", "loses a lead", "event"),
    ("loses_lead_home", "home", "loses a lead at home", "event"),
    ("loses_lead_away", "away", "loses a lead away", "event"),
    ("ahead", "one", "ahead at half-time", "event"),
    ("loses_lead", "ahead", "ahead, then loses", "event"),
    ("goals_for", "one", "goals scored", "count"),
    ("goals_against", "one", "goals conceded", "count"),
)
RANKED = ("comes back", "loses a lead")
TOP = 20  # the teams in each list of the top teams, chosen on 2026-10-19


def main() -> None:
    """Entry point: print the card per team."""

    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    team_rows_df = card.team_rows(matches_df)
    print(card.team_line(team_rows_df))

    summary, within_results = [], {}
    for quantity in QUANTITIES:
        row, within_results[quantity[2]] = units.within_row(team_rows_df, LEAGUE, UNIT, quantity)
        summary.append(row)

    report.show(
        "One test of the teams around their league, for each quantity", pd.DataFrame(summary)
    )
    report.show(
        "The luck line of the two roles",
        pd.DataFrame([units.within_luck_row(label, within_results[label]) for label in RANKED]),
    )

    for label in RANKED:
        report.show(
            f"Teams most above their league: {label}",
            card.top_teams(team_rows_df, within_results[label].part_values_df, TOP),
        )


if __name__ == "__main__":
    main()
