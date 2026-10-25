"""Reading and writing the staged pipeline's CSV files, the same way everywhere.

A CSV cannot tell `""` from a missing value, nor `"2025"` the season label from the
integer 2025, so every reader names the text columns or pandas guesses them wrong: an
empty stage becomes NaN, a calendar-year season becomes an int, an id loses its leading
form. One reader and one writer keep every stage file round-tripping exactly.
"""

import os

import pandas as pd

from domain.columns import STAGE_TEXT_COLUMNS


def read_stage_csv(path: str) -> pd.DataFrame:
    """A stage file as written: text columns stay text, empty text stays `""`."""

    head = pd.read_csv(path, nrows=0).columns
    text = [c for c in STAGE_TEXT_COLUMNS if c in head]
    stage_file_df = pd.read_csv(
        path, dtype=dict.fromkeys(text, str), keep_default_na=False, na_values=[""]
    )

    return stage_file_df.fillna(dict.fromkeys(text, ""))


def write_stage_csv(stage_file_df: pd.DataFrame, path: str, columns: list[str]) -> None:
    """Write `stage_file_df` with exactly `columns`, in that order; a missing column is an error."""

    missing = [c for c in columns if c not in stage_file_df.columns]
    if missing:
        raise KeyError(f"columns missing before writing {path}: {missing[:5]}")

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    stage_file_df[columns].to_csv(path, index=False)
