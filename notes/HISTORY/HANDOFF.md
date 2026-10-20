# HANDOFF.md — The Retiring Statistician's Guide to the Comeback Prediction Project

**Group: History.** Read it for context only. Do not edit it. Its facts can be out of date.

**Audience:** any future model (or human) continuing this project — including smaller models.
Read `CLAUDE.md` first for repo mechanics. This document is the *strategy and statistics*
layer: what the project is really trying to do, what has already been learned (often the
hard way), what the numbers actually say, and the traps that will quietly ruin you.

Everything quantitative below was computed from `data/english_premier_league.csv`
(2025–26 season, 380 matches) unless noted. Recompute when more data lands — but the
*structure* of these findings is the durable part.

---

## 1. What this project is

A data pipeline + LLM evaluation loop targeting one hard betting market (no real money —
this is data science):

> **HT/FT turnaround ("comeback"):** the team trailing at half-time wins at full-time.
> Secondary market: 7+ total goals (7 or more).

The architecture is deliberately **not** a local ML model:

1. **League scraper** (`scrapers/schedule.py` → `data/<league>.csv`) — historical finished matches.
   Role: *league/team context* — base rates, team recovery profiles, the "registry".
2. **Detail scraper** (`scrapers/detail.py` → `data/<league>_detail.csv`) — per-match wide feature
   rows from the H2H detail page. Role: *pre-match inputs* — the same page exists for
   scheduled (not yet played) matches, so `scrape_match_detail()` is mode-agnostic.
3. **Prediction engine (future):** a "matchup card" (JSON) per upcoming match — league
   context card + detail features + structured web-search findings — sent to the Claude
   API, which outputs a probability with reasoning. Predictions are logged and scored.

---

## 2. The market math — memorize these numbers

From 380 PL matches, 2025–26:

| Quantity | Value |
|---|---|
| Any comeback (either side) | **6.05%** (23/380) — home 2.9%, away 3.2% |
| 7+ goals | **1.84%** (7/380) |
| P(win \| trailing by 1 at HT) | **12.9%** (22/170) |
| P(draw \| trailing by 1 at HT) | **21.8%** — equalizing is ~1.7× more common than completing |
| P(win \| trailing by 2+ at HT) | **1.5%** (1/66) — effectively dead |
| Comeback rate when favorite odds < 1.5 | **3.2%** |
| Comeback rate when favorite odds ≥ 2.2 | **9.2%** (≈3× lift for competitive matches) |
| HT/FT combos `1-2` + `2-1` | 3.2% + 2.9% (these ARE the comeback market) |

Consequences you must internalize:

- **This is a rare event.** 23 positives per league-season. No feature engineering
  compensates for that; only more leagues × more seasons does. Ten leagues × five seasons
  ≈ 19,000 matches ≈ 1,150 comebacks — the minimum for confident conclusions.
- **The market is really "trailing by exactly one."** Always condition on HT deficit.
- **"Equalize but not win" is the central phenomenon.** Comeback *attempts* are common;
  *completion* is what the market pays for. These are different problems.
- The comeback bet decomposes into three sub-problems:
  **(a) volatility** (is this a turnaround-conducive match), **(b) direction** (who leads
  at HT), **(c) completion** (trail → win). Historical evidence: (a) is somewhat
  predictable, (b) is near coin-flip, (c) is a 12.9% conditional. Multiplying all three
  pre-match compounds noise — prefer direction-free outputs, or condition on the HT state.

---

## 3. History: the "Mode 2" manual framework (2025–26 season)

Before this repo, the user ran a season-long manual framework via Claude web chat
(Flashscore screenshots, gates, a ChatGPT "kill validator"). Full summary lives with the
user; the audited conclusions:

**What replicated in the scraped data (trust these):**
- The competitiveness gate: heavy favorites suppress comebacks (3.2% vs 9.2% above).
- "Equalize but not win" — confirmed and quantified (21.8% draw vs 12.9% win at −1).
- Aston Villa as comeback-prone: 4 comebacks from 12 HT-trailing situations (33% vs
  league 9.7%), 13 points from HT-losing positions. **But note:** Brighton also earned 13
  points from behind with nobody building a narrative around them — team fame drives
  narratives, data doesn't.

**What is unverified narrative (n < 5 — treat as hypotheses, not rules):**
- Monday/midweek suppression, motivation asymmetry, endogenous red cards, "state-transition
  psychology". Plausible; test each against the multi-season dataset before encoding.

