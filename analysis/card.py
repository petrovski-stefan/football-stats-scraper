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

from domain.stats import SEVEN_PLUS_GOALS

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


def card_frame(matches_df: pd.DataFrame) -> pd.DataFrame:
    """One row per match: the outcomes of the card as floats, the league-season and cohort."""

    margin = matches_df["s1_ht_home_goals"] - matches_df["s1_ht_away_goals"]

    card_df = pd.DataFrame(
        {
            "is_comeback": matches_df["s2_is_comeback"],
            "is_comeback_home": matches_df["s2_is_comeback_home"],
            "is_comeback_away": matches_df["s2_is_comeback_away"],
            "ht_decisive": matches_df["s2_ht_decisive"],
            "home_behind": margin < 0,
            "away_behind": margin > 0,
            "seven": matches_df["s2_total_goals"] >= SEVEN_PLUS_GOALS,
            "goals": matches_df["s2_total_goals"],
            "goals_1h": matches_df["s2_goals_1h"],
            "goals_2h": matches_df["s2_goals_2h"],
            "ht_deficit": margin.abs(),
        },
        index=matches_df.index,
    ).astype(float)

    card_df["one"] = 1.0
    card_df["cluster"] = matches_df["s1_league_id"].astype(str) + " " + matches_df["s1_season"]
    card_df["season_cohort"] = matches_df["season_cohort"]

    return card_df


# The columns of `team_rows` that name the unit (a team in one league) and its league.
TEAM_UNIT = "unit"
TEAM_LEAGUE = "league"


def team_rows(
    matches_df: pd.DataFrame,
    extra: "dict[str, tuple[pd.Series[Any], pd.Series[Any]]] | None" = None,
) -> pd.DataFrame:
    """Two rows per match, one for each team: its venue, its goals, its unit (the team in its
    league), the league-season, the cohort and its two roles: it comes back (behind at
    half-time, then wins) or it loses a lead (ahead at half-time, then loses).

    Args:
        extra: more columns, each as (home team values, away team values) on `matches_df`'s index.
    """

    sides = []
    for index, (side, other) in enumerate((("home", "away"), ("away", "home"))):
        ht_for, ht_against = matches_df[f"s1_ht_{side}_goals"], matches_df[f"s1_ht_{other}_goals"]
        ft_for, ft_against = matches_df[f"s1_ft_{side}_goals"], matches_df[f"s1_ft_{other}_goals"]
        behind, ahead = ht_for < ht_against, ht_for > ht_against

        side_rows_df = pd.DataFrame(
            {
                "behind": behind,
                "ahead": ahead,
                "comes_back": behind & (ft_for > ft_against),
                "loses_lead": ahead & (ft_for < ft_against),
                "goals_for": ft_for,
                "goals_against": ft_against,
            },
            index=matches_df.index,
        ).astype(float)

        side_rows_df["home"] = 1.0 if side == "home" else 0.0
        side_rows_df["team"] = matches_df[f"s1_{side}_team_id"]
        side_rows_df["team_name"] = matches_df[f"s1_{side}_team_name"]
        side_rows_df[TEAM_LEAGUE] = matches_df["s1_league_id"]
        side_rows_df["league_name"] = matches_df["s1_league_name"]
        side_rows_df["cluster"] = (
            matches_df["s1_league_id"].astype(str) + " " + matches_df["s1_season"]
        )
        side_rows_df["season_cohort"] = matches_df["season_cohort"]

        for name, side_values in (extra or {}).items():
            side_rows_df[name] = side_values[index]

        sides.append(side_rows_df)

    team_rows_df = pd.concat(sides, ignore_index=True)
    team_rows_df["away"] = 1.0 - team_rows_df["home"]
    team_rows_df["one"] = 1.0

    for role in ("comes_back", "loses_lead"):
        for venue in ("home", "away"):
            team_rows_df[f"{role}_{venue}"] = team_rows_df[role] * team_rows_df[venue]

    team_rows_df[TEAM_UNIT] = (
        team_rows_df["team"].astype(str) + " " + team_rows_df[TEAM_LEAGUE].astype(str)
    )

    return team_rows_df


