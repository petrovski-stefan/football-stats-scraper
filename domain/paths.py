"""Where the project's CSVs and its league config live, and how to get from a CSV to its siblings.

The physical counterpart to `domain/columns.py`: that module declares *which columns*
a file has, this one declares *which file, where*. Both are contracts shared between
the scrapers that write and the layers that read, which is why they sit in the base
package every layer may import.

The old pipeline's files sit in `data/archived/` (moved there from `data/raw/` and
`data/processed/` on 2026-10-10, the user's call), split by provenance as before:

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
    """`data/raw/epl_2025-2026.csv` -> `epl_2025-2026`."""

    return os.path.splitext(os.path.basename(base_path))[0]


def split_league_season(path: str) -> tuple[str, str]:
    """`data/raw/norway_eliteserien_2025.csv` -> `("norway_eliteserien", "2025")`.

    The inverse of the name `scrapers/csv_io.py:league_csv_path` builds. Never do this by
    fixed-width slicing: a season label is 9 characters for a cross-year league but 4 for
    a calendar-year one, so a hardcoded width eats into the league name instead —
    `norway_eliteserien_2025` sliced at 9 yields `("norway_elites", "rien_2025")`.

    Returns `(stem, "")` if the name carries no recognisable season, so a stray file
    labels itself oddly in a report rather than crashing the caller.
    """

    stem = _stem(path)
    match = _STEM_RE.match(stem)
    if match is None:
        return stem, ""
    return match.group("league"), match.group("season")


def base_league_csvs() -> list[str]:
    """Every base league CSV in `data/archived/raw/`, sorted.

    Two kinds of file share the directory without being league-seasons and must be
    excluded, or every consumer treats them as one: the per-league `_detail.csv` scrapes,
    and the **global** goal-timing store, which is keyed by match id rather than by
    league-season and so has no `<league>_<season>` stem to split.
    """

    return [
        path
        for path in sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
        if not path.endswith(DETAIL_SUFFIX) and os.path.basename(path) not in GLOBAL_FILES
    ]


def detail_path(base_path: str) -> str:
    """The detail scrape that accompanies a base league CSV — same directory."""

    return os.path.join(RAW_DIR, _stem(base_path) + DETAIL_SUFFIX)


def enriched_path(base_path: str) -> str:
    """The enriched join built from a base league CSV — a *different* directory.

    This is the function that knows raw and derived have been separated. Callers that
    used to reach a sibling with `base_path.replace(".csv", "_enriched.csv")` must go
    through here instead; that string surgery silently produced a `data/raw/` path.
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
    """The attempt log beside it.

    Separate from `goals_done_path()` on purpose: the two stores are filled by the same
    page render but were introduced at different times, so a match can be done for goals
    and pending for events. Keeping the logs apart is what lets the scraper fetch such a
    match once, write only the store that is missing, and never re-fetch it again.
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
    """`.../england_english_premier_league_2025-2026_schedule.csv` ->
    `("england_english_premier_league", "2025-2026")`. The staged files carry a kind suffix
    after the season, so the suffix goes first and `split_league_season` does the rest.
    `(stem, "")` when the name does not fit."""

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
