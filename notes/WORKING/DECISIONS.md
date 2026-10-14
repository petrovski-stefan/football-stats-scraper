# DECISIONS — open research decisions

**Group: Working.** Edit it in place, and keep it current.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

This file holds the questions that need an owner's decision but must not block the task that raised them (convention in root `CLAUDE.md`). Each entry keeps its current working value until the owner decides it. When a decision is made, move the entry to **Closed**, with the date and the choice. If the decision changes a screening bar, or anything else under preregistration, it also needs a dated entry in the amendment log of `notes/RECORD/PREREGISTRATION.md`.

## Open

### D1 — Raise the market-orthogonality low bar above 0.05?

- **Raised:** 2026-09-28, by Claude (while recording the screening bars)
- **Question:** The low bar kills a candidate when |r| with the market is **below 0.05**. `BEHAVIOURAL_RESULTS.md` §4 puts the failed behavioural rule at **+0.05** with the market. §5.2 introduced this screen because that rule failed. So, as written, the bar passes the rule that the screen must catch.
- **Options:**
  1. Keep "< 0.05" (current, provisional).
  2. Make it inclusive: kill at |r| ≤ 0.05.
  3. Raise it to a higher value (for example 0.10) that is clearly above the behavioural rule.
- **Context:** `modelling/CLAUDE.md` §3 "Screening bars"; `notes/RECORD/BEHAVIOURAL_RESULTS.md` §4, §5.

### D2 — Is 0.80 too loose as a redundancy bound?

- **Raised:** 2026-09-28, by Claude
- **Question:** The high bar kills a candidate as redundant when |r| with the market is **above 0.80**. The one "priced" feature that the notes had (rolling last-5 shot share, dropped 2026-10-13) was killed by a partial test, with closing odds as a control (partial p = 0.73). A raw correlation did not kill it. Its raw |r| with the market was never published. A feature can be priced at a raw |r| well below 0.80. So this bound can fail to catch it.
- **Options:**
  1. Keep 0.80 (current, provisional).
  2. Lower it to a stated value.
  3. Replace the raw-|r| test with an incremental test: the partial association of the candidate, with the market as a control. The old league study (dropped 2026-10-13) did this.
- **Context:** `modelling/CLAUDE.md` §3 "Screening bars". Its examples were dropped on 2026-10-13: the old league study's F10 (shot share, "priced") and F11 (venue "already priced"), and their STATE rows.

### D3 — The market-orthogonality screen for candidates that are themselves market prices

- **Raised:** 2026-09-28, by Claude
- **Question:** Retry claims #9 (nowgoal's O/U line) and #10 (the AH line) *are* market lines. Their |r| with the market is about 1. So the redundancy bar would kill them automatically. The current working value: the screen is "not applicable" to a market-price candidate. Both claims were dropped on 2026-10-13. The question stays open for any later candidate that is a market price.
- **Options:**
  1. Keep "not applicable" (current, provisional).
  2. Apply the bar anyway, which kills such a candidate at this screen.
  3. For a market candidate, correlate only against the *other* market columns (for example AH against O/U). This fits the framing of the dropped #10, "adds over O/U".
- **Context:** `modelling/CLAUDE.md` §3 "Screening bars". #9 and #10 were in `notes/RECORD/RETRY_CANDIDATES_2026-09-23.md` §5 until 2026-10-13.

### D4 — What "the market price" means for the screen

