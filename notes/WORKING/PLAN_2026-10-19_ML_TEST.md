# PLAN — the ML test: comebacks beyond the odds

**Group: Working.** Edit it in place, and keep it current. Move done items to `notes/LOG/MIGRATIONS.md`.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

**Status: IN PROGRESS since 2026-10-19.** The user asked for a deeper analysis of the relations between the data and comebacks, "or ML - you decide". Claude chose an ML test first. The user: "we gotta try both schedule and schedule+detail".

**Result on the schedule fields (steps 1–4, done 2026-10-19):** model B does not beat model A. The schedule fields add no comeback information beyond the odds, for this method (`notes/ML/SCHEDULE/WHOLE_CORPUS/ALL/BEYOND_ODDS.md`). So step 7 does not run on the schedule fields. The next step is step 5, after the detail scrape.

## 1. The question

Do the pre-match fields hold information about a team's comeback beyond the odds? If they do not, a rule search on the same fields (`IDEAS_2026-10-01.md` idea 24) is very unlikely to find something. If they do, the test names the fields, and idea 24 turns them into rules that people can read.

## 2. Decisions (2026-10-19)

1. **The row:** one row for each side of a match: "this team is behind at half-time and wins". These are the 2/1 and 1/2 bets.
2. **Two models, with the same method:**
   - A: the odds only. These are the opening prices and the values that the odds yardstick makes from them (`analysis/methods/yardstick.py`).
   - B: the fields of A, plus every other pre-match field of the same sources.
   - The gain of B over A is the information beyond the odds. A alone is a comeback chance from the odds, with no Poisson assumption. The yardstick expects 24% too few comebacks (`notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ODDS_YARDSTICK.md` C2).
3. **The method:** gradient boosting (LightGBM, pinned). Its settings are tuned inside the training cohort only, with each league-season kept whole.
4. **The split:** fit on one season cohort, and score the other, both ways. Both cohorts were seen before, so each result is exploratory.
5. **The score:** the comebacks in the top N of each ranking (N = 100, 250, 500 and 1,000), with intervals over league-seasons. Then the log loss and the calibration. Not the AUC (`notes/ANALYSIS/CLAUDE.md` §6).
6. **The fields:** only fields with the timing `before` (`notes/FIELDS/`). The outcome columns are never fields. The team ids are not fields: a team trait does not repeat (`PER_TEAM/ODDS_YARDSTICK.md`), and 1,337 ids would let a model learn the teams of one cohort.
7. **If B gains:** SHAP values (LightGBM's own) name the fields that carry the gain. Then the non-ML steps of idea 24 run on those fields only.
8. **Code and docs:** a new package `ml/`, with the tree and the rules of `analysis/`. A runner prints, and Claude writes the doc in `notes/ML/` (the split of the user, 2026-10-16, IDEAS idea 24).
9. **Confirmation:** a claim from the test is tested only on seasons that are scraped later. A Record note declares them before their scrape (`notes/ANALYSIS/CLAUDE.md` §6, the holdout).
10. **No goal of the test cohort in a field** (the stats review, 2026-10-19). The yardstick's chances are fields of both models, and they use one first-half share. In each split, that share comes from the training cohort only (`split_rows` of the runner). The first run took it from all matches; its numbers were not kept.
11. **"B without league"** is a third model: B without the league. It was added after the first run, when the league was B's largest field. It checks that reading; it was not planned before the run.

## 3. Steps

| step | what | size |
|---|---|---|
| 1–4 | (done 2026-10-19; `notes/LOG/MIGRATIONS.md`) | — |
| 5 | after the detail scrape (IDEAS idea 2a): again, with the detail fields. A model A from the closing odds needs the closing O/U market too: candidate C5, added by the user on 2026-10-21 (Bet365 AH and O/U Live) | 0.5 day |
| 6 | after the live scrape (IDEAS idea 2b): again, with the live fields | 0.5 day |
| 7 | only if B gains: idea 24 on the fields that carry the gain | 10–12 days |

## 4. Done when

- Steps 1–4: done 2026-10-19.
- Steps 5 and 6: their docs give the answer when their data exist.
