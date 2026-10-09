# LEAGUE_STUDY.md — The 23,000-Match Study

**Corpus:** football-data.co.uk main catalog, 22 divisions across 11 countries, seasons
2023-24 → 2025-26. **23,127 matches, 1,191 comebacks (5.15%), 476 seven-plus (2.06%).**
All odds are Bet365 closing unless stated. Data quality: 5 rows missing HT scores in the
entire corpus; Bet365 closing 1X2 essentially complete everywhere (raw files in
`football-data-co-uk/<country>/<season>/` — that corpus was retired from the repo on
2026-07-26; see notes/MARKET_LINE_FINDINGS.md S5 to re-fetch it).

**Coverage caveat:** these 11 countries are roughly **one fifth of Europe's ~50 football
nations** — the strongest fifth, but a fifth. Findings marked *(surveyed fifth)* are
proven only inside this corpus; extending them to the remaining ~30 countries (Balkans,
Scandinavia beyond the catalog, Baltics, Caucasus, etc.) is the mission of the planned
nowgoal multi-league scraping campaign — football-data.co.uk cannot cover it (its Extra
files lack HT scores). Note, however, that the surveyed fifth spans tiers 1–5 of the
continent's deepest pyramids, so "unsurveyed" means untested, not likely-different.

This study was the proof-of-concept for the methods in `HANDOFF.md`, `STATS_PRIMER.md`
and `ESOTERIC_MODELS.md`. Several beliefs held before it — including some recorded in
those documents — **did not survive contact with the corpus.** Findings below are ordered
by how much they change the plan. Where a finding contradicts an earlier document, this
file wins.

**Scope decision (July 2026):** the project's hypothesis is **pre-match prediction
only** — no live / in-play (post-half-time) betting. F1–F9 are population measurements;
F10–F13 are the modeling verdicts under that scope, all walk-forward tested (train
2023-25, test untouched 2025-26).

---

## F1. Leagues do NOT differ in comeback rate — league selection is dead *(surveyed fifth)*

- Chi-square, league × comeback over 23,127 matches: χ² = 26.7, dof = 21, **p = 0.18**.
- Empirical-Bayes shrinkage (method of moments across 66 league-seasons) estimates the
  between-league s.d. of *true* comeback rates at **≈ 0.08 percentage points**. Every
  league's shrunk rate lands in 5.1–5.2%.
- Persistence test — rank leagues on 2023-24+2024-25, verify on 2025-26:
  **Spearman r = 0.108, p = 0.63.** League rankings do not persist.
- The raw table runs from POR Liga 3.8% to ENG Premier League 6.7% — the two leagues this
  project happened to examine first, a live demonstration of the winner's curse. An
  earlier two-league comparison (England vs Portugal, z = 2.09) looked significant
  precisely because those are the extremes among 22 draws.

**Consequence:** within the surveyed fifth there is nothing to select on — do not build
a comeback-league selector from this corpus. The remaining ~30 European countries are
untested; the extension survey (via the nowgoal scraper) is legitimate **only under the
preregistered bar** set before any of that data is seen:

> A league becomes a comeback-candidate only if it shows **≥ 8% comeback rate over
> ≥ 600 matches**, survives a select-on-early-seasons / verify-on-latest-season
> persistence test, **and** has a mechanism story. Rationale: under a pure null, the
> maximum among ~50 leagues of ~600 matches lands near 7% by luck alone — anything
> below the bar is the England-vs-Portugal winner's curse repeating.

Until a league clears that bar, scrape leagues for *other* reasons (market softness —
F8; over-6.5 structure — F9; data availability).

## F2. Team-level comeback-proneness is dead

621 team season-pairs (same league, consecutive seasons): Spearman(comebacks in season t,
season t+1) = **0.068, p = 0.09**. Teams in the top quartile at t average 1.08 comebacks
at t+1 vs 0.97 for everyone else — against a corpus mean of 1.00 per team-season.
The "Aston Villa flag" (HANDOFF §3) is formally buried. Any comeback-proneness feature
must be built from mechanisms (2H goal share, blown-lead profile, bench/manager effects),
never from comeback counts.

