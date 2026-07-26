"""Post-scrape data validator.

Discovers every scraped league-season in `data/` and validates three subjects per
league-season: the base league CSV, its detail CSV, and the relationship between them
and the enriched join. Dataset-agnostic rules come from `qa/universal.py`; rules that
need to know what a column means come from `qa/league.py` and `qa/detail.py`.

There are no exemptions. A column that is empty because a parser broke fails, whether
or not the breakage is already known — the only declared allowance is
`domain.columns.OPTIONAL_BASE_COLUMNS`, which names columns that are empty in a
*correct* scrape. Exits non-zero if any subject fails.

Run: `uv run python -m qa.validate`
"""

import glob
import os

import pandas as pd

from domain.columns import (
    DETAIL_ORDERED_COLUMNS,
    OPTIONAL_BASE_COLUMNS,
    ORDERED_DF_COLUMNS,
)
from qa import detail as detail_checks
from qa import league as league_checks
from qa import universal
from qa.report import Report

DATA_DIR = "data"


def _base_league_csvs() -> list[str]:
    return [
        p
        for p in sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
        if not p.endswith("_detail.csv") and not p.endswith("_enriched.csv")
    ]


def _league_season(path: str) -> tuple[str, str]:
    name = os.path.splitext(os.path.basename(path))[0]
    season = name[-9:]  # "YYYY-YYYY"
    league = name[:-10]
    return league, season


def _ids(df: pd.DataFrame) -> list[str]:
    return df["match_id"].dropna().astype(str).str.strip().tolist()


def validate_league_season(base_path: str) -> bool:
    """Validate one league-season across its base, detail and enriched files."""
    league, season = _league_season(base_path)
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

    detail_path = base_path.replace(".csv", "_detail.csv")
    enriched_path = base_path.replace(".csv", "_enriched.csv")
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


def main() -> None:
    paths = _base_league_csvs()
    if not paths:
        print(f"no league CSVs found in {DATA_DIR}/")
        raise SystemExit(1)

    results = [validate_league_season(path) for path in paths]
    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} league-seasons passed")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
