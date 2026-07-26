"""Second-stage scraper: render each match's detail page and produce one wide
feature row per match, joined back to the base league CSV by `match_id`.

Enrichment (now): match ids come from the finished-match league CSVs in `data/`.
A future prediction mode can feed upcoming ids to `scrape_match_detail` unchanged.

Run: `uv run python -m scrapers.detail [--limit N]`
"""

import glob
import logging
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, cast

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

from domain.columns import DETAIL_ORDERED_COLUMNS
from domain.match_detail import MatchDetail
from scrapers import detail_parsers as dp
from scrapers.constants import (
    DETAIL_AWAY_RECENT_ROWS,
    DETAIL_H2H_ROWS,
    DETAIL_HOME_RECENT_ROWS,
)
from scrapers.csv_io import DATA_DIR, append_rows, write_ordered_csv
from scrapers.driver import get_detail_page, get_driver

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

WORKERS = 4

# One Chrome driver per worker thread (a Selenium session isn't safe to share
# across threads), created lazily on first use and reused for every task that
# thread picks up afterward — across leagues, since the pool spans the whole run.
_thread_local = threading.local()
_drivers: list[webdriver.Chrome] = []
_drivers_lock = threading.Lock()


def _thread_driver() -> webdriver.Chrome:
    driver = getattr(_thread_local, "driver", None)
    if driver is None:
        driver = get_driver()
        _thread_local.driver = driver
        with _drivers_lock:
            _drivers.append(driver)
    return driver


def _quit_all_drivers() -> None:
    for driver in _drivers:
        driver.quit()
    _drivers.clear()


def scrape_match_detail(driver: webdriver.Chrome, match_id: str) -> dict[str, Any]:
    """Mode-agnostic core: render the detail page and return a validated feature dict."""
    get_detail_page(driver, match_id)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    home_records = dp._rows_to_records(soup.select(DETAIL_HOME_RECENT_ROWS))
    away_records = dp._rows_to_records(soup.select(DETAIL_AWAY_RECENT_ROWS))
    h2h_records = dp._rows_to_records(soup.select(DETAIL_H2H_ROWS))
    home_id = dp._subject_team_id(home_records)
    away_id = dp._subject_team_id(away_records)

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


def _base_league_csvs() -> list[str]:
    """Base league CSVs in data/ (exclude generated _detail / _enriched files)."""
    return [
        p
        for p in sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
        if not p.endswith("_detail.csv") and not p.endswith("_enriched.csv")
    ]


def _done_ids(detail_path: str) -> set[str]:
    if not os.path.exists(detail_path):
        return set()
    return set(pd.read_csv(detail_path, usecols=["match_id"])["match_id"].astype(str))


def _scrape_one(mid: str) -> tuple[str, dict[str, Any] | None, Exception | None]:
    """Run in a worker thread with that thread's own driver; errors come back,
    not raised, so one bad match doesn't cancel the others already in flight."""
    driver = _thread_driver()
    try:
        return mid, scrape_match_detail(driver, mid), None
    except Exception as exc:  # keep going; the id stays pending for the next run
        return mid, None, exc


def enrich_league(
    pool: ThreadPoolExecutor,
    base_path: str,
    limit: int | None,
    csv_lock: threading.Lock,
) -> None:
    league = os.path.splitext(os.path.basename(base_path))[0]
    detail_path = base_path.replace(".csv", "_detail.csv")

    base = pd.read_csv(base_path)
    base["match_id"] = base["match_id"].astype(str)
    all_ids = list(dict.fromkeys(base["match_id"]))  # preserve order, dedup

    done = _done_ids(detail_path)
    pending = [mid for mid in all_ids if mid not in done]
    if limit is not None:
        pending = pending[:limit]

    logger.info(
        "%s: %d matches, %d done, scraping %d",
        league,
        len(all_ids),
        len(done),
        len(pending),
    )

    futures = {pool.submit(_scrape_one, mid): mid for mid in pending}
    for i, future in enumerate(as_completed(futures), 1):
        mid, row, exc = future.result()
        if row is None:
            logger.warning("  [%d/%d] %s failed: %s", i, len(pending), mid, exc)
            continue
        # Append each row immediately so an interrupted run stays resumable;
        # the lock serializes writes since all workers share one CSV per league.
        with csv_lock:
            append_rows([row], detail_path, DETAIL_ORDERED_COLUMNS)
        logger.info(
            "  [%d/%d] %s odds=%s h2h=%s",
            i,
            len(pending),
            mid,
            row.get("odds_bookmaker"),
            row.get("h2h_played"),
        )

    _write_enriched(base, detail_path, base_path.replace(".csv", "_enriched.csv"))


def _write_enriched(base: pd.DataFrame, detail_path: str, enriched_path: str) -> None:
    if not os.path.exists(detail_path):
        return
    detail = pd.read_csv(detail_path)
    detail["match_id"] = detail["match_id"].astype(str)
    detail = detail.drop_duplicates("match_id", keep="last")
    merged = base.merge(detail, on="match_id", how="left", suffixes=("", "_detail"))
    feature_cols = [c for c in DETAIL_ORDERED_COLUMNS if c != "match_id"]
    rows = cast(list[dict[str, Any]], merged.to_dict("records"))
    write_ordered_csv(rows, enriched_path, list(base.columns) + feature_cols)


def enrich_finished(limit: int | None = None) -> None:
    csv_lock = threading.Lock()
    try:
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            for base_path in _base_league_csvs():
                enrich_league(pool, base_path, limit, csv_lock)
    finally:
        _quit_all_drivers()


def _parse_limit(argv: list[str]) -> int | None:
    if "--limit" in argv:
        return int(argv[argv.index("--limit") + 1])
    return None


def main() -> None:
    enrich_finished(limit=_parse_limit(sys.argv))


if __name__ == "__main__":
    main()
