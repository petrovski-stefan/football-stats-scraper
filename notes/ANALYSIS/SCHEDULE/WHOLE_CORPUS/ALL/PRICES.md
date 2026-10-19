# PRICES — the returns of the opening prices, their margins, and the 7+ tail

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 prices (S1.16–18), the opening O/U line and prices (S1.19–21), the opening AH line and prices (S1.22–24), and the proportional probabilities (S2.17–19). For the 7+ tail, the odds yardstick (`ODDS_YARDSTICK.md`). Outcome: the full-time goals (S1.14–15) and their total (S2.01).
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 36,237 of them have all three opening markets.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.prices`, at the commit that adds this doc.
- **Kind:** empirical: the size of the margin, and how the returns change with the price (`notes/REFERENCE/MARKET_COMEBACKS.md` §6, "Empirical").

## Question

What does a flat stake on each opening price return, by price band, in the 1X2, the O/U and the AH? How large are the O/U and AH margins, and which lines do they use? And why do 7+ matches fall short of the yardstick (`ODDS_YARDSTICK.md`, C7): because the totals are too high, or because of the shape of the goal counts?

## Claims

A return is the mean profit of a stake of 1 at the opening price. The cost of a margin m is 1 / (1 + m) − 1: the return of a fair price after that margin.

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | In the 1X2, the return falls as the price grows: the favourite–longshot bias. Shin's probabilities expect most of the fall. Above a price of 5.5, the return is lower than even Shin expects, but the intervals are wide | up to 1.3: −0.0093 [−0.0293, 0.0095]. 3.5 to 5.5: −0.1084 [−0.1285, −0.0892], Shin expects −0.1074. 5.5 to 8.0: −0.2172 [−0.2709, −0.1615], Shin −0.1559. 8.0 to 13.0: −0.3209 [−0.4400, −0.1832], Shin −0.2097. Proportional probabilities expect −0.0656 to −0.0799 in every band | 36,237 matches, 3 bets each | yes: up to 1.3, −0.0042 and −0.0146; 8.0 to 13.0, −0.3910 and −0.2460 | exploratory |
| C2 | A bet on the away win returns less than its price expects, also under Shin's method | away −0.1205 [−0.1382, −0.1031], Shin expects −0.0962. Home −0.0727 [−0.0851, −0.0596], Shin −0.0728. Draw −0.0832 [−0.1013, −0.0665], Shin −0.0983 | 36,237 bets on each side | yes: away −0.1218 and −0.1193 | exploratory |
| C3 | The O/U lines are a little too far apart: at the lines 3.0 to 3.5, the under returns more than the over; at the lines 2.0 and 2.25, the over returns more | 3.5: over −0.1106 [−0.1650, −0.0574], under 0.0159 [−0.0359, 0.0686]. 3.25: over −0.0643, under −0.0163. 2.25: over −0.0260, under −0.0476. The cost of the margin is −0.0429 to −0.0471 at each of these lines | 36,237 | yes, at 3.5: over −0.1118 and −0.1096, under 0.0252 and 0.0083 | exploratory |
| C4 | Large Asian handicaps are too large: the side that gives 1 goal or more returns less than the cost of the margin, and the side that receives them returns near 0 | home gives 1 or more: home −0.0701 [−0.0943, −0.0445], away −0.0022 [−0.0277, 0.0221]. Away gives 1 or more: away −0.0949 [−0.1308, −0.0598], home 0.0193 [−0.0149, 0.0547]. The cost of the margin is about −0.043 | 5,784 and 1,884 | yes: the giving side −0.0632 and −0.0769 (home), −0.0716 and −0.1184 (away) | exploratory |
| C5 | The O/U and AH margins are about 0.05, smaller than the 1X2 margin. Half of their lines are quarter lines | median margin: O/U 0.0500, AH 0.0500, 1X2 0.0828. Quarter lines: O/U 0.5059, AH 0.5057 | 36,237 | the cost of the O/U margin: −0.0397 in 2024, −0.0473 in 2025 | exploratory |
| C6 | Most of the 7+ deficit comes from the shape of the goal counts, not from the totals. With each band's totals matched to its observed goals, 7+ matches are still fewer than Poisson expects | 7+ O/E 0.8250 [0.7644, 0.8853] on the market's totals, 0.8816 [0.8176, 0.9461] on the matched totals: the matching closes 0.3673 of the gap. Above 2.5 expected goals, the variance of the goal totals is 0.9553 to 0.9832 of their mean | 36,237 | yes: 0.8964 [0.7995, 0.9945] and 0.8674 [0.7863, 0.9474]; the matching closes 0.4072 and 0.3325 | exploratory |

## 1X2 by price band

Each match gives three bets, one on each outcome.

| price | bets | mean price | hit rate | return [95% interval] | proportional expects | Shin expects | 2024 | 2025 |
|---|---|---|---|---|---|---|---|---|
| (1.0, 1.3] | 2,046 | 1.2235 | 0.8123 | −0.0093 [−0.0293, 0.0095] | −0.0770 | −0.0453 | −0.0042 | −0.0146 |
| (1.3, 1.6] | 5,892 | 1.4730 | 0.6490 | −0.0468 [−0.0649, −0.0280] | −0.0799 | −0.0525 | −0.0331 | −0.0599 |
| (1.6, 2.0] | 12,605 | 1.8182 | 0.5173 | −0.0641 [−0.0816, −0.0451] | −0.0788 | −0.0590 | −0.0622 | −0.0659 |
| (2.0, 2.6] | 17,080 | 2.3118 | 0.4059 | −0.0669 [−0.0822, −0.0507] | −0.0781 | −0.0689 | −0.0718 | −0.0623 |
| (2.6, 3.5] | 36,110 | 3.1678 | 0.2903 | −0.0858 [−0.0979, −0.0733] | −0.0778 | −0.0864 | −0.0757 | −0.0954 |
| (3.5, 5.5] | 28,135 | 4.1823 | 0.2171 | −0.1084 [−0.1285, −0.0892] | −0.0776 | −0.1074 | −0.1175 | −0.0996 |
| (5.5, 8.0] | 4,752 | 6.6328 | 0.1193 | −0.2172 [−0.2709, −0.1615] | −0.0767 | −0.1559 | −0.2172 | −0.2171 |
| (8.0, 13.0] | 1,695 | 10.0959 | 0.0702 | −0.3209 [−0.4400, −0.1832] | −0.0723 | −0.2097 | −0.3910 | −0.2460 |
| (13.0, inf] | 396 | 18.2449 | 0.0505 | −0.1162 [−0.5014, 0.3061] | −0.0656 | −0.3150 | 0.3250 | −0.5663 |

| side | mean price | hit rate | return [95% interval] | proportional expects | Shin expects | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| home | 2.5279 | 0.4375 | −0.0727 [−0.0851, −0.0596] | −0.0778 | −0.0728 | −0.0694 | −0.0758 |
| draw | 3.7341 | 0.2552 | −0.0832 [−0.1013, −0.0665] | −0.0778 | −0.0983 | −0.0814 | −0.0849 |
| away | 3.7140 | 0.3073 | −0.1205 [−0.1382, −0.1031] | −0.0778 | −0.0962 | −0.1218 | −0.1193 |

## O/U by opening line

Lines with 200 matches or more. A quarter line splits the stake between its two neighbours, and a whole line returns the stake on a push.

| line | matches | over [95% interval] | under [95% interval] | cost of the margin |
|---|---|---|---|---|
| 2 | 2,639 | −0.0229 [−0.0585, 0.0138] | −0.0419 [−0.0798, −0.0056] | −0.0437 |
| 2.25 | 7,900 | −0.0260 [−0.0473, −0.0061] | −0.0476 [−0.0680, −0.0267] | −0.0429 |
| 2.5 | 9,246 | −0.0500 [−0.0694, −0.0296] | −0.0360 [−0.0560, −0.0170] | −0.0430 |
| 2.75 | 7,541 | −0.0410 [−0.0608, −0.0209] | −0.0352 [−0.0558, −0.0144] | −0.0432 |
| 3 | 4,792 | −0.0460 [−0.0712, −0.0219] | −0.0233 [−0.0476, 0.0015] | −0.0445 |
| 3.25 | 2,409 | −0.0643 [−0.0980, −0.0285] | −0.0163 [−0.0514, 0.0175] | −0.0451 |
| 3.5 | 1,083 | −0.1106 [−0.1650, −0.0574] | 0.0159 [−0.0359, 0.0686] | −0.0471 |
| 3.75 | 305 | −0.0253 [−0.1214, 0.0686] | −0.0583 [−0.1504, 0.0350] | −0.0456 |
| all lines | 36,237 | −0.0429 [−0.0520, −0.0344] | −0.0343 [−0.0427, −0.0253] | −0.0436 |

## AH by opening handicap

A positive line means that the home team gives the handicap (S1.22).

| handicap | matches | home side [95% interval] | away side [95% interval] | cost of the margin |
|---|---|---|---|---|
| home gives 1 or more | 5,784 | −0.0701 [−0.0943, −0.0445] | −0.0022 [−0.0277, 0.0221] | −0.0432 |
| home gives 0.25 to 0.75 | 15,906 | −0.0324 [−0.0458, −0.0192] | −0.0461 [−0.0595, −0.0325] | −0.0432 |
| level | 5,554 | −0.0458 [−0.0664, −0.0266] | −0.0187 [−0.0379, 0.0022] | −0.0438 |
| away gives 0.25 to 0.75 | 7,109 | −0.0235 [−0.0445, −0.0025] | −0.0551 [−0.0772, −0.0328] | −0.0436 |
| away gives 1 or more | 1,884 | 0.0193 [−0.0149, 0.0547] | −0.0949 [−0.1308, −0.0598] | −0.0442 |
| all lines | 36,237 | −0.0360 [−0.0462, −0.0263] | −0.0392 [−0.0493, −0.0288] | −0.0434 |

## Margins and lines

| market | 1% | 5% | median | 95% | 99% | mean |
|---|---|---|---|---|---|---|
| 1X2 | 0.0505 | 0.0581 | 0.0828 | 0.1173 | 0.1233 | 0.0848 |
| O/U | 0.0257 | 0.0283 | 0.0500 | 0.0556 | 0.0588 | 0.0457 |
| AH | 0.0257 | 0.0274 | 0.0500 | 0.0556 | 0.0592 | 0.0455 |

The 1X2 margin is also in `SHIN.md` (Caveats, median 0.08277).

| O/U line | 1.5 | 1.75 | 2.0 | 2.25 | 2.5 | 2.75 | 3.0 | 3.25 | 3.5 | 3.75 | 4.0 | 4.25 | 4.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| matches | 7 | 146 | 2,639 | 7,900 | 9,246 | 7,541 | 4,792 | 2,409 | 1,083 | 305 | 129 | 32 | 8 |
| share | 0.0002 | 0.0040 | 0.0728 | 0.2180 | 0.2552 | 0.2081 | 0.1322 | 0.0665 | 0.0299 | 0.0084 | 0.0036 | 0.0009 | 0.0002 |

## The 7+ tail

The yardstick's expected goals, against the observed goals, by band of expected goals:

| expected goals | matches | model mean | observed mean | observed / model | variance / mean |
|---|---|---|---|---|---|
| up to 2.2 | 1,774 | 2.1301 | 2.1793 | 1.0231 | 1.0148 |
| 2.2 to 2.5 | 8,140 | 2.3825 | 2.3862 | 1.0016 | 1.0054 |
| 2.5 to 2.8 | 10,524 | 2.6551 | 2.6184 | 0.9862 | 0.9832 |
| 2.8 to 3.1 | 8,797 | 2.9438 | 2.8978 | 0.9844 | 0.9615 |
| 3.1 to 3.4 | 4,294 | 3.2264 | 3.1898 | 0.9886 | 0.9553 |
| above 3.4 | 2,708 | 3.6269 | 3.5188 | 0.9702 | 0.9784 |

Matches with k goals or more:

| goals | observed | Poisson on the market's totals | Poisson on the matched totals |
|---|---|---|---|
| 5+ | 5,320 | 5,574.5 | 5,382.1 |
| 6+ | 2,235 | 2,478.3 | 2,358.1 |
| 7+ | 812 | 984.3 | 921.0 |
| 8+ | 271 | 354.0 | 325.1 |

## Method

- **The bets:** a stake of 1 on each outcome at Bet365's opening price, with no selection.
- **1X2:** a bet wins the price minus 1, or loses 1. The bands are the price bands of `SHIN.md` (`analysis/methods/shin.py:PRICE_EDGES`). "Proportional expects" and "Shin expects" are the mean of probability × price − 1, with each method's probabilities.
- **O/U and AH:** Asian settlement (`analysis/schedule/whole_corpus/all/prices.py:settle`). A quarter line puts half the stake on each neighbouring line. On a whole line, a result equal to the line returns the stake. The O/U over wins above the line. The AH home side wins when the home team's goal lead is above the line.
- **The cost of a margin:** 1 / (1 + m) − 1 for a two-way market with margin m. It is the return of a price that is fair after the margin. With pushes and quarter lines, this is an approximation.
- **Intervals:** a cluster bootstrap over the league-seasons, with 2,000 resamples (`analysis/stats.py:cluster_bootstrap_ci`).
- **The 7+ tail:** the yardstick of `ODDS_YARDSTICK.md`, on the 36,237 matches with both opening markets. The bands are those of its expected goals (`analysis/methods/yardstick.py:TOTAL_EDGES`). The matched totals: each match's expected goals, times the observed / model goals of its band. Then the Poisson chance of 7 goals or more. "Closes" is (market − matched) / (market − observed), with the expected counts.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025. 2025 holds 2025 and 2025-2026. In the cohorts, the 7+ tail matches the totals inside each cohort.

## Caveats

- **Not profit.** No band in this doc returns more than 0 with an interval above 0. A return near 0, such as the side that receives a large handicap (C4), is not a strategy. The bets here are all bets in a band, with no selection, at the opening price. A real bettor gets other prices, and limits.
- **Many looks.** 9 price bands and 3 sides, 9 O/U rows with 2 sides, and 6 AH rows with 2 sides, each for all matches and for 2 cohorts; 3 margins; 13 lines; 6 bands, 4 counts and 2 O/E values of the 7+ tail, also per cohort. The claims are patterns that run over several bands and agree in both cohorts, not single cells.
- **C1 is `SHIN.md` C4 in money.** That doc shows the same bias as rates: proportional probabilities are too low for favourites and too high for long shots.
- **C3 is the yardstick's calibration in money.** `ODDS_YARDSTICK.md` (Caveats) finds that the prices spread the expected goals a little too wide: the goal O/E goes from 1.0231 at up to 2.2 expected goals to 0.9702 above 3.4.
- **C4 and the score effects.** A team ahead by 1 at half-time scores fewer second-half goals than the yardstick expects (`SCORE_EFFECTS.md`, C3). A team ahead by 2 or more is near it (C4 there). So a large favourite that leads by 1 can win by less than the basic goal model says. This can explain part of C4 here. This doc does not test it.
- **C3 at 3.75.** The line 3.75 goes the other way, but it has only 305 matches, and both of its intervals include the cost of the margin.
- **C6 matches the totals in-sample.** The matched totals use the goals of the same matches, so they equal the observed mean goals of each band by construction. Only the part of the gap that remains after that is about the shape. The shape agrees with the dispersion of the goals given the yardstick, 0.9730 (`PER_LEAGUE/ODDS_YARDSTICK.md`, Method).
- **The variance in C6 is a lower limit of the shape effect.** The matches of a band have different expected goals, and that spread adds variance. So the variance of a match's goals around its own expected goals is lower than the table shows.
- **Opening prices only, Bet365 only.** The closing prices and the other bookmakers are on the detail page, which the staged pipeline does not read yet.
