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
    toy_matches: pd.DataFrame,
) -> None:
    bets = runner.x12_bets(toy_matches)

    assert len(bets) == 3 * 4  # the toy match without a draw price has no bets
    assert bets["profit"].tolist() == pytest.approx(
        np.where(bets["hit"], bets["price"] - 1.0, -1.0).tolist()
    )
    assert bets["profit_prop"].tolist() == pytest.approx(
        (bets["prop"] * bets["price"] - 1.0).tolist()
    )


def test_x12_table_orders_the_bands_from_the_shortest_price(toy_matches: pd.DataFrame) -> None:
    bets = runner.x12_bets(toy_matches)
    bands = runner.x12_table(bets, "band")

    edges = [float(band.split(",")[0].strip("(")) for band in bands["band"]]
    assert edges == sorted(edges)
    assert bands["bets"].sum() == len(bets)

    sides = runner.x12_table(bets, "side")
    assert sides["side"].tolist() == ["home", "draw", "away"]


@pytest.fixture
def asian() -> pd.DataFrame:
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


def test_two_way_bets_settle_both_markets(asian: pd.DataFrame) -> None:
    bets = runner.two_way_bets(asian)

    assert bets["over"].tolist() == pytest.approx([0.9, -1.0, 0.0, 0.0])
    assert bets["under"].tolist() == pytest.approx([-1.0, 0.9, 0.0, 0.0])

    # Home gives 1 and wins by 1: a push. Level and a draw: a push. Home gets 0.5 and draws:
    # it wins. Home gives 1.25 and wins by 3: it wins.
    assert bets["home"].tolist() == pytest.approx([0.0, 0.0, 0.9, 0.8])
    assert bets["ou_cost"].tolist() == pytest.approx([1 / (2 / 1.9) - 1, 1 / (2 / 1.9) - 1, 0, 0])
    assert bets["cluster"].tolist() == ["1 2024", "1 2024", "2 2025", "2 2025"]


def test_groups_cover_the_lines_and_the_bands(
    asian: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    bets = runner.two_way_bets(asian)
    monkeypatch.setattr(runner, "MIN_LINE_MATCHES", 2)

    assert list(runner.ou_groups(bets)) == ["2.5", "all lines"]

    groups = runner.ah_groups(bets)
    assert groups["home gives 1 or more"].tolist() == [True, False, False, True]
    assert groups["level"].tolist() == [False, True, False, False]
    assert groups["away gives 0.25 to 0.75"].tolist() == [False, False, True, False]

    table = runner.side_table(bets, groups, ("home", "away"), "ah_cost")
    assert table.loc[table["group"] == "all lines", "matches"].item() == 4.0


def test_margin_table_has_one_row_per_market(asian: pd.DataFrame) -> None:
    matches = asian.assign(**dict.fromkeys(shin.ODDS, 3.0))
    table = runner.margin_table(matches).set_index("market")
    assert list(table.index) == ["1X2", "O/U", "AH"]
    assert table.loc["1X2", "mean"] == pytest.approx(0.0)


def test_line_shares_and_the_quarter_share() -> None:
    lines = pd.Series([2.5, 2.5, 2.25, 3.0])
    table = runner.line_shares(lines)
    assert table["line"].tolist() == [2.25, 2.5, 3.0]
    assert table["share"].tolist() == pytest.approx([0.25, 0.5, 0.25])
    assert runner.quarter_share(pd.Series([2.25, 2.75, 2.5, -0.25])) == pytest.approx(0.75)


@pytest.fixture
def tail() -> pd.DataFrame:
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


def test_calibrated_totals_match_the_observed_mean_of_each_band(tail: pd.DataFrame) -> None:
    calibrated = runner.calibrated_totals(tail)
    assert calibrated[:3].mean() == pytest.approx(tail["goals"][:3].mean())
    assert calibrated[3:].mean() == pytest.approx(tail["goals"][3:].mean())


def test_tail_tables(tail: pd.DataFrame) -> None:
    bands = runner.tail_bands(tail)

    assert bands["matches"].tolist() == [3, 3]
    assert bands["observed / model"].tolist() == pytest.approx([7 / 6, 4 / 3.6])

    counts = runner.tail_counts(tail).set_index("goals")
    assert counts.loc["7+", "observed"] == 1.0

    table = runner.tail_oe(tail)
    market, matched = table["expected"]
    assert table["gap closed"].tolist() == pytest.approx([0.0, (market - matched) / (market - 1)])
