"""Toy data of the ML tests: the toy priced matches with every column that `ml/rows.py` reads."""

import numpy as np
import pandas as pd
import pytest

from ml import rows

TABLE_STATS = ("rank", "played", "won", "drawn", "lost", "goals_for", "goal_diff", "points")


@pytest.fixture
def toy_schedule_df(toy_priced_matches_df: pd.DataFrame) -> pd.DataFrame:
    """The five toy matches with the AH market, a kickoff, a round and every stage-3 column of
    `ml/rows.py`. The home side has played 0, 2, 4, 6 and 8 matches in each table, the away
    side 1, 3, 5, 7 and 9, and every other count equals played, so each per-match rate is 1.
    """

    schedule_df = toy_priced_matches_df.copy()
    schedule_df["s1_odds_ah_open_line"] = [-1.0, 0.0, -1.5, 0.25, -0.5]
    schedule_df["s1_odds_ah_open_home"] = 1.9
    schedule_df["s1_odds_ah_open_away"] = 1.9
    schedule_df["s2_implied_ah_home"] = [0.6, 0.5, 0.4, 0.45, 0.55]
    schedule_df["s1_round"] = [1, 2, 3, 4, 5]

    # Summer and winter kickoffs in Berlin time with their offsets: Sunday 15:30 and
    # Wednesday 20:45.
    schedule_df["s1_date"] = ["2024-08-04 15:30+02:00", "2025-01-15 20:45+01:00"] + [
        "2025-03-01 18:00+01:00"
    ] * 3

    played = {"home": np.arange(0, 10, 2), "away": np.arange(1, 10, 2)}
    columns: dict[str, np.ndarray] = {}
    for side, counts in played.items():
        columns |= table_columns(side, counts) | record_columns(side, counts)
    for column in rows.ROUND_SO_FAR:
        columns[column] = np.ones(len(schedule_df), dtype=int)
    columns["s3_pre_rank_gap"] = np.full(len(schedule_df), 3)

    return pd.concat([schedule_df, pd.DataFrame(columns, index=schedule_df.index)], axis=1)


def table_columns(side: str, counts: np.ndarray) -> dict[str, np.ndarray]:
    """Every table column of one side (S3.03), each equal to `counts`."""

    return {
        f"s3_{side}_pre_{half}_{venue}_{stat}": counts
        for half in rows.HALVES
        for venue in rows.VENUES
        for stat in TABLE_STATS
    }


def record_columns(side: str, counts: np.ndarray) -> dict[str, np.ndarray]:
    """Every HT/FT record column of one side (S3.08), each equal to `counts`, and its stakes
    (S3.11 to S3.13), each `counts` + 100."""

    records = {
        f"s3_{side}_pre_htft_{venue}_{ht}_{ft}": counts
        for venue in rows.VENUES
        for ht in rows.RESULTS
        for ft in rows.RESULTS
    }

    return records | {f"s3_{side}_{stake}": counts + 100 for stake in rows.STAKES}
