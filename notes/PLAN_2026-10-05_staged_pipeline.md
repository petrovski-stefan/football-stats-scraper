# PLAN — the staged pipeline (the data refactor)

**Agreed with the user on 2026-10-05. Not started.**

**Why:** the user's goal is to cut the cognitive load of the field work and to understand what
every field means, clearly. Each stage gets its own fields doc, and each doc answers one
question. More CSV files is an accepted cost.

**Supersedes:**
- `notes/IDEAS_2026-10-01.md` Phase A1 steps 2–4 (14b layout, 2 refactor, 17 dictionary). The
  plan takes 16's naming and format rules.
- the class split in `notes/FIELDS.md` (raw / scrape-derived / derived). Its rows, page
  locations, examples and the user's S1 checks carry over (step P1).

---

## 1. The stages

Each source (schedule, then detail) goes through the same three stages:

| stage | reads | adds | the doc answers | checked by |
|---|---|---|---|---|
| 1 raw | the page | values read from the page, parsed only | where is it on the page? | the user, on the page |
| 2 row | stage 1, one row at a time | fields computed from that row alone | what formula on this row? | Claude; the user skims |
| 3 multi | stage 2, plus other rows and other files | fields that need other rows | which rows does it read, and are they all before kickoff? | Claude + stats-reviewer |

**Rules:**

1. **Stage 1 only parses: one page value in, one typed value out.** Allowed: `"0-2"` → two
   ints, `"2.5/3"` → 2.75, UTC+8 → UTC, a page name → a slug. Anything that reads a second value
   is not stage 1. The score strings are dropped: they repeat the goal ints.
2. **Stage 2 reads only its own row.** A stage-2 field's timing is the latest timing of its
   inputs, so a field built from a post-kickoff input is `after` by construction.
3. **Every stage-3 field states its row window:** which rows it reads, and that all of them
   kicked off before this match. This line is the leakage guard. Cross-row leakage can only
   enter at stage 3; same-row leakage (a value only known after kickoff) is caught by stage 1's
   timing column.
4. **Each stage file is the previous file plus new columns.** Each doc lists only its new
   columns.
5. **Only stage 1 is scraper output.** Stages 2 and 3 are rebuilt from stage 1 at any time, so
   only a stage-1 change forces a re-scrape. The big CONFIRM scrape waits for the stage-1 docs
   to freeze, not for stages 2–3.

**Analysis input:** schedule stage 3 alone, or schedule stage 3 joined to detail stage 3 by
`match_id` (the labels live in the schedule file), optionally with the goal and event
aggregates. The join adds no fields, so it has no doc.

## 2. Layout

`data/` gets one parent directory per match state (the user, 2026-10-05):

- `data/finished/` — all work now. Played matches only.
  - `1_raw/` — scraper output only:
    - `<league>_<season>_schedule.csv` — one row per finished match;
    - `<league>_<season>_final_table.csv` — the page's final FT / Total table, one row per team,
      read once as a check against our rebuilt table (`notes/fields/schedule_1_raw.md` §B;
      replaced the per-round standings file on 2026-10-06);
    - `<league>_<season>_detail.csv` — one row per match, the page's match-level values
      (~16 columns);
    - `<league>_<season>_history.csv` — one row per history row the page shows: `for_match_id`,
      `section` (home / away / h2h), `n` (1 = most recent), then the history match's own
      `match_id`, `league_id`, `date`, `league`, `home_team_id`, `away_team_id`,
      `home_team_name`, `away_team_name`, HT and FT goals, 1X2 odds, corners FT and HT. Up to
      20 rows per section (2789361 has 20 h2h rows), so up to ~60 per match;
    - `goals.csv`, `events.csv` and their done logs — unchanged for now (Q4).
  - `2_row/` and `3_multi/` — the derived files, same names.
- `data/scheduled/` (or `unplayed/`) — later: upcoming matches, same three stages.
- `data/predictions/` — later, maybe.

Paths are built only in `domain/paths.py`, so the names can change cheaply.

## 3. Decisions, 2026-10-05

