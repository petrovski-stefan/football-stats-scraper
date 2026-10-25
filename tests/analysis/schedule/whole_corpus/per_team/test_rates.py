"""`analysis/schedule/whole_corpus/per_team/rates.py`: its quantities.

The team rows, the tests and the tables are `analysis/card.py` and `analysis/units.py`, tested
in `tests/analysis/test_card.py` and `tests/analysis/test_units.py`.
"""

import pandas as pd

from analysis import card
from analysis.schedule.whole_corpus.per_team import rates as runner


def test_the_quantities_read_columns_of_the_team_rows(toy_priced_matches_df: pd.DataFrame) -> None:
    team_rows_df = card.team_rows(toy_priced_matches_df)
    for numerator, denominator, _, _ in runner.QUANTITIES:
        assert {numerator, denominator} <= set(team_rows_df.columns), (numerator, denominator)
    assert set(runner.RANKED) <= {label for _, _, label, _ in runner.QUANTITIES}
