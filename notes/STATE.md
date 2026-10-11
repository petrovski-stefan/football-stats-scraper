# STATE — the claim ledger

**Maintenance rule: whenever a study concludes, update this file in the same commit.** Numbers here are copied from the source note; if they disagree, the source note wins and this file is the bug. How to act on the ledger (holdout, candidate protocol, binding rules): `modelling/CLAUDE.md`.

Evidence: only the exclusion-filter row has committed raw output (`FILTER_STUDY_RAW.md`). Every other row is **note-only** until its output is committed under `notes/runs/` (rule: `modelling/CLAUDE.md` §2).

Status: **Dead** = tested and failed · **Live-exploratory** = positive, not preregistered · **Live-preregistered** = passed a preregistered bar (none yet) · **Reopened** = once dead, now unresolved · **On-retry-list** = in the closed 15-claim list (`RETRY_CANDIDATES_2026-09-23.md` §4–5), untested on the new corpus · **Untested**.

## Ledger

| claim / feature family | status | key number | n | source |
|---|---|---|---|---|
| League identity → comeback rate | Reopened | χ² p=0.18; between-league sd ≈0.08pp; persistence r=0.108 | 23,127 (22 divisions, 11 countries ≈ one fifth of Europe, 2023-26) | LEAGUE_STUDY F1; RETRY §2 |
| League gap in completion given HT-decisive (EPL vs Ekstraklasa) | On-retry-list (#1) | 10.73% vs 6.85%, p=0.017; MH stratification costs +2.9% SE | 2,058 | RETRY §1b, §2 |
| Unsurveyed ~30 countries clear F1's bar (≥8% over ≥600) | On-retry-list (#8) | — | — | LEAGUE_STUDY F1; RETRY §5 |
| Team comeback-proneness (counts; HANDOFF's "Villa flag") | Dead | Spearman 0.068, p=0.09 | 621 team season-pairs | LEAGUE_STUDY F2 |
| Match balance / fav odds / \|AH\| (HANDOFF's competitiveness gate) | Dead | r=0.002, p=0.81; \|AH\| AUC 0.502 | 23,127; 15,475 | LEAGUE_STUDY F3; MARKET_LINE §2 |
| Venue as a separate completion feature | Dead | logistic venue coef +0.001 | 9,195 | LEAGUE_STUDY F11 |
| Completion given trailing (HT-conditional, not pre-match) | Live-exploratory | 2.6% → 25.6% by trailer odds; Brier 0.0704 vs 0.0749; nowgoal replication 8.8% vs 9.0% | 9,969; test 4,526; 1,090 | LEAGUE_STUDY F4, F11; RESULTS §4 |
| Rest days / calendar / open→close odds movement | Dead | p=0.77; p=0.27, 0.099; p=0.89, 0.33 | 23,127 | LEAGUE_STUDY F10 |
| Last-match market flags (alone and 45 AND-pairs) | Dead | 0 of 90 survive | 23,127 | LEAGUE_STUDY F10 |
| Rolling last-5 shot share | Dead (priced) | partial p=0.73 | 23,127 | LEAGUE_STUDY F10 |
| Rolling last-5 goals scored | Dead | zero walk-forward Brier gain | 6,630 | LEAGUE_STUDY F10, F12 |
| "Late-goal leagues" | Dead | 2H share 53.7–57.0%, p≈0.15 | 22 leagues | LEAGUE_STUDY F10 |
| Implied totals (O/U 2.5 price) → comeback | Live-exploratory | 4.2% → 6.8% across octiles, r=+0.028 | 23,127 | LEAGUE_STUDY F10 |
| F12 chained pre-match pricer | Dead | Brier 0.04809 vs constant 0.04812 | 6,630 | LEAGUE_STUDY F12 |
| Comebacks are deserved (shot share) | Live-exploratory | 57.6% of shots vs 55.2% for winners | 1,104 | LEAGUE_STUDY F7 |
| Favorite–longshot bias prices HT/FT out | Live-exploratory | ROI −27.5% (odds 7–12) to −42.6% (12+) | 69,366 prices | LEAGUE_STUDY F6 |
| Over-6.5 league structure and model | Live-exploratory; retest On-retry-list (#14) | χ² p=9e-9; log-loss 0.0899 vs 0.0931 | test 7,647 | LEAGUE_STUDY F9, F13; RETRY §5 |
| Family A: rolling HT-state history | Dead | Holm p=0.700 | 1,182 dev | RESULTS §1 |
| Family B: 2H supremacy | Dead | Holm p=0.834 | 1,182 dev | RESULTS §1 |
| Family C: corner-vs-goal pressure | Dead | Holm p=0.621 | 1,182 dev | RESULTS §1 |
| Family D: site strength / crowd consensus | Dead | Holm p=1.000 | 1,182 dev | RESULTS §1 |
| Family E: cross-competition congestion | Dead | Holm p=1.000 | 1,182 dev | RESULTS §1 |
| Family F: venue / H2H splits | Dead | Holm p=0.834 | 1,182 dev | RESULTS §1 |
| The half-time state is pre-match predictable | Dead | market beats a constant by only 0.64% | 591 holdout | RESULTS §3 |
| Pre-match exclusion filter | Dead | 27 missed vs 26.7 random; UB 8.25% vs <2% bar; goal-total AUC 0.559; ~15% of the needed distance | 1,565 | FILTER_RESULTS §1–2; FILTER_STUDY_RAW. Its oracle (≤ 2 goals, 0 comebacks missed) is true by definition, not a finding: MARKET_COMEBACKS §1 (2026-10-11) |
| Filter pilot inversion (low goal env → more comebacks) | Dead | did not replicate walk-forward | 591 → 1,565 | PREREG_FILTER §3; FILTER_RESULTS §1 |
| In-house comeback-environment model | Dead | AUC 0.497; top-20% zero enrichment | 591 | PLAN_2026-07-25 §1 |
| Market O/U 2.5 line ranks the environment | Live-exploratory; the 2025-26 confirmation MARKET_LINE §4 planned is void (A9), so it needs a new confirmatory set | AUC 0.592; top-20% 1.33× (Wilson LB 5.68% vs 5.16%) | 7,675 test | MARKET_LINE §2–3 (read §4); PREREGISTRATION A9 |
| nowgoal's own O/U line reproduces it / AH adds over O/U | On-retry-list (#9, #10) | — | — | RETRY §5 |
| Per-league testing of candidate rules | Dead | best-of-50 under a pure null clears the top-100 bar (2.03×); a per-league slate resolves only 2.52× | simulated | RETRY §0, §1a; PLAN_2026-09-20 §3 |
| Table-vs-market divergence | On-retry-list (#2) | 7.11%, 1.29×, p=0.060: **unsourced** (2026-10-11). No definition or run was recorded (DECISIONS D6.2), and the only table columns in that corpus were the post-round positions, which move each match's winner up the table: the leak favours this claim. Not prior evidence; a retest uses the pre-kickoff table (S3.03) | 2,058 | RETRY §4 |
| Behavioural candidate rule (last 5 + 3 H2H), 2026-08-29 | Dead | top-100: 5 hits, 4.90%, 0.88×; bar excluded at every slate ≥ 50; corr +0.004 HT-decisive, +0.006 goals | 2,058 | BEHAVIOURAL §0, §4 |
| Global AUC/Brier can judge a candidate rule | Dead | a 3.6× rule scores AUC 0.527 | — | BEHAVIOURAL §1 |
| Its five signals individually | Dead | 0 of 12 comparisons > 1.96 SE | 2,058 | BEHAVIOURAL §3 |
| Out-of-round matches suppress comebacks | Reopened (2026-10-11) | 5.41%, 0.98×, p=0.582, on a flag that misfired: in the 4 of its 6 seasons still held, 70 of the 89 flagged matches were played on schedule (a later round had started early), so at most 41 of the 111 were rescheduled matches | 111 | PLAN_2026-09-20 §1 and its erratum |
| Out-of-round 1.5× slate; T1 exhaustion; T3 round state; T4 Monday; T2 structured BTTS | On-retry-list (#3–7) | Holm p 0.779–1.000 on first test. Two of the five rest on faulty flags (2026-10-11): T4 most likely read the stored UTC+8 weekday (its script was not kept; survey claim #6 copies it as "`is_monday` as stored"), and 96 of the 103 stored Mondays in the 4 seasons still held were Sundays, so Mondays are untested; the slate used the misfiring out-of-round flag | 2,058 | PLAN_2026-09-20 §3 and its errata; RETRY §4 |
| Goal-timing aggregates (`conceded_pre_ht_rate`, `late_goal_rate`, 36 buckets) | On-retry-list (#11–13) | — | — | RETRY §5 |
| Card/sub team traits incl. `yellows_while_leading_avg` | On-retry-list (#15, EPL 2025-26 stratum excluded) | reliability @6: 0.290 | 20 teams | RETRY §5; PREREGISTRATION A8 |
| Trailing-conditioned first-sub minute | Dead (reliability screen) | depth-6 reliability 0.000 (raw split-half −0.004) | 20 teams | RELIABILITY §2; erratum in PREREGISTRATION A9 |
| P(FT win \| HT loss) as a team trait | Dead (reliability screen) | 0.000 (A8.3 does not say whether split-half or depth-6) | 20 teams | PREREGISTRATION A8.3 |
| `first_sub_minute_avg` measures reaction speed | Dead | corr 0.428 with the claimed quantity | 20 teams | RELIABILITY §3 |
| Leader's 2H yellows → completion | Live-exploratory (used 2025-26 labels; spent per A9) | 6.39% → 13.25%; p=0.020, Holm 0.34 | 1,397 | RELIABILITY §4 |
| Leader's 2H red card → completion | Dead | 4.2× raw; 17.65% [6.19, 41.03] after ordering check | 17 | RELIABILITY §4 |
| Chaser's first 2H substitution timing | Dead | 57.1' vs 57.6' | 876 | RELIABILITY §4 |
| Prospective gut log of the un-encodable filter | Untested | needs 11 hits per 100 picks | — | PLAN_2026-09-20 §2 |

## Open leads, in priority order

1. **Declare the confirmatory set** (league list + date) in a dated amendment before any new scrape starts (PREREGISTRATION A9(c)). 2025-26 is spent and cannot confirm anything.
2. **Confirm the market-line result under preregistration** on that set: closed features, LOLO + walk-forward (MARKET_LINE §4, §7). MARKET_LINE §4's planned 2025-26 opening is void per A9. The football-data corpus was retired 2026-07-26; re-fetch via MARKET_LINE §5.
3. **Phase 0 of the scrape:** neutral league list plus `PREREGISTRATION_ENVIRONMENT.md` (PLAN_2026-07-25 Phase 0). Then evaluate the 15 claims with Holm, MH strata and LOLO (RETRY §6–7).
4. **Decide `FRIENDLY_MARKER`**; it gates what the scrape fetches (PREREGISTRATION A8.6; `qa/CLAUDE.md` §3).
5. **Set picks-per-week** to unblock the prospective gut log; 2026-27 is part of the confirmatory set as it accrues (PLAN_2026-09-20 §2, §4; A9(b)).
6. **The filter's 10–15% coverage dip:** 5 missed vs 8.9 expected, P≈0.13. It needs more data, not more modelling (FILTER_RESULTS §4).

## Resolved conflicts

- **Retry list size:** 15 claims (A8.2). The "14" in RETRY §0 and RELIABILITY §6 predates A8 — PREREGISTRATION A9 erratum.
- **Holdout status (2025-26):** spent, not "opened N times"; its labels informed at least eight analyses — PREREGISTRATION A9.
- **Oracle and totals figures** (was conflict 4; resolved 2026-10-11): not a conflict. The two notes measured different sets (2,058 matches, and the 1,565 the walk-forward evaluated), and both quantities follow from the definition or the goal model: no comeback is possible with 2 goals or fewer, and the comeback rate by final goal total is structural (MARKET_COMEBACKS §1 "Minimum goals", §2 "Comeback rate by final goal total").

## Conflicts (listed, not resolved)

1. **F1.** LEAGUE_STUDY F1 says league selection is dead. RETRY §2 moves it out of the graveyard, while saying it "does not overturn F1".
2. **Corpus expansion.** RESULTS §7.4 says it is "not indicated". PLAN_2026-07-25, RETRY and MARKET_LINE §7 plan a multi-country scrape.
3. **Role of over-6.5.** LEAGUE_STUDY F13 and RESULTS §7.3 call it the product. PLAN_2026-07-25 §0 calls it "an input feature, not a target".
4. *(Resolved 2026-10-11: see "Resolved conflicts", oracle and totals figures.)*
5. **HANDOFF vs LEAGUE_STUDY.** HANDOFF §2–3 (380 PL matches) trusts the competitiveness gate (3.2% vs 9.2%) and the Villa flag, with a 6.05% base rate. LEAGUE_STUDY F2/F3 refute both at 5.15%, and LEAGUE_STUDY says it wins.
6. **ALGOBETTING vs measurements.**
   - ALGOBETTING §6 gives a comeback base of "~7–8%" against the measured 5.15%.
   - It calls comebacks "substitute-driven", but RELIABILITY §4 finds substitution timing null.
7. **Stale claim.** RESULTS §7.3 says the pipeline doesn't collect the O/U line; it was built 2026-09-23 (MARKET_LINE §7).

## Method notes

- `HANDOFF.md`: strategy, leakage traps, methodology rules.
- `STATS_PRIMER.md`: shrinkage, Brier, calibration, Dixon–Coles.
- `ESOTERIC_MODELS.md`: seven further tools; #2 and #3 are already measured (LEAGUE_STUDY F5, F6).
- `PREREGISTRATION.md`: the testing template and amendment log.
- `PREREGISTRATION_FILTER.md`: the filter study's preregistration.
- `ALGOBETTING.md`: untested background.
