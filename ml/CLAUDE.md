# ml/ — machine learning on the finished corpus

Imports `domain`, `features` and `analysis`. Nothing imports `ml`.

## 1. What counts as ML

The user's line (2026-10-16, `notes/WORKING/IDEAS_2026-10-01.md` idea 24): a method is ML when it needs a fitted predictive model whose settings are tuned on the data. Those methods live here; every other method lives in `analysis/` (`analysis/CLAUDE.md` §1).

- **Now:** gradient boosting (LightGBM) for the ML test, `notes/WORKING/PLAN_2026-10-19_ML_TEST.md`: model A reads the odds only, model B the odds and every other pre-match field.
- **Later:** the ML steps of idea 24 (sparse interaction selection, tree subgroups, H-statistics, partial dependence, nested resampling) and idea 9.

## 2. Runners print; Claude writes the doc

As in `analysis/` (§2 there): a runner prints what it measured and **never writes a file** — no model file, no prediction file, no note. Claude reads the output, audits it and writes the doc in `notes/ML/` (`notes/ML/CLAUDE.md`). Every runner prints `corpus.corpus_line()` first.

## 3. Honest evaluation

- **Tune inside the training rows only,** over folds of whole league-seasons (`boosting.group_folds`). The test rows never choose a setting, a field or a number of trees.
- **Split by time:** fit on one season cohort, score the other, both ways. Both cohorts were seen before, so every result is exploratory; a claim is tested only on seasons scraped later (`notes/ANALYSIS/CLAUDE.md` §6).
- **Compare with the odds alone, by the same method** (model A). Judge a model by the comebacks in its top N, then by the log loss and the calibration — never by the AUC.
- **Fields:** only those with the timing `before` and the role `input` in `notes/FIELDS/`. Never an outcome; never a team id (`rows.py`).
- **Intervals** resample whole league-seasons of the test cohort (`score.resampled_sums`).
- **Deterministic:** fixed seeds and LightGBM's `deterministic` mode, so a run repeats exactly.

## 4. The tree mirrors `notes/ML/`

One runner per doc, at the same path in lowercase, as in `analysis/` (§3 there): `ml/schedule/whole_corpus/all/beyond_odds.py` is the runner of `notes/ML/SCHEDULE/WHOLE_CORPUS/ALL/BEYOND_ODDS.md`.

Run one as `uv run python -m ml.schedule.whole_corpus.all.beyond_odds`.

Shared code at the top of the package, with no notes counterpart:

- `rows.py` — one row per side of a priced match, with the fields of models A and B;
- `boosting.py` — LightGBM: the tuning over folds of whole league-seasons, the fit, the prediction and the SHAP values;
- `score.py` — the comebacks in the top N, the log loss and the calibration, with intervals over league-seasons.

## 5. Tests

As in `analysis/` (§4 there): mechanics only, toy frames, never `data/`; `tests/ml/` mirrors the tree. A boosting test uses a small synthetic table with a known signal.
