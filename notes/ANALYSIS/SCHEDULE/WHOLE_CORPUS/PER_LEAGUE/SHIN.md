# SHIN — Shin's method per league

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/PER_LEAGUE`: 73 leagues, each with its seasons together.
- **Sources:** schedule stage 3. Inputs: the opening 1X2 prices (S1.16–18) and the proportional probabilities (S2.17–19). Outcome: the full-time goals (S1.14–15).
- **Corpus:** 2026-10-16: 144 league-seasons, 36,238 matches. 36,237 priced matches in 73 leagues.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.per_league.shin`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

Do the leagues differ in Shin's z? Do they differ in the log-loss gain of Shin's method over proportional removal (`../ALL/SHIN.md` C2)?

## Claims

| id | claim | number | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | The leagues differ in z | Cochran's Q 81529.1 on 72 df (p prints as 0); between-league sd 0.009245; shrunk league values 0.027859 to 0.057497, median 0.042479 | 73 leagues | yes: the league means of the two cohorts agree, Spearman 0.850 over 71 leagues | exploratory |
| C2 | There is no sign that the log-loss gain differs between leagues | Cochran's Q 85.1 on 72 df, p = 0.139; between-league sd 0.000464; shrunk gains 0.000228 to 0.001084, median 0.000636, all above 0 | 73 leagues | the league gains of the two cohorts hardly agree: Spearman 0.186 over 71 leagues | exploratory |

## Method

- **Per league:** the mean of each match's z, and the mean of its log-loss gain (`../ALL/SHIN.md`, Method). The variance of a mean is the variance over its matches, divided by their number.
- **One test for each quantity:** Cochran's Q, with a χ² distribution on 72 df. The between-league variance τ² comes from the method of moments (DerSimonian–Laird). The table gives τ as the between-league sd.
- **Pooled value:** the precision-weighted mean of the league means: 0.044378 for z, 0.000631 for the gain. It is not the mean over matches in `../ALL/SHIN.md`.
- **Shrinkage:** Empirical-Bayes normal shrinkage to the pooled value (`analysis/stats.py:shrink`). This is the continuous form of `notes/REFERENCE/STATS_PRIMER.md` §1. A league keeps the share τ² / (τ² + its variance) of its own distance from the pooled value.
- **Both seasons:** the Spearman correlation of the league means of the two season cohorts, over the 71 leagues with a season in each cohort. 2 leagues have one season only.

## Caveats

- **z follows the margin** (`../ALL/SHIN.md`, Caveats). So C1 says that Bet365's opening margin differs between leagues. It says nothing about football.
- **The tests are too generous.** The variance of a league mean treats its matches as independent. So Q is too large, and p is too small. C2 does not depend on this: a correction makes its p larger.
- **Raw league gains are noisy.** They go from −0.00332 to 0.00571. After shrinkage, all of them are above 0. Read the shrunk column, not the raw one.
- **Looks:** 2 tests and 2 correlations. No league was tested alone. The table is in the order of the league names, not of the values.

## League values

The league names are those of the stage files.

