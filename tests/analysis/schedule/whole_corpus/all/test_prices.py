"""`analysis/schedule/whole_corpus/all/prices.py`: settlement, returns, margins, the 7+ tail."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats as sps

from analysis.methods import shin
from analysis.schedule.whole_corpus.all import prices as runner


def test_settle_a_half_line_wins_or_loses_the_stake() -> None:
    profit = runner.settle(np.array([3.0, 2.0]), np.array([2.5, 2.5]), np.array([1.9, 1.9]))
    assert profit.tolist() == pytest.approx([0.9, -1.0])


def test_settle_a_whole_line_returns_the_stake_on_the_line() -> None:
    profit = runner.settle(np.array([3.0, 2.0]), np.array([2.0, 2.0]), np.array([2.0, 2.0]))
    assert profit.tolist() == pytest.approx([1.0, 0.0])


def test_settle_a_quarter_line_splits_the_stake() -> None:
    # 2.25 with 2 goals: the half on 2.0 is a push, the half on 2.5 loses.
    # 2.75 with 3 goals: the half on 2.5 wins, the half on 3.0 is a push.
    profit = runner.settle(np.array([2.0, 3.0]), np.array([2.25, 2.75]), np.array([2.0, 2.0]))
    assert profit.tolist() == pytest.approx([-0.5, 0.5])


def test_settle_the_side_that_receives_a_quarter_handicap() -> None:
    # The away side at +0.75 (line -0.75 for it) when the home team wins by 1: the half
    # on +0.5 loses and the half on +1.0 is a push.
    profit = runner.settle(np.array([-1.0]), np.array([-0.75]), np.array([1.9]))
    assert profit.tolist() == pytest.approx([-0.5])


def test_margin_is_the_sum_of_the_inverse_prices_minus_one() -> None:
    values = runner.margin(pd.Series([2.0, 1.9]), pd.Series([2.0, 1.9]))
    assert values.tolist() == pytest.approx([0.0, 2 / 1.9 - 1])


def test_x12_bets_give_three_bets_a_match_and_their_profits(
    toy_matches_df: pd.DataFrame,
) -> None:
    bets_df = runner.x12_bets(toy_matches_df)

    assert len(bets_df) == 3 * 4  # the toy match without a draw price has no bets
    assert bets_df["profit"].tolist() == pytest.approx(
        np.where(bets_df["hit"], bets_df["price"] - 1.0, -1.0).tolist()
    )
    assert bets_df["profit_prop"].tolist() == pytest.approx(
        (bets_df["prop"] * bets_df["price"] - 1.0).tolist()
    )


def test_x12_table_orders_the_bands_from_the_shortest_price(toy_matches_df: pd.DataFrame) -> None:
    bets_df = runner.x12_bets(toy_matches_df)
    band_table_df = runner.x12_table(bets_df, "band")

    edges = [float(band.split(",")[0].strip("(")) for band in band_table_df["band"]]
    assert edges == sorted(edges)
    assert band_table_df["bets"].sum() == len(bets_df)

    side_table_df = runner.x12_table(bets_df, "side")
    assert side_table_df["side"].tolist() == ["home", "draw", "away"]


@pytest.fixture
def asian_matches_df() -> pd.DataFrame:
    """Four matches with both Asian markets, in two league-seasons."""

    return pd.DataFrame(
        {
            "s1_league_id": [1, 1, 2, 2],
            "s1_season": ["2024", "2024", "2025", "2025"],
            "season_cohort": [2024, 2024, 2025, 2025],
            "s1_ft_home_goals": [2, 0, 1, 3],
            "s1_ft_away_goals": [1, 0, 1, 0],
            "s2_total_goals": [3, 0, 2, 3],
            "s1_odds_ou_open_line": [2.5, 2.5, 2.0, 3.0],
            "s1_odds_ou_open_over": [1.9, 1.9, 2.0, 2.0],
            "s1_odds_ou_open_under": [1.9, 1.9, 2.0, 2.0],
            "s1_odds_ah_open_line": [1.0, 0.0, -0.5, 1.25],
            "s1_odds_ah_open_home": [2.0, 1.9, 1.9, 1.8],
            "s1_odds_ah_open_away": [1.8, 1.9, 1.9, 2.0],
        }
    )


def test_two_way_bets_settle_both_markets(asian_matches_df: pd.DataFrame) -> None:
    bets_df = runner.two_way_bets(asian_matches_df)

    assert bets_df["over"].tolist() == pytest.approx([0.9, -1.0, 0.0, 0.0])
    assert bets_df["under"].tolist() == pytest.approx([-1.0, 0.9, 0.0, 0.0])

    # Home gives 1 and wins by 1: a push. Level and a draw: a push. Home gets 0.5 and draws:
    # it wins. Home gives 1.25 and wins by 3: it wins.
    assert bets_df["home"].tolist() == pytest.approx([0.0, 0.0, 0.9, 0.8])
    assert bets_df["ou_cost"].tolist() == pytest.approx(
        [1 / (2 / 1.9) - 1, 1 / (2 / 1.9) - 1, 0, 0]
    )
    assert bets_df["cluster"].tolist() == ["1 2024", "1 2024", "2 2025", "2 2025"]


def test_groups_cover_the_lines_and_the_bands(
    asian_matches_df: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    bets_df = runner.two_way_bets(asian_matches_df)
    monkeypatch.setattr(runner, "MIN_LINE_MATCHES", 2)

    assert list(runner.ou_groups(bets_df)) == ["2.5", "all lines"]

    groups = runner.ah_groups(bets_df)
    assert groups["home gives 1 or more"].tolist() == [True, False, False, True]
    assert groups["level"].tolist() == [False, True, False, False]
    assert groups["away gives 0.25 to 0.75"].tolist() == [False, False, True, False]

    side_table_df = runner.side_table(bets_df, groups, ("home", "away"), "ah_cost")
    assert side_table_df.loc[side_table_df["group"] == "all lines", "matches"].item() == 4.0


def test_margin_table_has_one_row_per_market(asian_matches_df: pd.DataFrame) -> None:
    asian_priced_df = asian_matches_df.assign(**dict.fromkeys(shin.ODDS, 3.0))
    margin_table_df = runner.margin_table(asian_priced_df).set_index("market")
    assert list(margin_table_df.index) == ["1X2", "O/U", "AH"]
    assert margin_table_df.loc["1X2", "mean"] == pytest.approx(0.0)


def test_line_shares_and_the_quarter_share() -> None:
    lines = pd.Series([2.5, 2.5, 2.25, 3.0])
    line_shares_df = runner.line_shares(lines)
    assert line_shares_df["line"].tolist() == [2.25, 2.5, 3.0]
    assert line_shares_df["share"].tolist() == pytest.approx([0.25, 0.5, 0.25])
    assert runner.quarter_share(pd.Series([2.25, 2.75, 2.5, -0.25])) == pytest.approx(0.75)


@pytest.fixture
def tail_matches_df() -> pd.DataFrame:
    """Six matches in two bands of expected goals, in two league-seasons."""

    return pd.DataFrame(
        {
            "m_goals": [2.0, 2.0, 2.0, 3.6, 3.6, 3.6],
            "goals": [1.0, 2.0, 4.0, 2.0, 3.0, 7.0],
            "seven": [0.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            "m_seven": sps.poisson.sf(6, [2.0, 2.0, 2.0, 3.6, 3.6, 3.6]),
            "cluster": ["a", "b", "a", "b", "a", "b"],
        }
    )


def test_calibrated_totals_match_the_observed_mean_of_each_band(
    tail_matches_df: pd.DataFrame,
) -> None:
    calibrated = runner.calibrated_totals(tail_matches_df)
    assert calibrated[:3].mean() == pytest.approx(tail_matches_df["goals"][:3].mean())
    assert calibrated[3:].mean() == pytest.approx(tail_matches_df["goals"][3:].mean())


def test_tail_tables_give_bands_counts_and_the_gap_closed(tail_matches_df: pd.DataFrame) -> None:
    tail_bands_df = runner.tail_bands(tail_matches_df)

    assert tail_bands_df["matches"].tolist() == [3, 3]
    assert tail_bands_df["observed / model"].tolist() == pytest.approx([7 / 6, 4 / 3.6])

    tail_counts_df = runner.tail_counts(tail_matches_df).set_index("goals")
    assert tail_counts_df.loc["7+", "observed"] == 1.0

    tail_oe_df = runner.tail_oe(tail_matches_df)
    market, matched = tail_oe_df["expected"]
    assert tail_oe_df["gap closed"].tolist() == pytest.approx(
        [0.0, (market - matched) / (market - 1)]
    )
