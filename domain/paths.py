"""Where the project's CSVs and its league config live, and how to get from a CSV to its siblings.

The physical counterpart to `domain/columns.py`: that module declares *which columns*
a file has, this one declares *which file, where*. Both are contracts shared between
the scrapers that write and the layers that read, which is why they sit in the base
package every layer may import.

The old pipeline's files sit in `data/archived/`, split by provenance:

    data/archived/raw/        <league>_<season>.csv           scrapers.schedule (old format)
                              <league>_<season>_detail.csv    scrapers.detail
                              goals.csv, events.csv (+ _done) scrapers.goals
    data/archived/processed/  <league>_<season>_enriched.csv  features.enrich

They are reference data for refactoring the detail, goal and event sources (plan steps
P4-P5); `qa.validate --archived` still checks them. The old tools still read and write
there through `RAW_DIR` and `PROCESSED_DIR` until those steps move them, so don't run them
on the archive.

The staged pipeline (`notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md`) replaces that tree,
one source at a time. Its files sit under `data/finished/`, one directory per stage:

    data/finished/1_raw/    <league>_<season>_schedule.csv     scrapers.schedule
                            <league>_<season>_final_table.csv  scrapers.schedule
                  2_row/    <league>_<season>_schedule.csv     features.schedule_row
                  3_multi/  <league>_<season>_schedule.csv     features.schedule_multi

Only `1_raw/` is scraper output; `2_row/` and `3_multi/` are rebuilt from it at any time.
Here `<league>` is the config's country and then the league's name in the page's title
(`japan_j2_league`), joined by `scrapers/csv_io.py:league_slug`; a name that already
starts with the exact country keeps it once (`brazil_serie_a`).

Stdlib only, deliberately: `domain` depends on nothing internal and (apart from the
pydantic models) nothing heavy, so a path lookup never drags pandas into a caller.
Paths are relative to the working directory, so every entry point runs from the repo
root — see CLAUDE.md.
"""

import glob
import os
import re

# The league catalogue: `scrapers/links.py` reads the jobs from it, and `qa.validate` holds
# the stored files against it. Written as it appears in messages.
LEAGUES_FILE = "config/leagues.json"

DATA_DIR = "data"
ARCHIVED_DIR = os.path.join(DATA_DIR, "archived")
RAW_DIR = os.path.join(ARCHIVED_DIR, "raw")
PROCESSED_DIR = os.path.join(ARCHIVED_DIR, "processed")

DETAIL_SUFFIX = "_detail.csv"
ENRICHED_SUFFIX = "_enriched.csv"

FINISHED_DIR = os.path.join(DATA_DIR, "finished")
# One directory per stage: 1 = read from the page, 2 = derived inside one row, 3 = needs
# other rows. The names sort in pipeline order.
STAGE_DIRS = {1: "1_raw", 2: "2_row", 3: "3_multi"}
SCHEDULE_SUFFIX = "_schedule.csv"
FINAL_TABLE_SUFFIX = "_final_table.csv"

# Goal timings are stored GLOBALLY rather than per league-season, the one exception to the
# naming scheme above. A fixture's history references matches from cups, European
# competition and other leagues, so a referenced match belongs to no single league-season
# file -- and the dedupe that makes the scrape affordable only works if it spans all of
# them. The key is the nowgoal match id, which is globally unique.
GOALS_FILE = "goals.csv"
GOALS_DONE_FILE = "goals_done.csv"
# Cards and substitutions, from the same live page and global for the same reason.
EVENTS_FILE = "events.csv"
EVENTS_DONE_FILE = "events_done.csv"
# Files in data/archived/raw/ that are NOT a league-season. `base_league_csvs()` must skip these,
# or everything that iterates league-seasons — the validator, the enricher, the goals
# work list — picks them up and tries to treat a global store as a league.
GLOBAL_FILES = frozenset({GOALS_FILE, GOALS_DONE_FILE, EVENTS_FILE, EVENTS_DONE_FILE})


# `<league>_<season>`, where season is "2025-2026" or "2025". Greedy `.+` so the split
# falls at the *last* underscore that leaves a valid season behind.
_STEM_RE = re.compile(r"^(?P<league>.+)_(?P<season>\d{4}(?:-\d{4})?)$")


def _stem(base_path: str) -> str:
    """`data/archived/raw/epl_2025-2026.csv` -> `epl_2025-2026`."""

    return os.path.splitext(os.path.basename(base_path))[0]


