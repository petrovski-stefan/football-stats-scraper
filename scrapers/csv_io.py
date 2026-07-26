import logging
import os
from typing import Any

import pandas as pd

from domain.columns import ORDERED_DF_COLUMNS
from scrapers.parsers import clean_string

logger = logging.getLogger(__name__)

DATA_DIR = "data"


def league_csv_path(league_name: str, season: str) -> str:
    return os.path.join(DATA_DIR, f"{clean_string(league_name)}_{season}.csv")


def write_ordered_csv(rows: list[dict[str, Any]], csv_path: str, columns: list[str]) -> None:
    """Write rows to csv_path with columns in the given order (missing cols dropped)."""
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    df = pd.DataFrame(rows)
    df = df[[c for c in columns if c in df.columns]]
    df.to_csv(csv_path, index=False)
    logger.info("Saved %d rows to %s", len(df), csv_path)


def append_rows(rows: list[dict[str, Any]], csv_path: str, columns: list[str]) -> None:
    """Append rows to csv_path (writing the header only when the file is new).

    Used for resumable incremental scrapes so progress survives an interruption.
    """
    if not rows:
        return
    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    df = pd.DataFrame(rows)
    df = df[[c for c in columns if c in df.columns]]
    write_header = not os.path.exists(csv_path)
    df.to_csv(csv_path, mode="a", header=write_header, index=False)


def save_df_to_csv(
    league_matches_data: list[dict[str, Any]], league_name: str, season: str
) -> None:
    csv_file_path = league_csv_path(league_name, season)

    if os.path.exists(csv_file_path):
        new_len = len(league_matches_data)
        old_df = pd.read_csv(csv_file_path)
        # Only overwrite when the new scrape is at least as complete as the old one,
        # so a partial run never clobbers a good file.
        if new_len < len(old_df):
            logger.warning(
                "Not overwriting %s: new=%d rows < old=%d rows",
                csv_file_path,
                new_len,
                len(old_df),
            )
            return

    write_ordered_csv(league_matches_data, csv_file_path, ORDERED_DF_COLUMNS)
