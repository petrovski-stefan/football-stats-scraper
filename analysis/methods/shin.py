"""Shin's method on the opening 1X2: margin-free probabilities and the insider share z.

The arithmetic is the `shin` package from PyPI (the user, 2026-10-14), not our own code.
Shin (1993) prices a market against a share z of insiders; removing the margin that way
takes more from long shots than from favourites, by construction. The project's default,
proportional removal, is stage 2's `s2_mkt_p_*` (`features/schedule_row.py`).
"""

import math
from dataclasses import astuple, dataclass

import numpy as np
import pandas as pd
from shin import calculate_implied_probabilities

from analysis import corpus, stats

ODDS = ["s1_odds_1x2_open_home", "s1_odds_1x2_open_draw", "s1_odds_1x2_open_away"]
PROPORTIONAL = ["s2_mkt_p_home", "s2_mkt_p_draw", "s2_mkt_p_away"]
PROBABILITIES = ["shin_p_home", "shin_p_draw", "shin_p_away"]
KEYS = ["match_id", "s1_league_id", "s1_league_name", "s1_season", "season_cohort"]
# Decimal-odds bands of an outcome's price, from favourites to long shots.
PRICE_EDGES = (1.0, 1.3, 1.6, 2.0, 2.6, 3.5, 5.5, 8.0, 13.0, np.inf)


@dataclass(frozen=True)
class ShinResult:
    """Shin's three probabilities and the insider share z of one match, in the order of the
    columns `PROBABILITIES`, then `shin_z`."""

    p_home: float
    p_draw: float
    p_away: float
    z: float


def shin_row(home: float, draw: float, away: float) -> ShinResult:
    """Shin's three probabilities and z for one match; all NaN when a price is missing."""

    odds = [home, draw, away]
    if any(math.isnan(price) for price in odds):
        return ShinResult(p_home=math.nan, p_draw=math.nan, p_away=math.nan, z=math.nan)

    result = calculate_implied_probabilities(odds, full_output=True)
    p_home, p_draw, p_away = result.implied_probabilities

    return ShinResult(p_home=p_home, p_draw=p_draw, p_away=p_away, z=result.z)


def shin_frame(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Shin's probabilities (`PROBABILITIES`) and `shin_z`, one row per match, on the same index."""

    prices = matches_df[ODDS].itertuples(index=False)
    results = [shin_row(*map(float, match_prices)) for match_prices in prices]
    rows = [astuple(result) for result in results]

    return pd.DataFrame(rows, columns=[*PROBABILITIES, "shin_z"], index=matches_df.index)


def scored(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Every match with all three opening 1X2 prices, scored on its full-time result.

    Returns:
        Per match: the keys, the prices, both methods' probabilities, z, the bookmaker's
        margin, each method's log loss and Brier score, Shin's gain over proportional
        (proportional loss minus Shin loss: above 0 means Shin scored better) and `cluster`,
        the league-season.
    """

    priced_df = matches_df.dropna(subset=ODDS)
    scored_df = pd.concat([priced_df[KEYS + ODDS + PROPORTIONAL], shin_frame(priced_df)], axis=1)
    scored_df["margin"] = (1.0 / priced_df[ODDS]).sum(axis=1) - 1.0
    scored_df["outcome"] = corpus.outcome_1x2(priced_df)

    outcomes = scored_df["outcome"].to_numpy()
    for name, columns in (("prop", PROPORTIONAL), ("shin", PROBABILITIES)):
        probabilities = scored_df[columns].to_numpy()
        scored_df[f"ll_{name}"] = stats.log_loss_1x2(probabilities, outcomes)
        scored_df[f"brier_{name}"] = stats.brier_1x2(probabilities, outcomes)

    scored_df["ll_gain"] = scored_df["ll_prop"] - scored_df["ll_shin"]
    scored_df["brier_gain"] = scored_df["brier_prop"] - scored_df["brier_shin"]
    scored_df["cluster"] = priced_df["s1_league_id"].astype(str) + " " + priced_df["s1_season"]

    return scored_df


def outcome_rows(scored_df: pd.DataFrame) -> pd.DataFrame:
    """Three rows per match of `scored`, one per outcome: its side, its price, both
    probabilities, if it happened, and the league-season."""

    codes = (corpus.HOME, corpus.DRAW, corpus.AWAY)
    sides = [
        pd.DataFrame(
            {
                "side": side,
                "price": scored_df[odds].to_numpy(),
                "prop": scored_df[prop].to_numpy(),
                "shin": scored_df[shin_p].to_numpy(),
                "hit": (scored_df["outcome"] == code).to_numpy(),
                "cluster": scored_df["cluster"].to_numpy(),
            }
        )
        for side, code, odds, prop, shin_p in zip(
            ("home", "draw", "away"), codes, ODDS, PROPORTIONAL, PROBABILITIES, strict=True
        )
    ]

    return pd.concat(sides, ignore_index=True)


def sum_error(scored_df: pd.DataFrame) -> float:
    """Largest distance of a match's Shin probabilities from summing to 1 (a convergence check)."""

    return float(np.abs(scored_df[PROBABILITIES].sum(axis=1) - 1.0).max())
