"""Fourth-stage scraper: the live page, into two global stores.

One page render per match fills both:

  - `data/archived/raw/goals.csv` — one row per goal (`domain/goal.py`);
  - `data/archived/raw/events.csv` — one row per card or substitution (`domain/event.py`).

Goal timings and discipline are *team traits*, so they are needed not just for the corpus
matches but for the matches in each side's recent form and head-to-head history — those
are what a pre-match feature is built from. Those referenced matches come from cups,
European competition and other leagues, which is why both stores are global and keyed by
match id rather than split per league-season.

The work list is therefore the union of:

  - every match in `data/archived/raw/<league>_<season>.csv` (the corpus itself), and
  - every match referenced by a `*_lastN_match_id` column in the detail files.

That union is **deduplicated before anything is fetched**. The same historical match is
referenced by many fixtures -- measured at 17.8 references per match, of which only ~14 are
new by the twentieth page, and 48% are already corpus matches -- so fetching once per
unique id rather than once per reference is what makes the scrape affordable.

**The two stores have separate attempt logs**, `goals_done.csv` and `events_done.csv`, and
resume is keyed on those rather than on the stores themselves: a 0-0 produces no goal rows
and a clean match produces no event rows, so deriving "already scraped" from a store would
re-fetch every such match on every run, forever. Keeping the logs apart also means the
events store could be added to a corpus already scraped for goals: such a match is fetched
exactly once more, writes only the store it is missing, and is then done for both.

Run: `uv run python -m scrapers.goals [--limit N] [--sections home,away,h2h] [--depth 6]`
"""

import argparse
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from typing import Any

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver

from domain import paths, scope
from domain.columns import (
    EVENTS_DONE_COLUMNS,
    EVENTS_ORDERED_COLUMNS,
    GOALS_DONE_COLUMNS,
    GOALS_ORDERED_COLUMNS,
    MATCHES_PER_SECTION,
)
from domain.event import Event
from domain.goal import Goal
from scrapers.browser_pool import BrowserPool
from scrapers.csv_io import append_rows
from scrapers.driver import get_live_page
from scrapers.event_parsers import parse_match_events
from scrapers.goal_parsers import parse_goal_events

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

WORKERS = 3
SECTIONS = ("home", "away", "h2h")

_POOL = BrowserPool()


