# qa/ — corpus validation

## 1. The validate command

`uv run python -m qa.validate` checks internal self-consistency and **exits non-zero on any failure**. Its one cross-source check is the page's final table against our rebuilt standings (§5); the football-data.co.uk check was retired (see `notes/MIGRATIONS.md`).

## 2. Don't soften the canary

Do not soften the canary in `qa/` to make the run green. A failure is a finding about the data, not a bug in the check.

## 3. The current exit-1: friendly tournaments in the event store

It is a real finding rather than a stale one. **2 of 1,395 matches (0.14%) show 9-10 substitutions by one side**, which is impossible in competitive football. Both are pre-season friendly tournaments — `Germany Liga Total Cup` and `Emirates Cup` — that `domain/scope.py:FRIENDLY_MARKER` misses because neither name contains "friendly".

The threshold is calibrated to permit a legitimate 6th substitution (the concussion protocol; match 2789190 is a real EPL example), so only genuine contamination trips it.

**Fixing it means deciding how such matches are excluded, which is a corpus-definition call, not a code change.** Don't patch the threshold or the marker without that decision from the user.

## 4. Goals have an oracle; events do not

**Goals: the half-time score is a free oracle.** `qa/goals.py` reconciles all goals against the stored full-time score _and_ goals with `minute <= 45` against the stored half-time score. The second check is what tests the minute rather than the count: mishandle stoppage and a 45+3' goal lands in the second half, and the check fails loudly on every such match. `minute` and `stoppage` are stored separately for exactly this reason (45 and 3, never 48). History matches from other competitions have no stored score, so only the internal checks apply to them; that asymmetry is reported, not hidden.

**Events: `qa/events.py` has no free oracle.** Nothing in the corpus independently counts cards. So it checks structure (ranges, kinds, contiguous index, ordering, at most six substitutions per side) plus wide per-match rate bands, and says so rather than implying the same guarantee `qa/goals.py` gets from the half-time score.

## 5. The page's final table checks our rebuilt standings

The standings the analysis uses are rebuilt from stored results at each kickoff (`features/schedule_multi.py`; the user's decision, 2026-10-06), so `qa/final_table.py` is the only thing that holds them against the site. For every staged schedule (`data/finished/1_raw/`) it rebuilds each stage's table from all its stored results and compares every team's P, W, D, L, GD and PTS with the page's final table, read once per stage by the scraper. Rank only has to fall inside the block of positions tied teams share: our table gives teams level on points, goal difference and goals for one rank, while the page breaks such ties its own way.

A failure is a data finding (§2): a points deduction, a missed match, a wrong score, or a league whose points carry into a later stage before its carry-over rule exists. A missing final table fails too, because the rebuild is then unchecked. EPL 2025-26 passed on 2026-10-07, 20/20 teams.
