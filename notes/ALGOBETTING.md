# Algobetting in Football — Conversation Summary

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

Notes from a long, detailed conversation about quantitative football betting: market structure, the history of the models, the Asian handicap, comeback (HT/FT) markets, and feature engineering.

---

## 1. Why algobetting is real but hidden

- A real edge becomes smaller when people share it. So the methods that work stay private. Public discussion = tipsters and noise. Serious work = private syndicates.
- The standard examples: **Starlizard** (Tony Bloom, ~160 analysts) and **Smartodds** (Matthew Benham). Both founders bought football clubs (Brighton, Brentford) with profits from betting.

## 2. Market structure — the first esoteric lesson

- **Sharp books** (Pinnacle, Asian books such as SBOBet, brokers such as Mollybet): very large volume, ~2% margins. They accept winners, because winners make their prices more accurate.
- **Soft books** (the well-known brands): large margins. They are slow to change their prices, and they ban winners quickly.
- Most profit at retail scale = use of the delay between sharp prices and soft prices.
- The **sharp closing line** is the nearest thing to an efficient price in football.

### Closing Line Value (CLV)
- The variance is too high to judge your work by its profit over hundreds of bets.
- Instead, ask: did you consistently get a better price than the closing price? (You bet at 2.10, and the price closes at 1.95 → you beat the close.)
- The core change of view: *you do not predict matches. You predict where the price will move.*

## 3. The modeling lineage

1. **Poisson model** (Maher 1982): goals as independent Poisson processes, from attack and defence strengths.
2. **Dixon & Coles (1997)**, the founding paper: a correlation correction for low-scoring draws (0-0, 1-1), and an exponential time decay on past matches. Almost every serious model comes from it.
3. Improvements: bivariate Poisson (Karlis & Ntzoufras), dynamic/state-space strengths (Rue & Salvesen), Bayesian hierarchical models.
4. **Modern layer**: xG and shot-based data (a denser signal than goals, ~2.7 per match), possession-value models (VAEP, xT), and player-level ratings rebuilt from the probable starting XIs. These ratings let a model react at once to lineup news.

### Unglamorous truths
- Data quality and feature engineering are more important than the choice of algorithm.
- Overfitting is the largest cause of failure (~380 matches per league per season).
- The model does not have to be right. It must be *less wrong than the margin*. Look for systematic biases: the favourite–longshot bias, slow price changes after lineup news, small leagues, and derivative markets that a formula prices.
- **Staking**: fractional Kelly (for example quarter-Kelly), because the estimate of your edge is also uncertain.
- **Execution** ("getting money down") is the really hidden skill: account networks, Asian brokers, bots. Starlizard has more traders than statisticians.

### Reading path
- Dixon & Coles (1997) — founding paper
- Joseph Buchdahl — *Squares & Sharps*, *Monte Carlo or Bust* (market efficiency, CLV)
- David Sumpter — *Soccermatics* (modeling intuition)
- Miller & Davidow — *The Logic of Sports Betting* (market structure)

## 4. Why algobettors target small leagues

- The edge is inversely proportional to the smart money that is already in a market. EPL closing lines are almost efficient. The lines of the Norwegian second division are not.
- **Compiler effort scales with turnover**: the prices of minor leagues often come semi-automatically from shared third-party feeds (for example Betradar). One error in a feed then goes to half of the industry. Such an error is systematic, and a bettor can use it.
- **Slow information diffusion**: injury news in the local language can take hours to get into the price. Scrapes of local sources, or payments to local reporters, give an information advantage. That advantage is worth more than a better model.
- **Less informed competing money**: local recreational bettors and accumulator bettors. The lines move on sentiment.
- **The problem — liquidity works against you too**: limits are very small, and your own bets move the price.
- **Lifecycle**: develop edges in small leagues (large edges, low capacity). Then you must move up into Asian handicap markets on big leagues (small edges, very large capacity). Small leagues are where you learn the skill. Big leagues are where the large profits are, and you arrive there with the skill.
- **Degrees of freedom**: in obscure leagues, even one extra layer (xG, promotion/relegation motivation, artificial pitches, travel fatigue, cup rotation) can beat the compiler. In the EPL, the price already contains all of it.

## 5. Asian handicap (AH) — in depth

Origin: Indonesian and Malaysian markets. Joe Saumarez Smith made the term (late 1990s). It solves the draw problem: it changes any unequal match into ~50/50.

### Mechanics
| Line type | Behavior |
|---|---|
| Whole (0, -1, -2) | Push (stake refund) possible on exact margin |
| Half (-0.5, -1.5) | Binary, no push |
| Quarter (-0.25, -0.75) | Stake split across the two adjacent lines → half-win / half-loss outcomes |
| AH 0 (level ball) | Draw no bet |

