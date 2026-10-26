"""`analysis/units.py`: unit values, their variance, the tests across units, and their parts."""

import numpy as np
import pandas as pd
import pytest

from analysis import card, units

UNIT = "unit"


@pytest.fixture
def toy_unit_matches_df() -> pd.DataFrame:
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
    unit_rows_df = pd.DataFrame(
        {UNIT: [1, 1, 2, 2], "observed": [1.0, 3.0, 0.0, 4.0], "expected": [2.0, 2.0, 1.0, 1.0]}
    )

    # Unit 1: own value 1, residuals -1 and 1, Poisson variance 2 + 2. Unit 2: own value 2,
    # residuals -2 and 2, variance 2 + 2. So (2 + 8) / (4 + 4).
    assert units.dispersion(unit_rows_df, UNIT, "observed", "expected", "count") == pytest.approx(
        1.25
    )


def test_unit_values_are_ratios_of_sums(toy_unit_matches_df: pd.DataFrame) -> None:
    unit_values_df = units.unit_values(toy_unit_matches_df, UNIT, "goals", "m_goals", "count")

    assert unit_values_df["observed"].tolist() == [6.0, 7.0]
    assert unit_values_df["expected"].tolist() == [7.0, 7.5]
    assert unit_values_df["value"].tolist() == pytest.approx([6 / 7, 7 / 7.5])

    pooled = 13 / 14.5
    assert unit_values_df["variance"].tolist() == pytest.approx([pooled / 7, pooled / 7.5])

    doubled_df = units.unit_values(
        toy_unit_matches_df, UNIT, "goals", "m_goals", "count", dispersion_factor=2.0
    )
    assert doubled_df["variance"].tolist() == pytest.approx(
        (2 * unit_values_df["variance"]).tolist()
    )


def test_equal_units_show_no_spread_and_keep_the_pooled_value() -> None:
    unit_rows_df = pd.DataFrame(
        {UNIT: [1, 1, 2, 2], "hit": [1.0, 0.0, 1.0, 0.0], "chance": [0.5, 0.5, 0.5, 0.5]}
    )

    unit_values_df, het, dispersion_factor = units.tested(
        unit_rows_df, UNIT, "hit", "chance", "event"
    )

    assert (het.cochran_q, het.tau_squared) == pytest.approx((0.0, 0.0))
    assert dispersion_factor == pytest.approx(1.0)
    assert unit_values_df["shrunk"].tolist() == pytest.approx([1.0, 1.0])


def test_luck_line_brackets_the_pooled_value() -> None:
    low, high = units.luck_line(pd.Series([10.0, 20.0, 30.0]), 1.2)
    assert low <= 1.2 <= high
    low, high = units.luck_line(pd.Series([1e9, 1e9]), 1.2)
    assert (low, high) == pytest.approx((1.2, 1.2), abs=1e-3)


def test_cohort_agreement_pairs_the_units_seen_in_both_cohorts(
    toy_unit_matches_df: pd.DataFrame,
) -> None:
    cohort_correlation, cohort_count = units.cohort_agreement(
        toy_unit_matches_df, UNIT, "goals", "m_goals"
    )

    assert cohort_count == 2

    # Two units are ranked the same way in both cohorts, or the opposite way.
    assert abs(cohort_correlation) == pytest.approx(1.0)


def test_summary_row_shrinks_toward_the_pool(toy_unit_matches_df: pd.DataFrame) -> None:
    quantity = ("goals", "m_goals", "goals O/E", "count")

    row, unit_values_df = units.summary_row(toy_unit_matches_df, UNIT, quantity, has_luck_line=True)

    assert row["quantity"] == "goals O/E"
    assert row["pooled"] == pytest.approx(13 / 14.5)
    assert isinstance(row["p"], str)
    assert float(row["luck min"]) <= float(row["luck max"])

    for raw, shrunk in zip(unit_values_df["value"], unit_values_df["shrunk"], strict=True):
        assert min(raw, 13 / 14.5) - 1e-12 <= shrunk <= max(raw, 13 / 14.5) + 1e-12, (raw, shrunk)

    no_luck, _ = units.summary_row(toy_unit_matches_df, UNIT, quantity)
    assert pd.isna(no_luck["luck min"])