- **Raised:** 2026-09-28, by Claude
- **Question:** `BEHAVIOURAL_RESULTS.md` §4–5 says "the market price", but it does not name a column. Today the bar applies to the **largest |r| across the pre-kickoff market columns** (`implied_init_*`, `implied_live_*`, and the O/U line where it exists). The largest |r| makes the low bar easier to pass, and the high bar easier to trip.
- **Options:**
  1. Keep max |r| across the pre-kickoff market columns (current, provisional).
  2. Name one column (for example the favourite's `implied_live_*` probability, or the O/U line).
  3. Use one composite market score (for example the multiple correlation R of the candidate on all market columns).
- **Context:** `modelling/CLAUDE.md` §3 "Screening bars"; `notes/RECORD/BEHAVIOURAL_RESULTS.md` §4, §5.

### D5 — Give `features.engine --self-check` a post-match leak check (engineering task)

- **Raised:** 2026-09-28, by Claude (a planted-leak test of the stats-reviewer agent)
- **Question:** Should the engine get a leak check like `modelling.scoreline --leak-check`? That check sets every post-match column to NaN, builds again, and requires identical output.
- **Evidence:** A planted edit added `df["ft_home_goals"] + df["ft_away_goals"]` to `combined_recent_gf` in `features/engine.py` `build_features`. The as-of-round self-check still **passed** ("1600 comparisons, 0 mismatches"). It compares rolling features against the target round only, but this line reads the outcome columns of the target row itself. Only the stats-reviewer agent caught it (BLOCK, with the line cited). A leak that does not go through the reviewer has no automatic guard. An example is a leak committed without `/check`.
- **Options:**
  1. Add `--leak-check` to `features.engine`. It sets the columns of its post-match list to NaN (`engine.py`, the "never model features" block), builds again, and requires every feature column to stay the same.
  2. Leave it to the reviewer (current).
- **Context:** `features/engine.py` `self_check`, `build_features`; `modelling/scoreline.py` `--leak-check`.

### D6 — Notes cleanup from the 2026-09-28 full ledger audit

- **Raised:** 2026-09-28, by two full consistency audits of the notes. These issues existed before the audits.
- **Handling rule:** fix them with dated errata (in `notes/RECORD/PREREGISTRATION.md` §10, or in the amendment log of the relevant note), and with pointers from `notes/WORKING/STATE.md`. **Do not edit the historical notes' text.**
- **Items:**
  1. *(audit #2)* **Ambiguous label.** PREREGISTRATION A8.3 gives the reliability of P(FT win | HT loss) as 0.000. It does not say if that value is split-half or depth-6. RELIABILITY_SCREEN §2 has no row for this quantity. STATE already flags it on its row. **Moot 2026-10-13:** the claim was dropped.
  2. *(audit #3)* **Figure not found in its cited source.** RETRY_CANDIDATES §4 row 2 gives the table-vs-market divergence as 7.11%, 1.29×, p=0.060, and cites MARKET_LINE. But MARKET_LINE_FINDINGS has no such figure. Its §1 MH table (z=+1.12) does not give p=0.060. Find the run that produced the figure, or mark it unsourced. **Done 2026-10-11: marked unsourced** in the `notes/WORKING/STATE.md` row. The run was never committed. The only table columns in that corpus were the post-round positions (`home_team_position`, `away_team_position`, `position_gap`), and they leak in favour of this claim. **Moot 2026-10-13:** the claim was dropped.
  3. *(audit #4)* **Dead path.** PREREGISTRATION A9.1 row 4 cites `notes/filter_study_raw.txt (1c5ac01)`. The file no longer exists, and MIGRATIONS has no entry for it. Add a MIGRATIONS line that points to `notes/RECORD/FILTER_STUDY_RAW.md`.
  4. *(audit #6)* **Stale planned counts.** PREREGISTRATION_FILTER §7 expects 531 excluded / 29.4 at 30% coverage (and matching rows for 20/40/50%). It calculated them from the ~1,773 usable matches. But the walk-forward evaluated n=1,565, so the actual figures are 469 / 26.7 (FILTER_RESULTS §1). This needs a dated amendment in PREREGISTRATION_FILTER §9.
  5. *(audit #7)* **One n for two measurements.** The STATE row "Market O/U 2.5 line ranks the environment" puts AUC 0.592 (MARKET_LINE §2, environment target, pooled dev n=15,475) and 1.33× (§3, comeback target, test n=7,675) under one n, "7,675 test". Split the key number and the n in the STATE row. This is the one item that edits STATE and not a historical note. **Moot 2026-10-13:** the claim was dropped.
  6. *(second audit, #7)* **Truncated key number.** The STATE row "Rest days / calendar / open→close odds movement" gives the rest-days result as p=0.77. LEAGUE_STUDY F10 gives three sub-tests: p = 0.77 / 0.15 / 0.48 (min, differential, the trailing team's own). Fix it in the STATE row. **Moot 2026-10-13:** the claim was dropped.
  7. *(second audit, #8)* **Citation format.** STATE Open leads items 1 and 4 (5 before 2026-10-13) cite "PREREGISTRATION A9(c)" and "A9(b)". A9 numbers its sub-items 1–4, and A10 cites them as "A9.2". So these must read A9.3 (declare first) and A9.2 (the confirmatory set). Fix it in STATE.
  8. *(second audit, #9)* **Stale instruction.** The RESULTS.md header still says "Reproduce with `uv run python -m modelling.experiment --holdout`". A7 says that the transcript must not be regenerated, and A9.1 says that `--holdout` must not be run. Do not edit RESULTS. Add a STATE pointer, or extend the A9 erratum, to record that its reproduce line is void.
- **Context:** neither audit report is saved. Items 1–5 come from the first audit. Items 6–8 come from the second audit on the same day.

### D7 — Order rounds by stage in `features/` and `modelling/` (engineering task)

- **Raised:** 2026-10-01, by Claude (stage-aware schedule scraper)
- **Question:** How should `features/` and `modelling/` order the rounds of a league-season that has more than one kept stage? This must be decided before such a league-season gets to them.
- **Evidence:** Since 2026-10-01, `scrapers.schedule` writes every kept stage of a league-season into one CSV. Rounds start again at 1 in each stage, and the `stage` column names the stage. So Apertura round 3 and Clausura round 3 both have `round == 3`. `features/engine.py` `_rolling_form` sorts the matches of each team by (league_name, season, round). `self_check` takes the history as `round < row["round"]`. With two stages, a Clausura match counts as "before" Apertura round 5. That is future data, so it is a leak. `modelling/experiment.py` and `modelling/filter_study.py` group by (league_name, season, round), so two different rounds become one block. Parallel groups (Group 1–5) share round numbers correctly, because they are played at the same time. Sequential stages (Apertura, then Clausura) do not. `features/engine.py` `ROUND_GROUP` and `qa/league.py` `_rounds` already include `stage`.
- **Options:**
  1. Order by kickoff date inside a league-season, and use (stage, round) as the key of the round blocks.
  2. Let only league-seasons with one kept stage, or only parallel groups, get to `features/` and `modelling/`.
- **Working value:** no league-season with more than one kept stage is enabled for analysis. Today only EPL 2025-26 is enabled, and its page has no stage tabs.
- **Context:** `scrapers/schedule.py` `_scrape_stage`; `config/leagues.json` `keep`; `features/engine.py`; `modelling/experiment.py`; `modelling/filter_study.py`.

## Closed

### D8 — The market-orthogonality low bar for the stake fields

- **Raised and decided:** 2026-10-12. Claude raised it. The user's choice: skip the low bar for these fields.
- **Question:** the low bar (`modelling/CLAUDE.md` §3: kill a candidate below |r| 0.05 with the market) assumes that a useful candidate overlaps the market price. The stake fields S3.11–13 (`notes/FIELDS/SCHEDULE_3_MULTI.md` §B3) carry what the opening odds cannot carry: what a result is worth to each side, and the results after the odds were published.
- **Measured 2026-10-12**, under D4's working value (largest |r| across the opening 1X2 probabilities, the O/U line and the AH line): S3.11 0.091, S3.12 0.124 (`above`) and 0.177 (`below`), S3.13 0.043. The two flags of the planned test: "late and close" (S3.11 ≤ 5 and S3.12 `above` ≤ 3) 0.026; "fell 2+ places since the odds opened" (S3.13 ≥ 2) 0.072. The low bar would kill S3.13 and the first flag.
- **Choice:** the low bar does not apply to S3.11–13, or to flags built from them. The high bar (redundant above 0.80) still applies, and all of them pass it. D1 (the value of the bar for other candidates) stays open.
- **Amendment log:** `modelling/CLAUDE.md` §3 asks for a dated entry in `notes/RECORD/PREREGISTRATION.md` §10 when a bar changes. It is not written yet. The survey draft that reserved A11 and A12 was deleted on 2026-10-13, so the next number is A11. Open.
