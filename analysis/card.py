"""The card of the ALL and PER_LEAGUE levels (`notes/ANALYSIS/CLAUDE.md` §2), match by match.

Each row of `CARD` is sum(numerator) / sum(denominator): against `one` a rate or a mean per
match, against a half-time state a completion. The kind is the variance model of a unit's
value (`analysis/units.py`): the 0/1 outcomes are events, the goals are counts.
"""

import pandas as pd

# (numerator column, denominator column, label, kind)
CARD = (
    ("is_comeback", "one", "comeback", "event"),
    ("ht_decisive", "one", "link 1: a team is behind at half-time", "event"),
    ("is_comeback", "ht_decisive", "link 2: the team behind wins", "event"),
    ("is_comeback_home", "one", "home comeback", "event"),
    ("home_behind", "one", "home team behind at half-time", "event"),
    ("is_comeback_home", "home_behind", "home team behind wins", "event"),
    ("is_comeback_away", "one", "away comeback", "event"),
    ("away_behind", "one", "away team behind at half-time", "event"),
    ("is_comeback_away", "away_behind", "away team behind wins", "event"),
    ("seven", "one", "7+ goals", "event"),
    ("goals_1h", "one", "goals in the first half", "count"),
    ("goals_2h", "one", "goals in the second half", "count"),
    ("goals", "one", "goals per match", "count"),
)


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
