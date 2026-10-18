# ODDS_YARDSTICK — the odds yardstick on all matches

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 prices (S1.16–18) and the opening O/U line and prices (S1.19–21), through the two-way probability S2.24. Outcome: the half-time and full-time goals (S1.12–15) and the labels S2.01–03 and S2.26–29.
- **Corpus:** 2026-10-18: 144 league-seasons, 36,238 matches. 36,237 of them have both opening markets. The match without them is the awarded match that has no odds (`ALL/SHIN.md`).
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.odds_yardstick`, at the commit that adds this doc. The yardstick itself is `analysis/methods/yardstick.py`.
- **Kind:** empirical. Under the basic goal model, the opening prices imply a chance of a comeback and of 7+ goals. That is structural (`notes/REFERENCE/MARKET_COMEBACKS.md` §6). How far the results are from it is empirical.

## Question

The opening prices of a match imply a goal rate for each team. Under the basic goal model, these rates expect a number of comebacks and of 7+ matches. How many happened, against that expectation? Do the assumptions of this yardstick hold?

The later docs read their claims against this yardstick (`notes/ANALYSIS/CLAUDE.md` §5, rule 3).

## Claims

O/E is the observed count divided by the count that the yardstick expects. 1 means "as the prices expect".

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | The opening prices expect slightly more goals than happened | O/E 0.9888 [0.9825, 0.9948] (99,564 goals against 100,686.8) | 36,237 | yes: 0.9869 [0.9776, 0.9961] in 2024, 0.9907 [0.9817, 0.9989] in 2025 | exploratory |
| C2 | Comebacks happen more often than the yardstick expects, by about a quarter | O/E 1.2427 [1.1885, 1.2981] (1,891 against 1,521.7) | 36,237 | yes: 1.2317 [1.1532, 1.3144] in 2024, 1.2532 [1.1849, 1.3262] in 2025 | exploratory |
| C3 | The excess is in link 2, the completion from the half-time score. Link 1, the decisive half-time, is near the yardstick | link 2: 1.2371 [1.1847, 1.2901]. Link 1: 0.9924 [0.9829, 1.0016] | 36,237 (21,412 decisive half-times) | yes. Link 2: 1.2313 [1.1514, 1.3135] and 1.2426 [1.1784, 1.3074]. Link 1: 0.9890 [0.9771, 0.9999] and 0.9957 [0.9816, 1.0095] | exploratory |
| C4 | The completion excess is largest after a deficit of 2 goals or more | 1.7139 [1.4607, 1.9662] (163 against 95.1). After a deficit of 1: 1.2054 [1.1549, 1.2576] | 5,957 and 15,455 half-times | not measured | exploratory |
| C5 | Comebacks exceed the yardstick at every strength of the favourite | O/E from 1.1620 to 1.3033 in the 7 bands. The lowest lower bound is 1.0199 | 36,237 | not measured | exploratory |
| C6 | The comeback excess is largest at low expected goals, and smallest at high expected goals | up to 2.2 expected goals: 1.5472 [1.2029, 1.9030]. Above 3.4: 1.0759 [0.9356, 1.1976]. The 4 bands between: 1.2172 to 1.2995 | 1,774 and 2,708 | not measured | exploratory |
| C7 | 7+ goals happen less often than the yardstick expects | O/E 0.8250 [0.7644, 0.8853] (812 against 984.3) | 36,237 | yes: 0.8369 [0.7469, 0.9274] in 2024, 0.8137 [0.7362, 0.8911] in 2025 | exploratory |
| C8 | 0-0 and 1-1 happen a little more often than the yardstick expects | 0-0: 1.0577 [1.0140, 1.1022]. 1-1: 1.0580 [1.0250, 1.0891] | 36,237 | 1-1 yes: 1.0550 [1.0101, 1.0983], 1.0610 [1.0163, 1.1074]. 0-0 only in 2024: 1.0823 [1.0197, 1.1500]; 2025: 1.0340 [0.9696, 1.1026] | exploratory |
| C9 | One first-half share for all matches does not cause the comeback excess | share 0.4471. By band: 0.4416 to 0.4563. A shift of ±0.02 gives a comeback O/E from 1.2023 to 1.2892 | 36,237 | yes: 0.4482 in 2024, 0.4460 in 2025 | exploratory |
| C10 | Proportional margin removal in place of Shin's method changes the result very little | comebacks 1.2286 [1.1745, 1.2833]. 7+ goals 0.8263 [0.7657, 0.8868] | 36,237 | not measured | exploratory |

## Observed and expected, all matches

| quantity | observed | expected | O/E [95% interval] | 2024 | 2025 |
|---|---|---|---|---|---|
| goals | 99,564 | 100,686.8 | 0.9888 [0.9825, 0.9948] | 0.9869 | 0.9907 |
| home goals | 54,803 | 55,595.6 | 0.9857 [0.9764, 0.9950] | — | — |
| away goals | 44,761 | 45,091.2 | 0.9927 [0.9836, 1.0011] | — | — |
| comeback, either side | 1,891 | 1,521.7 | 1.2427 [1.1885, 1.2981] | 1.2317 | 1.2532 |
| comeback, home side | 1,075 | 847.7 | 1.2682 [1.1966, 1.3451] | 1.2395 | 1.2957 |
| comeback, away side | 816 | 674.1 | 1.2106 [1.1247, 1.2969] | 1.2218 | 1.1998 |
| decisive half-time (link 1) | 21,412 | 21,575.3 | 0.9924 [0.9829, 1.0016] | 0.9890 | 0.9957 |
| completion from the HT score (link 2) | 1,891 | 1,528.6 | 1.2371 [1.1847, 1.2901] | 1.2313 | 1.2426 |
| 7+ goals | 812 | 984.3 | 0.8250 [0.7644, 0.8853] | 0.8369 | 0.8137 |
| 0-0 | 2,557 | 2,417.5 | 1.0577 [1.0140, 1.1022] | 1.0823 | 1.0340 |
| 1-1 | 4,237 | 4,004.6 | 1.0580 [1.0250, 1.0891] | 1.0550 | 1.0610 |

The observed mean is 2.7476 goals per match: 1.2284 in the first half and 1.5192 in the second.

## By the favourite's win chance

The favourite is the side with the higher Shin win probability. Each cell is O/E [95% interval]. The last column is the observed first-half share of the goals.

| win chance | matches | goals | comeback | link 1 | link 2 | 7+ goals | first-half share |
|---|---|---|---|---|---|---|---|
| up to 0.40 | 6,511 | 0.9883 [0.9724, 1.0043] | 1.1845 [1.0640, 1.3034] | 0.9713 [0.9517, 0.9940] | 1.2128 [1.0916, 1.3309] | 0.6884 [0.5368, 0.8553] | 0.4435 |
| 0.40 to 0.45 | 7,565 | 0.9729 [0.9593, 0.9859] | 1.2744 [1.1479, 1.4006] | 1.0001 [0.9809, 1.0205] | 1.2653 [1.1450, 1.3900] | 0.7540 [0.6400, 0.8668] | 0.4504 |
| 0.45 to 0.50 | 6,071 | 0.9892 [0.9758, 1.0024] | 1.2609 [1.1302, 1.3915] | 0.9761 [0.9541, 0.9975] | 1.2583 [1.1315, 1.3811] | 0.8484 [0.6932, 1.0147] | 0.4439 |
| 0.50 to 0.55 | 4,917 | 0.9942 [0.9785, 1.0103] | 1.1620 [1.0199, 1.3033] | 0.9736 [0.9510, 0.9971] | 1.1832 [1.0449, 1.3245] | 0.9792 [0.8016, 1.1549] | 0.4416 |
| 0.55 to 0.60 | 4,019 | 0.9883 [0.9715, 1.0058] | 1.3033 [1.1490, 1.4620] | 0.9984 [0.9731, 1.0229] | 1.2629 [1.1171, 1.4092] | 0.8539 [0.7116, 1.0055] | 0.4500 |
| 0.60 to 0.70 | 4,410 | 1.0038 [0.9893, 1.0190] | 1.2542 [1.0733, 1.4369] | 1.0228 [1.0016, 1.0452] | 1.2128 [1.0504, 1.3628] | 0.8257 [0.6909, 0.9617] | 0.4530 |
| above 0.70 | 2,744 | 0.9955 [0.9730, 1.0190] | 1.2925 [1.1177, 1.4767] | 1.0240 [0.9996, 1.0472] | 1.2633 [1.1030, 1.4319] | 0.8396 [0.7057, 0.9797] | 0.4481 |

## By expected goals

The expected goals of a match are the sum of its two fitted rates.

| expected goals | matches | goals | comeback | link 1 | link 2 | 7+ goals | first-half share |
|---|---|---|---|---|---|---|---|
| up to 2.2 | 1,774 | 1.0231 [0.9853, 1.0633] | 1.5472 [1.2029, 1.9030] | 0.9722 [0.9106, 1.0329] | 1.6118 [1.2736, 1.9235] | 0.7077 [0.3068, 1.1908] | 0.4563 |
| 2.2 to 2.5 | 8,140 | 1.0016 [0.9887, 1.0146] | 1.2295 [1.0984, 1.3613] | 0.9667 [0.9445, 0.9889] | 1.2509 [1.1249, 1.3750] | 0.9133 [0.7221, 1.1133] | 0.4455 |
| 2.5 to 2.8 | 10,524 | 0.9862 [0.9746, 0.9980] | 1.2172 [1.1231, 1.3199] | 0.9904 [0.9751, 1.0055] | 1.1927 [1.1037, 1.2891] | 0.8138 [0.7006, 0.9342] | 0.4422 |
| 2.8 to 3.1 | 8,797 | 0.9844 [0.9723, 0.9964] | 1.2658 [1.1615, 1.3720] | 1.0056 [0.9892, 1.0221] | 1.2439 [1.1454, 1.3416] | 0.8229 [0.7221, 0.9237] | 0.4488 |
| 3.1 to 3.4 | 4,294 | 0.9886 [0.9741, 1.0040] | 1.2995 [1.1423, 1.4623] | 1.0053 [0.9815, 1.0282] | 1.2846 [1.1416, 1.4277] | 0.8129 [0.6705, 0.9640] | 0.4494 |
| above 3.4 | 2,708 | 0.9702 [0.9490, 0.9923] | 1.0759 [0.9356, 1.1976] | 1.0148 [0.9882, 1.0413] | 1.1110 [0.9817, 1.2357] | 0.8173 [0.6748, 0.9786] | 0.4527 |

## Where the comeback excess sits

Decisive half-times only. "Expected" is the yardstick's completion from the half-time score that happened.

| who is behind at half-time | half-times | observed | expected | O/E [95% interval] |
|---|---|---|---|---|
| the favourite | 7,662 | 1,212 | 957.3 | 1.2661 [1.1975, 1.3346] |
| the underdog | 13,750 | 679 | 571.3 | 1.1885 [1.1060, 1.2701] |
| by 1 goal | 15,455 | 1,728 | 1,433.5 | 1.2054 [1.1549, 1.2576] |
| by 2 goals or more | 5,957 | 163 | 95.1 | 1.7139 [1.4607, 1.9662] |
| the home side | 9,233 | 1,075 | 850.6 | 1.2638 [1.1957, 1.3337] |
| the away side | 12,179 | 816 | 678.0 | 1.2036 [1.1223, 1.2824] |

The excess is in every split. The favourite and the underdog, and the home side and the away side, have intervals that overlap.

## The first-half share

The yardstick splits each rate into halves with one share: 0.4471 of all goals came in the first half.

- By the favourite's win chance: 0.4416 to 0.4530. By expected goals: 0.4422 to 0.4563.
- The favourite's goals: 0.4480 [0.4443, 0.4516]. The underdog's goals: 0.4457 [0.4412, 0.4501].
- Per season cohort: 0.4482 [0.4431, 0.4525] in 2024, 0.4460 [0.4422, 0.4500] in 2025.
- Other shares: with 0.4271, the yardstick expects 1,572.8 comebacks (O/E 1.2023). With 0.4671, it expects 1,466.8 (O/E 1.2892).

So the share changes by about 0.01 between bands. A change of 0.02 does not remove the comeback excess.

## Method

- **Prices:** Bet365's opening ("Initial") prices from the league page: the 1X2 (S1.16–18) and the O/U line with its two prices (S1.19–21). Bet365 publishes them about 7 days before kickoff.
- **Margin:** the 1X2 margin goes by Shin's method (`analysis/methods/shin.py`; `ALL/SHIN.md`, C2–C4). The O/U margin goes proportionally (S2.24). It is a two-way market near 50/50, where the two methods are close.
- **The model:** the basic goal model (`notes/REFERENCE/MARKET_COMEBACKS.md`, "The basic goal model"): independent Poisson goals per team.
- **The fit:** a grid of home and away rates from 0.02 to 6.00, in steps of 0.02. For each match, the grid point nearest to three market numbers: Shin's home and away win probabilities, and the fair over chance at the opening line. The distance is Euclidean, in probability, with one KD-tree per line. A quarter line (2.25) splits the stake between its two neighbours. An integer line returns the stake when the total equals it (`analysis/methods/yardstick.py:fair_over`).
- **The fit error:** median 0.0106, 99th percentile 0.0295. 12 matches have an error above 0.05. The largest is 0.2239: match 2592387, Holland Eredivisie 2024-2025.
- **Halves:** one first-half share for all matches, 0.4471. It is the share of all goals of the priced matches that came in the first half.
- **Expected values per match:** the comeback chance (for each half-time deficit d, the chance to be behind by d at half-time, times the chance to win the second half by more than d); the chance of a decisive half-time; the completion from the half-time score that happened; the chances of 7+ goals, 0-0 and 1-1; and the goals.
- **Links:** link 1 is a decisive half-time. Link 2 is the completion from the half-time score (`notes/REFERENCE/MARKET_COMEBACKS.md`, "The two links").
- **O/E and intervals:** the sum of the observed values, divided by the sum of the expected values. A cluster bootstrap over the 144 league-seasons gives the interval, with 2,000 resamples (`analysis/stats.py:cluster_bootstrap_ratio_ci`).
- **Bands:** the favourite's Shin win probability, cut at 0.40, 0.45, 0.50, 0.55, 0.60 and 0.70. The expected goals, cut at 2.2, 2.5, 2.8, 3.1 and 3.4.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025 (17,756 matches). 2025 holds 2025 and 2025-2026 (18,481).

## Caveats

- **The share comes from the same goals.** The first-half share is one parameter, taken from the outcomes of these matches. It also helps link 1: the model's first-half goals equal the observed ones, up to the goal ratio of C1. So link 1 near 1 is a weak check. For the same reason, this doc gives no O/E for each half: it would equal C1 by construction.
- **Calibration of the yardstick (rule 3).** The goal O/E goes from 1.0231 at up to 2.2 expected goals to 0.9702 above 3.4. So the prices spread the expected goals a little too wide. Link 1 goes from 0.9713 for the most balanced matches to 1.0240 for the strongest favourites. Both changes are small next to C2.
- **By league:** this doc does not test the yardstick per league. `PER_LEAGUE/ODDS_YARDSTICK.md` does that (`notes/WORKING/PLAN_2026-10-16_ANALYSIS_MIGRATION.md`, step 2).
- **No score effects in the model.** The basic goal model keeps each rate constant in a half, whatever the score. C3 and C4 show that the second half turns more results around than that model expects. They do not show why. `ALL/SCORE_EFFECTS.md` measures the second-half rates after each half-time score.
- **The tail.** The O/U price fixes the chance of goals above the line, not the chance of 7 or more. C7 says that the model's tail is too heavy for these matches.
- **Low scores.** C8 is the known low-score dependency that independent goals miss (`notes/REFERENCE/STATS_PRIMER.md`, Dixon–Coles, "The low-score dependency (tau)").
- **Looks:** 11 quantities for all matches; 9 for each of the 2 cohorts; 6 for each of 7 strength bands and 6 expected-goal bands; 6 trailer splits; 41 cells of win chance by expected goals; 4 share checks; 3 share settings; 2 rows with proportional removal. The claims come from this set. The 41 cells are in the runner's output only: no claim reads a cell.
- **Not profit.** A comeback above the yardstick does not show value. The value needs the 2/1 and 1/2 prices, and nowgoal does not show them.
- **Opening prices only.** The closing prices are on the detail page, which the staged pipeline does not read yet.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-18 | 144 league-seasons, 36,238 matches | first run |
