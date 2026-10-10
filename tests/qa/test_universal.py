"""`qa/universal.py`: the checks that hold for any table the project writes."""

import numpy as np
import pandas as pd

from qa import universal
from qa.report import Report


def _report() -> Report:
    return Report("test subject")


def test_check_not_empty() -> None:
    r = _report()
    universal.check_not_empty(r, pd.DataFrame({"a": [1]}))
    assert r.ok
    universal.check_not_empty(r, pd.DataFrame({"a": []}))
    assert not r.ok


def test_check_required_columns() -> None:
    r = _report()
    universal.check_required_columns(r, pd.DataFrame({"a": [1]}), ["a"])
    assert r.ok
    universal.check_required_columns(r, pd.DataFrame({"a": [1]}), ["a", "b", "c"])
    assert r.issues == ["2 declared column(s) missing: ['b', 'c']"]


def test_check_primary_key_passes_unique_ids() -> None:
    r = _report()
    universal.check_primary_key(r, pd.DataFrame({"match_id": ["1", "2", "3"]}))
    assert r.ok


def test_check_primary_key_missing_column() -> None:
    r = _report()
    universal.check_primary_key(r, pd.DataFrame({"other": [1]}))
    assert r.issues == ["missing primary key column 'match_id'"]


def test_check_primary_key_null_blank_and_duplicate() -> None:
    r = _report()
    # " 1" and 1 normalise to the same id, so they count as a duplicate.
    ids = pd.DataFrame({"match_id": [1, " 1", None, " "]}, dtype=object)
    universal.check_primary_key(r, ids)
    assert r.issues == [
        "1 rows with a null match_id",
        "1 rows with a blank match_id",
        "1 duplicate match_id",
    ]


def test_check_unique_across() -> None:
    r = _report()
    # A repeat inside one file is `check_primary_key`'s job, not this check's.
    universal.check_unique_across(r, {"a.csv": ["1", "2", "2"], "b.csv": ["3"]})
    assert r.ok
    universal.check_unique_across(r, {"a.csv": ["1", "2"], "b.csv": ["2", "3"]})
    assert r.issues == ["1 match_id values in more than one file, e.g. 2 in ['a.csv', 'b.csv']"]


def test_check_declared() -> None:
    r = _report()
    universal.check_declared(r, {"a.csv": ["1", "1"], "b.csv": ["2"]}, {"1", "2", "3"}, "stray id")
    assert r.ok
    universal.check_declared(r, {"a.csv": ["1"], "b.csv": ["2", "4"]}, {"1", "2"}, "stray id")
    assert r.issues == ["1 files with a stray id ['b.csv']"]


def test_check_no_dead_columns() -> None:
    frame = pd.DataFrame({"full": [1, 2], "dead": [np.nan, np.nan]})
    r = _report()
    universal.check_no_dead_columns(r, frame)
    assert len(r.issues) == 1
    assert "['dead']" in r.issues[0]

    r = _report()
    universal.check_no_dead_columns(r, frame, optional={"dead"})
    assert r.ok


def test_check_no_dead_columns_respects_the_threshold() -> None:
    half_empty = pd.DataFrame({"half": [1, np.nan]})
    r = _report()
    universal.check_no_dead_columns(r, half_empty, threshold=0.6)
    assert r.ok
    universal.check_no_dead_columns(r, half_empty, threshold=0.5)
    assert not r.ok


def test_check_ids_covered() -> None:
    r = _report()
    universal.check_ids_covered(r, {"1", "2"}, {"1", "2", "3"}, "the store")
    assert r.ok
    universal.check_ids_covered(r, {"1", "4"}, {"1"}, "the store")
    assert r.issues == ["1 ids missing from the store"]


def test_check_attempt_log_agreeing() -> None:
    rows = pd.DataFrame({"match_id": ["1", "1", "2"]})
    done = pd.DataFrame({"match_id": ["1", "2", "3"], "goals": [2, 1, 0]})
    r = _report()
    universal.check_attempt_log(r, rows, done, "goals")
    assert r.ok


def test_check_attempt_log_catches_each_disagreement() -> None:
    rows = pd.DataFrame({"match_id": ["1", "1", "5"]})
    done = pd.DataFrame({"match_id": ["1", "1"], "goals": [1, 1]})
    r = _report()
    universal.check_attempt_log(r, rows, done, "goals")
    assert r.issues == [
        "1 duplicate match_id in the attempt log (would re-scrape)",
        "1 matches have rows but no attempt-log entry",
        "1 matches where the attempt log's goals disagrees with the rows",
    ]