| league | matches | z | z shrunk | gain | gain shrunk |
|---|---|---|---|---|---|
| austrian_bundesliga | 264 | 0.03876 | 0.03878 | -0.00175 | 0.00042 |
| belgian_pro_league | 480 | 0.03765 | 0.03766 | -0.00017 | 0.00051 |
| brasileiro,_serie_c | 380 | 0.05052 | 0.05051 | 0.00112 | 0.00070 |
| brazil_serie_a | 760 | 0.03393 | 0.03394 | 0.00126 | 0.00082 |
| brazil_serie_b | 760 | 0.03729 | 0.03730 | 0.00048 | 0.00059 |
| bulgaria_first_league | 480 | 0.03595 | 0.03596 | -0.00112 | 0.00052 |
| chile_primera_division | 480 | 0.03806 | 0.03807 | 0.00132 | 0.00076 |
| chinese_football_association_jia_league | 480 | 0.05688 | 0.05688 | 0.00144 | 0.00069 |
| chinese_super_league | 480 | 0.03803 | 0.03804 | 0.00345 | 0.00099 |
| croatia_1.division | 360 | 0.04688 | 0.04687 | -0.00092 | 0.00054 |
| cyprus_1_division | 363 | 0.04449 | 0.04449 | 0.00366 | 0.00081 |
| czech_republic_gambrinus_liga | 480 | 0.04144 | 0.04144 | 0.00231 | 0.00080 |
| danish_1st_division | 264 | 0.04200 | 0.04201 | -0.00188 | 0.00054 |
| denmark_superliga | 264 | 0.03811 | 0.03812 | -0.00073 | 0.00052 |
| england_league_1 | 1104 | 0.03985 | 0.03986 | 0.00118 | 0.00083 |
| england_league_2 | 1104 | 0.03992 | 0.03992 | -0.00002 | 0.00040 |
| english_premier_league | 760 | 0.03431 | 0.03432 | -0.00063 | 0.00037 |
| estonia_champions_league | 360 | 0.05392 | 0.05391 | 0.00571 | 0.00083 |
| finland_veikkausliga | 264 | 0.04344 | 0.04344 | 0.00203 | 0.00073 |
| finland_ykkonen | 270 | 0.04797 | 0.04796 | -0.00068 | 0.00057 |
| france_ligue_1 | 612 | 0.03464 | 0.03464 | 0.00099 | 0.00069 |
| france_ligue_2 | 612 | 0.04558 | 0.04557 | -0.00018 | 0.00047 |
| german_3.liga | 760 | 0.04591 | 0.04591 | 0.00116 | 0.00077 |
| german_bundesliga | 612 | 0.03398 | 0.03399 | -0.00018 | 0.00054 |
| german_bundesliga_2 | 612 | 0.03788 | 0.03788 | 0.00001 | 0.00045 |
| greece_super_league_a | 364 | 0.02784 | 0.02786 | -0.00166 | 0.00046 |
| holland_eerste_divisie | 760 | 0.04248 | 0.04248 | -0.00033 | 0.00046 |
| holland_eredivisie | 612 | 0.03750 | 0.03751 | -0.00082 | 0.00051 |
| hungary_borsodi_liga | 396 | 0.04506 | 0.04506 | 0.00068 | 0.00064 |
| iceland_premier_division | 264 | 0.04690 | 0.04689 | 0.00037 | 0.00062 |
| ireland_first_division | 360 | 0.04724 | 0.04724 | 0.00056 | 0.00062 |
| ireland_premier_division | 360 | 0.04188 | 0.04189 | -0.00036 | 0.00050 |
| italy_serie_a | 760 | 0.03324 | 0.03325 | 0.00090 | 0.00069 |
| italy_serie_b | 760 | 0.04040 | 0.04040 | 0.00138 | 0.00090 |
| j2_league | 380 | 0.03932 | 0.03932 | 0.00077 | 0.00067 |
| j3_league | 760 | 0.05617 | 0.05617 | 0.00084 | 0.00068 |
| japan_j1_league | 380 | 0.03379 | 0.03380 | 0.00126 | 0.00082 |
| k_league_1 | 396 | 0.03700 | 0.03702 | 0.00019 | 0.00050 |
| liga_auf_uruguaya | 480 | 0.03927 | 0.03927 | 0.00115 | 0.00072 |
| liga_de_expansion_mx | 420 | 0.04670 | 0.04669 | 0.00288 | 0.00089 |
| liga_portugal_1 | 612 | 0.03687 | 0.03688 | 0.00218 | 0.00083 |
| liga_portugal_2 | 612 | 0.04820 | 0.04819 | -0.00089 | 0.00024 |
| national_premier_leagues_western_australia | 264 | 0.05723 | 0.05723 | 0.00219 | 0.00071 |
| northern_ireland_premier_league | 396 | 0.04921 | 0.04921 | 0.00087 | 0.00065 |
| norway_eliteserien | 480 | 0.03633 | 0.03634 | 0.00080 | 0.00065 |
| nsw_premier_league | 480 | 0.05745 | 0.05744 | 0.00138 | 0.00068 |
| poland_ekstraklasa | 612 | 0.03902 | 0.03902 | -0.00028 | 0.00040 |
| poland_liga_1 | 612 | 0.04907 | 0.04906 | 0.00007 | 0.00053 |
| primera_division_de_paraguay | 528 | 0.04258 | 0.04258 | -0.00168 | 0.00023 |
| primera_division_de_venezuela | 388 | 0.05073 | 0.05072 | 0.00208 | 0.00083 |
| primera_division_liga_mx | 612 | 0.03698 | 0.03698 | 0.00071 | 0.00064 |
| qatar_stars_league | 264 | 0.05197 | 0.05195 | -0.00171 | 0.00057 |
| romania_liga_i | 480 | 0.04461 | 0.04461 | 0.00104 | 0.00069 |
| saudi_professional_league | 612 | 0.04707 | 0.04706 | 0.00470 | 0.00108 |
| scottish_championship | 360 | 0.04947 | 0.04946 | -0.00130 | 0.00044 |
| scottish_division_one | 360 | 0.05157 | 0.05156 | -0.00028 | 0.00052 |
| scottish_division_two | 360 | 0.05298 | 0.05297 | -0.00212 | 0.00038 |
| scottish_premiership | 396 | 0.03773 | 0.03774 | -0.00074 | 0.00054 |
| serbian_superliga | 480 | 0.04773 | 0.04773 | -0.00004 | 0.00059 |
| slovak_super_liga | 264 | 0.04441 | 0.04441 | -0.00051 | 0.00057 |
| spanish_la_liga | 760 | 0.03454 | 0.03454 | 0.00151 | 0.00082 |
| spanish_la_liga_2 | 924 | 0.04144 | 0.04144 | 0.00105 | 0.00076 |
| sweden_superettan | 480 | 0.04032 | 0.04033 | 0.00008 | 0.00052 |
| swedish_allsvenskan | 480 | 0.03596 | 0.03597 | 0.00051 | 0.00061 |
| switzerland_challenge_league | 360 | 0.04444 | 0.04444 | 0.00140 | 0.00073 |
| switzerland_super_league | 396 | 0.04066 | 0.04066 | -0.00093 | 0.00041 |
| thai_league_1 | 480 | 0.05450 | 0.05449 | 0.00121 | 0.00068 |
| turkey_super_lig | 648 | 0.04117 | 0.04118 | 0.00298 | 0.00096 |
| uae_pro-league | 364 | 0.05719 | 0.05718 | 0.00193 | 0.00069 |
| v.league_1 | 364 | 0.05687 | 0.05686 | 0.00123 | 0.00067 |
| vic_premier_league | 364 | 0.05743 | 0.05742 | 0.00325 | 0.00074 |
| victorian_state_league_division_1 | 364 | 0.05750 | 0.05750 | -0.00080 | 0.00056 |
| welsh_premier_league | 264 | 0.05178 | 0.05176 | -0.00332 | 0.00055 |
