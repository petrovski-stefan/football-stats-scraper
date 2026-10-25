"""`qa/report.py`: collecting failures and printing one verdict."""

import pytest

from qa.report import Report


def test_report_records_only_failures() -> None:
    report = Report("test subject")
    report.check(True, "never recorded")
    report.check(False, "first failure")
    assert report.issues == ["first failure"]
    assert report.ok is False


def test_fail_always_records_its_message() -> None:
    report = Report("test subject")
    report.fail("a failure")
    assert report.issues == ["a failure"]
    assert report.ok is False


def test_flush_prints_the_verdict(capsys: pytest.CaptureFixture[str]) -> None:
    passing, failing = Report("clean"), Report("broken")
    failing.check(False, "a problem")

    assert passing.flush() is True
    assert failing.flush() is False

    out = capsys.readouterr().out
    assert "[PASS] clean" in out
    assert "[FAIL (1)] broken" in out
    assert "- a problem" in out
