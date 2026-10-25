"""`qa/universal.py`: the checks that hold for any table the project writes."""

import numpy as np
import pandas as pd

from qa import universal
from qa.report import Report


def _report() -> Report:
    """An empty report to check against."""

    return Report("test subject")


def test_check_not_empty_fails_an_empty_table() -> None:
    report = _report()
    universal.check_not_empty(report, pd.DataFrame({"a": [1]}))
    assert report.ok
    universal.check_not_empty(report, pd.DataFrame({"a": []}))
    assert not report.ok


def test_check_required_columns_names_the_missing_ones() -> None:
    report = _report()
    universal.check_required_columns(report, pd.DataFrame({"a": [1]}), ["a"])
    assert report.ok
    universal.check_required_columns(report, pd.DataFrame({"a": [1]}), ["a", "b", "c"])
    assert report.issues == ["2 declared column(s) missing: ['b', 'c']"]


def test_check_primary_key_passes_unique_ids() -> None:
    report = _report()
    universal.check_primary_key(report, pd.DataFrame({"match_id": ["1", "2", "3"]}))
    assert report.ok


def test_check_primary_key_missing_column() -> None:
    report = _report()
    universal.check_primary_key(report, pd.DataFrame({"other": [1]}))
    assert report.issues == ["missing primary key column 'match_id'"]


def test_check_primary_key_null_blank_and_duplicate() -> None:
    report = _report()

    # " 1" and 1 normalise to the same id, so they count as a duplicate.
    ids_df = pd.DataFrame({"match_id": [1, " 1", None, " "]}, dtype=object)
    universal.check_primary_key(report, ids_df)

    assert report.issues == [
        "1 rows with a null match_id",
        "1 rows with a blank match_id",
        "1 duplicate match_id",
    ]


def test_check_unique_across_fails_an_id_in_two_files() -> None:
    report = _report()

    # A repeat inside one file is `check_primary_key`'s job, not this check's.
    universal.check_unique_across(report, {"a.csv": ["1", "2", "2"], "b.csv": ["3"]})
    assert report.ok

    universal.check_unique_across(report, {"a.csv": ["1", "2"], "b.csv": ["2", "3"]})
    assert report.issues == [
        "1 match_id values in more than one file, e.g. 2 in ['a.csv', 'b.csv']"
    ]


def test_check_declared_names_the_files_with_an_undeclared_id() -> None:
    report = _report()
    universal.check_declared(
        report, {"a.csv": ["1", "1"], "b.csv": ["2"]}, {"1", "2", "3"}, "stray id"
    )
    assert report.ok
    universal.check_declared(report, {"a.csv": ["1"], "b.csv": ["2", "4"]}, {"1", "2"}, "stray id")
    assert report.issues == ["1 files with a stray id ['b.csv']"]


def test_check_no_dead_columns() -> None:
    with_dead_column_df = pd.DataFrame({"full": [1, 2], "dead": [np.nan, np.nan]})
    report = _report()
    universal.check_no_dead_columns(report, with_dead_column_df)

    assert len(report.issues) == 1
    assert "['dead']" in report.issues[0]

    report = _report()
    universal.check_no_dead_columns(report, with_dead_column_df, optional={"dead"})

    assert report.ok


def test_check_no_dead_columns_leaves_an_empty_table_to_check_not_empty() -> None:
    report = _report()
    universal.check_no_dead_columns(report, pd.DataFrame({"a": []}))
    assert report.ok


def test_check_no_dead_columns_respects_the_threshold() -> None:
    half_empty_df = pd.DataFrame({"half": [1, np.nan]})
    report = _report()
    universal.check_no_dead_columns(report, half_empty_df, threshold=0.6)
    assert report.ok
    universal.check_no_dead_columns(report, half_empty_df, threshold=0.5)
    assert not report.ok


def test_check_ids_covered_counts_the_ids_missing_from_the_store() -> None:
    report = _report()
    universal.check_ids_covered(report, {"1", "2"}, {"1", "2", "3"}, "the store")
    assert report.ok
    universal.check_ids_covered(report, {"1", "4"}, {"1"}, "the store")
    assert report.issues == ["1 ids missing from the store"]


def test_check_attempt_log_agreeing() -> None:
    store_df = pd.DataFrame({"match_id": ["1", "1", "2"]})
    attempt_log_df = pd.DataFrame({"match_id": ["1", "2", "3"], "goals": [2, 1, 0]})
    report = _report()
    universal.check_attempt_log(report, store_df, attempt_log_df, "goals")
    assert report.ok


def test_check_attempt_log_catches_each_disagreement() -> None:
    store_df = pd.DataFrame({"match_id": ["1", "1", "5"]})
    attempt_log_df = pd.DataFrame({"match_id": ["1", "1"], "goals": [1, 1]})
    report = _report()
    universal.check_attempt_log(report, store_df, attempt_log_df, "goals")

    assert report.issues == [
        "1 duplicate match_id in the attempt log (would re-scrape)",
        "1 matches have rows but no attempt-log entry",
        "1 matches where the attempt log's goals disagrees with the rows",
    ]
