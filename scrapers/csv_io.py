import logging
import os
from typing import Any

import pandas as pd

from scrapers.parsers import clean_string

logger = logging.getLogger(__name__)


def league_slug(country: str, league_name: str) -> str:
    """The league part of a staged file name: the config's country, then the league's name
    as the page's title gives it (`lithuania_2.division`). The title alone can leave the
    country out. A name that already starts with the exact country keeps it once
    (`england_championship`, but `england_english_premier_league`; the user, 2026-10-08).
    Stays here rather than in `domain/paths.py` because it needs `clean_string`, and
    `domain` may not import from `scrapers`."""
    prefix = country.lower().replace(" ", "_")
    league = clean_string(league_name)
    if league == prefix or league.startswith(f"{prefix}_"):
        return league
    return f"{prefix}_{league}"


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
