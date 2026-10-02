"""First-stage scraper: render each configured league season's schedule and write one
row per finished match to `data/raw/<league>_<season>.csv`.

Structured like `scrapers/detail.py`, the second stage: a unit function
(`scrape_league`) that renders one league, an orchestration function (`scrape_all`) that
walks the enabled seasons in `config/leagues.json`, and a CLI entry point.

One code path covers every page layout. A page without stage tabs is scraped as it
opens; otherwise each stage named in the league's `keep` list is clicked and scraped in
turn, its name going into the `stage` column.

Run: `uv run python -m scrapers.schedule`
"""

import logging
from dataclasses import dataclass
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
    STAGE_ROUND_SPANS,
    STAGE_SPANS,
)
from scrapers.csv_io import save_df_to_csv
from scrapers.driver import (
    click_round,
    click_stage,
    get_driver,
    open_page,
    switch_odds_type,
    sync_standings_to_round,
    sync_standings_to_stage,
    wait_for_odds,
    wait_for_schedule_rows,
)
from scrapers.links import LeagueSeason, get_league_seasons
from scrapers.parsers import (
    attr,
    parse_ah_odds,
    parse_ou_odds,
    parse_row_identity,
    parse_schedulis_row,
    parse_standings,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _Stage:
    """One pass over the schedule: a stage tab, or the whole page when it has none."""

    stage_id: str | None  # the tab's `stage` attribute; None on pages without tabs
    name: str  # written to the `stage` column; "" on pages without tabs


@dataclass(frozen=True)
class _StagePass:
    """What every round of one stage pass shares."""

    season: str
    league_id: int
    league_name: str
    stage: _Stage
    standings_ok: bool  # False: this stage's standings could not be shown, positions dropped


def scrape_league(job: LeagueSeason) -> tuple[list[dict[str, Any]], str]:
    """Render a league page and scrape every finished match of its kept stages.

    Returns (rows, league_name). Only finished matches (with HT + FT scores) are
    returned; unplayed/live rows are skipped by the parser.
    """
    driver = get_driver()
    try:
        open_page(driver, job.url)
        wait_for_schedule_rows(driver)
        switch_odds_type(driver, "1x2")  # the choice persists across round and stage clicks

        league_name = _read_league_name(driver, job.season)
        stages = _resolve_stages(_read_stages(driver), job.keep, f"{league_name} {job.season}")

        matches: list[dict[str, Any]] = []
        for stage in stages:
            matches.extend(_scrape_stage(driver, stage, job, league_name))

        logger.info("League '%s': %d finished matches", league_name, len(matches))
        return matches, league_name
    finally:
        driver.quit()


def _read_stages(driver: webdriver.Chrome) -> list[tuple[str, str]]:
    """The page's stage tabs as (stage id, name), in page order. Empty without tabs."""
    return [
        (span.get_attribute("stage") or "", (span.get_attribute("textContent") or "").strip())
        for span in driver.find_elements(By.CSS_SELECTOR, STAGE_SPANS)
    ]


def _resolve_stages(tabs: list[tuple[str, str]], keep: tuple[str, ...], label: str) -> list[_Stage]:
    """Choose the stage passes for a page from the config's `keep` list.

    No tabs means one pass over the page as it opens; otherwise one pass per kept tab,
    in page order. A kept stage missing from the page only warns, since an unfinished
    season may not have reached it yet. A config whose shape does not match the page at
    all scrapes nothing: any guess would be a stage nobody chose.
    """
    if not tabs:
        if keep:
            logger.error("%s: config keeps %s but the page has no stage tabs", label, list(keep))
            return []
        return [_Stage(None, "")]
    if not keep:
        names = [name for _, name in tabs]
        logger.error("%s: page has stage tabs %s but config keeps none", label, names)
        return []
    missing = sorted(set(keep) - {name for _, name in tabs})
    if missing:
        logger.warning("%s: kept stages %s are not on the page", label, missing)
    return [_Stage(stage_id, name) for stage_id, name in tabs if name in keep]


def _scrape_stage(
    driver: webdriver.Chrome, stage: _Stage, job: LeagueSeason, league_name: str
) -> list[dict[str, Any]]:
    """Scrape one stage pass round by round, with the standings pointed at that stage."""
    standings_ok = True
    if stage.stage_id is not None:
        click_stage(driver, stage.stage_id)
        standings_ok = sync_standings_to_stage(driver, stage.stage_id)
        if not standings_ok:
            logger.warning("  %s: standings not available, positions left empty", stage.name)

    rounds = _read_rounds(driver, stage.stage_id)
    logger.info("League '%s' (%s) %s: %d rounds", league_name, job.season, stage.name, len(rounds))

    ctx = _StagePass(job.season, job.league_id, league_name, stage, standings_ok)
    matches: list[dict[str, Any]] = []
    for round_number in rounds:
        matches.extend(_scrape_round(driver, round_number, ctx))
    return matches


def _scrape_round(
    driver: webdriver.Chrome, round_number: int, ctx: _StagePass
) -> list[dict[str, Any]]:
    click_round(driver, round_number, ctx.stage.stage_id)
    if ctx.standings_ok:
        sync_standings_to_round(driver, round_number)
    wait_for_odds(driver)

    secondary = _secondary_odds(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    positions = parse_standings(soup) if ctx.standings_ok else {}
    rows = soup.select(SCHEDULE_ROWS)

    index_by_id, matches_in_round = _order_round(rows)
    label = f"{ctx.stage.name} round {round_number}".strip()

    round_matches: list[dict[str, Any]] = []
    for row in rows:
        parsed = parse_schedulis_row(row, positions=positions)
        if parsed is None:
            continue
        match_id = parsed["match_id"]
        if match_id not in index_by_id:
            logger.warning("  %s: no position for match %r", label, match_id)
        parsed.update(
            {
                "season": ctx.season,
                "league_id": ctx.league_id,
                "league_name": ctx.league_name,
                "stage": ctx.stage.name,
                "round": round_number,
                "match_index_in_round": index_by_id.get(match_id, 0),
                "matches_in_round": matches_in_round,
            }
        )
        parsed.update(secondary.get(match_id, {}))
        round_matches.append(parsed)

    logger.info("  %s: %d finished / %d rows", label, len(round_matches), len(rows))
    return round_matches


# Each secondary odds type, and the row fields its three cells map to.
_SECONDARY_ODDS = (
    ("ou", parse_ou_odds, ("over_odds", "ou_line", "under_odds")),
    ("ah", parse_ah_odds, ("ah_home_odds", "ah_line", "ah_away_odds")),
)


def _secondary_odds(driver: webdriver.Chrome) -> dict[str, dict[str, float | None]]:
    """Read the OU and AH columns for the round already on screen, keyed by match id.

    The odds type is a page-level setting shared by every row, so the only way to get
    all three is to switch the header and re-read. This leaves the header back on 1X2,
    because the caller parses the full rows (scores, teams, 1X2 odds) after it returns.

    A league that does not carry a type is skipped rather than raised on, so its rows
    simply come out with empty columns for it.
    """
    out: dict[str, dict[str, float | None]] = {}
    for kind, parse, fields in _SECONDARY_ODDS:
        if not switch_odds_type(driver, kind):
            logger.warning("  odds type %r unavailable", kind)
            continue
        wait_for_odds(driver)
        soup = BeautifulSoup(driver.page_source, "html.parser")
        for row in soup.select(SCHEDULE_ROWS):
            match_id = (attr(row, "matchid") or "").strip()
            if match_id:
                out.setdefault(match_id, {}).update(dict(zip(fields, parse(row), strict=True)))
    switch_odds_type(driver, "1x2")
    wait_for_odds(driver)
    return out


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


def _read_rounds(driver: webdriver.Chrome, stage_id: str | None) -> list[int]:
    """Return round numbers 1..current (finished rounds + the live one) of one stage.

    Rounds beyond the current one are future fixtures with no results; their rows
    would all be skipped, so we stop at the round marked 'current'. Every stage's round
    buttons are in the DOM at once, each set with its own 'current', so the read is
    scoped to `stage_id` (None on pages without stage tabs).
    """
    selector = ROUND_SPANS if stage_id is None else STAGE_ROUND_SPANS.format(stage=stage_id)
    spans = driver.find_elements(By.CSS_SELECTOR, selector)
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
    """Scrape every enabled league season in `config/leagues.json` into `data/raw/`."""
    for job in get_league_seasons():
        logger.info("Scraping %s", job.url)
        rows, league_name = scrape_league(job)

        matches = _validate(rows)
        logger.info("%s: %d valid matches", league_name, len(matches))

        if matches:
            save_df_to_csv(matches, league_name, job.season)


def main() -> None:
    scrape_all()


if __name__ == "__main__":
    main()
