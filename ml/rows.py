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


def odds_fields(matches: pd.DataFrame, frame: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The odds fields of one side's rows: the Shin chances, the yardstick's rates and chances,
    the O/U and AH markets from T's view, and the 1X2 margin. `frame` is the yardstick's frame
    of the same matches (`analysis/methods/yardstick.py:frame`)."""
    sign = 1.0 if side == "home" else -1.0
    ah_home = matches["s2_implied_ah_home"]
    return pd.DataFrame(
        {
            "venue_home": 1.0 if side == "home" else 0.0,
            "p_T": frame[f"shin_p_{side}"],
            "p_draw": frame["shin_p_draw"],
            "p_O": frame[f"shin_p_{other}"],
            "lam_T": frame[f"lam_{side}"],
            "lam_O": frame[f"lam_{other}"],
            "ou_line": matches["s1_odds_ou_open_line"],
            "p_over": matches["s2_implied_over"],
            "ah_line_T": sign * matches["s1_odds_ah_open_line"],
            "p_ah_T": ah_home if side == "home" else 1.0 - ah_home,
            "margin_1x2": (1.0 / matches[shin.ODDS]).sum(axis=1),
            "m_cb_T": frame[f"m_cb_{side}"],
            "m_cb_O": frame[f"m_cb_{other}"],
            "m_behind_T": frame[f"m_{side}_behind"],
        },
        index=frame.index,
    ).astype(float)


def per_game(count: "pd.Series[float]", played: "pd.Series[float]") -> "pd.Series[float]":
    """A count per match played; empty before the first match."""
    return count.astype(float) / played.where(played > 0)


def table_fields(matches: pd.DataFrame, side: str, who: str) -> dict[str, "pd.Series[float]"]:
    """One team's table before kickoff (S3.03), as per-match rates, with its rank and its
    matches played; then its second-half goals and goal difference per match (FT minus HT)."""
    out: dict[str, pd.Series[float]] = {}
    for venue in VENUES:
        played = matches[f"s3_{side}_pre_ft_{venue}_played"].astype(float)
        for half in HALVES:
            base = f"s3_{side}_pre_{half}_{venue}"
            out[f"{who}_{half}_{venue}_rank"] = matches[f"{base}_rank"].astype(float)
            out[f"{who}_{half}_{venue}_played"] = matches[f"{base}_played"].astype(float)
            for stat in RATE_STATS:
                out[f"{who}_{half}_{venue}_{stat}_pg"] = per_game(matches[f"{base}_{stat}"], played)
        for stat in ("goals_for", "goal_diff"):
            second_half = (
                matches[f"s3_{side}_pre_ft_{venue}_{stat}"]
                - matches[f"s3_{side}_pre_ht_{venue}_{stat}"]
            )
            out[f"{who}_2h_{venue}_{stat}_pg"] = per_game(second_half, played)
    return out


def record_fields(matches: pd.DataFrame, side: str, who: str) -> dict[str, "pd.Series[float]"]:
    """One team's HT/FT record before kickoff (S3.08), as shares of its matches played, and its
    stakes (S3.11 to S3.13)."""
    out: dict[str, pd.Series[float]] = {}
    for venue in VENUES:
        played = matches[f"s3_{side}_pre_ft_{venue}_played"].astype(float)
        for ht in RESULTS:
            for ft in RESULTS:
                count = matches[f"s3_{side}_pre_htft_{venue}_{ht}_{ft}"]
                out[f"{who}_htft_{venue}_{ht}_{ft}_pg"] = per_game(count, played)
    for stake in STAKES:
        out[f"{who}_{stake}"] = matches[f"s3_{side}_{stake}"].astype(float)
    return out


def match_fields(matches: pd.DataFrame) -> pd.DataFrame:
    """The fields of the match: the round so far (S3.01, S3.14 to S3.20), the gap between the two
    ranks (S3.04), the round (S1.05), the kickoff in Berlin time (S1.07) and the league (S1.02)."""
    kickoff = pd.to_datetime(matches["s1_date"], utc=True).dt.tz_convert("Europe/Berlin")
    out = matches[list(ROUND_SO_FAR)].astype(float)
    out["s3_pre_rank_gap"] = matches["s3_pre_rank_gap"].astype(float)
    out["round"] = matches["s1_round"].astype(float)
    out["weekday"] = kickoff.dt.weekday.astype(float)
    out["hour"] = (kickoff.dt.hour + kickoff.dt.minute / 60.0).astype(float)
    out["month"] = kickoff.dt.month.astype(float)
    out[LEAGUE] = pd.Categorical(matches["s1_league_id"])
    return out


def side_fields(matches: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """Every non-odds field of one side's rows: T's and O's tables, records and stakes, and the
    match's fields."""
    teams: dict[str, pd.Series[float]] = {}
    for who, index in WHO:
        team = (side, other)[index]
        teams |= table_fields(matches, team, who)
        teams |= record_fields(matches, team, who)
    return pd.concat([pd.DataFrame(teams, index=matches.index), match_fields(matches)], axis=1)


def side_rows(matches: pd.DataFrame, frame: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """Two rows per priced match, home side first (`card.team_yardstick_rows`), with the
    fields of models A and B; and the fields of model B, the odds first. `frame` is the
    yardstick's frame of the matches."""
    priced = matches.loc[frame.index]
    rows = card.team_yardstick_rows(priced, frame)
    fields = pd.concat(
        [
            pd.concat(
                [odds_fields(priced, frame, side, other), side_fields(priced, side, other)],
                axis=1,
            )
            for side, other in SIDES
        ],
        ignore_index=True,
    )
    return rows.join(fields), list(fields.columns)


def summary(rows: pd.DataFrame, fields: list[str]) -> dict[str, float]:
    """How many rows and comebacks, how many fields each model reads, and the share of the
    values of model B that are empty (mostly before a team's first match of the stage)."""
    return {
        "rows": float(len(rows)),
        "comebacks": float(rows[TARGET].sum()),
        "rate": float(rows[TARGET].mean()),
        "fields A": float(len(ODDS)),
        "fields B": float(len(fields)),
        "empty share of B": float(np.mean(rows[fields].isna().to_numpy())),
    }
