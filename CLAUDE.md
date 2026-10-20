# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository. Each package has its own `CLAUDE.md` with the detail for work inside it: `scrapers/`, `features/`, `analysis/`, `ml/`, `qa/`, `domain/`.

## Overview

Selenium + BeautifulSoup scraper that collects finished football match data (teams, kickoff, round, HT/FT goals, opening odds) from **nowgoal26.com** league pages. **The data is moving to a staged pipeline** (`notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md`): each source is stored as read from the page (stage 1), then enriched with fields from one row (stage 2), then with fields that need other rows (stage 3), under `data/finished/`; every field is defined once in `notes/FIELDS/`. The schedule is on the new pipeline (2026-10-06); the detail page, the live page and the analysis still use the old per-league CSVs, archived in `data/archived/` on 2026-10-10, until the plan's steps P4–P5. It serves analytics for two betting markets: **comebacks**, where the HT loser wins at FT (`is_comeback`, split into `is_comeback_home` / `is_comeback_away`), and **7+** (7 or more goals, `is_seven_or_more_goals`). Package manager is **uv**; requires **Python 3.13** (pinned in `.python-version`).

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
- Tests: `uv run pytest` (`tests/`; pure functions only so far)

**Run all seven on every change, not just before committing, and do a caller sweep by hand when adding a function.** Ruff and mypy pass clean on unused functions, unreferenced constants and private names called across modules, and pyscn's dead-code detector does not catch unreferenced definitions either (history in `notes/LOG/MIGRATIONS.md`).

pytest (`tests/`, since 2026-10-03) covers pure, mechanical functions across all six packages: labels, parsers, paths, column contracts, config validation, history-cell reading, round positions, the scoring and interval helpers, and the QA checks. **Tests check mechanics only:** never a research finding or anything about the project's outcomes, and a project-chosen constant (a year cutoff, a threshold) is read from the code, not restated. **`tests/` mirrors the packages, one test module per source module:** the tests for `domain/paths.py` live in `tests/domain/test_paths.py`. **Tests never contain the real site's domains;** a URL in a test uses the reserved `example.com`. **Tests never make a network request or start a browser,** not even to `example.com` (the user, 2026-10-13): a scraper test gets a fake driver (`tests/scrapers/test_driver.py`) or a stubbed job (`tests/scrapers/test_schedule.py`). Checked 2026-10-13: the whole suite passes with connections, DNS lookups and new processes blocked. **New code ships with its tests in the same change** (the user, 2026-10-13); there is no separate test backlog. There is no CI. Stage 3 of the schedule has a leak test in pytest since 2026-10-13 (`tests/features/test_schedule_multi.py`: no score or opening odds of a match that kicked off less than 2 h 30 min earlier, or later, reaches a row; fixtures are read by design); the old pipeline's leakage is still guarded only by the hand-run `features.engine --self-check` and `features.chain --replicate-f11`. That matters because this project's real failure mode is statistical leakage, and leaky code is lint-clean by construction.

Tool config: Ruff, mypy and pytest are configured in `pyproject.toml`.

- Ruff lint uses a pragmatic bug-focused set (`E/W/F/I/B/C4/SIM/UP` plus `RUF/PIE/LOG/G/PGH/TID`, line-length 100). `TID` is what enforces the no-relative-imports rule.
- mypy runs `strict = true` with only `prop-decorator` disabled, for the pydantic `@computed_field` idiom.
- Dependencies are split: runtime packages in `[project] dependencies`, every tool (ruff, mypy, complexipy, pyscn, deptry, pytest, stubs, ipykernel) in `[dependency-groups] dev`, pinned exactly. `uv sync` installs both.
- **Every Python tool is a pinned dev dependency run through `uv run`. Never `uvx`.** A new release then cannot change a gate result without a code change, and deptry in particular needs the venv: under `uvx` it cannot see the installed packages and reports false issues. Upgrading a tool is a deliberate version bump.
- pyscn reads `.pyscn.toml`, which disables type-4 clone detection and encodes the layer table below as machine-checked architecture rules.

