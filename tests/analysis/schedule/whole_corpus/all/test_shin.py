"""`analysis/schedule/whole_corpus/all/shin.py`: the pooled summary and the price-band table."""

import pandas as pd
import pytest

from analysis.methods import shin
from analysis.schedule.whole_corpus.all import shin as runner


def test_summary_counts_matches_and_orders_z(toy_matches: pd.DataFrame) -> None:
    frame = shin.scored(toy_matches)
    values = runner.summary(frame)
    assert values["matches"] == len(frame) == 4
    assert values["z_q1"] <= values["z_median"] <= values["z_q3"]
    assert values["ll_gain"] == pytest.approx(frame["ll_gain"].mean())
    assert values["ll_gain_low"] <= values["ll_gain_high"]


def test_price_table_counts_every_outcome_once(toy_matches: pd.DataFrame) -> None:
    frame = shin.scored(toy_matches)
    table = runner.price_table(frame)
    assert table["outcomes"].sum() == 3 * len(frame)
    assert len(table) <= len(shin.PRICE_EDGES) - 1
    # Exactly one of the three outcomes of each match happens.
    assert round((table["observed"] * table["outcomes"]).sum()) == len(frame)
