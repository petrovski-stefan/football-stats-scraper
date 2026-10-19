# RATES — comebacks and 7+ matches per league

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/PER_LEAGUE`: 73 leagues, each with its seasons together.
- **Sources:** schedule stage 3, outcomes only: the half-time goals (S1.12–13), the goals in total and in each half (S2.01–03), and the labels S2.26–29. Units: the league (S1.02, S1.03) and the league-season (with S1.01). The stage (S1.04) gives the stage slice.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches, in 73 leagues.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.per_league.rates`, at the commit that adds this doc.
- **Kind:** empirical: how often each outcome happened in each league.

## Question

Which leagues have the most comebacks and the most 7+ matches? Do the leagues differ by more than luck? This doc gives the card of the `PER_LEAGUE/` level (`notes/ANALYSIS/CLAUDE.md` §2) for each league, with one test across the leagues for each value.

## Claims

"sd" is the between-league standard deviation τ of the test. "At 80%" gives the sd that the test finds at p < 0.05 in 80% of simulated corpora. Each test across the leagues has 72 df. "Both seasons" is the Spearman correlation of the league values, cohort 2024 against cohort 2025, over 71 leagues.

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | The leagues differ in comeback rate. A league does not change between its seasons by more than noise | Q 114.5, p = 0.00107, sd 0.0077 (14.71% of the rate 0.0522); shrunk 0.0408 to 0.0624. Raw 0.0208 to 0.0947; with no difference, luck alone gives 0.0271 to 0.0806. League-seasons inside their league: Q 75.9 on 71 df, p = 0.324 | 73 leagues | the order hardly repeats: 0.1679 | exploratory |
| C2 | The leagues differ clearly in how often a team is behind at half-time, and less clearly in how often the team behind wins | link 1: Q 271.8, p = 5.68e-25, sd 0.0368 (6.23% of 0.5909); shrunk 0.5058 to 0.6462. Link 2: Q 100.7, p = 0.0144, sd 0.0105 (11.86% of 0.0883); shrunk 0.0766 to 0.0995 | 73 leagues | link 1 0.4463, link 2 0.1505 | exploratory |
| C3 | How often the home team, and how often the away team, is behind at half-time differs between leagues. When behind, the home team's win rate shows no clear difference | home behind: Q 184.2, p = 8.81e-12, sd 0.0244. Away behind: Q 144.3, p = 9.22e-07, sd 0.0213. Home team behind wins: Q 89.4, p = 0.0808. Away team behind wins: Q 99.7, p = 0.017 | 73 leagues | 0.4454, 0.2503, 0.1205, 0.0960 | exploratory |
| C4 | The leagues differ much in 7+ rate, and a league also changes between its seasons | Q 292.4, p = 2.45e-28, sd 0.0116 (51.92% of the rate 0.0224); shrunk 0.0072 to 0.0544. Raw 0.0039 to 0.0720; luck alone gives 0.0076 to 0.0417. League-seasons inside their league: Q 105.6 on 71 df, p = 0.0048 | 73 leagues | yes: 0.5595 | exploratory |
| C5 | The leagues differ much in goals per match, in each half too, and a league also changes between its seasons | Q 1107.5, p = 3.52e-185, sd 0.2815 goals (10.24% of 2.7476); shrunk 2.2275 to 3.5271. First half: sd 0.1306. Second half: sd 0.1538. League-seasons inside their league: Q 107.5 on 71 df, p = 0.00335 | 73 leagues | yes: 0.8520 (first half 0.7049, second half 0.8098) | exploratory |
| C6 | In the leagues with an Apertura and a Clausura, the two stages show no clear difference | comeback 0.0440 [0.0356, 0.0538] in the Apertura, 0.0549 [0.0411, 0.0745] in the Clausura. 7+ goals 0.0163 [0.0104, 0.0227] and 0.0200 [0.0107, 0.0307]. Goals per match 2.5661 [2.4109, 2.7228] and 2.5807 [2.3611, 2.7990] | 5 leagues: 1,226 and 1,202 matches | not measured | exploratory |

## These differences are in the prices

`PER_LEAGUE/ODDS_YARDSTICK.md` (C1–C3) tests the same leagues against the odds yardstick. After the yardstick, there is no sign that the leagues differ in comebacks, in 7+ matches or in goals. So a league with a high comeback rate is a league where the opening prices already expect more comebacks. The table below tells where comebacks happen. It does not tell where they happen more often than the prices expect.