## Formatting

The user's VS Code formats on save (Ruff for `.py`, pointed at the project's ruff by `.vscode/settings.json`; Prettier with `.prettierrc` for `.md`). A `PostToolUse` hook (`.claude/hooks/format-on-write.sh`) runs the same formatters on every file Claude writes, using the Prettier copy inside the VS Code extension, so a Ctrl+S afterwards changes nothing. **`notes/` is not formatted** (`.prettierignore`): padded tables cost about 2.4× the context on every read.

## Required runtime setup

- `config/leagues.json` (gitignored; start from the committed template `config/leagues.example.json`, one fake league) — a list of leagues: `name`, `code`, `continent`, `country`, `league_id`, `stages` (every stage tab the league page shows, `[]` for none), `keep` (the stages to scrape) and `seasons` (`season`, `url`, `enabled`). `scrapers.schedule` scrapes only the seasons with `"enabled": true`. `scrapers/links.py` validates the whole file when it loads, and fails on any bad entry. Season URLs have the format `/league/<season>/<id>`. **`<season>` takes two forms**, both accepted: `2025-2026` for a cross-year European league (`.../league/2025-2026/36`) and `2025` for a calendar-year one — Scandinavia, Brazil, Japan and others that play inside a single year (`.../league/2025/71`). See "Season labels" in `domain/CLAUDE.md`.
- `data/` — one gitignored tree. **`data/finished/`** is the staged pipeline: `1_raw/` is scraper output only, `2_row/` and `3_multi/` are rebuilt from it; `data/scheduled/` and `data/predictions/` come later. **`data/archived/`** holds the old pipeline's files, moved there on 2026-10-10 (the user's call) and kept for refactoring the detail, goal and event sources: `raw/` (`<league>_<season>.csv`, `_detail.csv`, the goal and event stores) and `processed/` (`_enriched.csv`). The old tools still read and write there until steps P4–P5 move them, so don't run them on the archive. All auto-create on write. All are declared in **`domain/paths.py`**, the only place a data directory or a sibling-file path is constructed — never rebuild one by hand from a filename.
- A locally installed **Chrome** — Selenium 4 auto-manages the driver and runs headless.

## Architecture

Five layers, imported **absolutely** and strictly one-directional — `domain` → `scrapers` → `features` → `analysis` → `ml` (`analysis` imports only `domain` and `features`; `ml` imports those and `analysis`), with `qa` off to the side. Nothing lower may import something higher; that rule is the whole point of the split, so keep it.

