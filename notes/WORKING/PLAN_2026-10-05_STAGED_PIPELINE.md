# PLAN — the staged pipeline (the data refactor)

**Group: Working.** Edit it in place, and keep it current. Move done items to `notes/LOG/MIGRATIONS.md`.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

**Agreed with the user on 2026-10-05. In progress.** What is done goes into `notes/LOG/MIGRATIONS.md` (2026-10-05 to 2026-10-10), and is deleted here (the user's rule, 2026-10-10). So this file holds only open work.

**Why:** the user has two goals: less cognitive load in the field work, and a clear understanding of what each field means. Each stage gets its own fields doc. Each doc answers one question. More CSV files are an accepted cost.

**Supersedes:**
- `notes/WORKING/IDEAS_2026-10-01.md` ideas 14b (layout), 2 (refactor) and 17 (dictionary). This plan also took the naming and format rules of idea 16. They are now "Rules for values" in `notes/FIELDS/README.md`. Since 2026-10-13, the IDEAS file groups its open steps by page: ideas 2a (detail) and 2b (live).
- the class split in the old `notes/FIELDS.md` (raw / scrape-derived / derived; deleted on 2026-10-14). Its rows, page locations, examples and the user's S1 checks moved to the new docs (step P1).

---

## 1. The stages

Each source (the schedule, then the detail) goes through the same three stages:

| stage | reads | adds | the doc answers | checked by |
|---|---|---|---|---|
| 1 raw | the page | values read from the page, parsed only | where is it on the page? | the user, on the page |
| 2 row | stage 1, one row at a time | fields computed from that row alone | what formula on this row? | Claude; the user skims |
| 3 multi | stage 2, plus other rows and other files | fields that need other rows | which rows does it read, and are they all before kickoff? | Claude + stats-reviewer |

**Rules:**

1. **Stage 1 only parses: one page value in, one typed value out.** Examples of what is permitted: `"0-2"` → two ints, `"2.5/3"` → 2.75, UTC+8 → UTC, a page name → a slug. A step that reads a second value is not stage 1. The score strings are dropped, because they repeat the goal ints.
2. **Stage 2 reads only its own row.** The timing of a stage-2 field is the latest timing of its inputs. So a field built from a post-kickoff input is `after` by construction.
3. **Every stage-3 field states its row window:** which rows it reads, and that all of them kicked off before this match. This line is the leakage guard. Cross-row leakage can enter only at stage 3. The timing column of stage 1 catches same-row leakage (a value that is known only after kickoff).
4. **Each stage file is the previous file plus new columns.** Each doc lists only its new columns.
5. **Only stage 1 is scraper output.** Stages 2 and 3 can be rebuilt from stage 1 at any time. So only a change in stage 1 makes a re-scrape necessary. A scrape of new data for a confirmatory test (`notes/RECORD/PREREGISTRATION.md` A9.2–A9.3) waits until the stage-1 docs are frozen. It does not wait for stages 2–3.

**Analysis input:** schedule stage 3 alone, or schedule stage 3 joined to detail stage 3 by `match_id` (the labels are in the schedule file). The goal and event aggregates can be added. The join adds no fields, so it has no doc.

## 2. Layout

`data/` has one parent directory for each match state (the user, 2026-10-05). The schedule's files are in place. These are still to add:

- `data/finished/` — played matches only.
  - `1_raw/` — scraper output only:
    - `<country>_<league>_<season>_detail.csv` — one row per match, with the page's match-level values (~16 columns);
    - `<country>_<league>_<season>_history.csv` — one row for each history row that the page shows. The columns: `for_match_id`, `section` (home / away / h2h), `n` (1 = most recent), then the history match's own `match_id`, `league_id`, `date`, `league`, `home_team_id`, `away_team_id`, `home_team_name`, `away_team_name`, HT and FT goals, 1X2 odds, corners FT and HT. A section has up to 20 rows (2789361 has 20 h2h rows). So a match has up to ~60 rows;
    - `goals.csv`, `events.csv` and their done logs — unchanged for now (Q4).
  - `2_row/` and `3_multi/` — the derived detail files, with the same names.
- `data/scheduled/` (or `unplayed/`) — later: upcoming matches, with the same three stages.
- `data/predictions/` — later, possibly.

Only `domain/paths.py` builds paths. So the names are cheap to change.

## 3. Decisions, 2026-10-05

- **The three stages and one doc per stage:** the user's design.
- **Q3, history rows: long format, every row the page shows** (Claude's recommendation, accepted).
  - The form and h2h averages can then be rebuilt. Today they use up to 10 rows, but only 6 are stored.
  - The window becomes a stage-3 setting.
  - Both team ids are stored. They replace the majority-vote guess of the subject team (`scrapers/detail_parsers.py:subject_team_id`) behind `is_home`, `opponent` and `result`.
  - Stage 3 turns the history back into one row per match: the averages, plus only the slots that the analysis uses.
  - The column names change under the value rules (`notes/FIELDS/README.md`).
- **History windows (the user, later on 2026-10-05):** each team's last 5 or 6 matches. Head to head: at most 4, each played no earlier than 2 years before this match. These are stage-3 settings, and stage 1 still stores every row that the page shows. There are two reasons:
  1. The 2-year cut compares the history date with the date of this match. Rule 1 keeps that comparison out of stage 1.
  2. A cut at scrape time can change only with a re-scrape. The stored rows add no columns and no page loads.

  Claude's defaults. Each one is a one-line change, with no re-scrape:
  - team window **6, locked by the user**. It applies to the per-match slots and to the form averages, which use 10 rows today;
  - "2 years" = the kickoff date minus 2 calendar years, inclusive (2026-01-31 → 2024-01-31);
  - head to head over all competitions that the page lists, as today;
  - fewer qualifying matches → fewer rows. No qualifying match → the h2h fields are empty, not zero.
- **Q4, goals and events: unchanged for now.** They already fit stage 1. Three columns stay as documented exceptions: `goal_index`, the goal `side` and the copied `league_id`. Their three docs come after the schedule and detail docs, ~0.5 day.

## 4. Where the detail, goal and event columns go

Counted on 2026-10-05 from `domain/columns.py` and the EPL 2025-26 files: detail 537 (51 + 18 history slots × 27), goals 9 + 3, events 9 + 3.

**Stage 1:**
- detail (16): `match_id`, `odds_bookmaker`, `odds1x2_init_*` (3), `odds1x2_live_*` (3), `strength_*` (2), `h2h_compare_*_pct` (2), `guess_*_pct` (2), `*_next_fixture_days` (2);
- history slot (17 × 18): `match_id`, `league_id`, `date`, `league`, `ht_score`, `ft_score`, HT/FT goals (4), `odds_{home,draw,away}`, `corners_{ft,ht}_{home,away}` (4). Each slot becomes one row of the history file. That row also gets the two team ids and names, which the slot does not have today;
- goals (6), events (7), done logs' `match_id` (2). Bookkeeping: `scraped_at` (2).

**Stage 2:**
- detail (4): `implied_{init,live}_{home,away}`;
- history slot (7 × 18): `total_goals`, `ht_result`, `ft_result`, `over_25`, `btts`, `is_comeback`, `corners_total`.
- Labels of other markets wait for their market (comebacks first).

**Stage 3:**
- detail (31): `{home,away}_recent_*` (12 each), `h2h_*` (7);
- history slot (3 × 18): `is_home`, `opponent`, `result`;
- goals (3): `goal_index`, `side`, `league_id`; events (2): `event_index`, `league_id`; done logs (2): `n_goals`, `n_events` — the documented exceptions of Q4. They stay in stage 1 for now.
- New, from the old `notes/FIELDS.md`: rest days (D13, now `notes/FIELDS/DETAIL_3_MULTI.md` D3.24). Of the survey's flags (K6), only the out-of-round flag is left. It is a schedule field now (`notes/FIELDS/SCHEDULE_3_MULTI.md` S3.07). The other two left the project on 2026-10-13 (`notes/LOG/MIGRATIONS.md`).

## 5. Steps — one at a time

| step | what | who | size |
|---|---|---|---|
| P2 | The user's on-page check of the detail and live stage-1 docs, ≤ 20 fields a sitting (progress in `notes/FIELDS/README.md`). Decide which of the remaining page candidates (C5–C7, C9–C22) join stage 1, comebacks only | user + Claude | ~4 sittings |
| P4 | Detail: stage-1 scraper (match-level + long history), stage-2 and stage-3 builders. Stage 2 of the history file carries a read-only `d2_is_friendly` per history row (the user, 2026-10-10), from `domain/scope.py:is_friendly`; tournament friendlies without "friendly" in their name slip through (`qa/CLAUDE.md` §3) | Claude | ~2.5 days |
| P5 | The join; re-point `features/`, `qa/`, `analysis/` and the goal/event work lists (`scrapers/goals.py:history_ids` reads the history file) | Claude | ~0.5 day |
| P6 | Re-scrape in the new format: detail and live, after P4. Then run every gate and self-check | Claude, with the user's go | detail ≈ 36k pages (36,238 matches, 2026-10-13), ~18 h at the one measured rate (`notes/WORKING/IDEAS_2026-10-01.md` idea 4, Phase 1) |
| P7 | Freeze the stage-1 docs | user | — |

P2 comes before P4, because the docs are the specification for the code.

## 6. Open points Claude handles (no user decision needed)

- The odds snapshot of the history rows (Initial or Final?): `notes/FIELDS/DETAIL_1_RAW.md` D1.32–34. Settle it in P2.
- `corners_ht_*` are stored as floats (`3.0`) because of empty cells. Store them as nullable ints.
- The join: a loader function or a written file. Decide in P5.
- Module names, and their place in the layer table. The steps that change them also update root `CLAUDE.md` (data paths, and the rule "Only `scrapers/` may write to `data/finished/1_raw/`") and `notes/LOG/MIGRATIONS.md`.
