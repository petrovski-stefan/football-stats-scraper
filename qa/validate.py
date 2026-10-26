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
    STAGE_TEXT_COLUMNS,
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
    """The table's match ids as stripped text; a missing id is left out."""

    return df["match_id"].dropna().astype(str).str.strip().tolist()


def read_staged(path: str, columns: list[str] | None = None) -> pd.DataFrame:
    """A staged file, all its columns or only `columns`, with its text columns kept as text:
    an empty stage stays ""."""

    head = pd.read_csv(path, nrows=0).columns
    text = [c for c in STAGE_TEXT_COLUMNS if c in head and (columns is None or c in columns)]
    staged_df = pd.read_csv(path, usecols=columns, dtype=dict.fromkeys(text, str))

    return staged_df.fillna(dict.fromkeys(text, ""))


def validate_league_season(base_path: str) -> bool:
    """Validate one league-season across its base, detail and enriched files."""

    league, season = paths.split_league_season(base_path)
    subject = f"{league} {season}"
    reports: list[Report] = []

    base_df = pd.read_csv(base_path)
    report = Report(f"{subject} - base")
    universal.check_not_empty(report, base_df)
    universal.check_required_columns(report, base_df, ORDERED_DF_COLUMNS)
    universal.check_primary_key(report, base_df)
    universal.check_no_dead_columns(report, base_df, optional=OPTIONAL_BASE_COLUMNS)
    league_checks.validate(report, base_df)
    reports.append(report)

    detail_path = paths.detail_path(base_path)
    enriched_path = paths.enriched_path(base_path)
    detail_df = pd.read_csv(detail_path, low_memory=False) if os.path.exists(detail_path) else None

    if detail_df is not None:
        report = Report(f"{subject} - detail")
        universal.check_not_empty(report, detail_df)
        universal.check_required_columns(report, detail_df, DETAIL_ORDERED_COLUMNS)
        universal.check_primary_key(report, detail_df)
        universal.check_no_dead_columns(report, detail_df)
        detail_checks.validate(report, detail_df)
        reports.append(report)

    if detail_df is not None or os.path.exists(enriched_path):
        report = Report(f"{subject} - joins")
        if detail_df is not None:
            universal.check_ids_covered(report, _ids(base_df), _ids(detail_df), "the detail file")

        if os.path.exists(enriched_path):
            enriched_df = pd.read_csv(enriched_path, low_memory=False)
            report.check(
                len(enriched_df) == len(base_df),
                f"enriched row count {len(enriched_df)} != base row count {len(base_df)}",
            )
            universal.check_primary_key(report, enriched_df)
            universal.check_ids_covered(
                report, _ids(base_df), _ids(enriched_df), "the enriched file"
            )

        reports.append(report)

    # Flush every report before deciding — `all()` over a generator would short-circuit
    # on the first failure and swallow the remaining subjects' output.
    verdicts = [report.flush() for report in reports]

    return all(verdicts)


def validate_goals() -> bool | None:
    """Validate the global goal store, once for all league-seasons, since history matches come
    from other competitions too. None when nothing is scraped yet: an absent store is skipped,
    not failed.
    """

    goals_path, done_path = paths.goals_path(), paths.goals_done_path()
    if not os.path.exists(done_path):
        return None

    goals_df = (
        pd.read_csv(goals_path)
        if os.path.exists(goals_path)
        else pd.DataFrame(columns=GOALS_ORDERED_COLUMNS)
    )
    attempt_log_df = pd.read_csv(done_path)

    report = Report("goal timings (global store)")
    goal_checks.validate(report, goals_df, attempt_log_df, _goal_truth())

    return report.flush()


def validate_events() -> bool | None:
    """Validate the global card/substitution store, once for all league-seasons; None when
    nothing is scraped yet. It has no free oracle like the goal store's scores, so
    `qa/events.py` checks structure and rate bands instead (`qa/CLAUDE.md` §4).
    """

    events_path, done_path = paths.events_path(), paths.events_done_path()
    if not os.path.exists(done_path):
        return None

    events_df = (
        pd.read_csv(events_path)
        if os.path.exists(events_path)
        else pd.DataFrame(columns=EVENTS_ORDERED_COLUMNS)
    )
    attempt_log_df = pd.read_csv(done_path)

    report = Report("cards and substitutions (global store)")
    event_checks.validate(report, events_df, attempt_log_df)

    return report.flush()


SCORE_COLUMNS = ["match_id", "ht_home_goals", "ht_away_goals", "ft_home_goals", "ft_away_goals"]


def _goal_truth() -> pd.DataFrame:
    """Every match whose half-time and full-time score we know independently: the corpus's
    own matches (the base league CSVs) and every match a fixture's history references (the
    detail files), without which only ~20% of the goal store could be checked.
    """

    frames = [pd.read_csv(path, usecols=SCORE_COLUMNS) for path in paths.base_league_csvs()]
    for base in paths.base_league_csvs():
        detail_path = paths.detail_path(base)
        if not os.path.exists(detail_path):
            continue

        detail_df = pd.read_csv(detail_path, low_memory=False)
        frames.extend(_history_scores(detail_df))

    if not frames:
        return pd.DataFrame(columns=SCORE_COLUMNS)

    truth_df = pd.concat(frames, ignore_index=True).dropna(subset=["match_id"])

    return truth_df.drop_duplicates("match_id", keep="first")


