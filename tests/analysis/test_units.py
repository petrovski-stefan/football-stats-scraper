"""`analysis/units.py`: unit values, their variance, the tests across units, and their parts."""

import pandas as pd
import pytest

from analysis import units

UNIT = "unit"


@pytest.fixture
def toy_frame() -> pd.DataFrame:
    """Six matches of two units in both cohorts: goals against an expected count."""
    return pd.DataFrame(
        {
            UNIT: [1, 1, 1, 2, 2, 2],
            "season_cohort": [2024, 2024, 2025, 2024, 2025, 2025],
            "goals": [3.0, 1.0, 2.0, 4.0, 0.0, 3.0],
            "m_goals": [2.5, 2.0, 2.5, 3.0, 2.0, 2.5],
        }
    )


def test_match_variance_of_each_kind() -> None:
    assert units.match_variance("count", 1.2, pd.Series([0.5, 2.0])).tolist() == pytest.approx(
        [0.6, 2.4]
    )
    events = units.match_variance("event", 0.5, pd.Series([0.1, 0.4]))
    assert events.tolist() == pytest.approx([0.05 * 0.95, 0.2 * 0.8])
    shares = units.match_variance("share", 0.4, pd.Series([3.0, 0.0]))
    assert shares.tolist() == pytest.approx([0.24 * 3, 0.0])
    with pytest.raises(ValueError, match="unknown kind"):
        units.match_variance("rate", 0.5, pd.Series([1.0]))


def test_dispersion_compares_the_spread_with_the_kind() -> None:
    frame = pd.DataFrame(
        {UNIT: [1, 1, 2, 2], "observed": [1.0, 3.0, 0.0, 4.0], "expected": [2.0, 2.0, 1.0, 1.0]}
    )
    # Unit 1: own value 1, residuals -1 and 1, Poisson variance 2 + 2. Unit 2: own value 2,
    # residuals -2 and 2, variance 2 + 2. So (2 + 8) / (4 + 4).
    assert units.dispersion(frame, UNIT, "observed", "expected", "count") == pytest.approx(1.25)


def test_unit_values_are_ratios_of_sums(toy_frame: pd.DataFrame) -> None:
    values = units.unit_values(toy_frame, UNIT, "goals", "m_goals", "count")
    assert values["observed"].tolist() == [6.0, 7.0]
    assert values["expected"].tolist() == [7.0, 7.5]
    assert values["value"].tolist() == pytest.approx([6 / 7, 7 / 7.5])
    pooled = 13 / 14.5
    assert values["variance"].tolist() == pytest.approx([pooled / 7, pooled / 7.5])
    doubled = units.unit_values(toy_frame, UNIT, "goals", "m_goals", "count", phi=2.0)
    assert doubled["variance"].tolist() == pytest.approx((2 * values["variance"]).tolist())


def test_equal_units_show_no_spread_and_keep_the_pooled_value() -> None:
    frame = pd.DataFrame(
        {UNIT: [1, 1, 2, 2], "hit": [1.0, 0.0, 1.0, 0.0], "chance": [0.5, 0.5, 0.5, 0.5]}
    )
    values, het, phi = units.tested(frame, UNIT, "hit", "chance", "event")
    assert (het.q, het.tau2) == pytest.approx((0.0, 0.0))
    assert phi == pytest.approx(1.0)
    assert values["shrunk"].tolist() == pytest.approx([1.0, 1.0])


def test_luck_line_brackets_the_pooled_value() -> None:
    low, high = units.luck_line(pd.Series([10.0, 20.0, 30.0]), 1.2)
    assert low <= 1.2 <= high
    low, high = units.luck_line(pd.Series([1e9, 1e9]), 1.2)
    assert (low, high) == pytest.approx((1.2, 1.2), abs=1e-3)


def test_cohort_agreement_pairs_the_units_seen_in_both_cohorts(toy_frame: pd.DataFrame) -> None:
    r, n = units.cohort_agreement(toy_frame, UNIT, "goals", "m_goals")
    assert n == 2
    # Two units are ranked the same way in both cohorts, or the opposite way.
    assert abs(r) == pytest.approx(1.0)


def test_summary_row_shrinks_toward_the_pool(toy_frame: pd.DataFrame) -> None:
    quantity = ("goals", "m_goals", "goals O/E", "count")
    row, values = units.summary_row(toy_frame, UNIT, quantity, luck=True)
    assert row["quantity"] == "goals O/E"
    assert row["pooled"] == pytest.approx(13 / 14.5)
    assert isinstance(row["p"], str)
    assert float(row["luck min"]) <= float(row["luck max"])
    for raw, shrunk in zip(values["value"], values["shrunk"], strict=True):
        assert min(raw, 13 / 14.5) - 1e-12 <= shrunk <= max(raw, 13 / 14.5) + 1e-12
    no_luck, _ = units.summary_row(toy_frame, UNIT, quantity)
    assert pd.isna(no_luck["luck min"])


@pytest.fixture
def seasons() -> pd.DataFrame:
    """Two units with two parts each: unit 1's parts agree, unit 2's parts differ widely."""
    goals = [1.0, 3.0, 3.0, 1.0, 0.0, 1.0, 5.0, 7.0]
    return pd.DataFrame(
        {
            UNIT: [1, 1, 1, 1, 2, 2, 2, 2],
            "part": ["1a", "1a", "1b", "1b", "2a", "2a", "2b", "2b"],
            "goals": goals,
            "one": 1.0,
        }
    )


def test_within_test_sums_the_parts_of_each_unit(seasons: pd.DataFrame) -> None:
    q, df, p = units.within_test(seasons, UNIT, "part", "goals", "one", "count")
    assert df == 2  # two units with two parts each
    assert q > 0
    alone = units.within_test(seasons[seasons[UNIT] == 1], UNIT, "part", "goals", "one", "count")
    assert alone[0] == pytest.approx(0.0)
    assert alone[1] == 1
    assert 0.0 <= p <= 1.0
