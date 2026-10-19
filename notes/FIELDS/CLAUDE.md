# notes/FIELDS/ — one doc for each source and stage

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

The rule of this group: one row per field. Never change a field code. The stage-1 docs are frozen after plan step P7. The rules for every note are in `notes/CLAUDE.md`.

## Read

1. Start with `README.md`. It lists the docs, and it tells how to read a row (id, name, timing, role, ✓, status). It also gives the rules for values and the reference match.
2. Then read the doc of the source and stage that you work on, for example `SCHEDULE_3_MULTI.md` (schedule, stage 3). Read it before you touch, add or read a column of a staged file.

- A doc lists only the columns that its stage adds. The earlier columns are in the docs of the earlier stages.
- The detail docs describe the files that plan step P4 will build, not the old detail file.
- `ANALYSIS_FEATURES.md` lists the model features that `features/engine.py` builds in memory. They are not stored.
- The stages, their rules and the decisions behind them are in `notes/WORKING/PLAN_2026-10-05_STAGED_PIPELINE.md` §1–3.

## Write and edit

- **A row is the specification of its field.** Write a new row first, and get the user's go. The code comes after it.
- **A new field** gets one row in the doc of its source and stage, with the next free id. Never reuse or change an id. Gaps are permitted.
- **Its column name** starts with the code of its doc, for example `s3_` (`README.md`, "Rules for values").
- **Give each field its timing** (`before` or `after` kickoff) **and its role.** A stage-3 field also gives its row window: which rows it reads. All of them must kick off before this match. This line is the guard against leakage.
- **Who checks a row:**
  - stage 1: the user, on the page, field by field, with about 20 rows in a sitting. Mark ✓ only after the user's own check, never on Claude's word. Then update the progress line in `README.md`;
  - stage 2: Claude writes the formulas, and the user skims them;
  - stage 3: Claude writes the rows, and the `stats-reviewer` agent checks them.
- **A page candidate** (`C<n>`) is a value that a page shows, but that no file stores. The user decides each one in plan step P2. The decision goes in its row, and the count goes in `README.md`.
- **A dropped field:** delete its row and its explanation. Record the drop in `notes/LOG/MIGRATIONS.md`, with the date, who decided and why (the user, 2026-10-11).
- **After plan step P7,** a stage-1 doc is frozen. Do not change it.