@pytest.fixture
def seasons_df() -> pd.DataFrame:
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


def test_within_tested_uses_each_units_value_and_shrinks_toward_it(
    seasons_df: pd.DataFrame,
) -> None:
    result = units.within_tested(seasons_df, UNIT, "part", "goals", "one", "count")
    part_values_df = result.part_values_df
    dispersion = units.dispersion(seasons_df, "part", "goals", "one", "count")

    # Unit 1 has the value 2 and unit 2 the value 3.25; each part has 2 matches.
    assert part_values_df.loc["1a", "variance"] == pytest.approx(dispersion * 2.0 / 2)
    assert part_values_df.loc["2a", "variance"] == pytest.approx(dispersion * 3.25 / 2)
    assert part_values_df.loc["1a", "owner_mean"] == pytest.approx(2.0)
    assert part_values_df["shrunk"].loc[["1a", "1b"]].tolist() == pytest.approx([2.0, 2.0])

    for part in ("2a", "2b"):
        raw, mean = (
            float(part_values_df.at[part, "value"]),
            float(part_values_df.at[part, "owner_mean"]),
        )
        shrunk = float(part_values_df.at[part, "shrunk"])
        assert min(raw, mean) - 1e-12 <= shrunk <= max(raw, mean) + 1e-12, part

    assert result.tau_squared >= 0.0


def test_cohort_values_against_a_group_and_the_repeat_test() -> None:
    unit_rows_df = pd.DataFrame(
        {
            UNIT: [1, 1, 2, 2, 3, 3] * 2,
            "league": ["x"] * 12,
            "season_cohort": [2024] * 6 + [2025] * 6,
            "hit": [1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0],
            "one": 1.0,
        }
    )

    cohort_values_df = units.cohort_values(unit_rows_df, UNIT, "hit", "one", against="league")

    # The league has 1/2 in each cohort; units 1, 2 and 3 have 1, 1/2 and 0.
    assert cohort_values_df[2024].tolist() == pytest.approx([0.5, 0.0, -0.5])

    repeat_correlation, repeat_count, repeat_p_value = units.repeat_test(
        unit_rows_df, UNIT, "hit", "one", "league"
    )
    assert repeat_correlation == pytest.approx(1.0)
    assert repeat_count == 3
    assert 0.0 <= repeat_p_value <= 1.0


def test_within_test_sums_the_parts_of_each_unit(seasons_df: pd.DataFrame) -> None:
    cochran_q, degrees_of_freedom, p_value = units.within_test(
        seasons_df, UNIT, "part", "goals", "one", "count"
    )

    assert degrees_of_freedom == 2  # two units with two parts each
    assert cochran_q > 0

    alone = units.within_test(
        seasons_df[seasons_df[UNIT] == 1], UNIT, "part", "goals", "one", "count"
    )
    assert alone[0] == pytest.approx(0.0)
    assert alone[1] == 1
    assert 0.0 <= p_value <= 1.0


def test_within_row_tests_the_teams_around_their_league(round_robin_df: pd.DataFrame) -> None:
    team_rows_df = card.team_rows(round_robin_df)
    quantity = ("goals_for", "one", "goals scored", "count")

    row, result = units.within_row(team_rows_df, card.TEAM_LEAGUE, card.TEAM_UNIT, quantity)

    assert row["df"] == 8.0 - 2.0  # 8 teams in 2 leagues
    assert row["repeat n"] == 8.0
    assert isinstance(row["p"], str)

    against = result.part_values_df["shrunk"] - result.part_values_df["owner_mean"]
    assert float(row["shrunk - league min"]) == pytest.approx(against.min())

    luck = units.within_luck_row("goals scored", result)
    assert float(luck["luck min"]) <= float(luck["luck max"])


def test_null_q_has_the_mean_of_its_df(round_robin_df: pd.DataFrame) -> None:
    team_rows_df = card.team_rows(round_robin_df)
    quantity = ("goals_for", "one", "goals scored", "count")

    mean, standard_deviation = units.null_q(
        team_rows_df, card.TEAM_LEAGUE, card.TEAM_UNIT, quantity, draws=200
    )

    assert mean == pytest.approx(6.0, abs=1.0)  # 8 teams in 2 leagues
    assert standard_deviation > 0

    with pytest.raises(ValueError, match="no null draws"):
        units.null_q(
            team_rows_df, card.TEAM_LEAGUE, card.TEAM_UNIT, ("goals_1h", "goals", "x", "share")
        )


