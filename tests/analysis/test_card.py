"""`analysis/card.py`: the card's quantities and the outcomes of each match."""

import pandas as pd

from analysis import card


def test_each_card_row_has_a_known_kind_and_one_label() -> None:
    labels = [label for _, _, label, _ in card.CARD]
    assert len(labels) == len(set(labels))
    assert {kind for *_, kind in card.CARD} <= {"event", "count"}


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
