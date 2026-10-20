# Fields — one doc per stage

**Group: FIELDS.** One row per field. Never change a field code. The stage-1 docs are frozen after plan step P7.

**Split from the old `notes/FIELDS.md` on 2026-10-05** (that file was deleted on 2026-10-14) (step P1 of
`notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md`). The stages, their rules and the decisions behind them
are in that plan, §1–3; they are not repeated here.

**Progress: stage-1 fields checked on the page 36 / 98** (schedule 36 / 36, done; detail 0 / 38; live 0 / 24) **· page candidates decided 5 / 22** (C1–C4, C8)

## The docs

| doc | describes | answers | checked by |
|---|---|---|---|
| `SCHEDULE_1_RAW.md` | league page → match file + standings file | where is it on the page? | the user, on the page |
| `SCHEDULE_2_ROW.md` | fields from one match row | what formula on this row? | Claude; the user skims |
| `SCHEDULE_3_MULTI.md` | fields from other rows: round position, pre-kickoff table, survey flags | which rows, all before kickoff? | Claude + stats-reviewer |
| `DETAIL_1_RAW.md` | h2h page → match file + history file | where is it on the page? | the user, on the page |
| `DETAIL_2_ROW.md` | fields from one detail row or one history row | what formula on this row? | Claude; the user skims |
| `DETAIL_3_MULTI.md` | the history windows, form and h2h averages | which rows, all before kickoff? | Claude + stats-reviewer |
| `LIVE_1_RAW.md` | live page → goal and event stores (unchanged for now) | where is it on the page? | the user, on the page |
| `LIVE_3_MULTI.md` | goal-timing and card aggregates (as today) | which rows, all before kickoff? | Claude + stats-reviewer |
| `ANALYSIS_FEATURES.md` | the engine's model features (not stored) | which exist, which are alive? | — |

Analysis reads only stage 3: the schedule's, or the schedule's joined to the detail's (and the
live aggregates) by `match_id`.

## How to read a row

- **Field ids:** source letter + stage + row. `S1.07` = schedule, stage 1, row 7. `D` = detail,
  `L` = live page. One row per field; a field is defined once.
- **Names** carry the doc's code (rule 2 below). Today's name in the files is the name without
  its code, unless the status says `today ...`.
- **Example:** the value on the reference match below.
- **Timing — the user's rule (2026-10-05):** in every row, only the match's own score is after
  kickoff. That means the HT and FT goals and every field computed from them. Everything else in
  the row must be known before kickoff; a field that is not is replaced or dropped. The match's
  own events, statistics and in-play odds never go into its own row; they feed later matches'
  history, where they are `before`. The column says `before` or `after`.
- **Role — one or more (the user, 2026-10-05):** `key` identifies a row or links it to another
  file; `input` may be used to predict, and only `before` fields can be inputs; `label` is an
  outcome of this match, never an input for its own match; `check` is read by a data-quality
  test (open for discussion).
- **✓** = the user checked it on the page. Stage-1 fields only.
- **Status:** `keep`, `drop`, `rename → new_name`, `add`, `fix`. A `?` marks Claude's proposal,
  decided in P2. **Bold** marks a problem found while drafting.

## Rules for values

1. **Every date and time is stored in Berlin time, with its offset** (the user, 2026-10-05; it
   replaces the same day's "store UTC"). Berlin time is the clock in Berlin: UTC+1 in winter,
   UTC+2 in summer. The offset is written in the value, so the time is exact across the clock
   change: `2026-01-31 18:30+01:00`, `2025-08-15 21:00+02:00`. The league page gives UTC+8 (China
   time) and the h2h page gives UTC; the scraper converts both. **The league page's dates were
   stored as UTC+8 in every file so far**: see `SCHEDULE_1_RAW.md` S1.07.
2. **Decided by the user, 2026-10-06:**
   - typed values only: no score strings beside the goal columns;
   - odds as `odds_<market>_<snapshot>_<selection>`, snapshot `open` (the page's "Initial") or
     `close` (the page's "Live"), stored as decimal odds. What the snapshots are (the user,
     2026-10-10):
     - **Initial** (`open`): the first price the bookmaker publishes for the match, usually about
       7 days before kickoff (more or fewer by league, country and competition). nowgoal keeps it
       as a snapshot that never changes, on the schedule and the h2h page alike. **Every odd on the
       schedule page is Bet365's Initial**, finished or scheduled match, all three markets;
     - **Live** (`close`, h2h page only): the price as it moves before kickoff. For a finished
       match that is the last pre-kickoff price, the closing price. For a scheduled match it is
       the price at the moment of reading, so it needs that moment stored beside it;
     - **In-Play**: the price during the match, moving with the score, the clock and events. It
       is after kickoff, so it is never stored as a field of its own match;
   - no rounding in stored data; round only in reports;
   - **every column name starts with the code of the doc that defines it:** source letter (`s`
     schedule, `d` detail, `l` live page) + stage number + `_`. Examples: `s1_date`,
     `s2_is_comeback`, `s3_match_index_in_round`, `d3_h2h_played`, `l3_home_late_goal_rate`. The
     code stays the same in later stage files. **Bare names:** only the columns that identify a
     row in their own file: `match_id` in the match files; `for_match_id`, `section`, `n` in the
     history file; `season`, `league_id`, `stage`, `round`, `half`, `venue`, `team_id` in the
     standings file. The goal and event stores keep their names until their redesign (plan Q4).
     A test checks that every column has a code or is a listed key.
3. **Deferred by the user, 2026-10-06 — one name per fact.** Duplicates stay for now (S1.16–18 =
   D1.03–05); the user reviews them later.
4. **Decided by the user, 2026-10-06 — a value known only after kickoff never has a name that
   reads like a pre-match value.** The positions problem behind it is solved: the standings are
   rebuilt at each kickoff (`SCHEDULE_3_MULTI.md` §B), and the page's table is a check only.

## Reference match

2789361, Chelsea v West Ham, English Premier League 2025-26, round 24: 0-2 at HT, 3-2 at FT, a
red card, quarter lines (AH 1.25, O/U 3.25).

- League page: <https://football.nowgoal50.com/league/2025-2026/36> (round 24). nowgoal often moves to a new domain; the paths stay the same (`scrapers/CLAUDE.md`).
- Detail page: <https://live.nowgoal50.com/match/h2h-2789361>
- Live page: <https://live.nowgoal50.com/match/live-2789361>

## Across all pages

**The comeback's own price (HT/FT odds) is on none of the 3 pages.** Another page type would
need the user's go and a robots.txt check. The closest is the first-half odds (C22,
`LIVE_1_RAW.md`): the market's price for the half-time state.