def scrape_match_live(
    driver: webdriver.Chrome, match_id: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Mode-agnostic core: render one live page, return its goals and its events.

    Both come from a single render, which is the whole reason the two stores share a
    scraper — the page is the expensive part and it carries both.
    """
    get_live_page(driver, match_id)
    soup = BeautifulSoup(driver.page_source, "html.parser")

    goals = [
        Goal(match_id=str(match_id), **event).model_dump() for event in parse_goal_events(soup)
    ]
    events = [
        Event(match_id=str(match_id), **event).model_dump() for event in parse_match_events(soup)
    ]

    return goals, events


# --- work list ----------------------------------------------------------------


def corpus_ids() -> dict[str, int | None]:
    """Match ids from the base league CSVs, mapped to their league id."""
    found: dict[str, int | None] = {}
    for path in paths.base_league_csvs():
        base_df = pd.read_csv(path, usecols=lambda column: column in {"match_id", "league_id"})
        for row in base_df.itertuples(index=False):
            found.setdefault(str(row.match_id), _as_int(getattr(row, "league_id", None)))

    return found


def history_ids(sections: tuple[str, ...], depth: int) -> dict[str, int | None]:
    """Match ids referenced by the detail files' per-match history blocks.

    Detail files scraped before 2026-09-22 have no `*_match_id` columns; those simply
    contribute nothing, and the caller reports the shortfall rather than failing.
    """
    wanted = {
        f"{section}_last{slot}_{field}"
        for section in sections
        for slot in range(1, depth + 1)
        for field in ("match_id", "league_id", "league", "date")
    }
    prefixes = [f"{section}_last{slot}_" for section in sections for slot in range(1, depth + 1)]

    found: dict[str, int | None] = {}
    for base in paths.base_league_csvs():
        detail = paths.detail_path(base)
        if not os.path.exists(detail):
            continue

        detail_df = pd.read_csv(detail, usecols=lambda column: column in wanted, low_memory=False)
        for prefix in prefixes:
            _collect_block_ids(detail_df, prefix, found)

    return found


def _collect_block_ids(detail_df: pd.DataFrame, prefix: str, found: dict[str, int | None]) -> None:
    """Fold one `<section>_last<n>_` block's referenced ids into `found`.

    First writer wins, so an id already seen keeps its original league id rather than
    being overwritten by a later, equally valid reference to the same match.
    """
    id_col = f"{prefix}match_id"
    if id_col not in detail_df.columns:
        return

    blank = pd.Series([None] * len(detail_df), index=detail_df.index)
    leagues = detail_df.get(f"{prefix}league_id", blank)
    names = detail_df.get(f"{prefix}league", blank)
    dates = detail_df.get(f"{prefix}date", blank)

    for raw_id, raw_league, name, date in zip(
        detail_df[id_col], leagues, names, dates, strict=True
    ):
        match_id = _as_id(raw_id)
        # Friendlies carry no timings and pre-2023 pages are truncated, so they are
        # dropped here rather than fetched and discarded later -- see domain/scope.py.
        if match_id and scope.in_scope(name, date):
            found.setdefault(match_id, _as_int(raw_league))


def done_ids(path: str) -> set[str]:
    """Match ids already attempted, from one attempt log."""
    if not os.path.exists(path):
        return set()
    return set(pd.read_csv(path, usecols=["match_id"])["match_id"].astype(str))


def build_work_list(sections: tuple[str, ...], depth: int) -> dict[str, int | None]:
    """Everything that needs fetching, deduplicated.

    A match is pending when *either* store is missing it, because one render fills both.
    """
    corpus = corpus_ids()
    history = history_ids(sections, depth)
    union: dict[str, int | None] = {**history, **corpus}  # corpus league id wins

    goals_done = done_ids(paths.goals_done_path())
    events_done = done_ids(paths.events_done_path())
    pending = {k: v for k, v in union.items() if k not in goals_done or k not in events_done}

    logger.info(
        "work list: %d corpus + %d referenced = %d unique "
        "(goals done %d, events done %d, %d pending)",
        len(corpus),
        len(history),
        len(union),
        len(goals_done),
        len(events_done),
        len(pending),
    )

    if history and not any(k not in corpus for k in history):
        logger.warning("no history ids outside the corpus — are the detail files stale?")
    return pending


def _as_int(value: Any) -> int | None:
    try:
        return None if value is None or pd.isna(value) else int(value)
    except (TypeError, ValueError):
        return None


def _as_id(value: Any) -> str:
    """History ids arrive from pandas as floats when the column has gaps."""
    if value is None or pd.isna(value):
        return ""

    text = str(value).strip()
    return text[:-2] if text.endswith(".0") else text


# --- orchestration ------------------------------------------------------------


def _scrape_one(
    match_id: str,
) -> tuple[str, list[dict[str, Any]], list[dict[str, Any]], Exception | None]:
    """Run in a worker thread; errors come back rather than cancelling the batch."""
    try:
        goals, events = scrape_match_live(_POOL.driver(), match_id)
        return match_id, goals, events, None
    except Exception as exc:  # the id stays pending for the next run
        return match_id, [], [], exc


def _stamp() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _store_rows(
    rows: list[dict[str, Any]],
    league_id: int | None,
    match_id: str,
    store_path: str,
    store_columns: list[str],
    log_path: str,
    log_columns: list[str],
    count_field: str,
) -> None:
    """Append one match's rows and its attempt-log entry.

    Both writes happen together so the log can never claim a match whose rows are missing.
    The caller holds the lock.
    """
    for row in rows:
        row["league_id"] = league_id

    append_rows(rows, store_path, store_columns)
    append_rows(
        [{"match_id": match_id, "scraped_at": _stamp(), count_field: len(rows)}],
        log_path,
        log_columns,
    )


def scrape_goals(
    limit: int | None = None, sections: tuple[str, ...] = SECTIONS, depth: int = 6
) -> None:
    pending = build_work_list(sections, depth)
    ids = list(pending)[:limit] if limit is not None else list(pending)
    if not ids:
        logger.info("nothing to do")
        return

    goals_done = done_ids(paths.goals_done_path())
    events_done = done_ids(paths.events_done_path())
    csv_lock = threading.Lock()

    with _POOL, ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(_scrape_one, mid): mid for mid in ids}
        for i, future in enumerate(as_completed(futures), 1):
            match_id, goals, events, exc = future.result()
            if exc is not None:
                logger.warning("  [%d/%d] %s failed: %s", i, len(ids), match_id, exc)
                continue

            league_id = pending.get(match_id)
            # Only the store that is actually missing gets written, so a match fetched
            # purely to backfill events does not duplicate its goal rows.
            with csv_lock:
                if match_id not in goals_done:
                    _store_rows(
                        goals,
                        league_id,
                        match_id,
                        paths.goals_path(),
                        GOALS_ORDERED_COLUMNS,
                        paths.goals_done_path(),
                        GOALS_DONE_COLUMNS,
                        "n_goals",
                    )

                if match_id not in events_done:
                    _store_rows(
                        events,
                        league_id,
                        match_id,
                        paths.events_path(),
                        EVENTS_ORDERED_COLUMNS,
                        paths.events_done_path(),
                        EVENTS_DONE_COLUMNS,
                        "n_events",
                    )

            logger.info(
                "  [%d/%d] %s -> %d goals, %d events",
                i,
                len(ids),
                match_id,
                len(goals),
                len(events),
            )

    logger.info("done — run `python -m features.enrich` to rebuild the enriched join")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=None, help="cap this batch")
    parser.add_argument(
        "--sections",
        default=",".join(SECTIONS),
        help="history sections to pull ids from (home,away,h2h). h2h reaches back years "
        "and is the least-reused, so dropping it shortens a first run considerably",
    )
    parser.add_argument(
        "--depth", type=int, default=MATCHES_PER_SECTION, help="matches per section"
    )

    args = parser.parse_args()
    chosen = tuple(s.strip() for s in args.sections.split(",") if s.strip())

    scrape_goals(limit=args.limit, sections=chosen, depth=args.depth)


if __name__ == "__main__":
    main()
