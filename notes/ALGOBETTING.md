# Algobetting in Football — Conversation Summary

Notes from a deep-dive conversation on quantitative football betting: market structure, modeling lineage, the Asian handicap, comeback (HT/FT) markets, and feature engineering.

---

## 1. Why algobetting is real but hidden

- Any genuine edge decays when shared, so working methods stay private. Public discourse = tipsters and noise; serious work = private syndicates.
- Canonical examples: **Starlizard** (Tony Bloom, ~160 analysts) and **Smartodds** (Matthew Benham). Both founders bought football clubs (Brighton, Brentford) with betting profits.

## 2. Market structure — the first esoteric lesson

- **Sharp books** (Pinnacle, Asian books like SBOBet, brokers like Mollybet): huge volume, ~2% margins, welcome winners because winners sharpen their prices.
- **Soft books** (household names): fat margins, slow to reprice, ban winners quickly.
- Most retail-scale profit = exploiting the lag between sharp and soft prices.
- The **sharp closing line** is the closest thing to an efficient price in football.

### Closing Line Value (CLV)
- Variance is too high to judge yourself on profit over hundreds of bets.
- Instead: did you consistently beat the closing price? (Bet 2.10, closes 1.95 → you beat the close.)
- Core reframe: *you're not predicting matches, you're predicting where the price will move.*

## 3. The modeling lineage

1. **Poisson model** (Maher 1982): goals as independent Poisson processes from attack/defence strengths.
2. **Dixon & Coles (1997)** — the founding paper: correlation fix for low-scoring draws (0-0, 1-1) + exponential time-decay on past matches. Ancestor of almost every serious model.
3. Refinements: bivariate Poisson (Karlis & Ntzoufras), dynamic/state-space strengths (Rue & Salvesen), Bayesian hierarchical models.
4. **Modern layer**: xG / shot-based data (denser signal than goals, ~2.7 per match), possession-value models (VAEP, xT), player-level ratings rebuilt from likely starting XIs (enables instant reaction to lineup news).

### Unglamorous truths
- Data quality + feature engineering beat algorithm choice.
- Overfitting is the #1 killer (~380 matches/league/season).
- The model must be *less wrong than the margin*, not right. Hunt systematic biases: favourite–longshot bias, slow lineup repricing, small leagues, formula-priced derivative markets.
- **Staking**: fractional Kelly (e.g. quarter-Kelly) because your edge estimate is itself uncertain.
- **Execution** ("getting money down") is the truly hidden craft: account networks, Asian brokers, bots. Starlizard employs more traders than statisticians.

### Reading path
- Dixon & Coles (1997) — founding paper
- Joseph Buchdahl — *Squares & Sharps*, *Monte Carlo or Bust* (market efficiency, CLV)
- David Sumpter — *Soccermatics* (modeling intuition)
- Miller & Davidow — *The Logic of Sports Betting* (market structure)

## 4. Why algobettors target small leagues

- Edge is inversely proportional to smart money already in a market. EPL closing lines are near-efficient; the Norwegian second division is not.
- **Compiler effort scales with turnover**: minor-league prices are often semi-automated from shared third-party feeds (e.g. Betradar) — one feed error replicates across half the industry (systematic, exploitable).
- **Slow information diffusion**: local-language injury news can take hours to hit the price. Scraping local sources / paying local stringers = information asymmetry beats model sophistication.
- **Dumber competing money**: recreational locals, accumulator punters; lines move on sentiment.
- **The catch — liquidity cuts both ways**: limits are tiny and your own bets move the price.
- **Lifecycle**: incubate edges in small leagues (fat edges, low capacity) → forced up the food chain into Asian handicap markets on big leagues (thin edges, huge capacity). Small leagues: learn to fish. Big leagues: where the big fish are, armed.
- **Degrees of freedom**: in obscure leagues even one extra layer (xG, promotion/relegation motivation, artificial pitches, travel fatigue, cup rotation) can beat the compiler; in the EPL it's all priced.

## 5. Asian handicap (AH) — in depth

Origin: Indonesian/Malaysian markets; term coined by Joe Saumarez Smith (late 90s). Solves the draw problem — rebalances any mismatch to ~50/50.

