# Leagues Teams Summarizer

A web scraper that collects football match data across multiple leagues — including match results, odds, team positions, and half-time scores — and exports everything to structured CSV files for analysis.

## What it does

1. Reads a list of league URLs from `config/LEAGUES.txt`
2. Navigates each league page using a headless Chrome browser
3. Discovers all stages (regular season, groups, etc.) and rounds within each league
4. Scrapes every match in every round, collecting:
   - Team names and their current league positions
   - Full-time and half-time goals
   - Betting odds in three flavours — 1X2, Asian Handicap, and Over/Under
   - Stage, round, date, and match position in the round
5. Validates data with Pydantic and saves per-league CSV files to `data/raw/`
6. Enriches each match from its detail page (recent form, H2H, odds movement) into `data/raw/`
7. Scrapes each match's live page into two global stores — `data/raw/goals.csv` (goal timings) and `data/raw/events.csv` (yellow cards, red cards, substitutions)
8. Joins them into `data/processed/` for the feature and modelling layers

## Tech stack

| Tool | Purpose |
|---|---|
| Selenium | Headless Chrome browser automation |
| BeautifulSoup4 | HTML parsing |
| Pandas | CSV output |
| Pydantic | Match data validation |
| ThreadPoolExecutor | Concurrent page scraping (3 workers, one browser each) |
| `uv` | Dependency management |

## Project structure

Five packages, imported absolutely and strictly one-directional:
`domain` → `scrapers` → `features` → `modelling`, with `qa` off to the side.

```
.
├── config/
│   └── LEAGUES.txt       # One league URL per line
├── data/
│   ├── raw/              # Scraper output only — nothing else writes here
│   └── processed/        # Derived files, all reproducible from data/raw/
├── domain/               # Pydantic contracts, column order, paths, pure stat kernel
├── scrapers/             # Selenium driver, DOM parsers, schedule/detail/live-page scrapes
├── features/             # The joins, goal/event aggregates, as-of-round feature matrix
├── modelling/            # Experiments: scoreline model, feature screens, filter study
├── qa/                   # Corpus validator
└── notes/                # Study records, preregistrations, findings
```

There are no top-level Python scripts; every entry point is `python -m <package>.<module>`,
run from the repo root. `scripts/pipeline.sh` wraps the four pipeline stages (see Usage).
See `CLAUDE.md` for the layer rules and the full architecture.

## Setup

Requires Python 3.13+ and [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

Chrome must be installed — the scraper runs it in headless mode.

## Usage

Add league URLs (one per line) to `config/LEAGUES.txt`, then run all four stages with one
command (from any directory; on Windows, use Git Bash):

```bash
bash scripts/pipeline.sh                # schedule -> detail -> goals -> enrich
bash scripts/pipeline.sh --limit 50     # cap detail and goals at 50 matches each
bash scripts/pipeline.sh --skip-schedule --skip-detail --skip-goals   # enrich only
bash scripts/pipeline.sh --help         # all options
```

It stops at the first failing stage and says which one. Rerun the same command to resume.

Or run the four stages by hand, in order:

```bash
uv run python -m scrapers.schedule   # -> data/raw/<league>_<season>.csv
uv run python -m scrapers.detail     # -> data/raw/<league>_<season>_detail.csv
uv run python -m scrapers.goals      # -> data/raw/goals.csv + events.csv (global, not per league)
uv run python -m features.enrich     # -> data/processed/<league>_<season>_enriched.csv
```

Both scrapes are resumable — they skip ids already done, so interrupt them freely. Detail
is ~1 page render per match (~380 a season). The live-page scrape is heavier: its work list
is the corpus *plus* every match referenced by a detail row's history blocks, deduplicated
by match id before anything is fetched, which is why its stores are global rather than per
league-season. One render fills both stores.

`features.enrich` needs no browser and can be re-run at any time.

Then check the result:

```bash
uv run python -m qa.validate
```

## Output columns

The league CSV carries 58 columns, of which 30 are stored directly and the other 28 are
`@computed_field` properties derived from them. The detail CSV adds 537.

**`domain/columns.py` is the authoritative list** (`ORDERED_DF_COLUMNS`,
`DETAIL_ORDERED_COLUMNS`), with per-column meaning documented on the Pydantic models in
`domain/match.py` and `domain/match_detail.py`. It is not duplicated here, because a
hand-copied schema table goes stale silently and this one did.

## Notes

- User agents are rotated randomly per request to reduce bot detection.
- Portuguese special characters in team/league names are transliterated to ASCII before being used as file names.
- If a league CSV already exists, it is overwritten only when the new scrape has at least
  as many rows, so an interrupted run cannot clobber a good file.
- `data/` is gitignored; the corpus is not committed.
