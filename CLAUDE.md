# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Each package has its own `CLAUDE.md` with the detail for work inside it: `scrapers/`, `features/`, `analysis/`, `ml/`, `qa/`, `domain/`.

## Overview

Selenium + BeautifulSoup scraper that collects finished football match data (teams, kickoff, round, HT/FT goals, opening odds) from **nowgoal** league pages (the site often moves to a new domain, with the same paths and page structure, `scrapers/CLAUDE.md`). **The data is moving to a staged pipeline** (`notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md`): each source is stored as read from the page (stage 1), then enriched with fields from one row (stage 2), then with fields that need other rows (stage 3), under `data/finished/`; every field is defined once in `notes/FIELDS/`. The schedule, `analysis/` and `ml/` are on the new pipeline; the detail page, the live page and the old feature matrix (`features.engine`) still use the old per-league CSVs in `data/archived/` until the plan's steps P4–P5. It serves analytics for two betting markets: **comebacks**, where the HT loser wins at FT (`is_comeback`, split into `is_comeback_home` / `is_comeback_away`), and **7+** (7 or more goals, `is_seven_or_more_goals`). Package manager is **uv**; requires **Python 3.13** (pinned in `.python-version`).

Never call the site's data/API endpoints directly — always render pages in Selenium and parse the DOM.

## Commands

All commands run from the repo root — the `data/`, `notes/` and `config/` paths are relative to the working directory, not to the module.

Pipeline, in order:

- Install deps: `uv sync`
- Run the league scraper: `uv run python -m scrapers.schedule` → `data/finished/1_raw/` (the schedule and the page's final table, `notes/FIELDS/SCHEDULE_1_RAW.md`). With no option it takes the `enabled` seasons; `--leagues "SCO PR,SCO CH"` / `--all`, `--before-year 2026`, `--list` (no page opens) and `--force` choose others (`scrapers/CLAUDE.md` §1). It resumes: a league-season already on disk is skipped.
- Build schedule stage 2: `uv run python -m features.schedule_row` → `data/finished/2_row/` (`notes/FIELDS/SCHEDULE_2_ROW.md`)
- Build schedule stage 3: `uv run python -m features.schedule_multi` → `data/finished/3_multi/` (`notes/FIELDS/SCHEDULE_3_MULTI.md`; the standings rebuilt at each kickoff)
- Run the detail enricher: `uv run python -m scrapers.detail [--limit N]` → `data/archived/raw/` (resumable; `--limit` caps the batch)
- Scrape the live page: `uv run python -m scrapers.goals [--limit N] [--sections home,away,h2h] [--depth 6]` → `data/archived/raw/goals.csv` **and** `data/archived/raw/events.csv` (fourth stage; see `scrapers/CLAUDE.md`)
- Build the enriched join: `uv run python -m features.enrich` → `data/archived/processed/` — the third pipeline step, required after either scrape before anything in `features/` sees new data.

Validation, features, analysis:

- Validate the corpus: `uv run python -m qa.validate` — the staged files in `data/finished/` only (`--archived` checks the old pipeline's files instead); exits non-zero on any failure; read `qa/CLAUDE.md` before touching it.
- Build the feature matrix: `uv run python -m features.engine` (`--self-check` proves the as-of-round invariant)
- Validate the imported F11 completion curve: `uv run python -m features.chain --replicate-f11`
- Run an analysis: `uv run python -m analysis.schedule.whole_corpus.all.shin`, `uv run python -m analysis.schedule.whole_corpus.per_league.shin`. A runner only prints; Claude writes its doc in `notes/ANALYSIS/` (`analysis/CLAUDE.md`).
- Run the ML test: `uv run python -m ml.schedule.whole_corpus.all.beyond_odds`. A runner only prints; Claude writes its doc in `notes/ML/` (`ml/CLAUDE.md`).

## Quality gates

- Lint: `uv run ruff check` (autofix: `uv run ruff check --fix`)
- Format: `uv run ruff format` (check only: `uv run ruff format --check`)
- Type-check: `uv run mypy .`
- Cognitive complexity: `uv run complexipy . --failed --suggest-refactors`
- Structural analysis: `uv run pyscn analyze .` (clones, dead code, coupling, layer compliance)
- Dependencies: `uv run deptry .` (imports vs declared dependencies: missing, unused, transitive, dev-only)
- Security lint: `uv run bandit -r domain scrapers features analysis ml qa` (the six packages; `tests/` stays out, because pytest's `assert` is bandit's finding B101)
- Tests: `uv run coverage run -m pytest` (`tests/`). `uv run coverage report` then lists the lines no test runs, and `/check` reads those of the diff. No % threshold: the browser code and the old pipeline are untested on purpose.

**Run all eight on every change, not just before committing, and do a caller sweep by hand when adding a function.** Ruff and mypy pass clean on unused functions, unreferenced constants and private names called across modules, and pyscn's dead-code detector does not catch unreferenced definitions either (history in `notes/LOG/MIGRATIONS.md`).

Tests:

- **Tests check mechanics only:** pure functions in all six packages, some as Hypothesis property tests (one rule tried on many generated cases; the profile in `tests/conftest.py` fixes the cases with `derandomize`). Never a research finding or anything about the project's outcomes, and a project-chosen constant (a year cutoff, a threshold) is read from the code, not restated.
- **`tests/` mirrors the packages, one test module per source module:** the tests for `domain/paths.py` live in `tests/domain/test_paths.py`.
- **Tests never contain the real site's domains;** a URL in a test uses the reserved `example.com`. **Tests never make a network request or start a browser,** not even to `example.com` (the user, 2026-10-13): a scraper test gets a fake driver (`tests/scrapers/test_driver.py`) or a stubbed job (`tests/scrapers/test_schedule.py`).
- **New code ships with its tests in the same change** (the user, 2026-10-13); there is no separate test backlog and no CI.
- **This project's real failure mode is statistical leakage, and leaky code is lint-clean by construction.** Stage 3 of the schedule has a leak test and a Hypothesis leak property in `tests/features/test_schedule_multi.py` (`features/CLAUDE.md` §0; the property takes about 55 s, most of the suite's time). The old pipeline's leakage is guarded only by the hand-run `features.engine --self-check` and `features.chain --replicate-f11`.

Tool config: Ruff, mypy, pytest and Coverage.py in `pyproject.toml` (Ruff's `TID` rule enforces the no-relative-imports rule; mypy runs `strict`); the Hypothesis profile in `tests/conftest.py`; pyscn in `.pyscn.toml`, which encodes the layer table below as machine-checked architecture rules. **Every Python tool is a pinned dev dependency run through `uv run`. Never `uvx`.** A new release then cannot change a gate result without a code change, and deptry in particular needs the venv: under `uvx` it cannot see the installed packages and reports false issues. Upgrading a tool is a deliberate version bump.

## Formatting

The user's VS Code formats on save (Ruff for `.py`, pointed at the project's ruff by `.vscode/settings.json`; Prettier with `.prettierrc` for `.md`). A `PostToolUse` hook (`.claude/hooks/format-on-write.sh`) runs the same formatters on every file Claude writes, using the Prettier copy inside the VS Code extension, so a Ctrl+S afterwards changes nothing. **`notes/` is not formatted** (`.prettierignore`): padded tables cost about 2.4× the context on every read.

### Readability

`CODING_STYLE.md` holds the readability rules (the user, 2026-10-22): names, function shape, blank lines, comments, errors and tests. **Read it before you write or change Python code**, `tests/` included.

## Required runtime setup

- `config/leagues.json` (gitignored; start from the committed template `config/leagues.example.json`, one fake league) — a list of leagues: `name`, `code`, `continent`, `country`, `league_id`, `stages` (every stage tab the league page shows, `[]` for none), `keep` (the stages to scrape) and `seasons` (`season`, `url`, `enabled`). `scrapers.schedule` scrapes only the seasons with `"enabled": true`. `scrapers/links.py` validates the whole file when it loads, and fails on any bad entry. Season URLs have the format `/league/<season>/<id>`, where **`<season>` takes two forms**, both accepted: `2025-2026` for a cross-year league and `2025` for a calendar-year one (see "Season labels" in `domain/CLAUDE.md`).
- `data/` — one gitignored tree. **`data/finished/`** is the staged pipeline: `1_raw/` is scraper output only, `2_row/` and `3_multi/` are rebuilt from it; `data/scheduled/` and `data/predictions/` come later. **`data/archived/`** holds the old pipeline's files, moved there on 2026-10-10 (the user's call) and kept for refactoring the detail, goal and event sources: `raw/` (`<league>_<season>.csv`, `_detail.csv`, the goal and event stores) and `processed/` (`_enriched.csv`). The old tools still read and write there until steps P4–P5 move them, so don't run them on the archive. All auto-create on write. All are declared in **`domain/paths.py`**, the only place a data directory or a sibling-file path is constructed — never rebuild one by hand from a filename.
- A locally installed **Chrome** — Selenium 4 auto-manages the driver and runs headless.