## F3. Comeback rate is invariant in match balance — the balanced-match precondition is dead

Pooled comeback rate by closing favorite odds is **flat** (~5%) from odds 1.0 to 10
(corr r = 0.002, p = 0.81), and flat across |AH| lines. A single-season E0 gradient
(3.3% → 8.0%) did not replicate; nor did a "comebacks vanish at |AH| ≥ 1.75" claim.
The flatness is a cancellation of opposing gradients:

| fav odds  | P(HT non-draw) | P(fav is the trailer) | P(trailer wins) | P(comeback) |
|-----------|---------------|----------------------|-----------------|-------------|
| [1.0,1.3) | 0.716         | 0.128                | 0.071           | 0.051       |
| [1.7,1.9) | 0.591         | 0.338                | 0.091           | 0.054       |
| [2.4,10)  | 0.548         | 0.485                | 0.096           | 0.053       |

Lopsided match: someone trails often, but it's the dog, who can't finish. Balanced match:
trailing is rarer, but the trailer is a coin-flip team who can. Product ≈ constant.

**Consequence:** *unconditional* P(comeback) is unpredictable from match balance. All
predictive structure lives in the conditional stage — F4.

## F4. The crown jewel: completion is a steep function of the trailing team's own strength

Among matches with a −1 half-time deficit (n = 9,969), the trailer's closing 1X2 odds
predict completion over a **10× range**, monotone in every octile:

| trailer's closing odds (median) | n | completes (wins) |
|---|---|---|
| 1.65 | 1,303 | **25.6%** |
| 2.10 | 1,366 | 14.9% |
| 2.45 | 1,109 | 13.2% |
| 2.80 | 1,286 | 10.2% |
| 3.30 | 1,193 | 9.2% |
| 3.90 | 1,364 | 6.7% |
| 5.00 | 1,149 | 4.8% |
| 8.00 | 1,199 | **2.6%** |

corr(log trailer odds, completes) = −0.198, p ≈ 4e-121. Related corpus anchors:

- Deficit size: trail −1 → 11.1% win / 22.9% draw; trail −2+ → 2.4% win / 6.3% draw.
- 62% of all comebacks are completed by the closing favorite (median comeback-team odds 2.30).
- Venue: home teams trailing −1 complete **14.0%** vs away teams **8.7%** — resolved in
  F11: the venue gap is *fully absorbed by the trailer's closing odds* (logistic venue
  coefficient ≈ 0). Venue is not a separate feature; the market already priced it.

**Consequence:** the prediction target should be reframed. Pre-match, "will there be a
comeback" ≈ "will a strong team trail at HT" — so the engine's job is
P(fav trails at HT) × completion-curve(trailer strength, deficit, venue). This is the
HT-conditional product (HANDOFF roadmap item 6) with its parameters now measured.

## F5. The 9-state HT→FT Markov matrix (context-card core, ESOTERIC #3 v1)

Row = HT state, column = FT result, % of row (n = 23,121):

| HT \ FT | H | D | A |
|---|---|---|---|
| **H** (n=7,799) | 76.8 | 16.5 | 6.7 |
| **D** (n=9,401) | 35.6 | 37.7 | 26.6 |
| **A** (n=5,921) | 11.3 | 20.8 | 67.9 |

P(trail→win) varies across leagues only from 6.6% to 10.8% (s.d. 1.3pp, mostly sampling
noise per F1). One matrix serves all leagues until proven otherwise.

## F6. The favorite–longshot bias, measured on 69,366 closing prices (ESOTERIC #2: done)

Flat 1-unit bet ROI at Bet365 closing odds, monotone throughout:

| odds | n | implied | actual | ROI |
|---|---|---|---|---|
| 1.0–1.3 | 1,212 | .835 | .828 | **−0.8%** |
| 1.6–2.0 | 7,055 | .561 | .524 | −6.6% |
| 2.5–3.2 | 11,904 | .354 | .327 | −7.5% |
| 4.5–7 | 7,518 | .193 | .173 | −10.9% |
| 7–12 | 2,494 | .122 | .090 | **−27.5%** |
| 12+ | 686 | .068 | .038 | **−42.6%** |

HT/FT comeback markets price at 8.0–30.0 — squarely in the −27% to −43% zone. This is
the definitive quantification of HANDOFF §10's warning: pre-match directional comeback
betting fights a structural headwind that no plausible model edge overcomes. The
project's product is calibrated probabilities and in-match understanding, not longshot
tickets.

## F7. Comebacks are deserved, not lucky

Across 1,104 comebacks with shot data, the comeback team took **57.6%** of the match's
shots (t = 17.5, p ≈ 9e-61) — *more* than the average match winner (55.2%). Comebacks
are dominance eventually expressed, not variance. Features about sustained pressure
(shots, corners as proxy) are on-signal.

## F8. Market efficiency varies by league — relevant for CLV, not for comebacks

Open→close Brier information gain (how much the market learns pre-kickoff), top:
GRE Super League (.0068), SCO Championship (.0064), POR Liga (.0046), ENG PL (.0044).
Bottom (≈0): GER Bundesliga, FRA Ligue 1, SCO Premiership, GER Bundesliga 2. Closing vig
runs 5.5% (top-5 leagues) to ~10% (Scottish lower divisions). Late-arriving-information
leagues are where a 1-day-before web-search feature and CLV-based evaluation have the
most room. Fat vig ≠ soft prices, though — Scottish lower leagues combine both, Greece
combines low-ish vig with high info gain (most attractive).

## F9. The over-6.5 market DOES have league structure — league selection lives here

Unlike comebacks: 7+ × league χ² = 79.6, **p = 9e-9**, and league 7+ rate correlates
r = 0.84 with goals/match. GER Bundesliga 2 3.8%, NED Eredivisie 3.6%, GER Bundesliga
3.5% vs ITA Serie A 0.9%, GRE Super League 0.7% — a 5× spread. The secondary market is
where "pick your league" is a real strategy: German and Dutch football, structurally.

## F10. The pre-match feature graveyard is complete *(surveyed fifth)*

Every pre-match variable available in (or derivable from) this corpus has now been
tested against comebacks. The full census:

| pre-match variable | result |
|---|---|
| League identity | dead (F1) |
| Team comeback history (season counts) | dead (F2) |
| Last-match market flags (BTTS/O2.5/HT-O2.5/7+/comeback, alone and in all 45 AND-pairs) | dead — 0 of 90 tests survive correction |
| Match balance: favorite odds, \|AH\| line | dead (F3) |
| Rest days (min, differential, trailer's own) | dead (p = 0.77 / 0.15 / 0.48) |
| Calendar: month, round-of-season | dead (p = 0.27 / 0.099) |
| Odds movement open→close (magnitude, direction) | dead (p = 0.89 / 0.33) |
| Rolling last-5 shot share | priced — dies once own closing odds are controlled (partial p = 0.73) |
| Rolling last-5 goals scored | survives screens (partial r = +0.015, p = 0.005 after odds control) — **but adds zero Brier in walk-forward (F12)** |
| **Implied totals (O/U 2.5 closing price)** | **the one live dial**: comeback rate 4.2% → 6.8% across octiles (r = +0.028, p < 0.001) |

The totals dial is *mechanical*, not tactical: implied P(over 2.5) predicts more
non-draw half-times (r = +0.103) but **not** completion given trailing (r = +0.011,
p = 0.19). Goal-rich fixtures create more trailing states; they don't help trailers
recover. Jointly with strength (which regains a small additive term once totals are
controlled, p = 0.001; no interaction, p = 0.22), grid cells span 4.1%–7.3% — that
range is the *ceiling* of pre-match comeback knowledge in this corpus.

Related: second halves carry **55.5%** of all goals with a remarkably tight league range
(53.7%–57.0%) — "late-goal leagues" don't exist as a real axis (corr with completion
rate p ≈ 0.15 across 22 leagues). One more spoke in the wheel of comeback mechanics
being league-invariant.

