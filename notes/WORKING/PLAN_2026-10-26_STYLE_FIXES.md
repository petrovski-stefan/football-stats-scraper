# PLAN — the style fixes from the strict check of 2026-10-26

**Group: Working.** Edit it in place, and keep it current. Move done items to `notes/LOG/MIGRATIONS.md`.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

**Status: IN PROGRESS.** The user asked for this plan on 2026-10-26, and gives the groups to fix one by one.

**Why:** a strict, read-only check of all `.py` files against `CODING_STYLE.md` found 9 groups of breaches. A second strict check found groups 10–14. Groups 2, 3 and 10 break a Must rule (`CODING_STYLE.md` §1). Groups 7, 8, 11, 13 and 14 break a Default rule. Groups 1, 4, 5, 6, 9 and 12, the §5 item, the new-pipeline items of groups 8, 11 and 14, and parts of groups 3 and 7 are done (`notes/LOG/MIGRATIONS.md`, 2026-10-26).

**Scope:** about 80 % of the breaches are in the old pipeline. The old pipeline is `features/{engine,enrich,events,goals,history,chain}.py`, `scrapers/{detail,detail_parsers,goals,goal_parsers,event_parsers,live_rows,browser_pool}.py`, `domain/{match_detail,goal,event}.py` and `qa/{league,detail,goals,events}.py`. Root `CLAUDE.md` keeps it until the steps P4–P5 of `PLAN_2026-10-05_STAGED_PIPELINE.md`. `CODING_STYLE.md` §1 says: code that nobody changes stays as it is. Thus, fix an old-pipeline item when P4–P5 change its function, or in a clean-up pass of its own.

---

## Method and measurements

- The check read 165 files (22,604 lines) on 2026-10-26, at commit `3d8941e`.
- Three AST and token sweeps found the candidates. Claude read each flagged site by hand and removed the false positives.
- These rules had 0 breaches: a blank line after each docstring, a blank line before each final `return`, the `_df` suffix (the 16 flags were functions with the same name), `_private` names across modules, wildcard imports, `raise` without `from` in an `except`, bare `except`, `# type: ignore` without an error code, test names as sentences, named Hypothesis strategies, assert messages in loops.
- Some counts come from a heuristic. Each such count says so. Do a check of each site before you change it.
- The second check ran on 2026-10-26, at commit `7658109`. It did all the sweeps of the first check again, and these sweeps too: names of 2 or 3 letters and short forms, nested comprehensions, nesting depth, fills with a fixed value, `except` blocks that return an empty value, arguments that a function changes, dynamic dispatch, and project numbers written again in tests.
- In the second check, these rules had 0 breaches: every function has a docstring, no docstring has more than 3 lines of prose, every `main` docstring starts with `Entry point:`, the blank lines after a docstring and before a final `return`, and one-letter names.
- In the second check, these flags were correct code: a parser that gives `None` for a page cell without a number, `fillna(0)` inside a sum that a mask limits, `rng`, `report.check(passed)`, `getattr` with a fixed field name, and the numbers in test data.

---

## Must rules

### 2. §10: errors

- `scrapers/detail.py:92` and `scrapers/goals.py:231` catch `Exception` around one job. The callers (`detail.py:126`, `goals.py:284`) log with `logger.warning`, so there is no traceback. The run does not exit non-zero at the end. §10 needs `logger.exception` and a non-zero exit (`scrapers/schedule.py:_run_job` is the model).
- `features/enrich.py:74` raises `RuntimeError`. `features/engine.py:317` raises `AssertionError`. Fix: a specific exception, for example `KeyError` or `ValueError`.

### 3. §9: a rule outside its home

- **Times:** `analysis/schedule/whole_corpus/all/prematch_screen.py:257`, `round_clusters.py:156` and `season_phase.py:42` parse `s1_date` with `pd.to_datetime`. `ml/rows.py:139` and `features/schedule_multi.py:116` use `clock.parse_instant`. Fix: one way, through `domain/clock.py`.
- **Clock:** `scrapers/goals.py:236` uses `datetime.now(UTC)`. The project clock is `domain/clock.py` (Berlin time with its offset).
- **Comeback:** `features/chain.py:146–165` calculates "completed" by hand. Fix: use `domain/stats`.
- These items touch `features/` and `analysis/`, so `/stats-review` is due after the fix.

