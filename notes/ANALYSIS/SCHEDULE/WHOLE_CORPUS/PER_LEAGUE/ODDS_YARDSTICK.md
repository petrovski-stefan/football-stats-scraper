# ODDS_YARDSTICK — the odds yardstick per league

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/PER_LEAGUE`: 73 leagues, each with its seasons together.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 prices (S1.16–18) and the opening O/U line and prices (S1.19–21), through the two-way probability S2.24. Units: the league (S1.02). The season (S1.01) gives the season cohort. Outcome: the half-time goals (S1.12–13), and S2.01, S2.02, S2.26 and S2.29.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 36,237 priced matches in 73 leagues.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.per_league.odds_yardstick`, at the commit that adds this doc. The yardstick itself is `analysis/methods/yardstick.py`.
- **Kind:** empirical.

## Question

The leagues differ in goals per match, in comebacks and in 7+ matches. Do the opening prices explain these differences? After the odds yardstick (`../ALL/ODDS_YARDSTICK.md`), does a league have more or fewer comebacks or 7+ matches than its prices expect?

The doc also tests the yardstick in each league (`notes/ANALYSIS/CLAUDE.md` §5, rule 3): its goal level, its two links and its one first-half share.

## Claims

A league's O/E is its observed count divided by the count that the yardstick expects. "sd" is the between-league standard deviation τ of the test. "At 80%" gives the sd that the test finds at p < 0.05 in 80% of simulated corpora. Each test has 72 df. "Both seasons" is the Spearman correlation of the league values, cohort 2024 against cohort 2025, over 71 leagues.

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | The leagues differ in comeback rate. After the yardstick, there is no sign that they differ in comebacks | Raw rate: Q 114.5, p = 0.00107, sd 0.0077 (14.71% of the rate 0.0522). O/E: Q 76.3, p = 0.343, sd 0.0578 (4.65% of 1.2427); shrunk 1.2117 to 1.2739. At 80%, the O/E test finds an sd of 13.48% of 1.2427: less than the spread of the raw rates | 73 leagues | O/E 0.0099. Raw rate 0.1679 | exploratory |
| C2 | The leagues have very different 7+ rates. After the yardstick, there is no clear sign that they differ in 7+ matches | Raw rate: Q 292.4, p = 2.46e-28, sd 0.0116 (51.92% of the rate 0.0224). O/E: Q 83.5, p = 0.167, sd 0.0973 (11.79% of 0.8250); shrunk 0.7285 to 0.9125. At 80%, the O/E test finds 20.85% | 73 leagues | O/E 0.1009. Raw rate 0.5595 | exploratory |
| C3 | The leagues have very different goals per match. There is no sign that the yardstick's goal O/E differs between them: the prices follow the goal level of each league | Raw: Q 1107.5, p = 3.51e-185, sd 0.2815 goals (10.24% of 2.7476). O/E: Q 86.6, p = 0.115, sd 0.0119 (1.20% of 0.9888); shrunk 0.9778 to 1.0021. At 80%, the O/E test finds 1.88% | 73 leagues | O/E 0.1714. Raw 0.8520 | exploratory |
| C4 | There is no sign that either link differs between leagues | Link 1: Q 87.2, p = 0.107; shrunk 0.9734 to 1.0070; at 80%, the test finds 2.62% of 0.9924. Link 2: Q 77.4, p = 0.311; shrunk 1.2113 to 1.2752; at 80%, 12.76% of 1.2371 | 73 leagues | link 1 −0.0270. Link 2 0.0150 | exploratory |
| C5 | There is a weak sign that the first-half share differs between leagues. The difference is small, and a share for each league does not change C1 | Share: Q 95.9, p = 0.0315, sd 0.0074 (1.66% of 0.4471); shrunk 0.4356 to 0.4546. With each league's own share: comeback O/E 1.2438 (1.2427 with one share), Q 72.2, p = 0.47 | 73 leagues | share 0.1863. Comeback O/E with the own share −0.0185 | exploratory |

## One test for each quantity

A raw rate divides by the number of matches. The share divides the first-half goals by all goals. "Dispersion" is the spread of the matches against the spread that the model of the quantity gives (Method).

