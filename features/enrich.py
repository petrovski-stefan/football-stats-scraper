"""Join each raw league scrape to its raw detail scrape, one enriched file per season.

The first derived artefact in the pipeline, and the reason it is here rather than in
`scrapers/`: a left join adds no scraped information, so it is not a scrape. Splitting
it out also means a stale or deleted `_enriched.csv` can be rebuilt from the raw files
in seconds — previously the only way to regenerate one was to invoke the detail
scraper, which starts Selenium even when there is nothing left to fetch.

Reads `data/raw/`, writes `data/processed/`. The enriched file is the base columns, then
the detail feature columns, then — when the goal-timing store exists — the derived timing
aggregates from `features/goals.py`. Those are the one set of columns this module does not
merely copy across, and they are appended last so the base-then-detail order is unchanged.

Run: `uv run python -m features.enrich`
"""

import logging
import os

import pandas as pd

from domain import paths
from domain.columns import DETAIL_ORDERED_COLUMNS
from features import goals as goal_features

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_enriched(base_path: str) -> str | None:
    """Join one league-season and write it. Returns the path, or None if not yet scraped."""
    detail_path = paths.detail_path(base_path)
    if not os.path.exists(detail_path):
        logger.info("%s: no detail scrape yet, skipping", os.path.basename(base_path))
        return None

    base = pd.read_csv(base_path)
    base["match_id"] = base["match_id"].astype(str)

    detail = pd.read_csv(detail_path, low_memory=False)
    detail["match_id"] = detail["match_id"].astype(str)
    # The detail scrape appends, so a re-scraped match appears twice; the later row wins.
    detail = detail.drop_duplicates("match_id", keep="last")

    merged = base.merge(detail, on="match_id", how="left", suffixes=("", "_detail"))

    # Naming the columns explicitly is load-bearing, not cosmetic: it drops the
    # `_detail`-suffixed duplicates the merge creates wherever the two files share a
    # column name, and pins the output order to base-then-detail.
    feature_cols = [c for c in DETAIL_ORDERED_COLUMNS if c != "match_id"]
    columns = list(base.columns) + feature_cols

    timing = _goal_timing_features(merged)
    if timing is not None:
        merged = pd.concat([merged, timing], axis=1)
        columns += list(timing.columns)

    enriched_path = paths.enriched_path(base_path)
    os.makedirs(paths.PROCESSED_DIR, exist_ok=True)
    merged[[c for c in columns if c in merged.columns]].to_csv(enriched_path, index=False)

    matched = merged["odds_bookmaker"].notna().sum() if "odds_bookmaker" in merged else 0
    logger.info("Saved %d rows (%d with detail) to %s", len(merged), matched, enriched_path)
    return enriched_path


def _goal_timing_features(merged: pd.DataFrame) -> pd.DataFrame | None:
    """Derived timing aggregates, or None when goal timings have not been scraped yet.

    An absent store is the normal state until `scrapers.goals` has run, so this returns
    None rather than a frame of NaNs — that keeps the enriched file's column set honest
    about what has actually been collected.
    """
    store_path = paths.goals_path()
    if not os.path.exists(store_path):
        return None
    store = goal_features.load_store(store_path)
    if not store:
        return None
    timing = goal_features.build(merged, store)
    covered = timing["home_goals_seen"].gt(0).mean()
    logger.info(
        "  goal timings: %d matches in the store, %.0f%% of rows have home history",
        len(store),
        covered * 100,
    )
    return timing


def build_all() -> None:
    """Rebuild every enriched file from the raw scrapes."""
    base_paths = paths.base_league_csvs()
    if not base_paths:
        raise FileNotFoundError(
            f"no league CSVs in {paths.RAW_DIR}/ — run `python -m scrapers.schedule` first"
        )
    for base_path in base_paths:
        build_enriched(base_path)


def main() -> None:
    build_all()


if __name__ == "__main__":
    main()
