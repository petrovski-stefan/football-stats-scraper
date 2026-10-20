# PREMATCH_SCREEN — pre-match fields beyond the odds, for a team's comeback

**Group: Analysis.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches together, two rows for each match (one for each team).
- **Sources:** schedule stage 3. Inputs, all known before kickoff: the opening prices (S1.16–24) and the market fields S2.24–25, through the odds yardstick (`ALL/ODDS_YARDSTICK.md`) too; the standings before kickoff (S3.03), the HT/FT counts (S3.08), the matches left (S3.11), the round so far (S3.14–20); the stage, round and kickoff (S1.04, S1.05, S1.07) and the team ids (S1.08–09). Outcomes: the half-time and full-time goals (S1.12–15). Units: the league-season (S1.02, S1.01), for the clusters. The season (S1.01) also gives the season cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 36,237 have both opening markets: 72,474 team rows. 60,288 rows have both teams with 5 or more matches played in the stage, with 1,598 comebacks. This doc uses them.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.prematch_screen`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

Does any field known before kickoff tell more than the odds about whether a team comes back? Each field is tried alone on top of a baseline from the odds. Then all fields together are tried out of sample, one season cohort against the other.

## Claims

The odds ratio (OR) is per standard deviation of the field, or per 1 for a 0/1 field. Each interval and p is clustered by league-season.

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | No field adds to the odds for a team's comeback after the Holm correction | the smallest p is 0.0245: `rec_T_cb_rate`, OR 0.9451 [0.8997, 0.9928], Holm p 0.7592. The next is 0.0983. Every other p is 0.1165 or more | 60,288 rows, 1,598 comebacks, 31 fields | no field has p below 0.05 in both cohorts. 4 have it in 2025 only: `rec_T_cb_rate` (0.0077), `mk_draw_resid` (0.0081), `rec_T_compl` (0.0237), `mk_ah_resid` (0.0269) | exploratory |
| C2 | The newer fields add nothing either: the round so far, and last season | `rnd_cb_share` OR 0.9899, p 0.7425. `rnd_goal_excess` 0.9964, p 0.8947. `prev_T_cb_rate` p 0.7404, `prev_O_blown` p 0.9748, `prev_league_oe` p 0.8770 | 40,100 rows (round so far); 26,786 and 29,460 (last season, 2025 only) | round so far: p 0.7600 and 0.4904 (`rnd_cb_share`), 0.3286 and 0.2941 (`rnd_goal_excess`) | exploratory |
| C3 | Out of sample, all fields together make the forecast worse than the odds baseline, in both directions | fit on 2024, scored on 2025: log loss 0.1206 against 0.1203, AUC 0.5963 against 0.6020. Fit on 2025, scored on 2024: 0.1215 against 0.1209, AUC 0.5923 against 0.6052 | 29,512 and 30,776 rows | is the test | exploratory |
| C4 | The odds put more comebacks into a small top set than chance does. The fields do not add to it | top 1,000 by the yardstick: 45 and 39 comebacks, against 26.4 and 26.6 by chance. By the baseline: 42 and 43. By the baseline and all fields: 46 and 32 | 30,776 and 29,512 scored rows | yes in both directions | exploratory |

## Each field alone

Sorted by the comeback p. Link 1 is "the team is behind at half-time" on all rows. Link 2 is "the team wins" on the rows where it is behind at half-time. The link p values have no correction.

| field | family | OR [95% interval] | p | Holm | OR 2024 (p) | OR 2025 (p) | link 1 OR (p) | link 2 OR (p) |
|---|---|---|---|---|---|---|---|---|
| rec_T_cb_rate | htft record | 0.9451 [0.8997, 0.9928] | 0.0245 | 0.7592 | 0.9840 (0.6276) | 0.9062 (0.0077) | 0.9847 (0.0918) | 0.9558 (0.0781) |
| rec_T_compl | htft record | 0.9551 [0.9044, 1.0086] | 0.0983 | 1.0 | 0.9972 (0.9415) | 0.9142 (0.0237) | 0.9819 (0.0621) | 0.9696 (0.2671) |
| mk_draw_resid | market | 0.9538 [0.8991, 1.0118] | 0.1165 | 1.0 | 1.0085 (0.8570) | 0.9067 (0.0081) | 0.9613 (0.0018) | 0.9356 (0.1111) |
| hp_T_2h_share_for | halves | 1.0349 [0.9874, 1.0848] | 0.1525 | 1.0 | 1.0427 (0.2183) | 1.0280 (0.4211) | 1.0017 (0.8469) | 1.0336 (0.2229) |
| hp_T_2h_gd | halves | 1.0359 [0.9834, 1.0912] | 0.1835 | 1.0 | 1.0528 (0.1838) | 1.0191 (0.6075) | 1.0048 (0.6255) | 1.0278 (0.3354) |
| mk_margin | market | 1.0338 [0.9835, 1.0865] | 0.1912 | 1.0 | 1.0329 (0.4082) | 1.0376 (0.2284) | 1.0011 (0.8901) | 1.0357 (0.2190) |
| mk_ah_resid | market | 1.0398 [0.9805, 1.1028] | 0.1930 | 1.0 | 0.9722 (0.4304) | 1.1050 (0.0269) | 0.9991 (0.9455) | 1.0452 (0.2010) |
| hp_O_2h_gd_venue | halves | 1.0313 [0.9811, 1.0841] | 0.2257 | 1.0 | 1.0419 (0.2269) | 1.0215 (0.5736) | 1.0153 (0.1109) | 1.0209 (0.4649) |
| mk_ah_tilt | market | 0.9725 [0.9235, 1.0241] | 0.2900 | 1.0 | 1.0060 (0.8632) | 0.9416 (0.1240) | 0.9891 (0.2990) | 0.9756 (0.3931) |
| tb_ppg_diff | table | 1.0434 [0.9610, 1.1329] | 0.3114 | 1.0 | 1.0512 (0.3889) | 1.0356 (0.5621) | 1.0154 (0.3873) | 1.0364 (0.4104) |
| hp_O_2h_gd | halves | 1.0257 [0.9712, 1.0832] | 0.3629 | 1.0 | 1.0322 (0.3829) | 1.0195 (0.6489) | 1.0022 (0.8190) | 1.0285 (0.3725) |
| hp_T_2h_gd_venue | halves | 1.0248 [0.9714, 1.0811] | 0.3695 | 1.0 | 1.0621 (0.0968) | 0.9877 (0.7599) | 0.9977 (0.8093) | 1.0227 (0.4114) |
| cal_midweek | calendar | 1.0606 [0.9173, 1.2263] | 0.4271 | 1.0 | 1.1381 (0.2219) | 0.9795 (0.8416) | 0.9697 (0.1930) | 1.1300 (0.1317) |
| cal_last_ko | calendar | 1.0426 [0.9182, 1.1839] | 0.5200 | 1.0 | 1.0250 (0.7847) | 1.0601 (0.5316) | 0.9971 (0.8894) | 0.9959 (0.9531) |
| rec_O_blown | htft record | 0.9871 [0.9402, 1.0364] | 0.6022 | 1.0 | 0.9556 (0.2135) | 1.0153 (0.6527) | 0.9821 (0.0676) | 0.9969 (0.9036) |
| tb_goal_env | table | 0.9797 [0.9066, 1.0587] | 0.6038 | 1.0 | 0.9940 (0.9196) | 0.9645 (0.4952) | 1.0133 (0.2752) | 0.9590 (0.3336) |
| rec_O_not_won | htft record | 0.9869 [0.9367, 1.0398] | 0.6203 | 1.0 | 0.9665 (0.3819) | 1.0062 (0.8625) | 1.0047 (0.6230) | 0.9832 (0.5468) |
| hp_T_1h_gd | halves | 0.9899 [0.9362, 1.0467] | 0.7218 | 1.0 | 0.9862 (0.7563) | 0.9929 (0.8427) | 1.0005 (0.9591) | 0.9879 (0.6883) |
| prev_T_cb_rate | last season | 0.9854 [0.9030, 1.0752] | 0.7404 | 1.0 | — | 0.9854 (0.7404) | 1.0072 (0.5650) | 0.9632 (0.4227) |
| rnd_cb_share | round so far | 0.9899 [0.9319, 1.0515] | 0.7425 | 1.0 | 1.0123 (0.7600) | 0.9681 (0.4904) | 0.9915 (0.3176) | 0.9909 (0.7831) |
| mk_ou_tilt | market | 1.0083 [0.9572, 1.0621] | 0.7561 | 1.0 | 1.0616 (0.1146) | 0.9631 (0.2905) | 0.9944 (0.4129) | 1.0150 (0.5882) |
| rec_T_trail_rate | htft record | 0.9921 [0.9370, 1.0504] | 0.7850 | 1.0 | 0.9924 (0.8622) | 0.9924 (0.8448) | 1.0065 (0.5203) | 0.9882 (0.7146) |
| prev_league_oe | last season | 1.0044 [0.9505, 1.0613] | 0.8770 | 1.0 | — | 1.0044 (0.8770) | 0.9933 (0.5871) | 1.0033 (0.9162) |
| rnd_goal_excess | round so far | 0.9964 [0.9439, 1.0517] | 0.8947 | 1.0 | 1.0366 (0.3286) | 0.9585 (0.2941) | 1.0021 (0.8092) | 1.0016 (0.9581) |
| ss_progress | season | 1.0031 [0.9527, 1.0562] | 0.9061 | 1.0 | 1.0216 (0.5891) | 0.9864 (0.6988) | 0.9940 (0.4209) | 1.0135 (0.6370) |
| ss_dead_rubber | season | 0.9929 [0.7841, 1.2572] | 0.9527 | 1.0 | 1.0534 (0.7668) | 0.9357 (0.6837) | 1.0099 (0.7854) | 0.9869 (0.9176) |
| rec_O_lead_rate | htft record | 1.0015 [0.9463, 1.0599] | 0.9578 | 1.0 | 0.9682 (0.4162) | 1.0348 (0.4150) | 1.0040 (0.6592) | 0.9924 (0.8071) |
| tb_gd_diff | table | 1.0016 [0.9239, 1.0859] | 0.9683 | 1.0 | 1.0276 (0.6581) | 0.9780 (0.6977) | 1.0015 (0.9361) | 0.9921 (0.8558) |
| prev_O_blown | last season | 0.9986 [0.9173, 1.0872] | 0.9748 | 1.0 | — | 0.9986 (0.9748) | 0.9915 (0.6034) | 0.9997 (0.9942) |
| hp_O_2h_share_against | halves | 0.9994 [0.9493, 1.0522] | 0.9822 | 1.0 | 0.9850 (0.6726) | 1.0133 (0.7283) | 1.0104 (0.2530) | 0.9950 (0.8505) |
| hp_O_1h_gd | halves | 0.9995 [0.9474, 1.0544] | 0.9844 | 1.0 | 0.9825 (0.6348) | 1.0166 (0.6835) | 1.0019 (0.8334) | 0.9970 (0.9179) |

## Out of sample

| fit on → scored on | model | log loss | AUC | top 100 | top 250 | top 500 | top 1,000 |
|---|---|---|---|---|---|---|---|
| 2024 → 2025 (813 comebacks) | chance | 0.1221 | 0.5000 | 2.6 | 6.6 | 13.2 | 26.4 |
| | yardstick | 0.1209 | 0.6018 | 7 | 12 | 20 | 45 |
| | baseline | 0.1203 | 0.6020 | 6 | 11 | 18 | 42 |
| | baseline + all fields | 0.1206 | 0.5963 | 6 | 10 | 23 | 46 |
| 2025 → 2024 (785 comebacks) | chance | 0.1227 | 0.5000 | 2.7 | 6.6 | 13.3 | 26.6 |
| | yardstick | 0.1216 | 0.6059 | 5 | 8 | 17 | 39 |
| | baseline | 0.1209 | 0.6052 | 3 | 8 | 15 | 43 |
| | baseline + all fields | 0.1215 | 0.5923 | 1 | 3 | 12 | 32 |

"Chance" gives every row the training rate. Its top-N column is the count that chance expects.

## Method

- **Rows.** Two rows for each match with both opening markets, one for each team (`analysis/card.py:team_rows`). T is the team of the row, O its opponent. A row counts when both teams have played 5 or more matches of the stage (S3.03), so that the season fields mean something.
- **Targets.** The comeback: T is behind at half-time and wins. Link 1: T is behind at half-time. Link 2: T wins, on the rows where it is behind.
- **The baseline.** A logistic regression on: the log odds of the yardstick's chance of the target (T's comeback chance; T's chance to be behind at half-time; the ratio of the two for link 2), the log odds of T's Shin win chance and its square, the log of the expected goals of the match, and T's venue.
- **One field alone.** The field is added to the baseline, in standard deviations (a 0/1 field as it is). The OR, its interval and the Wald p use a covariance clustered by league-season (`statsmodels` 0.15.0). The two rows of one match are in the same cluster (`notes/ANALYSIS/CLAUDE.md` §5, rules 5 and 7). Holm runs over the 31 comeback tests.
- **The fields** (31, in 8 families). Per match played means divided by the matches played in the stage before kickoff.
  - market: `mk_margin` the 1X2 overround; `mk_ah_resid` T's AH line against the yardstick's expected goal margin for T; `mk_ah_tilt` and `mk_ou_tilt` the AH chance of T (S2.25) and the over chance (S2.24) away from 0.5; `mk_draw_resid` the Shin draw chance against the yardstick's draw chance;
  - table: `tb_ppg_diff` and `tb_gd_diff` points and goal difference per match played, T against O; `tb_goal_env` the goals for and against per match played, both teams together;
  - halves: `hp_T_1h_gd`, `hp_T_2h_gd`, `hp_O_1h_gd`, `hp_O_2h_gd` each team's goal difference per match played in each half; `hp_T_2h_share_for` the second half's share of T's goals; `hp_O_2h_share_against` the second half's share of the goals against O; `hp_T_2h_gd_venue`, `hp_O_2h_gd_venue` each team's second-half goal difference per match at its venue of this match;
  - htft record (S3.08): `rec_T_trail_rate` and `rec_T_cb_rate` how often T was behind at half-time, and came back, per match played; `rec_T_compl` T's comebacks over its half-times behind; `rec_O_lead_rate` how often O led at half-time; `rec_O_blown` O's lost leads over its leads; `rec_O_not_won` O's leads not won. The ratios are shrunk with 10 pseudo-counts at 0.083 (comebacks, lost leads) and 0.26 (leads not won), the priors of the old run of 2026-10-09;
  - season: `ss_progress` T's share of the stage played, from S3.11; `ss_dead_rubber` 0.8 of the stage played or more, with both teams' rank shares between 0.3 and 0.7;
  - calendar: `cal_midweek` a kickoff from Tuesday to Thursday, Berlin time; `cal_last_ko` the last kickoff of a round with more than one kickoff time;
  - round so far: `rnd_cb_share` S3.15 over S3.14 (empty before a round-mate finished); `rnd_goal_excess` S3.19 − S3.20;
  - last season (2025 cohort only): `prev_T_cb_rate` T's comeback rate in the 2024 cohort, shrunk with 40 pseudo-matches at that cohort's rate; `prev_O_blown` O's lost leads over its leads in 2024, shrunk as above; `prev_league_oe` the league's comebacks against the yardstick in 2024.
- **Out of sample.** Fit on one cohort, score the other, in both directions. The joint model is the baseline plus every field except last season's (one cohort only) and `tb_gd_diff` (the sum of the four half fields, so the fit has no unique solution), unpenalised. An empty value takes the training median; each field is scaled with the training rows. In each split, the yardstick's chances (in the baseline and in the yardstick row) use the first-half share of the training cohort only: 0.4482 (2024) and 0.4460 (2025). So no goal of the test cohort reaches the baseline or a field. The screen of each field alone fits on all rows, so it keeps the share of all matches (0.4471, `ALL/ODDS_YARDSTICK.md` C9). The scores: the mean log loss, the AUC (as the Mann–Whitney statistic), and the comebacks among the 100, 250, 500 and 1,000 rows with the highest chance (`notes/ANALYSIS/CLAUDE.md` §6, the candidate protocol).
- **Changed from the old run** (`b1_screen.py` and `b2_oos.py`, 2026-10-09): Shin win chances in place of proportional ones; the yardstick of `analysis/methods/yardstick.py`; `ss_progress` from S3.11; `cal_midweek` from the kickoff in Berlin time (the stage-2 weekday field was dropped on 2026-10-11); intervals clustered by league-season in place of a likelihood-ratio test; the new family "round so far". The boosted trees of `b2_oos.py` are machine learning, so they are not here (`analysis/CLAUDE.md` §1).
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025. 2025 holds 2025 and 2025-2026.

## Caveats

- **Looks:** 31 fields × 5 tests (all rows, 2 cohorts, 2 links), less the 3 last-season fields in 2024: 152 tests, and 8 scored models. Holm covers only the 31 comeback tests. The smallest link p (`mk_draw_resid`, link 1, 0.0018) is one of 62 link tests with no correction.
- **Shared data.** The market fields come from the same prices as the baseline. They ask if the shape of the prices tells more than the yardstick reads from them.
- **The early rounds are out.** Only 60,288 of the 72,474 rows have both teams with 5 or more matches played.
- **Link 2's baseline** uses the pre-match completion chance, not the half-time score. A field that tells the size of the deficit can show up in link 2.
- **The yardstick's known errors** (`ALL/ODDS_YARDSTICK.md`, C6: more comeback excess at low expected goals) are partly in the baseline through the expected goals. A field that follows the goal level could pick up the rest. None does here.
- **The priors** of the HT/FT record and last-season fields were set by the old run and are not tuned here.
- **Midweek in Berlin time.** For leagues far from Europe, the local weekday can differ.
- **Not a holdout.** Both cohorts were seen. The old run asked the same on the corpus of 2026-10-09.