## F11. The half-time completion model — the conditional stage works (measured, walk-forward)

F4 as a fitted product: logistic P(trailing team wins | log trailer odds, deficit,
venue), trained on 9,195 trailing states (2023-25), tested on 4,526 (2025-26):

- **Held-out Brier 0.0704** vs 0.0749 constant and 0.0735 deficit-only — real skill.
- Predictions span 0.6%–39% and **calibrate decile by decile** across the whole 40×
  range (bottom decile predicted 0.6% / observed 0.7%; top predicted 24.9% / observed 23.3%).
- Coefficients: log(trailer odds) −1.72, deficit −1.27, venue **+0.001** — the F4
  home/away asymmetry is entirely inside the odds.
- Drift caveat: 2025-26 ran comeback-poorer than training (8.15% vs 8.94% base), so the
  model mildly overpredicts globally; an annual intercept refit is part of the product.
- Secondary target (trailing team salvages ≥ draw): even larger relative skill
  (Brier 0.170 vs 0.195 constant).
- Slate shape at threshold P ≥ 0.22: ~9 alerts/week across 22 leagues, 24.0% observed hit rate.

**Under the pre-match-only scope this model is a *component*, not a product** — its
inputs include the half-time state. Its legitimate pre-match use is inside F12's chain
(integrated over half-time states that haven't happened yet).

## F12. The pre-match comeback PoC — built honestly, and it failed *(surveyed fifth)*

The strongest pre-match model this corpus permits was built and walk-forward tested:
**chained pricer** P(comeback) = Σ_d P(trail by d at HT | closing odds) ×
F11(recover | odds, d), with the first factor from two Poisson regressions on 1H goals
(Skellam). Benchmarks: constant, direct logistic (totals + strength + balance), direct +
rolling-form. Held-out 2025-26, n = 6,630:

| model | Brier |
|---|---|
| constant (train rate 5.3%) | 0.04812 |
| direct logistic (odds features) | 0.04814 |
| direct + rolling form | 0.04813 |
| chained (best) | 0.04809 |

**Nothing beats "always say 5%" by more than rounding error.** The chained model's
top-decile slate — its 663 most confident picks, predicted 6.4% — delivered **4.5%
observed**, below the unfiltered base rate and below its own binomial lower bound. The
rolling-form signal that survived F10's screens evaporated. The model's entire fair-odds
range was 16-to-1 vs 22-to-1 — unmonetizable even if it had validated, and squarely
inside F6's −27%..−43% longshot zone.

**Consequence — the scope verdict:** within the surveyed fifth, pre-match comeback
prediction is refuted *by construction* (the best possible model was built and cannot
out-predict a constant), not merely by correlation tables. The hypothesis has exactly
one refuge: the ~30 unsurveyed European countries, reachable only by the nowgoal
scraper, judged by F1's preregistered bar.

## F13. The pre-match over-6.5 model — the same pipeline, pointed at the market that works

Identical discipline (train 15,475 / test 7,647): logistic on implied P(over 2.5) +
favorite strength + train-only league goal environment:

- **Held-out log-loss 0.0899 vs 0.0931 constant (−3.5%)** — roughly 20× the relative
  skill the comeback model managed. Brier 0.01822 vs 0.01836. A Poisson-tail benchmark
  (P(N≥7) from odds-fitted goal rates) lands close behind (0.01832).
- Predictions span 0.24%–17.9% and the **ranking validates**: bottom decile observed
  0.78%, top decile 3.66%, against a 1.87% test base — a 2× lift at the top, 0.4× at
  the bottom.
- Honest flaw: the very top decile overpredicts (5.6% predicted vs 3.7% observed) — the
  tail needs shrinkage/regularization; and 2025-26 ran goal-poorer than training
  (1.87% vs 2.15%), the same downward drift F11 saw.

Combined with F9 (real league structure) this is the pre-match product the corpus
actually supports: a calibrated rare-event predictor for over 6.5, today.

---

## Reading this study for a pre-filtered prediction workflow

The population rates above (5.15% unconditional, flat everywhere) describe the *whole*
corpus — but no real prediction workflow bets the whole corpus. In practice the engine
will run on a **pre-filtered candidate slate** (a shortlist of matches chosen by some
rule), and the study should be read accordingly:

1. **The unconditional 5% is the prior, not the operating condition.** Filtering is
   exactly how the rate is supposed to move. The study's contribution is telling you
   *which filters move it and which don't.*
2. **Filters proven to give no lift** (do not build slates from these): league identity
   (F1), the team's own comeback history (F2), match balance / favorite odds / AH line
   as an unconditional cut (F3). A slate built on any of these has the same ~5% hit
   rate as a random slate — measured, not conjectured.
3. **Filters with measured lift** (build slates from these): everything conditional on
   the half-time state — trailer's pre-match strength (2.6% → 25.6%, F4), deficit size
   (−1 vs −2+: 11.1% vs 2.4%), venue of the trailer (14.0% home vs 8.7% away). These
   only activate at half-time, which is why the HT-conditional product (HANDOFF item 6)
   is the natural shape of the predictor.
4. **Any new filter must pay rent.** A candidate pre-filter is itself a model: measure
   its slate's comeback rate on held-out (later) seasons against the 5.15% prior, with
   the slate's own n setting the error bars. A filter that selects 50 matches a season
   needs years of data before a 8-vs-5% difference means anything — see the
   preregistered bar in F1.
5. **Filtering does not escape F6.** The bookmaker prices each match with the same
   public information a pre-filter uses; a slate with a genuine 8% rate will find its
   HT/FT prices already shorter. The longshot headwind applies to the *slate*, not just
   the corpus — which is why the deliverable stays calibrated probabilities, evaluated
   by Brier/calibration on the slate, not tickets.

---

## Appendix: comeback leaderboards (counts, with health warnings)

Raw counts, kept for reference and intuition. Counts favor long seasons (English lower
divisions play 552 matches vs 306–380 elsewhere), and per F1/F2 none of these rankings
is predictive — the team table in particular is **F4 wearing a jersey**, not a list of
"comeback DNA" clubs.

**League-season, most comebacks:**

| league, season | comebacks | matches | rate |
|---|---|---|---|
| ENG League Two 2023-24 | 35 | 552 | 6.3% |
| ENG Championship 2025-26 | 34 | 552 | 6.2% |
| ENG Championship 2024-25 | 31 | 552 | 5.6% |

One league's rows were removed from this list on 2026-10-08, at the user's request. Every
figure in this study, these counts included, was measured with it in the corpus.

**Team-season, most completed comebacks:** four-way tie at **5** — Fulham (PL 2024-25),
Fenerbahçe (TUR 2024-25), Man City (PL 2023-24), Southampton (Championship 2025-26).
Aston Villa: 4 (PL 2025-26).

**League, three seasons merged:** by count, ENG Championship 93/1,656 (5.6%); by rate,
ENG Premier League 76/1,140 (6.7%) — the F1 winner's-curse extreme, not a real property.

**Team, three seasons merged:**

| team | league | comebacks |
|---|---|---|
| Fenerbahçe | TUR Süper Lig | **12** |
| Barcelona | ESP La Liga | 9 |
| Real Madrid, Celta | ESP La Liga | 8 |
| Aston Villa | ENG Premier League | 8 |
| Bolton, Rodez, Fortuna Düsseldorf | (League One / Ligue 2 / Bundesliga 2) | 8 |

Reading: the top of the merged table is dominated by perennial heavy favorites
(Fenerbahçe, Barcelona, Real Madrid, Man City) — exactly the "62% of comebacks are
completed by the closing favorite" mechanism (F4). The mid-table oddities (Bolton,
Rodez) are the noise F2 predicts: ~2.7 comebacks/season vs a corpus mean of 1.0, with no
season-to-season persistence. Fenerbahçe's 4-per-season-every-season is the only
striking entry, and has a boring candidate explanation: a dominant club in a chaotic
league is near-permanently the stronger side when trailing.