- **The three stages and one doc per stage:** the user's design.
- **Q1, unplayed rows:** answered by the layout. `data/finished/` holds played matches only.
  Consequence (Claude's to handle): `match_index_in_round` and `matches_in_round` count finished
  matches only. In a completed season that is every match but the cancelled ones; a postponed
  match counts once played. A QA check flags any round with fewer than teams ÷ 2 matches.
- **Q2, standings: their own raw file** (Claude's recommendation, accepted). **Superseded
  2026-10-06:** the user chose to rebuild the standings from our own results at each kickoff (the
  2 h 30 min rule, `notes/fields/schedule_3_multi.md` §B), and to read only the page's final table
  as a check. The paragraph below is kept as history. The round X−1
  shift and its guard (`notes/FIELDS.md` D11) become a stage-3 step. The page clicks are the
  same either way; idea 19's table check reads the file directly, points included.
- **Q3, history rows: long format, every row the page shows** (Claude's recommendation,
  accepted). The form and h2h averages (today over up to 10 rows, while 6 are stored) become
  rebuildable, and the window becomes a stage-3 setting. Storing both team ids replaces the
  majority-vote subject guess (`scrapers/detail_parsers.py:subject_team_id`) behind `is_home`,
  `opponent` and `result`. Stage 3 turns the history back into one row per match: the
  averages, plus only the slots analysis uses. The column names change under 16's rules.
- **History windows (the user, later on 2026-10-05):** each team's last 5 or 6 matches; head
  to head at most 4, each played no earlier than 2 years before this match. These are
  stage-3 settings: stage 1 still stores every row the page shows. Two reasons: the 2-year cut
  compares the history date with this match's date, which rule 1 keeps out of stage 1; and a
  cut made at scrape time can only change with a re-scrape, while the stored rows add no
  columns and no page loads. Claude's defaults, each a one-line change with no re-scrape:
  - team window **6, locked by the user**. It applies to the per-match slots and to the form
    averages, which today use 10 rows;
  - "2 years" = the kickoff date minus 2 calendar years, inclusive (2026-01-31 → 2024-01-31);
  - head to head over all competitions the page lists, as today;
  - fewer qualifying matches → fewer rows; none → the h2h fields are empty, not zero.
- **Times: Berlin time, with the offset in every value** (the user, later on 2026-10-05; it
  replaces the same day's "store UTC"). `2026-01-31 18:30+01:00` in winter, `+02:00` in summer.
  Found the same day: the league page's `data-t` is UTC+8 and was stored unconverted in every
  schedule file, while the h2h page's history dates are UTC. Verified on 2789361 and on
  Liverpool v Bournemouth (Friday 15 Aug 2025, 20:00 UK, stored `2025-08-16 03:00`).
  - Wrong as a result: the weekday flags (`day_of_week`, `is_monday`, `is_midweek`): the stored
    weekday differs from the Berlin weekday in 41% of EPL 2025-26 rows, 60–63% of the Algerian,
    77% of the Moroccan and 0–2% of the Tunisian rows. Morocco 2024-25 stores 55 Mondays; 7 are
    Mondays in Berlin time. Also anything comparing a schedule date with a history date
    (`features/engine.py` congestion features: `days_since_last`, `matches_14d`).
  - Not affected: anything comparing dates inside one schedule file (round order, the 2 h 30 min
    and out-of-round rules), because every row there carries the same 8-hour shift.
- **Value rules, 2026-10-06** (`notes/fields/README.md`, "Rules for values"): typed values, the
  odds naming, no rounding and the doc-code prefix (`s1_`, `d3_`, …; row keys bare) are decided.
  One name per fact is deferred: duplicates stay until the user reviews them. Positions must
  mean the placement before the match: the user reviews that by hand (`schedule_3_multi.md` §B).
- **Q4, goals and events: unchanged for now.** They already fit stage 1, apart from three
  columns kept as documented exceptions (`goal_index`, goal `side`, the copied `league_id`).
  Their three docs come after schedule and detail, ~0.5 day.

## 4. Where today's 619 columns go

Counted from `domain/columns.py` and the EPL 2025-26 files on 2026-10-05: schedule 58, detail
537 (51 + 18 history slots × 27), goals 9 + 3, events 9 + 3.

**Stage 1 (365 today):**
- schedule (28): `season`, `league_id` (config URL); `league_name`, `stage`, `round`,
  `match_id`, `date`, `{home,away}_team_id`, `{home,away}_team_name`; `ht_score`, `ft_score`,
  `ht_{home,away}_goals`, `ft_{home,away}_goals`; the 1X2, O/U and AH odds (9);
  `{home,away}_team_position` (move to the standings file);
- detail (16): `match_id`, `odds_bookmaker`, `odds1x2_init_*` (3), `odds1x2_live_*` (3),
  `strength_*` (2), `h2h_compare_*_pct` (2), `guess_*_pct` (2), `*_next_fixture_days` (2);
- history slot (17 × 18): `match_id`, `league_id`, `date`, `league`, `ht_score`, `ft_score`,
  HT/FT goals (4), `odds_{home,draw,away}`, `corners_{ft,ht}_{home,away}` (4). Becomes one row of
  the history file, plus the two team ids and names it lacks today;
- goals (6), events (7), done logs' `match_id` (2). Bookkeeping: `scraped_at` (2).

**Stage 2 (158 today):**
- schedule (28): `total_goals`, `goals_1h`, `goals_2h`, `{home,away}_2h_goals`; `ht_result`,
  `ft_result`, `ht_ft_combo`; `is_comeback*` (3), `btts`, `over_25`,
  `is_seven_or_more_goals`; `day_of_week`, `is_monday`, `is_midweek`; `has_odds`,
  `has_ou_odds`, `has_ah_odds`, `implied_prob_*` (2), `implied_over`, `implied_ah_home`,
  `favorite`, `favorite_odds`, `underdog_odds`; `position_gap` (post-round inputs, so `after`:
  dropped; the pre-kickoff gap is stage 3);
- detail (4): `implied_{init,live}_{home,away}`;
- history slot (7 × 18): `total_goals`, `ht_result`, `ft_result`, `over_25`, `btts`,
  `is_comeback`, `corners_total`.
- Labels of other markets wait for their market (comebacks first).

**Stage 3 (94 today):**
- schedule (2): `match_index_in_round`, `matches_in_round`;
- detail (31): `{home,away}_recent_*` (12 each), `h2h_*` (7);
- history slot (3 × 18): `is_home`, `opponent`, `result`;
- goals (3): `goal_index`, `side`, `league_id`; events (2): `event_index`, `league_id`; done
  logs (2): `n_goals`, `n_events` — the documented exceptions of Q4, left in stage 1 for now.
- New, from `notes/FIELDS.md`: the pre-kickoff table (rebuilt from our results, S3.03), rest days
  (D13), the survey's flags (K6). `ht_decisive` (K2) is new too, but single-row: stage 2.

## 5. Steps — one at a time

| step | what | who | size |
|---|---|---|---|
| P1 | **Done 2026-10-05.** Split `notes/FIELDS.md` into `notes/fields/`: an index, schedule × 3, detail × 3, live × 2 (as today) and the engine features. The S1 checks carried over: #1–11 to S1.01–11, #12–13 to S3.01–02. FIELDS.md is marked superseded, kept until the user confirms | Claude | 2–3 h |
| P2 | The user's on-page check of the stage-1 docs, ≤ 20 fields a sitting. Decide which page candidates (FIELDS C1–C22) join stage 1, comebacks only | user + Claude | ~3 sittings |
| P3 | **Code done 2026-10-06.** Schedule: stage-1 scraper (raw values plus the page's final table as a check), stage-2 and stage-3 builders (standings rebuilt at each kickoff). All 7 gates pass. Dry run on the old EPL file converted in memory: 380 rows valid, Chelsea v West Ham's pre-kickoff line as in the docs, rebuilt final table equal to the page's for all 20 teams. `domain/match.py` removed (`notes/MIGRATIONS.md` 2026-10-06). Left: the real EPL scrape (P6), with the user's go | Claude | ~1.5 days |
| P4 | Detail: stage-1 scraper (match-level + long history), stage-2 and stage-3 builders | Claude | ~2.5 days |
| P5 | The join; re-point `features/`, `modelling/`, `qa/` and the goal/event work lists (`scrapers/goals.py:history_ids` reads the history file) | Claude | ~0.5 day |
| P6 | Re-scrape EPL 2025-26 in the new format, then run every gate and self-check. **Schedule done 2026-10-07** (the user's go): 3 min, 380 matches, every match id, goal, odd and team name equal to the old file, all 380 kickoffs equal to the old UTC+8 text converted, all three odds markets present, and the table rebuilt from the new results equal to the page's final table for 20/20 teams. Stages 2 and 3 built. The final-table comparison is now an automatic QA check (`qa/final_table.py`, run by `qa.validate`; 2026-10-07). Detail and live: after P4 | Claude, with the user's go | ~1–2 h scrape |
| P7 | Freeze the stage-1 docs. With Phase S's other conditions, this unblocks the CONFIRM scrape | user | — |

P1 and P2 come first: the docs are the spec the code is written to.

## 6. Open points Claude handles (no user decision needed)

- The history rows' odds snapshot (Initial or Final?) — FIELDS #60–62, settle in P2.
- `corners_ht_*` are stored as floats (`3.0`) because of empty cells: store nullable ints.
- ~~When the page rebuilds `Round N` to include a postponed match~~ — answered 2026-10-06: `Round N`
  counts by round number, so the standings are now rebuilt from our own results instead
  (`notes/fields/schedule_3_multi.md` §B).
- The join: a loader function or a written file — decide in P5.
- **Weekday flags outside Europe, before the survey:** Berlin time puts a Sunday 21:00 kickoff in
  Brazil (01:00 Berlin) on Monday. For European and North African leagues the Berlin weekday
  matches the local one except within an hour or two of midnight. Settle the weekday's timezone
  for the Americas and Asia at Phase S step 8, with survey claim #6.
- Module names and placement in the layer table; root `CLAUDE.md` (data paths, "only scrapers
  write `data/raw/`") and `notes/MIGRATIONS.md` are updated in the steps that change them.
