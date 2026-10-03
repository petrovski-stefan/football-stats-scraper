"""`scrapers/csv_io.py`: where a scraped league-season is written."""

import os

import pytest

from domain import paths
from domain.paths import split_league_season
from scrapers.csv_io import league_csv_path
from scrapers.parsers import clean_string


@pytest.mark.parametrize(
    ("league", "season"),
    [
        ("english_premier_league", "2025-2026"),
        ("norway_eliteserien", "2025"),
        ("brasileirão_série_a", "2025"),
    ],
)
def test_league_csv_path_round_trips(league: str, season: str) -> None:
    path = league_csv_path(league, season)
    assert os.path.dirname(path) == paths.RAW_DIR
    assert split_league_season(path) == (clean_string(league), season)
