# analysis/ — analysis of the finished corpus

Imports `domain` and `features` only.

## 1. Analysis, not machine learning

This package measures the finished corpus: descriptive statistics, classical tests, and fitted statistical models whose parameters mean something (Shin's method, Poisson rates). **No machine learning or deep learning lives here**: no gradient boosting, no neural networks, no hyperparameter search. Prediction models for unplayed matches belong to a later package (`notes/WORKING/IDEAS_2026-10-01.md` ideas 6 and 9).

## 2. Runners print; Claude writes the doc

A runner prints what it measured and **never writes a file**: no CSV, no transcript, no note. Claude reads the output, audits it and writes the doc in `notes/ANALYSIS/` (workflow: `notes/ANALYSIS/CLAUDE.md`). Every runner prints `corpus.corpus_line()` first, and the doc copies that line, so each claim names the corpus it was measured on.

## 3. The tree mirrors `notes/ANALYSIS/`

One runner per doc, at the same path in lowercase. The first folder is the source of the fields the runner uses: `schedule/`, `schedule_detail/`, `schedule_live/`, `schedule_detail_live/`, and `detail/`, `live/`, `detail_live/` without the schedule (rules: `notes/ANALYSIS/CLAUDE.md` §2):

| runner                                                        | doc                                                                 |
| ------------------------------------------------------------- | ------------------------------------------------------------------- |
| `analysis/schedule/whole_corpus/all/shin.py`                  | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SHIN.md`                  |
| `analysis/schedule/whole_corpus/per_league/shin.py`           | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/SHIN.md`           |
| `analysis/schedule/whole_corpus/all/odds_yardstick.py`        | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ODDS_YARDSTICK.md`        |
| `analysis/schedule/whole_corpus/all/score_effects.py`         | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SCORE_EFFECTS.md`         |
| `analysis/schedule/whole_corpus/all/htft.py`                  | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/HTFT.md`                  |
| `analysis/schedule/whole_corpus/per_league/odds_yardstick.py` | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/ODDS_YARDSTICK.md` |
| `analysis/schedule/whole_corpus/per_league/odds_coverage.py`  | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/ODDS_COVERAGE.md`  |
| `analysis/schedule/whole_corpus/all/rates.py`                 | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/RATES.md`                 |
| `analysis/schedule/whole_corpus/per_league/rates.py`          | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/RATES.md`          |
| `analysis/schedule/whole_corpus/all/prices.py`                | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/PRICES.md`                |
| `analysis/schedule/whole_corpus/per_team/rates.py`            | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_TEAM/RATES.md`            |
| `analysis/schedule/whole_corpus/per_team/odds_yardstick.py`   | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_TEAM/ODDS_YARDSTICK.md`   |
| `analysis/schedule/whole_corpus/all/season_phase.py`          | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SEASON_PHASE.md`          |
| `analysis/schedule/whole_corpus/all/odds_groups.py`           | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ODDS_GROUPS.md`           |
| `analysis/schedule/whole_corpus/all/stakes.py`                | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/STAKES.md`                |
| `analysis/schedule/whole_corpus/all/round_fields.py`          | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ROUND_FIELDS.md`          |
| `analysis/schedule/whole_corpus/all/prematch_screen.py`       | `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/PREMATCH_SCREEN.md`       |

Run one as `uv run python -m analysis.schedule.whole_corpus.all.shin`. A new source folder (`schedule_live/`, …) or level folder (`per_team/`) appears with its first runner, beside its notes folder.

Shared code sits at the top of the package and has no notes counterpart:

- `corpus.py` — loads every stage-3 schedule file, adds the season cohort and the 1X2 outcome, gives the corpus line, and names the columns of the AH market. The schedule is the only staged source today; loaders for the detail and live stage-3 files join it when plan steps P4–P6 create them;
- `stats.py` — scores, intervals, observed against expected (O/E), shrinkage, the heterogeneity test with the spread it can find, and the Mantel–Haenszel odds ratio over strata with the Holm correction;
- `report.py` — the table printer that every runner uses;
- `card.py` — the card of the `ALL/` and `PER_LEAGUE/` levels (`notes/ANALYSIS/CLAUDE.md` §2): its quantities, and the outcomes of each match that they read;
- `units.py` — one quantity per unit (a league or a team): its value and variance, one heterogeneity test across the units, the shrunk values, the luck line, the agreement of the two season cohorts, the test of the parts of a unit (its seasons, or its teams) with shrinkage toward it, and the repeat test;
- `methods/` — per-match methods that several runners use: `methods/shin.py`, and `methods/yardstick.py`, the odds yardstick that later docs read their claims against.

## 4. Tests

Tests check mechanics only and mirror the tree (`tests/analysis/schedule/whole_corpus/all/test_shin.py`). They use toy frames and never read `data/`. A runner's printing is not tested; the pure functions it calls are.
