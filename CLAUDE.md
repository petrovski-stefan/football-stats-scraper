# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Each package has its own `CLAUDE.md` with the detail for work inside it: `scrapers/`, `features/`, `modelling/`, `qa/`, `domain/`.

## Overview

Selenium + BeautifulSoup scraper that collects finished football match data (teams, date, round, standings positions, HT/FT goals) from **nowgoal26.com** league pages, validates it with a Pydantic `Match` model (`domain/match.py`), and writes per-league CSVs to `data/raw/`. It serves analytics for two betting markets: **comebacks**, where the HT loser wins at FT (`is_comeback`, split into `is_comeback_home` / `is_comeback_away`), and **over 6.5 goals** (`is_seven_or_more_goals`). Package manager is **uv**; requires **Python 3.13** (pinned in `.python-version`).

Never call the site's data/API endpoints directly — always render pages in Selenium and parse the DOM.

## Commands

All commands run from the repo root — the `data/raw/`, `data/processed/`, `notes/` and `config/` paths are relative to the working directory, not to the module.

Pipeline, in order:

- Install deps: `uv sync`
- Run the league scraper: `uv run python -m scrapers.schedule` → `data/raw/`
- Run the detail enricher: `uv run python -m scrapers.detail [--limit N]` → `data/raw/` (resumable; `--limit` caps the batch)
- Scrape the live page: `uv run python -m scrapers.goals [--limit N] [--sections home,away,h2h] [--depth 6]` → `data/raw/goals.csv` **and** `data/raw/events.csv` (fourth stage; see `scrapers/CLAUDE.md`)
- Build the enriched join: `uv run python -m features.enrich` → `data/processed/` — the third pipeline step, required after either scrape before anything in `features/` or `modelling/` sees new data.

Validation, features, modelling:

- Validate the corpus: `uv run python -m qa.validate` — exits non-zero on any failure; read `qa/CLAUDE.md` before touching it.
- Build the feature matrix: `uv run python -m features.engine` (`--self-check` proves the as-of-round invariant)
- Validate the imported F11 completion curve: `uv run python -m features.chain --replicate-f11`
- Screen features: `uv run python -m modelling.experiment --dev` — **never run `--holdout`: it targets a spent season (see `modelling/CLAUDE.md` §2)**. A `PreToolUse` hook (`.claude/settings.json` → `.claude/hooks/block-holdout.sh`) blocks any Bash or PowerShell command containing the flag. The --holdout hook fails open if bash is unavailable; rerun its proof after any environment change.
- Validate the scoreline model: `uv run python -m modelling.scoreline --self-check --leak-check`
- Run the exclusion-filter study: `uv run python -m modelling.filter_study --curve` / `--bar`

## Quality gates

- Lint: `uv run ruff check` (autofix: `uv run ruff check --fix`)
- Format: `uv run ruff format` (check only: `uv run ruff format --check`)
- Type-check: `uv run mypy .`
- Cognitive complexity: `uvx complexipy@latest . --failed --suggest-refactors`
- Structural analysis: `uvx pyscn@latest analyze .` (clones, dead code, coupling, layer compliance)

**Run all five on every change, not just before committing, and do a caller sweep by hand when adding a function.** Ruff and mypy pass clean on unused functions, unreferenced constants and private names called across modules, and pyscn's dead-code detector does not catch unreferenced definitions either (history in `notes/MIGRATIONS.md`).

No test framework or CI is set up. The only correctness guards are the hand-run `--self-check` / `--leak-check` / `--replicate-f11` flags. That matters because this project's real failure mode is statistical leakage, and leaky code is lint-clean by construction.

Tool config: Ruff and mypy are configured in `pyproject.toml`.
- Ruff lint uses a pragmatic bug-focused set (`E/W/F/I/B/C4/SIM/UP` plus `RUF/PIE/LOG/G/PGH/TID`, line-length 100). `TID` is what enforces the no-relative-imports rule.
- mypy runs `strict = true` with only `prop-decorator` disabled, for the pydantic `@computed_field` idiom.
- complexipy and pyscn run via `uvx`, so they are not project dependencies.
- pyscn reads `.pyscn.toml`, which disables type-4 clone detection and encodes the layer table below as machine-checked architecture rules.

## Required runtime setup

- `config/LEAGUES.txt` — one nowgoal26 league URL per line, format `/league/<season>/<id>`. **`<season>` takes two forms**, both accepted: `2025-2026` for a cross-year European league (`.../league/2025-2026/36`) and `2025` for a calendar-year one — Scandinavia, Brazil, Japan, MLS, and others that play inside a single year (`.../league/2025/71`). See "Season labels" in `domain/CLAUDE.md`.
- `data/` — one gitignored tree, split by provenance: **`data/raw/`** is scraper output only (`<league>_<season>.csv` and `_detail.csv`), **`data/processed/`** is derived (`_enriched.csv`, written by `features/enrich.py`). Both auto-create on write. Both are declared in **`domain/paths.py`**, the only place a data directory or a sibling-file path is constructed — never rebuild one by hand from a filename.
- A locally installed **Chrome** — Selenium 4 auto-manages the driver and runs headless.

## Architecture

Four layers, imported **absolutely** and strictly one-directional — `domain` → `scrapers` → `features` → `modelling`, with `qa` off to the side. Nothing lower may import something higher; that rule is the whole point of the split, so keep it.

