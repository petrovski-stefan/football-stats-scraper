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
| `2026-10-09_corpus_scan` a2 | base rates; comeback and 7+ rates per league; league differences; the same leagues in two seasons | `ALL/RATES.md`, `PER_LEAGUE/RATES.md` | |
| a3, a7, b3 | the yardstick per league | `PER_LEAGUE/ODDS_YARDSTICK.md` | Done on 2026-10-18: `ALL/ODDS_YARDSTICK.md` (observed against expected, the rate by win chance and expected goals, the test of the one first-half share) and `ALL/SCORE_EFFECTS.md` (second-half score effects, and a7's question: how much of the comeback gap they close). Test the share per league too. |
| a4 | the return by price band (1X2, O/U, AH) | `ALL/PRICES.md` | Where the comeback excess sits is in `ALL/ODDS_YARDSTICK.md` since 2026-10-18. |
| b1, b2 | 29 stage-3 fields beyond the odds, one at a time; the same out of sample, one season against the other | `ALL/PREMATCH_SCREEN.md` (b2 is its per-season slice) | b2 also used boosted trees. That is machine learning, so it waits for the later prediction package (`analysis/CLAUDE.md` §1). Only logistic regression moves. |
| c1 | the comeback rate by season phase and by round | `ALL/SEASON_PHASE.md` | |
| d1, d2 | do comebacks collect on identical opening prices | `ALL/ODDS_GROUPS.md` | |
| a1, a5, a8, `load.py`, `run_all.py` | — | none | a1's counts are the corpus line, and its margins are in `SHIN.md`. a5 lists the QA failures of one day. a8 is a QA check now (`qa/odds.py`). `analysis/corpus.py` does the work of `load.py` and `run_all.py`. |
| `2026-10-10_odds_coverage` | the odds coverage per league, and the cause of each gap | `PER_LEAGUE/ODDS_COVERAGE.md` (short) | Six of its sections are QA checks since 2026-10-11. Today one match has no odds. |
| `2026-10-12_stakes` | the stakes test: flags F1 and F2 | `ALL/STAKES.md` | Copy the frozen plan of its `TEST.md` into the doc first. No STATE row (the user, 2026-10-13). |
| `2026-10-13_zone_stakes` | zone lines from team turnover, and the zone-stakes test | `ALL/ZONE_STAKES.md`; the zone lines as `analysis/methods/zones.py` | Copy its `TEST.md` first. No STATE row. |
| `2026-10-13_round_so_far`, `2026-10-13_round_goals` | a recount and a scramble check of S3.14–20, and how often each value occurs | `ALL/ROUND_FIELDS.md` (how often only) | pytest has the checks now: the `round_so_far` tests and the stage-3 leak test in `tests/features/test_schedule_multi.py`. Then change the citations in `notes/FIELDS/SCHEDULE_3_MULTI.md` §A2. |
| the weekday check (no folder) | comebacks and 7+ by weekday | `ALL/WEEKDAY.md` (optional) | Its numbers are in `notes/LOG/MIGRATIONS.md` 2026-10-11. |
| none: the level design of 2026-10-18 | the card of a team, with the repeat test; clusters in one round; which level the differences sit at | `PER_TEAM/RATES.md`, `PER_TEAM/ODDS_YARDSTICK.md`, `ALL/ROUND_CLUSTERS.md`, `ALL/LEVELS.md` | No run asked these. All four use the yardstick. |

## 3. Order (one doc for each sitting)

| step | docs | size |
|---|---|---|
| 1 | §1 above | 2–3 h |
| 2 | `PER_LEAGUE/ODDS_YARDSTICK`: it uses the yardstick (`ODDS_YARDSTICK`, `SCORE_EFFECTS` and `HTFT` were done on 2026-10-18) | 2–3 h |
| 3 | `RATES`, `PER_LEAGUE/RATES`, `PRICES` | 4–5 h |
| 4 | the new docs of the level design: `PER_TEAM/RATES`, `PER_TEAM/ODDS_YARDSTICK`, `ROUND_CLUSTERS`, `LEVELS` | 11–15 h |
| 5 | the screens and the measured nulls: `PREMATCH_SCREEN`, `SEASON_PHASE`, `ODDS_GROUPS`, `STAKES`, `ZONE_STAKES`, `WEEKDAY` | 12–16 h |
| 6 | `ROUND_FIELDS`, `ODDS_COVERAGE`, and the new citations in `SCHEDULE_3_MULTI.md` | 2–3 h |
| 7 | delete `notes/runs/` and its line in `.gitignore`; a MIGRATIONS entry | ~0.5 h |

Total: about 4–5½ days of Claude's work, plus §1.

## 4. Rules for each run

- Measure every number again on the corpus of the day. Copy nothing from an old output or from memory.
- A run that tested a frozen plan (the stakes and zone-stakes tests) keeps its plan: the doc's Method gets a copy before the folder goes. The new run is exploratory. It is not a second test.
- Delete a run folder only when each of its questions has a doc, or a line in §2 that tells why not. Back the folder up first: git cannot restore it.
- A claim goes into STATE only with the user's go.

## 5. Done when

- `notes/runs/` and its `.gitignore` line are gone. Only Log entries, Record notes and History notes still cite `notes/runs/`.
- `uv run mypy .` shows 0 errors. Today its 45 errors are all in `notes/runs/` scripts.
- pyscn shows 0 layer violations. Today its 20 are all in `notes/runs/` scripts.
- The seven gates pass.

## 6. Later: docs that need the detail or the live page

These docs wait until plan steps P4–P6 (`notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md`) make the detail and live stage-3 files. The source folder follows `notes/ANALYSIS/CLAUDE.md` §2. The list is a brainstorm, not an order.

| folder | examples |
|---|---|
| `SCHEDULE_DETAIL` | the move of the 1X2 price from opening to closing (Initial → Live) against the result; the form and h2h windows (the old families A–F of `notes/RECORD/RESULTS.md`); rest days (D3.24) |
| `SCHEDULE_LIVE` | the minute of the trailing team's goals in comebacks; second-half scoring by minute and state; the leader's second-half yellow cards → completion (`notes/RECORD/RELIABILITY_SCREEN_2026-09-23.md` §4); team goal-timing and card traits (retry claims #11–13 and #15) |
| `SCHEDULE_DETAIL_LIVE` | one screen of form (detail) and goal-timing traits (live) together, beyond the odds |
| `DETAIL`, `LIVE` | the bookmakers on the h2h page; the share of friendlies in the history rows; the spread of goal minutes over every scraped match |