| package     | holds                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            | may import                       |
| ----------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| `domain/`   | `schedule.py`, `match_detail.py`, `goal.py`, `event.py` (Pydantic contracts; `schedule.py` also holds the **season-label** parser), `clock.py` (Berlin time with its offset, the project's one clock), `columns.py` (CSV column order), `paths.py` (where files live, and filename↔league/season), `stats.py` (pure derived-stat kernel), `standings.py` (the standings table rebuilt from results), `scope.py` (which history matches are in scope: not friendlies, not pre-2023 pages), `deductions.py` (points deductions declared for the final-table check) | nothing internal                 |
| `scrapers/` | `driver`, `links`, `parsers`, `schedule`, `detail`, `detail_parsers`, `goals`, `live_rows` (the shared live-page row reader), `goal_parsers`, `event_parsers`, `browser_pool`, `csv_io`, `constants` (DOM selectors)                                                                                                                                                                                                                                                                                                                                             | `domain`                         |
| `features/` | `schedule_row.py` and `schedule_multi.py` (the schedule's stages 2 and 3), `stage_io.py` (reading and writing the stage files), `enrich.py` (the base+detail join), `engine.py` (the as-of-round feature matrix), `chain.py`, `history.py` (which history matches count, the shared build shape, and the score reconciliation both builders need), `goals.py` (goal-timing aggregates), `events.py` (card/substitution aggregates, state-conditioned against the goal store)                                                                                     | `domain`                         |
| `analysis/` | one runner per doc of `notes/ANALYSIS/`, in the same tree in lowercase (`schedule/whole_corpus/all/shin.py` → `SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`); shared `corpus.py`, `stats.py`, `methods/`. Prints only, never writes a file; analysis only, no ML (`analysis/CLAUDE.md`)                                                                                                                                                                                                                                                                                    | `domain`, `features`             |
| `ml/`       | the ML runners (models with settings tuned on the data), one per doc of `notes/ML/`, in the same tree in lowercase; shared `rows.py`, `boosting.py` (LightGBM), `score.py`. Prints only, never writes a file (`ml/CLAUDE.md`)                                                                                                                                                                                                                                                                                                                                    | `domain`, `features`, `analysis` |
| `qa/`       | `report.py`, `universal.py` (dataset-agnostic checks), `league.py`, `detail.py`, `goals.py`, `events.py`, `schedule.py` (the staged schedule file), `stages.py` (its stage-2 and stage-3 files against the stages before them), `odds.py` (odds checks for any table, given its columns), `final_table.py` (the page's final table against our rebuilt standings), `validate.py` (orchestrator)                                                                                                                                                                  | `domain`                         |

Every entry point is a module inside its package, run as `python -m <package>.<module>` from the repo root — there are no top-level scripts. Do **not** use relative (`from .x import`) imports anywhere — Ruff's `TID` rule bans them. Import as `from scrapers.parsers import ...`, `from domain import stats`, `from features import engine`.

Modules and directories have been renamed several times. If code or a note cites a path that doesn't exist, check **`notes/LOG/MIGRATIONS.md`**.

## Conventions

- Work directly on `main`; there is no `dev` or feature-branch flow. Since nothing isolates a bad commit from the default branch, run `uv run ruff check && uv run ruff format --check && uv run mypy . && uv run pytest` before committing.
- Change dependencies only with uv commands, never by editing `pyproject.toml` by hand, and pin exactly: `uv add "pkg==1.2.3"` (runtime), `uv add --dev "pkg==1.2.3"` (tools), `uv remove pkg`. A bare `uv add pkg` writes a `>=` bound, so always give the `==` version. uv updates `uv.lock` and the venv in the same step.
- Absolute package imports only (`from domain import stats`), never relative — enforced by Ruff `TID`. Respect the layer direction in the table above.
- Never hardcode a data directory or build a CSV's sibling by string surgery (`base_path.replace(".csv", "_enriched.csv")` was the old idiom and silently resolves to the wrong directory now). Go through `domain/paths.py`.
- Open research decisions go to `notes/WORKING/DECISIONS.md` instead of blocking the current task. Only stop and ask when the task genuinely can't continue without the answer.
- When an item from a `notes/WORKING/IDEAS_*.md` or `notes/WORKING/PLAN_*.md` file is implemented, record it in `notes/LOG/MIGRATIONS.md` under the date it was done and delete it from the file that first mentioned it; a partly done item keeps only its open part there (the user, 2026-10-10). The IDEAS and PLAN files then hold only open work.
- Only `scrapers/` may write to `data/finished/1_raw/`. Everything else derives into the later stage directories and must be reproducible from the raw files — that is what makes the raw corpus safe to treat as ground truth and a derived file safe to delete.
- Line endings: CRLF on disk for every text file, LF inside git (`.gitattributes`). `*.sh` stays LF, because bash fails on `\r`. The formatting hook converts each file Claude writes, since Write creates LF files.

## Where to read

Start with **`notes/WORKING/STATE.md`**, the current state of the research. Before proposing anything in prediction, features or analysis, also read `notes/ANALYSIS/CLAUDE.md` §6.

- `notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md` — before any data-format, data-path or refactor work: the staged pipeline, its decisions and its open steps.
- `notes/FIELDS/README.md` — before touching, adding or reading any column of a staged file: one doc per stage, every field defined once, with its place on the page, timing and role.

- `notes/REFERENCE/GLOSSARY.md` — when a term in a note or CLAUDE.md is unclear: short plain-language cards for the football, statistics, leakage, protocol and ledger terms. Concepts only: keep project results, code and file references, and named leagues or matches out of it, and write new cards in ASD-STE100 Simplified Technical English.
- `notes/REFERENCE/MARKET_COMEBACKS.md` — before measuring or reporting any comeback fact: every fact about the market sorted into definitional (never measure), structural (derived there once, from a goal model) and empirical. Concepts only, under the same rules as GLOSSARY.
- `notes/LOG/MIGRATIONS.md` — when code or a note cites a module, path or column that doesn't exist, and to see what has been implemented from the IDEAS and PLAN notes.
- `notes/HISTORY/HANDOFF.md` — before any prediction, feature or analysis work: strategy guide, base rates, pipeline-specific leakage traps, methodology rules, roadmap.
- `notes/REFERENCE/STATS_PRIMER.md` — when a roadmap step uses Empirical Bayes shrinkage, Brier scores, calibration curves or Dixon–Coles and you need the formulas.
- `notes/REFERENCE/ESOTERIC_MODELS.md` — when a modelling step matches one of its seven tools' tagged "reach for it when" moments.
- `notes/REFERENCE/POINTS_DEDUCTIONS.md` — before touching standings points or rank, or when the final-table check fails on points: every known deduction with its date, cause and source (option A now, C later).
- `notes/RECORD/LEAGUES_INCIDENTS.md` — before analysing, keeping or dropping any scraped league: known match-fixing incidents per league (unverified), and the rule that such decisions use outcome-blind data-quality checks only.
- `notes/RECORD/PREREGISTRATION.md` — before testing any claim; it is the template (closed family list, Holm correction, one holdout opening, dated amendments).
- `notes/RECORD/RESULTS.md` — before proposing any new pre-match comeback feature (six nowgoal-exclusive feature families, all dead).
- `notes/RECORD/PREREGISTRATION_FILTER.md` — when reading or re-running the exclusion-filter study; the closed preregistration it was held to (its verdict is in `FILTER_RESULTS.md`).
- `notes/RECORD/FILTER_RESULTS.md` — before proposing any filter that excludes "comeback-impossible" matches.
- `notes/RECORD/FILTER_STUDY_RAW.md` — only when auditing the filter study's numbers; the frozen raw transcript of the 2026-07-25 `filter_study --bar` run. Later runs saved theirs to `notes/runs/`.
- `notes/RECORD/BEHAVIOURAL_RESULTS.md` — before proposing any hand-weighted candidate rule; it introduced the candidate protocol.
- `notes/RECORD/RETRY_CANDIDATES_2026-09-23.md` — before retrying anything that already failed, and before the multi-country scrape's analysis.
- `notes/RECORD/RELIABILITY_SCREEN_2026-09-23.md` — before building any history-block feature, especially one on cards or substitutions.
- `notes/HISTORY/PLAN_2026-07-25_ENVIRONMENT_FILTER.md` — for the history of the comeback-environment plan: its decisions and its §1 measurements (§1's ceiling is an oracle: that it loses no comebacks is true by definition, `notes/REFERENCE/MARKET_COMEBACKS.md` §1 "Filters that remove impossible matches"). Its open phases moved to `notes/WORKING/IDEAS_2026-10-01.md` idea 4 on 2026-10-14.
- `notes/HISTORY/PLAN_2026-09-20_NEXT_DIRECTION.md` — when deciding what to do next. Its §1 out-of-round refutation does not stand (erratum 2026-10-11: the flag misfired, so the claim is reopened), and its T4 most likely measured Sundays, not Mondays. Its open part, §2 (the prospective gut log), moved to `notes/WORKING/IDEAS_2026-10-01.md` idea 4 on 2026-10-14.
- `notes/HISTORY/ALGOBETTING.md` — background only: a conversation summary on market structure, CLV, the modelling lineage and Asian handicaps. It predates every measured result here, so none of its claims are tested.