## One test for each value of the card

| quantity | pooled | dispersion | Q | p | sd | sd / pooled | at 80% / pooled | shrunk: lowest | median | highest | both seasons |
|---|---|---|---|---|---|---|---|---|---|---|---|
| comeback | 0.0522 | 1.0000 | 114.5 | 0.00107 | 0.0077 | 0.1471 | 0.1349 | 0.0408 | 0.0524 | 0.0624 | 0.1679 |
| link 1: a team is behind at half-time | 0.5909 | 1.0000 | 271.8 | 5.68e-25 | 0.0368 | 0.0623 | 0.0263 | 0.5058 | 0.5975 | 0.6462 | 0.4463 |
| link 2: the team behind wins | 0.0883 | 1.0000 | 100.7 | 0.0144 | 0.0105 | 0.1186 | 0.1327 | 0.0766 | 0.0883 | 0.0995 | 0.1505 |
| home comeback | 0.0297 | 1.0000 | 98.4 | 0.021 | 0.0046 | 0.1557 | 0.1810 | 0.0235 | 0.0291 | 0.0360 | 0.1035 |
| home team behind at half-time | 0.2548 | 1.0000 | 184.2 | 8.81e-12 | 0.0244 | 0.0959 | 0.0541 | 0.2060 | 0.2552 | 0.2973 | 0.4454 |
| home team behind wins | 0.1164 | 1.0000 | 89.4 | 0.0808 | 0.0140 | 0.1204 | 0.1729 | 0.1046 | 0.1158 | 0.1324 | 0.1205 |
| away comeback | 0.0225 | 1.0000 | 104.3 | 0.0077 | 0.0045 | 0.1982 | 0.2085 | 0.0176 | 0.0226 | 0.0278 | 0.1090 |
| away team behind at half-time | 0.3361 | 1.0000 | 144.3 | 9.22e-07 | 0.0213 | 0.0633 | 0.0445 | 0.3023 | 0.3357 | 0.3710 | 0.2503 |
| away team behind wins | 0.0670 | 1.0000 | 99.7 | 0.017 | 0.0120 | 0.1794 | 0.2036 | 0.0529 | 0.0676 | 0.0797 | 0.0960 |
| 7+ goals | 0.0224 | 1.0000 | 292.4 | 2.45e-28 | 0.0116 | 0.5192 | 0.2090 | 0.0072 | 0.0204 | 0.0544 | 0.5595 |
| goals in the first half | 1.2283 | 0.9635 | 585.9 | 1.43e-81 | 0.1306 | 0.1063 | 0.0280 | 1.0119 | 1.2309 | 1.5442 | 0.7049 |
| goals in the second half | 1.5193 | 0.9436 | 660.7 | 5.32e-96 | 0.1538 | 0.1012 | 0.0249 | 1.2345 | 1.5098 | 1.9195 | 0.8098 |
| goals per match | 2.7476 | 0.9931 | 1107.5 | 3.52e-185 | 0.2815 | 0.1024 | 0.0190 | 2.2275 | 2.7479 | 3.5271 | 0.8520 |

## League values

The leagues in the order of their shrunk comeback rate, highest first (`notes/ANALYSIS/CLAUDE.md` §5, rule 1). The names are those of the stage files. "Comebacks" and "7+" are counts. The goals are means per match. The home and away values of each league are in the runner's output only.

