"""Returns at the opening prices, the margins and lines, and the 7+ tail, all matches pooled.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/PRICES.md`. Prints the return of a flat stake on
each 1X2 outcome by price band and by side, with the returns that the proportional and Shin
probabilities expect; on the over and the under at each opening O/U line; and on each side of
the opening Asian handicap, by handicap band. Then the O/U and AH margins and lines. Then the
7+ tail: do the 7+ matches fall short of the yardstick (`ALL/ODDS_YARDSTICK.md`, C7) because
the totals are too high, or because of the shape of the goal counts? The returns also per
season cohort.

Run: `uv run python -m analysis.schedule.whole_corpus.all.prices`
"""

import numpy as np
import pandas as pd
from scipy import stats as sps

from analysis import corpus, report, stats
from analysis.methods import shin, yardstick

OU = ["s1_odds_ou_open_line", "s1_odds_ou_open_over", "s1_odds_ou_open_under"]
MIN_LINE_MATCHES = 200  # an O/U line with fewer matches gets no row of its own
# The AH line is positive when the home team gives the handicap (S1.22).
# (label, lowest line, highest line); a line is a multiple of 0.25.
AH_BANDS = (
    ("home gives 1 or more", 1.0, np.inf),
    ("home gives 0.25 to 0.75", 0.25, 0.75),
    ("level", 0.0, 0.0),
    ("away gives 0.25 to 0.75", -0.75, -0.25),
    ("away gives 1 or more", -np.inf, -1.0),
)
MARGIN_QUANTILES = (0.01, 0.05, 0.5, 0.95, 0.99)
TAIL_GOALS = (5, 6, 7, 8)


def settle(metric: np.ndarray, line: np.ndarray, price: np.ndarray) -> np.ndarray:
    """The profit per unit stake of a bet that wins when `metric` is above `line`, Asian rules.

    A quarter line splits the stake between its two neighbours (2.25: half on 2.0, half on
    2.5). On a whole line, a metric equal to it returns that part of the stake.
    """

    quarter = np.round(line * 4).astype(int) % 2 == 1
    profit = np.zeros(len(line))
    for shift in (-0.25, 0.25):
        part = np.where(quarter, line + shift, line)
        win = metric > part + 1e-9
        push = np.abs(metric - part) < 1e-9
        profit += 0.5 * np.where(win, price - 1.0, np.where(push, 0.0, -1.0))

    return profit


def margin(*prices: "pd.Series[float]") -> "pd.Series[float]":
    """The bookmaker's margin of one market: the sum of the inverse prices, minus 1."""

    return sum((1.0 / price for price in prices), start=pd.Series(0.0, index=prices[0].index)) - 1.0


def roi(bets_df: pd.DataFrame, profit: str) -> dict[str, float]:
    """The return per unit stake (the mean profit), with its interval over league-seasons."""

    low, high = stats.cluster_bootstrap_ci(bets_df[profit], bets_df["cluster"])
    return {
        "bets": float(len(bets_df)),
        "roi": float(bets_df[profit].mean()),
        "low": low,
        "high": high,
    }


def x12_bets(matches_df: pd.DataFrame) -> pd.DataFrame:
    """One flat bet on each 1X2 outcome of each priced match, with its profit and the profit
    that the proportional and the Shin probabilities expect."""

    outcome_rows_df = shin.outcome_rows(shin.scored(matches_df))

    outcome_rows_df["profit"] = np.where(
        outcome_rows_df["hit"], outcome_rows_df["price"] - 1.0, -1.0
    )
    outcome_rows_df["profit_prop"] = outcome_rows_df["prop"] * outcome_rows_df["price"] - 1.0
    outcome_rows_df["profit_shin"] = outcome_rows_df["shin"] * outcome_rows_df["price"] - 1.0
    outcome_rows_df["band"] = pd.cut(outcome_rows_df["price"], shin.PRICE_EDGES)
    outcome_rows_df["side"] = pd.Categorical(
        outcome_rows_df["side"], ["home", "draw", "away"], ordered=True
    )

    return outcome_rows_df