| quantity | pooled | dispersion | Q | p | sd | sd / pooled | at 80% / pooled | shrunk: lowest | median | highest | both seasons |
|---|---|---|---|---|---|---|---|---|---|---|---|
| goals per match | 2.7476 | 0.9932 | 1107.5 | 3.51e-185 | 0.2815 | 0.1024 | 0.0190 | 2.2275 | 2.7479 | 3.5271 | 0.8520 |
| goals O/E | 0.9888 | 0.9730 | 86.6 | 0.115 | 0.0119 | 0.0120 | 0.0188 | 0.9778 | 0.9886 | 1.0021 | 0.1714 |
| comeback rate | 0.0522 | 1.0000 | 114.5 | 0.00107 | 0.0077 | 0.1471 | 0.1349 | 0.0408 | 0.0524 | 0.0624 | 0.1679 |
| comeback O/E | 1.2427 | 1.0008 | 76.3 | 0.343 | 0.0578 | 0.0465 | 0.1348 | 1.2117 | 1.2443 | 1.2739 | 0.0099 |
| link 1 O/E | 0.9924 | 0.9985 | 87.2 | 0.107 | 0.0170 | 0.0171 | 0.0262 | 0.9734 | 0.9941 | 1.0070 | −0.0270 |
| link 2 O/E | 1.2371 | 1.0049 | 77.4 | 0.311 | 0.0613 | 0.0496 | 0.1276 | 1.2113 | 1.2369 | 1.2752 | 0.0150 |
| 7+ rate | 0.0224 | 1.0000 | 292.4 | 2.46e-28 | 0.0116 | 0.5192 | 0.2090 | 0.0072 | 0.0204 | 0.0544 | 0.5595 |
| 7+ O/E | 0.8250 | 1.0011 | 83.5 | 0.167 | 0.0973 | 0.1179 | 0.2085 | 0.7285 | 0.8195 | 0.9125 | 0.1009 |
| first-half share | 0.4471 | 0.9147 | 95.9 | 0.0315 | 0.0074 | 0.0166 | 0.0203 | 0.4356 | 0.4474 | 0.4546 | 0.1863 |
| comeback O/E, own share | 1.2438 | 1.0008 | 72.2 | 0.47 | 0.0137 | 0.0110 | 0.1348 | 1.2421 | 1.2441 | 1.2458 | −0.0185 |

Without the yardstick, the leagues differ in all three rates. The goal and 7+ rates also keep much of their order from one cohort to the next. After the yardstick, no O/E test finds a difference, and the league O/E of the two cohorts agree little (Spearman −0.0270 to 0.1714).

## The luck line

If all leagues had the pooled value, the raw league values would still spread. The table gives the median lowest and highest value over 2,000 Poisson draws, next to the real raw values.

| quantity | real lowest | real highest | luck lowest | luck highest |
|---|---|---|---|---|
| goals O/E | 0.9234 | 1.0712 | 0.9215 | 1.0582 |
| comeback O/E | 0.5764 | 1.8021 | 0.6614 | 1.9113 |
| 7+ O/E | 0.2552 | 1.6184 | 0.2090 | 1.6073 |

So a raw comeback O/E of 1.80 in one league is in the range of luck. Read the shrunk values.

## League values

The order is that of the league names, because no O/E test found a difference. The names are those of the stage files. "Comebacks" and "7+" are observed counts, and "expected" is the count of the yardstick. The two links of each league are in the runner's output only.

