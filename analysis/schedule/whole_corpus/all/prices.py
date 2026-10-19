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
AH = ["s1_odds_ah_open_line", "s1_odds_ah_open_home", "s1_odds_ah_open_away"]
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


def roi(frame: pd.DataFrame, profit: str) -> dict[str, float]:
    """The return per unit stake (the mean profit), with its interval over league-seasons."""
    low, high = stats.cluster_bootstrap_ci(frame[profit], frame["cluster"])
    return {"bets": float(len(frame)), "roi": float(frame[profit].mean()), "low": low, "high": high}


def x12_bets(matches: pd.DataFrame) -> pd.DataFrame:
    """One flat bet on each 1X2 outcome of each priced match, with its profit and the profit
    that the proportional and the Shin probabilities expect."""
    rows = shin.outcome_rows(shin.scored(matches))
    rows["profit"] = np.where(rows["hit"], rows["price"] - 1.0, -1.0)
    rows["profit_prop"] = rows["prop"] * rows["price"] - 1.0
    rows["profit_shin"] = rows["shin"] * rows["price"] - 1.0
    rows["band"] = pd.cut(rows["price"], shin.PRICE_EDGES)
    rows["side"] = pd.Categorical(rows["side"], ["home", "draw", "away"], ordered=True)
    return rows


def x12_table(bets: pd.DataFrame, by: str) -> pd.DataFrame:
    """Per group (a price band from the shortest, or a side): the bets, the mean price, the hit
    rate, the return with its interval, and the returns that the two sets of probabilities
    expect."""
    table = []
    for name, group in bets.groupby(by, observed=True):
        table.append(
            {
                by: str(name),
                **roi(group, "profit"),
                "mean price": float(group["price"].mean()),
                "hit rate": float(group["hit"].mean()),
                "proportional expects": float(group["profit_prop"].mean()),
                "Shin expects": float(group["profit_shin"].mean()),
            }
        )
    return pd.DataFrame(table)


def two_way_bets(matches: pd.DataFrame) -> pd.DataFrame:
    """Per match with both Asian markets: the profit of each side of the O/U and of the AH,
    and the cost of each market's margin, 1 / (1 + margin) - 1."""
    rows = matches.dropna(subset=[*OU, *AH])
    total = rows["s2_total_goals"].to_numpy(dtype=float)
    lead = (rows["s1_ft_home_goals"] - rows["s1_ft_away_goals"]).to_numpy(dtype=float)
    ou_line, over, under = (rows[c].to_numpy(dtype=float) for c in OU)
    ah_line, home, away = (rows[c].to_numpy(dtype=float) for c in AH)
    return pd.DataFrame(
        {
            "ou_line": ou_line,
            "over": settle(total, ou_line, over),
            "under": settle(-total, -ou_line, under),
            "ou_cost": 1.0 / (1.0 + margin(rows[OU[1]], rows[OU[2]])) - 1.0,
            "ah_line": ah_line,
            "home": settle(lead, ah_line, home),
            "away": settle(-lead, -ah_line, away),
            "ah_cost": 1.0 / (1.0 + margin(rows[AH[1]], rows[AH[2]])) - 1.0,
            "cluster": rows["s1_league_id"].astype(str) + " " + rows["s1_season"],
            "season_cohort": rows["season_cohort"],
        },
        index=rows.index,
    )


def side_table(
    bets: pd.DataFrame, groups: dict[str, "pd.Series[bool]"], sides: tuple[str, str], cost: str
) -> pd.DataFrame:
    """Per group of matches: the return of each of the two sides, and the margin's cost. A
    group with no match gets no row."""
    table = []
    for name, mask in groups.items():
        part = bets[mask]
        if part.empty:
            continue
        row: dict[str, float | str] = {"group": name, "matches": float(len(part))}
        for side in sides:
            values = roi(part, side)
            row |= {
                side: values["roi"],
                f"{side} low": values["low"],
                f"{side} high": values["high"],
            }
        row["margin cost"] = float(part[cost].mean())
        table.append(row)
    return pd.DataFrame(table)


def ou_groups(bets: pd.DataFrame) -> dict[str, "pd.Series[bool]"]:
    """Each opening O/U line with enough matches, and all lines together."""
    counts = bets["ou_line"].value_counts()
    lines = sorted(counts[counts >= MIN_LINE_MATCHES].index)
    groups = {f"{line:g}": bets["ou_line"] == line for line in lines}
    groups["all lines"] = pd.Series(True, index=bets.index)
    return groups


def ah_groups(bets: pd.DataFrame) -> dict[str, "pd.Series[bool]"]:
    """Each band of the opening handicap, and all bands together."""
    groups = {name: bets["ah_line"].between(lowest, highest) for name, lowest, highest in AH_BANDS}
    groups["all lines"] = pd.Series(True, index=bets.index)
    return groups


