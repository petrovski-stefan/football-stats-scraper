# BEYOND_ODDS — the ML test on the schedule fields, all matches

**Group: ML.** Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all priced matches, two rows for each match (one for each side).
- **Sources:** schedule stage 3. Inputs of model A: the opening prices (S1.16–24), through S2.24–25 and the odds yardstick (`notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ODDS_YARDSTICK.md`), and the venue. Model B adds every other field with the timing `before` and the role `input`: the tables before kickoff (S3.03–04), the HT/FT records (S3.08), the stakes (S3.11–13), the round so far (S3.01, S3.14–20), the league (S1.02), the round (S1.05) and the kickoff (S1.07). The team ids are not fields. Outcome: the half-time and full-time goals (S1.12–15). Units: the league-season (S1.02, S1.01), for the folds and the intervals. The season (S1.01) gives the season cohort.
- **Models:** A: the odds (14 fields). B: the odds and every other field (198). B without league (197). Gradient boosting (LightGBM), tuned inside the training cohort over folds of whole league-seasons.
- **Split and score:** fit on one season cohort, score the other, both ways. The comebacks in the top N, the log loss and the calibration, each with intervals over the league-seasons of the test cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. The 36,237 matches with both opening markets give 72,474 side rows and 1,891 comebacks (0.0261 of the rows).
- **Code:** `uv run python -m ml.schedule.whole_corpus.all.beyond_odds`, at the commit that adds this doc. Plan: `notes/WORKING/PLAN_2026-10-19_ML_TEST.md`.
- **Kind:** empirical.

## Question

Is a team's comeback related to any pre-match field of the schedule, beyond the odds? Model A sees the odds only. Model B sees them and every other field. If B does not beat A on the cohort that it did not see, the schedule fields hold no comeback information beyond the odds, for this method.

## Claims

"Fit on 2024" scores the 2025 cohort; "fit on 2025" scores the 2024 cohort. A log-loss difference above 0 means worse than A. Each interval is 95%, over 2,000 resamples of the league-seasons of the test cohort.

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | The schedule fields add no comeback information beyond the odds. Model B is never better than model A | log loss B − A: +0.0008 [0.0004, 0.0013] (fit on 2024), +0.0004 [−0.0000, 0.0007] (fit on 2025). In the top N (100 to 1,000), every interval of B − A holds 0 | 36,962 and 35,512 test rows; 975 and 916 comebacks | yes: no gain in either direction. Worse with a clear interval after the fit on 2024 only | exploratory |
| C2 | Without the league, the other 183 fields add nothing either | log loss: +0.0003 [0.0001, 0.0005] (fit on 2024), +0.0001 [−0.0001, 0.0003] (fit on 2025). Top N: two differences below 0, after the fit on 2024 (N = 100: −0.0400 [−0.0833, −0.0095]; N = 250: −0.0320 [−0.0671, −0.0006]); every other interval holds 0 | same | yes: no interval puts it above A | exploratory |
| C3 | A flexible model of the odds is no better than the yardstick times one number | log loss of the yardstick, scaled by its O/E in the training cohort, − A: −0.0001 [−0.0003, 0.0001] (fit on 2024), −0.0003 [−0.0005, 0.0000] (fit on 2025) | same | yes | exploratory |
| C4 | The odds carry comeback information: model A beats the base rate | log loss of the base rate − A: +0.0017 [0.0011, 0.0024] (fit on 2024), +0.0016 [0.0011, 0.0022] (fit on 2025). Top 1,000 of A: 41 comebacks against 26.4 by chance (fit on 2024), 48 against 25.8 (fit on 2025) | same | yes | exploratory |
| C5 | Model A is calibrated as a whole on the other cohort | O/E 1.0127 (fit on 2024) and 0.9895 (fit on 2025). By tenth of A's chance: O/E from 0.8442 to 1.1452, and from 0.7675 to 1.1845 | same | yes | exploratory |

## Log loss

The base rate is the comeback rate of the training cohort. The yardstick is its comeback chance, times its O/E in the training cohort.