def split_league_season(path: str) -> tuple[str, str]:
    """The league and season of a `<league>_<season>` file name; the inverse of `schedule_path`.

    Never slice a fixed width instead: a season label has 9 characters or 4. `(stem, "")` when
    the name carries no season, so a stray file shows oddly in a report and crashes nothing.
    """

    stem = _stem(path)
    found = _STEM_RE.match(stem)
    if found is None:
        return stem, ""

    return found.group("league"), found.group("season")


def base_league_csvs() -> list[str]:
    """Every base league CSV in `data/archived/raw/`, sorted.

    Leaves out the two kinds of file that share the directory but are no league-season: the
    `_detail.csv` scrapes and the global goal and event stores (`GLOBAL_FILES`).
    """

    league_csvs: list[str] = []
    for path in sorted(glob.glob(os.path.join(RAW_DIR, "*.csv"))):
        is_detail = path.endswith(DETAIL_SUFFIX)
        is_global_store = os.path.basename(path) in GLOBAL_FILES
        if not is_detail and not is_global_store:
            league_csvs.append(path)

    return league_csvs


def detail_path(base_path: str) -> str:
    """The detail scrape that accompanies a base league CSV — same directory."""

    return os.path.join(RAW_DIR, _stem(base_path) + DETAIL_SUFFIX)


def enriched_path(base_path: str) -> str:
    """The enriched join built from a base league CSV, in a *different* directory.

    Never build it from `base_path` by string surgery: the result would land in `RAW_DIR`.
    """

    return os.path.join(PROCESSED_DIR, _stem(base_path) + ENRICHED_SUFFIX)


def goals_path() -> str:
    """The global goal-timing store. One row per goal, keyed by match id."""

    return os.path.join(RAW_DIR, GOALS_FILE)


def goals_done_path() -> str:
    """The attempt log beside it: every match id fetched, whether or not it had goals.

    Separate from `goals_path()` because a 0-0 produces no goal rows, so the store alone
    cannot say whether a match has been scraped.
    """

    return os.path.join(RAW_DIR, GOALS_DONE_FILE)


def events_path() -> str:
    """The global card/substitution store. One row per event, keyed by match id."""

    return os.path.join(RAW_DIR, EVENTS_FILE)


def events_done_path() -> str:
    """The attempt log beside the event store.

    Kept apart from `goals_done_path()`: a match can be done for one store and pending for the
    other, and the scraper then fetches it once and writes only the store that is missing.
    """

    return os.path.join(RAW_DIR, EVENTS_DONE_FILE)


def enriched_csvs() -> list[str]:
    """Every enriched league-season in `data/archived/processed/`, sorted."""

    return sorted(glob.glob(os.path.join(PROCESSED_DIR, "*" + ENRICHED_SUFFIX)))


# --- The staged pipeline: data/finished/ ---------------------------------------------


def stage_dir(stage: int) -> str:
    """`data/finished/<n>_<name>/` for stage 1, 2 or 3. Any other stage is a KeyError."""

    return os.path.join(FINISHED_DIR, STAGE_DIRS[stage])


def schedule_path(stage: int, league: str, season: str) -> str:
    """A league-season's schedule file at one stage. `league` is the file-name slug."""

    return os.path.join(stage_dir(stage), f"{league}_{season}{SCHEDULE_SUFFIX}")


def final_table_path(league: str, season: str) -> str:
    """The page's final table for a league-season: stage 1 only, read as a check."""

    return os.path.join(stage_dir(1), f"{league}_{season}{FINAL_TABLE_SUFFIX}")


def schedule_csvs(stage: int) -> list[str]:
    """Every schedule file at one stage, sorted."""

    return sorted(glob.glob(os.path.join(stage_dir(stage), "*" + SCHEDULE_SUFFIX)))


def split_schedule_name(path: str) -> tuple[str, str]:
    """The league and season of a staged schedule file name; `(stem, "")` when it does not fit.

    The `_schedule.csv` suffix comes off first, then `split_league_season` does the rest.
    """

    name = os.path.basename(path)
    if not name.endswith(SCHEDULE_SUFFIX):
        return _stem(path), ""

    return split_league_season(name.removesuffix(SCHEDULE_SUFFIX) + ".csv")


def schedule_at_stage(path: str, stage: int) -> str:
    """The same league-season's schedule file at another stage."""

    league, season = split_schedule_name(path)
    if not season:
        raise ValueError(f"not a staged schedule file: {path}")

    return schedule_path(stage, league, season)
