"""First-stage scraper: render each configured league season's schedule and write its
stage-1 files (`notes/fields/schedule_1_raw.md`):

- `data/finished/1_raw/<country>_<league>_<season>_schedule.csv`: one row per finished
  match, the values its row on the page shows and nothing computed;
- `data/finished/1_raw/<country>_<league>_<season>_final_table.csv`: the page's final
  table, one row per team, read once per stage as a check on the standings we rebuild.

`<country>` is the config's country and `<league>` the league's name in the page's title,
written once when that name already starts with the exact country (`england_championship`).

Structured like `scrapers/detail.py`, the second stage: a unit function
(`scrape_league`) that renders one league, an orchestration function (`scrape_all`) that
walks the chosen league-seasons of `config/leagues.json`, and a CLI entry point.

A run is safe to leave alone for hours: one league failing is logged and the run goes on, a
league-season already on disk is skipped (so a re-run picks up only what is missing), the
first page load gets a longer wait, and each worker pauses between leagues. `WORKERS`
league-seasons are scraped at once, each in its own Chrome and its own files; every log line
names the league-season it comes from. Ctrl+C drops the jobs not yet started and lets the
running ones finish.

One code path covers every page layout. A page without stage tabs is scraped as it
opens; otherwise each stage named in the league's `keep` list is clicked and scraped in
turn, its name going into the `s1_stage` column.

Run: `uv run python -m scrapers.schedule` (the `enabled` seasons)
     `uv run python -m scrapers.schedule --leagues "ENG LCH,SCO PR" --before-year 2026 --list`
"""

import argparse
import io
import logging
import sys
import threading
import time
from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from itertools import combinations
from typing import Any

import pandas as pd
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
from scrapers.links import LeagueSeason, Selection, get_league_seasons
from scrapers.parsers import (
    attr,
    parse_ah_odds,
    parse_final_table,
    parse_ou_odds,
    parse_schedulis_row,
)