| league | matches | comebacks | rate | shrunk | link 1 shrunk | link 2 shrunk | 7+ | 7+ rate | 7+ shrunk | goals 1H | goals 2H |
|---|---|---|---|---|---|---|---|---|---|---|---|
| iceland_premier_division | 264 | 25 | 0.0947 | 0.0624 | 0.6203 | 0.0995 | 13 | 0.0492 | 0.0390 | 1.5189 | 1.8144 |
| national_premier_leagues_western_australia | 264 | 23 | 0.0871 | 0.0605 | 0.6451 | 0.0961 | 19 | 0.0720 | 0.0531 | 1.6174 | 2.0114 |
| english_premier_league | 760 | 52 | 0.0684 | 0.0599 | 0.6249 | 0.0962 | 17 | 0.0224 | 0.0224 | 1.2763 | 1.5658 |
| qatar_stars_league | 264 | 22 | 0.0833 | 0.0596 | 0.6045 | 0.0969 | 14 | 0.0530 | 0.0414 | 1.4621 | 1.8750 |
| holland_eerste_divisie | 760 | 51 | 0.0671 | 0.0593 | 0.6462 | 0.0938 | 19 | 0.0250 | 0.0245 | 1.3829 | 1.7224 |
| thai_league_1 | 480 | 34 | 0.0708 | 0.0590 | 0.6188 | 0.0954 | 16 | 0.0333 | 0.0306 | 1.2271 | 1.6354 |
| victorian_state_league_division_1 | 364 | 27 | 0.0742 | 0.0588 | 0.6202 | 0.0952 | 25 | 0.0687 | 0.0544 | 1.6044 | 1.9725 |
| finland_veikkausliga | 264 | 21 | 0.0795 | 0.0587 | 0.5999 | 0.0960 | 9 | 0.0341 | 0.0297 | 1.2955 | 1.8409 |
| german_bundesliga_2 | 612 | 41 | 0.0670 | 0.0584 | 0.5914 | 0.0966 | 20 | 0.0327 | 0.0305 | 1.3252 | 1.6520 |
| liga_portugal_2 | 612 | 41 | 0.0670 | 0.0584 | 0.5673 | 0.0983 | 8 | 0.0131 | 0.0150 | 1.1176 | 1.3611 |
| chinese_super_league | 480 | 32 | 0.0667 | 0.0575 | 0.6400 | 0.0922 | 23 | 0.0479 | 0.0415 | 1.4563 | 1.7125 |
| turkey_super_lig | 648 | 41 | 0.0633 | 0.0570 | 0.5983 | 0.0942 | 16 | 0.0247 | 0.0242 | 1.2330 | 1.5694 |
| primera_division_de_paraguay | 528 | 34 | 0.0644 | 0.0569 | 0.5343 | 0.0982 | 10 | 0.0189 | 0.0198 | 1.0455 | 1.3125 |
| german_3.liga | 760 | 47 | 0.0618 | 0.0568 | 0.6185 | 0.0925 | 29 | 0.0382 | 0.0354 | 1.3553 | 1.7000 |
| switzerland_super_league | 396 | 26 | 0.0657 | 0.0565 | 0.6083 | 0.0929 | 10 | 0.0253 | 0.0244 | 1.3510 | 1.7020 |
| uae_pro-league | 364 | 24 | 0.0659 | 0.0563 | 0.5963 | 0.0933 | 11 | 0.0302 | 0.0278 | 1.3462 | 1.6621 |
| sweden_superettan | 480 | 30 | 0.0625 | 0.0559 | 0.5884 | 0.0933 | 11 | 0.0229 | 0.0228 | 1.1917 | 1.5562 |
| k_league_1 | 396 | 25 | 0.0631 | 0.0557 | 0.5404 | 0.0957 | 4 | 0.0101 | 0.0137 | 1.0303 | 1.6086 |
| spanish_la_liga | 760 | 45 | 0.0592 | 0.0555 | 0.5727 | 0.0942 | 14 | 0.0184 | 0.0191 | 1.1513 | 1.5053 |
| nsw_premier_league | 480 | 29 | 0.0604 | 0.0552 | 0.6431 | 0.0892 | 22 | 0.0458 | 0.0399 | 1.5042 | 1.6625 |
| welsh_premier_league | 264 | 17 | 0.0644 | 0.0551 | 0.6022 | 0.0914 | 11 | 0.0417 | 0.0343 | 1.4129 | 1.6250 |
| hungary_borsodi_liga | 396 | 24 | 0.0606 | 0.0549 | 0.5787 | 0.0924 | 16 | 0.0404 | 0.0352 | 1.2702 | 1.6263 |
| northern_ireland_premier_league | 396 | 24 | 0.0606 | 0.0549 | 0.6031 | 0.0911 | 5 | 0.0126 | 0.0155 | 1.1515 | 1.4949 |
| j2_league | 380 | 23 | 0.0605 | 0.0548 | 0.5684 | 0.0928 | 4 | 0.0105 | 0.0141 | 1.0842 | 1.3737 |
| norway_eliteserien | 480 | 28 | 0.0583 | 0.0544 | 0.6173 | 0.0897 | 13 | 0.0271 | 0.0259 | 1.3229 | 1.6896 |
| finland_ykkonen | 270 | 16 | 0.0593 | 0.0539 | 0.6164 | 0.0893 | 12 | 0.0444 | 0.0362 | 1.4111 | 1.7852 |
| v.league_1 | 364 | 21 | 0.0577 | 0.0538 | 0.5926 | 0.0903 | 3 | 0.0082 | 0.0126 | 1.1758 | 1.3709 |
| poland_liga_1 | 612 | 34 | 0.0556 | 0.0536 | 0.5977 | 0.0898 | 9 | 0.0147 | 0.0163 | 1.3121 | 1.5294 |
| saudi_professional_league | 612 | 34 | 0.0556 | 0.0536 | 0.6091 | 0.0890 | 18 | 0.0294 | 0.0279 | 1.2696 | 1.7092 |
| denmark_superliga | 264 | 15 | 0.0568 | 0.0533 | 0.6090 | 0.0889 | 3 | 0.0114 | 0.0156 | 1.4811 | 1.6326 |
| scottish_premiership | 396 | 22 | 0.0556 | 0.0533 | 0.6327 | 0.0875 | 6 | 0.0152 | 0.0173 | 1.2753 | 1.5682 |
| brasileiro,_serie_c | 380 | 21 | 0.0553 | 0.0531 | 0.5720 | 0.0905 | 2 | 0.0053 | 0.0104 | 1.0211 | 1.2079 |
| vic_premier_league | 364 | 20 | 0.0549 | 0.0530 | 0.6460 | 0.0866 | 18 | 0.0495 | 0.0411 | 1.4863 | 1.8626 |
| j3_league | 760 | 40 | 0.0526 | 0.0524 | 0.5514 | 0.0915 | 18 | 0.0237 | 0.0235 | 1.1039 | 1.4724 |
| estonia_champions_league | 360 | 19 | 0.0528 | 0.0524 | 0.6434 | 0.0860 | 12 | 0.0333 | 0.0299 | 1.4833 | 1.6028 |
| ireland_first_division | 360 | 19 | 0.0528 | 0.0524 | 0.5951 | 0.0883 | 5 | 0.0139 | 0.0165 | 1.2222 | 1.4917 |
| ireland_premier_division | 360 | 19 | 0.0528 | 0.0524 | 0.5803 | 0.0891 | 4 | 0.0111 | 0.0146 | 1.0833 | 1.2639 |
| german_bundesliga | 612 | 32 | 0.0523 | 0.0522 | 0.6331 | 0.0858 | 22 | 0.0359 | 0.0331 | 1.4559 | 1.7288 |
| cyprus_1_division | 364 | 19 | 0.0522 | 0.0522 | 0.6294 | 0.0864 | 7 | 0.0192 | 0.0202 | 1.1264 | 1.4945 |
| switzerland_challenge_league | 360 | 18 | 0.0500 | 0.0515 | 0.6044 | 0.0868 | 14 | 0.0389 | 0.0338 | 1.4167 | 1.6139 |
| primera_division_de_venezuela | 388 | 19 | 0.0490 | 0.0512 | 0.5498 | 0.0892 | 2 | 0.0052 | 0.0102 | 1.0954 | 1.2526 |
| france_ligue_2 | 612 | 30 | 0.0490 | 0.0508 | 0.5749 | 0.0876 | 11 | 0.0180 | 0.0189 | 1.1487 | 1.4118 |
| holland_eredivisie | 612 | 30 | 0.0490 | 0.0508 | 0.6243 | 0.0845 | 23 | 0.0376 | 0.0344 | 1.3856 | 1.6961 |
| primera_division_liga_mx | 612 | 30 | 0.0490 | 0.0508 | 0.5964 | 0.0862 | 14 | 0.0229 | 0.0228 | 1.3056 | 1.5278 |
| scottish_championship | 360 | 17 | 0.0472 | 0.0507 | 0.6081 | 0.0856 | 3 | 0.0083 | 0.0127 | 1.1778 | 1.2944 |
| chile_primera_division | 480 | 23 | 0.0479 | 0.0506 | 0.5580 | 0.0882 | 8 | 0.0167 | 0.0181 | 1.1417 | 1.5646 |
| austrian_bundesliga | 264 | 12 | 0.0455 | 0.0506 | 0.5773 | 0.0869 | 4 | 0.0152 | 0.0179 | 1.2235 | 1.5000 |
| greece_super_league_a | 364 | 17 | 0.0467 | 0.0505 | 0.5834 | 0.0866 | 3 | 0.0082 | 0.0126 | 1.1099 | 1.3599 |
| italy_serie_a | 760 | 37 | 0.0487 | 0.0505 | 0.5695 | 0.0876 | 6 | 0.0079 | 0.0104 | 1.0789 | 1.4145 |
| brazil_serie_b | 760 | 36 | 0.0474 | 0.0499 | 0.5152 | 0.0907 | 3 | 0.0039 | 0.0072 | 0.9921 | 1.2118 |
| czech_republic_gambrinus_liga | 480 | 22 | 0.0458 | 0.0499 | 0.6006 | 0.0848 | 9 | 0.0187 | 0.0197 | 1.2312 | 1.3729 |
| serbian_superliga | 480 | 22 | 0.0458 | 0.0499 | 0.6112 | 0.0842 | 13 | 0.0271 | 0.0259 | 1.2500 | 1.5000 |
| scottish_division_one | 360 | 16 | 0.0444 | 0.0499 | 0.6044 | 0.0847 | 3 | 0.0083 | 0.0127 | 1.1722 | 1.5000 |
| spanish_la_liga_2 | 924 | 44 | 0.0476 | 0.0498 | 0.5592 | 0.0874 | 13 | 0.0141 | 0.0153 | 1.1190 | 1.4621 |
| danish_1st_division | 264 | 11 | 0.0417 | 0.0497 | 0.6090 | 0.0844 | 4 | 0.0152 | 0.0179 | 1.2841 | 1.5076 |
| japan_j1_league | 380 | 16 | 0.0421 | 0.0490 | 0.5058 | 0.0887 | 9 | 0.0237 | 0.0233 | 1.0105 | 1.3868 |
| france_ligue_1 | 612 | 27 | 0.0441 | 0.0488 | 0.6154 | 0.0824 | 20 | 0.0327 | 0.0305 | 1.2647 | 1.6340 |
| slovak_super_liga | 264 | 10 | 0.0379 | 0.0488 | 0.5909 | 0.0841 | 2 | 0.0076 | 0.0132 | 1.2727 | 1.5455 |
| belgian_pro_league | 480 | 20 | 0.0417 | 0.0484 | 0.5975 | 0.0830 | 13 | 0.0271 | 0.0259 | 1.2271 | 1.4250 |
| liga_auf_uruguaya | 480 | 20 | 0.0417 | 0.0484 | 0.5368 | 0.0864 | 7 | 0.0146 | 0.0166 | 1.0188 | 1.3417 |
| swedish_allsvenskan | 480 | 20 | 0.0417 | 0.0484 | 0.5975 | 0.0830 | 19 | 0.0396 | 0.0353 | 1.2479 | 1.5917 |
| liga_de_expansion_mx | 420 | 17 | 0.0405 | 0.0483 | 0.6123 | 0.0822 | 11 | 0.0262 | 0.0251 | 1.3214 | 1.5952 |
| england_league_1 | 1104 | 50 | 0.0453 | 0.0483 | 0.5836 | 0.0834 | 19 | 0.0172 | 0.0179 | 1.1513 | 1.4565 |
| croatia_1.division | 360 | 14 | 0.0389 | 0.0482 | 0.5970 | 0.0830 | 3 | 0.0083 | 0.0127 | 1.2194 | 1.2889 |
| poland_ekstraklasa | 612 | 25 | 0.0408 | 0.0474 | 0.5888 | 0.0821 | 17 | 0.0278 | 0.0267 | 1.2827 | 1.4624 |
| scottish_division_two | 360 | 13 | 0.0361 | 0.0474 | 0.6044 | 0.0816 | 7 | 0.0194 | 0.0204 | 1.2750 | 1.4944 |
| england_league_2 | 1104 | 46 | 0.0417 | 0.0462 | 0.5563 | 0.0826 | 15 | 0.0136 | 0.0147 | 1.1178 | 1.4185 |
| romania_liga_i | 480 | 16 | 0.0333 | 0.0453 | 0.5687 | 0.0806 | 4 | 0.0083 | 0.0119 | 1.1250 | 1.3042 |
| italy_serie_b | 760 | 27 | 0.0355 | 0.0443 | 0.5663 | 0.0792 | 10 | 0.0132 | 0.0148 | 1.1474 | 1.3658 |
| liga_portugal_1 | 612 | 20 | 0.0327 | 0.0440 | 0.5825 | 0.0779 | 4 | 0.0065 | 0.0099 | 1.1797 | 1.4461 |
| brazil_serie_a | 760 | 26 | 0.0342 | 0.0436 | 0.5780 | 0.0776 | 6 | 0.0079 | 0.0104 | 1.1158 | 1.3684 |
| bulgaria_first_league | 480 | 13 | 0.0271 | 0.0431 | 0.5732 | 0.0774 | 5 | 0.0104 | 0.0134 | 1.0562 | 1.3208 |
| chinese_football_association_jia_league | 480 | 10 | 0.0208 | 0.0408 | 0.5292 | 0.0766 | 10 | 0.0208 | 0.0212 | 1.1271 | 1.4208 |

