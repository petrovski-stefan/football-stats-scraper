# SHIN — Shin's method on all matches

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 prices (S1.16–18) and the proportional probabilities (S2.17–19). Outcome: the full-time goals (S1.14–15).
- **Corpus:** 2026-10-16: 144 league-seasons, 36,238 matches. 36,237 of them have all three opening 1X2 prices. The match without prices is Cyprus D1's awarded match, 2609242.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.shin`, at the commit that adds this doc.
- **Kind:** empirical. The doc compares two ways to remove the margin with the full-time results.

## Question

Bet365's opening 1X2 prices have a margin. Proportional removal and Shin's method remove it in two different ways. Which method gives probabilities that agree better with the full-time results?

## Claims

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | The insider share z that Shin's method finds in the opening 1X2 prices | median 0.04175 (IQR 0.03396 to 0.05064), mean 0.04284 | 36,237 | median 0.03892 in 2024, 0.04372 in 2025 | exploratory |
| C2 | Shin's probabilities have a lower log loss than the proportional ones | gain 0.000661 [0.000362, 0.000951] per match (1.001723 → 1.001062) | 36,237 | yes: 0.000750 [0.000317, 0.001179] in 2024, 0.000575 [0.000177, 0.000999] in 2025 | exploratory |
| C3 | Shin's probabilities have a lower Brier score than the proportional ones | gain 0.000396 [0.000212, 0.000570] per match (0.598638 → 0.598243) | 36,237 | yes: 0.000473 [0.000209, 0.000739] in 2024, 0.000321 [0.000081, 0.000563] in 2025 | exploratory |
| C4 | Proportional probabilities are too low for favourites and too high for long shots. Shin's probabilities are near the observed rate in more price bands | proportional: outside the observed interval in 5 of 9 bands. Shin: outside in 1 band (prices up to 1.3), at the upper edge in 1 more (5.5 to 8.0) | 108,711 outcomes | not measured | exploratory |

## Observed and implied rates by price band

Each of the three outcomes of a match is one row. "Observed" is the share of the outcomes that happened. The interval is a Wilson 95% interval.

| price band | outcomes | observed | 95% interval | proportional | Shin |
|---|---|---|---|---|---|
| (1.0, 1.3] | 2,046 | 0.8123 | 0.7948 to 0.8286 | 0.7568 | 0.7828 |
| (1.3, 1.6] | 5,892 | 0.6490 | 0.6367 to 0.6611 | 0.6267 | 0.6454 |
| (1.6, 2.0] | 12,605 | 0.5173 | 0.5086 to 0.5261 | 0.5088 | 0.5198 |
| (2.0, 2.6] | 17,080 | 0.4059 | 0.3986 to 0.4133 | 0.4009 | 0.4050 |
| (2.6, 3.5] | 36,110 | 0.2903 | 0.2856 to 0.2950 | 0.2931 | 0.2905 |
| (3.5, 5.5] | 28,135 | 0.2171 | 0.2123 to 0.2220 | 0.2240 | 0.2171 |
| (5.5, 8.0] | 4,752 | 0.1193 | 0.1104 to 0.1288 | 0.1408 | 0.1289 |
| (8.0, 13.0] | 1,695 | 0.0702 | 0.0590 to 0.0834 | 0.0936 | 0.0800 |
| (13.0, inf] | 396 | 0.0505 | 0.0329 to 0.0767 | 0.0533 | 0.0396 |

## Method

- **Prices:** Bet365's opening ("Initial") 1X2 prices from the league page, S1.16–18 (`notes/FIELDS/SCHEDULE_1_RAW.md`). Bet365 publishes them about 7 days before kickoff.
- **Proportional:** `s2_mkt_p_*`, S2.17–19. Each inverse price is divided by the sum of the three.
- **Shin:** the `shin` package, version 0.2.2, `calculate_implied_probabilities(..., full_output=True)`. For each match, it gives three probabilities and z. The largest distance of a match's three probabilities from a sum of 1 is 4.7e-13.
- **Margin:** the sum of the three inverse prices, minus 1.
- **Scores:** log loss is minus the log of the probability of the result. The Brier score is the sum of (probability − hit)², from 0 to 2. The gain is the proportional score minus the Shin score. A gain above 0 means that Shin's method scored better.
- **Intervals:** a cluster bootstrap over the 144 league-seasons, with 2,000 resamples (`analysis/stats.py:cluster_bootstrap_ci`).
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025 (17,756 priced matches). 2025 holds 2025 and 2025-2026 (18,481).
- **Price bands:** decimal prices, cut at 1.3, 1.6, 2.0, 2.6, 3.5, 5.5, 8.0 and 13.0.

## Caveats

- **Construction, not finding.** Shin's method takes more margin from long shots than from favourites. So Shin is always above proportional for a favourite, and below it for a long shot. The finding is where the observed rates are.
- **z follows the margin.** The Spearman correlation of z with the margin is 0.997 (median margin 0.08277). So z tells little more than the margin. The margin is higher in the 2025 cohort (median 0.08627) than in 2024 (0.07686), and z follows it.
- **Small gains.** The log-loss gain is 0.000661 per match, against a loss of about 1.0. Better calibration is not profit: a bet still pays the margin.
- **Band intervals are too narrow.** They treat the three outcomes of a match, and the matches of a league-season, as independent. C2 and C3 use the clustered interval.
- **Looks:** z, 2 scores and the margin, each for all matches and for 2 cohorts, and 9 price bands. Nothing was selected from a larger set of looks.
- **Opening prices only.** The closing prices are on the detail page, which the staged pipeline does not read yet.
