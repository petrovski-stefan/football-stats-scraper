"""Post-scrape data validator.

Discovers every scraped league-season in `data/raw/` and validates three subjects per
league-season: the base league CSV, its detail CSV, and the relationship between them
and the enriched join in `data/processed/`. Dataset-agnostic rules come from
`qa/universal.py`; rules that need to know what a column means come from `qa/league.py`
and `qa/detail.py`.

There are no exemptions. A column that is empty because a parser broke fails, whether
or not the breakage is already known — the only declared allowance is
`domain.columns.OPTIONAL_BASE_COLUMNS`, which names columns that are empty in a
*correct* scrape. Exits non-zero if any subject fails.

Run: `uv run python -m qa.validate`
"""

import os

import pandas as pd

from domain import paths
from domain.columns import (
    DETAIL_ORDERED_COLUMNS,
    GOALS_ORDERED_COLUMNS,
    MATCHES_PER_SECTION,
    OPTIONAL_BASE_COLUMNS,
    ORDERED_DF_COLUMNS,
    PER_MATCH_SECTIONS,
)
from qa import detail as detail_checks
from qa import goals as goal_checks
from qa import league as league_checks
from qa import universal
from qa.report import Report


def _ids(df: pd.DataFrame) -> list[str]:
    return df["match_id"].dropna().astype(str).str.strip().tolist()


def validate_league_season(base_path: str) -> bool:
    """Validate one league-season across its base, detail and enriched files."""
    league, season = paths.split_league_season(base_path)
    subject = f"{league} {season}"
    reports: list[Report] = []

    base = pd.read_csv(base_path)
    r = Report(f"{subject} - base")
    universal.check_not_empty(r, base)
    universal.check_required_columns(r, base, ORDERED_DF_COLUMNS)
    universal.check_primary_key(r, base)
    universal.check_no_dead_columns(r, base, optional=OPTIONAL_BASE_COLUMNS)
    league_checks.validate(r, base)
    reports.append(r)

    detail_path = paths.detail_path(base_path)
    enriched_path = paths.enriched_path(base_path)
    detail = pd.read_csv(detail_path, low_memory=False) if os.path.exists(detail_path) else None

    if detail is not None:
        r = Report(f"{subject} - detail")
        universal.check_not_empty(r, detail)
        universal.check_required_columns(r, detail, DETAIL_ORDERED_COLUMNS)
        universal.check_primary_key(r, detail)
        universal.check_no_dead_columns(r, detail)
        detail_checks.validate(r, detail)
        reports.append(r)

    if detail is not None or os.path.exists(enriched_path):
        r = Report(f"{subject} - joins")
        if detail is not None:
            universal.check_ids_covered(r, _ids(base), _ids(detail), "the detail file")
        if os.path.exists(enriched_path):
            enriched = pd.read_csv(enriched_path, low_memory=False)
            r.check(
                len(enriched) == len(base),
                f"enriched row count {len(enriched)} != base row count {len(base)}",
            )
            universal.check_primary_key(r, enriched)
            universal.check_ids_covered(r, _ids(base), _ids(enriched), "the enriched file")
        reports.append(r)

    # Flush every report before deciding — `all()` over a generator would short-circuit
    # on the first failure and swallow the remaining subjects' output.
    verdicts = [report.flush() for report in reports]
    return all(verdicts)


def validate_goals() -> bool | None:
    """Validate the global goal store — once, across every league-season.

    Returns None when nothing has been scraped yet, so an absent store is skipped rather
    than counted as a failure. The store is global rather than per league-season because
    the matches a fixture's history references come from other competitions entirely.
    """
    goals_path, done_path = paths.goals_path(), paths.goals_done_path()
    if not os.path.exists(done_path):
        return None

    goals = (
        pd.read_csv(goals_path)
        if os.path.exists(goals_path)
        else pd.DataFrame(columns=GOALS_ORDERED_COLUMNS)
    )
    done = pd.read_csv(done_path)

    r = Report("goal timings (global store)")
    goal_checks.validate(r, goals, done, _goal_truth())
    return r.flush()


SCORE_COLUMNS = ["match_id", "ht_home_goals", "ht_away_goals", "ft_home_goals", "ft_away_goals"]


def _goal_truth() -> pd.DataFrame:
    """Every match whose half-time and full-time score we know independently.

    Two sources, and the second is what makes the goal store fully checkable:

      - the base league CSVs, which cover the corpus itself;
      - the detail files' history blocks, which record the score of **every match a
        fixture's history references** — cup ties, European games, other leagues.

    Without the second source only ~20% of the goal store could be reconciled, and an
    error in a history match would be invisible. With it, every scraped match has an
    oracle: a parser bug that truncated 19 matches on 2026-09-22 was caught this way.
    """
    frames = [pd.read_csv(path, usecols=SCORE_COLUMNS) for path in paths.base_league_csvs()]
    for base in paths.base_league_csvs():
        detail_path = paths.detail_path(base)
        if not os.path.exists(detail_path):
            continue
        detail = pd.read_csv(detail_path, low_memory=False)
        frames.extend(_history_scores(detail))
    if not frames:
        return pd.DataFrame(columns=SCORE_COLUMNS)
    truth = pd.concat(frames, ignore_index=True).dropna(subset=["match_id"])
    return truth.drop_duplicates("match_id", keep="first")


def _history_scores(detail: pd.DataFrame) -> list[pd.DataFrame]:
    """The per-match history blocks, reshaped into the same columns as a base CSV."""
    out: list[pd.DataFrame] = []
    for section in PER_MATCH_SECTIONS:
        for n in range(1, MATCHES_PER_SECTION + 1):
            columns = {f"{section}_last{n}_{field}": field for field in SCORE_COLUMNS}
            if not all(c in detail.columns for c in columns):
                continue
            block = detail[list(columns)].rename(columns=columns).dropna()
            if not block.empty:
                out.append(block.astype(dict.fromkeys(SCORE_COLUMNS, "int64")))
    return out


def main() -> None:
    base_paths = paths.base_league_csvs()
    if not base_paths:
        print(f"no league CSVs found in {paths.RAW_DIR}/")
        raise SystemExit(1)

    results = [validate_league_season(path) for path in base_paths]
    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} league-seasons passed")

    goals_ok = validate_goals()
    if goals_ok is None:
        print("goal timings: not scraped yet (skipped)")

    if failed or goals_ok is False:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