### 10. §9 and §10: a value that does not parse is read as missing

- `scrapers/goals.py:_as_int` catches `TypeError` and `ValueError` and returns `None`. Thus a `league_id` in a CSV that is not a number counts as missing, and nothing fails. §9 says: a file that does not parse raises.
- Decision for the user: does a bad id stop the run, or is it logged and skipped as one failed job (§10)?
- Do a check of `scrapers/detail_parsers.py:77` and `:89`: `attr(...) or ""` changes a missing id or date into `""` (old pipeline).

---

## Default rules

### 7. §4 and §8: function shape and contracts

- Tuples of 3 or more unnamed values (16): `analysis/methods/shin.py:25` `shin_row` (4 floats), `per_league/rates.py:38` `quantity` (4 strs), `analysis/units.py:161` `repeat_test`, `:278` `within_test`, `:95` `tested`, `analysis/methods/yardstick.py:86` `fit_rates`, `scrapers/detail_parsers.py:395` `_row_1x2`, `scrapers/parsers.py:92` `_odds_cells`, `scrapers/detail.py:85` and `scrapers/goals.py:223` `_scrape_one`. Fix: a frozen dataclass.
- Long argument lists: `scrapers/goals.py:239` `_store_rows` (8), `analysis/units.py:57` `unit_values` (7).
- Long function: `analysis/schedule/whole_corpus/all/odds_yardstick.py:148` `main` (101 lines).

### 8. §6: expressions and numbers

Only old-pipeline items are open.

- 7 comprehensions with more than one `for`: `features/engine.py:142`, `:608`, `features/events.py:123`, `features/goals.py:59`, `features/history.py:98`, `scrapers/goals.py:114`, `:120`.
- Heuristic: 17 module constants have no comment on their line or on the line above. Some can have a comment further up, over a group. Examples: `scrapers/detail.py:40` and `scrapers/goals.py:64` `WORKERS`, `features/engine.py:41–42`, `features/chain.py:29–36`, `qa/goals.py:31–32`, `qa/events.py:36–38`, `:51`. Do a check of each one.

### 11. §3.1: short forms in names

Only old-pipeline items are open.

- Statistical quantities with a short name (§3.1 says: name it after what it is): `obs` and `pred` in `features/chain.py:112`.
- Other short words: `ok` in `features/engine.py:437`, `:461` and `features/chain.py:145`; `avg`, `opp`, `src` and `dst` in `features/engine.py`; `agg` in `scrapers/detail.py:60` and `scrapers/detail_parsers.py:210`; `tr`, `nums`, `pcts`, `vals` and `bar` in `scrapers/detail_parsers.py`; `idx` in `qa/league.py:128`.
- Missed by group 4 and group 6: `lo` and `hi` in `features/goals.py:60` (`BUCKETS`), and `sgf` and `sga` in `scrapers/detail_parsers.py:238` (`aggregate_h2h`).

### 13. §8: a check of what a contract already makes sure of (4)

- `s1_stage.fillna("")` in `analysis/corpus.py:59`, `analysis/schedule/whole_corpus/all/prematch_screen.py:240`, `:263` and `season_phase.py:39`. These tables come from `features/stage_io.py:read_stage_csv`, which keeps an empty `s1_stage` as `""` (`features/CLAUDE.md` §0).

### 14. §6 and §7: other items

Only old-pipeline items are open.

- A nested comprehension: `features/history.py:177` (`_timelines`).
- A lambda with a long body: `qa/league.py:186`. Fix: a named function.

---

## Order

1. New-pipeline Musts: group 3 (all items). Then `/check` and `/stats-review`. Group 10 after the user's decision.
2. New-pipeline Defaults: groups 7 and 13, file by file. Groups 8, 11 and 14 have no new-pipeline items left.
3. Old-pipeline items: with P4–P5, or in a clean-up pass of their own.
