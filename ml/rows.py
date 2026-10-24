"""The rows of the ML test: one per side of a priced match, with the fields of models A and B.

A row asks: is this team (T) behind at half-time, and does it win (`comes_back`)? Its fields
belong to T, to its opponent (O) or to the match. Each one is known before kickoff: they come
from the fields of `notes/FIELDS/` with the timing `before` and the role `input`. Model A
reads the odds fields only (`ODDS`); model B reads them and every field of `schedule_fields`.
The team ids are not fields (`notes/WORKING/PLAN_2026-10-19_ML_TEST.md` §2, decision 6).
"""

import numpy as np
import pandas as pd

from analysis import card
from analysis.methods import shin
from domain.clock import BERLIN

TARGET = "comes_back"
SIDES = (("home", "away"), ("away", "home"))
WHO = (("T", 0), ("O", 1))  # the team of the row, and its opponent: the index into a side pair
HALVES = ("ft", "ht")
VENUES = ("total", "home", "away")
RATE_STATS = ("won", "drawn", "lost", "goals_for", "goal_diff", "points")
RESULTS = ("w", "d", "l")
STAKES = ("pre_matches_left", "pre_pts_to_above", "pre_pts_to_below", "rank_change_since_open")
ROUND_SO_FAR = (
    "s3_match_index_in_round",
    "s3_round_pre_finished",
    "s3_round_pre_comebacks",
    "s3_round_pre_seven_plus",
    "s3_round_pre_rare_events",
    "s3_round_pre_btts",
    "s3_round_pre_avg_goals",
    "s3_round_pre_avg_ou_line",
)
# The fields of model A: the odds, as the yardstick reads them, and the venue of T.
ODDS = (
    "venue_home",
    "p_T",
    "p_draw",
    "p_O",
    "lam_T",
    "lam_O",
    "ou_line",
    "p_over",
    "ah_line_T",
    "p_ah_T",
    "margin_1x2",
    "m_cb_T",
    "m_cb_O",
    "m_behind_T",
)
LEAGUE = "league_id"  # a categorical field of model B


def odds_fields(
    matches_df: pd.DataFrame, yardstick_df: pd.DataFrame, side: str, other: str
) -> pd.DataFrame:
    """The odds fields of one side's rows: the Shin chances, the yardstick's rates and chances,
    the O/U and AH markets from T's view, and the 1X2 margin. `yardstick_df` is the
    yardstick's frame of the same matches (`analysis/methods/yardstick.py:frame`)."""
    sign = 1.0 if side == "home" else -1.0
    ah_home = matches_df["s2_implied_ah_home"]

    return pd.DataFrame(
        {
            "venue_home": 1.0 if side == "home" else 0.0,
            "p_T": yardstick_df[f"shin_p_{side}"],
            "p_draw": yardstick_df["shin_p_draw"],
            "p_O": yardstick_df[f"shin_p_{other}"],
            "lam_T": yardstick_df[f"lam_{side}"],
            "lam_O": yardstick_df[f"lam_{other}"],
            "ou_line": matches_df["s1_odds_ou_open_line"],
            "p_over": matches_df["s2_implied_over"],
            "ah_line_T": sign * matches_df["s1_odds_ah_open_line"],
            "p_ah_T": ah_home if side == "home" else 1.0 - ah_home,
            "margin_1x2": (1.0 / matches_df[shin.ODDS]).sum(axis=1),
            "m_cb_T": yardstick_df[f"m_cb_{side}"],
            "m_cb_O": yardstick_df[f"m_cb_{other}"],
            "m_behind_T": yardstick_df[f"m_{side}_behind"],
        },
        index=yardstick_df.index,
    ).astype(float)


def per_game(count: "pd.Series[float]", played: "pd.Series[float]") -> "pd.Series[float]":
    """A count per match played; empty before the first match."""
    return count.astype(float) / played.where(played > 0)


