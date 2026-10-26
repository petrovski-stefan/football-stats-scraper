"""The odds yardstick: the goal rates that the opening prices imply, and what they expect.

For each match, the yardstick finds the home and away goal rates of the basic goal model
(independent Poisson counts, `notes/REFERENCE/MARKET_COMEBACKS.md` "The basic goal model")
that best reproduce the market: Shin's home and away probabilities from the opening 1X2
(`methods/shin.py`) and the fair over price at the opening Asian O/U line (stage 2's
`s2_implied_over`). One first-half share, taken from the data, splits each rate into
halves. The four rates then give the model's chances of a comeback, a decisive half-time,
7+ goals, 0-0 and 1-1, and of a completion from the half-time score that happened.

The fit is a nearest neighbour on a grid of rate pairs, one KD-tree per O/U line, in the
space of (home win, away win, fair over) probabilities. Three market numbers meet two
rates, so the fit is a least-squares compromise, and `fit_error` says how far it is.
"""

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as sps
from scipy.spatial import cKDTree

from analysis import stats
from analysis.methods import shin
from domain.stats import SEVEN_PLUS_GOALS

RATE_STEP = 0.02
RATES = np.arange(RATE_STEP, 6.0 + stats.FLOAT_TOLERANCE, RATE_STEP)
MAX_GOALS = 25  # per team, for the grid's win probabilities; the mass beyond is negligible
MAX_DEFICIT = 11  # half-time deficits summed over for a comeback
OU = ["s1_odds_ou_open_line", "s1_odds_ou_open_over", "s1_odds_ou_open_under"]
MAX_MARGIN = 12  # goal margins summed over in each half for the HT/FT cells
HTFT = tuple(f"{ht}/{ft}" for ht in "1X2" for ft in "1X2")
# Bands of a match's expected goals (the sum of its two rates), for tables by goal level.
TOTAL_EDGES = (0.0, 2.2, 2.5, 2.8, 3.1, 3.4, 10.0)


@dataclass(frozen=True)
class Grid:
    """Every pair of rates on the grid, with the model's home and away win chances."""

    home: np.ndarray
    away: np.ndarray
    p_home: np.ndarray
    p_away: np.ndarray


def build_grid(rates: np.ndarray = RATES) -> Grid:
    """The rate pairs and their win chances under independent Poisson goals."""

    home, away = (axis.ravel() for axis in np.meshgrid(rates, rates, indexing="ij"))

    goals = np.arange(MAX_GOALS)
    pmf_home = sps.poisson.pmf(goals[None, :], home[:, None])
    pmf_away = sps.poisson.pmf(goals[None, :], away[:, None])

    # P(the other side scores fewer than k goals), for each k: the cdf one goal behind.
    fewer_away = np.cumsum(pmf_away, axis=1) - pmf_away
    fewer_home = np.cumsum(pmf_home, axis=1) - pmf_home

    p_home = (pmf_home * fewer_away).sum(axis=1)
    p_away = (pmf_away * fewer_home).sum(axis=1)

    return Grid(home, away, p_home, p_away)


def fair_over(total: np.ndarray, line: float) -> np.ndarray:
    """The fair over chance W / (W + L) at an Asian goal line, for Poisson goal totals.

    A quarter line (2.25) splits the stake between its two neighbours (2.0 and 2.5). An
    integer line returns the stake when the total equals it, so the push drops out.
    """

    parts = (line - 0.25, line + 0.25) if round(line * 4) % 2 == 1 else (line,)

    win = np.zeros(np.shape(total))
    loss = np.zeros(np.shape(total))
    for part in parts:
        floor = int(np.floor(part + stats.FLOAT_TOLERANCE))
        is_integer = abs(part - round(part)) < stats.FLOAT_TOLERANCE
        win += sps.poisson.sf(floor, total)
        loss += sps.poisson.cdf(floor - 1 if is_integer else floor, total)

    return np.asarray(win / (win + loss))


