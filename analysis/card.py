"""The card of each level (`notes/ANALYSIS/CLAUDE.md` §2), match by match.

Each row of `CARD` (the `ALL/` and `PER_LEAGUE/` levels) is sum(numerator) / sum(denominator):
against `one` a rate or a mean per match, against a half-time state a completion. The kind is
the variance model of a unit's value (`analysis/units.py`): the 0/1 outcomes are events, the
goals are counts. `ODDS_CARD` names the yardstick's column for its main rows. The `PER_TEAM/`
level reads `team_rows`: two rows per match, one per team, with the yardstick's chances for
each team in `team_yardstick_rows`.
"""

from typing import Any

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

# The main rows of the card with the column of the odds yardstick (`analysis/methods/
# yardstick.py`) that each is read against, on the yardstick's frame:
# (observed column, denominator column, yardstick column, label, kind).
ODDS_CARD = (
    ("is_comeback", "one", "m_cb", "comeback", "event"),
    ("ht_decisive", "one", "m_ht_decisive", "link 1: a team is behind at half-time", "event"),
    ("is_comeback", "ht_decisive", "m_completion", "link 2: the team behind wins", "event"),
    ("seven", "one", "m_seven", "7+ goals", "event"),
    ("goals", "one", "m_goals", "goals per match", "count"),
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


# The columns of `team_rows` that name the unit (a team in one league) and its league.
TEAM_UNIT = "unit"
TEAM_LEAGUE = "league"


def team_rows(
    matches: pd.DataFrame,
    extra: "dict[str, tuple[pd.Series[Any], pd.Series[Any]]] | None" = None,
) -> pd.DataFrame:
    """Two rows per match, one for each team: its venue, its two roles and its goals, its unit
    (the team in its league), the league-season and the cohort.

    The roles: the team comes back (behind at half-time, then wins), and the team loses a lead
    (ahead at half-time, then loses). `extra` adds columns, each given as (the value of the
    home team, the value of the away team) on the index of `matches`.
    """
    sides = []
    for index, (side, other) in enumerate((("home", "away"), ("away", "home"))):
        ht_for, ht_against = matches[f"s1_ht_{side}_goals"], matches[f"s1_ht_{other}_goals"]
        ft_for, ft_against = matches[f"s1_ft_{side}_goals"], matches[f"s1_ft_{other}_goals"]
        behind, ahead = ht_for < ht_against, ht_for > ht_against
        rows = pd.DataFrame(
            {
                "behind": behind,
                "ahead": ahead,
                "comes_back": behind & (ft_for > ft_against),
                "loses_lead": ahead & (ft_for < ft_against),
                "goals_for": ft_for,
                "goals_against": ft_against,
            },
            index=matches.index,
        ).astype(float)
        rows["home"] = 1.0 if side == "home" else 0.0
        rows["team"] = matches[f"s1_{side}_team_id"]
        rows["team_name"] = matches[f"s1_{side}_team_name"]
        rows[TEAM_LEAGUE] = matches["s1_league_id"]
        rows["league_name"] = matches["s1_league_name"]
        rows["cluster"] = matches["s1_league_id"].astype(str) + " " + matches["s1_season"]
        rows["season_cohort"] = matches["season_cohort"]
        for name, values in (extra or {}).items():
            rows[name] = values[index]
        sides.append(rows)
    frame = pd.concat(sides, ignore_index=True)
    frame["away"] = 1.0 - frame["home"]
    frame["one"] = 1.0
    for role in ("comes_back", "loses_lead"):
        for venue in ("home", "away"):
            frame[f"{role}_{venue}"] = frame[role] * frame[venue]
    frame[TEAM_UNIT] = frame["team"].astype(str) + " " + frame[TEAM_LEAGUE].astype(str)
    return frame


def team_yardstick_rows(matches: pd.DataFrame, frame: pd.DataFrame) -> pd.DataFrame:
    """The team rows of the priced matches (`team_rows`), with the chances of the odds
    yardstick for each team; `frame` is `analysis/methods/yardstick.py:frame` of the same
    matches."""
    extra = {
        "m_comes_back": (frame["m_cb_home"], frame["m_cb_away"]),
        "m_loses_lead": (frame["m_cb_away"], frame["m_cb_home"]),
        "m_behind": (frame["m_home_behind"], frame["m_away_behind"]),
        "m_ahead": (frame["m_away_behind"], frame["m_home_behind"]),
        "m_completion": (frame["m_completion"], frame["m_completion"]),
        "m_goals_for": (frame["lam_home"], frame["lam_away"]),
        "m_goals_against": (frame["lam_away"], frame["lam_home"]),
        "win_chance": (frame["shin_p_home"], frame["shin_p_away"]),
    }
    rows = team_rows(matches.loc[frame.index], extra)
    # The yardstick's completion is the chance of the team behind, from the half-time score.
    rows["m_wins_from_behind"] = rows["behind"] * rows["m_completion"]
    rows["m_loses_from_ahead"] = rows["ahead"] * rows["m_completion"]
    for role in ("comes_back", "loses_lead"):
        for venue in ("home", "away"):
            rows[f"m_{role}_{venue}"] = rows[f"m_{role}"] * rows[venue]
    return rows


def team_line(rows: pd.DataFrame) -> str:
    """How many team units, leagues, team-matches and teams in two leagues the rows hold."""
    in_two = int((rows.groupby("team")[TEAM_LEAGUE].nunique() > 1).sum())
    return (
        f"{rows[TEAM_UNIT].nunique():,} team units (a team in one league) in "
        f"{rows[TEAM_LEAGUE].nunique()} leagues; {len(rows):,} team-matches; "
        f"{in_two} teams in two leagues or more"
    )


def top_teams(
    rows: pd.DataFrame,
    values: pd.DataFrame,
    top: int,
    names: tuple[str, str, str] = ("events", "of", "rate"),
) -> pd.DataFrame:
    """The teams most above their league after shrinkage, then by the raw value, with the
    comebacks in all their matches. `values` are the team values of
    `analysis/units.py:within_tested`; `names` label their observed, expected and value."""
    team_names = rows.groupby(TEAM_UNIT)[["team_name", "league_name"]].first()
    in_matches = rows.groupby(TEAM_UNIT)[["comes_back", "loses_lead"]].sum().sum(axis=1)
    table = team_names.join(values[["observed", "expected", "value", "owner_mean", "shrunk"]])
    table["shrunk - league"] = table["shrunk"] - table["owner_mean"]
    table["comebacks in its matches"] = in_matches
    observed, expected, value = names
    table = table.rename(
        columns={"observed": observed, "expected": expected, "value": value, "owner_mean": "league"}
    )
    order = ["shrunk - league", value, "team_name"]
    return table.sort_values(order, ascending=[False, False, True]).head(top)
