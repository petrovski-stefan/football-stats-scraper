# STATS_PRIMER.md — The Four Statistical Tools of This Project, Explained

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

Companion to `HANDOFF.md`, which tells *when* to use these tools. This document tells *what the tools are, why they work, and exactly how to use them here*. The worked examples use this project's real numbers (PL 2025–26, 380 matches, league HT-recovery rate 9.7%). The file is complete in itself. A reader (or a model) with basic probability can implement everything from this file alone.

Contents:

1. [Empirical Bayes shrinkage](#1-empirical-bayes-shrinkage) — honest team-level rates from very small samples
2. [Brier score](#2-the-brier-score) — a score for probabilistic predictions
3. [Calibration curves](#3-calibration-curves) — do your "15%" events happen 15% of the time?
4. [Dixon–Coles](#4-the-dixoncoles-goal-model) — a goal model that gives the rare markets at no extra cost
5. [How they fit together](#5-how-the-four-tools-fit-together-here)

---

## 1. Empirical Bayes shrinkage

### The problem it solves

Aston Villa recovered from 4 of 12 HT deficits (33%). The league rate is 9.7%. Is Villa's "true" recovery ability 33%? Almost certainly not: 12 trials are too few. But it is probably not exactly 9.7% either. Shrinkage answers this question: **what is the best estimate of a team's true rate, from its small sample and from what we know about teams in general?**

It prevents two simple errors:

- **Trust in the raw rate:** with 20 teams × ~12 trials each, the *luckiest* team always shows an extreme rate. A ranking by raw rate is mostly a ranking by luck.
- **No use of the team at all:** 9.7% for every team removes the real differences between teams (some teams really are stronger in second halves).

### The idea

Use the league as a *prior*. Before any Villa data, our best guess for the recovery rate of a team is the league distribution, with its centre at 9.7%. Villa's 12 trials then *update* that prior. With few trials, the estimate stays near the prior. With many trials, the data has the most effect. The method is "empirical" Bayes because the prior comes from the data itself (the spread of rates across all 20 teams). Nobody chooses it by opinion.

### The formula

The standard model is Beta-Binomial. Each team has a true rate `p_i` from a Beta(α, β) distribution. The observed successes are Binomial(n_i, p_i). The posterior mean, which is the shrunk estimate, is:

```
p̂_i = (successes_i + α) / (trials_i + α + β)
```

A useful reparameterisation: let `μ = α/(α+β)` (the league rate) and `k = α+β` (the *prior strength*, in units of pseudo-trials):

```
p̂_i = (successes_i + k·μ) / (trials_i + k)
```

Read it like this: **each team starts the season with `k` imaginary trials at exactly the league rate. Then add the real data.** A team with 0 real trials gets exactly μ. A team with 500 trials gets almost its raw rate.

### Worked example (Villa)

With μ = 0.097 and k = 10:

```
p̂_Villa = (4 + 10 × 0.097) / (12 + 10) = 4.97 / 22 ≈ 0.226   → ~22.6%
```

(HANDOFF.md gives ~17%, from a slightly different choice of μ and k. The exact number is less important than the behaviour: 33% raw becomes ~17–23% shrunk. That is still clearly high. But it no longer claims that 12 trials fix a rate to the third significant figure.)

A team with 1 recovery in 3 trials (raw 33%, the same as Villa!) shrinks to `(1 + 0.97)/(3 + 10) ≈ 15%`. The formula automatically trusts Villa's 33% more than the 33% of the 3-trial team. That is the full purpose of the method.

### Choosing k

- **Quick default:** k = 10 for this project's team-season rates. Approximately: "a season of trailing situations (≈12) should move the estimate about halfway from prior to data."
- **Principled (method of moments):** estimate k from how much the teams *really* differ.
  1. Calculate the between-team variance of the raw rates.
  2. Subtract the variance that binomial noise alone gives.
  3. The remainder is the true spread.

  If the observed spread ≈ the noise-only spread, the true differences are ~zero. Then k must be very large (shrink everything to the mean). In Python, fit a Beta-Binomial by maximum likelihood (`scipy.optimize` over α, β) across the 20 (successes, trials) pairs of the teams.
- **The persistence test is the sanity check** (HANDOFF §6). If the shrunk rates of season N do not correlate with the outcomes of season N+1, k was too small. Shrink more.

### Rules for this project

- Give shrunk rates **with the raw counts attached** (`"villa": {"shrunk": 0.23, "raw": "4/12"}`), so that the LLM sees the sample size.
- Never give binary flags (`comeback_prone: true`) from one season.
- The same formula applies to *any* team-level rate: blown leads, BTTS rate, late-goal share. Write one helper function, and use it everywhere.

---

## 2. The Brier score

### What it is

The Brier score is the mean squared error of probabilistic predictions against binary outcomes. For N predictions `p_i` and outcomes `o_i ∈ {0, 1}`:

```
Brier = (1/N) · Σ (p_i − o_i)²
```

A lower score is better. The range is 0 (perfect) to 1 (confident and wrong each time). A prediction of 0.13 on a match with a comeback adds (0.13 − 1)² = 0.757. On a match without a comeback, it adds (0.13 − 0)² = 0.017.

### Why it's the right scorer here

- It is a **proper scoring rule**: you get the best expected score when you report your true belief. You cannot cheat it with a hedge to 50%, or with a claim that is too large. Accuracy is different: for an event with a 6% base rate, it has no meaning. A prediction of "no comeback" for every match gives 94% accuracy and zero information.
- It gives a quadratic penalty to **overconfidence**. That is exactly the LLM failure mode that this project must detect (narrative bias that makes 10% into 25%).

### The benchmarks that give it meaning

A Brier score alone tells nothing. It has a meaning only against references:

1. **The base-rate benchmark.** Predict the constant league rate p̄ = 0.0605 for every match. Its expected Brier is `p̄(1 − p̄) ≈ 0.0568`. **A prediction engine with a score worse than 0.0568 is worse than the base rate alone.**
2. **The market benchmark.** For every match, predict the vig-adjusted probability that the odds imply. This is the serious opponent. A model that is better than it is better than the market.

Report the **Brier Skill Score** against each one: `BSS = 1 − Brier_model / Brier_benchmark`. Positive = better than the benchmark. 0 = equal. Negative = worse. At best, expect very small positive numbers. On rare events, even real skill changes the Brier only a little.

### The decomposition (why a score is good or bad)

Murphy's decomposition divides the Brier into three parts:

```
Brier = Reliability − Resolution + Uncertainty
```

- **Uncertainty** = p̄(1−p̄): the difficulty of the problem itself (0.0568 here). You cannot change it.
- **Reliability** (lower = better): the calibration error. When you say 20%, does the event occur 20% of the time? §3 shows this as a chart.
- **Resolution** (higher = better): discrimination. Are your predictions really different for the matches with a comeback and the matches without one? A model that always says 6.05% is perfectly calibrated, but it has zero resolution.

A useful way to remember it: **calibration shows if the probabilities are honest, and resolution shows if the model knows something.** The engine needs both. The decomposition tells you which one is missing.

### Log loss (the companion metric)

`LogLoss = −(1/N)·Σ [o_i·ln(p_i) + (1−o_i)·ln(1−p_i)]`. It is also proper. But its penalty for extreme confidence has *no upper limit*. A prediction of 0.1% for an event that occurs costs ~6.9 (Brier: ~1.0). Record both. If the LLM gives careless probabilities near zero, log loss shows it first. Before you calculate the score, clip the predictions to [0.001, 0.999] to prevent infinite values.

### Practical notes for this project

- With a 6% base rate, you need **hundreds of scored predictions** before Brier differences between model versions have a meaning. Keep every prediction (HANDOFF §7.5). Patience is part of the method.
- Score *every* evaluated match, not only the "picks". Selective scores bring back the Mode 2 sample-size problem.

---

## 3. Calibration curves

### What they show

A calibration curve (reliability diagram) answers the most important question about a probabilistic predictor: **of all the times that you said "X%", did the event occur X% of the time?** Perfect calibration = the curve is on the diagonal.

### How to build one

1. Collect all logged (prediction, outcome) pairs.
2. Put the predictions into bins. For this project, use **quantile bins** (for example 5–8 bins with equal counts), not fixed-width bins. The predictions will be mostly in 3–20%, so fixed bins (0–10%, 10–20%…) would leave most bins almost empty.
3. For each bin, plot x = the mean predicted probability and y = the observed event frequency.
4. Add the diagonal, and error bars on y (binomial: `√(y(1−y)/n_bin)`). With rare events, the error bars show if a result is real or only noise.

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

- **Curve below the diagonal** (predicted 20%, observed 10%): overconfidence, the expected LLM failure. The sign of narrative bias is that *the top bins* are too high: the model's most extreme predictions are its least reliable.
- **Curve above the diagonal**: underconfidence. The engine stays too near the base rate, and its high predictions are really better than it claims.
- **Flat curve** (all bins observe ≈6%, whatever the prediction): zero resolution. The features carry no signal, and the engine only adds noise to the base rate.

### Fixing miscalibration without retraining

The engine is an LLM, so you cannot "retrain" it. But you can **calibrate it post hoc**. On logged data, fit a simple monotone map from the raw LLM probabilities to calibrated probabilities. Use Platt scaling (logistic regression on the logit of p), or isotonic regression if you have 500 points or more. The LLM gives the *ranking and the reasoning*. A one-line statistical map corrects the *levels*. This combination is usually much better than more work on the prompt.

### Sample-size reality

To tell "my 15% bucket observes 15%" from "observes 8%", you need approximately **hundreds of predictions per bin region**. At the start, use 3–4 coarse bins, and show the error bars. Do not make a conclusion that a binomial test does not support. A calibration claim from 30 predictions is the same error as a Mode 2 discovery.

---

## 4. The Dixon–Coles goal model

### Why model goals at all when the target is comebacks?

Because both target markets are **functionals of the goal process**:

- P(7+ goals) is the tail of the total-goals distribution.
- P(comeback) = Σ over HT scorelines of P(trail at HT) × P(overturn in the 2nd half).

A binary classifier on `is_comeback` learns from 23 positives per league-season. A goal model learns its parameters from **every goal in every match**. Then the probabilities of the rare markets are *calculated*, not estimated directly. This is the largest gain in data efficiency that this project can get.

### The base model (independent Poisson)

Each team has an **attack** strength `α_i` and a **defence** weakness `β_i`. The league has a **home advantage** `γ`. The goals in a match between home team i and away team j:

```
X_home ~ Poisson(λ),   λ = α_i · β_j · γ        (home goals)
X_away ~ Poisson(μ),   μ = α_j · β_i            (away goals)
```

The model needs an identification constraint (for example, the mean of all α's = 1). Fit it by maximum likelihood: maximise `Σ_matches [ log Pois(x_home; λ) + log Pois(x_away; μ) ]` over all α, β, γ. That is ~2·(number of teams)+1 parameters, which `scipy.optimize.minimize` fits easily on 380 matches or more. Then P(any exact scoreline h–a) = `Pois(h; λ) · Pois(a; μ)`. Each market is a sum over scorelines.

### The two Dixon–Coles (1997) corrections

1. **The low-score dependency (tau).** Real football is different from independence exactly at 0–0, 1–0, 0–1 and 1–1. It has slightly more draws and fewer 1–0s than independent Poissons predict. DC multiply those four scoreline probabilities by a correction `τ(h, a; λ, μ, ρ)`, with one extra parameter ρ:

   ```
   τ(0,0) = 1 − λμρ      τ(1,0) = 1 + μρ
   τ(0,1) = 1 + λρ       τ(1,1) = 1 − ρ
   ```

   (Usually ρ ≈ −0.1. With ρ = 0, the model is independent again.) It is most important for 1X2 and draw prices, and less important for totals.

2. **Time decay.** Team strength changes slowly. So give the log-likelihood of match `m` the weight `exp(−ξ · t_m)`, where `t_m` is the number of days before now. Choose the ξ that gives the highest *out-of-sample* predictive likelihood (usual half-life: ~one season, ξ ≈ 0.002–0.005/day). So the model stays current, without a sliding window that discards data.

### The per-half adaptation (this project's version)

The comeback market depends on the difference between the halves. This repo already stores `goals_1h`, `home_2h_goals` and `away_2h_goals`. So fit **two linked models**:

- A first-half model → a distribution over HT scorelines (λ₁, μ₁).
- A second-half model → a distribution over 2H goals (λ₂, μ₂). If possible, add a **state adjustment**: 2H scoring rates that depend on the HT state. In the data, teams that are behind at HT score at a higher rate, and leaders defend deeper. Start simple: one multiplicative factor per HT state (leading / level / trailing), so 2–3 extra parameters. Do this before anything more complex.

Then, exactly:

```
P(home comeback) = Σ over HT scorelines (h₁ < a₁) of
                     P(h₁, a₁ | 1H model)
                   · P(2H goals overturn the deficit | 2H model, state = home trailing)

P(7+ goals)      = Σ over (h, a) with h + a ≥ 7 of P(h, a | full model)
```

Stop the scoreline sums at ~10 goals per team. The probability mass after that is negligible.

**Where shrinkage comes back:** the per-team 2H multiplier for the trailing state is exactly the "comeback-prone" trait. Now it is inside a model that uses all matches. But it is a per-team parameter from little data. So shrink it (fit a hierarchical prior). Or use one multiplier for the whole league until the persistence test (§1) proves that teams really differ.

### Cautions specific to Dixon–Coles

- **It knows nothing about news**: injuries, rotation, motivation. That is the intended division of work here. DC gives the *statistical anchor*. Odds movement and the web-search layer give the *news adjustment* (through the LLM's bounded anchor-and-adjust, HANDOFF §7.2).
- **Promotion/relegation:** newly promoted teams have no top-flight history. Start their strengths from the average of promoted teams, not from the league average.
- **Overdispersion:** raw Poisson gives slightly too few very high scores. This is important for the 7+ market. If the model's P(7+) is below the observed 1.84%, think about a negative-binomial variant. But do this only after the multi-league data set confirms the gap out of sample.
- **Validate it like everything else:** walk-forward by season, with Brier and calibration on the derived market probabilities (§2, §3). An elegant goal model must also go through the evaluation loop.

---

## 5. How the four tools fit together here

The full loop, from start to end:

1. **Dixon–Coles (per half)** makes the scraped goal archive into a calibrated *statistical anchor*: P(comeback) and P(7+) per match, calculated, not guessed.
2. **Empirical Bayes shrinkage** gives honest team-level traits (recovery rates, 2H supremacy, blown leads) for the league context card. The sample sizes are visible, and the effect of luck is small.
3. The **LLM engine** starts from the anchor (1). It adjusts the anchor within limits, with the shrunk traits (2), the odds movement and structured news. Then it gives a probability.
4. **Brier scores** (against the base-rate and market benchmarks) and **calibration curves** on the logged predictions decide what stays. Every feature, prompt change and model version must improve the skill score, or it is removed.

One sentence per tool:

- *Shrinkage keeps the inputs honest.*
- *Dixon–Coles lets you estimate rare markets from all the data.*
- *Brier keeps the score.*
- *Calibration curves tell you if you can believe the score.*

### Suggested reading (if internet access is available)

- Dixon & Coles (1997), *Modelling Association Football Scores and Inefficiencies in the Football Betting Market*, JRSS-C — the original paper, and easy to read.
- Efron & Morris (1977), *Stein's Paradox in Statistics* (Scientific American) — the classic shrinkage story about baseball batting averages. It is exactly this project's Villa problem.
- Any text on Murphy's (1973) Brier decomposition, for the split into reliability, resolution and uncertainty.
