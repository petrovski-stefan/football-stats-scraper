# RATES — comebacks and 7+ matches on all matches

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together.
- **Sources:** schedule stage 3, outcomes only: the half-time goals (S1.12–13), the goals in total and in each half (S2.01–03), and the labels S2.26–29. Units: the league-season (S1.02, S1.01), for the intervals. The season (S1.01) also gives the season cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.rates`, at the commit that adds this doc.
- **Kind:** empirical: how often each outcome happened in this corpus.

## Question

How often do comebacks and 7+ matches happen? This doc gives the card of the `ALL/` level (`notes/ANALYSIS/CLAUDE.md` §2). For comebacks: the rate, how often a team is behind at half-time, and how often it then wins, for the home team and for the away team. For 7+: the rate, and the goals in each half.

## Claims

Each value is a count divided by a count, with a 95% interval over league-seasons.

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | Comebacks happen in 0.0522 of matches | 0.0522 [0.0496, 0.0549] (1,891 of 36,238) | 36,238 | yes: 0.0516 [0.0476, 0.0559] in 2024, 0.0528 [0.0496, 0.0561] in 2025 | exploratory |
| C2 | A team is behind at half-time in 0.5909 of matches. The team behind then wins 0.0883 of the time | link 1: 0.5909 [0.5822, 0.5995] (21,412 half-times). Link 2: 0.0883 [0.0842, 0.0926] (1,891 of 21,412) | 36,238 | yes. Link 1: 0.5888 [0.5777, 0.5995], 0.5928 [0.5806, 0.6053]. Link 2: 0.0876 [0.0814, 0.0941], 0.0890 [0.0838, 0.0942] | exploratory |
| C3 | The home team is behind at half-time in 0.2548 of matches, and then wins 0.1164 of the time. The away team is behind in 0.3361, and then wins 0.0670 of the time | home: behind 0.2548 [0.2491, 0.2608], wins from behind 0.1164 [0.1098, 0.1230], comeback 0.0297 [0.0279, 0.0316]. Away: behind 0.3361 [0.3300, 0.3425], wins from behind 0.0670 [0.0619, 0.0721], comeback 0.0225 [0.0207, 0.0243] | 36,238 | yes. Wins from behind: home 0.1153 and 0.1175, away 0.0670 and 0.0670 | exploratory |
| C4 | 7+ goals happen in 0.0224 of matches | 0.0224 [0.0201, 0.0249] (812 of 36,238) | 36,238 | yes: 0.0225 [0.0191, 0.0264] in 2024, 0.0223 [0.0191, 0.0255] in 2025 | exploratory |
| C5 | The second half has more goals than the first half | first half 1.2283 [1.2025, 1.2545] goals per match, second half 1.5193 [1.4924, 1.5467]. All: 2.7476 [2.6979, 2.7981] | 36,238 | yes: 1.2277 and 1.5117 in 2024, 1.2289 and 1.5265 in 2025 | exploratory |

## The card

| quantity | count | of | value [95% interval] | 2024 | 2025 |
|---|---|---|---|---|---|
| comeback | 1,891 | 36,238 | 0.0522 [0.0496, 0.0549] | 0.0516 | 0.0528 |
| link 1: a team is behind at half-time | 21,412 | 36,238 | 0.5909 [0.5822, 0.5995] | 0.5888 | 0.5928 |
| link 2: the team behind wins | 1,891 | 21,412 | 0.0883 [0.0842, 0.0926] | 0.0876 | 0.0890 |
| home comeback | 1,075 | 36,238 | 0.0297 [0.0279, 0.0316] | 0.0289 | 0.0304 |
| home team behind at half-time | 9,233 | 36,238 | 0.2548 [0.2491, 0.2608] | 0.2511 | 0.2584 |
| home team behind wins | 1,075 | 9,233 | 0.1164 [0.1098, 0.1230] | 0.1153 | 0.1175 |
| away comeback | 816 | 36,238 | 0.0225 [0.0207, 0.0243] | 0.0226 | 0.0224 |
| away team behind at half-time | 12,179 | 36,238 | 0.3361 [0.3300, 0.3425] | 0.3378 | 0.3345 |
| away team behind wins | 816 | 12,179 | 0.0670 [0.0619, 0.0721] | 0.0670 | 0.0670 |
| 7+ goals | 812 | 36,238 | 0.0224 [0.0201, 0.0249] | 0.0225 | 0.0223 |
| goals in the first half | 44,512 | 36,238 | 1.2283 [1.2025, 1.2545] | 1.2277 | 1.2289 |
| goals in the second half | 55,055 | 36,238 | 1.5193 [1.4924, 1.5467] | 1.5117 | 1.5265 |
| goals per match | 99,567 | 36,238 | 2.7476 [2.6979, 2.7981] | 2.7394 | 2.7554 |

The cohorts hold 17,757 matches (2024) and 18,481 (2025).

## Link 2 by half-time deficit

| deficit | half-times | share of matches | comebacks | completion [95% interval] |
|---|---|---|---|---|
| 1 | 15,455 | 0.4265 | 1,728 | 0.1118 [0.1066, 0.1172] |
| 2 | 4,703 | 0.1298 | 160 | 0.0340 [0.0288, 0.0392] |
| 3 or more | 1,254 | 0.0346 | 3 | 0.0024 [0.0000, 0.0055] |

## Goal totals

| goals | matches | share |
|---|---|---|
| 0 | 2,557 | 0.0706 |
| 1 | 6,355 | 0.1754 |
| 2 | 8,386 | 0.2314 |
| 3 | 8,069 | 0.2227 |
| 4 | 5,551 | 0.1532 |
| 5 | 3,085 | 0.0851 |
| 6 | 1,423 | 0.0393 |
| 7 | 541 | 0.0149 |
| 8 | 180 | 0.0050 |
| 9 | 74 | 0.0020 |
| 10 or more | 17 | 0.0005 |

## Against the odds

The card also gives the count against the count that the odds expect. `ALL/ODDS_YARDSTICK.md` has these, on the 36,237 matches with both opening markets: comebacks 1.2427 (its C2), and 7+ goals 0.8250 (its C7).

## Method

- **The card:** `notes/ANALYSIS/CLAUDE.md` §2. At the `ALL/` level, it splits by home team and away team, not by role.
- **A value:** the sum of a count over all matches, divided by the sum of another count. For a rate, the other count is the matches. For link 2, it is the half-times with a team behind. For "home team behind wins", it is the half-times with the home team behind, and the count is the home comebacks.
- **Intervals:** a cluster bootstrap over the 144 league-seasons, with 2,000 resamples (`analysis/stats.py:observed_expected`).
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025. 2025 holds 2025 and 2025-2026.
- **The matches:** all 36,238, also the one without odds.

## Caveats

- **Two identities, not findings.** The comeback rate is link 1 × link 2, and "home team behind" plus "away team behind" is link 1. Both are true by definition (`notes/REFERENCE/MARKET_COMEBACKS.md`, "The two links").
- **The direction of C3 is structural.** On average the home team is the stronger side. Under the goal model, the stronger side is behind less often and wins from behind more often (`notes/REFERENCE/MARKET_COMEBACKS.md`, "Favourite and underdog"). So only the sizes in C3 are empirical.
- **The fall by deficit is structural.** Under the goal model, the completion always falls as the deficit grows (`notes/REFERENCE/MARKET_COMEBACKS.md`, "Deficit size"). The table gives the sizes.
- **Raw rates, not "beyond the odds".** These rates do not tell if a match has more comebacks than its prices expect. `ALL/ODDS_YARDSTICK.md` does.
- **The corpus was chosen.** Its 73 leagues stayed because their odds coverage was complete (`PER_LEAGUE/ODDS_COVERAGE.md`, Caveats). The rates describe these leagues, not football in general.
- **The awarded match** is in the rates, as a 3-0 with 0-0 at half-time: 1 match of 36,238 (`PER_LEAGUE/ODDS_COVERAGE.md`, C2).
- **Looks:** 13 values for all matches and for each of the 2 cohorts; 3 deficit bands; 11 goal totals.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-19 | 144 league-seasons, 36,238 matches | first run |