def test_null_q_of_an_event_has_the_mean_of_its_df(round_robin_df: pd.DataFrame) -> None:
    # The 0/1 draws of an event. Comebacks are too rare in these toy leagues to test this with;
    # being behind at half-time is not.
    team_rows_df = card.team_rows(round_robin_df)
    quantity = ("behind", "one", "behind at half-time", "event")

    mean, standard_deviation = units.null_q(
        team_rows_df, card.TEAM_LEAGUE, card.TEAM_UNIT, quantity, draws=200
    )

    assert mean == pytest.approx(6.0, abs=1.0)  # 8 teams in 2 leagues
    assert standard_deviation > 0


def test_within_tested_leaves_out_the_parts_that_tell_nothing() -> None:
    # Unit 1: part 1c expects nothing. Unit 2 has no events, so its parts tell nothing.
    unit_rows_df = pd.DataFrame(
        {
            UNIT: [1, 1, 1, 1, 1, 2, 2],
            "part": ["1a", "1a", "1b", "1b", "1c", "2a", "2b"],
            "won": [1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            "behind": [1.0, 1.0, 1.0, 1.0, 0.0, 1.0, 1.0],
        }
    )

    result = units.within_tested(unit_rows_df, UNIT, "part", "won", "behind", "event")

    assert result.part_values_df.index.tolist() == ["1a", "1b"]
    assert result.degrees_of_freedom == 1
    assert np.isfinite(result.cochran_q)


def test_shuffled_parts_stay_inside_their_unit_and_keep_their_size() -> None:
    unit = pd.Series([1, 2, 1, 2, 1, 2, 1])
    part = pd.Series(["a", "x", "a", "y", "b", "y", "c"])

    moved = units.shuffled_parts(unit, part, np.random.default_rng(0))

    for key in (1, 2):
        inside = (unit == key).to_numpy()
        assert sorted(moved[inside]) == sorted(part[inside]), key

    assert not (moved == part.to_numpy()).all()


def test_permuted_qs_fall_below_the_q_of_parts_that_really_differ() -> None:
    unit_rows_df = pd.DataFrame(
        {
            UNIT: [1] * 40,
            "part": ["low"] * 20 + ["high"] * 20,
            "goals": [0.0, 1.0] * 10 + [5.0, 6.0] * 10,
            "one": 1.0,
        }
    )

    quantity = ("goals", "one", "goals", "count")
    cochran_qs = units.permuted_qs(unit_rows_df, UNIT, "part", quantity, draws=30)

    assert cochran_qs.shape == (30,)

    real = units.within_tested(unit_rows_df, UNIT, "part", "goals", "one", "count").cochran_q
    assert (cochran_qs < real).all()


def test_variance_share_scales_tau2_by_the_expected_values() -> None:
    unit_rows_df = pd.DataFrame({"goals": [0.0, 2.0, 4.0, 9.0], "expected": [1.0, 1.0, 2.0, 0.0]})

    # The rows that count are the first three: variance of 0, 2, 4 is 4; mean of e^2 is 2.
    assert units.variance_share(unit_rows_df, "goals", "expected", 0.5) == pytest.approx(
        0.5 * 2 / 4
    )


def test_level_row_tests_the_parts_against_their_shuffles(round_robin_df: pd.DataFrame) -> None:
    team_rows_df = card.team_rows(round_robin_df)
    quantity = ("goals_for", "one", "goals scored", "count")

    row = units.level_row(team_rows_df, card.TEAM_LEAGUE, card.TEAM_UNIT, quantity, draws=20)

    assert row["parts"] == 8.0
    assert row["df"] == 6.0  # 8 teams in 2 leagues
    assert 1 / 21 <= float(row["p"]) <= 1.0
    assert isinstance(row["p chi2"], str)
    assert float(row["found share"]) > 0

    if float(row["Q"]) > float(row["shuffled mean"]):
        assert float(row["tau/pooled"]) > 0
    else:
        assert float(row["tau/pooled"]) == 0
