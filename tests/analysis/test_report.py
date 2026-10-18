"""`analysis/report.py`: the shared table printer."""

import pandas as pd
import pytest

from analysis import report


def test_show_prints_the_title_then_the_table(capsys: pytest.CaptureFixture[str]) -> None:
    report.show("Title", pd.DataFrame({"name": ["a"], "value": [0.123456]}))
    lines = capsys.readouterr().out.splitlines()
    assert lines[:2] == ["", "== Title"]
    assert lines[-1].split() == ["a", "0.1235"]
