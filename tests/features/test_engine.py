"""`features/engine.py`: the tie-aware position of a match within its round.

Only `round_position` is tested here. It is pure bookkeeping on kickoff times; the rest of
the module builds the study's features and is covered by its own `--self-check`.
"""

import pandas as pd

from features.engine import round_position


def test_round_position_handles_shared_kickoffs_and_stages() -> None:
    df = pd.DataFrame(
        {
            "league_name": ["test_league"] * 5,
            "season": ["2025-2026"] * 5,
            "stage": ["A", "A", "A", "A", "B"],
            "round": [1, 1, 1, 1, 1],
            "date": [
                "2026-01-03 15:00",
                "2026-01-03 15:00",
                "2026-01-03 17:30",
                "2026-01-03 20:00",
                "2026-01-03 15:00",  # stage B's round 1 is a different round
            ],
        }
    )
    position = round_position(df)
    assert position["earlier"].tolist() == [0, 0, 2, 3, 0]
    assert position["later"].tolist() == [2, 2, 1, 0, 0]
    assert position["slot"].tolist() == [1, 1, 2, 3, 1]
    assert position["slots"].tolist() == [3, 3, 3, 3, 1]
