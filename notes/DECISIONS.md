# DECISIONS — open research decisions

Questions that need an owner's call but should not block the task that raised them
(convention in root `CLAUDE.md`). Each entry keeps the current working value until it is
decided. When one is decided, move it to **Closed** with the date and the choice. If the
decision changes a screening bar or anything else under preregistration, it also needs a
dated entry in the `notes/PREREGISTRATION.md` amendment log.

## Open

### D1 — Raise the market-orthogonality low bar above 0.05?

- **Raised:** 2026-09-28, by Claude (while recording the screening bars)
- **Question:** The low bar kills a candidate when |r| with the market is **below 0.05**.
  `BEHAVIOURAL_RESULTS.md` §4 puts the failed behavioural rule at **+0.05** with the
  market, and §5.2 introduced this screen because of that rule's failure. As worded, the
  bar passes the rule the screen was built to catch.
- **Options:**
  1. Keep "< 0.05" (current, provisional).
  2. Make it inclusive: kill at |r| ≤ 0.05.
  3. Raise it to a higher value (e.g. 0.10) that clears the behavioural rule with a margin.
- **Context:** `modelling/CLAUDE.md` §3 "Screening bars"; `notes/BEHAVIOURAL_RESULTS.md`
  §4, §5; `.claude/skills/new-candidate/SKILL.md` step c.

### D2 — Is 0.80 too loose as a redundancy bound?

- **Raised:** 2026-09-28, by Claude
- **Question:** The high bar kills a candidate as redundant when |r| with the market is
  **above 0.80**. The one "priced" feature in the notes (rolling last-5 shot share) was
  killed by a partial test after controlling for closing odds (partial p = 0.73), not by
  a raw correlation. Its raw |r| with the market was never published. A feature can be
  priced at a raw |r| well below 0.80, so this bound may not catch it.
- **Options:**
  1. Keep 0.80 (current, provisional).
  2. Lower it to a stated value.
  3. Replace the raw-|r| test with an incremental one: the candidate's partial
     association after controlling for the market, as in LEAGUE_STUDY F10.
- **Context:** `modelling/CLAUDE.md` §3 "Screening bars"; `notes/LEAGUE_STUDY.md` F10
  (shot share, "priced"), F11 (venue "already priced"); `notes/STATE.md` ledger row
  "Rolling last-5 shot share".

### D3 — Step c for candidates that are themselves market prices

- **Raised:** 2026-09-28, by Claude (an interpretation adopted in `/new-candidate`)
- **Question:** Retry claims #9 (nowgoal's O/U line) and #10 (the AH line) *are* market
  lines. Their |r| with the market is about 1, so the redundancy bar would kill them
  mechanically. Currently the skill marks step c "not applicable" for a market-price
  candidate.
- **Options:**
  1. Keep "not applicable" (current, provisional).
  2. Apply the bar anyway, which kills #9 and #10 at step c.
  3. For a market candidate, correlate only against the *other* market columns (e.g. AH
     against O/U), which fits #10's "adds over O/U" framing.
