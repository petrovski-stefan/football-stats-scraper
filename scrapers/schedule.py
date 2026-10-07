"""First-stage scraper: render each configured league season's schedule and write its
stage-1 files (`notes/fields/schedule_1_raw.md`):

- `data/finished/1_raw/<league>_<season>_schedule.csv`: one row per finished match, the
  values its row on the page shows and nothing computed;
- `data/finished/1_raw/<league>_<season>_final_table.csv`: the page's final table, one row
  per team, read once per stage as a check on the standings we rebuild ourselves.

Structured like `scrapers/detail.py`, the second stage: a unit function
(`scrape_league`) that renders one league, an orchestration function (`scrape_all`) that
walks the enabled seasons in `config/leagues.json`, and a CLI entry point.

One code path covers every page layout. A page without stage tabs is scraped as it
opens; otherwise each stage named in the league's `keep` list is clicked and scraped in
turn, its name going into the `s1_stage` column.

Run: `uv run python -m scrapers.schedule`
"""

import logging
from dataclasses import dataclass
from typing import Any

from bs4 import BeautifulSoup
from pydantic import BaseModel, ValidationError
from selenium import webdriver
from selenium.webdriver.common.by import By

from domain import paths
from domain.columns import FINAL_TABLE_COLUMNS, SCHEDULE_RAW_COLUMNS
from domain.schedule import FinalTableRow, ScheduleRow
from scrapers.constants import (
    ROUND_CURRENT_CLASS,
    ROUND_SPANS,
    SCHEDULE_ROWS,
    STAGE_ROUND_SPANS,
    STAGE_SPANS,
)
from scrapers.csv_io import league_slug, save_unless_shrinking
from scrapers.driver import (
    click_round,
    click_stage,
    get_driver,
    open_page,
    show_total_standings,
    switch_odds_type,
    sync_standings_to_stage,
    wait_for_odds,
    wait_for_schedule_rows,
)
from scrapers.links import LeagueSeason, get_league_seasons
from scrapers.parsers import (
    attr,
    parse_ah_odds,
    parse_final_table,
    parse_ou_odds,
    parse_schedulis_row,
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
    name: str  # written to the `s1_stage` column; "" on pages without tabs


@dataclass(frozen=True)
class _StagePass:
    """What every row of one stage pass shares."""

    season: str
    league_id: int
    league_name: str
    stage: _Stage


@dataclass
class _Scrape:
    """One league-season's stage-1 rows: the finished matches and the final table."""

    league_name: str
    matches: list[dict[str, Any]]
    final_table: list[dict[str, Any]]


def scrape_league(job: LeagueSeason) -> _Scrape:
    """Render a league page and scrape its kept stages: finished matches and final tables.

    Only finished matches (with HT + FT scores) are returned; unplayed/live rows are
    skipped by the parser.
    """
    driver = get_driver()
    try:
        open_page(driver, job.url)
        wait_for_schedule_rows(driver)
        switch_odds_type(driver, "1x2")  # the choice persists across round and stage clicks

        league_name = _read_league_name(driver, job.season)
        stages = _resolve_stages(_read_stages(driver), job.keep, f"{league_name} {job.season}")

        scrape = _Scrape(league_name, [], [])
        for stage in stages:
            ctx = _StagePass(job.season, job.league_id, league_name, stage)
            scrape.final_table.extend(_read_final_table(driver, ctx))
            scrape.matches.extend(_scrape_stage(driver, ctx))

        logger.info("League '%s': %d finished matches", league_name, len(scrape.matches))
        return scrape
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


def _read_final_table(driver: webdriver.Chrome, ctx: _StagePass) -> list[dict[str, Any]]:
    """The stage's final table as the page shows it: `Total`, FT, read once.

    A check only (`notes/fields/schedule_1_raw.md` §B). The standings have their own
    sub-table picker that ignores the stage tabs, so a stage page points it at its own
    sub-table first; a stage whose table cannot be shown gets none, never another's.
    """
    stage = ctx.stage
    if stage.stage_id is not None:
        click_stage(driver, stage.stage_id)
        if not sync_standings_to_stage(driver, stage.stage_id):
            logger.warning("  %s: standings not available, no final table", stage.name)
            return []
    if not show_total_standings(driver):
        logger.warning("  %s: the standings' Total view did not show, no final table", stage.name)
        return []
    lines = parse_final_table(BeautifulSoup(driver.page_source, "html.parser"))
    context = {"season": ctx.season, "league_id": ctx.league_id, "stage": stage.name}
    return [{**context, **line} for line in lines]


def _scrape_stage(driver: webdriver.Chrome, ctx: _StagePass) -> list[dict[str, Any]]:
    """Scrape one stage pass round by round."""
    if ctx.stage.stage_id is not None:
        click_stage(driver, ctx.stage.stage_id)
    rounds = _read_rounds(driver, ctx.stage.stage_id)
    logger.info(
        "League '%s' (%s) %s: %d rounds", ctx.league_name, ctx.season, ctx.stage.name, len(rounds)
    )
    matches: list[dict[str, Any]] = []
    for round_number in rounds:
        matches.extend(_scrape_round(driver, round_number, ctx))
    return matches


def _scrape_round(
    driver: webdriver.Chrome, round_number: int, ctx: _StagePass
) -> list[dict[str, Any]]:
    click_round(driver, round_number, ctx.stage.stage_id)
    wait_for_odds(driver)

    secondary = _secondary_odds(driver)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    rows = soup.select(SCHEDULE_ROWS)
    context = {
        "s1_season": ctx.season,
        "s1_league_id": ctx.league_id,
        "s1_league_name": ctx.league_name,
        "s1_stage": ctx.stage.name,
        "s1_round": round_number,
    }

    round_matches: list[dict[str, Any]] = []
    for row in rows:
        parsed = parse_schedulis_row(row)
        if parsed is None:
            continue
        parsed.update(context)
        parsed.update(secondary.get(parsed["match_id"], {}))
        round_matches.append(parsed)

    label = f"{ctx.stage.name} round {round_number}".strip()
    logger.info("  %s: %d finished / %d rows", label, len(round_matches), len(rows))
    return round_matches


# Each secondary odds type, and the row fields its three cells map to.
_SECONDARY_ODDS = (
    (
        "ou",
        parse_ou_odds,
        ("s1_odds_ou_open_over", "s1_odds_ou_open_line", "s1_odds_ou_open_under"),
    ),
    ("ah", parse_ah_odds, ("s1_odds_ah_open_home", "s1_odds_ah_open_line", "s1_odds_ah_open_away")),
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


def _validate(
    rows: list[dict[str, Any]], model: type[BaseModel], what: str
) -> list[dict[str, Any]]:
    """Validate scraped rows through a stage-1 model, dropping invalid ones."""
    valid: list[dict[str, Any]] = []
    for row in rows:
        try:
            valid.append(model(**row).model_dump())
        except ValidationError as exc:
            logger.warning("Skipping %s %s: %s", what, row.get("match_id", row.get("team_id")), exc)
    return valid


def scrape_all() -> None:
    """Scrape every enabled league season in `config/leagues.json` into its stage-1 files."""
    for job in get_league_seasons():
        logger.info("Scraping %s", job.url)
        scrape = scrape_league(job)
        league = league_slug(scrape.league_name)

        matches = _validate(scrape.matches, ScheduleRow, "match")
        logger.info("%s: %d valid matches", scrape.league_name, len(matches))
        if matches:
            path = paths.schedule_path(1, league, job.season)
            save_unless_shrinking(matches, path, SCHEDULE_RAW_COLUMNS)

        table = _validate(scrape.final_table, FinalTableRow, "final-table team")
        if table:
            path = paths.final_table_path(league, job.season)
            save_unless_shrinking(table, path, FINAL_TABLE_COLUMNS)


def main() -> None:
    scrape_all()


if __name__ == "__main__":
    main()
