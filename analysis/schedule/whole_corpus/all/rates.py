"""Comeback and 7+ rates on the whole corpus, all matches pooled: the card of the ALL level.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/RATES.md`. Prints the card of
`notes/ANALYSIS/CLAUDE.md` §2 for all matches and per season cohort: the comeback rate and
its two links, split by home and away team, the 7+ rate and the goals in each half. Then
the completion by half-time deficit, and how many matches end with each goal total. The
count against the odds is in `ALL/ODDS_YARDSTICK.md`.

Run: `uv run python -m analysis.schedule.whole_corpus.all.rates`
"""

import pandas as pd

from analysis import corpus, report, stats

# (numerator column, denominator column, label): each row is sum(numerator) / sum(denominator),
# so against `one` a rate or a mean per match, and against a half-time state a completion.
CARD = (
    ("is_comeback", "one", "comeback"),
    ("ht_decisive", "one", "link 1: a team is behind at half-time"),
    ("is_comeback", "ht_decisive", "link 2: the team behind wins"),
    ("is_comeback_home", "one", "home comeback"),
    ("home_behind", "one", "home team behind at half-time"),
    ("is_comeback_home", "home_behind", "home team behind wins"),
    ("is_comeback_away", "one", "away comeback"),
    ("away_behind", "one", "away team behind at half-time"),
    ("is_comeback_away", "away_behind", "away team behind wins"),
    ("seven", "one", "7+ goals"),
    ("goals_1h", "one", "goals in the first half"),
    ("goals_2h", "one", "goals in the second half"),
    ("goals", "one", "goals per match"),
)
# (smallest deficit, largest deficit, label) of the half-time deficit bands.
DEFICITS = ((1, 1, "1"), (2, 2, "2"), (3, 99, "3 or more"))
MANY_GOALS = 10  # totals of this many goals or more share one row


def card_frame(matches: pd.DataFrame) -> pd.DataFrame:
    """One row per match: the outcomes of the card as floats, the league-season and cohort."""
    margin = matches["s1_ht_home_goals"] - matches["s1_ht_away_goals"]
    frame = pd.DataFrame(
        {
            "is_comeback": matches["s2_is_comeback"],
            "is_comeback_home": matches["s2_is_comeback_home"],
            "is_comeback_away": matches["s2_is_comeback_away"],
            "ht_decisive": matches["s2_ht_decisive"],
            "home_behind": margin < 0,
            "away_behind": margin > 0,
            "seven": matches["s2_total_goals"] >= 7,
            "goals": matches["s2_total_goals"],
            "goals_1h": matches["s2_goals_1h"],
            "goals_2h": matches["s2_goals_2h"],
            "ht_deficit": margin.abs(),
        },
        index=matches.index,
    ).astype(float)
    frame["one"] = 1.0
    frame["cluster"] = matches["s1_league_id"].astype(str) + " " + matches["s1_season"]
    frame["season_cohort"] = matches["season_cohort"]
    return frame


def card(frame: pd.DataFrame) -> pd.DataFrame:
    """Each row of the card: its two sums, their ratio, and the interval over league-seasons."""
    rows = []
    for numerator, denominator, label in CARD:
        ratio = stats.observed_expected(frame, numerator, denominator)
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


def by_deficit(frame: pd.DataFrame) -> pd.DataFrame:
    """Link 2 by the half-time deficit: how often the team behind wins. A band with no
    half-time in it gets no row."""
    rows = []
    for smallest, largest, label in DEFICITS:
        part = frame[frame["ht_deficit"].between(smallest, largest)]
        if part.empty:
            continue
        ratio = stats.observed_expected(part, "is_comeback", "one")
        rows.append(
            {
                "deficit": label,
                "half-times": ratio["n"],
                "share of matches": ratio["n"] / len(frame),
                "comebacks": ratio["observed"],
                "completion": ratio["oe"],
                "low": ratio["low"],
                "high": ratio["high"],
            }
        )
    return pd.DataFrame(rows)


def goal_totals(frame: pd.DataFrame) -> pd.DataFrame:
    """How many matches end with each goal total; totals of MANY_GOALS or more share a row."""
    totals = frame["goals"].clip(upper=MANY_GOALS).astype(int)
    table = totals.value_counts().sort_index().rename_axis("goals").reset_index(name="matches")
    table["share"] = table["matches"] / len(frame)
    table["goals"] = [f"{g}+" if g == MANY_GOALS else str(g) for g in table["goals"]]
    return table


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    frame = card_frame(matches)
    report.show("The card, all matches", card(frame))
    for cohort, group in frame.groupby("season_cohort"):
        report.show(f"The card, season cohort {cohort} ({len(group):,} matches)", card(group))
    report.show("Link 2 by half-time deficit", by_deficit(frame))
    report.show("Goal totals", goal_totals(frame))


if __name__ == "__main__":
    main()