| model | fit on 2024: log loss | O/E | − A [95% interval] | fit on 2025: log loss | O/E | − A [95% interval] |
|---|---|---|---|---|---|---|
| base rate | 0.1219 | 1.0227 | +0.0017 [0.0011, 0.0024] | 0.1198 | 0.9778 | +0.0016 [0.0011, 0.0022] |
| yardstick | 0.1201 | 1.0174 | −0.0001 [−0.0003, 0.0001] | 0.1179 | 0.9829 | −0.0003 [−0.0005, 0.0000] |
| A | 0.1202 | 1.0127 | 0 | 0.1182 | 0.9895 | 0 |
| B | 0.1210 | 1.0153 | +0.0008 [0.0004, 0.0013] | 0.1185 | 0.9773 | +0.0004 [−0.0000, 0.0007] |
| B without league | 0.1205 | 1.0184 | +0.0003 [0.0001, 0.0005] | 0.1183 | 0.9805 | +0.0001 [−0.0001, 0.0003] |

## Comebacks in the top N

Each cell: the comebacks in the top N of the ranking. "Chance" is N times the comeback rate of the test cohort.

| N | chance | yardstick | A | B | B without league |
|---|---|---|---|---|---|
| fit on 2024: 100 | 2.6 | 7 | 4 | 3 | 0 |
| 250 | 6.6 | 13 | 13 | 9 | 5 |
| 500 | 13.2 | 19 | 22 | 19 | 16 |
| 1,000 | 26.4 | 44 | 41 | 38 | 40 |
| fit on 2025: 100 | 2.6 | 5 | 4 | 4 | 4 |
| 250 | 6.4 | 7 | 12 | 8 | 13 |
| 500 | 12.9 | 19 | 20 | 19 | 19 |
| 1,000 | 25.8 | 38 | 48 | 35 | 38 |

The differences in the share against A, with intervals, are in the runner's output. Only two intervals are clear of 0, and both are below 0 (C2).

## The chosen settings

Each model chose 4 leaves and 300 rows. The chosen settings stopped after 54 to 146 trees, at a learning rate of 0.03.

| model | fit on 2024: fields for each tree | trees | cv log loss | fit on 2025: fields for each tree | trees | cv log loss |
|---|---|---|---|---|---|---|
| A | 0.5 | 91 | 0.1180 | 0.5 | 146 | 0.1205 |
| B | all | 65 | 0.1184 | 0.5 | 54 | 0.1207 |
| B without league | all | 82 | 0.1182 | 0.5 | 72 | 0.1207 |

"Rows" is the smallest number of rows in a leaf. Inside the training cohort, B's cross-validated log loss was already above A's in each direction.

## What model B reads

The mean absolute SHAP value of each field, on the test cohort, as a share of the total. These shares describe model B. They are not findings, because B does not beat A (`notes/ML/CLAUDE.md` §2, rule 3). The fields with the largest shares:

| fit on 2024: B | share | fit on 2025: B | share |
|---|---|---|---|
| league_id | 0.3234 | league_id | 0.2357 |
| m_cb_T (odds) | 0.1979 | m_cb_T (odds) | 0.2237 |
| lam_T (odds) | 0.1511 | lam_T (odds) | 0.0997 |
| ah_line_T (odds) | 0.1468 | p_T (odds) | 0.0954 |
| p_O (odds) | 0.0357 | p_O (odds) | 0.0830 |
| T_2h_away_goal_diff_pg | 0.0327 | m_behind_T (odds) | 0.0688 |

All the fields that are not odds fields hold 0.4685 (fit on 2024) and 0.3744 (fit on 2025) of B's total. Without the league, they hold 0.4010 and 0.2913. Their order changes between the two directions: the first is `O_ht_away_lost_pg` (0.0643) after the fit on 2024, and `T_ft_away_points_pg` (0.0267) after the fit on 2025.

## Method

