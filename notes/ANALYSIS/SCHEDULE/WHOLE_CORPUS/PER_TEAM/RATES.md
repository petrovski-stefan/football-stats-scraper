# RATES — comebacks per team

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/PER_TEAM`: 1,337 teams, each in one league, with its seasons together. A team in two leagues is two units.
- **Sources:** schedule stage 3, outcomes only: the half-time and full-time goals (S1.12–15). Units: the teams (S1.08–11), the league (S1.02, S1.03) and the season (S1.01), which also gives the season cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches: 72,476 team-matches, of 1,337 teams in 73 leagues.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.per_team.rates`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

Do some teams come back, or lose a lead, more often than the other teams of their league? Does the value of a team in one season tell its value in the next? This doc gives the card of the `PER_TEAM/` level (`notes/ANALYSIS/CLAUDE.md` §2): the two roles, each at home and away, and the goals that a team scores and concedes.

## Claims

The two roles: the team comes back (it is behind at half-time and wins), and the team loses a lead (it is ahead at half-time and loses). Each test compares the teams with their own league, on 1,264 df. "sd" is the standard deviation τ of the teams around their league. "At 80%" gives the sd that the test finds at p < 0.05 in 80% of simulated corpora. "Repeat" is the Spearman correlation of a team's value against its league, cohort 2024 against cohort 2025, over 890 teams.

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | There is no sign that a team comes back more or less often than its league | Q 1212.8, p = 0.846, sd 0: the shrunk value of each team is the value of its league. At home p = 0.9, away p = 0.45. At 80%, the test finds an sd of 25.84% of the rate 0.0261. The raw team rates reach 0.1591; luck alone reaches 0.1579 | 1,337 teams | it does not repeat: r = −0.0254, p = 0.449 | exploratory |
| C2 | The teams differ a little in how often they lose a lead | Q 1392.6, p = 0.00639, sd 0.0067 (25.70% of the rate 0.0261). The shrunk team values are −0.0036 to 0.0096 from their league. At home p = 0.716, away p = 0.0281 | 1,337 teams | weakly: r = 0.0781, p = 0.0197 | exploratory |
| C3 | The teams differ clearly in how often they are behind and ahead at half-time, and in how often they then win or lose. The half-time state repeats; what happens after it repeats little | behind: Q 2892.0, p = 5.65e-129, sd 0.0703. Ahead: Q 3357.7, p = 3.09e-189, sd 0.0797. Behind, then wins: Q 1729.3, p = 4.15e-17, sd 0.0421. Ahead, then loses: Q 1933.2, p = 6.07e-31, sd 0.0507 | 1,337 teams | behind 0.3210 (p 8.98e-23), ahead 0.3806 (p 4.75e-32); behind, then wins 0.0528 (p 0.116); ahead, then loses 0.1158 (p 0.000535) | exploratory |
| C4 | The teams differ much in the goals that they score and concede, and this repeats | scored: Q 6454.4, sd 0.3187 goals (23.20% of 1.3738). Conceded: Q 4670.8, sd 0.2613 (19.02%). Both p print as 0 | 1,337 teams | yes: scored 0.5295 (p 1.85e-65), conceded 0.4719 (p 1.52e-50) | exploratory |

## One test for each quantity

"Keep" is the median share of its own distance from the league that a team keeps after shrinkage.