## Method

- **The card:** `notes/ANALYSIS/CLAUDE.md` §2, for each league (`analysis/card.py`). At the `PER_LEAGUE/` level, it splits by home team and away team, not by role.
- **A league value:** the sum of a count over the matches of the league, divided by the sum of another count, as in `../ALL/RATES.md`.
- **The test:** Cochran's Q over the 73 league values, one test for each value of the card (`analysis/units.py`, the method of `ODDS_YARDSTICK.md` of this folder). The variance of a league value is the one it would have if all leagues had the pooled value: a 0/1 outcome is a Bernoulli count, and the goals are a Poisson count. It is multiplied by the dispersion of the matches: 1.0000 for each 0/1 outcome, and 0.9436 to 0.9931 for the goals.
- **Shrinkage:** Empirical-Bayes normal shrinkage to the precision-weighted mean of the league values (`analysis/stats.py:shrink`).
- **At 80%** (`analysis/stats.py:detectable_tau`) and **the luck line** (2,000 Poisson draws of the count of each league, at the pooled value): as in `ODDS_YARDSTICK.md` of this folder.
- **League-seasons inside their league** (`analysis/units.py:within_test`): for each league, Cochran's Q of its two league-seasons around their own mean. The sum over the 71 leagues with two seasons, on 71 df. One test for all leagues, for the comeback rate, the 7+ rate and the goals per match.
- **Stages:** 5 leagues keep two stages, one after the other: the Apertura, then the Clausura. One league also has an Apertura-B of 24 matches, which counts with its Apertura. Each value has an interval over the 10 league-seasons of these leagues (`analysis/stats.py:observed_expected`).
- **Both seasons:** cohort 2024 holds the seasons 2024 and 2024-2025, and cohort 2025 holds 2025 and 2025-2026.

