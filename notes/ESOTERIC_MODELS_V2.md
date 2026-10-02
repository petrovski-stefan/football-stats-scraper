# ESOTERIC_MODELS_V2.md — the extended back shelf (parked)

**Status: PARKED, 2026-10-01. Nothing here is tested or scheduled.** It belongs to
`notes/IDEAS_2026-10-01.md` Phase C (idea 14a).

The source is a proposal written by another AI and pasted in by the user. Claude reviewed it
against this project's data and findings. The proposal's content is kept where it holds; where
it does not, the correction is stated. Numbering continues from `notes/ESOTERIC_MODELS.md`
(tools 1–7), so the models here are 8–34.

---

## 0. Four corrections that apply to the whole proposal

1. **The judge.** The proposal judges every model by global proper scores (log loss, Brier,
   calibration). That is right when the product is a *calibrated price*, for example over-6.5
   probabilities. It is the wrong judge when the product is a *candidate shortlist*. A rule
   hitting 20% on 35 matches (3.6× the base rate) scores AUC 0.527
   (`notes/BEHAVIOURAL_RESULTS.md` §1), so global scores cannot see it. Candidate questions use
   the hit rate in a fixed top-N slate.
2. **The market comes first, not eighth.** The proposal puts "do the models contain
   information the market lacks?" last, as Hypothesis 8. Here it is the gate.
   `notes/RESULTS.md` §3: the price beats a constant on the half-time state by 0.64%, and six
   team-level feature families added 4% of that. Every model below is tested *beyond the
   market* (draft `notes/PREREGISTRATION_SURVEY.md` §6.1), or it has not been tested.
3. **The data that exists.**
   - **Have:** HT/FT scores; opening 1X2, main AH and main O/U odds; goal minutes; card and
     substitution minutes with player names (live page, Tier D); six-match history blocks.
   - **Do not have:** shots, possession or corners per minute; lineups and player minutes;
     managers; odds for any line other than the main AH and O/U lines.

   Many models below need the second list.
4. **Scope.** Models 14–17 and 32 are in-play models. They reverse July's "pre-match only"
   decision and belong to idea 8 only.

## 1. Triage

Verdicts:

- **TRY** — fits the data we have; worth a test later.
- **LATER** — needs data or infrastructure we do not have yet.
- **LOW** — a poor fit for small goal counts or for this product.
- **OUT** — out of scope.
- **ALREADY** — already in the project.

| # | model | verdict | data | first use here |
|---|---|---|---|---|
| 8 | Bivariate Poisson | TRY | have | compare with Dixon–Coles inside baseline B |
| 9 | Hurdle / zero-inflated goals | TRY if diagnostics ask for it | have | 0-0 and BTTS calibration |
| 10 | Negative binomial / Conway–Maxwell–Poisson | TRY as a diagnostic | have | B's dispersion assumption |
| 11 | Hierarchical Bayesian team strength | LATER, low priority | have | a question the price cannot answer |
| 12 | Dynamic hierarchical model | LATER | have | extends ESOTERIC #5 |
| 13 | Gaussian-process team strength | LOW | have | — |
| 14 | Hidden Markov models | LATER, in-play | partial | minute-bucket states (idea 8) |
| 15 | Hawkes processes | TRY, in-play | have (goal minutes) | "does conceding change scoring intensity?" |
| 16 | Competing-risks survival | TRY, in-play | have | generalises F11 to every minute |
| 17 | Joint event models | LATER | missing (shots, corners per minute) | — |
| 18 | Causal forests / double ML | LOW now | — | only with a clean pre-match treatment |
| 19 | Quantile regression | LOW | — | — |
| 20 | Copulas | LOW | — | — |
| 21 | Extreme value theory | LOW | — | — |
| 22 | EVT + market tails | LATER | missing (tail-line odds) | — |
| 23 | Bayesian model averaging | LATER; prefer 24 | — | — |
| 24 | Stacking | LATER | — | once ≥ 2 models beat B |
| 25 | Dirichlet calibration | TRY | have | any 1X2 probability output |
| 26 | Conformal prediction | LOW | — | — |
| 27 | Calibration as a separate model | TRY, cheap | have | every model, before any market comparison |
| 28 | Bayesian neural nets / deep ensembles | OUT for now | missing | idea 9 |
| 29 | Player-level hierarchical models | LATER | missing (lineups) | if the 12b page inventory finds lineups |
| 30 | Managerial survival | OUT | missing | — |
| 31 | Change-point detection | TRY, low priority | have | a principled "form" |
| 32 | Reinforcement learning / MDPs | OUT | missing | — |
| 33 | Agent-based simulation | OUT | missing | — |
| 34 | Skellam distribution | ALREADY | — | F12's chained pricer; `modelling/scoreline.py` enumerates the full joint |

## 2. Model cards — only where the verdict needs a reason

**8 — Bivariate Poisson.** `Y_H = X_H + X_0`, `Y_A = X_A + X_0`. The shared `X_0` can only add
*positive* covariance. Football scores show little of it. Their real oddity is excess draws,
which Dixon–Coles (already in B) or a diagonal-inflated bivariate Poisson handles (Karlis &
Ntzoufras, 2003). Test it as a variant of B on DEV. Keep it only if it improves scoreline
calibration.

**9 — Hurdle / zero-inflated.** These split "did anyone score?" from "how many, given someone
did?". Dixon–Coles already corrects the four low-score cells. Reach for this only if B's
residuals at 0-0 or 1-0 stay wrong after that.

