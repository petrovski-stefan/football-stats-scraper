"""`analysis/schedule/whole_corpus/all/htft.py`: the observed cells, the table and the top N."""

import pandas as pd
import pytest

from analysis.methods import yardstick
from analysis.schedule.whole_corpus.all import htft as runner

SHARE = 0.45


@pytest.fixture
def toy_frame() -> pd.DataFrame:
    """Four matches in the shape `yardstick.frame` gives: HT/FT 1/1, X/X, 2/1 and 1/X."""
    return pd.DataFrame(
        {
            "match_id": ["m1", "m2", "m3", "m4"],
            "ht_margin": [1, 0, -1, 1],
            "goals_home": [2.0, 1.0, 2.0, 1.0],
            "goals_away": [0.0, 1.0, 1.0, 1.0],
            "lam_home": [1.6, 1.2, 1.1, 1.4],
            "lam_away": [0.9, 1.2, 1.5, 1.0],
            "is_comeback": [0.0, 0.0, 1.0, 0.0],
            "m_cb": [0.03, 0.05, 0.05, 0.04],
            "cluster": ["a", "a", "b", "b"],
        }
    )


def test_with_cells_marks_the_result_that_happened(toy_frame: pd.DataFrame) -> None:
    out = runner.with_cells(toy_frame, SHARE)

    assert out["o_1/1"].tolist() == [1.0, 0.0, 0.0, 0.0]
    assert out["o_X/X"].tolist() == [0.0, 1.0, 0.0, 0.0]
    assert out["o_2/1"].tolist() == [0.0, 0.0, 1.0, 0.0]
    assert out["o_1/X"].tolist() == [0.0, 0.0, 0.0, 1.0]

    observed = out[[f"o_{cell}" for cell in yardstick.HTFT]].sum(axis=1)
    assert observed.tolist() == [1.0, 1.0, 1.0, 1.0]


def test_cell_table_has_one_row_per_result(toy_frame: pd.DataFrame) -> None:
    table = runner.cell_table(runner.with_cells(toy_frame, SHARE))
    assert table["HT/FT"].tolist() == list(yardstick.HTFT)
    assert table["observed share"].sum() == pytest.approx(1.0)
    assert table["expected"].sum() == pytest.approx(4.0, abs=1e-5)


def test_top_n_takes_the_highest_chances_and_breaks_ties_by_match_id(
    toy_frame: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "TOP_N", (1, 3))
    table = runner.top_n(toy_frame, "is_comeback", "m_cb")
    assert table["hits"].tolist() == [0.0, 1.0]  # m2 and m3 tie at 0.05; m2 goes first
    assert table["yardstick"].tolist() == pytest.approx([0.05, 0.14 / 3])
    assert table["lift"].tolist() == pytest.approx([0.0, (1 / 3) / 0.25])
