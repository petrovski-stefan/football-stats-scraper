# ROUND_CLUSTERS — comebacks and 7+ matches in one round

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together, sliced by round (`notes/ANALYSIS/CLAUDE.md` §2, slices: clusters).
- **Sources:** schedule stage 3. Inputs: the stage and the round (S1.04–05), the kickoff (S1.07), and the opening 1X2 prices (S1.16–18) and O/U market (S1.19–21, through S2.24), through the odds yardstick. Outcomes: the half-time goals (S1.12–13), the goals (S2.01) and the labels S2.26 and S2.29. Units: the league-season (S1.02, S1.01) and the round. The season (S1.01) also gives the season cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 36,237 have both opening markets, in 4,606 rounds: a median of 8 matches in a round, from 2 to 12.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.round_clusters`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

Do comebacks or 7+ matches collect in one round of a league-season? The league-season and the odds also make clusters, so the test compares with them. The round-so-far fields S3.14–20 suppose that a round shares something. If the whole round shares nothing, its earlier matches cannot tell about its later ones.

## Claims

"Around its league-season" compares each round with the other rounds of its league-season. "Against the odds" reads each round's count against the count that the odds yardstick expects (O/E). Each p comes from 200 shuffles of the matches between the rounds of their league-season. Its smallest value is 0.00498.

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | Comebacks do not collect in a round, beyond the league-season and the odds | around its league-season: raw p 0.517, against the odds p 0.478 (sd 6.28% of the O/E 1.2427). The test finds an sd of 33.80% (raw) and 34.14% (odds) at 80%. Rounds with 2 or more comebacks: 275, against 297.8 that the odds and the league-season expect | 4,606 rounds | yes: against the odds p 0.443 (2024) and 0.418 (2025); raw 0.483 and 0.468 | exploratory |
| C2 | Neither link of a comeback collects in a round | against the odds: link 1 p 0.821, link 2 p 0.607. Raw: 0.886 and 0.363. At 80%, the test finds 6.87% (link 1) and 33.34% (link 2) | 4,606 rounds (4,594 with a decisive half-time) | yes: link 1 p 0.682 and 0.781, link 2 p 0.841 and 0.249, against the odds | exploratory |
| C3 | Against the odds, 7+ matches show a sign in the rounds. Single 7+ matches in rounds where the odds expect very few make it, not rounds with many 7+ matches | against the odds p 0.0149; raw p 0.109. Q is 212.1 above the shuffled mean (4549.4 against 4337.3). One round makes 116.0 of Q: 2 matches, one 7+ match, 0.0179 expected. Rounds with 2 or more 7+ matches: 71, against 77.6 expected | 4,471 rounds (in league-seasons with a 7+ match) | no: against the odds p 0.00498 (2024) and 0.602 (2025); raw 0.0149 and 0.881 | exploratory |
| C4 | Goals per match collect in the rounds of the 2024 cohort only | all cohorts: raw p 0.423, against the odds p 0.0249 (sd 4.53% of the O/E 0.9888). 2024: raw p 0.0199, odds 0.00498. Without the first 3 rounds of each stage, 2024 stays: raw 0.0498, odds 0.00995 | 4,606 rounds | no: 2025 raw p 0.975, odds 0.682 | exploratory |
| C5 | Without the league-season, the rounds differ in 7+ and in goals, because the league-seasons differ | around all matches: 7+ p 0.00995, goals p 0.00498. Comebacks p 0.119, link 1 0.164, link 2 0.119 | 4,606 rounds | not measured | exploratory |

## One test of the rounds for each quantity

"sd / pooled" is the spread of the rounds that the test finds, as a share of the pooled value. "Found" is the spread that the test finds at p < 0.05 in 80% of simulated corpora. "Share" is the share of the variance of one match that the spread makes (`ALL/LEVELS.md`, Method).

| quantity | reading | Q | df | shuffled mean | shuffled sd | p | sd / pooled | found / pooled | share |
|---|---|---|---|---|---|---|---|---|---|
| comeback | raw, around all matches | 4710.1 | 4,605 | 4595.5 | 96.0 | 0.119 | 0.2397 | 0.3537 | 0.0032 |
| | raw, around its league-season | 4490.3 | 4,462 | 4494.0 | 85.0 | 0.517 | 0 | 0.3380 | 0 |
| | odds, around its league-season | 4497.8 | 4,462 | 4489.5 | 85.1 | 0.478 | 0.0628 | 0.3414 | 0.0002 |
| link 1: a team is behind at half-time | raw, around all matches | 4702.5 | 4,605 | 4611.8 | 94.2 | 0.164 | 0.0417 | 0.0691 | 0.0025 |
| | raw, around its league-season | 4400.4 | 4,462 | 4491.4 | 75.7 | 0.886 | 0 | 0.0691 | 0 |
| | odds, around its league-season | 4414.3 | 4,462 | 4486.7 | 76.0 | 0.821 | 0 | 0.0687 | 0 |
| link 2: the team behind wins | raw, around all matches | 4688.4 | 4,593 | 4581.2 | 94.6 | 0.119 | 0.2274 | 0.3442 | 0.0050 |
| | raw, around its league-season | 4521.9 | 4,450 | 4489.4 | 87.8 | 0.363 | 0.1217 | 0.3327 | 0.0014 |
| | odds, around its league-season | 4345.9 | 4,450 | 4381.2 | 125.6 | 0.607 | 0 | 0.3334 | 0 |
| 7+ goals | raw, around all matches | 4918.2 | 4,605 | 4600.9 | 97.0 | 0.00995 | 0.6181 | 0.5481 | 0.0088 |
| | raw, around its league-season | 4447.9 | 4,332 | 4348.5 | 81.1 | 0.109 | 0.2756 | 0.4259 | 0.0018 |
| | odds, around its league-season | 4549.4 | 4,332 | 4337.3 | 85.0 | 0.0149 | 0.4648 | 0.4931 | 0.0078 |
| goals per match | raw, around all matches | 6566.2 | 4,605 | 5264.4 | 116.9 | 0.00498 | 0.1065 | 0.0466 | 0.0304 |
| | raw, around its league-season | 5136.7 | 4,462 | 5111.7 | 112.5 | 0.423 | 0.0149 | 0.0466 | 0.0006 |
| | odds, around its league-season | 5355.1 | 4,462 | 5120.6 | 112.2 | 0.0249 | 0.0453 | 0.0463 | 0.0056 |

For goals, the shuffled mean is far above the df. The chi-square p is wrong there, and this doc does not use it (Method).

## Around the league-season, by season cohort

Each cell is the p, raw, then against the odds. "From round 4" leaves out the first 3 rounds of each stage, where goals fall short of the odds (`ALL/SEASON_PHASE.md` C5).

| quantity | 2024, all rounds | 2024, from round 4 | 2025, all rounds | 2025, from round 4 |
|---|---|---|---|---|
| comeback | 0.483, 0.443 | 0.398, 0.358 | 0.468, 0.418 | 0.711, 0.697 |
| link 1 | 0.716, 0.682 | 0.622, 0.587 | 0.841, 0.781 | 0.796, 0.726 |
| link 2 | 0.562, 0.841 | 0.408, 0.826 | 0.234, 0.249 | 0.368, 0.279 |
| 7+ goals | 0.0149, 0.00498 | 0.0149, 0.00995 | 0.881, 0.602 | 0.91, 0.841 |
| goals per match | 0.0199, 0.00498 | 0.0498, 0.00995 | 0.975, 0.682 | 0.905, 0.662 |

The cohorts hold 17,756 matches (2024; 16,002 from round 4) and 18,481 (2025; 16,666 from round 4).

## The rounds that make the largest part of Q against the odds

7+ goals:

| round | league | matches | observed | expected | O/E | league-season O/E | part of Q |
|---|---|---|---|---|---|---|---|
| 391 2024 Apertura-B 4 | primera_division_de_venezuela | 2 | 1 | 0.0179 | 55.7257 | 0.4711 | 116.0 |
| 34 2024-2025 League 9 | italy_serie_a | 10 | 2 | 0.2106 | 9.4981 | 0.2539 | 71.0 |
| 358 2025 17 | brazil_serie_b | 10 | 1 | 0.0705 | 14.1762 | 0.3160 | 42.7 |
| 151 2024-2025 League 26 | scottish_division_one | 5 | 1 | 0.0926 | 10.7949 | 0.2574 | 39.9 |
| 1 2024 League 28 | ireland_premier_division | 5 | 1 | 0.0741 | 13.4951 | 0.3573 | 35.8 |

Goals per match:

| round | league | matches | observed | expected | O/E | league-season O/E | part of Q |
|---|---|---|---|---|---|---|---|
| 61 2024 League 11 | chinese_football_association_jia_league | 8 | 35 | 19.00 | 1.8421 | 1.0027 | 15.8 |
| 292 2025-2026 League 20 | saudi_professional_league | 9 | 9 | 27.84 | 0.3233 | 0.9812 | 14.5 |
| 212 2024 League 15 | finland_ykkonen | 5 | 28 | 14.36 | 1.9499 | 1.0291 | 14.0 |
| 60 2024 League 12 | chinese_super_league | 8 | 43 | 24.96 | 1.7228 | 1.0267 | 13.9 |
| 9 2024-2025 League 10 | german_bundesliga_2 | 9 | 45 | 28.26 | 1.5924 | 0.9886 | 12.3 |

A round key is the league id, the season, the stage and the round.

## Rounds by their count of events

The expected counts come from each match's chance: the odds yardstick's chance, times the O/E of its league-season. The matches of a round are taken as independent.

| events in the round | rounds: comebacks | expected | rounds: 7+ matches | expected |
|---|---|---|---|---|
| 0 | 3,032 | 3055.0 | 3,869 | 3878.3 |
| 1 | 1,299 | 1253.2 | 666 | 650.0 |
| 2 | 239 | 259.4 | 67 | 71.4 |
| 3 | 31 | 34.8 | 4 | 5.9 |
| 4 or more | 5 | 3.5 | 0 | 0.4 |

## Method

- **A round:** one round of one stage of a league-season (`analysis/corpus.py:round_key`). The Apertura and the Clausura are two stages.
- **The yardstick:** `ALL/ODDS_YARDSTICK.md`, on the 36,237 matches with both opening markets.
- **Three readings:**
  - raw, around all matches: the rounds against the pooled value, so the league-seasons also make the rounds differ;
  - raw, around its league-season: each round against the other rounds of its league-season;
  - against the odds, around its league-season: each round's O/E against the O/E of its league-season. The prices of the matches of a round then change nothing.
- **The test, the shuffles, the spread and the share:** as in `ALL/LEVELS.md` (Method), with the rounds as parts and the league-seasons as units (`analysis/units.py:level_row`). In each shuffle, each match takes the round of a random match of its league-season. Each round keeps its number of matches.
- **Why the shuffles:** the dispersion is measured around each round of about 8 matches. For goals it is then too low, and Q is too large: the shuffled mean is 5120.6 against 4,462 df. The shuffles have the same bias as the real Q. For 0/1 outcomes, the shuffled means stay near the df.
- **Near the date of the round:** a match more than 3 days from the median kickoff of its round is far. 1,119 matches (0.0309) are far, in 649 rounds. A far match can be a match that was put off.
- **The largest rounds:** the part of each round in Q, against the odds: (its O/E − the O/E of its league-season)² / its variance.
- **The counts of events:** the chance of each match is the yardstick's chance times the O/E of its league-season, capped at 1. The expected number of rounds with k events sums, over the rounds, the chance of k events among independent matches (a Poisson-binomial count).
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025. 2025 holds 2025 and 2025-2026.

## Caveats

- **The round-so-far fields.** This test reads the whole round, after all its matches. S3.14–20 read only the matches of the round that finished before kickoff. So C1 and C2 bound them: the earlier matches cannot share more than the whole round. But the test cannot see a round spread below the "found" values (about a third of the comeback rate). `ALL/PREMATCH_SCREEN.md` C2 finds that the round-so-far fields add nothing for a team's comeback.
- **C3 is fragile.** Q weighs each round by its variance. One rare event in a small round with a low expected count gives a large part of Q. The count table shows no more rounds with 2 or more 7+ matches than expected.
- **C4 has no cause in this run.** It is in one cohort only. It stays without the first rounds, so the low goals of the first rounds (`ALL/SEASON_PHASE.md` C5) do not make it alone. The shuffles break the order of time, so a trend over the stage also makes rounds differ.
- **The matches of a round are taken as independent** by the count table and by the variance of each round. Two matches of one round share a date, sometimes a ground and the weather. This is what the test looks for.
- **Matches put off:** without the 1,119 far matches, the p against the odds are: comeback 0.572, link 1 0.602, link 2 0.627, 7+ 0.00995, goals 0.00995. They do not change the claims.
- **"Found" uses a normal model.** For rare events in rounds of about 8 matches, the true power is lower.
- **Looks:** 15 tests on all matches, 5 near the date, 40 in the cohorts: 60 tests. Below p = 0.05: 7+ and goals around all matches (C5, the league-seasons); against the odds, 7+ and goals on all matches, near the date, and in 2024; raw, 7+ and goals in 2024. These share data. 2025 has none.
- **Not profit.** A round with more comebacks than the yardstick does not show value. The value needs the HT/FT prices, and nowgoal does not show them.