| quantity | pooled | Q | p | sd | sd / pooled | at 80% / pooled | keep | shrunk − league: lowest | highest | repeat r | repeat p |
|---|---|---|---|---|---|---|---|---|---|---|---|
| comes back | 0.0261 | 1212.8 | 0.846 | 0.0000 | 0.0000 | 0.2584 | 0.0000 | 0.0000 | 0.0000 | −0.0254 | 0.449 |
| comes back at home | 0.0297 | 1200.1 | 0.9 | 0.0000 | 0.0000 | 0.3347 | 0.0000 | 0.0000 | 0.0000 | −0.0608 | 0.0697 |
| comes back away | 0.0225 | 1269.7 | 0.45 | 0.0018 | 0.0789 | 0.3780 | 0.0038 | −0.0001 | 0.0006 | 0.0405 | 0.227 |
| behind at half-time | 0.2954 | 2892.0 | 5.65e-129 | 0.0703 | 0.2379 | 0.0673 | 0.5731 | −0.1430 | 0.1475 | 0.3210 | 8.98e-23 |
| behind, then wins | 0.0883 | 1729.3 | 4.15e-17 | 0.0421 | 0.4772 | 0.2521 | 0.2543 | −0.0390 | 0.0914 | 0.0528 | 0.116 |
| loses a lead | 0.0261 | 1392.6 | 0.00639 | 0.0067 | 0.2570 | 0.2584 | 0.0885 | −0.0036 | 0.0096 | 0.0781 | 0.0197 |
| loses a lead at home | 0.0225 | 1234.8 | 0.716 | 0.0000 | 0.0000 | 0.3780 | 0.0000 | 0.0000 | 0.0000 | 0.0603 | 0.0719 |
| loses a lead away | 0.0297 | 1361.7 | 0.0281 | 0.0086 | 0.2902 | 0.3348 | 0.0684 | −0.0031 | 0.0159 | 0.0063 | 0.85 |
| ahead at half-time | 0.2954 | 3357.7 | 3.09e-189 | 0.0797 | 0.2698 | 0.0673 | 0.6332 | −0.1568 | 0.2824 | 0.3806 | 4.75e-32 |
| ahead, then loses | 0.0883 | 1933.2 | 6.07e-31 | 0.0507 | 0.5735 | 0.2539 | 0.3280 | −0.0568 | 0.1214 | 0.1158 | 0.000535 |
| goals scored | 1.3738 | 6454.4 | 0 | 0.3187 | 0.2320 | 0.0367 | 0.8083 | −0.6978 | 1.5071 | 0.5295 | 1.85e-65 |
| goals conceded | 1.3738 | 4670.8 | 0 | 0.2613 | 0.1902 | 0.0372 | 0.7346 | −0.5920 | 0.8009 | 0.4719 | 1.52e-50 |

## The luck line

If each team had the value of its league, the raw team values would still spread. The median lowest and highest value over 2,000 Poisson draws:

| quantity | events of a team, median | raw lowest | raw highest | luck lowest | luck highest |
|---|---|---|---|---|---|
| comes back | 1 | 0.0000 | 0.1591 | 0.0000 | 0.1579 |
| loses a lead | 1 | 0.0000 | 0.2000 | 0.0000 | 0.1579 |

## Teams most above their league

The 10 teams with the largest shrunk distance above their league, then the highest raw rate. "Of" is the team-matches. "League value" is the precision-weighted mean of the teams of the league. The last column counts the comebacks in all matches of the team, in both roles.

Comes back. Each shrunk value is the league value (C1), so the order is the raw rate. These rates are in the range of luck.

| team | league | events | of | rate | league value | shrunk | shrunk − league | comebacks in its matches |
|---|---|---|---|---|---|---|---|---|
| Stirling Macedonia | national_premier_leagues_western_australia | 7 | 44 | 0.1591 | 0.0436 | 0.0436 | 0.0000 | 7 |
| Vasteras SK FK | sweden_superettan | 4 | 30 | 0.1333 | 0.0313 | 0.0313 | 0.0000 | 5 |
| Fenerbahce | turkey_super_lig | 8 | 70 | 0.1143 | 0.0316 | 0.0316 | 0.0000 | 8 |
| Itabaiana(SE) | brasileiro,_serie_c | 2 | 19 | 0.1053 | 0.0276 | 0.0276 | 0.0000 | 2 |
| Kalmar | sweden_superettan | 3 | 30 | 0.1000 | 0.0313 | 0.0313 | 0.0000 | 3 |
| Hume City | vic_premier_league | 5 | 52 | 0.0962 | 0.0275 | 0.0275 | 0.0000 | 5 |
| Aston Villa | english_premier_league | 7 | 76 | 0.0921 | 0.0342 | 0.0342 | 0.0000 | 8 |
| Brighton Hove Albion | english_premier_league | 7 | 76 | 0.0921 | 0.0342 | 0.0342 | 0.0000 | 9 |
| Afturelding | iceland_premier_division | 2 | 22 | 0.0909 | 0.0473 | 0.0473 | 0.0000 | 5 |
| Al Rayyan | qatar_stars_league | 4 | 44 | 0.0909 | 0.0417 | 0.0417 | 0.0000 | 8 |

Loses a lead:

| team | league | events | of | rate | league value | shrunk | shrunk − league | comebacks in its matches |
|---|---|---|---|---|---|---|---|---|
| Deportes Limache | chile_primera_division | 6 | 30 | 0.2000 | 0.0240 | 0.0336 | 0.0096 | 6 |
| Criciuma | brazil_serie_a | 4 | 38 | 0.1053 | 0.0171 | 0.0252 | 0.0081 | 5 |
| Sport Club do Recife | brazil_serie_a | 4 | 38 | 0.1053 | 0.0171 | 0.0252 | 0.0081 | 4 |
| Puebla | primera_division_liga_mx | 6 | 68 | 0.0882 | 0.0245 | 0.0317 | 0.0072 | 6 |
| Santos Laguna | primera_division_liga_mx | 6 | 68 | 0.0882 | 0.0245 | 0.0317 | 0.0072 | 7 |
| Coritiba PR | brazil_serie_b | 6 | 76 | 0.0789 | 0.0237 | 0.0308 | 0.0071 | 6 |
| Udinese | italy_serie_a | 6 | 76 | 0.0789 | 0.0243 | 0.0312 | 0.0069 | 8 |
| Alanyaspor | turkey_super_lig | 7 | 70 | 0.1000 | 0.0316 | 0.0380 | 0.0064 | 8 |
| Kilmarnock | scottish_premiership | 6 | 66 | 0.0909 | 0.0278 | 0.0340 | 0.0062 | 8 |
| AC Horsens | danish_1st_division | 4 | 44 | 0.0909 | 0.0208 | 0.0270 | 0.0062 | 6 |

## Method

- **Team rows:** each match gives two rows, one for each team: 72,476 team-matches. A comeback is one event in each role: the team that comes back, and the team that loses its lead.
- **A unit:** a team in one league, with its seasons together (`notes/ANALYSIS/CLAUDE.md` §2). 101 teams played in two leagues, so they are two units each.
- **The test** (`analysis/units.py:within_tested`): in each league, Cochran's Q of its teams around the precision-weighted mean of the teams. The sum over the 73 leagues, on 1,337 − 73 = 1,264 df. The variance of a team value uses the value of its league, times the dispersion of the matches. τ² comes from the summed Q (DerSimonian–Laird), with one value for all leagues.
- **Shrinkage:** each team toward the mean of its league. A team keeps the share τ² / (τ² + its variance) of its own distance from that mean.
- **One match, two teams** (`notes/ANALYSIS/CLAUDE.md` §5, rule 7). The tests at home and away count each match one time, because a match has one home team and one away team. The tests over home and away give each match one chance to each team, and count each comeback one time in each role. The comebacks in all matches of a team count each comeback for both teams, so they get no test.
- **At 80%** (`analysis/stats.py:detectable_tau`, with the leagues as groups) and **the luck line** (Poisson draws at the value of each team's league): as in `../PER_LEAGUE/ODDS_YARDSTICK.md`.
- **Repeat** (`analysis/units.py:repeat_test`): for each team, its value minus the value of its league, in each cohort. The Spearman correlation over the 890 teams with a season in each cohort. Cohort 2024 holds the seasons 2024 and 2024-2025, and cohort 2025 holds 2025 and 2025-2026.

## Caveats

- **The goal tests use the chi-square p.** For a count, that p is a little too small, and the sd a little too large, because the dispersion is measured around each team (`ODDS_YARDSTICK.md` of this folder, the goal tests against shuffles). With Q of 6454.4 and 4670.8 on 1,264 df, C4 does not change.
- **Few events.** A team has a median of 1 comeback and 1 lost lead in all its seasons. So the test finds only large differences between teams: at 80%, an sd of about a quarter of the rate (C1, C2).
- **The raw rates follow team strength.** Under the goal model, the stronger team is behind less often, and wins more often when it is behind (`notes/REFERENCE/MARKET_COMEBACKS.md`, "Favourite and underdog"). So C3 is strength, and strength repeats. The two links move the comeback rate in opposite directions. That can explain why C1 finds no difference while C3 does.
- **No trait.** A difference or a repeat in raw rates does not show a comeback trait of a team. Strength makes both (`notes/ANALYSIS/CLAUDE.md` §5, rule 8). `PER_TEAM/ODDS_YARDSTICK.md` takes strength out with the odds.
- **Opponents.** A team that is often behind meets strong teams more often when it is behind. A test of one team at a time cannot separate the team from its opponents (rule 7). The yardstick can, because the prices of a match carry both teams.
- **The test is generous.** The variance takes the matches of a team as independent. If they are not, Q is too large. This makes the "no sign" of C1 stronger, and the weak result of C2 weaker.
- **Looks:** 12 tests, 12 repeat tests and 12 values at 80%; 2 luck lines and 2 lists of 10 teams. No team was tested on its own.
