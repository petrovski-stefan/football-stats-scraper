# modelling/ — experiments, the scoreline model, studies

## 1. Read before proposing anything

Read **`notes/STATE.md`** before proposing any model, feature, filter or rule. The project's measured failures are in the notes it points to, and most "new" ideas have already been tested.

## 2. Holdout and run records

- **`--holdout` targets a spent season and must not be run.** `uv run python -m modelling.experiment --holdout` opens 2025-26, whose outcome labels already informed multiple analyses (`notes/PREREGISTRATION.md` A9). The next confirmatory test needs a new holdout definition per A9: a confirmatory set declared in a dated amendment before its scrape starts. Use `--dev` for everything else.
- **Any run that reads outcome labels saves its raw output to `notes/runs/<date>_<name>.txt`, committed in the same commit as the note that reports it.** A finding with no committed output is recorded as note-only in `notes/STATE.md`.

## 3. The candidate protocol

- Judge a rule by **precision@top-N with a Wilson CI and lift**, never by AUC or Brier. A rule can have large lift in a small top-N set while scoring near-chance AUC.
- **Screen every candidate rule outcome-free against the market price first.** A rule orthogonal to the market is orthogonal to the best known signal.
- For a history-block feature, run the reliability screen before either of the above (`features/CLAUDE.md` §5).
- Test any claim the `notes/PREREGISTRATION.md` way: closed family list, Holm correction, one holdout opening, amendments logged with dates.

## 4. Binding rules

- **Stratify by league, never test per league.** Pool with Mantel–Haenszel over league-season strata.
- The retry list for the multi-country scrape is **closed**: `notes/RETRY_CANDIDATES_2026-09-23.md`. Do not add claims after the data arrives.
- **F1 is out of the graveyard.** Do not treat it as refuted; its retest is defined in the retry list.
- Do not propose a new pre-match comeback feature without reading `notes/RESULTS.md` and `notes/FILTER_RESULTS.md`.
- The market-line result is exploratory, not preregistered: read `notes/MARKET_LINE_FINDINGS.md` §4 before quoting it.

## 5. `scoreline.py`

`modelling/scoreline.py` is a calibrated generative model of the full scoreline distribution. It is the reusable asset from the filter study, and the natural instrument for the over-6.5 market (F9/F13), which is a direct functional of the same goal distribution. Validate with `--self-check --leak-check`.