| league | matches | goals O/E | shrunk | comebacks | expected | O/E | shrunk | 7+ | expected | O/E | shrunk | first-half share | shrunk |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| austrian_bundesliga | 264 | 0.9707 | 0.9871 | 12 | 11.4 | 1.0523 | 1.2368 | 4 | 6.9 | 0.5839 | 0.8072 | 0.4492 | 0.4474 |
| belgian_pro_league | 480 | 0.9234 | 0.9778 | 20 | 21.3 | 0.9375 | 1.2253 | 13 | 13.9 | 0.9354 | 0.8407 | 0.4627 | 0.4508 |
| brasileiro,_serie_c | 380 | 0.9881 | 0.9888 | 21 | 12.2 | 1.7166 | 1.2585 | 2 | 3.3 | 0.5977 | 0.8167 | 0.4581 | 0.4490 |
| brazil_serie_a | 760 | 1.0344 | 0.9985 | 26 | 26.3 | 0.9894 | 1.2253 | 6 | 9.3 | 0.6478 | 0.8080 | 0.4492 | 0.4477 |
| brazil_serie_b | 760 | 0.9894 | 0.9890 | 36 | 23.6 | 1.5228 | 1.2601 | 3 | 6.3 | 0.4746 | 0.8013 | 0.4501 | 0.4480 |
| bulgaria_first_league | 480 | 0.9558 | 0.9839 | 13 | 15.8 | 0.8210 | 1.2248 | 5 | 7.3 | 0.6831 | 0.8140 | 0.4443 | 0.4465 |
| chile_primera_division | 480 | 1.0124 | 0.9926 | 23 | 19.8 | 1.1621 | 1.2385 | 8 | 9.9 | 0.8072 | 0.8233 | 0.4219 | 0.4410 |
| chinese_football_association_jia_league | 480 | 1.0171 | 0.9931 | 10 | 17.3 | 0.5764 | 1.2117 | 10 | 7.5 | 1.3260 | 0.8656 | 0.4424 | 0.4460 |
| chinese_super_league | 480 | 1.0229 | 0.9950 | 32 | 22.2 | 1.4404 | 1.2546 | 23 | 20.2 | 1.1375 | 0.8862 | 0.4596 | 0.4504 |
| croatia_1.division | 360 | 0.9571 | 0.9850 | 14 | 13.5 | 1.0403 | 1.2353 | 3 | 7.0 | 0.4270 | 0.7949 | 0.4862 | 0.4541 |
| cyprus_1_division | 363 | 0.9435 | 0.9830 | 19 | 13.7 | 1.3909 | 1.2483 | 7 | 9.3 | 0.7508 | 0.8178 | 0.4311 | 0.4441 |
| czech_republic_gambrinus_liga | 480 | 0.9290 | 0.9789 | 22 | 19.4 | 1.1363 | 1.2372 | 9 | 12.9 | 0.6999 | 0.8087 | 0.4728 | 0.4531 |
| danish_1st_division | 264 | 0.9311 | 0.9828 | 11 | 12.4 | 0.8885 | 1.2306 | 4 | 9.3 | 0.4292 | 0.7857 | 0.4600 | 0.4490 |
| denmark_superliga | 264 | 1.0264 | 0.9928 | 15 | 12.5 | 1.1959 | 1.2411 | 3 | 9.6 | 0.3135 | 0.7731 | 0.4757 | 0.4518 |
| england_league_1 | 1104 | 0.9883 | 0.9887 | 50 | 44.7 | 1.1179 | 1.2287 | 19 | 21.5 | 0.8851 | 0.8372 | 0.4415 | 0.4448 |
| england_league_2 | 1104 | 0.9676 | 0.9825 | 46 | 44.8 | 1.0276 | 1.2185 | 15 | 20.5 | 0.7303 | 0.8068 | 0.4407 | 0.4445 |
| english_premier_league | 760 | 0.9582 | 0.9812 | 52 | 34.1 | 1.5269 | 1.2679 | 17 | 25.9 | 0.6573 | 0.7857 | 0.4491 | 0.4478 |
| estonia_champions_league | 360 | 0.9799 | 0.9876 | 19 | 16.3 | 1.1690 | 1.2395 | 12 | 15.9 | 0.7540 | 0.8137 | 0.4806 | 0.4542 |
| finland_veikkausliga | 264 | 1.0712 | 0.9973 | 21 | 11.8 | 1.7752 | 1.2601 | 9 | 8.3 | 1.0871 | 0.8485 | 0.4130 | 0.4414 |
| finland_ykkonen | 270 | 1.0062 | 0.9908 | 16 | 13.3 | 1.2057 | 1.2414 | 12 | 12.7 | 0.9439 | 0.8410 | 0.4415 | 0.4461 |
| france_ligue_1 | 612 | 1.0052 | 0.9922 | 27 | 26.5 | 1.0179 | 1.2270 | 20 | 18.7 | 1.0691 | 0.8694 | 0.4363 | 0.4438 |
| france_ligue_2 | 612 | 1.0106 | 0.9929 | 30 | 23.5 | 1.2755 | 1.2448 | 11 | 9.8 | 1.1204 | 0.8554 | 0.4486 | 0.4475 |
| german_3.liga | 760 | 1.0263 | 0.9982 | 47 | 36.7 | 1.2792 | 1.2462 | 29 | 25.5 | 1.1384 | 0.8977 | 0.4436 | 0.4458 |
| german_bundesliga | 612 | 1.0074 | 0.9930 | 32 | 29.7 | 1.0765 | 1.2297 | 22 | 28.0 | 0.7863 | 0.8154 | 0.4572 | 0.4503 |
| german_bundesliga_2 | 612 | 0.9809 | 0.9871 | 41 | 30.3 | 1.3511 | 1.2514 | 20 | 22.3 | 0.8983 | 0.8404 | 0.4451 | 0.4465 |
| greece_super_league_a | 364 | 0.9373 | 0.9825 | 17 | 12.6 | 1.3523 | 1.2465 | 3 | 7.5 | 0.3999 | 0.7907 | 0.4494 | 0.4475 |
| holland_eerste_divisie | 760 | 0.9585 | 0.9808 | 51 | 39.7 | 1.2833 | 1.2469 | 19 | 37.1 | 0.5117 | 0.7285 | 0.4453 | 0.4464 |
| holland_eredivisie | 612 | 0.9791 | 0.9867 | 30 | 28.6 | 1.0481 | 1.2280 | 23 | 27.3 | 0.8432 | 0.8296 | 0.4496 | 0.4479 |
| hungary_borsodi_liga | 396 | 0.9836 | 0.9881 | 24 | 18.3 | 1.3148 | 1.2463 | 16 | 12.8 | 1.2482 | 0.8809 | 0.4385 | 0.4452 |
| iceland_premier_division | 264 | 0.9683 | 0.9864 | 25 | 14.6 | 1.7099 | 1.2617 | 13 | 16.6 | 0.7836 | 0.8182 | 0.4557 | 0.4486 |
| ireland_first_division | 360 | 1.0041 | 0.9908 | 19 | 14.9 | 1.2769 | 1.2441 | 5 | 7.7 | 0.6461 | 0.8103 | 0.4504 | 0.4477 |
| ireland_premier_division | 360 | 0.9371 | 0.9828 | 19 | 13.3 | 1.4321 | 1.2496 | 4 | 5.5 | 0.7277 | 0.8193 | 0.4615 | 0.4495 |
| italy_serie_a | 760 | 0.9624 | 0.9829 | 37 | 28.1 | 1.3155 | 1.2481 | 6 | 14.0 | 0.4284 | 0.7694 | 0.4327 | 0.4425 |
| italy_serie_b | 760 | 1.0262 | 0.9969 | 27 | 28.0 | 0.9634 | 1.2223 | 10 | 10.3 | 0.9695 | 0.8406 | 0.4565 | 0.4501 |
| j2_league | 380 | 0.9785 | 0.9876 | 23 | 14.8 | 1.5583 | 1.2554 | 4 | 5.9 | 0.6751 | 0.8155 | 0.4411 | 0.4460 |
| j3_league | 760 | 1.0284 | 0.9975 | 40 | 29.2 | 1.3715 | 1.2526 | 18 | 11.5 | 1.5661 | 0.9125 | 0.4285 | 0.4411 |
| japan_j1_league | 380 | 0.9721 | 0.9868 | 16 | 14.3 | 1.1200 | 1.2380 | 9 | 5.6 | 1.6184 | 0.8734 | 0.4215 | 0.4424 |
| k_league_1 | 396 | 1.0219 | 0.9932 | 25 | 16.0 | 1.5593 | 1.2565 | 4 | 6.9 | 0.5836 | 0.8073 | 0.3904 | 0.4356 |
| liga_auf_uruguaya | 480 | 0.9608 | 0.9847 | 20 | 17.3 | 1.1538 | 1.2386 | 7 | 6.8 | 1.0276 | 0.8400 | 0.4316 | 0.4437 |
| liga_de_expansion_mx | 420 | 1.0303 | 0.9950 | 17 | 18.3 | 0.9290 | 1.2272 | 11 | 11.4 | 0.9647 | 0.8417 | 0.4531 | 0.4484 |
| liga_portugal_1 | 612 | 0.9914 | 0.9893 | 20 | 21.8 | 0.9156 | 1.2238 | 4 | 13.5 | 0.2967 | 0.7526 | 0.4493 | 0.4477 |
| liga_portugal_2 | 612 | 0.9917 | 0.9894 | 41 | 23.5 | 1.7425 | 1.2739 | 8 | 8.9 | 0.8977 | 0.8320 | 0.4509 | 0.4481 |
| national_premier_leagues_western_australia | 264 | 1.0532 | 0.9965 | 23 | 14.8 | 1.5541 | 1.2555 | 19 | 16.7 | 1.1391 | 0.8781 | 0.4457 | 0.4468 |
| northern_ireland_premier_league | 396 | 0.9593 | 0.9847 | 24 | 16.2 | 1.4804 | 1.2532 | 5 | 9.5 | 0.5264 | 0.7952 | 0.4351 | 0.4446 |
| norway_eliteserien | 480 | 0.9873 | 0.9886 | 28 | 22.5 | 1.2471 | 1.2430 | 13 | 18.8 | 0.6925 | 0.8008 | 0.4391 | 0.4450 |
| nsw_premier_league | 480 | 0.9440 | 0.9803 | 29 | 25.6 | 1.1341 | 1.2353 | 22 | 27.3 | 0.8054 | 0.8203 | 0.4750 | 0.4546 |
| poland_ekstraklasa | 612 | 1.0001 | 0.9911 | 25 | 26.3 | 0.9489 | 1.2223 | 17 | 14.4 | 1.1832 | 0.8768 | 0.4673 | 0.4529 |
| poland_liga_1 | 612 | 1.0120 | 0.9935 | 34 | 26.9 | 1.2648 | 1.2443 | 9 | 16.0 | 0.5632 | 0.7837 | 0.4618 | 0.4514 |
| primera_division_de_paraguay | 528 | 0.9693 | 0.9857 | 34 | 18.9 | 1.8021 | 1.2710 | 10 | 7.0 | 1.4334 | 0.8707 | 0.4434 | 0.4462 |
| primera_division_de_venezuela | 388 | 0.9998 | 0.9902 | 19 | 13.3 | 1.4252 | 1.2493 | 2 | 4.3 | 0.4644 | 0.8080 | 0.4665 | 0.4506 |
| primera_division_liga_mx | 612 | 0.9870 | 0.9885 | 30 | 26.9 | 1.1173 | 1.2338 | 14 | 17.6 | 0.7934 | 0.8197 | 0.4608 | 0.4511 |
| qatar_stars_league | 264 | 0.9941 | 0.9895 | 22 | 14.0 | 1.5665 | 1.2553 | 14 | 15.0 | 0.9344 | 0.8419 | 0.4381 | 0.4455 |
| romania_liga_i | 480 | 0.9791 | 0.9874 | 16 | 17.4 | 0.9218 | 1.2278 | 4 | 7.0 | 0.5703 | 0.8059 | 0.4631 | 0.4506 |
| saudi_professional_league | 612 | 0.9850 | 0.9880 | 34 | 26.6 | 1.2760 | 1.2451 | 18 | 24.2 | 0.7441 | 0.8069 | 0.4262 | 0.4407 |
| scottish_championship | 360 | 0.9607 | 0.9855 | 17 | 13.9 | 1.2259 | 1.2421 | 3 | 6.2 | 0.4854 | 0.8023 | 0.4764 | 0.4523 |
| scottish_division_one | 360 | 0.9829 | 0.9881 | 16 | 15.4 | 1.0400 | 1.2343 | 3 | 7.9 | 0.3788 | 0.7873 | 0.4387 | 0.4455 |
| scottish_division_two | 360 | 0.9933 | 0.9894 | 13 | 15.8 | 0.8213 | 1.2246 | 7 | 9.1 | 0.7667 | 0.8195 | 0.4604 | 0.4497 |
| scottish_premiership | 396 | 0.9942 | 0.9896 | 22 | 16.2 | 1.3564 | 1.2478 | 6 | 11.7 | 0.5145 | 0.7875 | 0.4485 | 0.4474 |
| serbian_superliga | 480 | 0.9776 | 0.9870 | 22 | 19.1 | 1.1515 | 1.2381 | 13 | 13.8 | 0.9395 | 0.8414 | 0.4545 | 0.4489 |
| slovak_super_liga | 264 | 0.9783 | 0.9878 | 10 | 11.6 | 0.8603 | 1.2305 | 2 | 7.8 | 0.2552 | 0.7769 | 0.4516 | 0.4478 |
| spanish_la_liga | 760 | 1.0091 | 0.9935 | 45 | 28.7 | 1.5680 | 1.2672 | 14 | 17.2 | 0.8141 | 0.8233 | 0.4334 | 0.4426 |
| spanish_la_liga_2 | 924 | 1.0412 | 1.0021 | 44 | 34.2 | 1.2871 | 1.2467 | 13 | 14.1 | 0.9237 | 0.8390 | 0.4335 | 0.4421 |
| sweden_superettan | 480 | 0.9758 | 0.9867 | 30 | 21.3 | 1.4068 | 1.2521 | 11 | 12.5 | 0.8824 | 0.8325 | 0.4337 | 0.4438 |
| swedish_allsvenskan | 480 | 0.9841 | 0.9880 | 20 | 21.5 | 0.9294 | 1.2246 | 19 | 14.2 | 1.3364 | 0.8986 | 0.4395 | 0.4452 |
| switzerland_challenge_league | 360 | 1.0143 | 0.9923 | 18 | 17.4 | 1.0369 | 1.2330 | 14 | 12.2 | 1.1480 | 0.8658 | 0.4675 | 0.4514 |
| switzerland_super_league | 396 | 0.9896 | 0.9890 | 26 | 19.7 | 1.3167 | 1.2467 | 10 | 15.6 | 0.6419 | 0.7965 | 0.4425 | 0.4460 |
| thai_league_1 | 480 | 0.9639 | 0.9845 | 34 | 21.6 | 1.5741 | 1.2620 | 16 | 16.3 | 0.9844 | 0.8509 | 0.4287 | 0.4425 |
| turkey_super_lig | 648 | 0.9768 | 0.9863 | 41 | 27.7 | 1.4814 | 1.2602 | 16 | 19.6 | 0.8148 | 0.8232 | 0.4400 | 0.4449 |
| uae_pro-league | 364 | 0.9576 | 0.9843 | 24 | 17.2 | 1.3921 | 1.2498 | 11 | 16.0 | 0.6864 | 0.8028 | 0.4475 | 0.4472 |
| v.league_1 | 364 | 0.9964 | 0.9898 | 21 | 13.6 | 1.5432 | 1.2539 | 3 | 6.3 | 0.4741 | 0.8010 | 0.4617 | 0.4498 |
| vic_premier_league | 364 | 1.0043 | 0.9912 | 20 | 18.9 | 1.0580 | 1.2332 | 18 | 20.1 | 0.8954 | 0.8389 | 0.4438 | 0.4463 |
| victorian_state_league_division_1 | 364 | 1.0255 | 0.9946 | 27 | 20.5 | 1.3173 | 1.2469 | 25 | 24.5 | 1.0204 | 0.8702 | 0.4485 | 0.4474 |
| welsh_premier_league | 264 | 1.0008 | 0.9901 | 17 | 11.4 | 1.4916 | 1.2506 | 11 | 10.3 | 1.0651 | 0.8517 | 0.4651 | 0.4500 |

