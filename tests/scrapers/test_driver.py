"""`scrapers/driver.py`: the robots guard in `open_page`. The browser-bound helpers need a
live page and are not unit-tested."""

from typing import Any, cast

import pytest
from selenium import webdriver

from scrapers import driver
from scrapers.constants import DETAIL_URL


class _FakeDriver:
    """Records the pages it is asked to open, and opens none. `redirects` maps a URL to the
    URL that the browser lands on."""

    def __init__(self) -> None:
        self.opened: list[str] = []
        self.redirects: dict[str, str] = {}
        self.current_url = ""

    def get(self, url: str) -> None:
        self.opened.append(url)
        self.current_url = self.redirects.get(url, url)


@pytest.fixture
def fake(monkeypatch: pytest.MonkeyPatch) -> _FakeDriver:
    rules = {"example.com": ("/private/", "/en/"), "new.example.com": ("/private/",)}
    monkeypatch.setattr(driver, "ROBOTS_DISALLOW", rules)

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


def test_a_redirect_to_a_recorded_host_is_kept(fake: _FakeDriver) -> None:
    fake.redirects["https://example.com/league/1"] = "https://new.example.com/league/1"
    _open(fake, "https://example.com/league/1")
    assert fake.current_url == "https://new.example.com/league/1"


@pytest.mark.parametrize(
    "landed",
    ["https://moved.example.com/league/1", "https://new.example.com/private/league/1"],
)
def test_a_redirect_to_an_unchecked_page_is_refused(fake: _FakeDriver, landed: str) -> None:
    fake.redirects["https://example.com/league/1"] = landed
    with pytest.raises(ValueError, match="it redirected to"):
        _open(fake, "https://example.com/league/1")


def test_robots_refusal_names_the_reason() -> None:
    assert driver.robots_refusal(DETAIL_URL.format(match_id=1)) is None
    assert "no robots.txt rules" in str(driver.robots_refusal("https://example.org/x"))
