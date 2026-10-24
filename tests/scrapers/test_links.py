"""`scrapers/links.py`: league URLs and the validation of `config/leagues.json` entries.

The URLs use the reserved `example.com` domain, never the real site: the parser reads only
the path, so the host is irrelevant to it.
"""

import json
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from scrapers.links import LeagueConfig, Selection, get_league_seasons, parse_league_url


@pytest.mark.parametrize(
    ("url", "parsed"),
    [
        ("https://example.com/league/2025-2026/36", ("2025-2026", 36)),
        ("https://example.com/league/2025/71", ("2025", 71)),
    ],
)
def test_parse_league_url(url: str, parsed: tuple[str, int]) -> None:
    assert parse_league_url(url) == parsed


def test_parse_league_url_rejects_other_pages() -> None:
    with pytest.raises(ValueError, match="Cannot parse"):
        parse_league_url("https://example.com/match/h2h-1")


def _league(**overrides: Any) -> dict[str, Any]:
    """A valid config entry; each test breaks one part of it."""

    entry: dict[str, Any] = {
        "name": "Test League",
        "code": "TST",
        "continent": "Testland",
        "country": "Testland",
        "league_id": 36,
        "stages": ["League", "Playoff"],
        "keep": ["League"],
        "seasons": [
            {
                "season": "2025-2026",
                "url": "https://example.com/league/2025-2026/36",
                "enabled": True,
            },
            {"season": "2025", "url": "https://example.com/league/2025/36", "enabled": False},
        ],
    }

    entry.update(overrides)
    return entry


def test_valid_league_config() -> None:
    config = LeagueConfig.model_validate(_league())
    assert config.keep == ["League"]
    assert [s.season for s in config.seasons] == ["2025-2026", "2025"]


def test_league_without_stage_tabs_keeps_nothing() -> None:
    LeagueConfig.model_validate(_league(stages=[], keep=[]))


def test_keep_must_be_a_listed_stage() -> None:
    with pytest.raises(ValidationError, match="not in stages"):
        LeagueConfig.model_validate(_league(keep=["Apertura"]))


@pytest.mark.parametrize(
    "season",
    [
        # The URL's season differs from the declared one.
        {"season": "2024-2025", "url": "https://example.com/league/2025-2026/36", "enabled": True},
        # The URL's league id differs from the league's.
        {"season": "2025-2026", "url": "https://example.com/league/2025-2026/99", "enabled": True},
    ],
)
def test_season_url_must_match_season_and_league_id(season: dict[str, Any]) -> None:
    with pytest.raises(ValidationError, match="is not season"):
        LeagueConfig.model_validate(_league(seasons=[season]))


# --- Choosing league-seasons ------------------------------------------------------------


def _config(tmp_path: Path) -> str:
    """Two leagues: TST with one enabled season, OTH with none enabled."""

    other = _league(
        name="Other League",
        code="OTH",
        league_id=71,
        seasons=[
            {"season": "2025", "url": "https://example.com/league/2025/71", "enabled": False},
            {"season": "2026", "url": "https://example.com/league/2026/71", "enabled": False},
        ],
    )

    path = tmp_path / "leagues.json"
    path.write_text(json.dumps([_league(), other]), encoding="utf-8")
    return str(path)


def _picked(selection: Selection | None, config: str) -> list[tuple[str, str]]:
    return [(job.code, job.season) for job in get_league_seasons(selection, config)]


def test_by_default_only_enabled_seasons_run(tmp_path: Path) -> None:
    assert _picked(None, _config(tmp_path)) == [("TST", "2025-2026")]


def test_named_leagues_run_whatever_their_flags(tmp_path: Path) -> None:
    assert _picked(Selection(leagues=("OTH",)), _config(tmp_path)) == [
        ("OTH", "2025"),
        ("OTH", "2026"),
    ]


def test_all_leagues_and_a_year_bound(tmp_path: Path) -> None:
    picked = _picked(Selection(all_leagues=True, before_year=2026), _config(tmp_path))
    # 2025-2026 and 2025 started in 2025; the calendar-year 2026 season is left out.
    assert picked == [("TST", "2025-2026"), ("TST", "2025"), ("OTH", "2025")]


def test_an_unknown_league_code_is_an_error(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="XXX"):
        get_league_seasons(Selection(leagues=("XXX",)), _config(tmp_path))


def test_a_job_carries_the_leagues_code_and_name(tmp_path: Path) -> None:
    (job,) = get_league_seasons(None, _config(tmp_path))
    assert (job.code, job.name, job.league_id, job.keep) == ("TST", "Test League", 36, ("League",))