## Method

- **The yardstick:** `../ALL/ODDS_YARDSTICK.md` (Method), on the same priced matches and with the same first-half share, 0.4471.
- **A league value:** the sum of the observed values of its matches, divided by the sum of their expected values. For a raw rate, each match expects 1. For the share, each match "expects" its goals.
- **The test:** Cochran's Q over the 73 league values, one test for each quantity. The between-league variance τ² comes from the method of moments (DerSimonian–Laird), as in `SHIN.md` of this folder. The pooled value in the tables is the value of all matches together: the sum of all observed values, divided by the sum of all expected values.
- **The variance of a league value:** the variance if all leagues had the pooled value. The goals of a match are a Poisson count. A comeback, a decisive half-time and a 7+ match are 0 or 1, with the chance pooled value × expected value. The first-half goals of a match are binomial over its goals.
- **Dispersion:** the squared distance of each match from its league value, summed, divided by the summed variance that the model of the quantity gives at that value (the runner's `dispersion`). The variance of each league value is multiplied by it. For the 0/1 outcomes it is from 0.9985 to 1.0049, so the model fits. For the goal O/E it is 0.9730: given the yardstick, goal counts vary a little less than Poisson counts. For the raw goals it is 0.9932. For the share it is 0.9147: the goals of one match divide between the halves more evenly than a binomial count.
- **Shrinkage:** Empirical-Bayes normal shrinkage to the precision-weighted mean of the league values (`analysis/stats.py:shrink`), as in `SHIN.md` of this folder.
- **At 80%** (`analysis/stats.py:detectable_tau`): 2,000 simulated corpora under the normal random-effects model, each league with its own variance. For each τ, the share of the corpora that give p < 0.05. A bisection finds the τ where this share is 0.80.
- **The luck line:** 2,000 Poisson draws of the count of each league, at the pooled value. The median of the lowest and of the highest league value.
- **The own share:** the share of the goals of a league that came in the first half. The yardstick's comeback chances are calculated again, with that share for the matches of the league.
- **Both seasons:** cohort 2024 holds the seasons 2024 and 2024-2025, and cohort 2025 holds 2025 and 2025-2026. 71 leagues have a season in each cohort. 2 leagues have one season only.

## Caveats

- **"No sign" has a size.** At 80%, the O/E tests find a between-league sd of 13.48% (comebacks), 20.85% (7+) and 1.88% (goals) of the pooled value. A smaller difference between leagues can exist, and this corpus does not see it.
- **The test is generous.** The variance takes the matches of a league as independent, given the yardstick. Teams and league-seasons can make them dependent. Then Q is too large. So the "no sign" of C1–C4 is stronger, not weaker. The raw tests and C5 can be a little too strong.
- **Shrunk values without a spread.** When a test finds no clear spread, the shrunk values stay near the pooled value. They do not show that one league is different.
- **The own share comes from the same goals.** The share of a league comes from the goals of its matches, and its comebacks come from the same goals. This can move the comeback test toward "no difference". The test moved from p = 0.343 to p = 0.47.
- **Why the share does not change C1.** In `../ALL/ODDS_YARDSTICK.md` (C9), a shift of 0.02 in the share for all matches changes the comeback O/E from 1.2427 to 1.2023 or 1.2892. The sd of the share between leagues is 0.0074.
- **Raw rates are only the baseline.** They show how much of the league differences the prices explain. The rates of each league are the subject of `PER_LEAGUE/RATES.md` (`notes/WORKING/PLAN_2026-10-16_ANALYSIS_MIGRATION.md`, step 3).
- **Looks:** 9 tests across the leagues and 1 with the own share; for each, one cohort correlation and one sd at 80%; 4 luck lines, 3 of them in this doc. C5's p = 0.0315 is one of the 10 tests. Read it as a weak sign.
- **Not profit.** A league with more comebacks than the yardstick does not show value. The value needs the 2/1 and 1/2 prices, and nowgoal does not show them.
- **Opening prices only.** The closing prices are on the detail page, which the staged pipeline does not read yet.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-19 | 144 league-seasons, 36,238 matches | first run |
