# Leagues Teams Summarizer

A web scraper that collects football match data across multiple leagues — including match results, odds, team positions, and half-time scores — and exports everything to structured CSV files for analysis.

## What it does

1. Reads the enabled league seasons from `config/leagues.json`
2. Navigates each league page using a headless Chrome browser
3. Clicks the stages the config keeps (regular season, groups, Apertura/Clausura, etc.) and walks each stage's rounds
4. Scrapes every match in every round, collecting:
   - Team names and their current league positions
   - Full-time and half-time goals
   - Betting odds in three flavours — 1X2, Asian Handicap, and Over/Under
   - Stage, round, date, and match position in the round
5. Validates data with Pydantic and saves per-league CSV files to `data/archived/raw/`
6. Enriches each match from its detail page (recent form, H2H, odds movement) into `data/archived/raw/`
7. Scrapes each match's live page into two global stores — `data/archived/raw/goals.csv` (goal timings) and `data/archived/raw/events.csv` (yellow cards, red cards, substitutions)
8. Joins them into `data/archived/processed/` for the feature layer

## Tech stack

| Tool               | Purpose                                                |
| ------------------ | ------------------------------------------------------ |
| Selenium           | Headless Chrome browser automation                     |
| BeautifulSoup4     | HTML parsing                                           |
| Pandas             | CSV output                                             |
| Pydantic           | Match data validation                                  |
| ThreadPoolExecutor | Concurrent page scraping (3 workers, one browser each) |
| `uv`               | Dependency management                                  |

## Project structure

Six packages, imported absolutely and strictly one-directional:
`domain` → `scrapers` → `features` → `analysis` → `ml`, with `qa` off to the side.

```
.
├── config/
│   ├── leagues.example.json  # Committed template: one fake league
│   └── leagues.json          # Your real config (gitignored): leagues, stages to keep, seasons
├── data/
│   ├── raw/              # Scraper output only — nothing else writes here
│   └── processed/        # Derived files, all reproducible from data/archived/raw/
├── domain/               # Pydantic contracts, column order, paths, pure stat kernel
├── scrapers/             # Selenium driver, DOM parsers, schedule/detail/live-page scrapes
├── features/             # The joins, goal/event aggregates, as-of-round feature matrix
├── analysis/             # Runners that only print, one per doc in notes/ANALYSIS/
├── ml/                   # ML runners that only print, one per doc in notes/ML/
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

Copy `config/leagues.example.json` to `config/leagues.json` and fill it with real leagues.
Set `"enabled": true` on the seasons to scrape in `config/leagues.json` (each league lists
its stage tabs in `stages` and the ones to scrape in `keep`), then run all four stages with one
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
uv run python -m scrapers.schedule   # -> data/archived/raw/<league>_<season>.csv
uv run python -m scrapers.detail     # -> data/archived/raw/<league>_<season>_detail.csv
uv run python -m scrapers.goals      # -> data/archived/raw/goals.csv + events.csv (global, not per league)
uv run python -m features.enrich     # -> data/archived/processed/<league>_<season>_enriched.csv
```

Both scrapes are resumable — they skip ids already done, so interrupt them freely. Detail
is ~1 page render per match (~380 a season). The live-page scrape is heavier: its work list
is the corpus _plus_ every match referenced by a detail row's history blocks, deduplicated
by match id before anything is fetched, which is why its stores are global rather than per
league-season. One render fills both stores.

`features.enrich` needs no browser and can be re-run at any time.

Then check the result:

```bash
uv run python -m qa.validate
```

## Output columns

The schedule is stored in three stages under `data/finished/`: the values read from the page
(stage 1), fields computed from one row (stage 2), and fields that need other rows, such as
the standings table at each kickoff (stage 3). The detail CSV (537 columns) still uses the old
layout in `data/archived/raw/` until the staged pipeline reaches it.

**`domain/columns.py` is the authoritative list of column orders**, and **`notes/FIELDS/`
defines every column once**: its place on the page, meaning, example, timing and role. Neither
is duplicated here, because a hand-copied schema table goes stale silently and this one did.

## Notes

- User agents are rotated randomly per request to reduce bot detection.
- Portuguese special characters in team/league names are transliterated to ASCII before being used as file names.
- If a league CSV already exists, it is overwritten only when the new scrape has at least
  as many rows, so an interrupted run cannot clobber a good file.
- `data/` is gitignored; the corpus is not committed.
