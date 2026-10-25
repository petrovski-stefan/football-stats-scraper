"""`analysis/card.py`: the card's quantities and the outcomes of each match."""

import numpy as np
import pandas as pd
import pytest

from analysis import card, units
from analysis.methods import yardstick

COARSE = np.round(np.arange(0.1, 4.01, 0.1), 2)


def test_each_card_row_has_a_known_kind_and_one_label() -> None:
    labels = [label for _, _, label, _ in card.CARD]
    assert len(labels) == len(set(labels))
    assert {kind for *_, kind in card.CARD} <= {"event", "count"}


def test_the_odds_card_reads_columns_of_the_yardstick_frame(
    toy_priced_matches_df: pd.DataFrame,
) -> None:
    yardstick_df = yardstick.frame(toy_priced_matches_df, yardstick.build_grid(COARSE))
    yardstick_df["one"] = 1.0
    for observed, denominator, model, _, kind in card.ODDS_CARD:
        assert {observed, denominator, model} <= set(yardstick_df.columns), (
            observed,
            denominator,
            model,
            kind,
        )
        assert kind in {"event", "count"}, (observed, denominator, model, kind)


def test_card_frame_reads_the_stage_columns(toy_priced_matches_df: pd.DataFrame) -> None:
    card_df = card.card_frame(toy_priced_matches_df)

    # Half-times 1-0, 0-0, 0-0, 1-0 and 0-1; full-time totals 2, 0, 1, 3 and 2.
    assert card_df["home_behind"].tolist() == [0.0, 0.0, 0.0, 0.0, 1.0]
    assert card_df["away_behind"].tolist() == [1.0, 0.0, 0.0, 1.0, 0.0]
    assert card_df["ht_deficit"].tolist() == [1.0, 0.0, 0.0, 1.0, 1.0]
    assert card_df["is_comeback_away"].tolist() == [0.0, 0.0, 0.0, 1.0, 0.0]
    assert card_df["goals"].tolist() == [2.0, 0.0, 1.0, 3.0, 2.0]
    assert card_df["cluster"].tolist() == [
        "1 2024",
        "1 2025",
        "2 2024-2025",
        "2 2025-2026",
        "2 2025-2026",
    ]

    columns: set[str] = set()
    for row in card.CARD:
        columns.update(row[:2])

    assert columns <= set(card_df.columns)


def test_team_rows_give_each_team_its_roles(toy_priced_matches_df: pd.DataFrame) -> None:
    team_rows_df = card.team_rows(toy_priced_matches_df)

    assert len(team_rows_df) == 2 * len(toy_priced_matches_df)

    team_21_df = team_rows_df[
        team_rows_df["team"] == 21
    ]  # behind away at 22 and wins; behind at home to 23
    assert team_21_df["behind"].sum() == 2.0
    assert team_21_df["comes_back"].sum() == 1.0
    assert team_21_df["comes_back_away"].sum() == 1.0

    team_22_df = team_rows_df[team_rows_df["team"] == 22]  # ahead at home to 21, then loses
    assert team_22_df["loses_lead_home"].sum() == 1.0

    assert (team_rows_df["home"] + team_rows_df["away"]).tolist() == [1.0] * len(team_rows_df)
    assert set(team_rows_df[card.TEAM_UNIT]) == {"11 1", "12 1", "21 2", "22 2", "23 2"}


def test_team_rows_add_extra_columns_by_side(toy_priced_matches_df: pd.DataFrame) -> None:
    home_value = pd.Series(1.0, index=toy_priced_matches_df.index)
    team_rows_df = card.team_rows(
        toy_priced_matches_df, extra={"x": (home_value, 2.0 * home_value)}
    )
    assert team_rows_df.loc[team_rows_df["home"] == 1.0, "x"].tolist() == [1.0] * 5
    assert team_rows_df.loc[team_rows_df["home"] == 0.0, "x"].tolist() == [2.0] * 5


@pytest.fixture
def team_yardstick(toy_priced_matches_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The team rows of the four priced toy matches, and the yardstick frame they come from."""

    yardstick_df = yardstick.frame(toy_priced_matches_df, yardstick.build_grid(COARSE))

    return card.team_yardstick_rows(toy_priced_matches_df, yardstick_df), yardstick_df


def test_each_team_gets_the_chances_of_its_own_side(
    team_yardstick: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    team_rows_df, yardstick_df = team_yardstick

    assert len(team_rows_df) == 2 * len(yardstick_df)
    home_rows_df, away_rows_df = (
        team_rows_df[team_rows_df["home"] == 1.0],
        team_rows_df[team_rows_df["home"] == 0.0],
    )
    assert home_rows_df["m_comes_back"].tolist() == pytest.approx(
        yardstick_df["m_cb_home"].tolist()
    )
    assert away_rows_df["m_comes_back"].tolist() == pytest.approx(
        yardstick_df["m_cb_away"].tolist()
    )
    assert home_rows_df["m_loses_lead"].tolist() == pytest.approx(
        yardstick_df["m_cb_away"].tolist()
    )
    assert away_rows_df["m_ahead"].tolist() == pytest.approx(yardstick_df["m_home_behind"].tolist())
    assert home_rows_df["m_goals_against"].tolist() == pytest.approx(
        yardstick_df["lam_away"].tolist()
    )
    assert home_rows_df["win_chance"].tolist() == pytest.approx(
        yardstick_df["shin_p_home"].tolist()
    )


def test_the_completion_counts_only_from_the_right_half_time_state(
    team_yardstick: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    team_rows_df, _ = team_yardstick

    assert (team_rows_df.loc[team_rows_df["behind"] == 0.0, "m_wins_from_behind"] == 0.0).all()
    assert (team_rows_df.loc[team_rows_df["ahead"] == 0.0, "m_loses_from_ahead"] == 0.0).all()

    behind_df = team_rows_df[team_rows_df["behind"] == 1.0]
    assert behind_df["m_wins_from_behind"].tolist() == pytest.approx(
        behind_df["m_completion"].tolist()
    )


def test_top_teams_rank_by_the_distance_from_the_league(round_robin_df: pd.DataFrame) -> None:
    team_rows_df = card.team_rows(round_robin_df)
    quantity = ("goals_for", "one", "goals scored", "count")
    _, result = units.within_row(team_rows_df, card.TEAM_LEAGUE, card.TEAM_UNIT, quantity)

    top_teams_df = card.top_teams(team_rows_df, result.part_values_df, top=3)

    assert len(top_teams_df) == 3
    distances = top_teams_df["shrunk - league"].tolist()
    assert distances == sorted(distances, reverse=True)
    assert set(top_teams_df.columns) >= {"team_name", "league_name", "rate", "league", "shrunk"}

    renamed_df = card.top_teams(
        team_rows_df, result.part_values_df, top=3, names=("observed", "expected", "O/E")
    )
    assert "O/E" in renamed_df.columns


def test_team_line_counts_the_units(round_robin_df: pd.DataFrame) -> None:
    line = card.team_line(card.team_rows(round_robin_df))
    assert line.startswith("8 team units (a team in one league) in 2 leagues; 96 team-matches")
