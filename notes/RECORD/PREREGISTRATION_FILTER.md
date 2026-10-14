# PREREGISTRATION — the pre-match exclusion filter

**Group: Record.** Do not edit it. Add a dated erratum. Only the user can decide an edit.

**Written 2026-07-25, before the filter model was built or fitted.** Companion to
`notes/PREREGISTRATION.md` (the F12 re-test) and bound by the same rules: the family list
below is closed, the bar is fixed, and any unavoidable deviation is appended to §9 with a
date and a reason rather than edited in silently.

---

## 1. The question — and why it is not the previous one

`notes/RESULTS.md` established that nowgoal-exclusive features cannot *predict* comebacks:
the half-time state is barely forecastable by anyone, and the bookmaker's own price beats
a constant by only 0.64%.

This study asks the opposite-signed question:

> **Hypothesis (H2).** A pre-match model can identify a large subset of matches in which a
> comeback is effectively impossible, and remove them.

These are different problems with different failure modes. Prediction needs lift on a 5.5%
event. Exclusion needs a *large* subset with a rate near zero. One can fail while the
other succeeds — and unlike prediction, exclusion has a hard mechanical foundation.

## 2. The mechanical foundation (measured, all 2,058 matches)

| condition | share of matches | comebacks |
|---|---|---|
| ≤ 2 total goals | 45.1% | **0** |
| no team scores 2+ in the second half | 64.4% | **0** |

Comebacks live entirely in the 35.6% of matches where some team scores 2+ after the break,
where the rate is 15.55%.

**The oracle:** a filter that knew the final goal total would exclude **45.1% of matches
with zero misses** (Wilson upper bound 0.41%). This study measures how much of that ceiling
a *pre-match* model can recover.

## 3. Prior evidence against H2 — recorded before the study runs

Two things already point at a null, and both are logged here so the result cannot later be
presented as a surprise.

**A pilot inverted.** A logistic on goal-environment features, trained on 2023-25 and
applied to 2025-26, put the *highest* comeback rates in its lowest-goal-environment bucket:
bottom decile 8.47%, bottom quintile 9.32%, against a 5.58% base. The environment model
itself worked (excluded-set env rate 23.7% vs 31% base) — the comebacks did not follow.
Neither result is significant (bottom-decile Wilson CI [3.67%, 18.35%] contains the base
rate), so this is suggestive, not decisive.

**The shape that explains it.** Comeback rate against total goals is non-monotone, peaking
at the minimum viable scoreline:

| total goals | 0 | 1 | 2 | **3** | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| comeback rate | 0% | 0% | 0% | **14.6%** | 5.1% | 10.9% | 2.5% | 19.4% |

Odd totals spike and even totals collapse, because a comeback requires a **decisive**
result and even-goal games are full of draws. 57.9% of all comebacks are exactly 3-goal
games. So lowering the goal forecast walks *toward* the band where comebacks concentrate,
until it falls off the cliff at 2 goals. Any filter that models a smooth goal-richness
gradient will therefore point the wrong way — which is precisely what the pilot did.

Related: F10 measured implied totals moving comeback rate only 4.2% → 6.8%, and F3's
cancellation mechanism has killed every unconditional pre-match filter attempted so far.

## 4. The model — generative, so the mechanics are structural

A discriminative model on a proxy target cannot express a cliff at 3 goals. The filter is
therefore a generative scoreline model, and `p_comeback` is obtained by summation, making
it **exactly zero wherever the scoreline mass cannot reach a reversal**.

1. **First-half rates** — Poisson regressions for home and away 1H goals on §5's features.
2. **Second-half rates conditional on the half-time state** — separate regressions taking
   the HT scoreline (lead/level/trail and margin) as features. *Prior note: the aggregate
   game-state effect in this corpus is small — 2H total goals run 1.605 / 1.556 / 1.608 by
   home-leads / level / away-leads — so this step is expected to add little. It is retained
   because a comeback model that assumes teams behave identically when leading and chasing
   is wrong in principle, and the size of the effect is itself worth reporting.*
3. **Dixon–Coles low-score correction** (`notes/STATS_PRIMER.md`). Load-bearing, not
   decorative: independent Poisson under-predicts draws, and the even-goal collapse in §3
   *is* the draw effect.
4. **Scoreline enumeration** — HT (0–4 × 0–4) × 2H (0–4 × 0–4); sum the mass where the
   half-time leader loses at full time. Yields `p_comeback`, `p_total_le2`, `p_ft_draw`.

## 5. Feature families — closed list

