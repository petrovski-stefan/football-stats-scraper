# RESULTS — the pre-match exclusion filter

**Group: Record.** Do not edit it. Add a dated erratum. Only the user can decide an edit.

**Run 2026-07-25.** Preregistration: `notes/PREREGISTRATION_FILTER.md` (two amendments,
both logged before any filter result was produced). Raw transcript:
`notes/FILTER_STUDY_RAW.md`. Reproduce with `uv run python -m modelling.filter_study --bar`.

## Verdict

**The bar is not passed, and the filter is statistically indistinguishable from random
exclusion.**

At the preregistered 30% coverage the filter missed **27 comebacks where random exclusion
misses 26.7**. Required upper bound < 2%; achieved 8.25%.

| | excluded n | comebacks missed | miss rate | Wilson UB |
|---|---|---|---|---|
| random exclusion | 469 | 26.7 avg | 5.69% | — |
| naive lowest `mkt_tot` | 469 | 28 | 5.97% | 8.49% |
| **scoreline filter** | **469** | **27** | **5.76%** | **8.25%** |
| **oracle** (knows the total) | 469 | **0** | **0.00%** | 0.81% |

---

## 1. The coverage-vs-miss curve

Corpus n = 1,565 (walk-forward drops the first blocks to the 200-match minimum training
size), 89 comebacks, base rate 5.69%.

| coverage | n | missed | miss rate | 95% CI | expected if useless |
|---|---|---|---|---|---|
| 5% | 78 | 4 | 5.13% | [2.01%, 12.46%] | 4.4 |
| **10%** | 156 | **5** | **3.21%** | [1.38%, 7.28%] | 8.9 |
| 15% | 234 | 9 | 3.85% | [2.04%, 7.15%] | 13.3 |
| 20% | 313 | 16 | 5.11% | [3.17%, 8.14%] | 17.8 |
| 30% *(bar)* | 469 | 27 | 5.76% | [3.99%, 8.25%] | 26.7 |
| 40% | 626 | 33 | 5.27% | [3.78%, 7.31%] | 35.6 |
| 60% | 939 | 50 | 5.32% | [4.06%, 6.95%] | 53.4 |

There is a hint of something at 10–15% coverage — 5 missed where 8.9 were expected — but
it is not significant (Poisson P(≤5 | 8.9) ≈ 0.13) and the CI runs to 7.28%, nowhere near
the 2% the bar requires. Beyond 20% coverage the curve is flat on the base rate.

**The pilot's inversion did not replicate.** The exploratory run that motivated this study
put the *highest* comeback rates in its lowest bucket; done properly, walk-forward, with a
generative model, the low tail is slightly *better* than base. The inversion was noise, as
its confidence interval said at the time.

## 2. Why it fails — the number that explains everything

The mechanical ceiling is real and large: an oracle knowing the final goal total excludes
**44.2% of matches with zero misses**. The filter recovers almost none of it —
**1.12× enrichment** (49.5% of the excluded set is genuinely impossible, against 44.2%
corpus-wide).

The reason is that **the pre-match goal forecast is far too blunt**, and this is measurable
directly. Predicting the oracle's own criterion — will this match finish under 3 goals? —
the model scores:

- **AUC = 0.559** (0.50 is chance)
- predicted P(total ≤ 2) spans only 0.18–0.55, with the 10th–90th percentile inside
  **0.370–0.484**

| decile of predicted P(total ≤ 2) | predicted | actually ≤ 2 goals | comeback rate |
|---|---|---|---|
| 1 (most goals expected) | 0.331 | 35.7% | 6.37% |
| 5 | 0.431 | 39.5% | 5.73% |
| 10 (fewest goals expected) | 0.499 | **52.9%** | 5.73% |

The model does discriminate — 35.7% → 52.9% is a real gradient, and the excluded set's
mean total goals is genuinely lower (2.755 vs 2.953). The filter is **not broken**. It is
simply nowhere near sharp enough, and the arithmetic of the bar shows by how much.

### The arithmetic of the bar

Among matches that *can* produce a comeback (≥ 3 goals), the rate is 10.2%. So for an
excluded set:

```
miss rate  =  P(match is possible)  x  10.2%
```

To reach a 2% miss rate the excluded set must be **at least 80% mechanically impossible.**
The corpus baseline is 44.2%. The model achieves **49.5%**. It needs to travel from 44% to
80% and it travels to 50% — recovering roughly **15% of the required distance**.

That gap is a goal-forecasting limit, not a comeback-modelling limit. Even the decile the
model is most confident will be low-scoring still contains 47% of matches capable of a
comeback.

## 3. What this adds to the project

1. **Exclusion joins prediction in the graveyard.** `notes/RESULTS.md` showed comebacks
   cannot be *predicted* pre-match; this shows they cannot be *excluded* pre-match either.
   The two are different problems with different metrics, and both now have measured
   answers on this corpus.
2. **The binding constraint is now named and quantified.** Both failures reduce to the same
   root: the pre-match forecastable structure of a football match is very thin. The
   half-time state is predictable to AUC-equivalent ~0.64% Brier gain (`RESULTS.md`); the
   goal total to AUC 0.559. Comebacks sit downstream of both, so they inherit the product
   of two weak signals.
3. **A mechanical fact worth keeping.** Comeback rate is exactly 0 below 3 goals, and shows
   strong odd/even parity above it (3: 14.6%, 4: 4.9%, 5: 11.2%, 6: 2.8%) because a
   comeback requires a decisive result. 58% of all comebacks are 3-goal games. This is the
   most structured thing anyone has found about comebacks in this project — it is just not
   *forecastable* structure.
4. **A validated instrument now exists.** `modelling/scoreline.py` is a calibrated generative model
   of the full scoreline distribution (implied P(comeback) 4.9% vs 5.5% observed,
   P(total ≤ 2) 44.6% vs 44.3%, P(FT draw) 24.2% vs 25.9%), gated by a mass check, a
   structural check and a leak check. It is reusable for **7+** — F9/F13's live
   market — where the target is a direct functional of the same goal distribution rather
   than a rare reversal downstream of it. That is the natural next use.

## 4. Limits

- Two leagues, three seasons, 1,565 evaluated matches, 89 comebacks.
- **No clean holdout.** 2025-26 was already opened twice before this study
  (PREREGISTRATION_FILTER §6). Every prediction is out-of-sample in time, but the closed
  feature list and fixed bar are the only guards against accumulated knowledge. This
  matters less than usual here: the result is a null, and contamination inflates
  performance rather than deflating it.
- The 10–15% coverage dip is unexplained and not significant. If anyone revisits this, that
  is the only place worth looking, and it needs more data rather than more modelling.