def margin_table(matches: pd.DataFrame) -> pd.DataFrame:
    """Quantiles and the mean of each market's margin, over the matches that have it."""
    markets = {"1X2": shin.ODDS, "O/U": OU[1:], "AH": AH[1:]}
    table = []
    for name, columns in markets.items():
        rows = matches.dropna(subset=columns)
        values = margin(*(rows[c] for c in columns))
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


def calibrated_totals(frame: pd.DataFrame) -> "pd.Series[float]":
    """Each match's expected goals, times the observed / expected goals of its band."""
    bands = pd.cut(frame["m_goals"], yardstick.TOTAL_EDGES)
    grouped = frame.groupby(bands, observed=True)
    ratio = grouped["goals"].transform("mean") / grouped["m_goals"].transform("mean")
    return frame["m_goals"] * ratio


def tail_bands(frame: pd.DataFrame) -> pd.DataFrame:
    """Per band of expected goals: the model's and the observed mean goals, and the variance
    of the observed totals over their mean (a Poisson count gives 1)."""
    grouped = frame.groupby(pd.cut(frame["m_goals"], yardstick.TOTAL_EDGES), observed=True)
    table = pd.DataFrame(
        {
            "matches": grouped.size(),
            "model mean": grouped["m_goals"].mean(),
            "observed mean": grouped["goals"].mean(),
            "variance / mean": grouped["goals"].var() / grouped["goals"].mean(),
        }
    )
    table["observed / model"] = table["observed mean"] / table["model mean"]
    return table.reset_index().rename(columns={"m_goals": "expected goals"})


def tail_counts(frame: pd.DataFrame) -> pd.DataFrame:
    """Matches with k goals or more: observed, and expected by Poisson on the market's totals
    and on the band-calibrated totals."""
    calibrated = calibrated_totals(frame)
    return pd.DataFrame(
        [
            {
                "goals": f"{k}+",
                "observed": float((frame["goals"] >= k).sum()),
                "Poisson, market totals": float(sps.poisson.sf(k - 1, frame["m_goals"]).sum()),
                "Poisson, calibrated totals": float(sps.poisson.sf(k - 1, calibrated).sum()),
            }
            for k in TAIL_GOALS
        ]
    )


def tail_oe(frame: pd.DataFrame) -> pd.DataFrame:
    """7+ goals against Poisson on the market's totals and on the band-calibrated totals, and
    the share of the market's gap to the observed count that the calibration closes."""
    calibrated = frame.assign(m_seven_calibrated=sps.poisson.sf(6, calibrated_totals(frame)))
    table = stats.observed_expected_table(
        calibrated,
        (
            ("seven", "m_seven", "Poisson, market totals"),
            ("seven", "m_seven_calibrated", "Poisson, calibrated totals"),
        ),
    )
    market, matched = table["expected"]
    observed = float(table["observed"].iloc[0])
    table["gap closed"] = [0.0, (market - matched) / (market - observed)]
    return table


def show_returns(matches: pd.DataFrame, title: str) -> None:
    """The return tables of one set of matches."""
    bets = x12_bets(matches)
    report.show(f"1X2 by price band, {title}", x12_table(bets, "band"))
    report.show(f"1X2 by side, {title}", x12_table(bets, "side"))
    two_way = two_way_bets(matches)
    report.show(
        f"O/U by opening line, {title}",
        side_table(two_way, ou_groups(two_way), ("over", "under"), "ou_cost"),
    )
    report.show(
        f"AH by opening handicap, {title}",
        side_table(two_way, ah_groups(two_way), ("home", "away"), "ah_cost"),
    )


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    show_returns(matches, "all matches")
    for cohort, group in matches.groupby("season_cohort"):
        show_returns(group, f"season cohort {cohort}")

    report.show("Margins: quantiles and mean", margin_table(matches))
    priced = matches.dropna(subset=[*OU, *AH])
    report.show("Opening O/U lines", line_shares(priced[OU[0]]))
    print(
        f"\nquarter lines: O/U {quarter_share(priced[OU[0]]):.4f}, "
        f"AH {quarter_share(priced[AH[0]]):.4f}"
    )

    share = yardstick.first_half_share(yardstick.priced(matches))
    frame = yardstick.frame(matches, yardstick.build_grid(), share=share)
    report.show("The 7+ tail: goals by band of expected goals", tail_bands(frame))
    report.show("The 7+ tail: k goals or more", tail_counts(frame))
    report.show("7+ goals against the market's and the calibrated totals", tail_oe(frame))
    for cohort, group in frame.groupby("season_cohort"):
        report.show(f"The same, season cohort {cohort} (its own calibration)", tail_oe(group))


if __name__ == "__main__":
    main()
