"""Fourth-stage scraper: goal timings, into the global store `data/raw/goals.csv`.

Goal timings are a *team trait*, so they are needed not just for the corpus matches but for
the matches in each side's recent form and head-to-head history — those are what a
pre-match feature is built from. Those referenced matches come from cups, European
competition and other leagues, which is why the store is global and keyed by match id
rather than split per league-season.

The work list is therefore the union of:

  - every match in `data/raw/<league>_<season>.csv` (the corpus itself), and
  - every match referenced by a `*_lastN_match_id` column in the detail files.

That union is **deduplicated before anything is fetched**. The same historical match is
referenced by many fixtures -- measured at 17.8 references per match, of which only ~14 are
new by the twentieth page, and 48% are already corpus matches -- so fetching once per
unique id rather than once per reference is what makes the scrape affordable.

Resume is keyed on `data/raw/goals_done.csv`, not on the goal rows, because a 0-0 match
produces no goal rows at all. Deriving "already scraped" from the goal store would re-fetch
every goalless match on every run, forever.

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
from domain.columns import GOALS_DONE_COLUMNS, GOALS_ORDERED_COLUMNS, MATCHES_PER_SECTION
from domain.goal import Goal
from scrapers.browser_pool import BrowserPool
from scrapers.csv_io import append_rows
from scrapers.driver import get_live_page
from scrapers.goal_parsers import parse_goal_events

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

WORKERS = 4
SECTIONS = ("home", "away", "h2h")

_POOL = BrowserPool()


def scrape_match_goals(driver: webdriver.Chrome, match_id: str) -> list[dict[str, Any]]:
    """Mode-agnostic core: render one live page and return its validated goal rows."""
    get_live_page(driver, match_id)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    return [Goal(match_id=str(match_id), **event).model_dump() for event in parse_goal_events(soup)]


# --- work list ----------------------------------------------------------------


def corpus_ids() -> dict[str, int | None]:
    """Match ids from the base league CSVs, mapped to their league id."""
    found: dict[str, int | None] = {}
    for path in paths.base_league_csvs():
        frame = pd.read_csv(path, usecols=lambda c: c in {"match_id", "league_id"})
        for row in frame.itertuples(index=False):
            found.setdefault(str(row.match_id), _as_int(getattr(row, "league_id", None)))
    return found


def history_ids(sections: tuple[str, ...], depth: int) -> dict[str, int | None]:
    """Match ids referenced by the detail files' per-match history blocks.

    Detail files scraped before 2026-09-22 have no `*_match_id` columns; those simply
    contribute nothing, and the caller reports the shortfall rather than failing.
    """
    wanted = {
        f"{section}_last{n}_{field}"
        for section in sections
        for n in range(1, depth + 1)
        for field in ("match_id", "league_id", "league", "date")
    }
    prefixes = [f"{section}_last{n}_" for section in sections for n in range(1, depth + 1)]
    found: dict[str, int | None] = {}
    for base in paths.base_league_csvs():
        detail = paths.detail_path(base)
        if not os.path.exists(detail):
            continue
        frame = pd.read_csv(detail, usecols=lambda c: c in wanted, low_memory=False)
        for prefix in prefixes:
            _collect_block_ids(frame, prefix, found)
    return found


def _collect_block_ids(frame: pd.DataFrame, prefix: str, found: dict[str, int | None]) -> None:
    """Fold one `<section>_last<n>_` block's referenced ids into `found`.

    First writer wins, so an id already seen keeps its original league id rather than
    being overwritten by a later, equally valid reference to the same match.
    """
    id_col = f"{prefix}match_id"
    if id_col not in frame.columns:
        return
    blank = pd.Series([None] * len(frame), index=frame.index)
    leagues = frame.get(f"{prefix}league_id", blank)
    names = frame.get(f"{prefix}league", blank)
    dates = frame.get(f"{prefix}date", blank)
    for raw_id, raw_league, name, date in zip(frame[id_col], leagues, names, dates, strict=True):
        match_id = _as_id(raw_id)
        # Friendlies carry no timings and pre-2023 pages are truncated, so they are
        # dropped here rather than fetched and discarded later -- see domain/scope.py.
        if match_id and scope.in_scope(name, date):
            found.setdefault(match_id, _as_int(raw_league))


def done_ids() -> set[str]:
    """Match ids already attempted, from the attempt log."""
    path = paths.goals_done_path()
    if not os.path.exists(path):
        return set()
    return set(pd.read_csv(path, usecols=["match_id"])["match_id"].astype(str))


def build_work_list(sections: tuple[str, ...], depth: int) -> dict[str, int | None]:
    """Everything that needs fetching, deduplicated and with finished ids removed."""
    corpus = corpus_ids()
    history = history_ids(sections, depth)
    union: dict[str, int | None] = {**history, **corpus}  # corpus league id wins
    done = done_ids()
    pending = {k: v for k, v in union.items() if k not in done}

    logger.info(
        "work list: %d corpus + %d referenced = %d unique (%d already done, %d pending)",
        len(corpus),
        len(history),
        len(union),
        len(union) - len(pending),
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


def _scrape_one(match_id: str) -> tuple[str, list[dict[str, Any]], Exception | None]:
    """Run in a worker thread; errors come back rather than cancelling the batch."""
    try:
        return match_id, scrape_match_goals(_POOL.driver(), match_id), None
    except Exception as exc:  # the id stays pending for the next run
        return match_id, [], exc


def scrape_goals(
    limit: int | None = None, sections: tuple[str, ...] = SECTIONS, depth: int = 6
) -> None:
    pending = build_work_list(sections, depth)
    ids = list(pending)[:limit] if limit is not None else list(pending)
    if not ids:
        logger.info("nothing to do")
        return

    csv_lock = threading.Lock()
    with _POOL, ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(_scrape_one, mid): mid for mid in ids}
        for i, future in enumerate(as_completed(futures), 1):
            match_id, goals, exc = future.result()
            if exc is not None:
                logger.warning("  [%d/%d] %s failed: %s", i, len(ids), match_id, exc)
                continue
            league_id = pending.get(match_id)
            for goal in goals:
                goal["league_id"] = league_id
            # Both files are written together and under one lock, so the attempt log can
            # never claim a match that has no rows behind it.
            with csv_lock:
                append_rows(goals, paths.goals_path(), GOALS_ORDERED_COLUMNS)
                append_rows(
                    [
                        {
                            "match_id": match_id,
                            "scraped_at": datetime.now(UTC).isoformat(timespec="seconds"),
                            "n_goals": len(goals),
                        }
                    ],
                    paths.goals_done_path(),
                    GOALS_DONE_COLUMNS,
                )
            logger.info("  [%d/%d] %s -> %d goals", i, len(ids), match_id, len(goals))
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
