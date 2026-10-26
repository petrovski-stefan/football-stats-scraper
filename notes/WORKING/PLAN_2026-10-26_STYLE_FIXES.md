# PLAN — the style fixes from the strict check of 2026-10-26

**Group: Working.** Edit it in place, and keep it current. Move done items to `notes/LOG/MIGRATIONS.md`.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

**Status: PARKED.** The user asked for this plan on 2026-10-26. No fix is made yet.

**Why:** a strict, read-only check of all `.py` files against `CODING_STYLE.md` found 9 groups of breaches. Groups 2–3 break a Must rule (`CODING_STYLE.md` §1). Groups 6–8 break a Default rule. Groups 1, 4, 5 and 9 and the §5 item are done (`notes/LOG/MIGRATIONS.md`, 2026-10-26).

**Scope:** about 80 % of the breaches are in the old pipeline. The old pipeline is `features/{engine,enrich,events,goals,history,chain}.py`, `scrapers/{detail,detail_parsers,goals,goal_parsers,event_parsers,live_rows,browser_pool}.py`, `domain/{match_detail,goal,event}.py` and `qa/{league,detail,goals,events}.py`. Root `CLAUDE.md` keeps it until the steps P4–P5 of `PLAN_2026-10-05_STAGED_PIPELINE.md`. `CODING_STYLE.md` §1 says: code that nobody changes stays as it is. Thus, fix an old-pipeline item when P4–P5 change its function, or in a clean-up pass of its own.

---

## Method and measurements

- The check read 165 files (22,604 lines) on 2026-10-26, at commit `3d8941e`.
- Three AST and token sweeps found the candidates. Claude read each flagged site by hand and removed the false positives.
- These rules had 0 breaches: a blank line after each docstring, a blank line before each final `return`, the `_df` suffix (the 16 flags were functions with the same name), `_private` names across modules, wildcard imports, `raise` without `from` in an `except`, bare `except`, `# type: ignore` without an error code, test names as sentences, named Hypothesis strategies, assert messages in loops.
- Some counts come from a heuristic. Each such count says so. Do a check of each site before you change it.

---

## Must rules

### 2. §10: errors

- `scrapers/detail.py:92` and `scrapers/goals.py:231` catch `Exception` around one job. The callers (`detail.py:126`, `goals.py:284`) log with `logger.warning`, so there is no traceback. The run does not exit non-zero at the end. §10 needs `logger.exception` and a non-zero exit (`scrapers/schedule.py:_run_job` is the model).
- `features/enrich.py:74` raises `RuntimeError`. `features/engine.py:317` raises `AssertionError`. Fix: a specific exception, for example `KeyError` or `ValueError`.

### 3. §9: a rule outside its home

- **7+:** `analysis/methods/yardstick.py:144` and `analysis/schedule/whole_corpus/all/prices.py:288` use `poisson.sf(6, …)`. Fix: `SEVEN_PLUS_GOALS - 1` from `domain/stats.py`. `yardstick.py` already imports it.
- **Times:** `analysis/schedule/whole_corpus/all/prematch_screen.py:257`, `round_clusters.py:156` and `season_phase.py:42` parse `s1_date` with `pd.to_datetime`. `ml/rows.py:139` and `features/schedule_multi.py:116` use `clock.parse_instant`. Fix: one way, through `domain/clock.py`.
- **Seconds per day:** `/ 86400` is in `features/engine.py:419`, `:426` and `features/schedule_multi.py:120`. Fix: one helper or constant in `domain/clock.py`.
- **Clock:** `scrapers/goals.py:236` uses `datetime.now(UTC)`. The project clock is `domain/clock.py` (Berlin time with its offset).
- **Comeback:** `features/chain.py:146–165` calculates "completed" by hand. Fix: use `domain/stats`.
- These items touch `features/` and `analysis/`, so `/stats-review` is due after the fix.

---

## Default rules

### 6. §3.1: names

