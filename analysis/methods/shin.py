"""Shin's method on the opening 1X2: margin-free probabilities and the insider share z.

The arithmetic is the `shin` package from PyPI (the user, 2026-10-14), not our own code.
Shin (1993) prices a market against a share z of insiders; removing the margin that way
takes more from long shots than from favourites, by construction. The project's default,
proportional removal, is stage 2's `s2_mkt_p_*` (`features/schedule_row.py`).
"""

import math

import numpy as np
import pandas as pd
from shin import calculate_implied_probabilities

from analysis import corpus, stats

ODDS = ["s1_odds_1x2_open_home", "s1_odds_1x2_open_draw", "s1_odds_1x2_open_away"]
PROPORTIONAL = ["s2_mkt_p_home", "s2_mkt_p_draw", "s2_mkt_p_away"]
PROBS = ["shin_p_home", "shin_p_draw", "shin_p_away"]
KEYS = ["match_id", "s1_league_id", "s1_league_name", "s1_season", "season_cohort"]
# Decimal-odds bands of an outcome's price, from favourites to long shots.
PRICE_EDGES = (1.0, 1.3, 1.6, 2.0, 2.6, 3.5, 5.5, 8.0, 13.0, np.inf)


def shin_row(home: float, draw: float, away: float) -> tuple[float, float, float, float]:
    """Shin's three probabilities and z for one match; all NaN when a price is missing."""
    odds = [home, draw, away]
    if any(math.isnan(price) for price in odds):
        return (math.nan, math.nan, math.nan, math.nan)
    result = calculate_implied_probabilities(odds, full_output=True)
    p_home, p_draw, p_away = result.implied_probabilities
    return p_home, p_draw, p_away, result.z


def shin_frame(matches: pd.DataFrame) -> pd.DataFrame:
    """Shin's probabilities (`PROBS`) and `shin_z`, one row per match, on the same index."""
    rows = [shin_row(*map(float, prices)) for prices in matches[ODDS].itertuples(index=False)]
    return pd.DataFrame(rows, columns=[*PROBS, "shin_z"], index=matches.index)


def scored(matches: pd.DataFrame) -> pd.DataFrame:
    """Every match with all three opening 1X2 prices, scored on its full-time result.

    Per match: the keys, the prices, both methods' probabilities, z, the bookmaker's margin,
    each method's log loss and Brier score, and Shin's gain over proportional (proportional
    loss minus Shin loss: above 0 means Shin scored better). `cluster` is the league-season.
    """
    priced = matches.dropna(subset=ODDS)
    frame = pd.concat([priced[KEYS + ODDS + PROPORTIONAL], shin_frame(priced)], axis=1)
    frame["margin"] = (1.0 / priced[ODDS]).sum(axis=1) - 1.0
    frame["outcome"] = corpus.outcome_1x2(priced)
    result = frame["outcome"].to_numpy()
    for name, columns in (("prop", PROPORTIONAL), ("shin", PROBS)):
        probs = frame[columns].to_numpy()
        frame[f"ll_{name}"] = stats.log_loss_1x2(probs, result)
        frame[f"brier_{name}"] = stats.brier_1x2(probs, result)
    frame["ll_gain"] = frame["ll_prop"] - frame["ll_shin"]
    frame["brier_gain"] = frame["brier_prop"] - frame["brier_shin"]
    frame["cluster"] = priced["s1_league_id"].astype(str) + " " + priced["s1_season"]
    return frame


def outcome_rows(frame: pd.DataFrame) -> pd.DataFrame:
    """Three rows per match of `scored`, one per outcome: its side, its price, both
    probabilities, if it happened, and the league-season."""
    codes = (corpus.HOME, corpus.DRAW, corpus.AWAY)
    sides = [
        pd.DataFrame(
            {
                "side": side,
                "price": frame[odds].to_numpy(),
                "prop": frame[prop].to_numpy(),
                "shin": frame[shin_p].to_numpy(),
                "hit": (frame["outcome"] == code).to_numpy(),
                "cluster": frame["cluster"].to_numpy(),
            }
        )
        for side, code, odds, prop, shin_p in zip(
            ("home", "draw", "away"), codes, ODDS, PROPORTIONAL, PROBS, strict=True
        )
    ]
    return pd.concat(sides, ignore_index=True)


def sum_error(frame: pd.DataFrame) -> float:
    """Largest distance of a match's Shin probabilities from summing to 1 (a convergence check)."""
    return float(np.abs(frame[PROBS].sum(axis=1) - 1.0).max())
