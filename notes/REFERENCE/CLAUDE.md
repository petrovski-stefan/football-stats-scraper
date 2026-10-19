# notes/REFERENCE/ — explainers, methods and reference data

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

The rule of this group: change a note only to correct or extend it. Keep the headings and numbers, because other files cite them. The rules for every note are in `notes/CLAUDE.md`.

## Read

| note | holds | read it |
|---|---|---|
| `GLOSSARY.md` | short cards for the football, statistics, leakage, protocol and ledger terms | when a term in a note or a `CLAUDE.md` file is not clear |
| `MARKET_COMEBACKS.md` | each fact about the comeback market, sorted into definitional, structural and empirical | before you measure or report a comeback fact |
| `STATS_PRIMER.md` | the formulas for Empirical Bayes shrinkage, Brier scores, calibration curves and Dixon–Coles | when a step uses one of these tools |
| `ESOTERIC_MODELS.md` | seven less common tools, each with a "Reach for this when" line | when a step matches one of these lines |
| `POINTS_DEDUCTIONS.md` | each known points deduction, with its date, cause and source | before you touch standings points or ranks, or when the final-table check fails on points |

In `GLOSSARY.md`, find the term and read its first line. Stop if that is enough.

## Write and edit

- **Change a note only to correct it or to extend it.** Keep each heading, section number, card title and item number. Keep cited labels word for word, for example "Reach for this when".
- **The concept explainers** (`GLOSSARY.md`, `MARKET_COMEBACKS.md`, and each market explainer to come) explain concepts only.
  - Use invented numbers.
  - Give no project results, no code, paths or column names, and no named leagues or matches.
  - A method choice in words is permitted. Its value and its outcome are not.
  - Project numbers go to `notes/ANALYSIS/`.
- **A new market explainer:** first ask the user the questions in `notes/WORKING/IDEAS_2026-10-01.md` idea 1, "Explainers". Then follow the format rules there.
- **`POINTS_DEDUCTIONS.md` and `domain/deductions.py` list the same deductions.** A change to one needs the same change to the other. Give each new deduction its date, cause and source.