def team_yardstick_rows(matches_df: pd.DataFrame, yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """The team rows of the priced matches (`team_rows`), with the chances of the odds
    yardstick for each team; `yardstick_df` is `analysis/methods/yardstick.py:frame` of the same
    matches."""

    extra = {
        "m_comes_back": (yardstick_df["m_cb_home"], yardstick_df["m_cb_away"]),
        "m_loses_lead": (yardstick_df["m_cb_away"], yardstick_df["m_cb_home"]),
        "m_behind": (yardstick_df["m_home_behind"], yardstick_df["m_away_behind"]),
        "m_ahead": (yardstick_df["m_away_behind"], yardstick_df["m_home_behind"]),
        "m_completion": (yardstick_df["m_completion"], yardstick_df["m_completion"]),
        "m_goals_for": (yardstick_df["lam_home"], yardstick_df["lam_away"]),
        "m_goals_against": (yardstick_df["lam_away"], yardstick_df["lam_home"]),
        "win_chance": (yardstick_df["shin_p_home"], yardstick_df["shin_p_away"]),
    }

    team_rows_df = team_rows(matches_df.loc[yardstick_df.index], extra)

    # The yardstick's completion is the chance of the team behind, from the half-time score.
    team_rows_df["m_wins_from_behind"] = team_rows_df["behind"] * team_rows_df["m_completion"]
    team_rows_df["m_loses_from_ahead"] = team_rows_df["ahead"] * team_rows_df["m_completion"]

    for role in ("comes_back", "loses_lead"):
        for venue in ("home", "away"):
            team_rows_df[f"m_{role}_{venue}"] = team_rows_df[f"m_{role}"] * team_rows_df[venue]

    return team_rows_df


def team_line(team_rows_df: pd.DataFrame) -> str:
    """How many team units, leagues, team-matches and teams in two leagues the rows hold."""

    in_two = int((team_rows_df.groupby("team")[TEAM_LEAGUE].nunique() > 1).sum())

    return (
        f"{team_rows_df[TEAM_UNIT].nunique():,} team units (a team in one league) in "
        f"{team_rows_df[TEAM_LEAGUE].nunique()} leagues; {len(team_rows_df):,} team-matches; "
        f"{in_two} teams in two leagues or more"
    )


def top_teams(
    team_rows_df: pd.DataFrame,
    unit_values_df: pd.DataFrame,
    top: int,
    names: tuple[str, str, str] = ("events", "of", "rate"),
) -> pd.DataFrame:
    """The teams most above their league after shrinkage, then by the raw value, with the
    comebacks in all their matches. `unit_values_df` holds the team values of
    `analysis/units.py:within_tested`; `names` label their observed, expected and value."""

    team_names_df = team_rows_df.groupby(TEAM_UNIT)[["team_name", "league_name"]].first()
    in_matches = team_rows_df.groupby(TEAM_UNIT)[["comes_back", "loses_lead"]].sum().sum(axis=1)

    top_teams_df = team_names_df.join(
        unit_values_df[["observed", "expected", "value", "owner_mean", "shrunk"]]
    )
    top_teams_df["shrunk - league"] = top_teams_df["shrunk"] - top_teams_df["owner_mean"]
    top_teams_df["comebacks in its matches"] = in_matches

    observed_label, expected_label, value_label = names
    top_teams_df = top_teams_df.rename(
        columns={
            "observed": observed_label,
            "expected": expected_label,
            "value": value_label,
            "owner_mean": "league",
        }
    )

    order = ["shrunk - league", value_label, "team_name"]

    return top_teams_df.sort_values(order, ascending=[False, False, True]).head(top)