- Cryptic names in `features/engine.py:377–395`: `ch`, `ca`, `gh`, `ga`, `subj_c`, `tot_c`, `subj_g`, `tot_g`, `ok`, `mine_c`, `mine_g`.
- `scrapers/detail.py:85` parameter `mid`: the project word is `match_id`.
- `features/engine.py:490`: the function name `col`.
- US spelling: `features/engine.py:693` `summarize`.
- 43 empty names (`out`, `result`, `values`, `value`, `items`) in functions of 15 or more lines. Examples: `scrapers/detail_parsers.py:290`, `analysis/units.py:300`, `:460`, `scrapers/driver.py:244`, `:384`.
- Boolean parameters that are not a yes/no question: `proportional`, `binary`, `luck`, `ok` (see group 7).

### 7. §4 and §8: function shape and contracts

- Positional bool parameters: `analysis/methods/yardstick.py:228` `frame(proportional)`, `prematch_screen.py:398` `standardised(binary)`, `analysis/units.py:173` `summary_row(luck)`, `features/events.py:204` `_score_line(is_home)`, `qa/report.py:18` `check(ok)`. Fix: keyword-only.
- Tuples of 3 or more unnamed values (16): `analysis/methods/shin.py:25` `shin_row` (4 floats), `per_league/rates.py:38` `quantity` (4 strs), `analysis/units.py:161` `repeat_test`, `:278` `within_test`, `:95` `tested`, `analysis/methods/yardstick.py:86` `fit_rates`, `scrapers/detail_parsers.py:395` `_row_1x2`, `scrapers/parsers.py:92` `_odds_cells`, `scrapers/detail.py:85` and `scrapers/goals.py:223` `_scrape_one`. Fix: a frozen dataclass.
- About 14 functions return `X | None`, and the docstring does not say what `None` means: `qa/goals.py:235` `second_half_share`, `scrapers/live_rows.py:63` `content_cell`, `:102` `_minute_index`, `:112` `_side_of`, `scrapers/parsers.py:174` `attr`, `features/events.py:237` `_state_at`, `scrapers/detail_parsers.py:96` `_row_league_id`, `:121` `subject_team_id`, `:370` `_find_odds_table`, `:477` `_team_id`, `scrapers/detail.py:153` `_parse_limit`, `scrapers/goals.py:202` `_as_int`.
- Long argument lists: `scrapers/goals.py:239` `_store_rows` (8), `analysis/units.py:57` `unit_values` (7).
- Long function: `analysis/schedule/whole_corpus/all/odds_yardstick.py:148` `main` (101 lines).

### 8. §6: expressions and numbers

- 12 comprehensions with more than one `for`: `analysis/methods/yardstick.py:32`, `analysis/schedule/whole_corpus/all/odds_groups.py:29`, `:51`, `odds_yardstick.py:60`, `features/engine.py:141`, `:601`, `features/events.py:123`, `features/goals.py:59`, `features/history.py:98`, `qa/odds.py:82`, `scrapers/goals.py:114`, `:120`.
- Lambdas with logic: `scrapers/driver.py:188` (`any(...)`), `:356`, `:362` (`or`). Fix: a named function.
- Numbers in the code: `features/chain.py:70` has `1.72` and `1.27` next to its F11 constants; `features/chain.py:67` `60001`, `:106` `0.03`; `analysis/stats.py:136–166` `0.8`, `0.05`, `40`; `scrapers/goals.py:267` `depth=6` repeats `MATCHES_PER_SECTION`; `scrapers/detail_parsers.py:175` `[:6]`.
- Heuristic: about 35 module constants have no comment that gives the source of the value. Examples: `analysis/schedule/whole_corpus/all/stakes.py:26` `ALPHA`, `per_team/rates.py:38` and `per_team/odds_yardstick.py:63` `TOP = 20`, `scrapers/detail.py:40` and `scrapers/goals.py:64` `WORKERS = 3`, `ml/boosting.py:32–33` `FOLDS`, `MAX_TREES`. The sweep did not see a comment further up over a group of constants. Do a check of each one.

---

## Order

1. New-pipeline Musts: group 3 (all items). Then `/check` and `/stats-review`.
2. New-pipeline Defaults: groups 6–8, file by file.
3. Old-pipeline items: with P4–P5, or in a clean-up pass of their own.
