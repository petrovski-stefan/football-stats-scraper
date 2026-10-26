"""The odds yardstick per league: one heterogeneity test per quantity, and shrunk league values.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/ODDS_YARDSTICK.md`. With the yardstick of
`ALL/ODDS_YARDSTICK.md`, prints one test across the leagues for each quantity: the raw goal,
comeback and 7+ rates, the same observed against expected (O/E), the two links, and the
first-half share of the goals. Then the comeback O/E again, with each league's own share;
then the league tables, in the order of the league names. No league is tested on its own:
per-league testing is Dead in `notes/WORKING/STATE.md`.

Run: `uv run python -m analysis.schedule.whole_corpus.per_league.odds_yardstick`
"""

import pandas as pd

from analysis import corpus, report, units
from analysis.methods import yardstick

LEAGUE = "s1_league_id"
# (observed column, expected column, label, kind). A league's value is sum(observed) /
# sum(expected): against `one` a raw rate, against `goals` the first-half share, else an O/E.
# The kind gives one match's variance if every league had the pooled value
# (`units.match_variance`).
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


def with_own_share(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """The frame with the chances that use the share made again from each league's own share."""

    sums_df = yardstick_df.groupby(LEAGUE)[["goals_1h", "goals"]].sum()
    share = yardstick_df[LEAGUE].map(sums_df["goals_1h"] / sums_df["goals"]).to_numpy(dtype=float)

    lam_home, lam_away = yardstick_df["lam_home"].to_numpy(), yardstick_df["lam_away"].to_numpy()
    with_own_share_df = yardstick_df.copy()
    implied_df = yardstick.implied(lam_home, lam_away, share)
    with_own_share_df[implied_df.columns] = implied_df.to_numpy()
    with_own_share_df["m_completion"] = yardstick.completion_given_ht(
        lam_home, lam_away, share, yardstick_df["ht_margin"].to_numpy()
    )

    return with_own_share_df


def league_table(
    yardstick_df: pd.DataFrame,
    values: dict[str, pd.DataFrame],
    columns: tuple[tuple[str, str, str], ...],
) -> pd.DataFrame:
    """Per league, in the order of the names: its matches and each column asked for."""

    grouped = yardstick_df.groupby(LEAGUE)
    league_table_df = pd.DataFrame(
        {"league": grouped["s1_league_name"].first(), "matches": grouped.size()}
    )
    for label, column, header in columns:
        league_table_df[header] = values[label][column]

    return league_table_df.sort_values("league")


def main() -> None:
    """Entry point: print the odds yardstick per league."""

    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    share = yardstick.first_half_share(yardstick.priced(matches_df))
    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid(), share=share).assign(one=1.0)
    print(
        f"Priced: {len(yardstick_df):,} matches in {yardstick_df[LEAGUE].nunique()} leagues; "
        f"first-half share {share:.4f}"
    )

    rows, unit_values = [], {}
    for quantity in QUANTITIES:
        row, unit_values[quantity[2]] = units.summary_row(
            yardstick_df, LEAGUE, quantity, has_luck_line=quantity[2] in LUCK
        )
        rows.append(row)

    print(f"Each test: Cochran's Q on {len(unit_values['goals O/E']) - 1} df")
    report.show("One test across the leagues for each quantity", pd.DataFrame(rows))

    comeback = next(q for q in QUANTITIES if q[2] == "comeback O/E")
    report.show(
        "Comeback O/E with each league's own first-half share",
        pd.DataFrame(
            [
                units.summary_row(
                    with_own_share(yardstick_df), LEAGUE, comeback, has_luck_line=True
                )[0]
            ]
        ),
    )

    report.show(
        "Leagues: goals, comebacks, 7+ goals and the share",
        league_table(yardstick_df, unit_values, MAIN_COLUMNS),
    )
    report.show("Leagues: the two links", league_table(yardstick_df, unit_values, LINK_COLUMNS))


if __name__ == "__main__":
    main()
