"""Post-scrape data validator.

By default it checks the staged pipeline only (`data/finished/`): every stage-1 schedule,
the page's final table against the table rebuilt from its results (`qa/final_table.py`),
and the schedule's stage-2 and stage-3 files against the stages before them
(`qa/stages.py`); then, across all files, that no match id is in two league-seasons, every
league-season's league is in `config/leagues.json`, and no derived file has lost its
stage-1 file. The old pipeline's files, archived in
`data/archived/` on 2026-10-10 (the user's call), are checked only on request: per
league-season the base league CSV, its detail CSV and their join with the enriched file,
then the global goal and event stores. Dataset-agnostic rules come from
`qa/universal.py`; rules that need to know what a column means come from
`qa/schedule.py`, `qa/league.py` and `qa/detail.py`.

There are no exemptions. A column that is empty because a parser broke fails, whether
or not the breakage is already known — the only declared allowances are
`domain.columns.OPTIONAL_SCHEDULE_COLUMNS` and, in the archive, `OPTIONAL_BASE_COLUMNS`,
which name columns that are empty in a *correct* scrape. Exits non-zero if any subject
fails.

Run: `uv run python -m qa.validate` (the staged files)
     `uv run python -m qa.validate --archived` (the old pipeline's files)
"""

import argparse
import json
import os

import pandas as pd

from domain import paths
from domain.columns import (
    DETAIL_ORDERED_COLUMNS,
    EVENTS_ORDERED_COLUMNS,
    GOALS_ORDERED_COLUMNS,
    MATCHES_PER_SECTION,
    OPTIONAL_BASE_COLUMNS,
    OPTIONAL_SCHEDULE_COLUMNS,
    ORDERED_DF_COLUMNS,
    PER_MATCH_SECTIONS,
    SCHEDULE_RAW_COLUMNS,
)
from qa import detail as detail_checks
from qa import events as event_checks
from qa import final_table as final_table_checks
from qa import goals as goal_checks
from qa import league as league_checks
from qa import schedule as schedule_checks
from qa import stages as stage_checks
from qa import universal
from qa.report import Report

# The module that rebuilds each derived stage of the schedule from the stage before it.
_BUILDERS = {2: "features.schedule_row", 3: "features.schedule_multi"}


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


def validate_events() -> bool | None:
    """Validate the global card/substitution store — once, across every league-season.

    Returns None when nothing has been scraped yet. Unlike the goal store this one has no
    independent score to reconcile against, so `qa/events.py` checks structure and rate
    bands instead; that asymmetry is stated there rather than hidden.
    """
    events_path, done_path = paths.events_path(), paths.events_done_path()
    if not os.path.exists(done_path):
        return None

    events = (
        pd.read_csv(events_path)
        if os.path.exists(events_path)
        else pd.DataFrame(columns=EVENTS_ORDERED_COLUMNS)
    )
    done = pd.read_csv(done_path)

    r = Report("cards and substitutions (global store)")
    event_checks.validate(r, events, done)
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


def validate_staged_schedule(schedule_path: str) -> bool:
    """One staged league-season: its stage-1 schedule, the page's final table against the
    table rebuilt from it, then its stage-2 and stage-3 files against the stages before."""
    league, season = paths.split_schedule_name(schedule_path)
    schedule = schedule_checks.read_staged(schedule_path)

    r = Report(f"{league} {season} - schedule (stage 1)")
    universal.check_not_empty(r, schedule)
    universal.check_required_columns(r, schedule, SCHEDULE_RAW_COLUMNS)
    universal.check_primary_key(r, schedule)
    universal.check_no_dead_columns(r, schedule, optional=OPTIONAL_SCHEDULE_COLUMNS)
    if not schedule.empty:
        schedule_checks.validate(r, schedule)

    t = Report(f"{league} {season} - final table vs rebuilt standings")
    table_path = paths.final_table_path(league, season)
    exists = os.path.exists(table_path)
    table = schedule_checks.read_staged(table_path) if exists else pd.DataFrame()
    final_table_checks.check(t, schedule, table)

    reports = [r, t, *_derived_reports(schedule_path, schedule, f"{league} {season}")]
    # A list, not a generator: `all()` would stop at the first failure and leave the
    # remaining reports unprinted.
    verdicts = [report.flush() for report in reports]
    return all(verdicts)