| # | family | contents |
|---|---|---|
| **G1** | recent goals | rolling as-of-round goals for/against, per team and per half; detail's `*_recent_gf_avg` / `ga_avg` / `over25_rate` |
| **G2** | H2H goals | `h2h_avg_total_goals`, `h2h_over25_rate`, per-match H2H goal and HT-split detail from `h2h_last1..6_*` |
| **G3** | odds | `mkt_sup`, `mkt_tot`, `mkt_p_draw` (the market's own decisiveness estimate), closing price, open→close drift |

### What is not a feature

The target match's own `total_goals`, `ht_*_goals`, `*_2h_goals` and `is_comeback` are used
**only** as training labels, as the oracle benchmark (deliberately post-match — that is what
makes it an unachievable ceiling), and for scoring. They are never model inputs.

The one genuine leak risk is step 2, which conditions on the half-time state — unknown
pre-match. It is an observed feature *at fit time only*; at predict time the model sums
over every HT scoreline weighted by the first-half model. Enforced by `--leak-check` (§8),
which NaNs every post-match column and requires bit-identical predictions.

## 6. Protocol

- **Expanding-window walk-forward over all 1,773 usable matches** (post 5-round burn-in),
  pooled across leagues, cut off by date.
- **No clean holdout remains.** 2025-26 was opened for the F12 study and again for the §3
  pilot. Every prediction is still strictly out-of-sample *in time*, which is the property
  that matters most; what is lost is protection against accumulated knowledge of that
  season. The closed family list in §5 and the fixed bar in §7 are the compensating
  controls. Any positive result should be discounted accordingly and confirmed on new data.

## 7. Success bar

> **Exclude ≥ 30% of matches, with the excluded set's comeback rate at a Wilson 95% upper
> bound below 2%.**

| coverage | n excluded | max comebacks allowed | expected if the filter is worthless |
|---|---|---|---|
| 20% | 354 | 1 | 19.6 |
| **30% (the bar)** | **531** | **4** | **29.4** |
| 40% | 709 | 6 | 39.3 |
| 50% | 886 | 9 | 49.1 |

Deliberately strict: "really not possible" is a strong claim, and a filter that merely
thins comebacks slightly is not one anybody should act on.

**Reported regardless of the verdict:**

- the full coverage-vs-miss-rate curve (5%–60%) with CIs at every point;
- three benchmarks — random exclusion (= base rate), naive single-feature exclusion on
  lowest `mkt_tot` (the strawman the pilot effectively ran), and the oracle (45.1% / 0);
- **oracle recovery**: what fraction of the oracle frontier the pre-match model reaches —
  the honest headline number whichever way it lands;
- sanity diagnostics: the excluded set's actual mean total goals and draw rate. If the
  model is not finding genuinely low-scoring matches, the *filter* is broken rather than
  the hypothesis, and that is a different (fixable) finding.

## 8. Hard gates — the study stops if any fails

- `modelling/scoreline.py --self-check`: enumerated probabilities sum to 1 (±1e-6) on every row;
  `p_comeback` is exactly 0 where the mass cannot reach 3 goals; model-implied base rates
  match observed on the fitting data within tolerance — P(comeback) ≈ 5.54%,
  P(total ≤ 2) ≈ 45.1%, P(FT draw) ≈ 25.95%, P(HT draw) ≈ 38.63%, mean 1H goals ≈ 0.727 /
  0.557, mean 2H goals ≈ 0.860 / 0.727; and the fitted model reproduces the non-monotone
  comeback-vs-total-goals shape including the 3-goal peak.
- `modelling/scoreline.py --leak-check`: predictions bit-identical with post-match columns NaNed.
- `features/engine.py --self-check`: the as-of-round invariant still holds after the G1 extension.

## 9. Amendments

**A1 — 2026-07-25, while building the model, before any filter result was produced.**
§8's gate required the fitted model to "reproduce the non-monotone comeback-vs-total-goals
shape *including the 3-goal peak*". **That gate was wrong, and it was wrong in this
document's own §3 table.** 3-goal games run 14.6% but 7-goal games run 19.4% in the full
corpus — the rate peak is not at 3. What is true of 3 goals is that it carries the largest
share of comeback *mass* (57.9% of all comebacks), which is a statement about where
comebacks are, not where the rate is highest.

The mechanically correct structure, and the gate as now implemented, is:

- **zero floor** — comeback rate is exactly 0 below 3 total goals;
- **odd/even parity** — odd totals exceed their adjacent even totals, because a comeback
  requires a decisive result and even totals are full of draws.

The 3-goal mass share is reported as a diagnostic rather than enforced. The fitted model
passes both structural tests (model 0/0/0 below 3; 3:10.3% > 4:3.9%, 5:13.5% > 6:6.4%) and
puts 46.8% of comeback mass at 3 goals against 58.2% observed. No bar in §7 changes.

**A2 — 2026-07-25, same window.** Two implementation details worth recording because they
affect the numbers:

- **Enumeration grid.** §4 did not fix a truncation limit. Fitted second-half rates reach
  ~2.0 on the highest-scoring fixtures, where Poisson mass above 5 goals is ~1.7% — too
  much to renormalise away honestly. The grid runs to **8 goals per team per half**,
  leaving a residual under 1e-4 (verified by the mass gate).
- **Half-time state clipping.** The second-half model's state inputs are clipped to a
  3-goal lead. Enumeration still visits every half-time scoreline; only the *state feature*
  is clipped, so the regression is never extrapolated to a 5-0 half-time it never saw in
  training. This does not touch the leak guarantee — the state remains enumerated, never
  observed, and `--leak-check` passes.
