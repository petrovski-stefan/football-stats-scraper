# features/ — derived data and the feature matrix

Everything here derives into `data/processed/` and must be reproducible from `data/raw/`.

## 1. The enrich join (third stage)

`features/enrich.py` left-joins the detail file on `match_id` into `data/processed/<league>_enriched.csv`; both raw files are left untouched. It is cheap and idempotent (no browser), so re-run it freely. It lives here rather than in `scrapers/` because a join is not a scrape. The practical gain is that a stale or deleted enriched file is rebuilt in seconds without starting Selenium.

## 2. History blocks go through `history.py`

`features/goals.py` and `features/events.py` both build through `features/history.py`, which owns the shared shape: which history matches count, the aggregate/timeline split, and the score reconciliation both need.

## 3. Four timelines, kept separate

The enriched file carries **four timeline blocks**, six slots per section per kind: `<section>_last<n>_` + `goal_timeline` / `yellow_timeline` / `red_timeline` / `sub_timeline`. The kind is implied by the column, so an entry is just the minute and `F`/`A` — `"26F;53A;63F"`.

They were split on 2026-09-23 after measuring a combined string at 12.1 entries and 62 characters, of which substitutions were 68.1% and red cards 0.6%: the rare event was buried behind the common one. Merging them back is a sort on minute, and the raw stores keep `event_index` for the 1.19% of events that share a minute with a goal.

**Do not merge them into one string.** 5.0% of history slots have a usable event timeline but no usable goal timeline — goals must reconcile against the block's own score, cards have nothing to reconcile against — so one string would force a wrong usability rule on one slot in twenty, and would store the goals four times over.

## 4. Events are conditioned on the goal store

**`features/events.py` takes the goal store because an event without a scoreline is a three-way mixture.** Measured over 6,840 history slots, the subject's own substitutions split 37.3% trailing / 26.0% level / 36.7% leading, and yellows 30.8/35.7/33.4 — so an unconditioned average blends a reaction, a routine change and a closing-out change in near-equal parts. Only **`yellows_while_leading_avg`** was built from that, and only because the reliability screen below said so. An absent goal store is fine: that one column comes back NaN and nothing else changes.

## 5. Reliability screen — run it before testing against outcomes

**Screen a history-block feature for reliability before testing it against outcomes.** The screen costs no outcome data and no Holm budget, which is why it goes first. Method: split-half reliability on the 2025-2026 corpus (each team's 38 matches split odd/even, correlated across 20 teams), then Spearman–Brown extrapolated to the six-match depth these features actually have. Figures below are reliability **at depth 6**, with the raw split-half r in brackets (`notes/RELIABILITY_SCREEN_2026-09-23.md` §2).

- Plain yellows 0.295 (split-half 0.570), `yellows_while_leading` 0.290 (0.564) — conditioning is nearly free, so it was kept.
- A **trailing-conditioned first-substitution minute came out at 0.000 (split-half -0.004)**: managers have no stable "how fast I react when behind", so it was deliberately not built.
- A per-minute exposure denominator scored 0.142 (split-half 0.345) against 0.290 (0.564) per match, so exposure normalisation was rejected too.
- `minutes trailing` correlates -0.925 with points per game, i.e. it is team strength wearing a hat.
- **`first_sub_minute_avg` is kept unconditioned and is not a candidate** — it correlates 0.428 with the quantity its own docstring claimed, and the honest version is noise; do not "fix" it by conditioning it.

Caveat on all of it: n=20 teams, one league-season, so the intervals are wide. Full write-up: `notes/RELIABILITY_SCREEN_2026-09-23.md`.

## 6. Position within a round: use `round_position`

**Never read `match_index_in_round == 1` as "the first match of the round".** 15.6% of matches share their round's earliest kickoff and the tiebreak between them is alphabetical, i.e. meaningless. Use `features/engine.py:round_position`, which derives tie-aware `earlier` / `later` / `slot` / `slots` from `date`: joint-first is `earlier == 0` (321 matches in the current corpus), joint-last is `later == 0` (263). These are derived, not stored, because they are pure functions of a column that is already there. How `match_index_in_round` itself is assigned: `scrapers/CLAUDE.md` §4.

## 7. `TRAIN_SEASONS` / `TEST_SEASONS`

The constants in `features/engine.py` are literal labels fixed by `notes/PREREGISTRATION.md` §2, and **a calendar-year league can never match them** (why: "Season labels" in `domain/CLAUDE.md`). That exclusion is correct — the preregistered corpus is closed, and widening it is a protocol amendment, not a code change. `load_enriched` emits a `UserWarning` naming any league-season in neither split, so a newly scraped league cannot sit in `data/` contributing to nothing unnoticed.
