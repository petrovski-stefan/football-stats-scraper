# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Selenium + BeautifulSoup scraper that collects finished football match data (teams, date, round, standings positions, HT/FT goals) from **nowgoal26.com** league pages, validates it with a Pydantic `Match` model (`domain/match.py`), and writes per-league CSVs to `data/`. Purpose: analytics for two betting markets — comebacks (`is_match_transition`) and over 6.5 goals (`is_match_7plus`). Package manager is **uv**; requires **Python 3.13** (pinned in `.python-version`).

Never call the site's data/API endpoints directly — always render pages in Selenium and parse the DOM.

**Before working on prediction, features, or analysis, read `notes/HANDOFF.md`** — the project's strategy/statistics guide: measured base rates, leakage traps specific to this pipeline, methodology rules, and the prioritized roadmap. Its companion **`notes/STATS_PRIMER.md`** explains the statistical tools the roadmap relies on (Empirical Bayes shrinkage, Brier scores, calibration curves, Dixon–Coles) with formulas and worked examples from this dataset. **`notes/ESOTERIC_MODELS.md`** holds seven further tools (Shin's method, favorite–longshot bias, Markov absorption, lead-survival hazards, state-space ratings, Pythagorean expectation, Kelly-as-KL) each tagged with the future moment to reach for it. **`notes/LEAGUE_STUDY.md`** reports the 23,127-match football-data.co.uk study (22 divisions across 11 countries — about one fifth of Europe, 2023-26) whose measurements supersede the older PL-only numbers — read it before designing any comeback feature: league/team comeback-proneness and the balanced-match precondition are refuted within the surveyed fifth, the trailing-team completion curve is measured, and the preregistered bar for admitting any of Europe's remaining ~30 countries as a comeback-candidate league is defined there. **`notes/RESULTS.md`** records the July 2026 attempt to overturn F12 using nowgoal-exclusive features (rolling HT-state history, 2H supremacy, corner-vs-goal pressure, site strength/crowd consensus, cross-competition congestion, venue/H2H splits) — all six families died, and the well-powered finding is that the *half-time state itself* is barely predictable: the bookmaker's price improves on a constant by only 0.64%. Read it before proposing any new pre-match comeback feature. Its **`notes/PREREGISTRATION.md`** is the template for how a claim in this project gets tested (closed family list, Holm correction, one holdout opening, amendments logged with dates). **`notes/FILTER_RESULTS.md`** then tested the opposite-signed question — can matches where a comeback is *impossible* be filtered out pre-match? — and that failed too: an oracle knowing the goal total excludes 44.2% of matches with zero misses, but the pre-match goal forecast reaches only AUC 0.559, recovering ~15% of the distance the bar needs. Both failures share one root: **pre-match forecastable structure in football is very thin**, and comebacks sit downstream of two weak signals (half-time state and goal total). Do not propose a new pre-match comeback feature without reading both. The reusable asset from that study is **`modelling/scoreline.py`**, a calibrated generative model of the full scoreline distribution — the natural instrument for the over-6.5 market (F9/F13), which is a direct functional of the same goal distribution. **`notes/MARKET_LINE_FINDINGS.md`** then measured what beat all of it: the bookmaker's Over/Under 2.5 line reaches AUC 0.592 on the comeback-environment conjunction where in-house features reached 0.497, and a two-column market model clears `PLAN_2026-07-25`'s top-20% slate bar out-of-sample at 1.33× (Wilson LB 5.68% vs 5.16% base, n=7,675). It is **exploratory, not preregistered** — read its §4 before quoting the number, and its §7 for why the corpus scrape's purpose changed. The football-data.co.uk corpus it was measured on was retired from the repo on 2026-07-26; §5 records how to re-fetch it.

## Commands

- Install deps: `uv sync`
- Run the league scraper: `uv run python -m scrapers.schedule`
- Run the detail enricher: `uv run python -m scrapers.detail [--limit N]` (resumable; `--limit` caps the batch)
- Validate the corpus: `uv run python -m qa.validate` — internal self-consistency, **exits non-zero on any failure**. No exemptions: it currently reports FAIL on all six league-seasons for the known-stale `home_next_fixture_days` column (see `notes/PREREGISTRATION.md` §9); that clears on a detail re-scrape. The cross-source check was retired with the football-data corpus on 2026-07-26.
- Build the feature matrix: `uv run python -m features.engine` (`--self-check` proves the as-of-round invariant)
- Validate the imported F11 completion curve: `uv run python -m features.chain --replicate-f11`
- Screen features: `uv run python -m modelling.experiment --dev` — **`--holdout` opens the untouched season and is a one-shot**
- Validate the scoreline model: `uv run python -m modelling.scoreline --self-check --leak-check`
- Run the exclusion-filter study: `uv run python -m modelling.filter_study --curve` / `--bar`

