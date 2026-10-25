"""Join each raw league scrape to its raw detail scrape, one enriched file per season.

The first derived artefact in the pipeline, and the reason it is here rather than in
`scrapers/`: a left join adds no scraped information, so it is not a scrape. Splitting
it out also means a stale or deleted `_enriched.csv` can be rebuilt from the raw files
in seconds — previously the only way to regenerate one was to invoke the detail
scraper, which starts Selenium even when there is nothing left to fetch.

Reads `data/archived/raw/`, writes `data/archived/processed/`. The enriched file is the base
columns, then the detail feature columns, then — when the goal-timing store exists — the derived
timing aggregates from `features/goals.py`. Those are the one set of columns this module does not
merely copy across, and they are appended last so the base-then-detail order is unchanged.

Run: `uv run python -m features.enrich`
"""

import logging
import os

import pandas as pd

from domain import paths
from domain.columns import DETAIL_ORDERED_COLUMNS
from features import events as event_features
from features import goals as goal_features

logger = logging.getLogger(__name__)


def build_enriched(base_path: str) -> str | None:
    """Join one league-season and write it. Returns the path, or None if not yet scraped."""

    detail_path = paths.detail_path(base_path)
    if not os.path.exists(detail_path):
        logger.info("%s: no detail scrape yet, skipping", os.path.basename(base_path))
        return None

    base_df = pd.read_csv(base_path)
    base_df["match_id"] = base_df["match_id"].astype(str)

    detail_df = pd.read_csv(detail_path, low_memory=False)
    detail_df["match_id"] = detail_df["match_id"].astype(str)

    # The detail scrape appends, so a re-scraped match appears twice; the later row wins.
    detail_df = detail_df.drop_duplicates("match_id", keep="last")

    enriched_df = base_df.merge(detail_df, on="match_id", how="left", suffixes=("", "_detail"))

    # Naming the columns explicitly is load-bearing, not cosmetic: it drops the
    # `_detail`-suffixed duplicates the merge creates wherever the two files share a
    # column name, and pins the output order to base-then-detail.
    feature_cols = [c for c in DETAIL_ORDERED_COLUMNS if c != "match_id"]
    columns = list(base_df.columns) + feature_cols

    # The declared names rather than the built frame's own, for the same reason the detail
    # columns are named explicitly above: the output order is pinned by `features/*.py`
    # rather than by dict-insertion order. A disagreement means a column was renamed in one
    # place only, so it raises here instead of vanishing from the join unnoticed.
    for extra_df, declared in (
        (
            _goal_timing_features(enriched_df),
            goal_features.feature_names() + goal_features.timeline_names(),
        ),
        (
            _event_features(enriched_df),
            event_features.feature_names() + event_features.timeline_names(),
        ),
    ):
        if extra_df is None:
            continue

        missing = [c for c in declared if c not in extra_df.columns]
        if missing:
            raise RuntimeError(f"declared columns missing from the built block: {missing[:5]}")

        enriched_df = pd.concat([enriched_df, extra_df], axis=1)
        columns += declared

    enriched_path = paths.enriched_path(base_path)
    os.makedirs(paths.PROCESSED_DIR, exist_ok=True)
    enriched_df[[c for c in columns if c in enriched_df.columns]].to_csv(enriched_path, index=False)

    matched = enriched_df["odds_bookmaker"].notna().sum() if "odds_bookmaker" in enriched_df else 0
    logger.info("Saved %d rows (%d with detail) to %s", len(enriched_df), matched, enriched_path)

    return enriched_path


def _goal_timing_features(enriched_df: pd.DataFrame) -> pd.DataFrame | None:
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

    timing_df = goal_features.build(enriched_df, store)
    covered = timing_df["home_goals_seen"].gt(0).mean()
    logger.info(
        "  goal timings: %d matches in the store, %.0f%% of rows have home history",
        len(store),
        covered * 100,
    )

    return timing_df


def _event_features(enriched_df: pd.DataFrame) -> pd.DataFrame | None:
    """Card and substitution aggregates, or None when events have not been scraped yet.

    Same contract as `_goal_timing_features`: an absent store yields no columns rather
    than a block of NaNs, so the enriched file's column set stays honest about what has
    actually been collected.
    """

    store_path = paths.events_path()
    if not os.path.exists(store_path):
        return None

    store = event_features.load_store(store_path)
    if not store:
        return None

    # The goal store is what tells a card collected while protecting a lead from one
    # collected while chasing. Absent, the state-conditioned columns come back NaN and
    # every other event column is unaffected — so an events-only corpus still builds.
    goals_path = paths.goals_path()
    goal_store = goal_features.load_store(goals_path) if os.path.exists(goals_path) else {}

    event_features_df = event_features.build(enriched_df, store, goal_store)
    covered = event_features_df["home_events_seen"].gt(0).mean()
    logger.info(
        "  events: %d matches in the store, %.0f%% of rows have home history",
        len(store),
        covered * 100,
    )

    return event_features_df


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
    """Entry point: rebuild every enriched join."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    build_all()


if __name__ == "__main__":
    main()
