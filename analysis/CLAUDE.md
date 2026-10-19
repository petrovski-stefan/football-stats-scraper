# analysis/ — analysis of the finished corpus

Imports `domain` and `features` only.

## 1. Analysis, not machine learning

This package measures the finished corpus: descriptive statistics, classical tests, and fitted statistical models whose parameters mean something (Shin's method, Poisson rates). **No machine learning or deep learning lives here**: no gradient boosting, no neural networks, no hyperparameter search. Prediction models for unplayed matches belong to a later package (`notes/WORKING/IDEAS_2026-10-01.md` ideas 6 and 9).

## 2. Runners print; Claude writes the doc

A runner prints what it measured and **never writes a file**: no CSV, no transcript, no note. Claude reads the output, audits it and writes the doc in `notes/ANALYSIS/` (workflow: `notes/ANALYSIS/CLAUDE.md`). Every runner prints `corpus.corpus_line()` first, and the doc copies that line, so each claim names the corpus it was measured on.

## 3. The tree mirrors `notes/ANALYSIS/`

One runner per doc, at the same path in lowercase. The first folder is the source of the fields the runner uses: `schedule/`, `schedule_detail/`, `schedule_live/`, `schedule_detail_live/`, and `detail/`, `live/`, `detail_live/` without the schedule (rules: `notes/ANALYSIS/CLAUDE.md` §2):

| runner                                                 | doc                                                          |
| ------------------------------------------------------ | ------------------------------------------------------------ |
| `analysis/schedule/whole_corpus/all/shin.py`           | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`           |
| `analysis/schedule/whole_corpus/per_league/shin.py`    | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/SHIN.md`    |
| `analysis/schedule/whole_corpus/all/odds_yardstick.py` | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ODDS_YARDSTICK.md` |
| `analysis/schedule/whole_corpus/all/score_effects.py`  | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SCORE_EFFECTS.md`  |
| `analysis/schedule/whole_corpus/all/htft.py`           | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/HTFT.md`           |

Run one as `uv run python -m analysis.schedule.whole_corpus.all.shin`. A new source folder (`schedule_live/`, …) or level folder (`per_team/`) appears with its first runner, beside its notes folder.

Shared code sits at the top of the package and has no notes counterpart:

- `corpus.py` — loads every stage-3 schedule file, adds the season cohort and the 1X2 outcome, and gives the corpus line. The schedule is the only staged source today; loaders for the detail and live stage-3 files join it when plan steps P4–P6 create them;
- `stats.py` — scores, intervals, observed against expected (O/E), shrinkage and the heterogeneity test;
- `report.py` — the table printer that every runner uses;
- `methods/` — per-match methods that several runners use: `methods/shin.py`, and `methods/yardstick.py`, the odds yardstick that later docs read their claims against.

## 4. Tests

Tests check mechanics only and mirror the tree (`tests/analysis/schedule/whole_corpus/all/test_shin.py`). They use toy frames and never read `data/`. A runner's printing is not tested; the pure functions it calls are.