### Mechanics
| Line type | Behavior |
|---|---|
| Whole (0, -1, -2) | Push (stake refund) possible on exact margin |
| Half (-0.5, -1.5) | Binary, no push |
| Quarter (-0.25, -0.75) | Stake split across the two adjacent lines → half-win / half-loss outcomes |
| AH 0 (level ball) | Draw no bet |

- Thin, roughly symmetric margin (~2%, e.g. 1.95/1.95) vs 5–8% on 1X2.
- Enormous limits via the Asian broker ecosystem → the professional instrument.

### What can be derived from AH + total
Two liquid numbers summarize the match:
- AH line ≈ expected **supremacy** (home xG − away xG)
- Asian total ≈ expected **total** (home xG + away xG)

Recover team λs:
```
home λ = (total + supremacy) / 2
away λ = (total − supremacy) / 2
```
Feed λs into a Dixon-Coles-adjusted scoreline grid → probabilities for **every final score** → all derivatives fall out: 1X2, correct score, BTTS, clean sheets, team totals, halftime markets (scale λs — ~45% of goals are first-half), winning margins.

### Three professional applications
1. **Derivative/consistency arbitrage**: continuously convert sharp AH+total into a fresh scoreline matrix; scan soft books' derivative prices for inconsistencies. You're arbitraging a sharp market against its lazy echoes, not predicting football.
2. **Line-to-probability translation**: compare your model's supremacy directly against the market's line in the same units. Conversion must condition on the total (same supremacy stretches differently in high-scoring matches) — a seam lazy compilers get wrong.
3. **The line as data**: closing lines as features and ground truth — "market Elo" team ratings, divergence detection vs your xG rating, and the CLV self-evaluation (does your model predict open→close movement?).

### Esoteric edges
- Quarter lines require explicit push / half-push handling in EV and Kelly math (needs the full scoreline distribution; the one-goal-win cell is the most mispriced region per Dixon-Coles).
- Margin removal first; AH margin sits roughly symmetrically (unlike 1X2).
- Microstructure/tape reading: the sequence of quarter-line moves, at which broker, at what time relative to lineup news — closer to trading than statistics.

**Canonical exercise**: strip margin from historical Pinnacle AH+total, invert to λs, build the scoreline matrix, check derived 1X2 vs actual closing 1X2. When they match within a fraction of a percent, you've rebuilt the trading-desk machine — and any book that *doesn't* match is leaving a seam open.

## 6. Comebacks (lose HT / win FT) and in-play modeling

### The market
- One cell of the 3×3 **HT/FT** grid; base rate ~7–8%, typically priced 8.0–30.0+.
- HT/FT at soft books = margin dumping ground; the public overpays for story-shaped outcomes (favourite–longshot bias). The algo's first job is usually to **fade** the comeback narrative.
- HT/FT is **path-dependent** — it asks about the route, not just the final score, which breaks the pre-match machinery.

### Why constant-rate Poisson fails — Dixon & Robinson (1998)
Goals as a birth process with time- and score-dependent intensities:
- **Score effects**: trailing teams' intensity rises; leaders sit deeper. "Momentum" is mostly noise, but score-dependent intensity is real and large.
- **Time effects**: goal rates rise through the match; final 15 minutes are the most goal-dense. A HT deficit leaves the highest-intensity 45 minutes to work with.
- **Team-specific asymmetry**: a strong favourite trailing 0–1 at HT is still the better team over the remaining 45. Big-club comebacks are genuinely more frequent — the market's error is the *magnitude* of the premium, not the direction.

Modern in-play core: time-inhomogeneous, score-dependent bivariate counting process + jump events (red cards ≈ a full handicap line; penalties; weather). Comeback probability = integral over forward-simulated paths.

### Where the edges live
1. **Pre-match derivative scanning**: lazy compilers use constant-rate models → systematically underprice favourite comebacks; the public overprices famous-club comebacks. The seam: strong-but-unfashionable favourites, high-total matches, low-effort leagues. Caveats: savage variance, tiny Kelly stakes, low limits, fastest bans (longshot value is the classic sharp signature).
2. **In-play trading** — how professionals actually monetize comebacks: the live market overreacts to goals and to visible "pressure"; sharp models buy the trailing favourite moments after they concede at panic-inflated odds. Exchange version: back the trailing favourite live and close the position on the *equalizer* — the instrument is "will comeback probability rise," a strictly easier event. Moat = latency (in-stadium data beats TV delay by seconds).
3. **Feature-level "comeback-ness"**: real, measurable mechanisms — bench quality (comebacks are substitute-driven), managerial chasing behavior, fitness/late-goal profiles, schedule-driven motivation. "Mentality" as a free-floating trait ≈ zero after accounting for these. Keep the mechanisms, discard the story.