---

## What this changes in the standing documents

1. **HANDOFF §2 market-math table** was measured on 380 PL matches; corpus values
   supersede it (comeback 5.15%, trail−1→win 11.1%, trail−1→draw 22.9%, 7+ 2.06%).
2. **HANDOFF's favorite-odds split** (comeback 3.2% at fav<1.5 vs 9.2% at ≥2.2) was a
   one-season artifact — F3 kills it as an unconditional feature. It survives only in
   conditional form (F4).
3. **Comeback-prone team flag**: F2 closes the question. Remove from the feature roadmap.
4. **League selection**: redirect the effort from "comeback-prone leagues" (F1: none) to
   over-6.5 league targeting (F9) and market-softness targeting (F8).
5. **ESOTERIC #2 (fav–longshot)** and **#3 v1 (Markov matrix)** are no longer future
   items — measured here (F6, F5).

## Methodology notes

- **Provenance / no cherry-picking.** Neither the matches nor the columns were selected
  by the project owner, and none were selected in response to results. The corpus is the
  *complete* football-data.co.uk main catalog for 2023-26 — all 66 files, every match
  with a half-time score (5 rows dropped for missing `HTR`), zero other exclusions. The
  comeback definition was fixed *before* any corpus analysis: columns `HTR`/`FTR` only,
  formula `(HTR=="A" & FTR=="H") | (HTR=="H" & FTR=="A")` — the same rule as
  `stats.is_comeback_home/away` in the scraper pipeline, written weeks earlier.
  Independent verification: the E0 2025-26 file reproduces the project's own scraped PL
  CSV exactly (23 comebacks, 11 home / 12 away, 7 seven-plus). Every negative finding
  (F1–F3) was a hypothesis the project *wanted* to confirm; the data refused.
