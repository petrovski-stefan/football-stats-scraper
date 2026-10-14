# RESULTS — can nowgoal-exclusive features overturn F12?

**Group: Record.** Do not edit it. Add a dated erratum. Only the user can decide an edit.

**Run 2026-07-25.** Preregistration: `notes/PREREGISTRATION.md` (written before any model
was fitted; three amendments, all logged before the holdout was opened). Reproduce with
`uv run python -m modelling.experiment --holdout`.

> **2026-10-13:** F12, which this study tested against, F11, which it imported, and every
> other F-number below belong to the old league study, dropped from the project that day
> (`notes/MIGRATIONS.md`). The six families stay; §3 and §4 are deleted.

## Verdict

**No. Both preregistered bars fail, and the well-powered test fails cleanly.**

Zero of six nowgoal-exclusive feature families survive the dev screen. On the untouched
2025-26 season the full candidate does not beat a constant at the product level, and its
most confident picks are its worst. F12's conclusion extends to the nowgoal feature set.

| bar | result |
|---|---|
| **Bar 1** — held-out Brier beats constant *and* odds-only chain, CI excluding zero | **NOT PASSED** |
| **Bar 2** — top-quintile slate Wilson lower bound above base rate | **NOT PASSED** |

---

## 1. Dev screen — nothing survives

Expanding-window walk-forward, 1,182 matches / 65 comebacks, Holm-corrected over six tests.

| family | product Brier | factor-1 Brier | ΔBrier vs baseline | raw p | Holm p | |
|---|---|---|---|---|---|---|
| C_pressure | 0.054172 | 0.234742 | −0.000020 | 0.103 | 0.621 | dead |
| A_ht_state | 0.054134 | 0.235539 | −0.000060 | 0.140 | 0.700 | dead |
| B_2h_supremacy | 0.054160 | 0.235109 | −0.000032 | 0.208 | 0.834 | dead |
| F_venue_h2h | 0.054177 | 0.235417 | −0.000016 | 0.253 | 0.834 | dead |
| D_non_market | 0.054235 | 0.235136 | +0.000042 | 0.896 | 1.000 | dead |
| E_congestion | 0.054244 | 0.234769 | +0.000052 | 0.998 | 1.000 | dead |

Reference: constant 0.054195, `baseline_chain_odds` 0.054192. The **full candidate** (all
families, 20 regressors) scored 0.054198 — *worse* than the baseline (ΔBrier +0.000004,
CI [−0.000107, +0.000125]) and worse at factor 1 too (0.236259 vs 0.234922). Adding all
six families to the price is a net loss.

Note the ordering: `D_non_market` — the family with the strongest prior, since nowgoal's
crowd poll and H2H bar are only 40–56% correlated with the market price — finished
second-to-last. Being unpriced is not the same as being informative.

## 2. Holdout — 591 matches, 33 comebacks, opened once

```
  ## Level 1 — factor 1: the half-time state (well powered)
    Brier P(HT non-draw), constant  0.237717
    Brier P(HT non-draw), baseline  0.236200
    Brier P(HT non-draw), candidate 0.236141
    candidate vs baseline: dBrier=-0.000059  95% CI [-0.001269, +0.001137]  inconclusive
    candidate vs constant: dBrier=-0.001565  95% CI [-0.003331, +0.000148]

  ## Level 2 — factor 2: completion, the imported F11 curve
    trailing states n=361  completions=33 (9.14%)
    Brier, constant       0.083056
    Brier, imported F11   0.081418
    F11 vs constant: dBrier=-0.001638  95% CI [-0.005859, +0.002255]  inconclusive

  ## Level 3 — the product: P(comeback)  [Bar 1]
    constant             Brier=0.052720
    baseline_chain_odds  Brier=0.052835
    candidate_chain      Brier=0.052805
    restricted variant   Brier=0.052835  (families: none survived)
    candidate vs constant: dBrier=+0.000085 [-0.000109, +0.000259]
    candidate vs baseline: dBrier=-0.000030 [-0.000146, +0.000070]
    **BAR 1: NOT PASSED**

  ## Calibration (candidate, quintiles of predicted risk)
     n     predicted   observed
      119      5.18%      5.88%
      118      5.69%      6.78%
      118      5.91%      6.78%
      118      6.14%      5.93%
      118      6.53%      2.54%

  ## Bar 2 — slate lift  (base rate 5.58%)
     top decile               n= 59  hits= 1  rate= 1.69%  lift=0.30x  CI[0.30%, 9.00%]  fail
     top quintile (primary)   n=118  hits= 3  rate= 2.54%  lift=0.46x  CI[0.87%, 7.21%]  fail
     top third                n=195  hits= 7  rate= 3.59%  lift=0.64x  CI[1.75%, 7.22%]  fail
```

## 3. (dropped 2026-10-13: the half-time state's predictability)

## 4. (dropped 2026-10-13: the F11 replication)

## 5. Reading the slate inversion

The top decile went 1-for-59 (0.30× base). This looks like anti-signal, but with one hit
the Wilson CI is [0.30%, 9.00%] — it contains the base rate, so the honest reading is
noise, not inversion. Worth recording that F12's chained model produced the same shape
(its top decile predicted 6.4%, delivered 4.5%): when a model has no signal, its confident
tail is where its noise concentrates.

## 6. Limits of this result

Stated plainly, per PREREGISTRATION §8:

- **The product-level null is underpowered and proves little on its own.** 33 holdout
  comebacks cannot detect anything but a large effect. Do not cite Bar 1's failure as a
  replication of F12.
- **The factor-1 null is well powered and is the real finding.** 591 trials at a 61% rate,
  against a benchmark (the market) that itself gains only 0.64%.
- **Scope: two leagues, three seasons, 2,058 matches.** England and Poland. Per F1 leagues
  do not differ in comeback rate, so pooling is justified — but this is not a continental
  claim.
- **Family E lost its forward-looking half** to a stale-data quarantine
  (PREREGISTRATION §9); congestion was tested backward-looking only.
- Six families, ≤2 engineered features each, one closed list, one holdout opening. No
  feature was added, dropped, or redefined after results were seen.

## 7. What this changes

1. **The nowgoal feature set is now in F10's graveyard**, tested and dead: rolling HT-state
   history, 2H supremacy, corner-vs-goal pressure, site strength/crowd consensus,
   cross-competition congestion, venue splits and H2H half-time patterns. These were the
   untested residue F12 never saw; they are no longer untested.
2. **The remaining refuge for the comeback hypothesis is unchanged**: the ~30 unsurveyed
   European countries, judged by F1's preregistered bar (≥8% over ≥600 matches, persistence,
   mechanism). Nothing here speaks to that, and nothing here makes it more likely.
3. **The over-6.5 market (F9/F13) is still the pre-match product this project actually
   supports** — and the pipeline still does not collect the O/U line that F13's model runs
   on. That remains the highest value-per-hour change available.
4. **Corpus expansion is not indicated for this question.** The binding constraint is not
   sample size at factor 1; it is that the half-time state carries almost no pre-match
   signal. More leagues would sharpen a null we can already see clearly.
