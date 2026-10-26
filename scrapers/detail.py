"""Second-stage scraper: render each match's detail page and produce one wide
feature row per match, keyed by `match_id`.

Enrichment (now): match ids come from the finished-match league CSVs in `data/archived/raw/`.
A future prediction mode can feed upcoming ids to `scrape_match_detail` unchanged.

Writes only `data/archived/raw/<league>_<season>_detail.csv`. The join against the base league
CSV is not a scrape and lives in `features/enrich.py` — run that afterwards to refresh
`data/archived/processed/<league>_<season>_enriched.csv`.

Run: `uv run python -m scrapers.detail [--limit N]`
"""

import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

from domain import paths
from domain.columns import DETAIL_ORDERED_COLUMNS
from domain.match_detail import MatchDetail
from scrapers import detail_parsers as dp
from scrapers.browser_pool import BrowserPool
from scrapers.constants import (
    DETAIL_AWAY_RECENT_ROWS,
    DETAIL_H2H_ROWS,
    DETAIL_HOME_RECENT_ROWS,
)
from scrapers.csv_io import append_rows
from scrapers.driver import get_detail_page

logger = logging.getLogger(__name__)

WORKERS = 3

# One Chrome per worker thread, spanning the whole run rather than one league, so a
# browser is started once and reused across every league it processes.
_POOL = BrowserPool()


def scrape_match_detail(driver: webdriver.Chrome, match_id: str) -> dict[str, Any]:
    """Mode-agnostic core: render the detail page and return a validated feature dict."""

    get_detail_page(driver, match_id)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    home_records = dp.rows_to_records(soup.select(DETAIL_HOME_RECENT_ROWS))
    away_records = dp.rows_to_records(soup.select(DETAIL_AWAY_RECENT_ROWS))
    h2h_records = dp.rows_to_records(soup.select(DETAIL_H2H_ROWS))
    home_id = dp.subject_team_id(home_records)
    away_id = dp.subject_team_id(away_records)

    # Aggregate + odds/strength features go through the validated MatchDetail model.
    agg: dict[str, Any] = {"match_id": str(match_id)}
    agg.update(dp.parse_odds_1x2(soup))
    agg.update(dp.aggregate_recent(home_records, home_id, "home"))
    agg.update(dp.aggregate_recent(away_records, away_id, "away"))
    agg.update(dp.aggregate_h2h(h2h_records, home_id))
    agg.update(dp.parse_strength(soup))
    agg.update(dp.parse_guess(soup))
    agg.update(dp.parse_fixtures(soup))
    row = MatchDetail(**agg).model_dump()

    # Per-match column blocks (home_lastN_/away_lastN_/h2h_lastN_) are plain data.
    row.update(dp.flatten_history(home_records, home_id, "home"))
    row.update(dp.flatten_history(away_records, away_id, "away"))
    row.update(dp.flatten_history(h2h_records, home_id, "h2h"))

    return row


def _done_ids(detail_path: str) -> set[str]:
    """The match ids already in the detail file, empty when the file does not exist yet."""

    if not os.path.exists(detail_path):
        return set()

    return set(pd.read_csv(detail_path, usecols=["match_id"])["match_id"].astype(str))


@dataclass(frozen=True)
class _Scraped:
    """One detail page's result: its row, or the error that stopped it (row None)."""

    match_id: str
    row: dict[str, Any] | None
    error: Exception | None


def _scrape_one(match_id: str) -> _Scraped:
    """One match scraped in a worker thread with that thread's own driver. Errors come back,
    not raised, so one bad match does not cancel the others already in flight."""

    driver = _POOL.driver()
    try:
        return _Scraped(match_id=match_id, row=scrape_match_detail(driver, match_id), error=None)
    except Exception as exc:  # keep going; the id stays pending for the next run
        return _Scraped(match_id=match_id, row=None, error=exc)


def enrich_league(
    pool: ThreadPoolExecutor,
    base_path: str,
    limit: int | None,
    csv_lock: threading.Lock,
) -> None:
    """Scrape one league CSV's pending detail pages, at most `limit`, appending each row."""

    league = os.path.splitext(os.path.basename(base_path))[0]
    detail_path = paths.detail_path(base_path)

    base_df = pd.read_csv(base_path)
    base_df["match_id"] = base_df["match_id"].astype(str)
    all_ids = list(dict.fromkeys(base_df["match_id"]))  # preserve order, dedup

    done = _done_ids(detail_path)
    pending = [match_id for match_id in all_ids if match_id not in done]
    if limit is not None:
        pending = pending[:limit]

    logger.info(
        "%s: %d matches, %d done, scraping %d",
        league,
        len(all_ids),
        len(done),
        len(pending),
    )

    futures = {pool.submit(_scrape_one, match_id): match_id for match_id in pending}
    for i, future in enumerate(as_completed(futures), 1):
        scraped = future.result()
        match_id, row = scraped.match_id, scraped.row
        if row is None:
            logger.warning("  [%d/%d] %s failed: %s", i, len(pending), match_id, scraped.error)
            continue

        # Append each row immediately so an interrupted run stays resumable;
        # the lock serialises writes since all workers share one CSV per league.
        with csv_lock:
            append_rows([row], detail_path, DETAIL_ORDERED_COLUMNS)

        logger.info(
            "  [%d/%d] %s odds=%s h2h=%s",
            i,
            len(pending),
            match_id,
            row.get("odds_bookmaker"),
            row.get("h2h_played"),
        )


def enrich_finished(limit: int | None = None) -> None:
    """Scrape the pending detail pages of every base league CSV, at most `limit` per CSV."""

    csv_lock = threading.Lock()
    with _POOL, ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for base_path in paths.base_league_csvs():
            enrich_league(pool, base_path, limit, csv_lock)

    logger.info("done — run `python -m features.enrich` to rebuild the enriched join")


def _parse_limit(argv: list[str]) -> int | None:
    """The number after `--limit`, None when the option is not given."""

    if "--limit" in argv:
        return int(argv[argv.index("--limit") + 1])

    return None


def main() -> None:
    """Entry point: scrape the detail pages still missing, at most `--limit` of them."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    enrich_finished(limit=_parse_limit(sys.argv))


if __name__ == "__main__":
    main()