def _derived_reports(schedule_path: str, raw: pd.DataFrame, subject: str) -> list[Report]:
    """Stage 2 and stage 3 of one league-season, each against every stage before it."""
    earlier = {1: raw}
    reports: list[Report] = []
    for stage, builder in _BUILDERS.items():
        r = Report(f"{subject} - schedule (stage {stage})")
        path = paths.schedule_at_stage(schedule_path, stage)
        if os.path.exists(path):
            frame = schedule_checks.read_staged(path)
            universal.check_required_columns(r, frame, stage_checks.declared_columns(stage))
            universal.check_primary_key(r, frame)
            stage_checks.validate(r, frame, stage, earlier)
            earlier[stage] = frame
        else:
            r.check(False, f"no stage-{stage} file: run `uv run python -m {builder}`")
        reports.append(r)
    return reports


def validate_corpus(schedule_paths: list[str]) -> bool:
    """The checks across files: no match in two league-seasons, every league-season's
    league in `config/leagues.json`, and no stage-2 or stage-3 file left without its
    stage-1 file."""
    r = Report(f"corpus - {len(schedule_paths)} staged league-seasons together")
    keys = {
        os.path.basename(path): schedule_checks.read_staged(path, ["match_id", "s1_league_id"])
        for path in schedule_paths
    }
    universal.check_unique_across(r, {name: _ids(frame) for name, frame in keys.items()})
    league_ids = _config_league_ids()
    r.check(league_ids is not None, f"no {paths.LEAGUES_FILE}: the leagues go unchecked")
    if league_ids is not None:
        found = {name: frame["s1_league_id"].astype(str).tolist() for name, frame in keys.items()}
        universal.check_declared(r, found, league_ids, f"league id not in {paths.LEAGUES_FILE}")
    for stage in _BUILDERS:
        stage_checks.check_no_orphans(r, schedule_paths, paths.schedule_csvs(stage), stage)
    return r.flush()


def _config_league_ids() -> set[str] | None:
    """The league ids the config declares, as text; None when there is no config."""
    if not os.path.exists(paths.LEAGUES_FILE):
        return None
    with open(paths.LEAGUES_FILE, encoding="utf-8") as f:
        return {str(league["league_id"]) for league in json.load(f)}


def validate_staged() -> bool:
    """Every stage-1 schedule in `data/finished/1_raw/` with its final table and its later
    stages, then the checks across files."""
    schedule_paths = paths.schedule_csvs(1)
    if not schedule_paths:
        print(f"no staged schedules found in {paths.stage_dir(1)}/")
        return False
    staged = [validate_staged_schedule(path) for path in schedule_paths]
    corpus = validate_corpus(schedule_paths)
    print(f"{staged.count(True)}/{len(staged)} staged league-seasons passed")
    return all(staged) and corpus


def validate_archived() -> bool:
    """The old pipeline's league-seasons and global stores in `data/archived/`."""
    base_paths = paths.base_league_csvs()
    if not base_paths:
        print(f"no league CSVs found in {paths.RAW_DIR}/")
        return False

    results = [validate_league_season(path) for path in base_paths]
    failed = results.count(False)
    print(f"\n{len(results) - failed}/{len(results)} league-seasons passed")

    goals_ok = validate_goals()
    if goals_ok is None:
        print("goal timings: not scraped yet (skipped)")

    events_ok = validate_events()
    if events_ok is None:
        print("cards and substitutions: not scraped yet (skipped)")

    return not failed and goals_ok is not False and events_ok is not False


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Validate the scraped data.")
    parser.add_argument(
        "--archived",
        action="store_true",
        help="check the old pipeline's files in data/archived/ instead of data/finished/",
    )
    args = parser.parse_args(argv)
    if not (validate_archived() if args.archived else validate_staged()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
