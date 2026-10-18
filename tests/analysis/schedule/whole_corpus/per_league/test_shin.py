"""`analysis/schedule/whole_corpus/per_league/shin.py`: the league table and the cohort check."""

import pandas as pd
import pytest

from analysis.methods import shin
from analysis.schedule.whole_corpus.per_league import shin as runner


def test_league_table_has_one_row_per_league_shrunk_toward_the_pool(
    toy_matches: pd.DataFrame,
) -> None:
    table, tests = runner.league_table(shin.scored(toy_matches))
    assert table["league"].tolist() == ["A", "B"]
    assert table["matches"].tolist() == [2, 2]
    for name in runner.QUANTITIES:
        pooled = tests[name].pooled
        for raw, shrunk in zip(table[name], table[f"{name}_shrunk"], strict=True):
            assert min(raw, pooled) - 1e-12 <= shrunk <= max(raw, pooled) + 1e-12


def test_cohort_stability_pairs_the_leagues_seen_in_both_cohorts(
    toy_matches: pd.DataFrame,
) -> None:
    r, n = runner.cohort_stability(shin.scored(toy_matches), "shin_z")
    assert n == 2
    # Two leagues are ranked the same way in both cohorts, or the opposite way.
    assert abs(r) == pytest.approx(1.0)
