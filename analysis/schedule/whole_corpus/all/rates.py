"""Comeback and 7+ rates on the whole corpus, all matches pooled: the card of the ALL level.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/RATES.md`. Prints the card of
`notes/ANALYSIS/CLAUDE.md` §2 (`analysis/card.py`) for all matches and per season cohort: the
comeback rate and its two links, split by home and away team, the 7+ rate and the goals in
each half. Then the completion by half-time deficit, and how many matches end with each goal
total. The count against the odds is in `ALL/ODDS_YARDSTICK.md`.

Run: `uv run python -m analysis.schedule.whole_corpus.all.rates`
"""

import pandas as pd

from analysis import card, corpus, report, stats

# (smallest deficit, largest deficit, label) of the half-time deficit bands.
DEFICITS = ((1, 1, "1"), (2, 2, "2"), (3, 99, "3 or more"))
MANY_GOALS = 10  # totals of this many goals or more share one row


def card_table(card_df: pd.DataFrame) -> pd.DataFrame:
    """Each row of the card: its two sums, their ratio, and the interval over league-seasons."""

    rows = []
    for numerator, denominator, label, _ in card.CARD:
        ratio = stats.observed_expected(card_df, numerator, denominator)
        rows.append(
            {
                "quantity": label,
                "count": ratio["observed"],
                "of": ratio["expected"],
                "value": ratio["oe"],
                "low": ratio["low"],
                "high": ratio["high"],
            }
        )

    return pd.DataFrame(rows)


def by_deficit(card_df: pd.DataFrame) -> pd.DataFrame:
    """Link 2 by the half-time deficit: how often the team behind wins. A band with no
    half-time in it gets no row."""

    rows = []
    for smallest, largest, label in DEFICITS:
        deficit_df = card_df[card_df["ht_deficit"].between(smallest, largest)]
        if deficit_df.empty:
            continue

        ratio = stats.observed_expected(deficit_df, "is_comeback", "one")
        rows.append(
            {
                "deficit": label,
                "half-times": ratio["n"],
                "share of matches": ratio["n"] / len(card_df),
                "comebacks": ratio["observed"],
                "completion": ratio["oe"],
                "low": ratio["low"],
                "high": ratio["high"],
            }
        )

    return pd.DataFrame(rows)


def goal_totals(card_df: pd.DataFrame) -> pd.DataFrame:
    """How many matches end with each goal total; totals of MANY_GOALS or more share a row."""

    totals = card_df["goals"].clip(upper=MANY_GOALS).astype(int)
    goal_totals_df = (
        totals.value_counts().sort_index().rename_axis("goals").reset_index(name="matches")
    )
    goal_totals_df["share"] = goal_totals_df["matches"] / len(card_df)
    goal_totals_df["goals"] = [
        f"{total}+" if total == MANY_GOALS else str(total) for total in goal_totals_df["goals"]
    ]

    return goal_totals_df


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    card_df = card.card_frame(matches_df)

    report.show("The card, all matches", card_table(card_df))
    for cohort, cohort_df in card_df.groupby("season_cohort"):
        report.show(
            f"The card, season cohort {cohort} ({len(cohort_df):,} matches)", card_table(cohort_df)
        )
    report.show("Link 2 by half-time deficit", by_deficit(card_df))
    report.show("Goal totals", goal_totals(card_df))


if __name__ == "__main__":
    main()
