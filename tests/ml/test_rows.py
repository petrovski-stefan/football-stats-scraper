"""`ml/rows.py`: the side rows and the fields of models A and B."""

import numpy as np
import pandas as pd
import pytest

from analysis.methods import yardstick
from ml import rows

COARSE = np.round(np.arange(0.1, 4.01, 0.1), 2)
PRICED = 4  # the fifth toy match has no draw price


@pytest.fixture
def built(toy_schedule: pd.DataFrame) -> tuple[pd.DataFrame, list[str], pd.DataFrame]:
    """The side rows of the toy schedule, model B's fields, and the yardstick frame."""
    frame = yardstick.frame(toy_schedule, yardstick.build_grid(COARSE))
    side_rows, fields = rows.side_rows(toy_schedule, frame)
    return side_rows, fields, frame


def test_two_rows_per_priced_match_home_first(
    built: tuple[pd.DataFrame, list[str], pd.DataFrame],
) -> None:
    side_rows, fields, _ = built
    assert len(side_rows) == 2 * PRICED
    assert side_rows["venue_home"].tolist() == [1.0] * PRICED + [0.0] * PRICED
    assert fields[: len(rows.ODDS)] == list(rows.ODDS)
    assert len(fields) == len(set(fields))


def test_no_outcome_and_no_team_id_is_a_field(
    built: tuple[pd.DataFrame, list[str], pd.DataFrame],
) -> None:
    _, fields, _ = built
    outcomes = {rows.TARGET, "behind", "ahead", "loses_lead", "goals_for", "goals_against"}
    assert not outcomes & set(fields)
    assert not {"team", "team_name", "s1_home_team_id", "s1_away_team_id"} & set(fields)
    assert not [field for field in fields if field.startswith(("s1_ft", "s1_ht", "s2_"))]


def test_odds_fields_take_the_view_of_the_side(
    built: tuple[pd.DataFrame, list[str], pd.DataFrame], toy_schedule: pd.DataFrame
) -> None:
    side_rows, _, frame = built
    away = side_rows.iloc[PRICED:]
    priced = toy_schedule.loc[frame.index]

    assert away["p_T"].tolist() == pytest.approx(frame["shin_p_away"].tolist())
    assert away["lam_O"].tolist() == pytest.approx(frame["lam_home"].tolist())
    assert away["ah_line_T"].tolist() == pytest.approx((-priced["s1_odds_ah_open_line"]).tolist())
    assert away["p_ah_T"].tolist() == pytest.approx((1 - priced["s2_implied_ah_home"]).tolist())
    assert away["m_cb_T"].tolist() == pytest.approx(away["m_comes_back"].tolist())


def test_table_fields_are_rates_per_match_played(
    built: tuple[pd.DataFrame, list[str], pd.DataFrame],
) -> None:
    side_rows, _, _ = built
    home, away = side_rows.iloc[:PRICED], side_rows.iloc[PRICED:]

    # The first match: the home side has played 0 matches, so its rates are empty.
    assert np.isnan(home["T_ft_total_won_pg"].iloc[0])
    assert home["T_ft_total_won_pg"].iloc[1:].tolist() == [1.0] * (PRICED - 1)
    assert home["T_ft_total_played"].tolist() == [0.0, 2.0, 4.0, 6.0]
    # The opponent of a home row is the away side, and the other way.
    assert home["O_ft_total_played"].tolist() == [1.0, 3.0, 5.0, 7.0]
    assert away["T_ft_total_played"].tolist() == [1.0, 3.0, 5.0, 7.0]
    # Every count equals the matches played, so the FT and HT counts cancel in the 2nd half.
    assert away["T_2h_home_goal_diff_pg"].tolist() == [0.0] * PRICED


def test_record_fields_and_stakes(built: tuple[pd.DataFrame, list[str], pd.DataFrame]) -> None:
    side_rows, _, _ = built
    away = side_rows.iloc[PRICED:]
    assert away["T_htft_away_l_w_pg"].tolist() == [1.0] * PRICED
    assert away["T_pre_matches_left"].tolist() == [101.0, 103.0, 105.0, 107.0]
    assert away["O_pre_matches_left"].tolist() == [100.0, 102.0, 104.0, 106.0]


def test_match_fields_read_the_kickoff_in_berlin_time(toy_schedule: pd.DataFrame) -> None:
    fields = rows.match_fields(toy_schedule)
    assert fields["weekday"].tolist()[:2] == [6.0, 2.0]  # Sunday, Wednesday
    assert fields["hour"].tolist()[:2] == [15.5, 20.75]
    assert fields["month"].tolist()[:2] == [8.0, 1.0]
    assert isinstance(fields[rows.LEAGUE].dtype, pd.CategoricalDtype)
    assert fields["s3_pre_rank_gap"].tolist() == [3.0] * len(toy_schedule)


def test_per_game_is_empty_before_the_first_match() -> None:
    rates = rows.per_game(pd.Series([3.0, 4.0]), pd.Series([0.0, 2.0]))
    assert np.isnan(rates.iloc[0])
    assert rates.iloc[1] == 2.0


def test_summary_counts_the_rows_and_fields(
    built: tuple[pd.DataFrame, list[str], pd.DataFrame],
) -> None:
    side_rows, fields, _ = built
    summary = rows.summary(side_rows, fields)
    assert summary["rows"] == 2 * PRICED
    assert summary["fields A"] == len(rows.ODDS)
    assert summary["fields B"] == len(fields)
    assert 0.0 < summary["empty share of B"] < 1.0
