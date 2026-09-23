"""Where the project's CSVs live, and how to get from one to its siblings.

The physical counterpart to `domain/columns.py`: that module declares *which columns*
a file has, this one declares *which file, where*. Both are contracts shared between
the scrapers that write and the layers that read, which is why they sit in the base
package every layer may import.

One `data/` tree, split by provenance — a file's directory states what produced it:

    data/raw/        <league>_<season>.csv           scrapers.schedule
                     <league>_<season>_detail.csv    scrapers.detail
    data/processed/  <league>_<season>_enriched.csv  features.enrich

Nothing but a scraper writes into `data/raw/`. Everything derived — today just the
base+detail join — goes to `data/processed/` and is reproducible from the raw files,
so the whole directory is safe to delete and rebuild.

Stdlib only, deliberately: `domain` depends on nothing internal and (apart from the
pydantic models) nothing heavy, so a path lookup never drags pandas into a caller.
Paths are relative to the working directory, so every entry point runs from the repo
root — see CLAUDE.md.
"""

import glob
import os
import re

DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")

DETAIL_SUFFIX = "_detail.csv"
ENRICHED_SUFFIX = "_enriched.csv"

# Goal timings are stored GLOBALLY rather than per league-season, the one exception to the
# naming scheme above. A fixture's history references matches from cups, European
# competition and other leagues, so a referenced match belongs to no single league-season
# file -- and the dedupe that makes the scrape affordable only works if it spans all of
# them. The key is the nowgoal match id, which is globally unique.
GOALS_FILE = "goals.csv"
GOALS_DONE_FILE = "goals_done.csv"
# Files in data/raw/ that are NOT a league-season. `base_league_csvs()` must skip these,
# or everything that iterates league-seasons — the validator, the enricher, the goals
# work list — picks them up and tries to treat a global store as a league.
GLOBAL_FILES = frozenset({GOALS_FILE, GOALS_DONE_FILE})


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
    """Every base league CSV in `data/raw/`, sorted.

    Two kinds of file share the directory without being league-seasons and must be
    excluded, or every consumer treats them as one: the per-league `_detail.csv` scrapes,
    and the **global** goal-timing store, which is keyed by match id rather than by
    league-season and so has no `<league>_<season>` stem to split.
    """
    return [
        p
        for p in sorted(glob.glob(os.path.join(RAW_DIR, "*.csv")))
        if not p.endswith(DETAIL_SUFFIX) and os.path.basename(p) not in GLOBAL_FILES
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


def enriched_csvs() -> list[str]:
    """Every enriched league-season in `data/processed/`, sorted."""
    return sorted(glob.glob(os.path.join(PROCESSED_DIR, "*" + ENRICHED_SUFFIX)))
