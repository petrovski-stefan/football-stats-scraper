# ODDS_YARDSTICK — the odds yardstick per team

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/PER_TEAM`: 1,337 teams, each in one league, with its seasons together. A team in two leagues is two units.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 prices (S1.16–18) and the opening O/U line and prices (S1.19–21), through the odds yardstick (`../ALL/ODDS_YARDSTICK.md`). Units: the teams (S1.08–11), the league (S1.02, S1.03) and the season (S1.01), which also gives the season cohort. Outcome: the half-time and full-time goals (S1.12–15).
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 36,237 of them have both opening markets: 72,474 team-matches, of 1,337 teams in 73 leagues.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.per_team.odds_yardstick`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

After the opening prices, does a team come back, or lose a lead, more often than the other teams of its league? Does this repeat from one season to the next? `RATES.md` of this folder asks the same of the raw rates. The prices of a match carry the strength of both teams. So this doc can separate a team from its strength and from its opponents (`notes/ANALYSIS/CLAUDE.md` §5, rule 7).

## Claims

A team's O/E is the count of its events divided by the count that the yardstick expects for it. Each test compares the teams with their own league, on 1,264 df. "sd", "at 80%" and "repeat" are as in `RATES.md` of this folder.

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | After the prices, there is no sign that a team comes back more or less often than its league | Q 1117.2, p = 0.999, sd 0: the shrunk O/E of each team is the value of its league. At home p = 0.975, away p = 0.858. At 80%, the test finds an sd of 26.24% of the pooled O/E 1.2427. The raw team O/E reach 7.7358; luck alone reaches 8.5964 | 1,337 teams | no repeat: r = −0.0731, p = 0.0292, one of 12 repeat tests | exploratory |
| C2 | After the prices, there is no sign that a team loses a lead more or less often than its league | Q 1261.6, p = 0.514, sd 0. At home p = 0.947, away p = 0.417. At 80%: 26.14% of 1.2427. The raw team O/E reach 8.2612; luck alone reaches 8.0251 | 1,337 teams | no repeat: r = 0.0491, p = 0.143 | exploratory |
| C3 | After the prices, the two links show no clear difference between teams. The raw differences of `RATES.md` (C3) are in the prices | behind at half-time: p = 0.225, sd 0.0350. Ahead: p = 0.221, sd 0.0353. Behind, then wins: p = 0.982, sd 0. Ahead, then loses: p = 0.576, sd 0 | 1,337 teams | behind −0.0126, ahead −0.0034; behind, then wins −0.0696 (p 0.038); ahead, then loses 0.0607 (p 0.0701) | exploratory |
| C4 | The yardstick fits the goals that each team scores and concedes | scored: Q 1338.9, p = 0.0702, sd 0.0271 (2.74% of 0.9888); at 80%, 3.63%. Conceded: Q 1279.8, p = 0.372, sd 0.0125 | 1,337 teams | no repeat: scored 0.0036 (p 0.914), conceded 0.0186 (p 0.579) | exploratory |
| C5 | The comeback excess is about the same at each strength of the team. For goals, the prices spread the strength of the teams a little too wide | comes back: O/E 1.1918 to 1.3241 in the 7 bands of the team's own win chance. Loses a lead: 1.1401 to 1.3119. Goals scored at a win chance up to 0.2: 1.0344 [1.0142, 1.0553]. Goals conceded at 0.2 to 0.3: 0.9773 [0.9657, 0.9888]; above 0.7: 1.0457 [0.9931, 1.0981] | 72,474 team-matches | not measured | exploratory |
| C6 | The comeback counts of the teams vary less than independent matches would make them | comes back: Q 1117.2. With outcomes drawn from the test's own null: 1263.4 (sd 50.3), so 2.91 sd lower. Behind, then wins: 2.32 sd lower. Loses a lead: 0.05 sd lower | 1,337 teams | not measured | exploratory |

## Calibration by the strength of the team

Rule 8 (`notes/ANALYSIS/CLAUDE.md` §5): a repeat can come from a yardstick that is wrong by strength. So, first, the O/E by the team's own Shin win chance, over its team-matches. Each cell is O/E [95% interval].

