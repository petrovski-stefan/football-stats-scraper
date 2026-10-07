"""`scrapers/csv_io.py`: file-name slugs, and a re-scrape never clobbering a fuller file."""

from pathlib import Path

import pandas as pd
import pytest

from domain import paths
from scrapers.csv_io import league_slug, save_unless_shrinking
from scrapers.parsers import clean_string


@pytest.mark.parametrize(
    ("league", "season"),
    [
        ("english_premier_league", "2025-2026"),
        ("norway_eliteserien", "2025"),
        ("brasileirão_série_a", "2025"),
    ],
)
def test_league_slug_round_trips_through_the_schedule_path(league: str, season: str) -> None:
    path = paths.schedule_path(1, league_slug(league), season)
    assert paths.split_schedule_name(path) == (clean_string(league), season)


def test_save_unless_shrinking(tmp_path: Path) -> None:
    path = str(tmp_path / "out.csv")
    columns = ["a", "b"]
    assert save_unless_shrinking([{"b": 1, "a": 2}, {"b": 3, "a": 4}], path, columns)
    assert list(pd.read_csv(path).columns) == columns
    # A shorter scrape is a partial run: the fuller file stays.
    assert not save_unless_shrinking([{"a": 9, "b": 9}], path, columns)
    assert len(pd.read_csv(path)) == 2
    # An equal or longer one replaces it.
    assert save_unless_shrinking([{"a": 5, "b": 6}] * 3, path, columns)
    assert len(pd.read_csv(path)) == 3
