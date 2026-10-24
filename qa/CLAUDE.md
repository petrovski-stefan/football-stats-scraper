# qa/ — corpus validation

## 1. The validate command

`uv run python -m qa.validate` checks internal self-consistency of the staged files in `data/finished/` and **exits non-zero on any failure**. `--archived` runs the old pipeline's checks instead, on the files archived in `data/archived/` on 2026-10-10 (base, detail, joins, the goal and event stores); use it when refactoring those sources. Its one cross-source check is the page's final table against our rebuilt standings (§5).

## 2. Don't soften the canary

Do not soften the canary in `qa/` to make the run green. A failure is a finding about the data, not a bug in the check.

## 3. The archive's exit-1 (`--archived`): friendly tournaments in the event store

It is a real finding rather than a stale one. **2 of 1,395 matches (0.14%) show 9-10 substitutions by one side**, which is impossible in competitive football. Both are pre-season friendly tournaments — `Germany Liga Total Cup` and `Emirates Cup` — that `domain/scope.py:FRIENDLY_MARKER` misses because neither name contains "friendly".

The threshold is calibrated to permit a legitimate 6th substitution (the concussion protocol; match 2789190 is a real EPL example), so only genuine contamination trips it.

**Fixing it means deciding how such matches are excluded, which is a corpus-definition call, not a code change.** Don't patch the threshold or the marker without that decision from the user.

## 4. Goals have an oracle; events do not

**Goals: the half-time score is a free oracle.** `qa/goals.py` reconciles all goals against the stored full-time score _and_ goals with `minute <= 45` against the stored half-time score. The second check is what tests the minute rather than the count: mishandle stoppage and a 45+3' goal lands in the second half, and the check fails loudly on every such match. `minute` and `stoppage` are stored separately for exactly this reason (45 and 3, never 48). History matches from other competitions have no stored score, so only the internal checks apply to them; that asymmetry is reported, not hidden.

**Events: `qa/events.py` has no free oracle.** Nothing in the corpus independently counts cards. So it checks structure (ranges, kinds, contiguous index, ordering, at most six substitutions per side) plus wide per-match rate bands, and says so rather than implying the same guarantee `qa/goals.py` gets from the half-time score.

## 5a. The staged schedule file (`qa/schedule.py`, 2026-10-07)

Each `data/finished/1_raw/` schedule gets its own report:

- the universal checks: rows, the declared columns, a unique `match_id`, no dead column except `s1_stage`;
- HT goals ≤ FT goals, the odds (`qa/odds.py`), kickoffs inside the season's years, no team twice within 24 h;
- **the season's shape.** Every kept "League" stage is a k-fold round robin, so each round must hold floor(teams ÷ 2) matches, no team may play twice in one round, and every pair of teams must meet equally often. A missed or doubled match fails the size and pair checks, and so does a real event like a team withdrawn mid-season. The once-per-round check catches a page whose rounds are only labels: there about one match in twelve is filed under a neighbouring round, although every round's size is right. The standings stay right on such a page (they are rebuilt by kickoff time); anything that reads `s1_round` as a real round does not.

**`qa/odds.py` holds the odds checks once, for any table given its column names**: the old base files (`qa/league.py:BASE_ODDS`) and the staged ones (`qa/schedule.py:STAGED_ODDS`) both call it.

- `odds.check_goal_line_above_handicap` (the user, 2026-10-08) fails any row whose O/U line is not above the AH line's size. The page itself can carry that error (seen on 6 and 19 Oct 2024: an opening O/U line equal to the AH line's size), a re-scrape does not change page values, and the range check sees it only when the line is below 1.5.
- **The largest line a row may carry depends on its 1X2 favourite's price** (`odds.LINE_LIMITS`, the user's call, 2026-10-10): fixed limits (a 4-goal handicap, a 5.5 total) failed real mismatches, where a 1.01–1.04 favourite carries a 4.25–6 handicap and a total up to 7, and they let a 3.5 handicap on a 1.60 favourite pass.
- The overround checks flag a row whose O/U and AH cells repeat its 1X2 prices, or the reverse: a scraper bug fixed on 2026-10-08 (`scrapers/schedule.py:drop_stale_odds`), so such a row means a file scraped before that day.

## 5b. Odds coverage, the derived stages and the corpus (2026-10-11)

Added at the user's request after the odds-coverage analysis of 2026-10-10.

- **In the stage-1 report:** every market is all or nothing (`odds.check_whole_markets`); at least `odds.COVERAGE_FLOOR` (99%) of a league-season's matches carry all three markets (`odds.check_coverage`); and no round of `schedule.BLANK_ROUND_MIN_MATCHES` (2) or more matches lacks odds on every match. One unpriced match is the bookmaker's choice (an awarded match passes the floor); a blank round is a page that did not show its odds when it was read.
- **The stage-2 and stage-3 reports** (`qa/stages.py`): each file holds exactly stage 1's matches, every earlier stage's columns carry over unchanged, and stage 2's `s2_has_*` flags and odds values agree with the stage-1 cells, the three 1X2 probabilities summing to 1. Stage 3's round-so-far counts (S3.14–20) keep the rules between them (`stages.check_round_fields`): a rare event is a comeback or a 7+ match counted once, fewer round-mates finished than the round holds, both teams scored in every comeback, and the two averages are empty together. **A stage file built before a re-scrape fails here: rebuild stages 2 and 3.** Floats compare within `stages.TOLERANCE`, because a CSV round trip moves some long floats by their last digit.
- **The corpus report:** no match id in two league-seasons, every league-season's league in `config/leagues.json` (`domain/paths.py:LEAGUES_FILE`), and no stage-2 or stage-3 file without its stage-1 file. Files left behind by a removed league would still be read: the config check guards the stage-1 files, the orphan check the derived ones. A missing config fails, since the leagues then go unchecked.

## 5. The page's final table checks our rebuilt standings

The standings the analysis uses are rebuilt from stored results at each kickoff (`features/schedule_multi.py`; the user's decision, 2026-10-06), so `qa/final_table.py` is the only thing that holds them against the site. For every staged schedule (`data/finished/1_raw/`) it rebuilds each stage's table from all its stored results and compares every team's P, W, D, L, GD and PTS with the page's final table, read once per stage by the scraper. Rank only has to fall inside the block of positions the teams level on points share: the page breaks a tie on points by its league's rule (head-to-head in Spain, Portugal, Italy and Poland, most wins in Belgium), ours by goal difference and goals for. The user accepted that difference on 2026-10-07, since every count stays exact.

A deduction confirmed in public reports is declared in `domain/deductions.py` (details in `notes/REFERENCE/POINTS_DEDUCTIONS.md`) and added to the rebuilt points before comparing; where the page's table applies less than the official total, `deductions.PAGE_TOTALS` holds the page's figure and the check uses it. Stage 3 itself keeps the points earned on the pitch (option A, the user, 2026-10-07). Any other failure is a data finding (§2): an undeclared points deduction, a missed match, a wrong score, a match the page's table leaves out (an abandoned or awarded one), or a league whose points carry into a later stage before its carry-over rule exists. A missing final table fails too, because the rebuild is then unchecked. What was decided is in `notes/LOG/MIGRATIONS.md` (2026-10-07); the deductions still open (exact dates, option C) are in `notes/REFERENCE/POINTS_DEDUCTIONS.md`.