def x12_table(bets_df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Per group (a price band from the shortest, or a side): the bets, the mean price, the hit
    rate, the return with its interval, and the returns that the two sets of probabilities
    expect."""

    table = []
    for name, group_bets_df in bets_df.groupby(by, observed=True):
        table.append(
            {
                by: str(name),
                **roi(group_bets_df, "profit"),
                "mean price": float(group_bets_df["price"].mean()),
                "hit rate": float(group_bets_df["hit"].mean()),
                "proportional expects": float(group_bets_df["profit_prop"].mean()),
                "Shin expects": float(group_bets_df["profit_shin"].mean()),
            }
        )

    return pd.DataFrame(table)


def two_way_bets(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Per match with both Asian markets: the profit of each side of the O/U and of the AH,
    and the cost of each market's margin, 1 / (1 + margin) - 1."""

    priced_df = matches_df.dropna(subset=[*OU, *corpus.AH])

    total = priced_df["s2_total_goals"].to_numpy(dtype=float)
    lead = (priced_df["s1_ft_home_goals"] - priced_df["s1_ft_away_goals"]).to_numpy(dtype=float)

    ou_line, over, under = (priced_df[c].to_numpy(dtype=float) for c in OU)
    ah_line, home, away = (priced_df[c].to_numpy(dtype=float) for c in corpus.AH)

    return pd.DataFrame(
        {
            "ou_line": ou_line,
            "over": settle(total, ou_line, over),
            "under": settle(-total, -ou_line, under),
            "ou_cost": 1.0 / (1.0 + margin(priced_df[OU[1]], priced_df[OU[2]])) - 1.0,
            "ah_line": ah_line,
            "home": settle(lead, ah_line, home),
            "away": settle(-lead, -ah_line, away),
            "ah_cost": 1.0 / (1.0 + margin(priced_df[corpus.AH[1]], priced_df[corpus.AH[2]])) - 1.0,
            "cluster": priced_df["s1_league_id"].astype(str) + " " + priced_df["s1_season"],
            "season_cohort": priced_df["season_cohort"],
        },
        index=priced_df.index,
    )


def side_table(
    bets_df: pd.DataFrame, groups: dict[str, "pd.Series[bool]"], sides: tuple[str, str], cost: str
) -> pd.DataFrame:
    """Per group of matches: the return of each of the two sides, and the margin's cost. A
    group with no match gets no row."""

    table = []
    for name, mask in groups.items():
        side_bets_df = bets_df[mask]
        if side_bets_df.empty:
            continue

        row: dict[str, float | str] = {"group": name, "matches": float(len(side_bets_df))}
        for side in sides:
            values = roi(side_bets_df, side)
            row |= {
                side: values["roi"],
                f"{side} low": values["low"],
                f"{side} high": values["high"],
            }

        row["margin cost"] = float(side_bets_df[cost].mean())
        table.append(row)

    return pd.DataFrame(table)


def ou_groups(bets_df: pd.DataFrame) -> dict[str, "pd.Series[bool]"]:
    """Each opening O/U line with enough matches, and all lines together."""

    counts = bets_df["ou_line"].value_counts()
    lines = sorted(counts[counts >= MIN_LINE_MATCHES].index)
    groups = {f"{line:g}": bets_df["ou_line"] == line for line in lines}
    groups["all lines"] = pd.Series(True, index=bets_df.index)
    return groups


def ah_groups(bets_df: pd.DataFrame) -> dict[str, "pd.Series[bool]"]:
    """Each band of the opening handicap, and all bands together."""

    groups = {
        name: bets_df["ah_line"].between(lowest, highest) for name, lowest, highest in AH_BANDS
    }
    groups["all lines"] = pd.Series(True, index=bets_df.index)
    return groups


def margin_table(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Quantiles and the mean of each market's margin, over the matches that have it."""

    markets = {"1X2": shin.ODDS, "O/U": OU[1:], "AH": corpus.AH[1:]}

    table = []
    for name, columns in markets.items():
        priced_df = matches_df.dropna(subset=columns)
        values = margin(*(priced_df[c] for c in columns))
        quantiles = values.quantile(list(MARGIN_QUANTILES))

        table.append(
            {
                "market": name,
                **{f"q{q:g}": float(v) for q, v in quantiles.items()},
                "mean": float(values.mean()),
            }
        )

    return pd.DataFrame(table)


def line_shares(line: "pd.Series[float]") -> pd.DataFrame:
    """The share of matches at each line."""

    counts = line.value_counts().sort_index()
    return pd.DataFrame(
        {"line": counts.index, "matches": counts.to_numpy(), "share": counts.to_numpy() / len(line)}
    )


def quarter_share(line: "pd.Series[float]") -> float:
    """The share of quarter lines (a .25 or .75 line, which splits the stake)."""

    return float((np.round(line * 4) % 2 == 1).mean())


def calibrated_totals(yardstick_df: pd.DataFrame) -> "pd.Series[float]":
    """Each match's expected goals, times the observed / expected goals of its band."""

    bands = pd.cut(yardstick_df["m_goals"], yardstick.TOTAL_EDGES)
    grouped = yardstick_df.groupby(bands, observed=True)
    ratio = grouped["goals"].transform("mean") / grouped["m_goals"].transform("mean")
    return yardstick_df["m_goals"] * ratio


def tail_bands(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """Per band of expected goals: the model's and the observed mean goals, and the variance
    of the observed totals over their mean (a Poisson count gives 1)."""

    grouped = yardstick_df.groupby(
        pd.cut(yardstick_df["m_goals"], yardstick.TOTAL_EDGES), observed=True
    )
    tail_bands_df = pd.DataFrame(
        {
            "matches": grouped.size(),
            "model mean": grouped["m_goals"].mean(),
            "observed mean": grouped["goals"].mean(),
            "variance / mean": grouped["goals"].var() / grouped["goals"].mean(),
        }
    )

    tail_bands_df["observed / model"] = tail_bands_df["observed mean"] / tail_bands_df["model mean"]
    return tail_bands_df.reset_index().rename(columns={"m_goals": "expected goals"})


def tail_counts(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """Matches with k goals or more: observed, and expected by Poisson on the market's totals
    and on the band-calibrated totals."""

    calibrated = calibrated_totals(yardstick_df)
    return pd.DataFrame(
        [
            {
                "goals": f"{minimum_goals}+",
                "observed": float((yardstick_df["goals"] >= minimum_goals).sum()),
                "Poisson, market totals": float(
                    sps.poisson.sf(minimum_goals - 1, yardstick_df["m_goals"]).sum()
                ),
                "Poisson, calibrated totals": float(
                    sps.poisson.sf(minimum_goals - 1, calibrated).sum()
                ),
            }
            for minimum_goals in TAIL_GOALS
        ]
    )


def tail_oe(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """7+ goals against Poisson on the market's totals and on the band-calibrated totals, and
    the share of the market's gap to the observed count that the calibration closes."""

    calibrated_df = yardstick_df.assign(
        m_seven_calibrated=sps.poisson.sf(6, calibrated_totals(yardstick_df))
    )
    tail_oe_df = stats.observed_expected_table(
        calibrated_df,
        (
            ("seven", "m_seven", "Poisson, market totals"),
            ("seven", "m_seven_calibrated", "Poisson, calibrated totals"),
        ),
    )

    market, matched = tail_oe_df["expected"]
    observed = float(tail_oe_df["observed"].iloc[0])
    tail_oe_df["gap closed"] = [0.0, (market - matched) / (market - observed)]

    return tail_oe_df


def show_returns(matches_df: pd.DataFrame, title: str) -> None:
    """The return tables of one set of matches."""

    bets_df = x12_bets(matches_df)
    report.show(f"1X2 by price band, {title}", x12_table(bets_df, "band"))
    report.show(f"1X2 by side, {title}", x12_table(bets_df, "side"))

    two_way_bets_df = two_way_bets(matches_df)
    report.show(
        f"O/U by opening line, {title}",
        side_table(two_way_bets_df, ou_groups(two_way_bets_df), ("over", "under"), "ou_cost"),
    )
    report.show(
        f"AH by opening handicap, {title}",
        side_table(two_way_bets_df, ah_groups(two_way_bets_df), ("home", "away"), "ah_cost"),
    )


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    show_returns(matches_df, "all matches")
    for cohort, cohort_df in matches_df.groupby("season_cohort"):
        show_returns(cohort_df, f"season cohort {cohort}")

    report.show("Margins: quantiles and mean", margin_table(matches_df))

    priced_df = matches_df.dropna(subset=[*OU, *corpus.AH])
    report.show("Opening O/U lines", line_shares(priced_df[OU[0]]))
    print(
        f"\nquarter lines: O/U {quarter_share(priced_df[OU[0]]):.4f}, "
        f"AH {quarter_share(priced_df[corpus.AH[0]]):.4f}"
    )

    share = yardstick.first_half_share(yardstick.priced(matches_df))
    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid(), share=share)

    report.show("The 7+ tail: goals by band of expected goals", tail_bands(yardstick_df))
    report.show("The 7+ tail: k goals or more", tail_counts(yardstick_df))
    report.show("7+ goals against the market's and the calibrated totals", tail_oe(yardstick_df))

    for cohort, cohort_df in yardstick_df.groupby("season_cohort"):
        report.show(f"The same, season cohort {cohort} (its own calibration)", tail_oe(cohort_df))


if __name__ == "__main__":
    main()
