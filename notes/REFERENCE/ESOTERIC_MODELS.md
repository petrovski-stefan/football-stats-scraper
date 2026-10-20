# ESOTERIC_MODELS.md — The Back-Shelf Toolbox

**Group: Reference.** Change it only to correct or extend it. Keep the headings and numbers, because other files cite them.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

This file keeps seven less common statistical tools. Each tool has a *specific* use in this project. Companions: `HANDOFF.md` (strategy) and `STATS_PRIMER.md` (core methods).

No tool is on the critical path: the roadmap in `HANDOFF.md` §9 comes first. But each tool is the correct upgrade at a known time in the future. The **"Reach for this when"** line of each tool gives that time.

The tools are in the order of their expected use to this project.

---

## 1. Shin's method — correct vig removal on long odds

**What it is.** The simple method to remove a bookmaker's margin is proportional normalisation: divide each `1/odds` by `Σ(1/odds)`. Shin (1993) made a model of a bookmaker who must protect the book against *insider traders*. He showed that the margin is not spread evenly. The bookmaker puts more of it on **long odds**, because informed money causes the largest losses there. His method calculates the insider fraction `z`. Then it calculates the true probabilities from the quoted odds.

**Why it matters here.** This project's markets (the HT/FT comeback, 7+) have long odds. On long odds, proportional normalisation has its largest error. So the engine can seem to have an edge over a proportionally normalised implied probability. That "edge" can be only vig in the wrong place.

**Concrete use.** Use a Shin adjustment in place of `stats.implied_prob` and proportional normalisation. Do this everywhere that the engine's output is compared with market prices (HANDOFF §7.6). The algebra fits on one page. The solution is iterative. Use the `shin` package from PyPI, not code of our own (the user, 2026-10-14).

**Reach for this when:** the project collects closing odds or HT/FT odds, and builds its first comparison of a model with the market.

---

## 2. The favourite–longshot bias — measure the bias against you first

**What it is.** It is the most robust empirical anomaly in betting markets. Research has recorded it for a century. Bettors consistently pay too much for long odds. So the quoted long odds are *shorter* than fair odds. A comeback with a true chance of 5% can have the price of a 7–8% chance.

**Why it matters here.** On long odds, the consistent error of the market goes *against* the bettor. This project works on those markets. The bias is the structural reason why "pre-match directional completion may be unbeatable" (HANDOFF §9.5, §10).

**Concrete use.** When closing odds from many leagues exist:

1. Put all matches into buckets by decile of implied probability.
2. In each bucket, compare the implied frequency with the observed frequency.

One table then gives the size of the bias in *this* data set. It also shows the minimum edge that a model needs against the bias.

**Reach for this when:** the archive holds about 2,000 matches or more with closing odds.

---

## 3. The match as an absorbing Markov chain — a comeback as an absorption probability

**What it is.** Make a model of the score state (level, home +1, away +1, ±2, …) as a Markov chain over the minutes of the match. Estimate its transition intensities. A comeback is a property of the *path*. Start from the state "behind by 1 at minute 45". The comeback chance is then the probability of absorption in the state "the trailing team wins" at full time.

**Why it matters here.**

- It gives the HT-conditional product directly (HANDOFF roadmap item 6).
- It estimates the transition intensities from **every goal in every match**. This is the same argument for data efficiency as for Dixon–Coles, at a finer level.
- It splits "equalize but not win" (HANDOFF §2) into two transitions, and each transition can have its own model:
  - behind → level is common: 21.8% of the teams that are behind by 1 at HT end in a draw;
  - level → a late win is rare. This step is the real limit.

**Concrete use.** Version 1 needs no new data: a 9-state HT→FT transition matrix from the existing `ht_result` and `ft_result` columns. Version 2 (by minute) needs goal timings.

**Reach for this when:** you build the HT-conditional evaluator. For the minute level, use the goal store of the live page (`scrapers.goals`). The project has scraped it since September 2026.

---

## 4. Survival analysis on leads — the hazard rate of the equaliser

**What it is.** Treat a half-time lead as a subject, and the equaliser as the event. Fit a hazard curve over minutes 45–90. Use three covariates: the size of the deficit, the leader's blown-lead profile, and the trailing team's 2H supremacy. The standard tool is Cox proportional hazards.