All commands run from the repo root — the data/notes/config paths are relative to the
working directory, not to the module.
- Lint: `uv run ruff check` (autofix: `uv run ruff check --fix`)
- Format: `uv run ruff format` (check only: `uv run ruff format --check`)
- Type-check: `uv run mypy .`

(No test framework or CI is set up yet. Ruff and mypy are both configured in `pyproject.toml` — Ruff lint uses a pragmatic bug-focused set (`E/W/F/I/B/C4/SIM/UP` plus `RUF/PIE/LOG/G/PGH/TID`, line-length 100), where `TID` is what enforces the no-relative-imports rule; mypy runs `strict = true` with only `prop-decorator` disabled for the pydantic `@computed_field` idiom.)

## Required runtime setup

- `config/LEAGUES.txt` — one nowgoal26 league URL per line, format `/league/<season>/<id>` (e.g. `https://football.nowgoal26.com/league/2025-2026/36`). Committed with the PL example.
- `data/` — output dir for `<league>.csv`; auto-created by `scrapers/csv_io.py:save_df_to_csv()`.
- A locally installed **Chrome** — Selenium 4 auto-manages the driver and runs headless.

## Architecture

### Package layout

Four layers, imported **absolutely** and strictly one-directional — `domain` → `scrapers` → `features` → `modelling`, with `qa` off to the side. Nothing lower may import something higher; that rule is the whole point of the split, so keep it.

| package | holds | may import |
|---|---|---|
| `domain/` | `match.py`, `match_detail.py` (Pydantic contracts), `columns.py` (CSV column order), `stats.py` (pure derived-stat kernel) | nothing internal |
| `scrapers/` | `driver`, `links`, `parsers`, `schedule`, `detail`, `detail_parsers`, `csv_io`, `constants` (DOM selectors) | `domain` |
| `features/` | `engine.py` (the as-of-round feature matrix), `chain.py` | `domain` |
| `modelling/` | `scoreline`, `experiment`, `filter_study`, `analysis` | everything below |
| `qa/` | `report.py`, `universal.py` (dataset-agnostic checks), `league.py`, `detail.py`, `validate.py` (orchestrator) | `domain` |

Every entry point is a module inside its package, run as `python -m <package>.<module>` from the repo root — there are no top-level scripts. Do **not** use relative (`from .x import`) imports anywhere — Ruff's `TID` rule bans them. Import as `from scrapers.parsers import ...`, `from domain import stats`, `from features import engine`.

Two names moved and are easy to mis-search for: the old `constants.py` split into `scrapers/constants.py` (DOM selectors, user agents, transliteration table) and `domain/columns.py` (`ORDERED_DF_COLUMNS`, `DETAIL_ORDERED_COLUMNS`, `per_match_columns()`); the old `df.py` is `scrapers/csv_io.py` and the old `features.py` is `features/engine.py` (renamed because `features.matrix` would have collided with the pervasive local `matrix` variable). Two further changes landed the same day, both worth knowing when reading anything written earlier: a short-lived `core/` package was collapsed — `stats.py` moved into the base layer (its consumers span three packages, and it defines the meaning of the derived columns `domain/columns.py` declares) while `exceptions.py` was deleted as dead code with zero references anywhere in the repo — and that base layer, briefly called `schemas/`, was renamed **`domain/`**, because it holds the pure `stats.py` kernel alongside the Pydantic contracts and "schema" only described three of its four modules. Anything citing `core.stats`, `schemas.columns`, or `schemas/match.py` predates 2026-07-26.

### Scrape flow

`schedule.scrape_all()` → `links.get_leagues_links()` reads league URLs, `links.parse_league_url()` splits each into `(season, league_id)` → `schedule.scrape_league()` opens headless Chrome (`driver.get_driver()`), renders the page, and iterates rounds `1..current`. For each round it clicks the round span (`driver.click_round`) and syncs the standings dropdown to the same round (`driver.sync_standings_to_round`) — both use `WebDriverWait`, not `sleep`. It parses `driver.page_source` with BeautifulSoup: `parsers.parse_standings()` builds a `{team_id: rank}` map, `parsers.parse_schedulis_row()` extracts each `div.schedulis` match. Teams are matched to standings **by team id** (`toTeam('<id>')`), not by name. Rows are validated by the `Match` model (`schedule._validate`) and written by `scrapers/csv_io.py:save_df_to_csv()` (column order from `domain.columns.ORDERED_DF_COLUMNS`).

Key DOM facts (nowgoal26): only one round renders at a time (`div.round span[round=N]`, live round has class `current on`); each match row carries `@matchid`, `@score`, `span.ht` (half-time), `span.date[data-t]`; standings are at `ul#standingList li.standlis` with a per-round dropdown `li[data-st-r=N]`. All selectors live in `scrapers/constants.py`.

