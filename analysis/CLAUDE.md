# analysis/ — analysis of the finished corpus

Imports `domain` and `features` only.

## 1. Analysis, not machine learning

This package measures the finished corpus: descriptive statistics, classical tests, and fitted statistical models whose parameters mean something (Shin's method, Poisson rates). **No machine learning or deep learning lives here**: no gradient boosting, no neural networks, no hyperparameter search. Prediction models for unplayed matches belong to a later package (`notes/WORKING/IDEAS_2026-10-01.md` ideas 6 and 9).

## 2. Runners print; Claude writes the doc

A runner prints what it measured and **never writes a file**: no CSV, no transcript, no note. Claude reads the output, audits it and writes the doc in `notes/ANALYSIS/` (workflow: `notes/ANALYSIS/CLAUDE.md`). Every runner prints `corpus.corpus_line()` first, and the doc copies that line, so each claim names the corpus it was measured on.

## 3. The tree mirrors `notes/ANALYSIS/`

One runner per doc, at the same path in lowercase: `analysis/schedule/whole_corpus/all/shin.py` is the runner of `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`. The first folder is the source of the fields the runner uses: `schedule/`, `schedule_detail/`, `schedule_live/`, `schedule_detail_live/`, and `detail/`, `live/`, `detail_live/` without the schedule (rules: `notes/ANALYSIS/CLAUDE.md` §2). List the tree to see every runner.

Run one as `uv run python -m analysis.schedule.whole_corpus.all.shin`. A new source folder (`schedule_live/`, …) or level folder appears with its first runner, beside its notes folder.

Shared code sits at the top of the package and has no notes counterpart:

- `corpus.py` — loads every stage-3 schedule file, adds the season cohort and the 1X2 outcome, gives the corpus line and the key of each round, and names the columns of the AH market. The schedule is the only staged source today; loaders for the detail and live stage-3 files join it when plan steps P4–P6 create them;
- `stats.py` — scores, intervals, observed against expected (O/E), shrinkage, the heterogeneity test with the spread it can find, and the Mantel–Haenszel odds ratio over strata with the Holm correction;
- `report.py` — the table printer that every runner uses;
- `card.py` — the card of each level (`notes/ANALYSIS/CLAUDE.md` §2): its quantities, with the yardstick column of the main ones, and the outcomes of each match that they read; the team rows of `PER_TEAM/`, with the yardstick's chances for each team;
- `units.py` — one quantity per unit (a league or a team): its value and variance, one heterogeneity test across the units, the shrunk values, the luck line, the agreement of the two season cohorts, the test of the parts of a unit (its seasons, its teams or its rounds) with shrinkage toward it, the repeat test, and that test as one row with its p from shuffles of the parts inside their units;
- `methods/` — per-match methods that several runners use: `methods/shin.py`, and `methods/yardstick.py`, the odds yardstick that later docs read their claims against.

## 4. Tests

Tests check mechanics only and mirror the tree (`tests/analysis/schedule/whole_corpus/all/test_shin.py`). They use toy frames and never read `data/`. A runner's printing is not tested; the pure functions it calls are.
