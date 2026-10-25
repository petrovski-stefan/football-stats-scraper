"""`qa/detail.py`: the order of the per-match history blocks."""

import pandas as pd

from qa import detail
from qa.report import Report


def _report_on(history_dates: dict[str, list[str | None]]) -> Report:
    """The report of the detail checks on a file that holds only these history date columns."""

    report = Report("test subject")
    detail.validate(report, pd.DataFrame(history_dates))

    return report


def test_a_history_date_that_does_not_parse_fails() -> None:
    report = _report_on({"home_last1_date": ["not a date"], "home_last2_date": ["2025-01-01"]})
    assert report.issues == ["1 home history dates that do not parse (left out of the order check)"]


def test_a_missing_history_date_is_not_a_parse_failure() -> None:
    report = _report_on({"home_last1_date": [None], "home_last2_date": ["2025-01-01"]})
    assert report.ok