- A small margin, approximately symmetric (~2%, for example 1.95/1.95), against 5–8% on 1X2.
- Very large limits through the Asian brokers → the professional instrument.

### What can be derived from AH + total
Two liquid numbers give a summary of the match:
- AH line ≈ expected **supremacy** (home xG − away xG)
- Asian total ≈ expected **total** (home xG + away xG)

Calculate the team λs:
```
home λ = (total + supremacy) / 2
away λ = (total − supremacy) / 2
```
Put the λs into a scoreline grid with the Dixon-Coles adjustment → probabilities for **every final score** → all derivatives follow: 1X2, correct score, BTTS, clean sheets, team totals, half-time markets (scale the λs: ~45% of goals are in the first half), winning margins.

### Three professional applications
1. **Derivative/consistency arbitrage**: convert the sharp AH and total into a new scoreline matrix, all the time. Then look for inconsistencies in the derivative prices of soft books. You do not predict football. You do arbitrage between a sharp market and its slow copies.
2. **Line-to-probability translation**: compare your model's supremacy directly with the market's line, in the same units. The conversion must depend on the total, because the same supremacy has a different effect in high-scoring matches. Careless compilers get this wrong, and that leaves a gap.
3. **The line as data**: closing lines as features and as ground truth. Uses: "market Elo" team ratings, the detection of differences from your xG rating, and the CLV self-evaluation (does your model predict the open→close movement?).

### Esoteric edges
- Quarter lines need explicit rules for a push and a half-push in the EV and Kelly mathematics. This needs the full scoreline distribution. By Dixon-Coles, the one-goal-win cell is the region with the worst prices.
- Remove the margin first. The AH margin is approximately symmetric (unlike 1X2).
- Microstructure and tape reading: the sequence of quarter-line moves, at which broker, and at what time relative to lineup news. This is nearer to trading than to statistics.

**Canonical exercise**:
1. Remove the margin from historical Pinnacle AH and totals.
2. Invert them to λs.
3. Build the scoreline matrix.
4. Compare the derived 1X2 with the actual closing 1X2.

When they agree within a fraction of a percent, you have rebuilt the machine of a trading desk. A book that does *not* agree leaves a gap open.

## 6. Comebacks (lose HT / win FT) and in-play modeling

### The market
- Two cells of the 3×3 **HT/FT** grid: 2/1 and 1/2 (`notes/MARKET_COMEBACKS.md` §1). Base rate ~7–8% in the conversation. The 36,238 matches of this project give 5.09–5.59% for each weekday (`notes/MIGRATIONS.md`, 2026-10-11). The usual price is 8.0–30.0 or more.
- At soft books, HT/FT is where they put large margins. The public pays too much for outcomes that make a good story (favourite–longshot bias). So the first job of the algorithm is usually to **fade** the comeback story, that is, to bet against it.
- HT/FT is **path-dependent**. It asks about the route, not only the final score. That breaks the pre-match machinery.

### Why constant-rate Poisson fails — Dixon & Robinson (1998)
Goals as a birth process, with intensities that depend on the time and the score:
- **Score effects**: the intensity of trailing teams increases, and leaders defend deeper. "Momentum" is mostly noise. But intensity that depends on the score is real and large.
- **Time effects**: goal rates increase during the match. The last 15 minutes have the most goals. A team behind at HT still has the 45 minutes with the highest intensity.
- **Team-specific asymmetry**: a strong favourite that is behind 0–1 at HT is still the better team for the remaining 45 minutes. Comebacks by big clubs really are more frequent. The market's error is the *size* of the premium, not its direction.

The modern in-play core: a time-inhomogeneous, score-dependent bivariate counting process, plus jump events (a red card ≈ a full handicap line; penalties; weather). Comeback probability = the integral over paths that are simulated forward.

### Where the edges live
1. **Pre-match derivative scanning**: careless compilers use constant-rate models. So they consistently give too low a probability to comebacks by the favourite. The public gives too high a probability to comebacks by famous clubs. The gap: strong favourites that are not famous, high-total matches, leagues where compilers make little effort. Cautions: very high variance, very small Kelly stakes, low limits, and the fastest bans (value on long odds is the classic sign of a sharp bettor).
2. **In-play trading**, which is how professionals really make money from comebacks. The live market reacts too much to goals and to visible "pressure". Sharp models back the trailing favourite just after it concedes, at odds that panic makes too long. The exchange version: back the trailing favourite live, and close the position at the *equaliser*. The instrument is then "will comeback probability rise," a strictly easier event. The protection against competitors is latency: data from the stadium arrives seconds before the TV picture.
3. **Feature-level "comeback-ness"**: real mechanisms that you can measure: bench quality (comebacks are substitute-driven), how managers chase a game, fitness and late-goal profiles, and motivation from the fixture list. "Mentality" as a separate trait ≈ zero after you account for these. Keep the mechanisms, and discard the story.