**Meta-lessons from that season:**
- Zero directional picks completed across ~20–25 picks — which is statistically
  **uninformative**: at a 3–5% directional base rate, even a genuine 2× edge yields ~15–20%
  probability of zero hits in 25 picks. Manual-scale samples cannot evaluate this market.
- The adversarial "kill validator" (default assumption: pick is WRONG) killed three
  actual turnarounds and passed nothing. On a rare event, an always-skeptical validator
  just restates the base rate. **Replace adversarial validation with calibration
  measurement** (§7).
- Manual analysis quality degraded over long conversations. The pipeline exists so that
  round 38 is analyzed with round 1 rigor.

---

## 4. Feature geography — which scraper owns what

**League scraper** (`constants.ORDERED_DF_COLUMNS`): identity (season/league/round/ids),
standings-as-of-round + `position_gap`, schedule flags, day-of-week, HT/FT scores and all
derived goals (incl. 2H splits), results/combos, 1X2 opening odds + implied probs +
favorite fields, labels (`is_comeback[_home/_away]`, `is_seven_or_more_goals`, `btts`,
`over_25`).

**Detail scraper** (`constants.DETAIL_ORDERED_COLUMNS` + `per_match_columns()`):
bookmaker 1X2 initial+live odds, recent-form aggregates with venue splits, H2H aggregates,
site analytics (strength / h2h-compare / crowd guess), fixture congestion, and flattened
`home/away/h2h_last1..6_*` blocks (25 fields each: scores, results, odds, corners, dates,
`is_home`). Data-quality fact (validated July 2026 on all 36,597 history records): the
detail page's history widgets are **anchored to the match** — every record predates its
target match, even on pages scraped long after kickoff — so these columns are valid
pre-match features for finished matches as scraped.

**Two structural facts to remember:**

1. **The best pre-match features live in the LEAGUE scraper, and the current code drops
   them for upcoming matches.** `parsers.parse_schedulis_row()` returns `None` when HT/FT
   don't parse — correct for building the historical archive, but the schedule page also
   shows upcoming rows with teams, date, round, **current standings**, and **opening
   odds**. The detail page has no standings-as-of-round at all. → Build a prediction mode
   that emits upcoming rows (slim `UpcomingMatch`: metadata + standings + odds, no labels).

2. **The user's old "proprietary filter" (venue-specific half-by-half scoring from the
   most recent match) is already automated** — it is exactly the `*_last1_*` block from
   `detail_parsers.flatten_history` (`is_home`, `ht_score`, `ft_score`). Every manual Mode 2
   gate now has a column equivalent; see the mapping in §8.

---

## 5. LEAKAGE — the section to reread before every change

These are the ways this specific pipeline can lie to you:

1. **`odds1x2_live_*` has two meanings.** Scraped pre-kickoff: the *current* price —
   legitimate, and `implied_live − implied_init` is the "what does the market know"
   feature (injuries/lineups/motivation, pre-digested). Scraped after the match: in-play
   or final odds — **poison** as a pre-match feature. Tag rows with scrape time; never
   show post-hoc live odds to the prediction engine as an analog.
2. **Standings must be as-of-round.** The schedule scraper already syncs the standings
   dropdown per round — preserve this invariant in any refactor.

   > **Erratum, 2026-10-11:** this rule was wrong. The page's round-N table already holds
   > round N's own results (measured 2026-10-01), and it counts by round number, so it can
   > also hold matches played later (2026-10-06). The per-round standings scrape was dropped
   > on 2026-10-06. Stage 3 rebuilds the table at each kickoff from our own results
   > (`notes/fields/schedule_3_multi.md` §B, S3.03). The old position columns
   > (`home_team_position`, `away_team_position`, `position_gap`) are post-match.
3. **Never evaluate with shuffled cross-validation.** Form features leak across a random
   split. Always walk-forward: train/tune on seasons ≤ N, evaluate on season N+1.
4. **Web-search features cannot be backfilled.** "What was known 1 day before kickoff"
   is unreconstructable for past matches. Log search findings prospectively (structured,
   timestamped) from day one; until an archive exists, treat news as an overlay, not a
   modeled feature. Note: 1 day out you get *probable* lineups; confirmed XIs land ~1h
   before kickoff. Pick one prediction timestamp and be consistent.

---

## 6. Statistical methodology — rules of the road

