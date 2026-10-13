"""`modelling/runs.py`: a run's printed output is copied into `notes/runs/`."""

import os
from datetime import date
from pathlib import Path

import pytest

from modelling.runs import RUNS_DIR, recorded


@pytest.fixture
def in_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _record(name: str) -> str:
    return os.path.join(RUNS_DIR, f"{date.today().isoformat()}_{name}.txt")


def test_the_output_reaches_the_terminal_and_the_run_file(
    in_tmp: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with recorded("study") as path:
        print("hello")
    assert path == _record("study")
    with open(path, encoding="utf-8") as fh:
        assert fh.read() == "hello\n"
    out = capsys.readouterr().out
    assert "hello" in out
    assert f"wrote {path}" in out


def test_a_failed_run_keeps_its_transcript(in_tmp: Path) -> None:
    with pytest.raises(RuntimeError), recorded("broken"):
        print("before the error")
        raise RuntimeError("stop")
    with open(_record("broken"), encoding="utf-8") as fh:
        assert fh.read() == "before the error\n"


def test_a_rerun_the_same_day_overwrites_the_file(in_tmp: Path) -> None:
    with recorded("study"):
        print("first")
    with recorded("study"):
        print("second")
    with open(_record("study"), encoding="utf-8") as fh:
        assert fh.read() == "second\n"