`parsers.parse_schedulis_row()` returns **only scraped primitives** — no derived values. Every derived column (goals splits, results, market flags, date and odds derivations) is a `@computed_field` on `domain/match.py:Match`, computed from `domain/stats.py`. Keep that division: new DOM extraction goes in `scrapers/parsers.py`, new arithmetic on already-scraped values goes on the model or in `domain/stats.py`.

### Detail enrichment (second stage)

`scrapers/detail.py` scrapes each finished match's detail page (`https://live10.nowgoal26.com/match/h2h-<match_id>` — same id as the schedule row) into **one wide feature row** per match, joined to the base league CSV. `scrape_match_detail(driver, match_id)` is **mode-agnostic** (a future prediction mode can feed upcoming ids); `enrich_finished(limit)` reads ids from `data/*.csv`, **reuses one browser**, and is **resumable** — it skips ids already in `data/<league>_detail.csv` and appends incrementally, then writes `data/<league>_enriched.csv` (base left-joined to detail; base CSV untouched). Detail is ~1 page render **per match** (heavy: ~380/season) — always run it resumable, not from scratch.

`scrapers/detail_parsers.py` parses each section: `parse_odds_1x2` (Bet365-or-first 1X2, initial+live; the 1X2 cells are `td[data-e="1"]`), and the H2H widget tables `tr[id^='tr1_'/'tr2_'/'tr3_']` (v1=home recent, v2=away recent, v3=H2H; score span class is indexed per table so match on prefix `span[class^='fscore']`, and each row is 15 cells — league/date/teams/score/**corner**/1X2 odds). Those rows feed two outputs: **aggregates** (`aggregate_recent`/`aggregate_h2h` → `*_recent_*`, `h2h_*`) and **per-match column blocks** (`flatten_history` → `home_lastN_*`/`away_lastN_*`/`h2h_lastN_*`, last1 = most recent, `N` up to `domain.columns.MATCHES_PER_SECTION`, oriented to the section's subject team). Plus best-effort strength/guess/standings/fixtures. Per-match derived stats (over2.5, BTTS, comeback, 1X2 result, implied prob) live in **`domain/stats.py`**, shared by the `Match` model and the detail records. Aggregate/odds fields are validated by `domain/match_detail.py:MatchDetail`; the per-match blocks are merged in as plain data. Full column order (incl. generated per-match names) comes from `domain.columns.DETAIL_ORDERED_COLUMNS` / `domain.columns.per_match_columns()`.

## Domain notes

- Only **finished** matches are emitted — `parsers.parse_schedulis_row()` returns `None` when HT+FT scores don't both parse as `int - int`, so unplayed/live rows are skipped.
- Standings positions are cumulative **as of the round being scraped** (dropdown synced per round).
- 1X2 odds: the schedule odds column defaults to Asian Handicap, so `driver.switch_odds_to_1x2()` clicks the header selectbox (`li[type='O']`) once after load — the choice persists across round clicks. Odds cells are then home/draw/away; missing odds parse to `None` (`has_odds=False`). Odds fields on `Match` are nullable.
- Markets: `is_seven_or_more_goals` (over 6.5), `is_comeback` (HT-loser wins at FT) split into `is_comeback_home`/`is_comeback_away`. Raw score strings (`ht_score`, `ft_score`) are kept alongside the derived goal ints.
- **Position within a round.** `match_index_in_round` is 1..`matches_in_round`, ordered by kickoff datetime then home name then away name (`domain/match.py:round_sort_key`). It is assigned in `scrapers/schedule.py:_order_round` over **every scheduled match in the round including unplayed ones**, then only finished rows are written — so `matches_in_round` can exceed the row count for a partially-played round, and the position cannot be recomputed downstream (unplayed rows never reach the CSV). This is the one derived column that cannot be a `@computed_field` on `Match`, because it depends on the round's other rows.
- **Never read `match_index_in_round == 1` as "the first match of the round".** 15.6% of matches share their round's earliest kickoff and the tiebreak between them is alphabetical, i.e. meaningless. Use `features/engine.py:round_position`, which derives tie-aware `earlier` / `later` / `slot` / `slots` from `date`: joint-first is `earlier == 0` (321 matches in the current corpus), joint-last is `later == 0` (263). These are derived, not stored, because they are pure functions of a column that is already there. The three former DOM-order booleans (`is_first_match_in_round`, `is_before_last_match_in_round`, `is_last_match_in_round`) were removed on 2026-07-26 for exactly this reason.

## Conventions

- Commit directly to the `dev` branch (main branch for releases is `main`).
- Pin dependency versions exactly in `pyproject.toml` (matches existing style); update `uv.lock` via `uv`.
- Absolute package imports only (`from domain import stats`), never relative — enforced by Ruff `TID`. Respect the layer direction in the table above.
- Older `notes/` entries written before 2026-07-26 cite the pre-refactor flat module paths (`features.py`, `constants.py`, `df.py`, `stats.py`). Their findings stand; only the paths moved — see the amendment log in `notes/PREREGISTRATION.md`.