- **The rows** (`ml/rows.py`): two rows for each priced match, one for each side. The target: the side is behind at half-time and wins.
- **Model A's fields:** the venue; the Shin chances of the side, the draw and the opponent; the yardstick's two goal rates; the O/U line and its over chance; the AH line and chance from the side's view; the 1X2 margin; the yardstick's comeback chance of each side and its chance that the side is behind at half-time.
- **The yardstick in each split:** its chances use one first-half share. In each split, that share comes from the training cohort only: 0.4482 (2024) and 0.4460 (2025). So no goal of the test cohort reaches a field. A test checks this (`tests/ml/schedule/whole_corpus/all/test_beyond_odds.py`).
- **Model B's other fields:** for the side and for its opponent, each table before kickoff (FT and HT, total, home and away) as rates per match played, with the rank and the matches played; the second-half goals and goal difference per match (FT minus HT); the HT/FT record as shares of the matches played; the stakes. For the match: the round so far, the gap between the ranks, the round, the weekday, hour and month of the kickoff in Berlin time, and the league as a category. 0.0384 of B's values are empty, mostly before a side's first match of the stage.
- **Tuning** (`ml/boosting.py`): 12 settings (4, 8 or 16 leaves; 300 or 1,000 rows in a leaf; 0.5 or all of the fields for each tree), each with early stopping after 100 trees with no gain, over 4 folds of whole league-seasons of the training cohort. The setting with the lowest log loss is trained on the whole training cohort. The test cohort chooses nothing.
- **Scores** (`ml/score.py`): the top N are the rows with the highest chance. A resample of the league-seasons of the test cohort keeps the rows that the full test cohort put in the top N.
- **SHAP values:** LightGBM's own TreeSHAP, on the test cohort.
- **Season cohorts:** 2024 holds the seasons 2024 and 2024-2025 (35,512 rows, 916 comebacks). 2025 holds 2025 and 2025-2026 (36,962 rows, 975).

## Caveats

- **Both cohorts were seen before.** Other docs read their comebacks. So each claim is exploratory. A test needs seasons that are scraped later (`notes/ANALYSIS/CLAUDE.md` §6).
- **"B without league" was added after the first run.** The first run showed the league as B's largest field, and this model checks that reading. It was not planned before any score was printed (the plan, decision 11). The first run also took the yardstick's share from all matches, and the stats review found that leak; the numbers here are from the run after the fix.
- **These fields were Dead before.** Model B holds schedule versions of three feature families that `notes/WORKING/STATE.md` lists as Dead (`notes/RECORD/RESULTS.md` §1): family A, the half-time state (for example `*_ht_*_lost_pg`, `*_ht_*_goal_diff_pg`); family B, second-half supremacy (`*_2h_*_goal_diff_pg`, `*_htft_*_w_l_pg`); family F, venue splits (`*_ft_home_points_pg`, `*_ft_away_points_pg`). C1 and C2 agree with those verdicts, on 36,237 matches; the old tests had 1,182.
- **"No gain" has a size.** The intervals of the log-loss differences with A are 0.0004 to 0.0009 wide. The odds themselves gain 0.0017 and 0.0016 over the base rate (C4). A field set with a much smaller gain than that can exist, and this test does not see it.
- **For this method.** Boosted trees learn interactions, but a small, rare pattern can stay below the tuned trees of 4 leaves. The rule search of idea 24 looks at such patterns. With no gain here, it is not run on the schedule fields (the plan, decision 7).
- **The top N is noisy.** At N = 100, the counts are 0 to 7 comebacks.
- **C3 is out of sample.** In sample, the comeback excess is larger at low expected goals (`ODDS_YARDSTICK.md` C6). A flexible model of the odds does not turn this into a better log loss on the other cohort. After the fit on 2025, the scaled yardstick is a little ahead of A, and the upper end of that interval is 0.0000 at four decimals.
- **The two rows of a match are not independent.** Only one side can come back. The intervals resample league-seasons, which keeps both rows of a match together.
- **Opening odds only.** The closing odds come with the detail page (plan step 5).
- **Looks:** 2 splits × (4 log-loss differences + 3 differences in each of 4 top-N tables) = 32 comparisons with A. 6 intervals are clear of 0, and each one favours A: the base rate 2, B 1, B without league 3. No interval favours a model over A.
- **Not profit.** The value of a comeback bet needs the HT/FT prices, and nowgoal does not show them.