## 7. Feature engineering for pre-match HT/FT

**Core question for every feature**: does it affect the two halves *differently*, or the *transition* between them? Symmetric features are already in the main line.

### Layer 0 — Target definition
Don't fit 9 flat classes. Model the process: four intensities (home/away × first/second half) + score-interaction terms → halftime matrix → score-adjusted propagation → fulltime matrix → all nine cells + related derivatives, mutually consistent.

### Layer 1 — Baseline
Supremacy + total (from your model or inverted from sharp AH+total), split 45/55 across halves, no score interaction. This ≈ the lazy compiler. All features are deviations from this baseline.

### Layer 2 — Half-profile features (temporal distribution of quality)
- Never build from goals (~25 events/season = noise). Use the shot/xG event stream (10–15× density).
- **xG tempo curves** per minute-bin, heavily shrunk toward the league curve → "slow starter" and "closer" coefficients.
- **Mechanism features**: early pressing intensity (PPDA, decays with fatigue), squad age + fixture congestion + travel (load on second half), **bench quality** (starters-vs-subs xG differential × manager sub timing — nearly orthogonal to the main line).
- **Manager fingerprints**: substitution timing, formation-change behavior by game state, halftime-adjustment effect. Transfers with the manager between clubs — markets are slow on that transfer.

### Layer 3 — Score-interaction features (the transition kernel)
- League-wide Dixon-Robinson effects as the prior; team-specific deviations on top.
- **Chasing capacity** (xG rate lift when trailing), decomposed into bench depth, plan-B availability (cross volume / box entries when trailing vs level), manager risk appetite.
- **Protecting capacity** (xG conceded when ahead vs level). The comeback cell needs a chaser × a poor protector — the interaction term beats either alone.
- **Incentive state**: season-context (objectives, matches left, is a draw useful) — absent from bulk odds feeds, so most valuable in small leagues.

### Layer 4 — Match context
Lineup-derived re-rating once XIs drop; referee card/penalty tendencies; weather/pitch; rest asymmetry (a second-half supremacy shift barely priced into derivatives); kickoff time and travel (away slow starts, larger in Brazil/Russia).

### Layer 5 — Market features
Sharp AH+total as the strength spine; per-book HT/FT bias fingerprints (which compiler model generates their prices); first-half Asian totals as a direct market check on your 45/55 estimate.

### Fitting, shrinkage, validation
- Fit on the **dense** signal (every shot/xG event, hundreds of thousands of events), not the sparse 9-cell outcomes (comebacks: a few hundred positives *ever*).
- Hierarchical shrinkage everywhere: team → league, manager → population; prior width earned by mechanistic plausibility.
- Nearly linear structure (Poisson-process GLM) beats gradient boosting at this data volume, and readable coefficients catch silently broken features.
- **Calibration**: reliability curves per cell (rare cells always come out miscalibrated; a recalibration layer fixes more EV than another feature). Benchmark log-loss vs the margin-stripped market. Ultimate test = CLV: does your disagreement with opening derivative prices predict where they close? Provable in hundreds of matches vs thousands for profit.

### One-paragraph summary of the craft
The main line already contains *how good* the teams are. Every HT/FT feature that survives is about *when* that quality expresses itself and *how it bends under game states* — tempo profiles, benches, managers, fatigue, incentives — estimated from dense event data, shrunk hard, and assembled through a process model so the nine cells stay coherent. Compilers approximate all of that with one league-wide 45/55 constant. The gap between those two sentences is the entire edge.

---

## Key references & resources
- Maher (1982) — Poisson goals model
- Dixon & Coles (1997) — founding paper (draw correction, time decay)
- Dixon & Robinson (1998) — in-play birth process (score/time effects)
- Karlis & Ntzoufras — bivariate Poisson; Rue & Salvesen — dynamic strengths
- Buchdahl — *Squares & Sharps*, *Monte Carlo or Bust*; Sumpter — *Soccermatics*; Miller & Davidow — *The Logic of Sports Betting*
