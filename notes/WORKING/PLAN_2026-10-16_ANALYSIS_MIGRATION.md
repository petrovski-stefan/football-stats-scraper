# PLAN — every run in the new analysis workflow

**Group: Working.** Edit it in place, and keep it current. Move done items to `notes/LOG/MIGRATIONS.md`.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

**Status: in progress since 2026-10-18** (the user: "Next is runs/ deletion and migration"). **Written 2026-10-16.** The idea is the user's: drop every run in `notes/runs/`, and do each one again in the new workflow. In that workflow, a runner in `analysis/` calculates and prints, and Claude writes the doc in `notes/ANALYSIS/` (`notes/ANALYSIS/CLAUDE.md`). Shin's method proved the workflow on 2026-10-16 (`notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`). The mapping and the order below are Claude's proposal. The user decides them when the work starts.

**Why:** a run in `notes/runs/` is outside git. Its script, its output and its frozen plan can get lost, and no claim can cite it. A doc in `notes/ANALYSIS/` is in git, and its runner can run again.

## 1. First: finish the switch (agreed with the user, 2026-10-16)

1. Write the notes workflow docs: `notes/CLAUDE.md` (the rules for every note) and one `CLAUDE.md` in each group folder. The rules that are only in Claude's memory go into them (the user, 2026-10-16).

## 2. Each run and its new docs

All docs go into `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/`, because every run read schedule fields only. Each runner has the same path in lowercase.

| run | what it asked | new docs | note |
|---|---|---|---|
| `2026-10-09_corpus_scan` b1, b2 | 29 stage-3 fields beyond the odds, one at a time; the same out of sample, one season against the other | `ALL/PREMATCH_SCREEN.md` (b2 is its per-season slice) | b2 also used boosted trees. That is machine learning, so it waits for the later prediction package (`analysis/CLAUDE.md` §1). Only logistic regression moves. |
| `load.py`, `run_all.py` | — | none | `analysis/corpus.py` does their work. They go with the last script of the folder. |
| the weekday check (no folder) | comebacks and 7+ by weekday | `ALL/WEEKDAY.md` (optional) | Its numbers are in `notes/LOG/MIGRATIONS.md` 2026-10-11. |
| none: the level design of 2026-10-18 | clusters in one round; which level the differences sit at | `ALL/ROUND_CLUSTERS.md`, `ALL/LEVELS.md` | No run asked these. Both use the yardstick. |

## 3. Order (one doc for each sitting)

| step | docs | size |
|---|---|---|
| 1 | §1 above | 2–3 h |
| 2 | (done 2026-10-19; `notes/LOG/MIGRATIONS.md`) | — |
| 3 | (done 2026-10-19; `notes/LOG/MIGRATIONS.md`) | — |
| 4 | the new docs of the level design: `ROUND_CLUSTERS`, `LEVELS` | 5–7 h |
| 5 | the screens and the measured nulls: `PREMATCH_SCREEN`, `WEEKDAY` (`SEASON_PHASE`, `ODDS_GROUPS` and `STAKES` done 2026-10-19; `ZONE_STAKES` skipped by the user) | 4–6 h |
| 6 | (done 2026-10-19; `notes/LOG/MIGRATIONS.md`) | — |
| 7 | delete what is left of `notes/runs/`, and its line in `.gitignore`; a MIGRATIONS entry | ~0.5 h |

Total: about 2½–3½ days of Claude's work, plus §1.

## 4. Rules for each run

- Measure every number again on the corpus of the day. Copy nothing from an old output or from memory.
- A run that tested a frozen plan (the stakes and zone-stakes tests) keeps its plan: the doc's Method gets a copy before the folder goes. The new run is exploratory. It is not a second test.
- When each question of a run script has a doc, or a line in §2 that tells why not, delete the script and its outputs at once. Delete the folder with its last script (the user, 2026-10-19). A partly done script loses the part that is done. Back up first, because git cannot restore them: a dated zip in `Desktop/football-stats-scraper_backups/`, next to the repo.
- A claim goes into STATE only with the user's go.

## 5. Done when

- `notes/runs/` and its `.gitignore` line are gone. Only Log entries, Record notes and History notes still cite `notes/runs/`.
- `uv run mypy .` shows 0 errors. On 2026-10-19 its 16 errors are all in the two scripts left in `notes/runs/` (b1, b2).
- pyscn shows 0 layer violations: met on 2026-10-19.
- The seven gates pass.

## 6. Later: docs that need the detail or the live page

These docs wait until plan steps P4–P6 (`notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md`) make the detail and live stage-3 files. The source folder follows `notes/ANALYSIS/CLAUDE.md` §2. The list is a brainstorm, not an order.

| folder | examples |
|---|---|
| `SCHEDULE_DETAIL` | the move of the 1X2 price from opening to closing (Initial → Live) against the result; the form and h2h windows (the old families A–F of `notes/RECORD/RESULTS.md`); rest days (D3.24) |
| `SCHEDULE_LIVE` | the minute of the trailing team's goals in comebacks; second-half scoring by minute and state; the leader's second-half yellow cards → completion (`notes/RECORD/RELIABILITY_SCREEN_2026-09-23.md` §4); team goal-timing and card traits (retry claims #11–13 and #15) |
| `SCHEDULE_DETAIL_LIVE` | one screen of form (detail) and goal-timing traits (live) together, beyond the odds |
| `DETAIL`, `LIVE` | the bookmakers on the h2h page; the share of friendlies in the history rows; the spread of goal minutes over every scraped match |
