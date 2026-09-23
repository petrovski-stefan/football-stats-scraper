# Retry candidates — the closed list, fixed before the scrape

**Date:** 2026-09-23
**Status:** list CLOSED. Amendments go in `PREREGISTRATION.md`'s log with a date, not here.

## 0. Why this document exists before the data

The corpus is about to grow from 6 league-seasons to a target of ~30 countries. Several
findings in `notes/` died on small samples. Retrying them is legitimate — *if the list is
fixed now*.

It is not legitimate afterwards. Re-testing claims that already failed, on data chosen
after seeing the failure, is the multiplicity problem `PREREGISTRATION.md` exists for.
Simulated on 2026-09-23, on a top-100 slate under a **pure null**:

| tests run | best-of-k hits | lift | vs the 11-hit bar |
|---|---|---|---|
| 1 | 5.53 | 1.00x | fails |
| 10 | 9.27 | 1.67x | fails |
| 50 | 11.23 | 2.03x | **passes** |
| 100 | 11.98 | 2.16x | **passes** |

At 50+ tests, selection alone clears the bar with no signal present. The list below is
**14 claims**; Holm correction over 14 is affordable, over 14 x 30 leagues is not.

## 1. Splitting by league — decided, with measurements

Three different operations, and they do not go the same way. Measured on the 6 backed-up
league-seasons (2,058 matches, 114 comebacks, 5.54%).

**(a) Separate tests per league — NO.** Turns k tests into k x L. It also guts precision:

| slate | Wilson half-width at p=0.08 | smallest lift resolvable |
|---|---|---|
| pooled top-100 | +/-5.4pp | 0.98x |
| 2 leagues, 50 each | +/-7.8pp | 1.42x |
| 6 league-seasons, 17 each | +/-14.0pp | 2.52x |

**(b) League as a stratum inside one pooled test — YES.** Free, and it removes a real
downward bias. Table-vs-market divergence, same rows, four stratifications:

| stratum | OR | se(logOR) | z |
|---|---|---|---|
| none (crude) | 1.154 | 0.1921 | +0.75 |
| league (2) | 1.242 | 0.1958 | +1.11 |
| league-season (6) | 1.247 | 0.1977 | +1.12 |
| goal-env tercile (3) | 1.209 | 0.1956 | +0.97 |

The SE is essentially unchanged (+2.9%); the *estimate* moves. Pooling a 6.67% league with
a 4.14% one biases the crude OR toward 1. Mantel-Haenszel over league-season strata is
therefore the default for every claim below. It stays **one test**.

**(c) Per-league formulas — NO.** Ekstraklasa contributes 38 comebacks across three
seasons. Nothing fits on that.

**Use a league dummy, not a goal-environment covariate.** The goal-env tercile recovers
only ~60% of the stratified gain, and section 2 explains why.

## 2. The finding that re-tiers F1

The EPL/Ekstraklasa comeback gap is **not** goal environment. Chain decomposition:

| league | P(HT-decisive) | P(complete given HT-dec) | product |
|---|---|---|---|
| english_premier_league | 62.1% | **10.73%** | 6.67% |
| poland_ekstraklasa | 60.5% | **6.85%** | 4.14% |

P(HT-decisive) is nearly equal. The entire gap sits in the completion rate: z=+2.39,
**p=0.017**. Per-league-season goals/match correlates with comeback rate at only +0.586
across six points, and Ekstraklasa's season-to-season sd is 0.19pp against 1.14pp of
binomial noise — too stable to be sampling noise.

**This does not overturn F1.** `LEAGUE_STUDY` F1 measured 22 divisions and found a
between-league true sd of 0.08pp at p=0.18, and it explicitly warns that a two-league
comparison (England vs Portugal, z=2.09) looked significant "because those are the extremes
of 22 draws." Ours is one hand-picked pair of two. p=0.017 uncorrected is exactly the
warned-about case.

It does mean F1 is **unresolved rather than dead**, and that the right target is the
*completion rate* conditional on HT-decisive, not the raw comeback rate F1 pooled. That is
a different quantity, and F1 never tested it per league.

Replication power: to detect 10.73% vs 6.85% at 80% power, alpha=0.05 needs **832
HT-decisive matches per league**, about 1,340 matches ~ 3.5 league-seasons each, ~7 total.
Cheap. Resolving the full between-league variance needs ~20 leagues, which the planned
scrape has.

## 3. Tier 1 — more data will NOT help (do not retry)

These failed with adequate power. Retrying them spends multiplicity budget on known nulls.

| claim | source | measurement |
|---|---|---|
| F2 team comeback-proneness | LEAGUE_STUDY | Spearman 0.068 across seasons |
| F3 balanced-match precondition | LEAGUE_STUDY | r=0.002, p=0.81 |
| F12 chained pricer beats market | RESULTS | Brier 0.04809 vs 0.04812 |
| half-time state is predictable | RESULTS | market beats a constant by 0.64% |
| six nowgoal feature families | RESULTS | all six died on a preregistered slate |
| behavioural hand-weighted rule | BEHAVIOURAL_RESULTS | 0.88x lift, corr +0.004 with HT-decisive |

**F1 (league identity) has been REMOVED from this tier** — see section 2. It is now Tier 2.

## 4. Tier 2 — more data would help (the closed retry list)

Each row carries the matches needed for 80% power at alpha=0.05, computed with
`modelling/experiment.py:required_n`. "L-S" = league-seasons at ~370 matches.

