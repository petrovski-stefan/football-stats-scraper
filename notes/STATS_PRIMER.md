# STATS_PRIMER.md — The Four Statistical Tools of This Project, Explained

Companion to `HANDOFF.md`, which says *when* to use these tools. This document explains
*what they are, why they work, and exactly how to apply them here* — with worked examples
using this project's real numbers (PL 2025–26, 380 matches, league HT-recovery rate 9.7%).
Written to be self-sufficient: a reader (or model) with basic probability should be able
to implement everything from this file alone.

Contents:

1. [Empirical Bayes shrinkage](#1-empirical-bayes-shrinkage) — honest team-level rates from tiny samples
2. [Brier score](#2-the-brier-score) — scoring probabilistic predictions
3. [Calibration curves](#3-calibration-curves) — do your "15%" events happen 15% of the time?
4. [Dixon–Coles](#4-the-dixoncoles-goal-model) — modeling goals so rare markets fall out for free
5. [How they fit together](#5-how-the-four-tools-fit-together-here)

---

## 1. Empirical Bayes shrinkage

### The problem it solves

Aston Villa recovered from 4 of 12 HT deficits (33%). The league rate is 9.7%. Is Villa's
"true" recovery ability 33%? Almost certainly not — 12 trials is nothing. But it's
probably not exactly 9.7% either. Shrinkage answers: **what's the best estimate of a
team's true rate, given both its small sample and what we know about teams in general?**

The naive failure modes it prevents:

- **Trusting the raw rate:** with 20 teams × ~12 trials each, the *luckiest* team will
  always show an extreme rate. Ranking by raw rate ranks mostly by luck.
- **Ignoring the team entirely:** using 9.7% for everyone throws away real heterogeneity
  (some teams genuinely are stronger in second halves).

### The idea

Treat the league as a *prior*: before seeing any Villa data, our best guess for any
team's recovery rate is the league distribution centered on 9.7%. Villa's 12 trials then
*update* that prior. With few trials the estimate stays near the prior; with many trials
the data dominates. "Empirical" Bayes because the prior is estimated from the data itself
(the spread of rates across all 20 teams), not chosen subjectively.

### The formula

The standard model is Beta-Binomial. Each team has a true rate `p_i` drawn from a
Beta(α, β) distribution; observed successes are Binomial(n_i, p_i). The posterior mean —
the shrunk estimate — is:

```
p̂_i = (successes_i + α) / (trials_i + α + β)
```

A convenient reparameterization: let `μ = α/(α+β)` (the league rate) and `k = α+β`
(the *prior strength*, in units of pseudo-trials):

```
p̂_i = (successes_i + k·μ) / (trials_i + k)
```

Read it as: **pretend every team starts the season with `k` imaginary trials at exactly
the league rate, then add the real data.** A team with 0 real trials gets exactly μ; a
team with 500 trials gets essentially its raw rate.

### Worked example (Villa)

With μ = 0.097 and k = 10:

```
p̂_Villa = (4 + 10 × 0.097) / (12 + 10) = 4.97 / 22 ≈ 0.226   → ~22.6%
```

(HANDOFF.md quotes ~17% from a slightly different μ/k choice — the exact number matters
less than the behavior: 33% raw becomes ~17–23% shrunk. Still clearly elevated, but no
longer pretending 12 trials pin down a rate to the third significant figure.)

A team with 1 recovery in 3 trials (raw 33%, same as Villa!) shrinks to
`(1 + 0.97)/(3 + 10) ≈ 15%` — the formula automatically trusts Villa's 33% more than the
3-trial team's 33%. That's the entire point.

### Choosing k

- **Quick default:** k = 10 for this project's team-season rates. Roughly: "a season of
  trailing situations (≈12) should move the estimate about halfway from prior to data."
- **Principled (method of moments):** estimate k from how much teams *actually* differ.
  Compute the raw rates' between-team variance; subtract the variance you'd expect from
  binomial noise alone; what's left is true spread. If observed spread ≈ noise-only
  spread, true heterogeneity is ~zero and k should be huge (shrink everything to the
  mean). In Python, fit a Beta-Binomial by maximum likelihood
  (`scipy.optimize` over α, β) across the 20 team (successes, trials) pairs.
- **The persistence test is the sanity check** (HANDOFF §6): if season-N shrunk rates
  don't correlate with season-N+1 outcomes, k was too small — shrink harder.

### Rules for this project

- Ship shrunk rates **with raw counts attached** (`"villa": {"shrunk": 0.23, "raw": "4/12"}`)
  so the LLM sees the sample size.
- Never emit binary flags (`comeback_prone: true`) from one season.
- The same formula applies to *any* team-level rate: blown leads, BTTS rate, late-goal
  share. One helper function, reused everywhere.

---

## 2. The Brier score

### What it is

The mean squared error of probabilistic predictions against binary outcomes. For N
predictions `p_i` and outcomes `o_i ∈ {0, 1}`:

```
Brier = (1/N) · Σ (p_i − o_i)²
```

Lower is better. Range 0 (perfect) to 1 (confidently wrong every time). Predicting 0.13
on a match that ends in a comeback contributes (0.13 − 1)² = 0.757; on a no-comeback
match, (0.13 − 0)² = 0.017.

### Why it's the right scorer here

- It's a **proper scoring rule**: your expected score is minimized by reporting your true
  belief. You cannot game it by hedging to 50% or by overclaiming — unlike accuracy,
  which is meaningless for a 6% base-rate event (predicting "no comeback" always gives
  94% accuracy and zero information).
- It punishes **overconfidence** quadratically — exactly the LLM failure mode (narrative
  bias inflating 10% to 25%) this project needs to detect.

### The benchmarks that give it meaning

A Brier score in isolation says nothing; it only means something against references:

1. **The base-rate benchmark.** Predict the constant league rate p̄ = 0.0605 for every
   match. Its expected Brier is `p̄(1 − p̄) ≈ 0.0568`. **Any prediction engine that
   scores worse than 0.0568 is worse than knowing nothing but the base rate.**
2. **The market benchmark.** Predict the vig-adjusted odds-implied probability for every
   match. This is the serious opponent — beating it means beating the market.

Report the **Brier Skill Score** against each: `BSS = 1 − Brier_model / Brier_benchmark`.
Positive = better than the benchmark; 0 = equal; negative = worse. Expect tiny positive
numbers at best — on rare events, even genuine skill moves the Brier by little.

### The decomposition (why a score is good or bad)

Murphy's decomposition splits the Brier into three parts:

```
Brier = Reliability − Resolution + Uncertainty
```

- **Uncertainty** = p̄(1−p̄): the irreducible difficulty of the problem (0.0568 here).
  You can't change it.
- **Reliability** (lower = better): calibration error — when you say 20%, does it happen
  20% of the time? This is what §3 visualizes.
- **Resolution** (higher = better): discrimination — do your predictions actually differ
  between matches that comeback and matches that don't? A model that always says 6.05%
  is perfectly calibrated but has zero resolution.

A useful mental model: **calibration is honesty, resolution is knowledge.** The engine
needs both; the decomposition tells you which one is missing.

### Log loss (the companion metric)

`LogLoss = −(1/N)·Σ [o_i·ln(p_i) + (1−o_i)·ln(1−p_i)]`. Also proper, but it punishes
extreme confidence *unboundedly* — predicting 0.1% on an event that happens costs ~6.9
(vs Brier's ~1.0). Track both: log loss will scream first if the LLM ever outputs
near-zero probabilities carelessly. Clip predictions to [0.001, 0.999] before scoring to
avoid infinities.

### Practical notes for this project

- With a 6% base rate you need **hundreds of scored predictions** before Brier
  differences between model versions are meaningful. Persist every prediction
  (HANDOFF §7.5); patience is part of the method.
- Score *every* evaluated match, not just "picks" — selective scoring reintroduces the
  Mode 2 sample-size problem.

---

## 3. Calibration curves

### What they show

A calibration curve (reliability diagram) answers the single most important question
about a probabilistic predictor: **of all the times you said "X%", did the event happen
X% of the time?** Perfect calibration = the curve lies on the diagonal.

### How to build one

1. Collect all logged (prediction, outcome) pairs.
2. Bin predictions — for this project use **quantile bins** (e.g., 5–8 bins with equal
   counts), not fixed-width bins: predictions will cluster in 3–20%, and fixed 0–10%,
   10–20%… bins would leave most bins nearly empty.
3. For each bin plot: x = mean predicted probability, y = observed event frequency.
4. Add the diagonal, and error bars on y (binomial: `√(y(1−y)/n_bin)`) — with rare events
   the error bars are the difference between insight and self-deception.

```python
import numpy as np, pandas as pd

def calibration_table(preds: pd.Series, outcomes: pd.Series, bins: int = 6) -> pd.DataFrame:
    df = pd.DataFrame({"p": preds, "o": outcomes})
    df["bin"] = pd.qcut(df.p, bins, duplicates="drop")
    g = df.groupby("bin", observed=True).agg(
        n=("o", "size"), mean_pred=("p", "mean"), observed=("o", "mean"))
    g["se"] = np.sqrt(g.observed * (1 - g.observed) / g.n)
    return g
```

### How to read the shapes

- **Curve below the diagonal** (predicted 20%, observed 10%): overconfidence — the
  expected LLM failure. The narrative-bias signature is specifically *the top bins* being
  too high: the model's most excited predictions are its least reliable.
- **Curve above the diagonal**: underconfidence — the engine is hugging the base rate
  and its high predictions are actually even better than it claims.
- **Flat curve** (all bins observe ≈6% regardless of prediction): zero resolution — the
  features carry no signal and the engine is decorating the base rate with noise.

### Fixing miscalibration without retraining

Because the engine is an LLM, you can't "retrain" it — but you can **post-hoc calibrate**:
fit a simple monotone map from raw LLM probabilities to calibrated ones on logged data
(Platt scaling = logistic regression on the logit of p; or isotonic regression if you
have 500+ points). The LLM supplies the *ranking and reasoning*; a one-line statistical
map fixes the *levels*. This combination is usually far better than prompting harder.

### Sample-size reality

To distinguish "my 15% bucket observes 15%" from "observes 8%" you need on the order of
**hundreds of predictions per bin region**. Early on, use 3–4 coarse bins, show the error
bars, and refuse to conclude anything a binomial test wouldn't support. A calibration
claim from 30 predictions is a Mode 2 discovery all over again.

---

## 4. The Dixon–Coles goal model

### Why model goals at all when the target is comebacks?

Because both target markets are **functionals of the goal process**:

- P(7+ goals) is the tail of the total-goals distribution.
- P(comeback) = Σ over HT scorelines of P(trail at HT) × P(overturn in the 2nd half).

A binary classifier on `is_comeback` learns from 23 positives per league-season. A goal
model learns its parameters from **every goal in every match** — then rare-market
probabilities are *computed*, not estimated directly. This is the single largest
data-efficiency win available to this project.

### The base model (independent Poisson)

Each team has an **attack** strength `α_i` and **defence** weakness `β_i`; there's a
league **home advantage** `γ`. Goals scored in a match between home team i and away
team j:

```
X_home ~ Poisson(λ),   λ = α_i · β_j · γ        (home goals)
X_away ~ Poisson(μ),   μ = α_j · β_i            (away goals)
```

with an identification constraint (e.g., mean of all α's = 1). Fit by maximum likelihood:
maximize `Σ_matches [ log Pois(x_home; λ) + log Pois(x_away; μ) ]` over all α, β, γ —
~2·(number of teams)+1 parameters, easily done with `scipy.optimize.minimize` on 380+
matches. Then P(any exact scoreline h–a) = `Pois(h; λ) · Pois(a; μ)`, and any market is a
sum over scorelines.

### The two Dixon–Coles (1997) corrections

1. **The low-score dependency (tau).** Real football deviates from independence exactly
   at 0–0, 1–0, 0–1, 1–1 (slightly more draws / fewer 1–0s than independent Poissons
   predict). DC multiply those four scoreline probabilities by a correction
   `τ(h, a; λ, μ, ρ)` with one extra parameter ρ:

   ```
   τ(0,0) = 1 − λμρ      τ(1,0) = 1 + μρ
   τ(0,1) = 1 + λρ       τ(1,1) = 1 − ρ
   ```

   (ρ ≈ −0.1 typically; ρ = 0 recovers independence.) Matters most for 1X2/draw pricing;
   less critical for totals.

2. **Time decay.** Team strength drifts, so weight match `m`'s log-likelihood by
   `exp(−ξ · t_m)` where `t_m` is days-before-now. Choose ξ by maximizing *out-of-sample*
   predictive likelihood (typical half-life: ~a season, ξ ≈ 0.002–0.005/day). This is how
   the model stays current without a sliding window that throws data away.

### The per-half adaptation (this project's version)

The comeback market lives in the difference between halves, and this repo already stores
`goals_1h`, `home_2h_goals`, `away_2h_goals`. So fit **two linked models**:

- A first-half model → distribution over HT scorelines (λ₁, μ₁).
- A second-half model → distribution over 2H goals (λ₂, μ₂), ideally with a
  **state adjustment**: 2H scoring rates conditional on the HT state (teams trailing
  at HT empirically raise their scoring intensity; leaders sit back). Start simple —
  a multiplicative factor per HT-state (leading / level / trailing), 2–3 extra
  parameters — before anything fancier.

Then, exactly:

```
P(home comeback) = Σ over HT scorelines (h₁ < a₁) of
                     P(h₁, a₁ | 1H model)
                   · P(2H goals overturn the deficit | 2H model, state = home trailing)

P(7+ goals)      = Σ over (h, a) with h + a ≥ 7 of P(h, a | full model)
```

Truncate scoreline sums at ~10 goals per team; the probability mass beyond is negligible.

**Where shrinkage re-enters:** the per-team 2H trailing-state multiplier is precisely the
"comeback-prone" trait, now expressed inside a model that uses all matches — and it's a
per-team parameter estimated from little data, so either shrink it (fit a hierarchical
prior) or share one multiplier league-wide until the persistence test (§1) proves teams
truly differ.

### Cautions specific to Dixon–Coles

- **It knows nothing about news** — injuries, rotation, motivation. That's the intended
  division of labor here: DC provides the *statistical anchor*; odds movement and the
  web-search layer provide the *news adjustment* (via the LLM's bounded anchor-and-adjust,
  HANDOFF §7.2).
- **Promotion/relegation:** newly promoted teams have no top-flight history — initialize
  their strengths from the promoted-team average, not the league average.
- **Overdispersion:** raw Poisson slightly underestimates high-scoring blowouts, which
  matters for the 7+ market specifically. If the model's P(7+) underruns the observed
  1.84%, consider a negative-binomial variant — but only after the multi-league dataset
  confirms the gap out-of-sample.
- **Validate it like everything else:** walk-forward by season, Brier + calibration on
  the derived market probabilities (§2, §3). A goal model is not exempt from the
  evaluation loop just because it's elegant.

---

## 5. How the four tools fit together here

The full loop, end to end:

1. **Dixon–Coles (per half)** turns the scraped goal archive into a calibrated
   *statistical anchor*: P(comeback), P(7+) per match, computed not guessed.
2. **Empirical Bayes shrinkage** produces honest team-level traits (recovery rates,
   2H supremacy, blown leads) for the league context card — sample sizes visible,
   luck suppressed.
3. The **LLM engine** starts from the anchor (1), adjusts within bounds using the shrunk
   traits (2) plus odds movement and structured news, and outputs a probability.
4. **Brier scores** (against the base-rate and market benchmarks) and **calibration
   curves** on the logged predictions decide what survives: every feature, prompt change,
   and model version must pay its way in skill score, or it goes.

One sentence per tool: *shrinkage keeps the inputs honest, Dixon–Coles makes rare markets
estimable from all the data, Brier keeps score, and calibration curves tell you whether
to believe the score.*

### Suggested reading (if internet access is available)

- Dixon & Coles (1997), *Modelling Association Football Scores and Inefficiencies in the
  Football Betting Market*, JRSS-C — the original paper, very readable.
- Efron & Morris (1977), *Stein's Paradox in Statistics* (Scientific American) — the
  classic baseball batting-average shrinkage story; this project's Villa problem exactly.
- Any treatment of Murphy (1973)'s Brier decomposition for the
  reliability/resolution/uncertainty split.
