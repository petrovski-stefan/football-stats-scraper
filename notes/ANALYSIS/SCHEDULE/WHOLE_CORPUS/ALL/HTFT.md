# HTFT — the nine half-time/full-time results on all matches

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 and O/U prices, through the odds yardstick (`ALL/ODDS_YARDSTICK.md`). Outcome: the half-time and full-time goals (S1.12–15), and S2.26 and the 7+ total from S2.01.
- **Corpus:** 2026-10-18: 144 league-seasons, 36,238 matches. 36,237 of them have both opening markets.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.htft`, at the commit that adds this doc.
- **Kind:** empirical. Under the basic goal model, the opening prices imply a chance for each HT/FT result (`notes/REFERENCE/MARKET_COMEBACKS.md`, "HT/FT notation"). The doc measures how far the results are from these chances.

## Question

The HT/FT market has nine results: 1/1, 1/X, 1/2, X/1, X/X, X/2, 2/1, 2/X and 2/2. How often does each one happen, against the yardstick? How well does the yardstick itself rank matches for a comeback and for 7+ goals?

2/1 and 1/2 are the home and away comebacks. Their numbers are those of `ALL/ODDS_YARDSTICK.md` (C2): the yardstick's 2/1 chance is its home comeback chance, within 3.3e-08 per match.

## Claims

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | A half-time lead ends in a draw more often than the yardstick expects | 1/X: 1.1428 [1.0915, 1.1912] (1,924 against 1,683.6). 2/X: 1.0881 [1.0355, 1.1443] (1,832 against 1,683.6) | 36,237 | 1/X yes: 1.1620 [1.0912, 1.2281], 1.1244 [1.0498, 1.2010]. 2/X only in 2025: 1.1139 [1.0311, 1.1901]; 2024: 1.0612 [0.9872, 1.1361] | exploratory |
| C2 | A half-time lead ends in a win less often than the yardstick expects | 1/1: 0.9577 [0.9411, 0.9747] (9,439 against 9,856.0). 2/2: 0.9262 [0.9050, 0.9472] (6,326 against 6,830.3) | 36,237 | yes. 1/1: 0.9582 [0.9332, 0.9810], 0.9572 [0.9329, 0.9819]. 2/2: 0.9193 [0.8884, 0.9519], 0.9327 [0.9049, 0.9617] | exploratory |
| C3 | A level half-time stays level more often than the yardstick expects. It becomes a win as often as expected | X/X: 1.0485 [1.0233, 1.0736] (5,493 against 5,238.9). X/1: 1.0017 [0.9750, 1.0298]. X/2: 0.9756 [0.9458, 1.0042] | 36,237 | X/X yes: 1.0536 [1.0189, 1.0889], 1.0436 [1.0077, 1.0807]. X/1 and X/2: each interval includes 1 in both cohorts | exploratory |
| C4 | The yardstick's own top N for a comeback hits between 1.28 and 1.53 times the base rate | top 100: 0.0800 [0.0374, 0.1356], lift 1.5330. Top 1,000: 0.0780 [0.0629, 0.0931], lift 1.4947. Top 5,000: 0.0674 [0.0616, 0.0733], lift 1.2916. Base rate 0.0522 | 36,237 | not measured | exploratory |
| C5 | The yardstick's own top N for 7+ goals hits between 2.35 and 6.25 times the base rate. At 5 of the 6 values of N, the hit rate is below the yardstick's own chance | top 250: 0.1400 [0.1017, 0.1795], lift 6.2478. Top 1,000: 0.0810 [0.0630, 0.1004], lift 3.6148, against a chance of 0.0971. Top 5,000: 0.0526 [0.0447, 0.0607], lift 2.3474, against 0.0646. Base rate 0.0224 | 36,237 | not measured | exploratory |

## The nine results, observed and expected

| HT/FT | observed | expected | O/E [95% interval] | observed share | 2024 | 2025 |
|---|---|---|---|---|---|---|
| 1/1 | 9,439 | 9,856.0 | 0.9577 [0.9411, 0.9747] | 0.2605 | 0.9582 | 0.9572 |
| 1/X | 1,924 | 1,683.6 | 1.1428 [1.0915, 1.1912] | 0.0531 | 1.1620 | 1.1244 |
| 1/2 | 816 | 674.1 | 1.2106 [1.1247, 1.2969] | 0.0225 | 1.2218 | 1.1998 |
| X/1 | 5,340 | 5,330.8 | 1.0017 [0.9750, 1.0298] | 0.1474 | 1.0088 | 0.9949 |
| X/X | 5,493 | 5,238.9 | 1.0485 [1.0233, 1.0736] | 0.1516 | 1.0536 | 1.0436 |
| X/2 | 3,992 | 4,092.0 | 0.9756 [0.9458, 1.0042] | 0.1102 | 0.9776 | 0.9736 |
| 2/1 | 1,075 | 847.7 | 1.2682 [1.1966, 1.3451] | 0.0297 | 1.2395 | 1.2957 |
| 2/X | 1,832 | 1,683.6 | 1.0881 [1.0355, 1.1443] | 0.0506 | 1.0612 | 1.1139 |
| 2/2 | 6,326 | 6,830.3 | 0.9262 [0.9050, 0.9472] | 0.1746 | 0.9193 | 0.9327 |

## The yardstick's top N

The N matches with the highest yardstick chance. "Yardstick" is the mean chance in those N matches. The lift is the hit rate divided by the base rate.

| N | comeback: hits | rate [95% interval] | yardstick | lift | 7+ goals: hits | rate [95% interval] | yardstick | lift |
|---|---|---|---|---|---|---|---|---|
| 100 | 8 | 0.0800 [0.0374, 0.1356] | 0.0672 | 1.5330 | 12 | 0.1200 [0.0706, 0.1739] | 0.1437 | 5.3552 |
| 250 | 18 | 0.0720 [0.0442, 0.0971] | 0.0647 | 1.3797 | 35 | 0.1400 [0.1017, 0.1795] | 0.1268 | 6.2478 |
| 500 | 39 | 0.0780 [0.0571, 0.0967] | 0.0627 | 1.4947 | 51 | 0.1020 [0.0758, 0.1288] | 0.1113 | 4.5519 |
| 1,000 | 78 | 0.0780 [0.0629, 0.0931] | 0.0606 | 1.4947 | 81 | 0.0810 [0.0630, 0.1004] | 0.0971 | 3.6148 |
| 2,000 | 134 | 0.0670 [0.0586, 0.0753] | 0.0583 | 1.2839 | 141 | 0.0705 [0.0569, 0.0835] | 0.0828 | 3.1462 |
| 5,000 | 337 | 0.0674 [0.0616, 0.0733] | 0.0547 | 1.2916 | 263 | 0.0526 [0.0447, 0.0607] | 0.0646 | 2.3474 |

A candidate rule must beat these rates at the same N to add anything to the prices (the candidate protocol, `notes/ANALYSIS/CLAUDE.md` §6).

## Method

- **The yardstick:** `ALL/ODDS_YARDSTICK.md` (`analysis/methods/yardstick.py`), with the same first-half share, 0.4471.
- **The nine chances:** for each match, the sum over the half-time margin and the second-half margin, each from −12 to 12, of the two Skellam chances. The full-time margin is their sum (`analysis/methods/yardstick.py:htft_cells`). The nine chances of a match add up to 1 within 8.1e-07.
- **Observed results:** the 1X2 code of the half-time margin, then of the full-time margin.
- **O/E and intervals:** the observed count divided by the sum of the chances. A cluster bootstrap over the 144 league-seasons gives the interval, with 2,000 resamples (`analysis/stats.py:observed_expected`).
- **Top N:** the matches sorted by the yardstick's chance, highest first. Many matches share one point of the rate grid and so one chance. Ties at the cut go by match id, so the same N always takes the same matches. The interval of a hit rate is a cluster bootstrap over league-seasons (`notes/ANALYSIS/CLAUDE.md` §5, rule 5). The candidate protocol names a Wilson interval (§6). The cluster interval also counts the league-seasons.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025 (17,756 matches). 2025 holds 2025 and 2025-2026 (18,481).

## Caveats

- **The cells share their data.** The three cells of one half-time result add up to the count of that half-time result. That count is near the yardstick (`ALL/ODDS_YARDSTICK.md`, C3: link 1 is 0.9924). So, in one row, a cell above the yardstick needs a cell below it. C1, C2 and the comebacks are one fact seen three ways: after a half-time lead, full-time results move from wins to draws and defeats.
- **1/X and 2/X have the same expected count, 1,683.6.** That is by construction. The yardstick uses one first-half share for both teams. Then, for each match, a home lead and an away lead have the same chance to end level. It is not a finding.
- **Why the cells move.** C1 and C2 agree with the second-half score effects (`ALL/SCORE_EFFECTS.md`, C1–C3). C3 agrees with the low-score excess (`ALL/ODDS_YARDSTICK.md`, C8) and with the slow second half after 0-0 (`ALL/SCORE_EFFECTS.md`, C5). This doc does not show a cause.
- **The top N are not a rule.** They show how far the prices alone can sort matches. The comeback hit rate is above the yardstick's own chance at every N, as the comeback excess of `ALL/ODDS_YARDSTICK.md` (C2) predicts.
- **Looks:** 9 results for all matches and for each of the 2 cohorts, and 6 values of N for 2 targets: 39 numbers. The claims come from these.
- **Not profit.** The HT/FT prices are not in the data. So the doc cannot say if a cell above the yardstick is also above its price.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-18 | 144 league-seasons, 36,238 matches | first run |