def _history_scores(detail_df: pd.DataFrame) -> list[pd.DataFrame]:
    """The per-match history blocks, reshaped into the same columns as a base CSV."""

    history_blocks: list[pd.DataFrame] = []
    for section in PER_MATCH_SECTIONS:
        for slot in range(1, MATCHES_PER_SECTION + 1):
            columns = {f"{section}_last{slot}_{field}": field for field in SCORE_COLUMNS}
            if not all(c in detail_df.columns for c in columns):
                continue

            history_block_df = detail_df[list(columns)].rename(columns=columns).dropna()
            if not history_block_df.empty:
                history_blocks.append(
                    history_block_df.astype(dict.fromkeys(SCORE_COLUMNS, "int64"))
                )

    return history_blocks


def validate_staged_schedule(schedule_path: str) -> bool:
    """One staged league-season: its stage-1 schedule, the page's final table against the
    table rebuilt from it, then its stage-2 and stage-3 files against the stages before."""

    league, season = paths.split_schedule_name(schedule_path)
    schedule_df = read_staged(schedule_path)

    schedule_report = Report(f"{league} {season} - schedule (stage 1)")
    universal.check_not_empty(schedule_report, schedule_df)
    universal.check_required_columns(schedule_report, schedule_df, SCHEDULE_RAW_COLUMNS)
    universal.check_primary_key(schedule_report, schedule_df)
    universal.check_no_dead_columns(
        schedule_report, schedule_df, optional=OPTIONAL_SCHEDULE_COLUMNS
    )
    if not schedule_df.empty:
        schedule_checks.validate(schedule_report, schedule_df)

    final_table_report = Report(f"{league} {season} - final table vs rebuilt standings")
    table_path = paths.final_table_path(league, season)
    exists = os.path.exists(table_path)
    final_table_df = read_staged(table_path) if exists else pd.DataFrame()
    final_table_checks.check(final_table_report, schedule_df, final_table_df)

    reports = [
        schedule_report,
        final_table_report,
        *_derived_reports(schedule_path, schedule_df, f"{league} {season}"),
    ]

    # A list, not a generator: `all()` would stop at the first failure and leave the
    # remaining reports unprinted.
    verdicts = [report.flush() for report in reports]

    return all(verdicts)


def _derived_reports(schedule_path: str, stage_1_df: pd.DataFrame, subject: str) -> list[Report]:
    """Stage 2 and stage 3 of one league-season, each against every stage before it."""

    earlier = {1: stage_1_df}
    reports: list[Report] = []
    for stage, builder in _BUILDERS.items():
        report = Report(f"{subject} - schedule (stage {stage})")
        path = paths.schedule_at_stage(schedule_path, stage)
        if os.path.exists(path):
            stage_file_df = read_staged(path)
            universal.check_required_columns(
                report, stage_file_df, stage_checks.declared_columns(stage)
            )
            universal.check_primary_key(report, stage_file_df)
            stage_checks.validate(report, stage_file_df, stage, earlier)
            earlier[stage] = stage_file_df
        else:
            report.fail(f"no stage-{stage} file: run `uv run python -m {builder}`")

        reports.append(report)

    return reports


def validate_corpus(schedule_paths: list[str]) -> bool:
    """The checks across files: no match in two league-seasons, every league-season's
    league in `config/leagues.json`, and no stage-2 or stage-3 file left without its
    stage-1 file."""

    report = Report(f"corpus - {len(schedule_paths)} staged league-seasons together")
    ids_by_file = {
        os.path.basename(path): read_staged(path, ["match_id", "s1_league_id"])
        for path in schedule_paths
    }

    universal.check_unique_across(
        report, {name: _ids(schedule_df) for name, schedule_df in ids_by_file.items()}
    )

    league_ids = _config_league_ids()
    report.check(league_ids is not None, f"no {paths.LEAGUES_FILE}: the leagues go unchecked")
    if league_ids is not None:
        found = {
            name: schedule_df["s1_league_id"].astype(str).tolist()
            for name, schedule_df in ids_by_file.items()
        }
        universal.check_declared(
            report, found, league_ids, f"league id not in {paths.LEAGUES_FILE}"
        )

    for stage in _BUILDERS:
        stage_checks.check_no_orphans(report, schedule_paths, paths.schedule_csvs(stage), stage)

    return report.flush()


def _config_league_ids() -> set[str] | None:
    """The league ids the config declares, as text; None when there is no config."""

    if not os.path.exists(paths.LEAGUES_FILE):
        return None

    with open(paths.LEAGUES_FILE, encoding="utf-8") as leagues_file:
        return {str(league["league_id"]) for league in json.load(leagues_file)}


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
    """Entry point: run the staged checks, or the archived ones, and exit 1 on any failure."""

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
