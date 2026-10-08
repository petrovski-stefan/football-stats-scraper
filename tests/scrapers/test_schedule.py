"""`scrapers/schedule.py`: planning a run (resume) and its summary. No browser opens here."""

import threading
import time
from pathlib import Path

import pandas as pd
import pytest

from domain import paths
from scrapers import schedule
from scrapers.links import LeagueSeason
from scrapers.schedule import Outcome, plan_jobs, scraped_league_seasons, summarise


def _job(league_id: int, season: str, code: str = "TST") -> LeagueSeason:
    url = f"https://example.com/league/{season}/{league_id}"
    return LeagueSeason(url, season, league_id, (), code, "Test League")


_JOBS = [_job(36, "2024-2025"), _job(36, "2025-2026"), _job(71, "2025", "OTH")]


def test_a_league_season_on_disk_is_skipped() -> None:
    to_scrape, on_disk = plan_jobs(_JOBS, {(36, "2025-2026")}, force=False)
    assert to_scrape == [_JOBS[0], _JOBS[2]]
    assert on_disk == [_JOBS[1]]


def test_force_scrapes_everything_again() -> None:
    to_scrape, on_disk = plan_jobs(_JOBS, {(36, "2025-2026")}, force=True)
    assert to_scrape == _JOBS
    assert on_disk == []


def test_what_is_on_disk_is_read_from_inside_the_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # The file name does not tell: the league id and season inside it do.
    path = tmp_path / "any_name_2025_schedule.csv"
    pd.DataFrame({"s1_league_id": [71], "s1_season": ["2025"]}).to_csv(path, index=False)
    monkeypatch.setattr(paths, "schedule_csvs", lambda stage: [str(path)])
    assert scraped_league_seasons() == {(71, "2025")}


def test_the_summary_counts_failures(capsys: pytest.CaptureFixture[str]) -> None:
    outcomes = [
        Outcome(_JOBS[0], matches=380, dropped=1),
        Outcome(_JOBS[2], error="TimeoutException: Message:"),
    ]
    assert summarise(outcomes, on_disk=[_JOBS[1]]) == 1
    printed = capsys.readouterr().out
    assert "1 scraped, 1 already on disk, 1 failed, 1 rows dropped" in printed
    assert "FAILED OTH 2025" in printed


def test_a_clean_run_reports_no_failures() -> None:
    assert summarise([Outcome(_JOBS[0], matches=10)], on_disk=[]) == 0


def _fake_run(
    monkeypatch: pytest.MonkeyPatch, jobs: list[LeagueSeason]
) -> tuple[list[str], list[float]]:
    """Run `scrape_all` over `jobs` with no browser: record each job's thread name and pauses."""
    names: list[str] = []
    pauses: list[float] = []
    lock = threading.Lock()

    def run_job(job: LeagueSeason) -> Outcome:
        with lock:
            names.append(threading.current_thread().name)
        return Outcome(job, error="boom") if job.code == "BAD" else Outcome(job, matches=1)

    monkeypatch.setattr(schedule, "get_league_seasons", lambda selection: jobs)
    monkeypatch.setattr(schedule, "scraped_league_seasons", set)
    monkeypatch.setattr(schedule, "_run_job", run_job)
    monkeypatch.setattr(time, "sleep", pauses.append)
    return names, pauses


def test_every_job_runs_once_on_a_thread_named_after_it(monkeypatch: pytest.MonkeyPatch) -> None:
    jobs = [_job(n, "2025", f"L{n}") for n in range(1, 8)]
    names, _ = _fake_run(monkeypatch, jobs)
    assert schedule.scrape_all() == 0
    assert sorted(names) == sorted(f"L{n} 2025" for n in range(1, 8))


def test_only_jobs_after_the_first_round_of_workers_pause(monkeypatch: pytest.MonkeyPatch) -> None:
    jobs = [_job(n, "2025", f"L{n}") for n in range(1, 8)]
    _, pauses = _fake_run(monkeypatch, jobs)
    schedule.scrape_all()
    assert pauses == [schedule.PAUSE_BETWEEN_JOBS] * (len(jobs) - schedule.WORKERS)


def test_a_failed_job_is_counted_and_the_others_still_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = [_job(1, "2025", "OK1"), _job(2, "2025", "BAD"), _job(3, "2025", "OK2")]
    names, _ = _fake_run(monkeypatch, jobs)
    assert schedule.scrape_all() == 1
    assert len(names) == len(jobs)
