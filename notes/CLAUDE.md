# notes/ — how to read, write and edit the notes

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each.

This file gives the rules for every note. Each group folder has its own `CLAUDE.md`, with the rules for its notes. Claude Code loads the `CLAUDE.md` of a folder when Claude reads a file in that folder.

## 1. The groups

Each note is in one group folder. Under its title, each note has the header line of its group, with the rule of the group. Copy the header line from a note of the same group.

| folder | holds | rule |
|---|---|---|
| `WORKING/` | the current state and the open work | Edit it in place, and keep it current. |
| `ANALYSIS/` | the results of methods run on the corpus: one doc for each method and scope | Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it. |
| `ML/` | the results of ML methods run on the corpus (`ml/CLAUDE.md`): one doc for each method and scope | Claude writes it from a run. A new run replaces its numbers. Each claim is untested until a Record note tests it. |
| `RECORD/` | preregistrations, results and closed lists, as they were written | Do not edit it. Add a dated erratum. Only the user can decide an edit. |
| `REFERENCE/` | explainers, methods and reference data that other files cite | Change it only to correct or extend it. Keep the headings and numbers, because other files cite them. |
| `FIELDS/` | one doc for each source and stage, with one row for each field | One row per field. Never change a field code. The stage-1 docs are frozen after plan step P7. |
| `LOG/` | the dated record of changes | Add dated entries only. Never change an old entry. |
| `HISTORY/` | old plans and guides | Read it for context only. Do not edit it. Its facts can be out of date. |

When the notes are grouped by market (`WORKING/IDEAS_2026-10-01.md` idea 1), each market gets a subfolder inside each group, for example `REFERENCE/COMEBACKS/` (the user, 2026-10-14).

## 2. Where new text goes

| new text | where it goes |
|---|---|
| a fact about the current state, or an open idea | the matching note in `WORKING/` |
| a plan that the user agreed, but that is not done | a new file `WORKING/PLAN_<YYYY-MM-DD>_<TOPIC>.md` |
| a question for the user that must not stop the task | `WORKING/DECISIONS.md` |
| the result of a method run on the corpus | a doc in `ANALYSIS/`, from a runner of the `analysis/` package |
| the result of an ML method: a model with settings tuned on the data | a doc in `ML/`, from a runner of the `ml/` package |
| a test of a claim: its preregistration, then its result | two new notes in `RECORD/` |
| a change that is done: a rename, a move, a deletion, an item of an IDEAS or PLAN note, a dropped field | `LOG/MIGRATIONS.md` |
| a concept, a method or reference data that other notes cite | `REFERENCE/` |
| a new or changed field | `FIELDS/` |

Nothing new goes into `HISTORY/`. A note moves there only with the user's go.

## 3. Before and after an edit

1. **Show the change first.** Give the file, the exact text before and after, and the reason. Then wait for the user's go. "Focus on", "analyse" or "look at" is not a go (the user, 2026-10-11).
2. **Out-of-date facts are the exception** (the user, 2026-10-14). A drop, a rename or a deletion can leave old facts in a note.
   - Check each one against the repo first, because some can still be true.
   - Then fix all of them in one session, with no proposal.
   - Record the fixes in `LOG/MIGRATIONS.md`.
   - This applies to facts only. Claims, decisions and wording still need a go.
3. **After a drop or a rename, look for out-of-date text only in `WORKING/`, `ANALYSIS/`, `ML/`, `REFERENCE/` and `FIELDS/`.** A Record note gets a dated erratum, if necessary. The History notes and the old Log entries stay as they are.
4. **A doc of `ANALYSIS/`** is written after the user's go for that doc. Then Claude reports each claim, and the user can strike one (`ANALYSIS/CLAUDE.md` §3).
5. **Audit an analysis before you propose an edit from it** (the user, 2026-10-13):
   - each number is in the printed output and in its source note;
   - a reading "beyond the odds" or "structural" tests the assumptions of its yardstick: calibration by team strength, by league and by expected total, and its one first-half share;
   - check each correlation for data that both sides share;
   - report all the problems at once.
6. **After the edit,** list each file, what changed, and what you ran to test it.
7. **A notes task changes only the notes.** The root and package `CLAUDE.md` files stay the same, unless the user names them (the user, 2026-10-14). If a note change breaks a citation in one of them, change the note so that the citation stays true.

## 4. How to write

- **Language:** new text is in ASD-STE100 Simplified Technical English (the user, 2026-10-14). This includes new notes, new sections, errata, amendments and Log entries.
  - Use British spelling.
  - A descriptive sentence has 25 words or fewer. An instruction has 20 words or fewer.
  - Keep quotes, code, paths, tables, headings and cited labels as they are.
- **Old wording stays** in the Record notes, and in `HISTORY/HANDOFF.md` and `HISTORY/ESOTERIC_MODELS_V2.md`, because their worth is the text of their day. New errata in them are in STE.
- **A new note** gets the header line of its group, under its title. A note in STE also gets the line "**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each."
- **Paths:** cite a note with its group folder, for example `notes/WORKING/STATE.md`. A citation with no group folder, such as `notes/STATE.md`, is from before 2026-10-14. For a path that does not exist, look in `LOG/MIGRATIONS.md`.
- **Removed leagues:** never name a league that the user removed. Give a count only (the user).
- **Findings:** first find the kind of a fact about a market.
  - A definitional fact (true by the settlement rule) is never a finding.
  - A structural fact (it follows from the goal model) is derived once, in the explainer of the market.
  - Only an empirical fact is measured.
  - For comebacks, see `REFERENCE/MARKET_COMEBACKS.md` §6.
- **Tables:** keep them compact, with no padding. Prettier does not format `notes/` (`.prettierignore`), because padded tables cost about 2.4 times the context on each read.
