"""The card per league: one heterogeneity test per quantity, and shrunk league values.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/RATES.md`. For each quantity of the card
(`analysis/card.py`), prints one test across the leagues, the spread of the shrunk league
values, the luck line of the two market rates, and the agreement of the two season cohorts.
Then one test of the league-seasons inside their leagues; the two stages of the leagues that
keep both; and the league table, ranked by the shrunk comeback rate. No league is tested on
its own. The count against the odds is in `PER_LEAGUE/ODDS_YARDSTICK.md`.

Run: `uv run python -m analysis.schedule.whole_corpus.per_league.rates`
"""

import pandas as pd

from analysis import card, corpus, report, stats, units

LEAGUE = "s1_league_id"
MARKETS = ("comeback", "7+ goals")  # the luck line: rare events, so Poisson draws fit them
SLICED = ("comeback", "7+ goals", "goals per match")  # the season and stage slices
# The stages of a league that keeps two, one after the other. Apertura-B is a part of the
# Apertura of one league.
STAGES = {"Apertura": "Apertura", "Apertura-B": "Apertura", "Clausura": "Clausura"}
# (quantity, column of its league values, header) of the league table.
TABLE_COLUMNS = (
    ("comeback", "observed", "comebacks"),
    ("comeback", "value", "rate"),
    ("comeback", "shrunk", "shrunk"),
    ("link 1: a team is behind at half-time", "shrunk", "link 1 shrunk"),
    ("link 2: the team behind wins", "shrunk", "link 2 shrunk"),
    ("7+ goals", "observed", "7+"),
    ("7+ goals", "value", "7+ rate"),
    ("7+ goals", "shrunk", "7+ shrunk"),
    ("goals in the first half", "value", "goals 1H"),
    ("goals in the second half", "value", "goals 2H"),
)


def quantity(label: str) -> tuple[str, str, str, str]:
    """The card's row with this label."""
    return next(row for row in card.CARD if row[2] == label)


def season_tests(frame: pd.DataFrame) -> pd.DataFrame:
    """Per sliced quantity: one test of the league-seasons around their own league."""
    rows = []
    for label in SLICED:
        numerator, denominator, _, kind = quantity(label)
        q, df, p = units.within_test(frame, LEAGUE, "cluster", numerator, denominator, kind)
        rows.append({"quantity": label, "Q": q, "df": float(df), "p": f"{p:.3g}"})
    return pd.DataFrame(rows)


def stage_table(frame: pd.DataFrame) -> pd.DataFrame:
    """The sliced quantities in the two stages of the leagues that keep both."""
    stage = frame["stage"].map(STAGES)
    rows = []
    for name, group in frame.groupby(stage):
        for label in SLICED:
            numerator, denominator, _, _ = quantity(label)
            ratio = stats.observed_expected(group, numerator, denominator)
            rows.append(
                {
                    "stage": name,
                    "quantity": label,
                    "matches": ratio["n"],
                    "value": ratio["oe"],
                    "low": ratio["low"],
                    "high": ratio["high"],
                }
            )
    return pd.DataFrame(rows)


def league_table(frame: pd.DataFrame, values: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per league: its matches and the columns of the table, highest shrunk comeback rate first."""
    grouped = frame.groupby(LEAGUE)
    table = pd.DataFrame({"league": grouped["league"].first(), "matches": grouped.size()})
    for label, column, header in TABLE_COLUMNS:
        table[header] = values[label][column]
    return table.sort_values(["shrunk", "league"], ascending=[False, True])


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    frame = card.card_frame(matches)
    frame[LEAGUE] = matches[LEAGUE]
    frame["league"] = matches["s1_league_name"]
    frame["stage"] = matches["s1_stage"]
    print(f"{frame[LEAGUE].nunique()} leagues; each test: Cochran's Q across them")
    rows, values = [], {}
    for row_of_card in card.CARD:
        label = row_of_card[2]
        row, values[label] = units.summary_row(frame, LEAGUE, row_of_card, luck=label in MARKETS)
        rows.append(row)
    report.show("One test across the leagues for each quantity of the card", pd.DataFrame(rows))
    report.show(
        "League-seasons inside their league (one test for all leagues)", season_tests(frame)
    )
    stages = frame[frame["stage"].isin(STAGES)]
    print(f"\nleagues that keep two stages: {stages[LEAGUE].nunique()}")
    report.show("Their two stages", stage_table(stages))
    report.show("Leagues, by the shrunk comeback rate", league_table(frame, values))


if __name__ == "__main__":
    main()
