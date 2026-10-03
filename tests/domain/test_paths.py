"""`domain/paths.py`: where each file lives, and splitting a league-season filename.

The filename tests cover both season conventions: the bug they guard against (fixed-width
slicing that assumes a 9-character season) passes on "2025-2026" names and breaks only on
calendar-year "2025" ones.
"""

import os

import pytest

from domain import paths
from domain.paths import split_league_season


@pytest.mark.parametrize(
    "base", ["data/raw/test_league_2025-2026.csv", "elsewhere/test_league_2025-2026.csv"]
)
def test_detail_path_is_beside_the_raw_csv(base: str) -> None:
    assert paths.detail_path(base) == os.path.join(
        paths.RAW_DIR, "test_league_2025-2026" + paths.DETAIL_SUFFIX
    )


def test_enriched_path_goes_to_the_processed_dir() -> None:
    assert paths.enriched_path("data/raw/test_league_2025.csv") == os.path.join(
        paths.PROCESSED_DIR, "test_league_2025" + paths.ENRICHED_SUFFIX
    )


def test_global_stores_live_in_raw_and_are_not_league_seasons() -> None:
    stores = [
        paths.goals_path(),
        paths.goals_done_path(),
        paths.events_path(),
        paths.events_done_path(),
    ]
    assert all(os.path.dirname(p) == paths.RAW_DIR for p in stores)
    assert {os.path.basename(p) for p in stores} == paths.GLOBAL_FILES


@pytest.mark.parametrize(
    ("path", "split"),
    [
        ("data/raw/norway_eliteserien_2025.csv", ("norway_eliteserien", "2025")),
        ("data/raw/english_premier_league_2025-2026.csv", ("english_premier_league", "2025-2026")),
        ("data/raw/j1_league_2025.csv", ("j1_league", "2025")),
        # Greedy league part: the split falls at the last underscore that leaves a season.
        ("data/raw/liga_2000_2025-2026.csv", ("liga_2000", "2025-2026")),
        # Not a league-season: the stem comes back whole, with no season.
        ("data/raw/goals.csv", ("goals", "")),
        (
            "data/raw/english_premier_league_2025-2026_detail.csv",
            ("english_premier_league_2025-2026_detail", ""),
        ),
    ],
)
def test_split_league_season(path: str, split: tuple[str, str]) -> None:
    assert split_league_season(path) == split