## 7. Feature engineering for pre-match HT/FT

**Core question for each feature**: does it have a *different* effect on the two halves, or an effect on the *transition* between them? The main line already contains the symmetric features.

### Layer 0 — Target definition
Do not fit 9 flat classes. Make a model of the process: four intensities (home/away × first/second half) + score-interaction terms → half-time matrix → propagation with a score adjustment → full-time matrix → all nine cells and the related derivatives, all consistent with each other.

### Layer 1 — Baseline
Supremacy + total (from your model, or inverted from the sharp AH and total), split 45/55 between the halves, with no score interaction. This ≈ the careless compiler. All features are deviations from this baseline.

### Layer 2 — Half-profile features (temporal distribution of quality)
- Never build these features from goals (~25 events per season = noise). Use the shot and xG event stream (10–15× the density).
- **xG tempo curves** per minute bin, shrunk strongly toward the league curve → "slow starter" and "closer" coefficients.
- **Mechanism features**:
  - early pressing intensity (PPDA; it decreases with fatigue);
  - squad age, fixture congestion and travel (the load on the second half);
  - **bench quality** (the xG difference between starters and substitutes × the manager's substitution timing). Bench quality is almost orthogonal to the main line.
- **Manager fingerprints**: substitution timing, changes of formation by game state, the effect of half-time adjustments. These traits move with the manager from club to club, and markets are slow to see that move.

### Layer 3 — Score-interaction features (the transition kernel)
- League-wide Dixon-Robinson effects as the prior, with team-specific deviations on top.
- **Chasing capacity** (the increase in xG rate when behind). Its parts: bench depth, a plan B (cross volume and box entries when behind vs level), and the manager's appetite for risk.
- **Protecting capacity** (xG conceded when ahead vs level). The comeback cell needs a chaser × a poor protector. The interaction term is better than either part alone.
- **Incentive state**: the season context (objectives, matches left, is a draw useful). Bulk odds feeds do not have it, so it is most valuable in small leagues.

### Layer 4 — Match context
- A new rating from the lineup, when the XIs are published.
- Referee tendencies for cards and penalties.
- Weather and pitch.
- Rest asymmetry: it shifts the second-half supremacy, and derivative prices almost do not include it.
- Kickoff time and travel: away teams start slowly, more so in Brazil and Russia.

### Layer 5 — Market features
- Sharp AH and total as the main measure of strength.
- Per-book fingerprints of HT/FT bias (which compiler model makes their prices).
- First-half Asian totals, as a direct market check on your 45/55 estimate.

### Fitting, shrinkage, validation
- Fit on the **dense** signal (every shot and xG event: hundreds of thousands of events). Do not fit on the sparse 9-cell outcomes (comebacks: a few hundred positives in *all* data).
- Hierarchical shrinkage everywhere: team → league, manager → population. A prior can be wide only if its mechanism is plausible.
- At this data volume, a nearly linear structure (a Poisson-process GLM) is better than gradient boosting. Its readable coefficients also show features that break without an error.
- **Calibration**: reliability curves per cell. Rare cells always have a bad calibration. A recalibration layer gives more EV than one more feature. Compare the log-loss with the market after its margin is removed. The final test = CLV: does your disagreement with the opening derivative prices predict where they close? You can prove CLV in hundreds of matches. Profit needs thousands.

### One-paragraph summary of the craft
The main line already contains *how good* the teams are. Each HT/FT feature that survives is about *when* that quality shows, and *how it changes with the game state*: tempo profiles, benches, managers, fatigue, incentives. Estimate these from dense event data, and shrink them hard. Put them together in a process model, so that the nine cells stay consistent. Compilers use one league-wide 45/55 constant for all of that. The difference between these two methods is the entire edge.

---

## Key references & resources
- Maher (1982) — Poisson goals model
- Dixon & Coles (1997) — founding paper (draw correction, time decay)
- Dixon & Robinson (1998) — in-play birth process (score/time effects)
- Karlis & Ntzoufras — bivariate Poisson; Rue & Salvesen — dynamic strengths
- Buchdahl — *Squares & Sharps*, *Monte Carlo or Bust*; Sumpter — *Soccermatics*; Miller & Davidow — *The Logic of Sports Betting*