- **Shrink every team-level trait.** Empirical-Bayes toward the league rate:
  `rate = (successes + k·league_rate) / (trials + k)`, k ≈ 10. Villa's raw 33% recovery
  shrinks to ~17% — still elevated, honestly so. **Never emit a binary
  `comeback_prone: true` from one season of data.** Ship the shrunk rate *plus raw counts*
  ("4/12 vs league 9.7%") so the LLM can weigh the sample size itself.
- **Test persistence before trusting any team trait.** Correlate each team's recovery
  rate in season N with season N+1 across the multi-season dataset. Traits that don't
  persist are luck, however good the story (published work suggests HT-recovery ability
  is at best weakly persistent).
- **Decompose "comeback-prone".** Raw comeback counts confound *trailing often* (bad
  team) with *recovering well* (strong 2H). The cleaner underlying trait is second-half
  goal supremacy (`home_2h_goals`/`away_2h_goals`, all 38 matches) — 3× the data of
  trailing situations. Also track the mirror image: **blown leads** — a turnaround needs
  a recoverer AND a collapser; profile the leading team's fragility too.
- **Model goals, not binaries, if a statistical model is ever added.** Both markets are
  functionals of the goal process: a Dixon–Coles / bivariate Poisson fit *per half* gives
  P(comeback) and P(7+ goals) by integration, using every match to estimate every
  parameter instead of 23 positives. The columns needed (`goals_1h`, 2H splits) already
  exist.
- **Remove the vig from implied probabilities.** `1/odds` overstates by the ~5–7%
  overround. Normalize: divide each `1/odds` by Σ(1/odds) over 1/X/2. Add the draw.
- **Beware the 450-column trap.** `per_match_columns()` generates ~450 features. With 23
  positives, pattern-mining across them is a false-discovery machine. Features earn their
  place via the persistence test and out-of-season lift, not in-sample correlation.
- **Rare-event power math.** Before claiming any gate/feature "works" or "fails," compute
  the expected count under the base rate. 0 hits in 25 directional picks proves nothing;
  neither do 4 hits in 12 trials, on their own, across 20 teams (one team will always
  lead by luck — selecting the leader is selecting on the outcome).

---

## 7. The prediction engine (Claude API) — design contract

1. **Input = one versioned JSON matchup card per match.** Never raw CSVs. Contents:
   - **League context card** (precomputed, small): league comeback rate, recovery by HT
     deficit, home/away split, per-team shrunk recovery + points-from-behind + blown-lead
     counts (the "registry", auto-generated — never hand-maintained).
   - **Upcoming-row basics:** standings positions, position gap, round, opening 1X2 odds.
   - **Detail features:** form aggregates, H2H, congestion, `last1..6` blocks, current
     odds + odds movement.
   - **Web-search findings:** structured fields only (absences count, probable-lineup
     changes, rest days, motivation category + asymmetry score), with sources and
     timestamps.
2. **Prompt = anchor-and-adjust, never free-form judgment.** Force: start from the
   base rate for this matchup class → list each adjustment with direction and bounded
   magnitude → output JSON `{p_comeback_home, p_comeback_away, p_turnaround_any,
   key_factors[], confidence}`. The known LLM failure mode is **narrative bias**: a juicy
   motivation story moves 10% to 25% because it's compelling. Bounded adjustments and
   visible sample sizes are the guardrails.