- **Context:** `.claude/skills/new-candidate/SKILL.md` step c;
  `notes/RETRY_CANDIDATES_2026-09-23.md` §5 (#9, #10).

### D4 — What "the market price" means for the screen

- **Raised:** 2026-09-28, by Claude (an interpretation adopted in `/new-candidate`)
- **Question:** `BEHAVIOURAL_RESULTS.md` §4–5 says "the market price" without naming a
  column. Currently the bar applies to the **largest |r| across the pre-kickoff market
  columns** (`implied_init_*`, `implied_live_*`, and the O/U line where present). Taking
  the largest |r| makes the low bar easier to pass and the high bar easier to trip.
- **Options:**
  1. Keep max |r| across the pre-kickoff market columns (current, provisional).
  2. Name one column (e.g. the favourite's `implied_live_*` probability, or the O/U line,
     which MARKET_LINE found to be the one live ranker).
  3. Use one composite market score (e.g. the multiple correlation R of the candidate on
     all market columns).
- **Context:** `.claude/skills/new-candidate/SKILL.md` step c;
  `notes/BEHAVIOURAL_RESULTS.md` §4, §5; `notes/MARKET_LINE_FINDINGS.md` §2–3.

### D5 — Give `features.engine --self-check` a post-match leak check (engineering task)

- **Raised:** 2026-09-28, by Claude (agent known-answer tests, test 1)
- **Question:** Should the engine get a leak check like `modelling.scoreline --leak-check`?
  That check sets every post-match column to NaN, rebuilds, and requires identical output.
- **Evidence:** A planted edit added `df["ft_home_goals"] + df["ft_away_goals"]` to
  `combined_recent_gf` in `features/engine.py` `build_features`. The as-of-round self-check
  still **passed** ("1600 comparisons, 0 mismatches"), because it compares rolling features
  against the target round only, and this line reads the target row's own outcome
  columns. Only the stats-reviewer agent caught it (BLOCK, citing the line). A leak that
  skips the reviewer, for example one committed without `/check`, has no automated guard.
- **Options:**
  1. Add `--leak-check` to `features.engine`: NaN the columns in its post-match list
     (`engine.py`, the "never model features" block), rebuild, and require every feature
     column unchanged.
  2. Leave it to the reviewer (current).
- **Context:** `features/engine.py` `self_check`, `build_features`; `modelling/scoreline.py`
  `--leak-check`; `.claude/skills/test-agents/SKILL.md` test 1.

### D6 — Notes cleanup from the 2026-09-28 full ledger audit

- **Raised:** 2026-09-28, by the `ledger-auditor` agent (scope full). These are pre-existing
  issues, not the one planted for the test.
- **Handling rule:** fix with dated errata (in `notes/PREREGISTRATION.md` §10 or the
  relevant note's amendment log) and pointers from `notes/STATE.md`. **Do not edit the
  historical notes' text.**
- **Items:**
  1. *(audit #2)* **Ambiguous label.** PREREGISTRATION A8.3 gives P(FT win | HT loss)
     reliability as 0.000 without saying whether it is split-half or depth-6.
     RELIABILITY_SCREEN §2 has no row for this quantity. STATE already flags it on its row.
  2. *(audit #3)* **Figure not found in its cited source.** RETRY_CANDIDATES §4 row 2 gives
     table-vs-market divergence as 7.11%, 1.29×, p=0.060 and cites MARKET_LINE, but
     MARKET_LINE_FINDINGS has no such figure. Its §1 MH table (z=+1.12) does not reduce to
     p=0.060. Find the run that produced it, or mark the figure unsourced.
  3. *(audit #4)* **Dead path.** PREREGISTRATION A9.1 row 4 cites
     `notes/filter_study_raw.txt (1c5ac01)`. The file no longer exists and MIGRATIONS has
     no entry for it. Add a MIGRATIONS line pointing to `notes/FILTER_STUDY_RAW.md`.
  4. *(audit #6)* **Stale planned counts.** PREREGISTRATION_FILTER §7 expects 531
     excluded / 29.4 at 30% coverage (and matching 20/40/50% rows). It computed them from
     the ~1,773 usable count, but walk-forward evaluated n=1,565, so the actual figures are
     469 / 26.7 (FILTER_RESULTS §1). Needs a dated amendment in PREREGISTRATION_FILTER §9.
  5. *(audit #7)* **One n for two measurements.** STATE row "Market O/U 2.5 line ranks
     the environment" puts AUC 0.592 (MARKET_LINE §2, environment target, pooled dev
     n=15,475) and 1.33× (§3, comeback target, test n=7,675) under the single n "7,675
     test". Split the key number and n in the STATE row. This is the one item that edits
     STATE, not a historical note.
  6. *(second audit, #7)* **Truncated key number.** The STATE row "Rest days / calendar /
     open→close odds movement" gives the rest-days result as p=0.77. LEAGUE_STUDY F10 gives
     three sub-tests: p = 0.77 / 0.15 / 0.48 (min, differential, trailer's own). Fix in the
     STATE row.
  7. *(second audit, #8)* **Citation format.** STATE Open leads items 1 and 5 cite
     "PREREGISTRATION A9(c)" and "A9(b)". A9 numbers its sub-items 1–4, and A10 cites them
     as "A9.2", so these should read A9.3 (declare first) and A9.2 (the confirmatory set).
     Fix in STATE.
  8. *(second audit, #9)* **Stale instruction.** The RESULTS.md header still says
     "Reproduce with `uv run python -m modelling.experiment --holdout`". A7 says the
     transcript must not be regenerated, and A9.1 says `--holdout` must not be run. Do not
     edit RESULTS: add a STATE pointer, or extend the A9 erratum, recording that its
     reproduce line is void.
- **Context:** neither audit report is saved. Rerun `ledger-auditor` with scope full to
  reproduce them. Items 1–5 come from the first run, and items 6–8 from the second run the
  same day.

### D7 — Order rounds by stage in `features/` and `modelling/` (engineering task)

- **Raised:** 2026-10-01, by Claude (stage-aware schedule scraper)
- **Question:** How should `features/` and `modelling/` order the rounds of a league-season
  that has more than one kept stage? This must be decided before such a league-season
  reaches them.
- **Evidence:** Since 2026-10-01 `scrapers.schedule` writes every kept stage of a
  league-season into one CSV. Rounds restart at 1 in each stage, and the `stage` column
  names the stage. So Apertura round 3 and Clausura round 3 both have `round == 3`.
  `features/engine.py` `_rolling_form` sorts each team's matches by
  (league_name, season, round), and `self_check` takes history as `round < row["round"]`.
  With two stages, a Clausura match counts as "before" Apertura round 5: that is future
  data, a leak. `modelling/experiment.py` and `modelling/filter_study.py` group by
  (league_name, season, round), so two different rounds merge into one block. Parallel
  groups (Group 1–5) share round numbers correctly, because they are played at the same
  time. Sequential stages (Apertura, then Clausura) do not. `features/engine.py`
  `ROUND_GROUP` and `qa/league.py` `_rounds` already include `stage`.
- **Options:**
  1. Order by kickoff date inside a league-season, and key round blocks on (stage, round).
  2. Let only league-seasons with one kept stage, or only parallel groups, reach
     `features/` and `modelling/`.
- **Working value:** no league-season with more than one kept stage is enabled for
  analysis. Today only EPL 2025-26 is enabled, and its page has no stage tabs.
- **Context:** `scrapers/schedule.py` `_scrape_stage`; `config/leagues.json` `keep`;
  `features/engine.py`; `modelling/experiment.py`; `modelling/filter_study.py`.

## Closed

(none yet)