| win chance | team-matches | comes back | loses a lead | behind at half-time | ahead at half-time | goals scored | goals conceded |
|---|---|---|---|---|---|---|---|
| up to 0.2 | 10,559 | 1.2552 [1.0393, 1.4733] | 1.2600 [1.1330, 1.3877] | 1.0069 [0.9855, 1.0273] | 1.0275 [0.9836, 1.0712] | 1.0344 [1.0142, 1.0553] | 0.9846 [0.9709, 0.9987] |
| 0.2 to 0.3 | 15,102 | 1.2043 [1.0754, 1.3370] | 1.3119 [1.1957, 1.4230] | 0.9712 [0.9502, 0.9923] | 0.9972 [0.9696, 1.0253] | 0.9974 [0.9827, 1.0111] | 0.9773 [0.9657, 0.9888] |
| 0.3 to 0.4 | 17,087 | 1.1918 [1.0869, 1.3020] | 1.1843 [1.0930, 1.2799] | 0.9838 [0.9643, 1.0040] | 0.9795 [0.9615, 1.0000] | 0.9839 [0.9713, 0.9963] | 0.9855 [0.9716, 0.9993] |
| 0.4 to 0.5 | 13,636 | 1.3047 [1.1949, 1.4181] | 1.2181 [1.0904, 1.3450] | 0.9961 [0.9731, 1.0201] | 0.9847 [0.9614, 1.0067] | 0.9743 [0.9615, 0.9873] | 0.9880 [0.9746, 1.0008] |
| 0.5 to 0.6 | 8,936 | 1.2165 [1.0801, 1.3507] | 1.2430 [1.0643, 1.4338] | 1.0096 [0.9704, 1.0475] | 0.9730 [0.9495, 0.9966] | 0.9804 [0.9657, 0.9952] | 1.0109 [0.9909, 1.0324] |
| 0.6 to 0.7 | 4,410 | 1.2789 [1.0650, 1.5036] | 1.1822 [0.8908, 1.4909] | 1.0292 [0.9597, 1.0983] | 1.0207 [0.9887, 1.0511] | 0.9940 [0.9752, 1.0138] | 1.0265 [0.9964, 1.0559] |
| above 0.7 | 2,744 | 1.3241 [1.1237, 1.5428] | 1.1401 [0.7045, 1.6019] | 1.0614 [0.9564, 1.1673] | 1.0171 [0.9856, 1.0469] | 0.9812 [0.9570, 1.0052] | 1.0457 [0.9931, 1.0981] |

The comeback roles have no trend with strength. For goals, the weak teams score a little more and concede a little less than their prices expect, and the strongest teams concede a little more.

## One test for each O/E

| quantity | pooled | Q | p | sd | sd / pooled | at 80% / pooled | keep | shrunk − league: lowest | highest | repeat r | repeat p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| comes back | 1.2427 | 1117.2 | 0.999 | 0.0000 | 0.0000 | 0.2624 | 0.0000 | 0.0000 | 0.0000 | −0.0731 | 0.0292 |
| comes back at home | 1.2682 | 1167.7 | 0.975 | 0.0000 | 0.0000 | 0.3383 | 0.0000 | 0.0000 | 0.0000 | −0.0755 | 0.0242 |
| comes back away | 1.2106 | 1210.2 | 0.858 | 0.0000 | 0.0000 | 0.3884 | 0.0000 | 0.0000 | 0.0000 | −0.0081 | 0.809 |
| behind at half-time | 0.9924 | 1301.8 | 0.225 | 0.0350 | 0.0353 | 0.0655 | 0.0283 | −0.0181 | 0.0175 | −0.0126 | 0.708 |
| behind, then wins | 1.2371 | 1160.7 | 0.982 | 0.0000 | 0.0000 | 0.2490 | 0.0000 | 0.0000 | 0.0000 | −0.0696 | 0.038 |
| loses a lead | 1.2427 | 1261.6 | 0.514 | 0.0000 | 0.0000 | 0.2614 | 0.0000 | 0.0000 | 0.0000 | 0.0491 | 0.143 |
| loses a lead at home | 1.2106 | 1183.8 | 0.947 | 0.0000 | 0.0000 | 0.3858 | 0.0000 | 0.0000 | 0.0000 | 0.0381 | 0.256 |
| loses a lead away | 1.2682 | 1273.9 | 0.417 | 0.1183 | 0.0933 | 0.3384 | 0.0070 | −0.0171 | 0.0807 | −0.0006 | 0.986 |
| ahead at half-time | 0.9924 | 1302.3 | 0.221 | 0.0353 | 0.0356 | 0.0657 | 0.0279 | −0.0220 | 0.0263 | −0.0034 | 0.92 |
| ahead, then loses | 1.2371 | 1253.7 | 0.576 | 0.0000 | 0.0000 | 0.2490 | 0.0000 | 0.0000 | 0.0000 | 0.0607 | 0.0701 |
| goals scored | 0.9888 | 1338.9 | 0.0702 | 0.0271 | 0.0274 | 0.0363 | 0.0568 | −0.0172 | 0.0217 | 0.0036 | 0.914 |
| goals conceded | 0.9888 | 1279.8 | 0.372 | 0.0125 | 0.0126 | 0.0361 | 0.0123 | −0.0040 | 0.0059 | 0.0186 | 0.579 |