**10 — Negative binomial / Conway–Maxwell–Poisson.** Given team strengths, goal counts are
usually close to Poisson and sometimes slightly *under*-dispersed. A Weibull count model was
built for that reason (Boshnakov, Kharrat & McHale, 2017). Negative binomial only adds
over-dispersion, so it may not help; Conway–Maxwell–Poisson covers both directions. Use them
as a diagnostic of B before a replacement.

**11–12 — Hierarchical and dynamic team strength.** Sound statistics: partial pooling, and it
handles promoted teams. But in this project team strength is what the market price already
carries best. B reads it from the odds, and every team-history feature so far died against
the price (RESULTS §1, LEAGUE_STUDY F10, F12). Build these only for a question the price
cannot answer. The shrinkage idea is already a standing rule (HANDOFF §6).

**15 — Hawkes processes.**

```
λ_A(t) = μ_A + α_AH · Σ exp(−β · (t − t_i^H))
```

Goal minutes exist, so this is testable. The trap: a match whose latent scoring rate is high
produces clustered goals with no excitation at all. Fitted naively, "conceding raises your
scoring" appears whether or not it is true. Condition `μ` on B's pre-match rates, and give
each match its own random effect.

**16 — Competing risks.** From "trailing by one at minute t": equaliser vs the leader scores
again vs full time. This generalises F11 (the half-time completion model) to every minute.
Pre-match it cannot help: the pre-match bottleneck is the *half-time state* (RESULTS §3),
which this model takes as given. In-play (idea 8) it is the right first model.

**17 — Joint event models.** Needs shots and corners per minute, which are not scraped. When
it becomes possible, apply the ordering check of `notes/RELIABILITY_SCREEN_2026-09-23.md` §4:
5 of 8 apparent red-card comebacks had the red *after* the equaliser.

**18 — Causal forests / double ML.** The proposal's example, "the effect of conceding first on
comeback probability", is partly true by definition: a team must concede to trail at
half-time. In-match treatments such as red cards fail the ordering and overlap assumptions
these methods need. Revisit only with a clean pre-match treatment (rest days, travel).

**19 — Quantile regression.** Goal counts take few values (0–7). Conditional quantiles are
coarse steps, and a count model's predictive distribution already gives every quantile.

**20 — Copulas.** With discrete margins (goal counts), the copula is not uniquely identified
(Genest & Nešlehová, 2007). Dixon–Coles and the bivariate Poisson model the same dependence
cleanly.

**21–22 — Extreme value theory.** EVT's asymptotics need continuous, unbounded tails. Goal
totals are small counts, and the 7+ tail is estimated directly (F13, family O). The useful
half of 22, "does the market misprice tails?", needs odds on tail lines (O4.5, O5.5, big
margins), which are not scraped. The favourite–longshot part is ESOTERIC #2 (LEAGUE_STUDY F6).

**23–24 — Model averaging and stacking.** Prefer stacking: when no candidate model is true, BMA
piles its weight onto one of them (Yao, Vehtari, Simpson & Gelman, 2018). For stacking,
"out-of-fold" must mean **time-ordered** folds, so each prediction is made only from earlier
matches. Random folds leak.

**25, 27 — Calibration.** Cheap and always worth it. F11 already needed a yearly intercept
refit. Fit the calibrator on past seasons only, and report raw and calibrated side by side.
For 1X2, calibrate the whole probability vector (Dirichlet calibration; Kull et al., 2019).

**26 — Conformal prediction.** A prediction set such as {Home, Draw} serves neither a price
nor a shortlist. Time order also breaks the exchangeability that its guarantee rests on.

**31 — Change-point detection.** A principled replacement for "last 5" form windows. Expect
little pre-match: rolling form added zero Brier in walk-forward (LEAGUE_STUDY F10, F12).

## 3. Priority — revised

The proposal's order was hierarchical team strength → competing risks → Hawkes. Reordered for
this project:

1. **Calibration (27, 25) and Shin's method (ESOTERIC #1).** Cheap, and needed before any
   model-vs-market comparison is honest.
2. **B's own assumptions (8, 9, 10) on DEV.** Dixon–Coles against bivariate Poisson against
   NB / Conway–Maxwell–Poisson. B produces the labels' baseline for every goal-based market
   (idea 1), so improving it improves all of them.
3. **In-play, only if idea 8 starts:** competing risks (16) first, then Hawkes (15).
4. **Team strength (11–12)** after that, and only for a question the market price cannot
   answer.

## 4. The evaluator

Kept from the proposal: models are competing explanations, and the evaluator decides. A
sophisticated model that cannot beat a simple baseline out of sample is a failed hypothesis.

Made specific for this project:

- **Baseline:** B, the market-odds goal model. "Beats a constant" is not enough.
- **Candidate questions:** hit rate in a top-N slate fixed in advance, with a Wilson CI and
  lift, tested beyond B.
- **Pricing questions:** log loss, Brier, calibration curves and PIT diagnostics, out of
  sample in time.
- **Fresh data:** a model chosen on DEV is judged once on data it never saw (draft
  `notes/PREREGISTRATION_SURVEY.md` §2).

## References

Dixon & Coles (1997), *Applied Statistics* · Karlis & Ntzoufras (2003), *The Statistician* ·
Boshnakov, Kharrat & McHale (2017), *International Journal of Forecasting* · Genest &
Nešlehová (2007), *ASTIN Bulletin* · Baio & Blangiardo (2010), *Journal of Applied Statistics*
· Koopman & Lit (2015), *JRSS A* · Hawkes (1971), *Biometrika* · Wager & Athey (2018), *JASA* ·
Chernozhukov et al. (2018), *Econometrics Journal* · Yao, Vehtari, Simpson & Gelman (2018),
*Bayesian Analysis* · Kull et al. (2019), *NeurIPS*.
