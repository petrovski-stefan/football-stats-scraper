"""`qa/validate.py`: the checks across the staged files (`validate_corpus`). The per-file
checks it runs are tested in their own modules."""

import json
import os
from pathlib import Path

import pandas as pd
import pytest

from domain import paths
from qa.validate import validate_corpus


def _schedule(stage: int, league: str, season: str, ids: list[str], league_id: int = 1) -> str:
    """A staged schedule file holding only the columns the corpus checks read."""

    path = paths.schedule_path(stage, league, season)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pd.DataFrame({"match_id": ids, "s1_league_id": league_id}).to_csv(path, index=False)
    return path


def _config(league_ids: list[int]) -> None:
    os.makedirs(os.path.dirname(paths.LEAGUES_FILE), exist_ok=True)
    with open(paths.LEAGUES_FILE, "w", encoding="utf-8") as config_file:
        json.dump([{"league_id": league_id} for league_id in league_ids], config_file)


@pytest.fixture
def corpus(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Two league-seasons of one configured league, each at all three stages."""

    monkeypatch.chdir(tmp_path)
    _config([1])
    raw = [
        _schedule(1, "test_league", "2024", ["a1", "a2"]),
        _schedule(1, "test_league", "2025", ["b1", "b2"]),
    ]

    for stage in (2, 3):
        _schedule(stage, "test_league", "2024", ["a1", "a2"])
        _schedule(stage, "test_league", "2025", ["b1", "b2"])

    return raw


def test_a_clean_corpus_passes(corpus: list[str]) -> None:
    assert validate_corpus(corpus)


def test_a_match_in_two_league_seasons_fails(
    corpus: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    _schedule(1, "test_league", "2025", ["b1", "a1"])
    assert not validate_corpus(corpus)
    assert "match_id values in more than one file" in capsys.readouterr().out


def test_a_league_missing_from_the_config_fails(
    corpus: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    corpus.append(_schedule(1, "other_league", "2025", ["c1"], league_id=2))
    for stage in (2, 3):
        _schedule(stage, "other_league", "2025", ["c1"], league_id=2)
    assert not validate_corpus(corpus)
    assert "league id not in" in capsys.readouterr().out


def test_a_derived_file_without_its_stage_1_file_fails(
    corpus: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    _schedule(3, "test_league", "2023", ["z1"])
    assert not validate_corpus(corpus)
    assert "stage-3 files without a stage-1 file" in capsys.readouterr().out


def test_a_missing_config_fails(corpus: list[str], capsys: pytest.CaptureFixture[str]) -> None:
    os.remove(paths.LEAGUES_FILE)
    assert not validate_corpus(corpus)
    assert "the leagues go unchecked" in capsys.readouterr().out