## Caveats

- **In the prices.** The differences between the leagues are differences that the opening prices know (the section above). Read the table as "where comebacks happen", not as "where comebacks are cheap".
- **The test is generous.** The variance takes the matches of a league as independent. Teams and league-seasons can make them dependent. Then Q is too large. So the tests that find a difference can be a little too strong, mostly the weaker ones: link 2, the home and away comebacks, and the season tests of C4 and C5.
- **The order of the comeback rates hardly repeats** (Spearman 0.1679). So the rank of a league in one season says little about its rank in the next. The shrunk values are the best guess for each league, but the leagues near the middle of the table are close to each other.
- **Two numbers of `ODDS_YARDSTICK.md` differ a little.** Its raw comeback test has Q 114.4848 on the 36,237 matches with odds. This doc uses all 36,238 matches (Q 114.4876). The match without odds is the awarded match (`ODDS_COVERAGE.md`, C2).
- **Link 1 follows the goals.** More goals in the first half give more half-times with a team behind. So C2's link 1 and C5 are partly one difference, seen two ways.
- **Small stages.** The stage slice has 5 leagues, and 1,226 and 1,202 matches. Its intervals are wide, so only a large difference between the stages would show.
- **Looks:** 13 tests across the leagues, 3 season tests and 6 stage values; 13 cohort correlations and 13 values at 80%; 2 luck lines. No league was tested on its own.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-19 | 144 league-seasons, 36,238 matches | first run |
