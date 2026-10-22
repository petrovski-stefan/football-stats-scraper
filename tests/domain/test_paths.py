"""`domain/paths.py`: where each file lives, and splitting a league-season filename.

The filename tests cover both season conventions: the bug they guard against (fixed-width
slicing that assumes a 9-character season) passes on "2025-2026" names and breaks only on
calendar-year "2025" ones.
"""

import os

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain import paths
from domain.paths import split_league_season

# A league slug as the file names hold it: lowercase letters, digits and underscores, so it may
# end in something that looks like a year (`liga_2000`).
_SLUGS = st.text("abcdefghijklmnopqrstuvwxyz0123456789_", min_size=1, max_size=30)


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


# --- The staged pipeline: data/finished/ ---------------------------------------------


@pytest.mark.parametrize("stage", [1, 2, 3])
def test_schedule_files_live_in_their_stage_dir(stage: int) -> None:
    path = paths.schedule_path(stage, "test_league", "2025")
    assert os.path.dirname(path) == paths.stage_dir(stage)
    assert os.path.dirname(paths.stage_dir(stage)) == paths.FINISHED_DIR


def test_an_unknown_stage_is_an_error() -> None:
    with pytest.raises(KeyError):
        paths.stage_dir(4)


def test_the_final_table_is_stage_1_only() -> None:
    path = paths.final_table_path("test_league", "2025-2026")
    assert os.path.dirname(path) == paths.stage_dir(1)
    assert path.endswith(paths.FINAL_TABLE_SUFFIX)


@pytest.mark.parametrize(
    ("league", "season"), [("test_league", "2025-2026"), ("liga_2000", "2025")]
)
def test_split_schedule_name_inverts_schedule_path(league: str, season: str) -> None:
    assert paths.split_schedule_name(paths.schedule_path(2, league, season)) == (league, season)


@given(_SLUGS, st.integers(1900, 2100), st.booleans(), st.sampled_from(sorted(paths.STAGE_DIRS)))
def test_any_league_and_season_survive_the_file_name(
    league: str, year: int, cross_year: bool, stage: int
) -> None:
    season = f"{year}-{year + 1}" if cross_year else str(year)
    assert paths.split_schedule_name(paths.schedule_path(stage, league, season)) == (league, season)


def test_split_schedule_name_rejects_other_files() -> None:
    assert paths.split_schedule_name("data/raw/test_league_2025.csv") == ("test_league_2025", "")


def test_schedule_at_stage_keeps_the_league_season() -> None:
    raw = paths.schedule_path(1, "test_league", "2025")
    assert paths.schedule_at_stage(raw, 3) == paths.schedule_path(3, "test_league", "2025")
    with pytest.raises(ValueError, match="not a staged schedule"):
        paths.schedule_at_stage("data/raw/test_league_2025.csv", 2)