| package | holds | may import |
|---|---|---|
| `domain/` | `match.py`, `match_detail.py`, `goal.py`, `event.py` (Pydantic contracts; `match.py` also holds the date and **season-label** parsers), `columns.py` (CSV column order), `paths.py` (where files live, and filename↔league/season), `stats.py` (pure derived-stat kernel), `scope.py` (which historical matches are usable) | nothing internal |
| `scrapers/` | `driver`, `links`, `parsers`, `schedule`, `detail`, `detail_parsers`, `goals`, `live_rows` (the shared live-page row reader), `goal_parsers`, `event_parsers`, `browser_pool`, `csv_io`, `constants` (DOM selectors) | `domain` |
| `features/` | `enrich.py` (the base+detail join), `engine.py` (the as-of-round feature matrix), `chain.py`, `history.py` (which history matches count, the shared build shape, and the score reconciliation both builders need), `goals.py` (goal-timing aggregates), `events.py` (card/substitution aggregates, state-conditioned against the goal store), `ratepair.py` (the shared home/away Poisson pair) | `domain` |
| `modelling/` | `scoreline`, `experiment`, `filter_study` | everything below |
| `qa/` | `report.py`, `universal.py` (dataset-agnostic checks), `league.py`, `detail.py`, `goals.py`, `events.py`, `validate.py` (orchestrator) | `domain` |

Every entry point is a module inside its package, run as `python -m <package>.<module>` from the repo root — there are no top-level scripts. Do **not** use relative (`from .x import`) imports anywhere — Ruff's `TID` rule bans them. Import as `from scrapers.parsers import ...`, `from domain import stats`, `from features import engine`.

Modules and directories have been renamed several times. If code or a note cites a path that doesn't exist, check **`notes/MIGRATIONS.md`**.

## Conventions

- Work directly on `main`; there is no `dev` or feature-branch flow. Since nothing isolates a bad commit from the default branch, run `uv run ruff check && uv run ruff format --check && uv run mypy .` before committing.
- Pin dependency versions exactly in `pyproject.toml` (matches existing style); update `uv.lock` via `uv`.
- Absolute package imports only (`from domain import stats`), never relative — enforced by Ruff `TID`. Respect the layer direction in the table above.
- Never hardcode a data directory or build a CSV's sibling by string surgery (`base_path.replace(".csv", "_enriched.csv")` was the old idiom and silently resolves to the wrong directory now). Go through `domain/paths.py`.
- Open research decisions go to `notes/DECISIONS.md` instead of blocking the current task. Only stop and ask when the task genuinely can't continue without the answer.
- Only `scrapers/` may write to `data/raw/`. Everything else derives into `data/processed/` and must be reproducible from the raw files — that is what makes the raw corpus safe to treat as ground truth and a derived file safe to delete.

## Where to read

Start with **`notes/STATE.md`**, the current state of the research. Before proposing anything in prediction, features or analysis, also read `modelling/CLAUDE.md`.

- `notes/MIGRATIONS.md` — when code or a note cites a module, path or column that doesn't exist.
- `notes/HANDOFF.md` — before any prediction, feature or analysis work: strategy guide, base rates, pipeline-specific leakage traps, methodology rules, roadmap.
- `notes/STATS_PRIMER.md` — when a roadmap step uses Empirical Bayes shrinkage, Brier scores, calibration curves or Dixon–Coles and you need the formulas.
- `notes/ESOTERIC_MODELS.md` — when a modelling step matches one of its seven tools' tagged "reach for it when" moments.
- `notes/LEAGUE_STUDY.md` — before designing any comeback feature, and before admitting a new country as a comeback-candidate league (defines the bar).
- `notes/PREREGISTRATION.md` — before testing any claim; it is the template (closed family list, Holm correction, one holdout opening, dated amendments).
- `notes/RESULTS.md` — before proposing any new pre-match comeback feature (the F12 re-test with nowgoal-exclusive features).
- `notes/PREREGISTRATION_FILTER.md` — when reading or re-running the exclusion-filter study; the closed preregistration it was held to (its verdict is in `FILTER_RESULTS.md`).
- `notes/FILTER_RESULTS.md` — before proposing any filter that excludes "comeback-impossible" matches.
- `notes/FILTER_STUDY_RAW.md` — only when auditing the filter study's numbers; raw transcript of `filter_study --bar`, overwritten on every run.
- `notes/MARKET_LINE_FINDINGS.md` — before quoting the market-line result or planning the corpus scrape (its §4 caveats and §7 purpose change are required reading).
- `notes/BEHAVIOURAL_RESULTS.md` — before proposing any hand-weighted candidate rule; it introduced the candidate protocol.
- `notes/RETRY_CANDIDATES_2026-09-23.md` — before retrying anything that already failed, and before the multi-country scrape's analysis.
- `notes/RELIABILITY_SCREEN_2026-09-23.md` — before building any history-block feature, especially one on cards or substitutions.
- `notes/PLAN_2026-07-25_environment_filter.md` — when picking up the multi-country corpus scrape; the open phases of the comeback-environment plan (§1's ceiling figures are still current; its purpose was revised by `MARKET_LINE_FINDINGS.md` §7).
- `notes/PLAN_2026-09-20_next_direction.md` — when deciding what to do next. Its §1 out-of-round claim is refuted; §2 (the prospective gut log) is still open.
- `notes/ALGOBETTING.md` — background only: a conversation summary on market structure, CLV, the modelling lineage and Asian handicaps. It predates every measured result here, so none of its claims are tested.
