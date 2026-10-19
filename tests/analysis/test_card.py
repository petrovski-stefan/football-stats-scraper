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
    toy_priced_matches: pd.DataFrame,
) -> None:
    frame = yardstick.frame(toy_priced_matches, yardstick.build_grid(COARSE))
    frame["one"] = 1.0
    for observed, denominator, model, _, kind in card.ODDS_CARD:
        assert {observed, denominator, model} <= set(frame.columns)
        assert kind in {"event", "count"}


def test_card_frame_reads_the_stage_columns(toy_priced_matches: pd.DataFrame) -> None:
    frame = card.card_frame(toy_priced_matches)
    # Half-times 1-0, 0-0, 0-0, 1-0 and 0-1; full-time totals 2, 0, 1, 3 and 2.
    assert frame["home_behind"].tolist() == [0.0, 0.0, 0.0, 0.0, 1.0]
    assert frame["away_behind"].tolist() == [1.0, 0.0, 0.0, 1.0, 0.0]
    assert frame["ht_deficit"].tolist() == [1.0, 0.0, 0.0, 1.0, 1.0]
    assert frame["is_comeback_away"].tolist() == [0.0, 0.0, 0.0, 1.0, 0.0]
    assert frame["goals"].tolist() == [2.0, 0.0, 1.0, 3.0, 2.0]
    assert frame["cluster"].tolist() == [
        "1 2024",
        "1 2025",
        "2 2024-2025",
        "2 2025-2026",
        "2 2025-2026",
    ]
    columns = {column for row in card.CARD for column in row[:2]}
    assert columns <= set(frame.columns)


def test_team_rows_give_each_team_its_roles(toy_priced_matches: pd.DataFrame) -> None:
    rows = card.team_rows(toy_priced_matches)
    assert len(rows) == 2 * len(toy_priced_matches)
    team_21 = rows[rows["team"] == 21]  # behind away at 22 and wins; behind at home to 23
    assert team_21["behind"].sum() == 2.0
    assert team_21["comes_back"].sum() == 1.0
    assert team_21["comes_back_away"].sum() == 1.0
    team_22 = rows[rows["team"] == 22]  # ahead at home to 21, then loses
    assert team_22["loses_lead_home"].sum() == 1.0
    assert (rows["home"] + rows["away"]).tolist() == [1.0] * len(rows)
    assert set(rows[card.TEAM_UNIT]) == {"11 1", "12 1", "21 2", "22 2", "23 2"}


def test_team_rows_add_extra_columns_by_side(toy_priced_matches: pd.DataFrame) -> None:
    home_value = pd.Series(1.0, index=toy_priced_matches.index)
    rows = card.team_rows(toy_priced_matches, extra={"x": (home_value, 2.0 * home_value)})
    assert rows.loc[rows["home"] == 1.0, "x"].tolist() == [1.0] * 5
    assert rows.loc[rows["home"] == 0.0, "x"].tolist() == [2.0] * 5


@pytest.fixture
def team_yardstick(toy_priced_matches: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The team rows of the four priced toy matches, and the yardstick frame they come from."""
    frame = yardstick.frame(toy_priced_matches, yardstick.build_grid(COARSE))
    return card.team_yardstick_rows(toy_priced_matches, frame), frame


def test_each_team_gets_the_chances_of_its_own_side(
    team_yardstick: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    rows, frame = team_yardstick
    assert len(rows) == 2 * len(frame)
    home, away = rows[rows["home"] == 1.0], rows[rows["home"] == 0.0]
    assert home["m_comes_back"].tolist() == pytest.approx(frame["m_cb_home"].tolist())
    assert away["m_comes_back"].tolist() == pytest.approx(frame["m_cb_away"].tolist())
    assert home["m_loses_lead"].tolist() == pytest.approx(frame["m_cb_away"].tolist())
    assert away["m_ahead"].tolist() == pytest.approx(frame["m_home_behind"].tolist())
    assert home["m_goals_against"].tolist() == pytest.approx(frame["lam_away"].tolist())
    assert home["win_chance"].tolist() == pytest.approx(frame["shin_p_home"].tolist())


def test_the_completion_counts_only_from_the_right_half_time_state(
    team_yardstick: tuple[pd.DataFrame, pd.DataFrame],
) -> None:
    rows, _ = team_yardstick
    assert (rows.loc[rows["behind"] == 0.0, "m_wins_from_behind"] == 0.0).all()
    assert (rows.loc[rows["ahead"] == 0.0, "m_loses_from_ahead"] == 0.0).all()
    behind = rows[rows["behind"] == 1.0]
    assert behind["m_wins_from_behind"].tolist() == pytest.approx(behind["m_completion"].tolist())


def test_top_teams_rank_by_the_distance_from_the_league(round_robin: pd.DataFrame) -> None:
    rows = card.team_rows(round_robin)
    quantity = ("goals_for", "one", "goals scored", "count")
    _, result = units.within_row(rows, card.TEAM_LEAGUE, card.TEAM_UNIT, quantity)
    table = card.top_teams(rows, result.values, top=3)
    assert len(table) == 3
    distances = table["shrunk - league"].tolist()
    assert distances == sorted(distances, reverse=True)
    assert set(table.columns) >= {"team_name", "league_name", "rate", "league", "shrunk"}
    renamed = card.top_teams(rows, result.values, top=3, names=("observed", "expected", "O/E"))
    assert "O/E" in renamed.columns


def test_team_line_counts_the_units(round_robin: pd.DataFrame) -> None:
    line = card.team_line(card.team_rows(round_robin))
    assert line.startswith("8 team units (a team in one league) in 2 leagues; 96 team-matches")