logging.basicConfig(
    level=logging.INFO,
    # A worker thread is named after its league-season (`_start`), so the lines of jobs
    # running at once can be told apart.
    format="%(asctime)s %(levelname)s [%(threadName)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# League-seasons scraped at once, as in `scrapers/detail.py`.
WORKERS = 4

# The first page load of a league can be slow: one took more than the default 20 s on
# 2026-10-06 and loaded within 45 s on the retry. Later clicks keep the default.
FIRST_LOAD_TIMEOUT = 45
# Between two leagues of one worker. The site sets no crawl delay, so the pace is ours.
PAUSE_BETWEEN_JOBS = 12


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
        wait_for_schedule_rows(driver, timeout=FIRST_LOAD_TIMEOUT)
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
    stale = 0
    for row in rows:
        parsed = parse_schedulis_row(row)
        if parsed is None:
            continue
        parsed.update(context)
        parsed.update(secondary.get(parsed["match_id"], {}))
        stale += bool(drop_stale_odds(parsed))
        round_matches.append(parsed)

    label = f"{ctx.stage.name} round {round_number}".strip()
    logger.info("  %s: %d finished / %d rows", label, len(round_matches), len(rows))
    if stale:
        logger.info("  %s: %d rows showed a market they do not carry; emptied", label, stale)
    return round_matches


# Each odds market and the row fields its three cells map to, in cell order.
_MARKETS = {
    "1x2": ("s1_odds_1x2_open_home", "s1_odds_1x2_open_draw", "s1_odds_1x2_open_away"),
    "ou": ("s1_odds_ou_open_over", "s1_odds_ou_open_line", "s1_odds_ou_open_under"),
    "ah": ("s1_odds_ah_open_home", "s1_odds_ah_open_line", "s1_odds_ah_open_away"),
}

# Each secondary odds type, read after the 1X2 view in this order.
_SECONDARY_ODDS = (("ou", parse_ou_odds, _MARKETS["ou"]), ("ah", parse_ah_odds, _MARKETS["ah"]))

# The markets a match does not carry, by the pairs of markets whose cells show the same
# numbers. One widget shows the markets in turn, 1X2, then O/U, then AH, then 1X2 again,
# and a market the match does not carry keeps the previous one's numbers after the switch.
_MISSING_BY_REPEATS: dict[frozenset[tuple[str, str]], list[str]] = {
    # 1X2 only: the O/U and AH views kept its prices (97 rows in 8 league-seasons on
    # 2026-10-08, never a whole round).
    frozenset({("1x2", "ou"), ("1x2", "ah"), ("ou", "ah")}): ["ou", "ah"],
    frozenset({("1x2", "ou")}): ["ou"],
    frozenset({("ou", "ah")}): ["ah"],
    # No 1X2: switching back to it kept the AH cells, so its "draw" was the AH line (1 row).
    frozenset({("1x2", "ah")}): ["1x2"],
}


def drop_stale_odds(row: dict[str, Any]) -> list[str]:
    """Empty each market whose three cells repeat another market's; return the ones emptied.

    Real markets never repeat each other (none of 29,478 rows): a 1X2 middle cell is a
    draw price, an O/U or AH middle cell a line. Which repeat means which market is
    missing is `_MISSING_BY_REPEATS`.
    """
    cells = {market: tuple(row.get(f) for f in fields) for market, fields in _MARKETS.items()}
    repeats = frozenset(
        (a, b)
        for a, b in combinations(_MARKETS, 2)
        if cells[a] == cells[b] and any(v is not None for v in cells[a])
    )
    missing = _MISSING_BY_REPEATS.get(repeats, [])
    for market in missing:
        row.update(dict.fromkeys(_MARKETS[market]))
    return list(missing)


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


@dataclass(frozen=True)
class Outcome:
    """What one job left behind: rows written and dropped, or the error that stopped it."""

    job: LeagueSeason
    matches: int = 0
    dropped: int = 0
    error: str = ""


def scraped_league_seasons() -> set[tuple[int, str]]:
    """(league id, season) of every league-season already in a stage-1 schedule file.

    Read from inside the files rather than from their names: a file is named after the
    page's title, which need not match the config's name ("England Championship").
    """
    done: set[tuple[int, str]] = set()
    for path in paths.schedule_csvs(1):
        head = pd.read_csv(
            path, usecols=["s1_league_id", "s1_season"], dtype={"s1_season": str}, nrows=1
        )
        if not head.empty:
            done.add((int(head.at[0, "s1_league_id"]), str(head.at[0, "s1_season"])))
    return done


def plan_jobs(
    jobs: Iterable[LeagueSeason], done: set[tuple[int, str]], force: bool
) -> tuple[list[LeagueSeason], list[LeagueSeason]]:
    """Split the chosen jobs into (to scrape, already on disk). `force` scrapes them all."""
    to_scrape: list[LeagueSeason] = []
    on_disk: list[LeagueSeason] = []
    for job in jobs:
        skip = not force and (job.league_id, job.season) in done
        (on_disk if skip else to_scrape).append(job)
    return to_scrape, on_disk


def _save(job: LeagueSeason, scrape: _Scrape) -> Outcome:
    league = league_slug(job.country, scrape.league_name)
    matches = _validate(scrape.matches, ScheduleRow, "match")
    table = _validate(scrape.final_table, FinalTableRow, "final-table team")
    if matches:
        save_unless_shrinking(
            matches, paths.schedule_path(1, league, job.season), SCHEDULE_RAW_COLUMNS
        )
    if table:
        save_unless_shrinking(
            table, paths.final_table_path(league, job.season), FINAL_TABLE_COLUMNS
        )
    dropped = len(scrape.matches) - len(matches) + len(scrape.final_table) - len(table)
    logger.info(
        "%s %s: %d matches, %d table rows, %d dropped",
        job.code,
        job.season,
        len(matches),
        len(table),
        dropped,
    )
    return Outcome(job, matches=len(matches), dropped=dropped)


def _run_job(job: LeagueSeason) -> Outcome:
    """Scrape and save one league-season. A failure is logged and returned, never raised."""
    try:
        return _save(job, scrape_league(job))
    except Exception as exc:  # one league must not end a run of many
        logger.exception("FAILED %s %s (%s)", job.code, job.season, job.url)
        return Outcome(job, error=f"{type(exc).__name__}: {exc}".splitlines()[0])


def summarise(outcomes: list[Outcome], on_disk: list[LeagueSeason]) -> int:
    """Print the run's summary; return how many jobs failed."""
    failed = [o for o in outcomes if o.error]
    print(
        f"\n{len(outcomes) - len(failed)} scraped, {len(on_disk)} already on disk, "
        f"{len(failed)} failed, {sum(o.dropped for o in outcomes)} rows dropped by validation"
    )
    for outcome in failed:
        print(f"  FAILED {outcome.job.code} {outcome.job.season}: {outcome.error}")
    if failed:
        print("  Re-run the same command: what is already on disk is skipped.")
    return len(failed)


def scrape_all(
    selection: Selection | None = None, *, force: bool = False, list_only: bool = False
) -> int:
    """Scrape the chosen league-seasons into their stage-1 files; return the failure count."""
    to_scrape, on_disk = plan_jobs(get_league_seasons(selection), scraped_league_seasons(), force)
    for job in on_disk:
        print(f"  on disk   {job.code:8s} {job.season:9s} {job.name}", flush=True)
    for job in to_scrape:
        print(f"  to scrape {job.code:8s} {job.season:9s} {job.name}", flush=True)
    # Flushed: in a run logged to a file, the plan must show before hours of progress lines.
    print(f"{len(to_scrape)} to scrape, {len(on_disk)} already on disk", flush=True)
    if list_only:
        return 0

    pool = ThreadPoolExecutor(max_workers=WORKERS)
    futures = [pool.submit(_start, n, len(to_scrape), job) for n, job in enumerate(to_scrape, 1)]
    try:
        pending = set(futures)
        while pending:  # waiting with a timeout keeps Ctrl+C working on Windows
            pending = wait(pending, timeout=1).not_done
    finally:
        pool.shutdown(cancel_futures=True)
    return summarise([future.result() for future in futures], on_disk)


def _start(number: int, total: int, job: LeagueSeason) -> Outcome:
    """One worker's job: named after its league-season, paused unless it is among the first."""
    threading.current_thread().name = f"{job.code} {job.season}"
    if number > WORKERS:
        time.sleep(PAUSE_BETWEEN_JOBS)
    logger.info("[%d/%d] Scraping %s", number, total, job.url)
    return _run_job(job)


def main() -> None:
    # Output sent to a file is written in the Windows code page, which cannot hold every
    # character a league name can have; UTF-8 can.
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Scrape league schedules into data/finished/1_raw/."
    )
    which = parser.add_mutually_exclusive_group()
    which.add_argument("--leagues", help='config codes, comma-separated, e.g. "ENG LCH,SCO PR"')
    which.add_argument(
        "--all", action="store_true", dest="all_leagues", help="every league in the config"
    )
    parser.add_argument(
        "--before-year", type=int, help="only seasons that started before this year"
    )
    parser.add_argument(
        "--list", action="store_true", dest="list_only", help="print the jobs; open no page"
    )
    parser.add_argument("--force", action="store_true", help="scrape again what is already on disk")
    args = parser.parse_args()
    codes = tuple(code.strip() for code in (args.leagues or "").split(",") if code.strip())
    selection = Selection(codes, args.all_leagues, args.before_year)
    failed = scrape_all(selection, force=args.force, list_only=args.list_only)
    raise SystemExit(1 if failed else 0)


if __name__ == "__main__":
    main()
