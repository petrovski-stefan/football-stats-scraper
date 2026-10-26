# notes/WORKING/ — the current state and the open work

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

The rule of this group: edit a note in place, and keep it current. The rules for every note are in `notes/CLAUDE.md`.

## Read

| note | holds | read it |
|---|---|---|
| `STATE.md` | the claim ledger: each claim with its status, key number and source; the open leads | first: it is the current state of the research |
| `IDEAS_2026-10-01.md` | the roadmap: the open ideas of the user, their size and their order | before you start or propose one of its ideas |
| `PLAN_2026-10-05_STAGED_PIPELINE.md` | the staged pipeline: its rules, its decisions and its open steps | before any work on a data format, a data path or a refactor |
| `DECISIONS.md` | open questions for the user, each with a working value until the user decides | when a task touches one of its questions |
| `PLAN_2026-10-19_ML_TEST.md` | the ML test: do the pre-match fields hold comeback information beyond the odds? Its decisions and open steps | before you write or run an ML doc, or start idea 24 |
| `PLAN_2026-10-26_STYLE_FIXES.md` | the breaches of `CODING_STYLE.md` that the strict check of 2026-10-26 found, in 9 groups, and the order of the fixes | before a style fix, or when you change a function that it lists |

- These notes hold only open work and current facts. Done work is in `notes/LOG/MIGRATIONS.md`.
- The numbers in `STATE.md` are copies. If a number does not agree with its source note, the source note is correct.

## Write and edit

- **`STATE.md`:** a claim goes in only with the user's go, in the same commit as its source note (its header). A changed row or a new status (for example Dead → Reopened) also needs the user's go.
- **`IDEAS_*.md` and `PLAN_*.md`:** when an item is done, record it in `notes/LOG/MIGRATIONS.md`, under the date when it was done. Then delete it here. A partly done item keeps only its open part (the user, 2026-10-10).
- **A new plan:** a plan that the user agreed, but that is not done, goes into a new file here, `PLAN_<YYYY-MM-DD>_<TOPIC>.md`.
  - Give its status (PARKED or IN PROGRESS), the decisions taken and the measurements made.
  - Do not lose the measurements. They can take hours to make again.
  - Its header line: "**Group: Working.** Edit it in place, and keep it current. Move done items to `notes/LOG/MIGRATIONS.md`."
- **A plan with no open work left:** ask the user if it goes, or if it moves to `notes/HISTORY/`. Before it goes, move its open parts to `IDEAS_2026-10-01.md`, and record this in `notes/LOG/MIGRATIONS.md`.
- **`DECISIONS.md`:** add a question that needs the user's decision, but must not stop the task.
  - Give the next free number, the date and who raised it, the question, the options, the context and a working value.
  - When the user decides, move the entry to **Closed**, with the date and the choice.
  - If the choice changes a screening bar, or anything else under preregistration, also add a dated amendment to `notes/RECORD/PREREGISTRATION.md` §10.
