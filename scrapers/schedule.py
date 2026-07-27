"""First-stage scraper: render each configured league season's schedule and write one
row per finished match to `data/raw/<league>_<season>.csv`.

Structured like `scrapers/detail.py`, the second stage: a unit function
(`scrape_league`) that renders one league, an orchestration function (`scrape_all`) that
walks `config/LEAGUES.txt`, and a CLI entry point.

Run: `uv run python -m scrapers.schedule`
"""

import logging
from typing import Any

from bs4 import BeautifulSoup, Tag
from pydantic import ValidationError
from selenium import webdriver
from selenium.webdriver.common.by import By

from domain.match import Match, round_sort_key
from scrapers.constants import (
    ROUND_CURRENT_CLASS,
    ROUND_SPANS,
    SCHEDULE_ROWS,
)
from scrapers.csv_io import save_df_to_csv
from scrapers.driver import (
    click_round,
    get_driver,
    switch_odds_to_1x2,
    sync_standings_to_round,
    wait_for_odds,
    wait_for_schedule_rows,
)
from scrapers.links import get_leagues_links, parse_league_url
from scrapers.parsers import parse_row_identity, parse_schedulis_row, parse_standings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def scrape_league(league_url: str, season: str, league_id: int) -> tuple[list[dict[str, Any]], str]:
    """Render a league page and scrape every finished match, round by round.

    Returns (rows, league_name). Only finished matches (with HT + FT scores) are
    returned; unplayed/live rows are skipped by the parser.
    """
    driver = get_driver()
    try:
        driver.get(league_url)
        wait_for_schedule_rows(driver)
        switch_odds_to_1x2(driver)  # 1X2 odds persist across round clicks

        league_name = _read_league_name(driver, season)
        rounds = _read_rounds(driver)
        logger.info("League '%s' (%s): %d rounds", league_name, season, len(rounds))

        matches: list[dict[str, Any]] = []
        for round_number in rounds:
            matches.extend(_scrape_round(driver, round_number, season, league_id, league_name))

        logger.info("League '%s': %d finished matches", league_name, len(matches))
        return matches, league_name
    finally:
        driver.quit()


def _scrape_round(
    driver: webdriver.Chrome,
    round_number: int,
    season: str,
    league_id: int,
    league_name: str,
) -> list[dict[str, Any]]:
    click_round(driver, round_number)
    sync_standings_to_round(driver, round_number)
    wait_for_odds(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    positions = parse_standings(soup)
    rows = soup.select(SCHEDULE_ROWS)

    index_by_id, matches_in_round = _order_round(rows)

    round_matches: list[dict[str, Any]] = []
    for row in rows:
        parsed = parse_schedulis_row(row, positions=positions)
        if parsed is None:
            continue
        match_id = parsed["match_id"]
        if match_id not in index_by_id:
            logger.warning("  round %d: no position for match %r", round_number, match_id)
        parsed.update(
            {
                "season": season,
                "league_id": league_id,
                "league_name": league_name,
                "stage": "",
                "round": round_number,
                "match_index_in_round": index_by_id.get(match_id, 0),
                "matches_in_round": matches_in_round,
            }
        )
        round_matches.append(parsed)

    logger.info("  round %d: %d finished / %d rows", round_number, len(round_matches), len(rows))
    return round_matches


def _order_round(rows: list[Tag]) -> tuple[dict[str, int], int]:
    """Map match_id -> 1-based position in the round, and the round's total size.

    Ordered over **every scheduled match**, not just the finished ones, so a match is
    the 5th of 10 whether or not the other nine have been played. That is the whole
    reason this runs here rather than downstream: unplayed rows exist in the DOM but
    never reach the CSV, so their positions cannot be recovered later.
    """
    identities = [ident for row in rows if (ident := parse_row_identity(row))["match_id"]]
    identities.sort(
        key=lambda i: round_sort_key(i["date"], i["home_team_name"], i["away_team_name"])
    )
    return {i["match_id"]: n for n, i in enumerate(identities, 1)}, len(identities)


def _read_league_name(driver: webdriver.Chrome, season: str) -> str:
    # Title looks like: "Schedule, Fixture, Latest Results - 2025-2026 English Premier League"
    name = driver.title.split(" - ")[-1].strip()
    # Drop the leading season, e.g. "2025-2026 English Premier League" -> "English Premier League"
    if name.startswith(season):
        name = name[len(season) :].strip()
    return name.lower().replace(" ", "_")


def _read_rounds(driver: webdriver.Chrome) -> list[int]:
    """Return round numbers 1..current (finished rounds + the live one).

    Rounds beyond the current one are future fixtures with no results; their rows
    would all be skipped, so we stop at the round marked 'current'.
    """
    spans = driver.find_elements(By.CSS_SELECTOR, ROUND_SPANS)
    numbers: list[int] = []
    current: int | None = None
    for span in spans:
        raw = span.get_attribute("round")
        if not raw or not raw.isdigit():
            continue
        number = int(raw)
        numbers.append(number)
        if ROUND_CURRENT_CLASS in (span.get_attribute("class") or ""):
            current = number

    numbers.sort()
    if current is not None:
        numbers = [n for n in numbers if n <= current]
    return numbers


# --- Orchestration / CLI -----------------------------------------------------


def _validate(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Validate scraped rows through the Match model, dropping invalid ones."""
    valid: list[dict[str, Any]] = []
    for row in rows:
        try:
            valid.append(Match(**row).model_dump())
        except ValidationError as exc:
            logger.warning("Skipping match %s: %s", row.get("match_id"), exc)
    return valid


def scrape_all() -> None:
    """Scrape every league season listed in `config/LEAGUES.txt` into `data/raw/`."""
    for url in get_leagues_links():
        try:
            season, league_id = parse_league_url(url)
        except ValueError as exc:
            logger.error("%s", exc)
            continue

        logger.info("Scraping %s", url)
        rows, league_name = scrape_league(url, season, league_id)

        matches = _validate(rows)
        logger.info("%s: %d valid matches", league_name, len(matches))

        if matches:
            save_df_to_csv(matches, league_name, season)


def main() -> None:
    scrape_all()


if __name__ == "__main__":
    main()
