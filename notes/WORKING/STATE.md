# STATE — the claim ledger

**Group: Working.** Edit it in place, and keep it current.

**Maintenance rule: whenever a study concludes, update this file in the same commit.** The numbers here are copies from the source note. If they disagree, the source note is correct, and this file has the error. How to act on the ledger (holdout, candidate protocol, binding rules): `modelling/CLAUDE.md`.

Evidence: only the exclusion-filter row has committed raw output (`FILTER_STUDY_RAW.md`). Every other row is **note-only** until its output is committed under `notes/runs/` (rule: `modelling/CLAUDE.md` §2).

Status: **Dead** = tested and failed · **Live-exploratory** = positive, not preregistered · **Live-preregistered** = passed a preregistered bar (none yet) · **Reopened** = once dead, now unresolved · **On-retry-list** = in the closed retry list (`RETRY_CANDIDATES_2026-09-23.md` §4–5; 6 claims left after the 2026-10-13 drop), untested on the new corpus · **Untested**.

## Ledger

| claim / feature family | status | key number | n | source |
|---|---|---|---|---|
| Family A: rolling HT-state history | Dead | Holm p=0.700 | 1,182 dev | RESULTS §1 |
| Family B: 2H supremacy | Dead | Holm p=0.834 | 1,182 dev | RESULTS §1 |
| Family C: corner-vs-goal pressure | Dead | Holm p=0.621 | 1,182 dev | RESULTS §1 |
| Family D: site strength / crowd consensus | Dead | Holm p=1.000 | 1,182 dev | RESULTS §1 |
| Family E: cross-competition congestion | Dead | Holm p=1.000 | 1,182 dev | RESULTS §1 |
| Family F: venue / H2H splits | Dead | Holm p=0.834 | 1,182 dev | RESULTS §1 |
| Pre-match exclusion filter | Dead | 27 missed vs 26.7 random; UB 8.25% vs <2% bar; goal-total AUC 0.559; ~15% of the needed distance | 1,565 | FILTER_RESULTS §1–2; FILTER_STUDY_RAW. Its oracle (≤ 2 goals, 0 comebacks missed) is true by definition, not a finding: MARKET_COMEBACKS §1 (2026-10-11) |
| Filter pilot inversion (low goal env → more comebacks) | Dead | did not replicate walk-forward | 591 → 1,565 | PREREG_FILTER §3; FILTER_RESULTS §1 |
| In-house comeback-environment model | Dead | AUC 0.497; top-20% zero enrichment | 591 | PLAN_2026-07-25 §1 |
| Per-league testing of candidate rules | Dead | best-of-50 under a pure null clears the top-100 bar (2.03×); a per-league slate resolves only 2.52× | simulated | RETRY §0, §1a; PLAN_2026-09-20 §3 |
| Behavioural candidate rule (last 5 + 3 H2H), 2026-08-29 | Dead | top-100: 5 hits, 4.90%, 0.88×; bar excluded at every slate ≥ 50; corr +0.004 HT-decisive, +0.006 goals | 2,058 | BEHAVIOURAL §0, §4 |
| Global AUC/Brier can judge a candidate rule | Dead | a 3.6× rule scores AUC 0.527 | — | BEHAVIOURAL §1 |
| Its five signals individually | Dead | 0 of 12 comparisons > 1.96 SE | 2,058 | BEHAVIOURAL §3 |
| Out-of-round matches suppress comebacks | Reopened (2026-10-11) | 5.41%, 0.98×, p=0.582, on a flag that misfired: in the 4 of its 6 seasons still held, 70 of the 89 flagged matches were played on schedule (a later round had started early), so at most 41 of the 111 were rescheduled matches | 111 | PLAN_2026-09-20 §1 and its erratum |
| Out-of-round 1.5× slate; T4 Monday | On-retry-list (#5, #6) | First test: T4 Holm p 0.891; the slate 0.98×. Both rest on faulty flags (2026-10-11): T4 most likely read the stored UTC+8 weekday (its script was not kept; survey claim #6 copies it as "`is_monday` as stored"), and 96 of the 103 stored Mondays in the 4 seasons still held were Sundays, so Mondays are untested; the slate used the misfiring out-of-round flag | 2,058 | PLAN_2026-09-20 §3 and its errata; RETRY §4 |
| Goal-timing aggregates (`conceded_pre_ht_rate`, `late_goal_rate`, 36 buckets) | On-retry-list (#11–13) | — | — | RETRY §5 |
| Card/sub team traits incl. `yellows_while_leading_avg` | On-retry-list (#15, EPL 2025-26 stratum excluded) | reliability @6: 0.290 | 20 teams | RETRY §5; PREREGISTRATION A8 |
| Trailing-conditioned first-sub minute | Dead (reliability screen) | depth-6 reliability 0.000 (raw split-half −0.004) | 20 teams | RELIABILITY §2; erratum in PREREGISTRATION A9 |
| `first_sub_minute_avg` measures reaction speed | Dead | corr 0.428 with the claimed quantity | 20 teams | RELIABILITY §3 |
| Leader's 2H yellows → completion | Live-exploratory (used 2025-26 labels; spent per A9) | 6.39% → 13.25%; p=0.020, Holm 0.34 | 1,397 | RELIABILITY §4 |
| Leader's 2H red card → completion | Dead | 4.2× raw; 17.65% [6.19, 41.03] after ordering check | 17 | RELIABILITY §4 |
| Chaser's first 2H substitution timing | Dead | 57.1' vs 57.6' | 876 | RELIABILITY §4 |
| Prospective gut log of the un-encodable filter | Untested | needs 11 hits per 100 picks | — | IDEAS idea 4 (moved from PLAN_2026-09-20 §2) |

## Open leads, in priority order

1. **Declare the confirmatory set** (league list + date) in a dated amendment before any new scrape starts (PREREGISTRATION A9(c)). 2025-26 is spent, and it cannot confirm anything.
2. **Phase 0 of the scrape:** a neutral league list and `PREREGISTRATION_ENVIRONMENT.md` (IDEAS idea 4, Phase 0). Then evaluate the 6 remaining retry claims with Holm, MH strata and LOLO (RETRY §6–7).
3. **Decide `FRIENDLY_MARKER`.** It controls what the scrape fetches (PREREGISTRATION A8.6; `qa/CLAUDE.md` §3).
4. **Set picks-per-week.** The prospective gut log cannot start without it. 2026-27 becomes part of the confirmatory set as its matches are played (IDEAS idea 4, the gut log; A9(b)).
5. **The filter's 10–15% coverage dip:** 5 missed vs 8.9 expected, P≈0.13. It needs more data, not more modelling (FILTER_RESULTS §4).

## Resolved conflicts

- **Retry list size:** 15 claims (A8.2). The "14" in RETRY §0 and RELIABILITY §6 is from before A8 (PREREGISTRATION A9 erratum). Six are left after the 2026-10-13 drop.
- **Holdout status (2025-26):** spent, not "opened N times". Its labels informed at least eight analyses (PREREGISTRATION A9).
- **Oracle and totals figures** (was conflict 4; resolved 2026-10-11): not a conflict. The two notes measured different sets: 2,058 matches, and the 1,565 matches that the walk-forward evaluated. Both quantities follow from the definition or from the goal model. No comeback is possible with 2 goals or fewer. The comeback rate by final goal total is structural (MARKET_COMEBACKS §1 "Minimum goals", §2 "Comeback rate by final goal total").

## Conflicts (listed, not resolved)

1. *(Dropped 2026-10-13 with the claims it compared.)*
2. **Corpus expansion.** RESULTS §7.4 says it is "not indicated". PLAN_2026-07-25 and RETRY plan a multi-country scrape.
3. **Role of over-6.5.** RESULTS §7.3 calls it the product. PLAN_2026-07-25 §0 calls it "an input feature, not a target".
4. *(Resolved 2026-10-11: see "Resolved conflicts", oracle and totals figures.)*
5. *(Dropped 2026-10-13 with the claims it compared.)*
6. **ALGOBETTING vs measurements.**
   - It calls comebacks "substitute-driven", but RELIABILITY §4 finds substitution timing null.
7. **Stale claim.** RESULTS §7.3 says that the pipeline does not collect the O/U line. The pipeline collects it since 2026-09-23.

## Method notes

- `HANDOFF.md`: strategy, leakage traps, methodology rules.
- `STATS_PRIMER.md`: shrinkage, Brier, calibration, Dixon–Coles.
- `ESOTERIC_MODELS.md`: seven further tools.
- `PREREGISTRATION.md`: the testing template and amendment log.
- `PREREGISTRATION_FILTER.md`: the filter study's preregistration.
- `ALGOBETTING.md`: untested background.
