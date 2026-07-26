# ESOTERIC_MODELS.md — The Back-Shelf Toolbox

Companion to `HANDOFF.md` (strategy) and `STATS_PRIMER.md` (core methods). This file
preserves seven less-common statistical tools, each with a *specific* use case in this
project. None are on the critical path — the roadmap in `HANDOFF.md` §9 comes first —
but each one is the right upgrade at a known future moment, noted per tool as
**"reach for this when…"**.

Ordering is by expected usefulness to this project.

---

## 1. Shin's method — proper vig removal for longshot markets

**What it is.** The naive way to strip a bookmaker's margin is proportional
normalization: divide each `1/odds` by `Σ(1/odds)`. Shin (1993) modeled a bookmaker
defending against *insider traders* and showed the margin is not spread evenly — it is
loaded onto **longshots**, because informed money hurts the book most there. His method
solves for the insider fraction `z` and recovers true probabilities from quoted odds.

**Why it matters here.** This project's markets (HT/FT comeback, over 6.5) are priced as
longshots — exactly where proportional normalization is most wrong. Comparing the
engine's probability to a proportionally-normalized implied probability can "find" edge
that is only misallocated vig.

**Concrete use case.** Replace `stats.implied_prob` + proportional normalization with a
Shin adjustment wherever the engine's output is benchmarked against market prices
(HANDOFF §7.6). One-page algebra; iterative solution; libraries exist (`shin` on PyPI).

**Reach for this when:** closing/HT-FT odds are being collected and the first
model-vs-market comparison is built.

---

## 2. The favorite–longshot bias — measure the headwind first

**What it is.** The most robust empirical anomaly in betting markets, documented for a
century: bettors systematically overpay for longshots, so quoted longshot odds are
*shorter* than fair. A true 5% comeback may be priced as if 7–8%.

**Why it matters here.** The market's systematic error on longshot markets runs
*against* the bettor — the tilt of the pitch this project plays on. It is the structural
reason "pre-match directional completion may be unbeatable" (HANDOFF §9.5, §10).

**Concrete use case.** Once multi-league closing odds exist: bucket all matches by
implied-probability decile, compare implied vs observed frequency per bucket. One table
quantifies the bias in *this* dataset and calibrates how much model edge is needed to
overcome it.

**Reach for this when:** ≥ ~2,000 matches with closing odds are archived.

---

## 3. The match as an absorbing Markov chain — comeback as absorption probability

**What it is.** Model the score state (level, home +1, away +1, ±2, …) as a Markov
chain over match minutes with estimated transition intensities. A comeback is a *path
property*: from state "trailing by 1 at minute 45", the probability of absorbing in
"trailing team wins" by full time.

**Why it matters here.**
- Directly produces the HT-conditional product (HANDOFF roadmap item 6).
- Transition intensities are estimated from **every goal in every match** — the same
  data-efficiency argument as Dixon–Coles, but finer-grained.
- Decomposes "equalize but not win" (HANDOFF §2) into two separately modelable
  transitions: trailing→level (common; 21.8% of −1 trailers end in a draw) and
  level→winning-late (rare; the actual bottleneck).

**Concrete use case.** v1 needs no new data: a 9-state HT→FT transition matrix from the
existing `ht_result`/`ft_result` columns. v2 (minute-level) needs goal timings.

**Reach for this when:** building the HT-conditional evaluator; upgrade to minute-level
once goal timings are scraped.

---

## 4. Survival analysis on leads — the hazard rate of the equalizer

**What it is.** Treat a half-time lead as a subject and the equalizer as the event; fit
a hazard curve over minutes 45–90 with covariates (deficit size, leader's blown-lead
profile, trailer's 2H supremacy). Cox proportional hazards is the standard tool.

**Why it matters here.** Football's scoring intensity *rises* through the match (~10% of
goals in the first 15 minutes vs ~14%+ in the last 15, more with stoppage time), and
game-state effects amplify it: trailing teams press, leaders retreat. The late-match
window is structurally the comeback window. A lead-survival model answers *which leads
are fragile* — the completion problem stated properly.

**Concrete use case.** The single best argument for adding **goal timings** to the
detail scraper (they typically render on match detail pages — DOM-only rule applies).
Also yields the "share of goals after 75'" team trait, a better comeback-proneness
measure than comeback counts (HANDOFF §9.8).

**Reach for this when:** goal-minute scraping lands.

---

## 5. Dynamic ratings via state-space models — form as a latent state

**What it is.** Instead of last-5/last-10 windows (step functions: a match falls out of
the window and the rating jumps), model team strength as a hidden state evolving by a
small random walk each week, observed noisily through results (Rue & Salvesen 2000;
Kalman-filter Elo variants).

**Why it matters here.** Smooth decay instead of window cliffs; explicit uncertainty
(a team after a winter break gets *wider error bars*, not stale point estimates);
promoted teams start with large variance instead of a guessed mean. Subsumes the
Dixon–Coles time-decay ξ (STATS_PRIMER §4) as a special case.

**Concrete use case.** Upgrade path for the `*_recent_*` window features once they prove
predictive but crude — feed filtered strength states into the matchup card instead of
raw window aggregates.

**Reach for this when:** window-based form features show signal in the gate retro-tests
and their jumpiness becomes the limiting factor. Not before — windows are fine to start.

---

## 6. Pythagorean expectation — the lie detector for the league table

**What it is.** Bill James's baseball estimator adapted to football: expected points
share from `GF^c / (GF^c + GA^c)` with c ≈ 1.3. The residual (actual points −
Pythagorean points) flags luck: over-performers regress, under-performers rebound.

**Why it matters here.** Two uses:
1. A better strength input than raw table position for the matchup card.
2. A **motivation corrector**: a team 8th in the table but 14th by Pythagoras has
   relegation-shaped underlying numbers — desperation asymmetry (a Mode 2 hypothesis,
   HANDOFF §3) that table-readers misprice.

**Concrete use case.** One computed column in the league context card, derivable today
from existing goals data. Cheapest item in this file.

**Reach for this when:** building the context-card generator (HANDOFF roadmap item 2).

---

## 7. Kelly as epistemology — scoring the project in nats

**What it is.** The Kelly criterion's deep form (not bet sizing): the long-run log
growth rate of a Kelly bettor equals the **KL divergence between your probability
distribution and the market's**.

**Why it matters here.** With no money involved, simulated log-Kelly growth of the
engine's probabilities against Shin-adjusted closing odds is a single number measuring
*how much more the model knows than the market*. Zero is a legitimate, publishable
finding: "the market already knows everything the scraper can see."

**Concrete use case.** Add simulated flat-Kelly log growth to the evaluation loop
(HANDOFF §7.5) alongside Brier and calibration, once closing odds exist. It is the
final-verdict metric for the whole project.

**Reach for this when:** the logging/scoring loop is live and closing odds are archived.

---

## Cross-cutting notes

- **The arc:** tools 1–2 are about *not fooling yourself with prices*; 3–5 model the
  *game's actual structure*; 6 audits the table; 7 scores the enterprise. The esoteric
  stuff is mostly rigorous humility with better math.
- Everything here obeys the standing rules: DOM-only scraping, walk-forward validation,
  shrink small-sample team parameters, and no tool ships without paying its way in
  Brier/calibration/Kelly terms (STATS_PRIMER §5).
- References: Shin (1993, *Economic Journal*) on insider trading and odds;
  Rue & Salvesen (2000, *The Statistician*) on dynamic football models;
  Cox (1972) proportional hazards; Kelly (1956) *A New Interpretation of Information
  Rate*; the favorite–longshot bias survey in Ottaviani & Sørensen (2008).
