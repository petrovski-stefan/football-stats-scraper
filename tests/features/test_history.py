"""`features/history.py`: reading one cell of a fixture's history blocks, and column names.

The friendly marker and year cutoff come from `domain.scope`, so these tests check the
mechanism and not the chosen values.
"""

import numpy as np
import pandas as pd
import pytest

from domain.scope import FRIENDLY_MARKER, HISTORY_FROM_YEAR
from features import history

PREFIX = "home_last1_"


def _block(**cells: object) -> pd.DataFrame:
    """A one-fixture frame holding a single history block's cells."""

    return pd.DataFrame({f"{PREFIX}{name}": [value] for name, value in cells.items()})


@pytest.mark.parametrize(
    ("value", "text"),
    [
        (2789133.0, "2789133"),  # an id read as float because the column had gaps
        (" Test League ", "Test League"),
        (np.nan, ""),
        (None, ""),
    ],
)
def test_cell(value: object, text: str) -> None:
    assert history.cell(_block(match_id=value), f"{PREFIX}match_id", 0) == text


def test_cell_of_a_missing_column_is_empty() -> None:
    assert history.cell(_block(match_id="1"), f"{PREFIX}league", 0) == ""


@pytest.mark.parametrize(
    ("value", "home"),
    [(True, True), ("True", True), (1.0, True), (False, False), ("False", False), (np.nan, None)],
)
def test_subject_is_home(value: object, home: bool | None) -> None:
    assert history.subject_is_home(_block(is_home=value), PREFIX, 0) is home


@pytest.mark.parametrize(
    ("league", "date", "key"),
    [
        ("Test League", f"{HISTORY_FROM_YEAR}-03-01 15:00:00", "7"),
        (f"Test {FRIENDLY_MARKER}", f"{HISTORY_FROM_YEAR}-03-01 15:00:00", None),
        ("Test League", f"{HISTORY_FROM_YEAR - 1}-03-01 15:00:00", None),
    ],
)
def test_match_key(league: str, date: str, key: str | None) -> None:
    detail_df = _block(match_id=7, league=league, date=date)
    assert history.match_key(detail_df, PREFIX, 0) == key


def test_match_key_without_an_id() -> None:
    assert history.match_key(_block(match_id=None), PREFIX, 0) is None


def test_score_matches() -> None:
    detail_df = _block(ft_home_goals=2, ft_away_goals=1)
    assert history.score_matches(detail_df, PREFIX, 0, 2, 1) is True
    assert history.score_matches(detail_df, PREFIX, 0, 1, 1) is False
    # No stored score to check against: treated as usable.
    assert history.score_matches(_block(match_id=7), PREFIX, 0, 0, 0) is True


def test_feature_names() -> None:
    assert history.feature_names(["a", "b"]) == [
        "home_a",
        "home_b",
        "away_a",
        "away_b",
        "h2h_a",
        "h2h_b",
    ]


def test_timeline_names() -> None:
    assert history.timeline_names("x", 2) == [
        "home_last1_x",
        "home_last2_x",
        "away_last1_x",
        "away_last2_x",
        "h2h_last1_x",
        "h2h_last2_x",
    ]