| # | claim | measured | needed | L-S | source |
|---|---|---|---|---|---|
| 1 | league completion-rate gap | 10.73% vs 6.85%, p=0.017 | ~2,700 | 7 | section 2 |
| 2 | table-vs-market divergence | 7.11%, 1.29x, p=0.060 | ~1,900 | 5 | MARKET_LINE |
| 3 | T3 round state | 7.36%, 1.33x, p=0.195 | ~1,400 | 4 | PLAN_2026-09-20 |
| 4 | T1 exhaustion | 2.75% vs 2.77% | ~200 | 1 | PLAN_2026-09-20 |
| 5 | out-of-round slate at 1.5x | 5.41%, 0.98x | ~12,000 | 35 | PLAN_2026-09-20 |
| 6 | Monday suppression | 2.90% on 4 comebacks | ~6,600 | 19 | PLAN_2026-09-20 |
| 7 | structured BTTS >=4/6 | 9.09% on n=22 | ~17,700 | 51 | PLAN_2026-09-20 |

Rows 5-7 need more than the planned scrape delivers. They are on the list so that a later
positive result cannot be presented as if it had been powered; they are **not** expected to
resolve, and a null from them is uninformative.

## 5. Tier 3 — never tested (new instruments, not retries)

Not subject to the retry argument — these have no prior failure. They still join the Holm
family, because they are tested on the same corpus at the same time.

| # | claim | instrument |
|---|---|---|
| 8 | comeback structure in the unsurveyed ~30 countries | the scrape itself; F1's preregistered bar |
| 9 | nowgoal O/U 2.5 line reproduces the AUC 0.592 result | MARKET_LINE_FINDINGS on an in-house line |
| 10 | Asian Handicap line adds over the O/U line | new columns, `parse_ah_odds` |
| 11 | `conceded_pre_ht_rate` (36-45') predicts HT-decisive | `features/goals.py` |
| 12 | `late_goal_rate` (>=75') beats comeback counts as proneness | HANDOFF section 9 item 7 |
| 13 | the 36 time buckets carry anything the aggregates do not | `features/goals.py:BUCKETS` |
| 14 | over-6.5 via the scoreline model (F9/F13) | `modelling/scoreline.py` |
| 15 | cards and substitutions as team traits, incl. `yellows_while_leading_avg` | `features/events.py` |

**Claim 15 was added by amendment `PREREGISTRATION.md` A8 (2026-09-23), before the scrape.**
Two conditions ride with it, both binding. It is evaluated with the
`english_premier_league 2025-2026` stratum **excluded** — A8 §4 discloses that holdout-season
comeback labels were looked at while designing the family. And every feature in it has
already passed the §6.7 reliability screen; two candidates that did not —
a trailing-conditioned first-substitution minute (-0.004) and `P(FT win | HT loss)`
(0.000) — were dropped before costing a test.

Item 14 is the one with a *prior positive*: F9 found real league structure in over-6.5
(chi2=79.6, p=9e-9, r=0.84 with goals/match, 5x spread). Unlike comebacks, splitting by
league is substantively correct there — but as a **continuous goal-environment covariate**,
which generalises to a country not yet scraped, rather than a dummy that does not.

## 6. Protocol

1. **One family of 15.** Holm correction across all of it. Claim 15 was added by a dated
   amendment (`PREREGISTRATION.md` A8, 2026-09-23, before the scrape); a 16th needs the
   same. Claim 15 additionally drops the `english_premier_league 2025-2026` stratum, per
   A8 §4.
2. **Mantel-Haenszel over league-season strata** is the default estimator (section 1b).
3. **Leave-one-league-out** for generalisation, per `PLAN_2026-07-25` Phase 2. A claim
   that survives Holm but fails LOLO is a corpus artifact.
4. **Judge by precision@top-N with a Wilson CI and lift**, never AUC or Brier — a 3.6x
   rule scores AUC 0.527 (`BEHAVIOURAL_RESULTS`).
5. **Screen every candidate outcome-free against the market price first**
   (`BEHAVIOURAL_RESULTS` section 7). A rule orthogonal to the market is orthogonal to the
   best known signal, and costs nothing to reject.
6. **The holdout season stays shut** until the list above is fully resolved on dev. One
   opening, `--holdout`, one shot. Still unspent — but see `PREREGISTRATION.md` A8 §4 for
   an informal look at 2025-26 comeback labels that constrains claim 15 only.
7. **Screen every history-block feature for reliability at depth 6 first**
   (`RELIABILITY_SCREEN_2026-09-23.md` §1, added by A8). Split-half stability of the trait
   at the six-match depth the feature actually has. Outcome-free, so it spends no Holm
   budget, and it kills a feature for free: the best trait measured scores 0.295, and a
   feature scoring ~0 cannot carry signal however good the mechanism behind it looks.
8. **Enumerate the season labels of every scraped league before evaluating anything**
   (A8 §5). A calendar-year league's "2025" never matches a cross-year `TRAIN_SEASONS`
   entry, so it silently lands in no split; `features/engine.py:_warn_unassigned` names it,
   but membership is a decision, not a default.

## 7. What a pass looks like

A claim passes only with all four: Holm-corrected p < 0.05; Wilson lower bound above the
base rate; lift >= 1.25x at a slate size fixed **before** looking; and the same sign in
leave-one-league-out. Three of four is a null with a note, not a finding.

## 8. Reproducing section 1 and section 2

Both were measured on the 6-league-season backup (EPL + Ekstraklasa, 2023-24 through
2025-26), which was trimmed out of `data/` on 2026-09-22 to speed up schema iteration. The
numbers above are the record; re-deriving them needs that corpus back, which the planned
full scrape restores as a by-product. No code was added to the repo for this — the analysis
was one-off, and the instruments it used (`required_n`, `wilson_ci`) already live in
`modelling/experiment.py`.