**Why it matters here.** The scoring rate *increases* during a match. About 10% of goals come in the first 15 minutes. About 14% or more come in the last 15, and more with added time. Game-state effects make this larger: teams that are behind attack more, and leaders defend deeper. So, by the structure of the match, the late minutes are the comeback window. A lead-survival model shows *which leads are fragile*. That is the correct statement of the completion problem.

**Concrete use.** This was the best argument to add **goal timings** to the scrape. They come from the live page, not the detail page (`scrapers.goals`, since September 2026), and the DOM-only rule applies. The model also gives the team trait "share of goals after 75'". That trait measures comeback-proneness better than comeback counts do (HANDOFF §9.7).

**Reach for this when:** the project scrapes goal minutes. It does, since September 2026 (the live page). The re-scrape in the new format is IDEAS idea 2b.

---

## 5. Dynamic ratings from state-space models — form as a latent state

**What it is.** Form features from last-5 or last-10 windows are step functions: when a match leaves the window, the rating jumps. In place of the windows, make a model of team strength as a hidden state. The state changes by a small random walk each week. The results are noisy observations of the state (Rue & Salvesen 2000; Kalman-filter Elo variants).

**Why it matters here.**

- Old matches lose weight smoothly. There are no sudden steps at the edge of a window.
- The uncertainty is explicit. After a winter break, a team gets *wider error bars*, not an old point estimate.
- A promoted team starts with a large variance, not a guessed mean.
- The Dixon–Coles time decay ξ (STATS_PRIMER §4) is a special case of this model.

**Concrete use.** It is the upgrade for the `*_recent_*` window features, after they show signal but are too coarse. Put the filtered strength states into the matchup card, in place of the raw window aggregates.

**Reach for this when:** form features from windows show signal in the gate retro-tests, and their sudden jumps become the limit. Not before: windows are sufficient at the start.

---

## 6. Pythagorean expectation — a luck check for the league table

**What it is.** It is Bill James's estimator from baseball, changed for football. The expected share of points is `GF^c / (GF^c + GA^c)`, with c ≈ 1.3. The residual (actual points − Pythagorean points) shows luck. Teams above their expected points usually move back down toward them. Teams below them usually move back up.

**Why it matters here.** It has two uses:

1. A better strength input for the matchup card than the raw table position.
2. A **motivation corrector**. Take a team that is 8th in the table but 14th by Pythagoras. Its underlying numbers look like those of a team near relegation. That is desperation asymmetry (a Mode 2 hypothesis, HANDOFF §3). People who read only the table give it the wrong price.

**Concrete use.** One calculated column in the league context card. You can calculate it today from the goal data that exists. It is the cheapest item in this file.

**Reach for this when:** you build the context-card generator (HANDOFF roadmap item 2).

---

## 7. Kelly as epistemology — a score for the project, in nats

**What it is.** This is the deep form of the Kelly criterion, not its rule for the size of a bet. The long-run log growth rate of a Kelly bettor is equal to the **KL divergence between your probability distribution and the market's**.

**Why it matters here.** No money is necessary. Simulate the log-Kelly growth of the engine's probabilities against Shin-adjusted closing odds. The result is one number. It measures *how much more the model knows than the market*. Zero is a valid finding, and you can publish it: "the market already knows everything the scraper can see."

**Concrete use.** When closing odds exist, add the simulated flat-Kelly log growth to the evaluation loop (HANDOFF §7.5), next to Brier and calibration. It is the metric for the final verdict on the whole project.

**Reach for this when:** the loop that logs and scores predictions runs, and the archive holds closing odds.

---

## Notes for all tools

- **The order of the tools:**
  - Tools 1–2 make sure that prices do not give you false conclusions.
  - Tools 3–5 make a model of the *real structure of the match*.
  - Tool 6 checks the table.
  - Tool 7 gives a score to the whole project.
- Most of these tools have one purpose: with better mathematics, they stop you from believing more than the data shows.
- All tools obey the standing rules:
  - DOM-only scraping;
  - walk-forward validation;
  - shrink the team parameters that come from small samples;
  - no tool goes into use unless it improves the Brier, calibration or Kelly results (STATS_PRIMER §5).
- References: Shin (1993, *Economic Journal*) on insider trading and odds; Rue & Salvesen (2000, *The Statistician*) on dynamic football models; Cox (1972) proportional hazards; Kelly (1956) *A New Interpretation of Information Rate*; the favourite–longshot bias survey in Ottaviani & Sørensen (2008).
