"""`scrapers/driver.py`: the robots guard in `open_page`. The browser-bound helpers need a
live page and are not unit-tested."""

from typing import Any, cast

import pytest
from selenium import webdriver

from scrapers import driver


class _FakeDriver:
    """Records the pages it is asked to open, and opens none."""

    def __init__(self) -> None:
        self.opened: list[str] = []

    def get(self, url: str) -> None:
        self.opened.append(url)


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> _FakeDriver:
    monkeypatch.setattr(driver, "ROBOTS_DISALLOW", {"example.com": ("/private/", "/en/")})
    return _FakeDriver()


def _open(fake: _FakeDriver, url: str) -> None:
    driver.open_page(cast(webdriver.Chrome, cast(Any, fake)), url)


def test_an_allowed_page_is_opened(fake: _FakeDriver) -> None:
    _open(fake, "https://example.com/league/2025-2026/1")
    assert fake.opened == ["https://example.com/league/2025-2026/1"]


@pytest.mark.parametrize("path", ["/private/", "/private/page", "/en/league/1"])
def test_a_disallowed_path_is_refused_before_any_request(fake: _FakeDriver, path: str) -> None:
    with pytest.raises(ValueError, match=r"robots\.txt disallows"):
        _open(fake, f"https://example.com{path}")
    assert fake.opened == []


def test_a_host_without_recorded_rules_is_refused(fake: _FakeDriver) -> None:
    with pytest.raises(ValueError, match=r"no robots\.txt rules recorded"):
        _open(fake, "https://other.example.com/league/1")
    assert fake.opened == []
