# MIGRATIONS — renames, moves and deletions

If code or a note cites a module, path or column that doesn't exist, it predates one of the changes below. Older `notes/` entries written before 2026-07-27 cite the earlier flat layout — module paths (`features.py`, `constants.py`, `df.py`, `stats.py`) and the single `data/` directory. **Their findings stand; only the paths moved** — see also the amendment log in `notes/PREREGISTRATION.md`.

## 2026-07-26

- **Module renames.** The old `constants.py` split into `scrapers/constants.py` (DOM selectors, user agents, transliteration table) and `domain/columns.py` (`ORDERED_DF_COLUMNS`, `DETAIL_ORDERED_COLUMNS`, `per_match_columns()`). The old `df.py` is `scrapers/csv_io.py`. The old `features.py` is `features/engine.py` (renamed because `features.matrix` would have collided with the pervasive local `matrix` variable).
- **`core/` collapsed.** A short-lived `core/` package was collapsed: `stats.py` moved into the base layer (its consumers span three packages, and it defines the meaning of the derived columns `domain/columns.py` declares), while `exceptions.py` was deleted as dead code with zero references anywhere in the repo.
- **`schemas/` → `domain/`.** The base layer, briefly called `schemas/`, was renamed `domain/` because it holds the pure `stats.py` kernel alongside the Pydantic contracts, and "schema" only described three of its four modules.
- Anything citing `core.stats`, `schemas.columns`, or `schemas/match.py` predates 2026-07-26.
- **`dev` branch retired.** `dev` was merged into `main`.
- **DOM-order booleans removed.** `is_first_match_in_round`, `is_before_last_match_in_round`, `is_last_match_in_round` were removed; use `features/engine.py:round_position` (see `features/CLAUDE.md` §6).
- **football-data.co.uk corpus retired** from the repo, and with it the cross-source check in `qa.validate`. `notes/MARKET_LINE_FINDINGS.md` §5 records how to re-fetch it.

## 2026-07-27

- **`data/` split by provenance.** The flat `data/` directory gained `data/raw/` (scraper output) and `data/processed/` (derived).
- **Enrich join moved** from `scrapers/detail.py` (`detail._write_enriched`) to the new `features/enrich.py`. Anything describing the detail scraper as writing `_enriched.csv` predates this.
- **`domain/paths.py` created.** Directory and sibling-path construction was consolidated there; previously there were five separate `DATA_DIR = "data"` definitions.
- **`scripts/` deleted.** The one-off `scripts/backfill_round_index.py` was deleted, its migration having been applied, leaving the repo with no `scripts/` package.
- Anything naming a CSV **directly** under `data/` (rather than in `data/raw/` or `data/processed/`), or citing `scripts.` or `detail._write_enriched`, predates 2026-07-27.
- **Why the five quality gates exist.** Three defects were found by hand this day, not by a tool: an unused module-level function, an unreferenced constant, and a private name called across modules. Ruff and mypy passed clean on all three. pyscn's own dead-code detector scored 100/100 while such code was present, because it detects unreachable statements, not unreferenced definitions. Hence root `CLAUDE.md`'s "run all five plus a manual caller sweep".

## 2026-09-20

- **`modelling/analysis.py` deleted.** It had been self-marked SUPERSEDED since 2026-07-25 ("kept only until it is committed, then delete") and was committed in `6643b1f`. It ran ~15 uncorrected bucket tests against `is_comeback`, most of them re-testing LEAGUE_STUDY F10's graveyard on a corpus 11× smaller than the one that established it. Its two reusable helpers, `wilson_ci` and `required_n`, already live in `modelling/experiment.py`. Anything citing `modelling.analysis` predates 2026-09-20.
- **`home_next_fixture_days` QA FAIL deferred.** Every league-season FAILed on this known-stale column; deferred because the parser was confirmed correct and only the stored data was at fault.

## 2026-09-22

- **History match/league ids added to detail.** `*_lastN_match_id` / `*_lastN_league_id` took `DETAIL_ORDERED_COLUMNS` from 501 to 537. Detail files scraped earlier lack them (consequence: `scrapers/CLAUDE.md` §7, "The work list").
- **`home_next_fixture_days` FAIL cleared.** The detail re-scrape fixed it with no code change, exactly as predicted; every league-season now PASSES that check.

## 2026-09-23

- **Combined event timeline split into four** (`goal` / `yellow` / `red` / `sub`). Rationale and measurements: `features/CLAUDE.md` §3.

## 2026-10-01

- **`config/LEAGUES.txt` replaced by `config/leagues.json`.** The league list is now JSON: one object per league (`name`, `code`, `continent`, `country`, `league_id`, `stages`, `keep`) with a `seasons` array (`season`, `url`, `enabled`). `enabled: true` replaces uncommenting a URL. `scrapers/links.py:get_leagues_links()` became `get_league_seasons()`, and the file is validated by `links.LeagueConfig`. The temporary `config/LEAGUE_STAGES.txt` review file was folded into the same JSON. Anything citing `config/LEAGUES.txt` or `get_leagues_links` predates 2026-10-01. Its findings stand.
- **Schedule scraper clicks stage tabs.** `scrapers.schedule` scrapes each stage named in `keep` and writes its name to `stage`. Before this, a page with several stages had every stage's round buttons read as one list, and the standings could show another stage's table. Downstream ordering is open: `notes/DECISIONS.md` D7.

## 2026-10-02

- **Detail and live pages moved from `live10` to `live11.nowgoal26.com`.** The site now answers every `live10` page with a `301` to the same path on `live11`, and `live10` itself timed out on some loads. `DETAIL_URL` and `LIVE_URL` in `scrapers/constants.py` point at `live11`. Anything citing `live10.nowgoal26.com` predates 2026-10-02; match ids and page layout are unchanged.
