"""`analysis/schedule/whole_corpus/per_league/odds_yardstick.py`: league values, tests, tables."""

import numpy as np
import pandas as pd
import pytest

from analysis.methods import yardstick
from analysis.schedule.whole_corpus.per_league import odds_yardstick as runner


@pytest.fixture
def toy_frame() -> pd.DataFrame:
    """Six matches in two leagues and both cohorts, in the shape `yardstick.frame` gives."""
    return pd.DataFrame(
        {
            "s1_league_id": [1, 1, 1, 2, 2, 2],
            "s1_league_name": ["A", "A", "A", "B", "B", "B"],
            "season_cohort": [2024, 2024, 2025, 2024, 2025, 2025],
            "goals": [3.0, 1.0, 2.0, 4.0, 0.0, 3.0],
            "goals_1h": [1.0, 1.0, 0.0, 2.0, 0.0, 1.0],
            "m_goals": [2.5, 2.0, 2.5, 3.0, 2.0, 2.5],
            "is_comeback": [1.0, 0.0, 0.0, 0.0, 0.0, 1.0],
            "m_cb": [0.05, 0.04, 0.05, 0.06, 0.04, 0.05],
            "lam_home": [1.5, 1.2, 1.4, 1.8, 1.0, 1.3],
            "lam_away": [1.0, 0.8, 1.1, 1.2, 1.0, 1.2],
            "ht_margin": [-1, 1, 0, 1, 0, 1],
            "one": 1.0,
        }
    )


def test_match_variance_of_each_kind() -> None:
    assert runner.match_variance("count", 1.2, pd.Series([0.5, 2.0])).tolist() == pytest.approx(
        [0.6, 2.4]
    )
    events = runner.match_variance("event", 0.5, pd.Series([0.1, 0.4]))
    assert events.tolist() == pytest.approx([0.05 * 0.95, 0.2 * 0.8])
    shares = runner.match_variance("share", 0.4, pd.Series([3.0, 0.0]))
    assert shares.tolist() == pytest.approx([0.24 * 3, 0.0])
    with pytest.raises(ValueError, match="unknown kind"):
        runner.match_variance("rate", 0.5, pd.Series([1.0]))


def test_dispersion_compares_the_spread_with_the_kind() -> None:
    frame = pd.DataFrame(
        {
            "s1_league_id": [1, 1, 2, 2],
            "observed": [1.0, 3.0, 0.0, 4.0],
            "expected": [2.0, 2.0, 1.0, 1.0],
        }
    )
    # League 1: own value 1, residuals -1 and 1, Poisson variance 2 + 2. League 2: own value
    # 2, residuals -2 and 2, variance 2 + 2. So (2 + 8) / (4 + 4).
    assert runner.dispersion(frame, "observed", "expected", "count") == pytest.approx(1.25)


def test_league_values_are_ratios_of_sums(toy_frame: pd.DataFrame) -> None:
    values = runner.league_values(toy_frame, "goals", "m_goals", "count")
    assert values["observed"].tolist() == [6.0, 7.0]
    assert values["expected"].tolist() == [7.0, 7.5]
    assert values["value"].tolist() == pytest.approx([6 / 7, 7 / 7.5])
    pooled = 13 / 14.5
    assert values["variance"].tolist() == pytest.approx([pooled / 7, pooled / 7.5])
    doubled = runner.league_values(toy_frame, "goals", "m_goals", "count", phi=2.0)
    assert doubled["variance"].tolist() == pytest.approx((2 * values["variance"]).tolist())


def test_equal_leagues_show_no_spread_and_keep_the_pooled_value() -> None:
    frame = pd.DataFrame(
        {
            "s1_league_id": [1, 1, 2, 2],
            "hit": [1.0, 0.0, 1.0, 0.0],
            "chance": [0.5, 0.5, 0.5, 0.5],
        }
    )
    values, het, phi = runner.tested(frame, "hit", "chance", "event")
    assert (het.q, het.tau2) == pytest.approx((0.0, 0.0))
    assert phi == pytest.approx(1.0)
    assert values["shrunk"].tolist() == pytest.approx([1.0, 1.0])


def test_luck_line_brackets_the_pooled_value() -> None:
    low, high = runner.luck_line(pd.Series([10.0, 20.0, 30.0]), 1.2)
    assert low <= 1.2 <= high
    low, high = runner.luck_line(pd.Series([1e9, 1e9]), 1.2)
    assert (low, high) == pytest.approx((1.2, 1.2), abs=1e-3)


def test_cohort_agreement_pairs_the_leagues_seen_in_both_cohorts(
    toy_frame: pd.DataFrame,
) -> None:
    r, n = runner.cohort_agreement(toy_frame, "goals", "m_goals")
    assert n == 2
    # Two leagues are ranked the same way in both cohorts, or the opposite way.
    assert abs(r) == pytest.approx(1.0)


def test_summary_row_shrinks_toward_the_pool(toy_frame: pd.DataFrame) -> None:
    quantity = ("goals", "m_goals", "goals O/E", "count")
    row, values = runner.summary_row(toy_frame, quantity)
    assert row["quantity"] == "goals O/E"
    assert row["pooled"] == pytest.approx(13 / 14.5)
    assert isinstance(row["p"], str)
    for raw, shrunk in zip(values["value"], values["shrunk"], strict=True):
        assert min(raw, 13 / 14.5) - 1e-12 <= shrunk <= max(raw, 13 / 14.5) + 1e-12


def test_with_own_share_uses_each_league_share(toy_frame: pd.DataFrame) -> None:
    own = runner.with_own_share(toy_frame)
    league = toy_frame["s1_league_id"] == 1
    share = 2 / 6  # league 1: 2 first-half goals of 6
    lam_home, lam_away = toy_frame["lam_home"][league], toy_frame["lam_away"][league]
    model = yardstick.implied(lam_home.to_numpy(), lam_away.to_numpy(), share)
    assert own["m_cb"][league].to_numpy() == pytest.approx(model["m_cb"].to_numpy())
    completion = yardstick.completion_given_ht(
        lam_home.to_numpy(), lam_away.to_numpy(), share, toy_frame["ht_margin"][league].to_numpy()
    )
    assert own["m_completion"][league].to_numpy() == pytest.approx(completion)


def test_league_table_is_in_the_order_of_the_names(toy_frame: pd.DataFrame) -> None:
    values = {"x": pd.DataFrame({"value": [0.9, 1.1]}, index=pd.Index([2, 1]))}
    table = runner.league_table(toy_frame, values, (("x", "value", "x O/E"),))
    assert table["league"].tolist() == ["A", "B"]
    assert table["matches"].tolist() == [3, 3]
    assert table["x O/E"].tolist() == [1.1, 0.9]
    assert np.all(table.columns == ["league", "matches", "x O/E"])