## Architecture

Five layers, imported **absolutely** and strictly one-directional — `domain` → `scrapers` → `features` → `analysis` → `ml` (`analysis` imports only `domain` and `features`; `ml` imports those and `analysis`), with `qa` off to the side. Nothing lower may import something higher; that rule is the whole point of the split, so keep it.

The layer table, one package per line (what it may import, then what it holds):

- **`domain/`** (imports nothing internal): `schedule.py`, `match_detail.py`, `goal.py`, `event.py` (Pydantic contracts; `schedule.py` also holds the **season-label** parser), `clock.py` (Berlin time with its offset, the project's one clock), `columns.py` (CSV column order), `paths.py` (where files live, and filename↔league/season), `stats.py` (pure derived-stat kernel), `standings.py` (the standings table rebuilt from results), `scope.py` (which history matches are in scope: not friendlies, not pre-2023 pages), `deductions.py` (points deductions declared for the final-table check)
- **`scrapers/`** (imports `domain`): `driver`, `links`, `parsers`, `schedule`, `detail`, `detail_parsers`, `goals`, `live_rows` (the shared live-page row reader), `goal_parsers`, `event_parsers`, `browser_pool`, `csv_io`, `constants` (DOM selectors)
- **`features/`** (imports `domain`): `schedule_row.py` and `schedule_multi.py` (the schedule's stages 2 and 3), `stage_io.py` (reading and writing the stage files), `enrich.py` (the base+detail join), `engine.py` (the as-of-round feature matrix), `chain.py`, `history.py` (which history matches count, the shared build shape, and the score reconciliation both builders need), `goals.py` (goal-timing aggregates), `events.py` (card/substitution aggregates, state-conditioned against the goal store)
- **`analysis/`** (imports `domain`, `features`): one runner per doc of `notes/ANALYSIS/`, in the same tree in lowercase (`schedule/whole_corpus/all/shin.py` → `SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`); shared `corpus.py`, `stats.py`, `methods/`. Prints only, never writes a file; analysis only, no ML (`analysis/CLAUDE.md`)
- **`ml/`** (imports `domain`, `features`, `analysis`): the ML runners (models with settings tuned on the data), one per doc of `notes/ML/`, in the same tree in lowercase; shared `rows.py`, `boosting.py` (LightGBM), `score.py`. Prints only, never writes a file (`ml/CLAUDE.md`)
- **`qa/`** (imports `domain`): `report.py`, `universal.py` (dataset-agnostic checks), `league.py`, `detail.py`, `goals.py`, `events.py`, `schedule.py` (the staged schedule file), `stages.py` (its stage-2 and stage-3 files against the stages before them), `odds.py` (odds checks for any table, given its columns), `final_table.py` (the page's final table against our rebuilt standings), `validate.py` (orchestrator)

Every entry point is a module inside its package, run as `python -m <package>.<module>` from the repo root — there are no top-level scripts. Do **not** use relative (`from .x import`) imports anywhere — Ruff's `TID` rule bans them. Import as `from scrapers.parsers import ...`, `from domain import stats`, `from features import engine`.

Modules and directories have been renamed several times. If code or a note cites a path that doesn't exist, check **`notes/LOG/MIGRATIONS.md`**.

## Conventions

- Work directly on `main`; there is no `dev` or feature-branch flow. Since nothing isolates a bad commit from the default branch, run `uv run ruff check && uv run ruff format --check && uv run mypy . && uv run bandit -q -r domain scrapers features analysis ml qa && uv run pytest` before committing. When the change touches `features/`, `analysis/`, `ml/`, `notes/` (not `notes/LOG/`, a change record only) or the leak tests (`tests/features`, `tests/analysis`, `tests/ml`), also run `/stats-review` once it is finished (`/check` says `stats review DUE`), and do not commit while the review is due or says BLOCK.
- Change dependencies only with uv commands, never by editing `pyproject.toml` by hand, and pin exactly: `uv add "pkg==1.2.3"` (runtime), `uv add --dev "pkg==1.2.3"` (tools), `uv remove pkg`. A bare `uv add pkg` writes a `>=` bound, so always give the `==` version. uv updates `uv.lock` and the venv in the same step.
- Absolute package imports only (`from domain import stats`), never relative — enforced by Ruff `TID`. Respect the layer direction in the layer table above.
- Never hardcode a data directory or build a CSV's sibling by string surgery (`base_path.replace(".csv", "_enriched.csv")` was the old idiom and silently resolves to the wrong directory now). Go through `domain/paths.py`.
- Open research decisions go to `notes/WORKING/DECISIONS.md` instead of blocking the current task. Only stop and ask when the task genuinely can't continue without the answer.
- When an item from a `notes/WORKING/IDEAS_*.md` or `notes/WORKING/PLAN_*.md` file is implemented, record it in `notes/LOG/MIGRATIONS.md` under the date it was done and delete it from the file that first mentioned it; a partly done item keeps only its open part there (the user, 2026-10-10). The IDEAS and PLAN files then hold only open work.
- Only `scrapers/` may write to `data/finished/1_raw/`. Everything else derives into the later stage directories and must be reproducible from the raw files — that is what makes the raw corpus safe to treat as ground truth and a derived file safe to delete.
- Line endings: CRLF on disk for every text file, LF inside git (`.gitattributes`). `*.sh` stays LF, because bash fails on `\r`. The formatting hook converts each file Claude writes, since Write creates LF files. It does not see `pyproject.toml` and `uv.lock` when uv rewrites them: uv writes LF, so after `uv add` or `uv lock` check `git ls-files --eol pyproject.toml uv.lock` and convert any `w/lf` back.

## Where to read

Start with **`notes/WORKING/STATE.md`**, the current state of the research. Before proposing anything in prediction, features or analysis, also read `notes/ANALYSIS/CLAUDE.md` §6. Each notes group's `CLAUDE.md` describes all of its notes; this list gives when to open one.

- `notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md` — before any data-format, data-path or refactor work.
- `notes/FIELDS/README.md` — before touching, adding or reading any column of a staged file.
- `notes/REFERENCE/GLOSSARY.md` — when a term in a note or CLAUDE.md is unclear.
- `notes/REFERENCE/MARKET_COMEBACKS.md` — before measuring or reporting any comeback fact: a definitional fact is never measured, a structural one is derived there once, only an empirical one is measured.
- `notes/LOG/MIGRATIONS.md` — when code or a note cites a module, path or column that doesn't exist, and to see what has been implemented from the IDEAS and PLAN notes.
- `notes/HISTORY/HANDOFF.md` — before any prediction, feature or analysis work: strategy guide, base rates, pipeline-specific leakage traps.
- `notes/REFERENCE/STATS_PRIMER.md` — when a step uses Empirical Bayes shrinkage, Brier scores, calibration curves or Dixon–Coles and you need the formulas.
- `notes/REFERENCE/ESOTERIC_MODELS.md` — when a modelling step matches one of its "reach for it when" lines.
- `notes/REFERENCE/POINTS_DEDUCTIONS.md` — before touching standings points or rank, or when the final-table check fails on points.
- `notes/RECORD/LEAGUES_INCIDENTS.md` — before analysing, keeping or dropping any scraped league; such decisions use outcome-blind data-quality checks only.
- `notes/RECORD/PREREGISTRATION.md` — before testing any claim.
- `notes/RECORD/RESULTS.md` — before proposing any new pre-match comeback feature (six nowgoal-exclusive feature families, all dead).
- `notes/RECORD/FILTER_RESULTS.md` — before proposing any filter that excludes "comeback-impossible" matches.
- `notes/RECORD/BEHAVIOURAL_RESULTS.md` — before proposing any hand-weighted candidate rule.
- `notes/RECORD/RETRY_CANDIDATES_2026-09-23.md` — before retrying anything that already failed, and before the multi-country scrape's analysis.
- `notes/RECORD/RELIABILITY_SCREEN_2026-09-23.md` — before building any history-block feature, especially one on cards or substitutions.
- `notes/HISTORY/PLAN_2026-09-20_NEXT_DIRECTION.md` — when deciding what to do next; read its errata first.
- The other notes of `notes/RECORD/` (the filter study's preregistration and raw run) and `notes/HISTORY/` (the environment-filter plan, `ALGOBETTING.md`): see the `CLAUDE.md` of their group.
