"""`features/stage_io.py`: a stage file reads back exactly as it was written."""

from pathlib import Path

import pandas as pd
import pytest

from features.stage_io import read_stage_csv, write_stage_csv


def test_text_columns_survive_a_round_trip(tmp_path: Path) -> None:
    path = str(tmp_path / "x_2025_schedule.csv")
    frame = pd.DataFrame(
        {
            "match_id": ["0012", "34"],
            "s1_season": ["2025", "2025"],  # a calendar-year label looks like an int
            "s1_stage": ["", "Group A"],  # an empty stage is a value, not a gap
            "s1_odds_1x2_open_home": [1.5, None],
        }
    )
    write_stage_csv(frame, path, list(frame.columns))
    back = read_stage_csv(path)
    assert back["match_id"].tolist() == ["0012", "34"]
    assert back["s1_season"].tolist() == ["2025", "2025"]
    assert back["s1_stage"].tolist() == ["", "Group A"]
    assert pd.isna(back.loc[1, "s1_odds_1x2_open_home"])


def test_write_refuses_a_missing_column(tmp_path: Path) -> None:
    with pytest.raises(KeyError, match="missing"):
        write_stage_csv(pd.DataFrame({"a": [1]}), str(tmp_path / "x.csv"), ["a", "b"])