def table_fields(matches_df: pd.DataFrame, side: str, who: str) -> dict[str, "pd.Series[float]"]:
    """One team's table before kickoff (S3.03), as per-match rates, with its rank and its
    matches played; then its second-half goals and goal difference per match (FT minus HT)."""
    out: dict[str, pd.Series[float]] = {}
    for venue in VENUES:
        played = matches_df[f"s3_{side}_pre_ft_{venue}_played"].astype(float)
        for half in HALVES:
            base = f"s3_{side}_pre_{half}_{venue}"
            out[f"{who}_{half}_{venue}_rank"] = matches_df[f"{base}_rank"].astype(float)
            out[f"{who}_{half}_{venue}_played"] = matches_df[f"{base}_played"].astype(float)
            for stat in RATE_STATS:
                out[f"{who}_{half}_{venue}_{stat}_pg"] = per_game(
                    matches_df[f"{base}_{stat}"], played
                )

        for stat in ("goals_for", "goal_diff"):
            second_half = (
                matches_df[f"s3_{side}_pre_ft_{venue}_{stat}"]
                - matches_df[f"s3_{side}_pre_ht_{venue}_{stat}"]
            )
            out[f"{who}_2h_{venue}_{stat}_pg"] = per_game(second_half, played)

    return out


def record_fields(matches_df: pd.DataFrame, side: str, who: str) -> dict[str, "pd.Series[float]"]:
    """One team's HT/FT record before kickoff (S3.08), as shares of its matches played, and its
    stakes (S3.11 to S3.13)."""
    out: dict[str, pd.Series[float]] = {}
    for venue in VENUES:
        played = matches_df[f"s3_{side}_pre_ft_{venue}_played"].astype(float)
        for ht in RESULTS:
            for ft in RESULTS:
                count = matches_df[f"s3_{side}_pre_htft_{venue}_{ht}_{ft}"]
                out[f"{who}_htft_{venue}_{ht}_{ft}_pg"] = per_game(count, played)

    for stake in STAKES:
        out[f"{who}_{stake}"] = matches_df[f"s3_{side}_{stake}"].astype(float)

    return out


def match_fields(matches_df: pd.DataFrame) -> pd.DataFrame:
    """The fields of the match: the round so far (S3.01, S3.14 to S3.20), the gap between the two
    ranks (S3.04), the round (S1.05), the kickoff in Berlin time (S1.07) and the league (S1.02)."""
    kickoff = pd.to_datetime(matches_df["s1_date"], utc=True).dt.tz_convert(BERLIN)

    match_fields_df = matches_df[list(ROUND_SO_FAR)].astype(float)
    match_fields_df["s3_pre_rank_gap"] = matches_df["s3_pre_rank_gap"].astype(float)
    match_fields_df["round"] = matches_df["s1_round"].astype(float)

    match_fields_df["weekday"] = kickoff.dt.weekday.astype(float)
    match_fields_df["hour"] = (kickoff.dt.hour + kickoff.dt.minute / 60.0).astype(float)
    match_fields_df["month"] = kickoff.dt.month.astype(float)
    match_fields_df[LEAGUE] = pd.Categorical(matches_df["s1_league_id"])

    return match_fields_df


def side_fields(matches_df: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """Every non-odds field of one side's rows: T's and O's tables, records and stakes, and the
    match's fields."""
    teams: dict[str, pd.Series[float]] = {}
    for who, index in WHO:
        team = (side, other)[index]
        teams |= table_fields(matches_df, team, who)
        teams |= record_fields(matches_df, team, who)

    return pd.concat(
        [pd.DataFrame(teams, index=matches_df.index), match_fields(matches_df)], axis=1
    )


def side_rows(
    matches_df: pd.DataFrame, yardstick_df: pd.DataFrame
) -> tuple[pd.DataFrame, list[str]]:
    """Two rows per priced match, home side first (`card.team_yardstick_rows`), with the
    fields of models A and B; and the fields of model B, the odds first. `yardstick_df` is
    the yardstick's frame of the matches."""
    priced_df = matches_df.loc[yardstick_df.index]
    team_rows_df = card.team_yardstick_rows(priced_df, yardstick_df)

    model_fields_df = pd.concat(
        [
            pd.concat(
                [
                    odds_fields(priced_df, yardstick_df, side, other),
                    side_fields(priced_df, side, other),
                ],
                axis=1,
            )
            for side, other in SIDES
        ],
        ignore_index=True,
    )

    return team_rows_df.join(model_fields_df), list(model_fields_df.columns)


def summary(side_rows_df: pd.DataFrame, fields: list[str]) -> dict[str, float]:
    """How many rows and comebacks, how many fields each model reads, and the share of the
    values of model B that are empty (mostly before a team's first match of the stage)."""
    return {
        "rows": float(len(side_rows_df)),
        "comebacks": float(side_rows_df[TARGET].sum()),
        "rate": float(side_rows_df[TARGET].mean()),
        "fields A": float(len(ODDS)),
        "fields B": float(len(fields)),
        "empty share of B": float(np.mean(side_rows_df[fields].isna().to_numpy())),
    }
