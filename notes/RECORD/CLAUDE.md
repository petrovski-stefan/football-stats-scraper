# notes/RECORD/ — preregistrations, results and closed lists

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

The rule of this group: do not edit a note. Add a dated erratum. Only the user can decide an edit. The rules for every note are in `notes/CLAUDE.md`.

## Read

| note | holds | read it |
|---|---|---|
| `PREREGISTRATION.md` | the template for a test (closed family list, Holm correction, one holdout opening) and its amendment log, §10 | before you test a claim |
| `RESULTS.md` | the verdict on six nowgoal-exclusive feature families: all dead | before you propose a new pre-match comeback feature |
| `PREREGISTRATION_FILTER.md` | the closed preregistration of the exclusion-filter study, with its amendments, §9 | when you read that study again |
| `FILTER_RESULTS.md` | the verdict of that study | before you propose a filter that removes "comeback-impossible" matches |
| `FILTER_STUDY_RAW.md` | the frozen raw output of the `filter_study --bar` run of 2026-07-25 | only to audit the numbers of that study |
| `BEHAVIOURAL_RESULTS.md` | the test of a hand-weighted rule; the candidate protocol starts here | before you propose a hand-weighted rule |
| `RETRY_CANDIDATES_2026-09-23.md` | the closed list of claims to try again | before you try again a claim that failed |
| `RELIABILITY_SCREEN_2026-09-23.md` | the reliability screen | before you build a history-block feature, especially one on cards or substitutions |
| `LEAGUES_INCIDENTS.md` | known match-fixing incidents for each league, not checked | before you analyse, keep or drop a league |

- **These notes keep the text of the day when they were written.** That text is their worth. Their wording is not STE, and it stays so.
- **First read the dated errata under the title** (`> **YYYY-MM-DD:** ...`), and the amendment log of a preregistration. They tell what changed later.
- **Old paths and F-numbers are normal here.** The old league study and its F-numbers were dropped on 2026-10-13. Find an old path in `notes/LOG/MIGRATIONS.md`.
- **The code of these studies is gone.** `modelling/` was deleted on 2026-10-18. Its last version is in git at `633ff90`. So no run writes `FILTER_STUDY_RAW.md` now, although its header says that each `--bar` run overwrites it.

## Write

- **Do not edit the text.** Only the user can decide an edit.
- **A correction or an update is a dated erratum** in STE, under the header line: `> **YYYY-MM-DD:** ...`. A preregistration gets a dated amendment in its log: `PREREGISTRATION.md` §10, `PREREGISTRATION_FILTER.md` §9. Claude proposes the text, and the user decides.
- **If an erratum changes a ledger row,** point to it from `notes/WORKING/STATE.md`.
- **The retry list is closed.** Add no claim to `RETRY_CANDIDATES_2026-09-23.md`. Its amendments go in the log of `PREREGISTRATION.md`.
- **A test of a claim gets two new notes here.**
  - The first is its preregistration. Commit it before the test reads its data. The holdout rules are in `notes/ANALYSIS/CLAUDE.md` §6.
  - The second is its results, whatever the verdict.
  - The claim in its `notes/ANALYSIS/` doc then gets the status `tested`, with a link to the results note.
  - Its row in `notes/WORKING/STATE.md` changes only with the user's go.