3. **Output shape: the decomposition, not the 9-cell HT/FT pick.** P(home leads HT),
   P(away leads HT), P(completion | trail by 1, given both teams' profiles).
   Direction-free "turnaround likely" is a valid, historically-vindicated output.
4. **Temperature 0; measure the noise floor** by running an identical card twice — if the
   probability moves 5 points between runs, no feature smaller than that matters.
5. **Log everything, score everything.** Every prediction: full input snapshot, model
   output, timestamp. After matches finish: calibration curve (of the "15%" predictions,
   did ~15% happen?), Brier/log-loss, and comparison against two dumb benchmarks —
   the league base rate and the odds-implied probability. **A feature that doesn't beat
   the benchmarks gets removed, however clever it feels.** This loop is a spreadsheet,
   not ML, and it is the only thing separating this project from astrology.
6. **The real benchmark is the market's price.** 1X2 odds are collected, but comebacks
   are priced as HT/FT (and 7+ on the O/U market) with brutal margins. If those odds are
   scrapeable from the DOM (never call site APIs — see CLAUDE.md), collect them; without
   the price you can prove "model says 8%, history says 6%" but never an edge.

---

## 8. Mode 2 → pipeline mapping (nothing was lost)

| Manual framework component | Pipeline equivalent |
|---|---|
| Gate 1: combined goals, last 5 | `*_recent_gf_avg + ga_avg` (detail) |
| H2H goals override | `h2h_avg_total_goals`, `h2h_over25_rate` (detail) |
| 1.40 competitiveness rule | `favorite_odds` (league) — confirmed real, 3.2% vs 9.2% |
| Turnaround Team Registry | shrunk recovery + points-from-behind per team, auto-computed |
| Proprietary venue half-by-half filter | `*_last1_*` blocks (`is_home`, `ht_score`, `ft_score`) |
| Motivation asymmetry | `team_position` + `round` (free proxy) + web-search layer |
| 2H scoring pattern | `home_2h_goals`/`away_2h_goals` supremacy (league) |
| Max-4-games discipline rule | one matchup card per API call (solved by architecture) |
| ChatGPT kill validator | **deleted** — replaced by calibration measurement (§7.5) |

Retro-test each surviving gate as a boolean column against `is_comeback` once
multi-season data exists; keep lift, kill the rest. Priors: odds gate survives, H2H-goals
survives weakly, Monday suppression dies, Gate 1 needs recalibration (it killed two
confirmed turnarounds — "volatile match" ≠ "turnaround match").

---

## 9. Roadmap, in priority order

1. **Breadth before depth:** add leagues to `config/LEAGUES.txt` and historical seasons
   (`/league/<season>/<id>` URL format). Target ≥ 10 league-seasons before drawing
   conclusions. Run `scrapers/detail.py` resumably (`--limit`) — it's ~380 renders per season.
2. **Build the context-card generator:** a script that reads `data/*.csv` and emits one
   JSON per league (base rates, deficit-conditional rates, shrunk team registry with raw
   counts, blown-lead profiles). Pure pandas, no scraping.
3. **Add the prediction mode:** upcoming rows from the schedule page (standings + opening
   odds) + `scrape_match_detail()` on upcoming ids + matchup-card assembly.
4. **Stand up the logging/scoring loop (§7.5) before the first real prediction.**
5. **Run the science:** gate retro-tests (§8), team-trait persistence tests (§6),
   and the handoff question — does *any* pre-match feature set move directional completed
   turnaround probability off ~3% with out-of-season calibration intact?
6. **Build the HT-conditional product** — the strongest idea from the manual season:
   pre-match shortlist → observe the HT state → evaluate completion (base 12.9% at −1)
   with recovery/collapse profiles and 2H supremacy. This deletes the direction problem,
   the hardest and least-solvable third of the market.
7. **Nice-to-haves as data grows:** goal-timing data if scrapeable (share of goals after
   75' beats comeback counts as a "comeback-prone" measure), SQLite instead of CSVs,
   parser tests against saved HTML fixtures (the day nowgoal26 changes its DOM you want a
   failing test, not silently empty CSVs).

---

## 10. Final cautions from the departing statistician

- **The opponent is the margin, not the fixture list.** Even with no money involved, the
  intellectually honest benchmark is the vig-adjusted market price.
- **The expensive, exciting features are usually the noise.** Web search, motivation
  narratives, psychology — measure their marginal Brier improvement over the odds-only
  baseline before believing in them.
- **Never form a belief from fewer than ~30 positive cases**, and never canonize a
  discovery that hasn't replicated out-of-sample. The previous framework's "10
  discoveries" came from a season containing seven turnarounds; three replicated.
- **When you find a team that "leads the league" in anything, immediately look at who's
  second.** (Villa 13 points from behind — and Brighton, quietly, also 13.)
- **Respect the scraping rules:** DOM-only via Selenium, never the site's API endpoints
  (see CLAUDE.md and project memory). The pipeline's value is the archive — protect its
  integrity over any single prediction.
- The honest end-state may be: *pre-match directional completion is unbeatable; pre-match
  shortlisting has real lift; the HT-conditional bet is where signal lives.* If the data
  says that, say it. A correct "no edge here" is a finding, not a failure.

Good luck. The foundation is real, the traps are now labeled, and the base rates are on
your side exactly 6.05% of the time.

*— compiled July 2026, at the end of a long career of being burned so you don't have to be.*
