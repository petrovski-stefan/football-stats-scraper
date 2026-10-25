"""`analysis/corpus.py`: loading toy stage-3 files, the corpus line and the 1X2 outcome."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from analysis import corpus
from domain import paths
from features.stage_io import write_stage_csv


def _write(tmp_path: Path, league_id: int, season: str, match_count: int) -> str:
    """Write a stage file of `match_count` matches of one league-season; return its path."""

    stage_file_df = pd.DataFrame(
        {
            "match_id": [f"{league_id}-{season}-{i}" for i in range(match_count)],
            "s1_league_id": [league_id] * match_count,
            "s1_season": [season] * match_count,
        }
    )

    path = str(tmp_path / f"league{league_id}_{season}_schedule.csv")
    write_stage_csv(stage_file_df, path, list(stage_file_df.columns))

    return path


def test_load_adds_the_season_cohort_and_keeps_the_season_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = [_write(tmp_path, 1, "2024-2025", 2), _write(tmp_path, 2, "2025", 1)]
    monkeypatch.setattr(paths, "schedule_csvs", lambda stage: files)
    corpus_df = corpus.load()
    assert corpus_df["s1_season"].tolist() == ["2024-2025", "2024-2025", "2025"]
    assert corpus_df["season_cohort"].tolist() == [2024, 2024, 2025]


def test_load_without_files_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(paths, "schedule_csvs", lambda stage: [])
    with pytest.raises(FileNotFoundError):
        corpus.load()


def test_corpus_line_counts_league_seasons_and_matches() -> None:
    corpus_df = pd.DataFrame(
        {"s1_league_id": [1, 1, 2, 2], "s1_season": ["2024-2025", "2025-2026", "2025", "2025"]}
    )
    line = corpus.corpus_line(corpus_df, date(2026, 10, 16))
    assert line == "Corpus 2026-10-16: 3 league-seasons, 4 matches"


def test_outcome_1x2_codes_home_win_draw_and_away_win() -> None:
    scores_df = pd.DataFrame({"s1_ft_home_goals": [2, 1, 0], "s1_ft_away_goals": [1, 1, 3]})
    assert corpus.outcome_1x2(scores_df).tolist() == [corpus.HOME, corpus.DRAW, corpus.AWAY]


def test_round_key_names_the_league_season_stage_and_round() -> None:
    rounds_df = pd.DataFrame(
        {
            "s1_league_id": [7, 7, 7],
            "s1_season": ["2025", "2025", "2025"],
            "s1_stage": ["Apertura", "Clausura", None],
            "s1_round": [3, 3, 3],
        }
    )

    assert corpus.round_key(rounds_df).tolist() == [
        "7 2025 Apertura 3",
        "7 2025 Clausura 3",
        "7 2025  3",
    ]
