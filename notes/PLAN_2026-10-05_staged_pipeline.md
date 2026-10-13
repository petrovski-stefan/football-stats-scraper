# PLAN — the staged pipeline (the data refactor)

**Agreed with the user on 2026-10-05. In progress.** What is done is recorded in
`notes/MIGRATIONS.md` (2026-10-05 to 2026-10-10) and deleted here (the user's rule, 2026-10-10),
so this file holds only open work.

**Why:** the user's goal is to cut the cognitive load of the field work and to understand what
every field means, clearly. Each stage gets its own fields doc, and each doc answers one
question. More CSV files is an accepted cost.

**Supersedes:**
- `notes/IDEAS_2026-10-01.md` ideas 14b (layout), 2 (refactor) and 17 (dictionary). It took
  16's naming and format rules, now "Rules for values" in `notes/fields/README.md`. Since
  2026-10-13 the IDEAS file groups its open steps by page: ideas 2a (detail) and 2b (live).
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

`data/` has one parent directory per match state (the user, 2026-10-05). Still to add (the
schedule's files are in place):

- `data/finished/` — played matches only.
  - `1_raw/` — scraper output only:
    - `<country>_<league>_<season>_detail.csv` — one row per match, the page's match-level values
      (~16 columns);
    - `<country>_<league>_<season>_history.csv` — one row per history row the page shows: `for_match_id`,
      `section` (home / away / h2h), `n` (1 = most recent), then the history match's own
      `match_id`, `league_id`, `date`, `league`, `home_team_id`, `away_team_id`,
      `home_team_name`, `away_team_name`, HT and FT goals, 1X2 odds, corners FT and HT. Up to
      20 rows per section (2789361 has 20 h2h rows), so up to ~60 per match;
    - `goals.csv`, `events.csv` and their done logs — unchanged for now (Q4).
  - `2_row/` and `3_multi/` — the derived detail files, same names.
- `data/scheduled/` (or `unplayed/`) — later: upcoming matches, same three stages.
- `data/predictions/` — later, maybe.

Paths are built only in `domain/paths.py`, so the names can change cheaply.

## 3. Decisions, 2026-10-05

- **The three stages and one doc per stage:** the user's design.
- **Q3, history rows: long format, every row the page shows** (Claude's recommendation,
  accepted). The form and h2h averages (today over up to 10 rows, while 6 are stored) become
  rebuildable, and the window becomes a stage-3 setting. Storing both team ids replaces the
  majority-vote subject guess (`scrapers/detail_parsers.py:subject_team_id`) behind `is_home`,
  `opponent` and `result`. Stage 3 turns the history back into one row per match: the
  averages, plus only the slots analysis uses. The column names change under the value rules (`notes/fields/README.md`).
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
- **Q4, goals and events: unchanged for now.** They already fit stage 1, apart from three
  columns kept as documented exceptions (`goal_index`, goal `side`, the copied `league_id`).
  Their three docs come after schedule and detail, ~0.5 day.

## 4. Where the detail, goal and event columns go

Counted from `domain/columns.py` and the EPL 2025-26 files on 2026-10-05: detail 537 (51 + 18
history slots × 27), goals 9 + 3, events 9 + 3.

**Stage 1:**
- detail (16): `match_id`, `odds_bookmaker`, `odds1x2_init_*` (3), `odds1x2_live_*` (3),
  `strength_*` (2), `h2h_compare_*_pct` (2), `guess_*_pct` (2), `*_next_fixture_days` (2);
- history slot (17 × 18): `match_id`, `league_id`, `date`, `league`, `ht_score`, `ft_score`,
  HT/FT goals (4), `odds_{home,draw,away}`, `corners_{ft,ht}_{home,away}` (4). Becomes one row of
  the history file, plus the two team ids and names it lacks today;
- goals (6), events (7), done logs' `match_id` (2). Bookkeeping: `scraped_at` (2).

**Stage 2:**
- detail (4): `implied_{init,live}_{home,away}`;
- history slot (7 × 18): `total_goals`, `ht_result`, `ft_result`, `over_25`, `btts`,
  `is_comeback`, `corners_total`.
- Labels of other markets wait for their market (comebacks first).

**Stage 3:**
- detail (31): `{home,away}_recent_*` (12 each), `h2h_*` (7);
- history slot (3 × 18): `is_home`, `opponent`, `result`;
- goals (3): `goal_index`, `side`, `league_id`; events (2): `event_index`, `league_id`; done
  logs (2): `n_goals`, `n_events` — the documented exceptions of Q4, left in stage 1 for now.
- New, from `notes/FIELDS.md`: rest days (D13, now `notes/fields/detail_3_multi.md` D3.24) and the
  survey's flags (K6).

## 5. Steps — one at a time

| step | what | who | size |
|---|---|---|---|
| P2 | The user's on-page check of the detail and live stage-1 docs, ≤ 20 fields a sitting (progress in `notes/fields/README.md`). Decide which of the remaining page candidates (C5–C7, C9–C22) join stage 1, comebacks only | user + Claude | ~4 sittings |
| P4 | Detail: stage-1 scraper (match-level + long history), stage-2 and stage-3 builders. Stage 2 of the history file carries a read-only `d2_is_friendly` per history row (the user, 2026-10-10), from `domain/scope.py:is_friendly`; tournament friendlies without "friendly" in their name slip through (`qa/CLAUDE.md` §3) | Claude | ~2.5 days |
| P5 | The join; re-point `features/`, `modelling/`, `qa/` and the goal/event work lists (`scrapers/goals.py:history_ids` reads the history file) | Claude | ~0.5 day |
| P6 | Re-scrape in the new format: detail and live, after P4. Then run every gate and self-check | Claude, with the user's go | detail ≈ 36k pages (36,238 matches, 2026-10-13), ~18 h at the one measured rate (`notes/PLAN_2026-07-25_environment_filter.md` Phase 1) |
| P7 | Freeze the stage-1 docs. With Phase S's other conditions, this unblocks the CONFIRM scrape | user | — |

P2 comes before P4: the docs are the spec the code is written to.

## 6. Open points Claude handles (no user decision needed)

- The history rows' odds snapshot (Initial or Final?) — FIELDS #60–62, settle in P2.
- `corners_ht_*` are stored as floats (`3.0`) because of empty cells: store nullable ints.
- The join: a loader function or a written file — decide in P5.
- **Weekday flags outside Europe, before the survey:** Berlin time puts a Sunday 21:00 kickoff in
  Brazil (01:00 Berlin) on Monday. Measured 2026-10-11 (kickoff times only): the Berlin day
  differs from the local day for 2,639 of 4,808 matches in the Americas (55%) and for none in
  Europe or Asia. The decision is listed in `notes/IDEAS_2026-10-01.md` idea 13.
- Module names and placement in the layer table; root `CLAUDE.md` (data paths, "only scrapers
  write `data/raw/`") and `notes/MIGRATIONS.md` are updated in the steps that change them.
