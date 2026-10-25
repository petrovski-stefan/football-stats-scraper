"""Writing scraped rows to CSV, and the league part of the stage-1 file names.

`save_unless_shrinking` keeps a shorter re-scrape from overwriting a fuller file, and
`append_rows` lets a resumable run keep its progress.
"""

import logging
import os
from typing import Any

import pandas as pd

from scrapers.parsers import clean_string

logger = logging.getLogger(__name__)


def league_slug(country: str, league_name: str) -> str:
    """The league part of a staged file name: the config's country, then the page title's league
    name (`japan_j2_league`), the country once if the name starts with it (`brazil_serie_a`; the
    user, 2026-10-08). Not in `domain/paths.py`: it needs `clean_string` from `scrapers`.
    """

    prefix = country.lower().replace(" ", "_")
    league = clean_string(league_name)

    if league == prefix or league.startswith(f"{prefix}_"):
        return league

    return f"{prefix}_{league}"


def write_ordered_csv(rows: list[dict[str, Any]], csv_path: str, columns: list[str]) -> None:
    """Write rows to csv_path with columns in the given order (missing cols dropped)."""

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    ordered_df = pd.DataFrame(rows)
    ordered_df = ordered_df[[c for c in columns if c in ordered_df.columns]]

    ordered_df.to_csv(csv_path, index=False)
    logger.info("Saved %d rows to %s", len(ordered_df), csv_path)


def append_rows(rows: list[dict[str, Any]], csv_path: str, columns: list[str]) -> None:
    """Append rows to csv_path (writing the header only when the file is new).

    Used for resumable incremental scrapes so progress survives an interruption.
    """

    if not rows:
        return

    os.makedirs(os.path.dirname(csv_path) or ".", exist_ok=True)
    new_rows_df = pd.DataFrame(rows)
    new_rows_df = new_rows_df[[c for c in columns if c in new_rows_df.columns]]

    write_header = not os.path.exists(csv_path)
    new_rows_df.to_csv(csv_path, mode="a", header=write_header, index=False)


def save_unless_shrinking(rows: list[dict[str, Any]], csv_path: str, columns: list[str]) -> bool:
    """Write `rows` over `csv_path`, unless the file already holds more rows.

    A re-scrape is at least as complete as the last one; one that comes back shorter is a
    partial run, and must not clobber a good file. Returns whether the file was written.
    """

    if os.path.exists(csv_path):
        old_len = len(pd.read_csv(csv_path))
        if len(rows) < old_len:
            logger.warning(
                "Not overwriting %s: new=%d rows < old=%d rows", csv_path, len(rows), old_len
            )
            return False

    write_ordered_csv(rows, csv_path, columns)

    return True
