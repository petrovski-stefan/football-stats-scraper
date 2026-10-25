"""`analysis/schedule/whole_corpus/all/shin.py`: the pooled summary and the price-band table."""

import pandas as pd
import pytest

from analysis.methods import shin
from analysis.schedule.whole_corpus.all import shin as runner


def test_summary_counts_matches_and_orders_z(toy_matches_df: pd.DataFrame) -> None:
    scored_df = shin.scored(toy_matches_df)
    values = runner.summary(scored_df)
    assert values["matches"] == len(scored_df) == 4
    assert values["z_q1"] <= values["z_median"] <= values["z_q3"]
    assert values["ll_gain"] == pytest.approx(scored_df["ll_gain"].mean())
    assert values["ll_gain_low"] <= values["ll_gain_high"]


def test_price_table_counts_every_outcome_once(toy_matches_df: pd.DataFrame) -> None:
    scored_df = shin.scored(toy_matches_df)
    price_table_df = runner.price_table(scored_df)
    assert price_table_df["outcomes"].sum() == 3 * len(scored_df)
    assert len(price_table_df) <= len(shin.PRICE_EDGES) - 1

    # Exactly one of the three outcomes of each match happens.
    assert round((price_table_df["observed"] * price_table_df["outcomes"]).sum()) == len(scored_df)