## Q against the test's own null

100 draws of the outcomes from the null of the test: each team has the O/E of its league.

| quantity | Q | null Q: mean | sd | real − null, in sd |
|---|---|---|---|---|
| comes back | 1117.2 | 1263.4 | 50.3 | −2.91 |
| comes back at home | 1167.7 | 1263.5 | 53.3 | −1.80 |
| comes back away | 1210.2 | 1260.7 | 54.9 | −0.92 |
| behind, then wins | 1160.7 | 1261.7 | 43.5 | −2.32 |
| loses a lead | 1261.6 | 1264.0 | 47.9 | −0.05 |
| loses a lead at home | 1183.8 | 1262.2 | 51.1 | −1.53 |
| loses a lead away | 1273.9 | 1265.8 | 45.4 | 0.18 |
| ahead, then loses | 1253.7 | 1256.2 | 48.9 | −0.05 |

The null means are near the df, 1,264. So the method gives Q the right mean, and a low Q is a property of the data.

## The luck line

| quantity | events of a team, median | raw lowest | raw highest | luck lowest | luck highest |
|---|---|---|---|---|---|
| comes back | 1 | 0.0000 | 7.7358 | 0.0000 | 8.5964 |
| loses a lead | 1 | 0.0000 | 8.2612 | 0.0000 | 8.0251 |

## Teams with the highest O/E

Each shrunk value is the value of the team's league (C1, C2), so the order is the raw O/E. These values are in the range of luck. The expected counts are small, so one or two events give a large O/E.

Comes back:

| team | league | events | expected | O/E | league value | shrunk | comebacks in its matches |
|---|---|---|---|---|---|---|---|
| Itabaiana(SE) | brasileiro,_serie_c | 2 | 0.2585 | 7.7358 | 1.7161 | 1.7161 | 2 |
| Deportivo Recoleta | primera_division_de_paraguay | 4 | 0.6490 | 6.1630 | 1.8029 | 1.8029 | 7 |
| HK Kopavogs | iceland_premier_division | 2 | 0.3783 | 5.2863 | 1.7080 | 1.7080 | 3 |
| Sunderland A.F.C | english_premier_league | 3 | 0.5753 | 5.2151 | 1.5257 | 1.5257 | 3 |
| Stirling Macedonia | national_premier_leagues_western_australia | 7 | 1.3550 | 5.1661 | 1.5573 | 1.5573 | 7 |
| Caxias RS | brasileiro,_serie_c | 3 | 0.6034 | 4.9720 | 1.7161 | 1.7161 | 5 |
| Vasteras SK FK | sweden_superettan | 4 | 0.8261 | 4.8422 | 1.4088 | 1.4088 | 5 |
| Sivasspor | turkey_super_lig | 3 | 0.6328 | 4.7412 | 1.4823 | 1.4823 | 3 |
| Havelse | german_3.liga | 3 | 0.6354 | 4.7216 | 1.2787 | 1.2787 | 5 |
| Adana Demirspor | turkey_super_lig | 2 | 0.4446 | 4.4984 | 1.4823 | 1.4823 | 6 |

Loses a lead:

| team | league | events | expected | O/E | league value | shrunk | comebacks in its matches |
|---|---|---|---|---|---|---|---|
| Deportes Limache | chile_primera_division | 6 | 0.7263 | 8.2612 | 1.1633 | 1.1633 | 6 |
| Brusque FC | brasileiro,_serie_c | 2 | 0.2853 | 7.0113 | 1.7168 | 1.7168 | 2 |
| Atletico Paranaense | brazil_serie_b | 3 | 0.4624 | 6.4879 | 1.5222 | 1.5222 | 4 |
| Coritiba PR | brazil_serie_b | 6 | 1.0242 | 5.8580 | 1.5222 | 1.5222 | 6 |
| Polonia Bytom | poland_liga_1 | 4 | 0.7697 | 5.1967 | 1.2653 | 1.2653 | 4 |
| AC Horsens | danish_1st_division | 4 | 0.7802 | 5.1271 | 0.8875 | 0.8875 | 6 |
| Eldense | spanish_la_liga_2 | 4 | 0.7908 | 5.0584 | 1.2868 | 1.2868 | 4 |
| Figueirense | brasileiro,_serie_c | 3 | 0.6057 | 4.9529 | 1.7168 | 1.7168 | 3 |
| Sport Club do Recife | brazil_serie_a | 4 | 0.8087 | 4.9464 | 0.9907 | 0.9907 | 4 |
| Criciuma | brazil_serie_a | 4 | 0.8144 | 4.9114 | 0.9907 | 0.9907 | 5 |

## Method

- **The yardstick:** `../ALL/ODDS_YARDSTICK.md`, on the 36,237 matches with both opening markets, with the first-half share 0.4471.
- **The chances of a team:** in each match, the team's comeback chance is the home or the away comeback chance of the match, and its chance to lose a lead is the comeback chance of the other team. Its chance to be behind or ahead at half-time comes from the first-half rates (`analysis/methods/yardstick.py:implied`, `m_home_behind` and `m_away_behind`). After the half-time score that happened, "behind, then wins" expects the completion chance when the team is behind, and "ahead, then loses" expects the completion chance of the other team when the team is ahead. The expected goals are the team's rate and the rate of the other team.
- **The team rows, the test, shrinkage, at 80%, the luck line and the repeat:** as in `RATES.md` of this folder (`analysis/card.py:team_rows`, `analysis/units.py:within_row`), with the O/E in place of the raw rate.
- **Calibration by strength:** the team-matches banded by the team's own Shin win chance, cut at 0.2, 0.3, 0.4, 0.5, 0.6 and 0.7. Each O/E has a cluster bootstrap interval over the league-seasons (`analysis/stats.py:observed_expected`).
- **The null check** (`analysis/units.py:null_q`): in each of 100 draws, each team-match gets an event with the chance league O/E × the yardstick's chance. Q of each draw, then the mean and the sd.

## Caveats

- **Rules 7 and 8.** The yardstick takes both teams of a match from its prices (rule 7). The calibration by strength comes before the repeat test (rule 8). The comeback roles have no trend with strength, so a repeat could not come from the yardstick. There is no repeat.
- **"No sign" has a size.** At 80%, the tests find an sd of about a quarter of the O/E (C1, C2). A smaller difference between teams can exist.
- **C6 makes the tests stricter.** For the team that comes back, the real Q is below its null. Then a team difference must be larger before the test finds it: the true sd at 80% is larger than the table says. But a team difference adds variance, and the data have less variance than chance. So C6 also speaks against team differences. This doc does not explain C6.
- **The negative repeats are one fact, three times.** Comes back, comes back at home, and behind, then wins all have r from −0.0696 to −0.0755, with p from 0.0242 to 0.038. They count the same comebacks. With 12 repeat tests, none of these p is small.
- **The goals and strength (C5).** The pattern is small, a few percent, and it agrees with `../ALL/PRICES.md` (C4: large handicaps are too large) and with `../ALL/ODDS_YARDSTICK.md` (Caveats: the prices spread the expected goals a little too wide). The goal O/E of the teams do not repeat (C4), so the pattern does not make a team trait.
- **Not profit.** A team with a high comeback O/E does not show value. The value needs the HT/FT prices, and nowgoal does not show them.
- **Looks:** 12 tests, 12 repeat tests and 12 values at 80%; 42 calibration cells; 8 null checks; 2 luck lines and 2 lists of 10 teams. No team was tested on its own.
