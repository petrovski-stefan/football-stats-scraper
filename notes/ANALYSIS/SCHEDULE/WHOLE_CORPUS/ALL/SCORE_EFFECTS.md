# SCORE_EFFECTS — second-half score effects on all matches

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 and O/U prices, through the odds yardstick (`ALL/ODDS_YARDSTICK.md`). Outcome: the half-time and full-time goals (S1.12–15), and S2.01–03 and S2.26.
- **Corpus:** 2026-10-18: 144 league-seasons, 36,238 matches. 36,237 of them have both opening markets: 72,474 team-halves.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.score_effects`, at the commit that adds this doc.
- **Kind:** empirical. The basic goal model keeps each team's rate constant in a half, whatever the score (`notes/REFERENCE/MARKET_COMEBACKS.md`, "The basic goal model"). This doc measures how the second half differs from it: open questions 7–9 of that note.

## Question

After half-time, does the team that is behind score faster than the yardstick expects? Does the team that is ahead score slower? Does it change with the deficit and with the strength of the teams? How much of the comeback excess of `ALL/ODDS_YARDSTICK.md` (C2, C3) do these changes explain?

## Claims

O/E is the observed second-half goals divided by the second-half goals that the yardstick expects. A team-half is one team's second half in one match.

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | A team behind by 1 at half-time scores more second-half goals than the yardstick expects | O/E 1.0868 [1.0675, 1.1056] (11,935 against 10,981.5) | 15,455 team-halves | yes: 1.0801 [1.0509, 1.1101] in 2024, 1.0932 [1.0686, 1.1157] in 2025 | exploratory |
| C2 | A team behind by 2 also scores more | O/E 1.0751 [1.0349, 1.1142] (3,419 against 3,180.3) | 4,703 | yes: 1.0760 [1.0164, 1.1354], 1.0742 [1.0220, 1.1267] | exploratory |
| C3 | A team ahead by 1 at half-time scores fewer second-half goals than the yardstick expects | O/E 0.9385 [0.9214, 0.9548] (12,028 against 12,815.8) | 15,455 | yes: 0.9337 [0.9059, 0.9612], 0.9431 [0.9209, 0.9641] | exploratory |
| C4 | A team ahead by 2 or more, and a team behind by 3 or more, are near the yardstick | ahead by 2: 0.9937 [0.9621, 1.0262]. Ahead by 3+: 0.9949 [0.9414, 1.0479]. Behind by 3+: 1.0020 [0.9339, 1.0744] | 4,703, 1,254 and 1,254 | yes: each interval includes 1 in both cohorts | exploratory |
| C5 | After a 0-0 half-time, both teams score fewer second-half goals than the yardstick expects. After 1 or more first-half goals, the second half is near the yardstick | 0-0: home 0.9421 [0.9216, 0.9621], away 0.9409 [0.9166, 0.9626]. All second-half goals after 0 first-half goals: 0.9416 [0.9244, 0.9577]. After 1, 2, 3 and 4+: 1.0056 to 1.0198, each interval includes 1 | 10,540 matches at 0-0 | the level state: 0.9466 [0.9268, 0.9673] in 2024, 0.9644 [0.9449, 0.9829] in 2025. The 0-0 split is not measured per cohort | exploratory |
| C6 | The effect is there at a fixed number of first-half goals: after 1-0 and 0-1, and after 2-1 and 1-2, the side behind scores more and the side ahead scores fewer | side behind: 1.0729 (1-0), 1.0966 (0-1), 1.1299 (2-1), 1.0746 (1-2). Side ahead: 0.9235, 0.9601, 0.9353, 0.9249. Each of the 8 intervals excludes 1 | 7,266, 5,736, 1,266 and 1,081 matches | not measured | exploratory |
| C7 | The favourite and the underdog both show it | behind by 1: favourite 1.1000 [1.0731, 1.1255], underdog 1.0739 [1.0465, 1.1001]. Ahead by 1: favourite 0.9290 [0.9077, 0.9489], underdog 0.9619 [0.9334, 0.9911] | 5,984 and 9,471 team-halves behind by 1 | not measured | exploratory |
| C8 | These second-half rates explain about three quarters of the comeback excess | basic model: 1,528.6 expected completions. With the measured rates: 1,809.1 (O/E 1.0453 against 1,891 observed), 0.7740 of the gap. The side behind alone: 0.6220. The side ahead alone: 0.1355 | 36,237 matches | not measured | exploratory |

## Second-half goals by half-time state

The state is the team's own margin at half-time: its goals minus the other side's.

| state | team-halves | observed | expected | O/E [95% interval] | 2024 | 2025 |
|---|---|---|---|---|---|---|
| behind by 3+ | 1,254 | 791 | 789.4 | 1.0020 [0.9339, 1.0744] | 1.0242 | 0.9786 |
| behind by 2 | 4,703 | 3,419 | 3,180.3 | 1.0751 [1.0349, 1.1142] | 1.0760 | 1.0742 |
| behind by 1 | 15,455 | 11,935 | 10,981.5 | 1.0868 [1.0675, 1.1056] | 1.0801 | 1.0932 |
| level | 29,650 | 21,397 | 22,390.4 | 0.9556 [0.9418, 0.9687] | 0.9466 | 0.9644 |
| ahead by 1 | 15,455 | 12,028 | 12,815.8 | 0.9385 [0.9214, 0.9548] | 0.9337 | 0.9431 |
| ahead by 2 | 4,703 | 4,218 | 4,244.9 | 0.9937 [0.9621, 1.0262] | 1.0108 | 0.9780 |
| ahead by 3+ | 1,254 | 1,264 | 1,270.5 | 0.9949 [0.9414, 1.0479] | 1.0279 | 0.9595 |

## Favourite and underdog

| state | favourite: team-halves | favourite O/E [95% interval] | underdog: team-halves | underdog O/E [95% interval] |
|---|---|---|---|---|
| behind by 3+ | 248 | 0.9650 [0.8330, 1.1007] | 1,006 | 1.0169 [0.9389, 1.0952] |
| behind by 2 | 1,430 | 1.0717 [1.0141, 1.1302] | 3,273 | 1.0773 [1.0289, 1.1273] |
| behind by 1 | 5,984 | 1.1000 [1.0731, 1.1255] | 9,471 | 1.0739 [1.0465, 1.1001] |
| level | 14,825 | 0.9583 [0.9419, 0.9745] | 14,825 | 0.9515 [0.9309, 0.9714] |
| ahead by 1 | 9,471 | 0.9290 [0.9077, 0.9489] | 5,984 | 0.9619 [0.9334, 0.9911] |
| ahead by 2 | 3,273 | 0.9757 [0.9423, 1.0104] | 1,430 | 1.0591 [0.9826, 1.1287] |
| ahead by 3+ | 1,006 | 0.9800 [0.9222, 1.0398] | 248 | 1.0948 [0.9424, 1.2513] |

## Each side after 8 common half-time scores

| half-time | matches | home O/E [95% interval] | away O/E [95% interval] |
|---|---|---|---|
| 0-0 | 10,540 | 0.9421 [0.9216, 0.9621] | 0.9409 [0.9166, 0.9626] |
| 1-0 | 7,266 | 0.9235 [0.9017, 0.9439] | 1.0729 [1.0411, 1.1039] |
| 0-1 | 5,736 | 1.0966 [1.0664, 1.1261] | 0.9601 [0.9316, 0.9886] |
| 1-1 | 3,937 | 0.9960 [0.9685, 1.0270] | 0.9687 [0.9406, 0.9975] |
| 2-0 | 2,477 | 0.9851 [0.9428, 1.0287] | 1.0917 [1.0384, 1.1485] |
| 0-2 | 1,728 | 1.0513 [0.9887, 1.1099] | 1.0262 [0.9714, 1.0787] |
| 2-1 | 1,266 | 0.9353 [0.8770, 0.9919] | 1.1299 [1.0588, 1.2056] |
| 1-2 | 1,081 | 1.0746 [1.0109, 1.1386] | 0.9249 [0.8611, 0.9938] |

## All second-half goals by first-half goals

| first-half goals | matches | observed | expected | O/E [95% interval] |
|---|---|---|---|---|
| 0 | 10,540 | 14,859 | 15,781.0 | 0.9416 [0.9244, 0.9577] |
| 1 | 13,002 | 20,029 | 19,918.2 | 1.0056 [0.9924, 1.0186] |
| 2 | 8,142 | 12,793 | 12,682.7 | 1.0087 [0.9920, 1.0259] |
| 3 | 3,294 | 5,286 | 5,246.4 | 1.0076 [0.9832, 1.0333] |
| 4 or more | 1,259 | 2,085 | 2,044.6 | 1.0198 [0.9782, 1.0637] |

## Comebacks under the measured second-half rates

Each side's second-half rate is multiplied by the O/E of its half-time state (the state table above). "Gap explained" is (expected − basic) ÷ (observed − basic).

| rates | expected completions | observed | O/E | gap explained |
|---|---|---|---|---|
| basic model | 1,528.6 | 1,891 | 1.2371 | 0 |
| the side behind scaled | 1,754.0 | 1,891 | 1.0781 | 0.6220 |
| the side ahead scaled | 1,577.7 | 1,891 | 1.1986 | 0.1355 |
| both sides scaled | 1,809.1 | 1,891 | 1.0453 | 0.7740 |

## Method

- **The yardstick:** `ALL/ODDS_YARDSTICK.md` (`analysis/methods/yardstick.py`), with the same first-half share, 0.4471.
- **Team-halves:** two rows per match, one for each team. Each row has the team's half-time state, its second-half goals (full-time minus half-time goals) and its expected second-half goals: (1 − 0.4471) times its fitted rate.
- **Favourite:** the side with the higher Shin win probability.
- **O/E and intervals:** the sum of the observed goals, divided by the sum of the expected goals. A cluster bootstrap over the 144 league-seasons gives the interval, with 2,000 resamples (`analysis/stats.py:observed_expected`). The two rows of a match are in the same league-season, so they stay together.
- **The gap:** the completion from the half-time score that happened (`analysis/methods/yardstick.py:completion_given_ht`), with each side's second-half rate multiplied by the O/E of its state. A level half-time has no completion, so its factor has no effect.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025. 2025 holds 2025 and 2025-2026.

## Caveats

- **C8 is in-sample.** Its factors come from the second-half goals of the same matches. So C8 is a check of consistency, not a test. It shows that a shift of the two mean rates gives most of the excess.
- **Selection by the half-time score.** A team that is behind at half-time is, on average, weaker than its prices say. A team that is ahead is stronger. That selection alone gives the side behind an O/E below 1, and the side ahead an O/E above 1. C1–C3 go the other way, so the score effects can be larger than these numbers. After 0-0 (C5), the same selection lowers the rates of both teams. So this doc cannot tell a slower game from a match with lower rates than its prices.
- **The neutral point is not exactly 1.** The yardstick expects slightly too many goals in all matches (`ALL/ODDS_YARDSTICK.md`, C1: 0.9888). The second-half expectation carries that ratio.
- **A small rate change moves a rare completion a lot.** The side behind by 2 scores 1.0751 times the yardstick (C2). But its completion is 1.7139 times the yardstick (`ALL/ODDS_YARDSTICK.md`, C4). This agrees with the structural card "Sensitivity to the second-half rates" (`notes/REFERENCE/MARKET_COMEBACKS.md`).
- **No minutes.** The schedule has the half-time and full-time scores only. When the second-half goals come is a question for the live page (`notes/WORKING/IDEAS_2026-10-01.md` idea 2b, step 8).
- **Looks:** 7 states for all matches; 7 for each of the 2 cohorts; 14 for the favourite and the underdog; 16 for the 8 half-time scores; 5 groups of first-half goals; 4 sets of rates. The claims come from these 60 numbers.
- **Not profit.** A faster side behind does not show value without the in-play prices, and the project is pre-match only.