- All rates are pooled 3-season; league comparisons use chi-square on counts, shrinkage
  via Beta-Binomial method of moments (μ = 0.0515; between-league component ≈ 0 forces
  k ≈ 77,000 — i.e., the data itself says "use the pooled rate").
- Persistence = Spearman rank correlation across seasons (leagues) or season-pairs (teams).
- No walk-forward needed here: nothing in this file is a fitted predictive model; these
  are population measurements. The moment a model is fit on this corpus, HANDOFF §6
  applies (walk-forward only, no shuffled CV).
- Analysis scripts live in the session scratchpad; the corpus loader normalizes the 66
  raw CSVs (Bet365 columns are complete; Pinnacle is NOT — it vanishes mid-2025-26).

## The one-paragraph verdict

Comebacks are a ~5% phenomenon everywhere *we have looked* (one fifth of Europe, tiers
1–5) — invariant across leagues, seasons, teams, and match balance. What varies, enormously and predictably, is **who completes**: a
trailing team's pre-match strength moves completion from 2.6% to 25.6%, favorites
complete 62% of all comebacks, home trailers nearly double away trailers, and comeback
teams out-shoot even ordinary winners. Prediction must therefore be conditional
(HT-state product), the market's longshot pricing makes directional pre-match betting
structurally unprofitable (−27% to −43% ROI zone), and the honest opportunities that
remain are: calibrated conditional probabilities, the over-6.5 market's real league
structure (Germany/Netherlands), and soft-market CLV experiments (Greece, Portugal,
Scottish lower divisions).
