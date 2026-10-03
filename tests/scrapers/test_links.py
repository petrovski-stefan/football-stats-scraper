"""`scrapers/links.py`: league URLs and the validation of `config/leagues.json` entries.

The URLs use the reserved `example.com` domain, never the real site: the parser reads only
the path, so the host is irrelevant to it.
"""

from typing import Any

import pytest
from pydantic import ValidationError

from scrapers.links import LeagueConfig, parse_league_url


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