def fit_rates(
    grid: Grid, p_home: np.ndarray, p_away: np.ndarray, over: np.ndarray, lines: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Per match, the grid's home and away rates nearest to its three market numbers.

    Returns the two rates and the fit error: the Euclidean distance, in probability, from
    (P(home), P(away), fair over) of the market to the same three numbers of the model.
    """

    lam_home, lam_away, error = (np.full(len(lines), np.nan) for _ in range(3))
    total = grid.home + grid.away
    for line in np.unique(lines):
        rows = np.flatnonzero(lines == line)
        tree = cKDTree(np.column_stack([grid.p_home, grid.p_away, fair_over(total, float(line))]))
        distance, nearest = tree.query(np.column_stack([p_home[rows], p_away[rows], over[rows]]))

        lam_home[rows] = grid.home[nearest]
        lam_away[rows] = grid.away[nearest]
        error[rows] = distance

    return lam_home, lam_away, error


def implied(
    lam_home: np.ndarray, lam_away: np.ndarray, share: "float | np.ndarray"
) -> pd.DataFrame:
    """The model's chances per match, from the two rates and the first-half share.

    `m_cb_home` sums, over each half-time deficit d of the home team, P(behind by d at HT)
    times P(win the second half by more than d); `m_cb_away` mirrors it.

    Args:
        share: one number for every match, or one per match.
    """

    home_rate_1h, away_rate_1h = share * lam_home, share * lam_away
    home_rate_2h, away_rate_2h = (1 - share) * lam_home, (1 - share) * lam_away

    cb_home = np.zeros(len(lam_home))
    cb_away = np.zeros(len(lam_home))
    for deficit in range(1, MAX_DEFICIT + 1):
        cb_home += sps.skellam.pmf(-deficit, home_rate_1h, away_rate_1h) * sps.skellam.sf(
            deficit, home_rate_2h, away_rate_2h
        )
        cb_away += sps.skellam.pmf(deficit, home_rate_1h, away_rate_1h) * sps.skellam.cdf(
            -deficit - 1, home_rate_2h, away_rate_2h
        )

    total = lam_home + lam_away

    return pd.DataFrame(
        {
            "m_cb_home": cb_home,
            "m_cb_away": cb_away,
            "m_cb": cb_home + cb_away,
            "m_ht_decisive": 1.0 - sps.skellam.pmf(0, home_rate_1h, away_rate_1h),
            "m_home_behind": sps.skellam.cdf(-1, home_rate_1h, away_rate_1h),
            "m_away_behind": sps.skellam.sf(0, home_rate_1h, away_rate_1h),
            "m_seven": sps.poisson.sf(SEVEN_PLUS_GOALS - 1, total),
            "m_00": np.exp(-total),
            "m_11": lam_home * lam_away * np.exp(-total),
            "m_goals": total,
            "m_goals_1h": share * total,
            "m_goals_2h": (1 - share) * total,
        }
    )


def completion_given_ht(
    lam_home: np.ndarray,
    lam_away: np.ndarray,
    share: "float | np.ndarray",
    ht_margin: np.ndarray,
    home_factor: "float | np.ndarray" = 1.0,
    away_factor: "float | np.ndarray" = 1.0,
) -> np.ndarray:
    """The model's chance that the team behind at half-time wins, from that HT score.

    A level half-time gives 0: no team is behind, so no comeback can happen.

    Args:
        share: one number for every match, or one per match.
        ht_margin: home minus away goals at half-time.
        home_factor: scales the home side's second-half rate; 1 is the basic model.
        away_factor: scales the away side's second-half rate; 1 is the basic model.
    """

    home_rate_2h = (1 - share) * lam_home * home_factor
    away_rate_2h = (1 - share) * lam_away * away_factor

    deficit = np.abs(ht_margin)
    home_behind = sps.skellam.sf(deficit, home_rate_2h, away_rate_2h)
    away_behind = sps.skellam.cdf(-deficit - 1, home_rate_2h, away_rate_2h)

    return np.asarray(
        np.where(ht_margin < 0, home_behind, np.where(ht_margin > 0, away_behind, 0.0))
    )


def result_code(margin: np.ndarray) -> np.ndarray:
    """The 1X2 code of a goal margin (home minus away): 1 home ahead, X level, 2 away ahead."""

    return np.asarray(np.where(margin > 0, "1", np.where(margin < 0, "2", "X")))


def htft_cells(lam_home: np.ndarray, lam_away: np.ndarray, share: float) -> pd.DataFrame:
    """The model's chance of each of the nine HT/FT results per match, column `m_<ht>/<ft>`.

    The half-time margin and the second-half margin are independent Skellam counts; the
    full-time margin is their sum. `m_2/1` is the home comeback and `m_1/2` the away one.
    """

    home_rate_1h, away_rate_1h = share * lam_home, share * lam_away
    home_rate_2h, away_rate_2h = (1 - share) * lam_home, (1 - share) * lam_away

    margins = np.arange(-MAX_MARGIN, MAX_MARGIN + 1)
    second = [sps.skellam.pmf(k, home_rate_2h, away_rate_2h) for k in margins]

    cells = {name: np.zeros(len(lam_home)) for name in HTFT}
    for ht_margin in margins:
        first = sps.skellam.pmf(ht_margin, home_rate_1h, away_rate_1h)
        ht = str(result_code(np.array(ht_margin)))
        for second_half_margin, chance in zip(margins, second, strict=True):
            cells[f"{ht}/{result_code(np.array(ht_margin + second_half_margin))!s}"] += (
                first * chance
            )

    return pd.DataFrame({f"m_{name}": chance for name, chance in cells.items()})


def first_half_share(matches_df: pd.DataFrame) -> float:
    """The share of all goals that came in the first half: one number for every match."""

    return float(matches_df["s2_goals_1h"].sum() / matches_df["s2_total_goals"].sum())


def priced(matches_df: pd.DataFrame) -> pd.DataFrame:
    """The matches that have all three opening 1X2 prices and the opening O/U market."""

    return matches_df.dropna(subset=[*shin.ODDS, *OU])


def frame(
    matches_df: pd.DataFrame,
    grid: Grid,
    share: float | None = None,
    *,
    is_proportional: bool = False,
) -> pd.DataFrame:
    """Every match with both opening markets, with its fitted rates and the model's chances.

    Outcomes come along as floats, so an observed count and an expected count add up the
    same way. `cluster` is the league-season.

    Args:
        share: the first-half share; None takes that of the priced matches.
        is_proportional: remove the 1X2 margin proportionally, not by Shin's method.
    """

    priced_df = priced(matches_df)
    if is_proportional:
        probabilities_df = priced_df[shin.PROPORTIONAL].set_axis(shin.PROBS, axis=1)
    else:
        probabilities_df = shin.shin_frame(priced_df)[shin.PROBS]

    lines = priced_df["s1_odds_ou_open_line"].to_numpy(dtype=float)
    lam_home, lam_away, error = fit_rates(
        grid,
        probabilities_df["shin_p_home"].to_numpy(dtype=float),
        probabilities_df["shin_p_away"].to_numpy(dtype=float),
        priced_df["s2_implied_over"].to_numpy(dtype=float),
        lines,
    )

    share = first_half_share(priced_df) if share is None else share

    yardstick_df = priced_df[shin.KEYS].copy()
    yardstick_df[shin.PROBS] = probabilities_df.to_numpy()
    yardstick_df["line"] = lines
    yardstick_df["lam_home"], yardstick_df["lam_away"], yardstick_df["fit_error"] = (
        lam_home,
        lam_away,
        error,
    )

    implied_df = implied(lam_home, lam_away, share)
    yardstick_df[implied_df.columns] = implied_df.to_numpy()

    ht_margin = (priced_df["s1_ht_home_goals"] - priced_df["s1_ht_away_goals"]).to_numpy()
    yardstick_df["m_completion"] = completion_given_ht(lam_home, lam_away, share, ht_margin)

    yardstick_df = yardstick_df.join(_outcomes(priced_df, ht_margin))
    yardstick_df["fav_p"] = yardstick_df[["shin_p_home", "shin_p_away"]].max(axis=1)
    yardstick_df["fav_is_home"] = yardstick_df["shin_p_home"] >= yardstick_df["shin_p_away"]
    yardstick_df["cluster"] = priced_df["s1_league_id"].astype(str) + " " + priced_df["s1_season"]

    return yardstick_df


def _outcomes(priced_df: pd.DataFrame, ht_margin: np.ndarray) -> pd.DataFrame:
    """The observed side of each comparison, as floats on the priced index."""

    home, away = priced_df["s1_ft_home_goals"], priced_df["s1_ft_away_goals"]
    outcomes_df = pd.DataFrame(
        {
            "is_comeback": priced_df["s2_is_comeback"],
            "is_comeback_home": priced_df["s2_is_comeback_home"],
            "is_comeback_away": priced_df["s2_is_comeback_away"],
            "ht_decisive": priced_df["s2_ht_decisive"],
            "seven": priced_df["s2_total_goals"] >= SEVEN_PLUS_GOALS,
            "is00": (home == 0) & (away == 0),
            "is11": (home == 1) & (away == 1),
            "goals": priced_df["s2_total_goals"],
            "goals_1h": priced_df["s2_goals_1h"],
            "goals_2h": priced_df["s2_goals_2h"],
            "goals_home": home,
            "goals_away": away,
            "goals_home_1h": priced_df["s1_ht_home_goals"],
            "goals_away_1h": priced_df["s1_ht_away_goals"],
        },
        index=priced_df.index,
    ).astype(float)

    outcomes_df["ht_margin"] = ht_margin

    return outcomes_df
