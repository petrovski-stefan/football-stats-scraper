"""`analysis/corpus.py`: loading toy stage-3 files, the corpus line and the 1X2 outcome."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from analysis import corpus
from domain import paths
from features.stage_io import write_stage_csv


def _write(tmp_path: Path, league_id: int, season: str, n: int) -> str:
    frame = pd.DataFrame(
        {
            "match_id": [f"{league_id}-{season}-{i}" for i in range(n)],
            "s1_league_id": [league_id] * n,
            "s1_season": [season] * n,
        }
    )

    path = str(tmp_path / f"league{league_id}_{season}_schedule.csv")
    write_stage_csv(frame, path, list(frame.columns))

    return path


def test_load_adds_the_season_cohort_and_keeps_the_season_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = [_write(tmp_path, 1, "2024-2025", 2), _write(tmp_path, 2, "2025", 1)]
    monkeypatch.setattr(paths, "schedule_csvs", lambda stage: files)
    loaded = corpus.load()
    assert loaded["s1_season"].tolist() == ["2024-2025", "2024-2025", "2025"]
    assert loaded["season_cohort"].tolist() == [2024, 2024, 2025]


def test_load_without_files_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths, "schedule_csvs", lambda stage: [])
    with pytest.raises(FileNotFoundError):
        corpus.load()


def test_corpus_line_counts_league_seasons_and_matches() -> None:
    frame = pd.DataFrame(
        {"s1_league_id": [1, 1, 2, 2], "s1_season": ["2024-2025", "2025-2026", "2025", "2025"]}
    )
    line = corpus.corpus_line(frame, date(2026, 10, 16))
    assert line == "Corpus 2026-10-16: 3 league-seasons, 4 matches"


def test_outcome_1x2_codes() -> None:
    frame = pd.DataFrame({"s1_ft_home_goals": [2, 1, 0], "s1_ft_away_goals": [1, 1, 3]})
    assert corpus.outcome_1x2(frame).tolist() == [corpus.HOME, corpus.DRAW, corpus.AWAY]


def test_round_key_names_the_league_season_stage_and_round() -> None:
    frame = pd.DataFrame(
        {
            "s1_league_id": [7, 7, 7],
            "s1_season": ["2025", "2025", "2025"],
            "s1_stage": ["Apertura", "Clausura", None],
            "s1_round": [3, 3, 3],
        }
    )

    assert corpus.round_key(frame).tolist() == [
        "7 2025 Apertura 3",
        "7 2025 Clausura 3",
        "7 2025  3",
    ]
