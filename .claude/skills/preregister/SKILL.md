---
name: preregister
description: Draft a dated preregistration amendment for notes/PREREGISTRATION.md (hypothesis, closed family, Holm, metric and bar, A9 confirmatory set, single opening), refuse if the confirmatory data already exists, and append only after the user approves the full draft.
argument-hint: "<claim or family to preregister>"
disable-model-invocation: true
allowed-tools: Read Grep Glob Bash(git log *) Bash(git status *) Bash(uv run python -c *) Agent
---

# /preregister — a dated amendment, declared before the data

Claim: **$ARGUMENTS**

Read first, in full: `notes/PREREGISTRATION.md` (the template, §1–§8, and every amendment in
§10, especially **A8** and **A9**), `notes/STATE.md`, `notes/RETRY_CANDIDATES_2026-09-23.md`
§4–§7, `modelling/CLAUDE.md`. If they disagree with this file, they win.

## 0. Ledger audit

Spawn the `ledger-auditor` agent with scope `claim: $ARGUMENTS`. If its report has any
`source suspect` or `unresolved` row touching this claim's STATE row, holdout or
confirmatory status, or the retry-list size, show the report and stop until the user says
how to proceed. Otherwise record `Ledger audit: clean` or `Ledger audit: <n> unrelated
issues` in the draft's preamble and continue.

## 1. Graveyard check

Run step a of `/new-candidate` on the claim. If it is **Dead** or in RETRY §3 Tier 1 ("do
not retry"), stop and cite the row: preregistering a known null spends Holm budget on it
(RETRY §0, §3). Continue only if the user explicitly overrides, and record the override
and its reason in the draft.

## 2. Gather the fields

Ask the user for anything missing; do not invent it.

| field | rule |
|---|---|
| **Hypothesis** | H1 and its null, stated as in §1. Pre-kickoff only. |
| **Family** | Closed list. If the claim is one of RETRY's 15, the family is those 15 (A8.2). A claim not on the list becomes claim 16+, and the family grows by this amendment — only legal because it is declared before the confirmatory data exists (RETRY §6.1). |
| **Correction** | Holm across the whole family (`modelling/experiment.py:holm`). State m. |
| **Metric and bar** | precision@top-N with Wilson 95% CI and lift, N fixed here. Pass = RETRY §7: Holm p < 0.05; Wilson LB > base rate; lift ≥ 1.25×; same sign leave-one-league-out. Estimator: Mantel–Haenszel over league-season strata. Never per league. Give the power line (`required_n`). |
| **Confirmatory set** | A9.2: league-seasons first scraped **after 2026-09-28** and never present in `data/raw/` or among the event store's referenced matches, plus 2026-27 as it accrues. List each as a `config/LEAGUES.txt` URL (`/league/<season>/<id>`) with its season label, plus the **scrape start date**. Enumerate calendar-year labels (`2025`) explicitly (A8.5). |
| **Single opening** | One run, the exact command, run once after the scrape completes and the dev screen is closed; its raw output goes to `notes/runs/<date>_<name>.txt` in the commit that reports it (`modelling/CLAUDE.md` §2). No second opening; a lost transcript is not regenerated (A7). |
| **Inherited conditions** | e.g. claim 15 excludes the `english_premier_league 2025-2026` stratum (A8.4). |

## 3. Refuse if the confirmatory data already exists

Eligibility is decided per **league-season**, not per match (A10): one match already present
anywhere disqualifies the whole league-season. For each proposed league-season, check all
of these and **refuse** on any hit:

1. The scrape start date is on or before 2026-09-28, or already past (A9.2(i), A9.3).
2. `data/raw/<league>_<season>.csv` exists (`domain/paths.py:base_league_csvs`).
3. The league id appears, dated inside that season, in any history slot of any
   `data/raw/*_detail.csv` (`home_lastN_*`, `away_lastN_*`, `h2h_lastN_*`, N=1..6, columns
   `_league_id` and `_date`), **or** any such match id is in `data/raw/goals.csv`,
   `goals_done.csv`, `events.csv` or `events_done.csv`. Those are "the event store's
   referenced matches".

Season window for check 3, conservative: a cross-year label `YYYY-YYYY+1` covers
YYYY-07-01 → YYYY+1-06-30; a calendar-year label `YYYY` covers YYYY-01-01 → YYYY-12-31.
Use a read-only `uv run python -c` with pandas; write nothing.

On refusal, say which check hit, the file, and the count of matching rows, and quote the
A9 clause it violates. Do not draft.

## 4. Draft

Number it `A<next>` after the last amendment in §10, dated today. Follow the style of
A8/A9: a bold title line, numbered items, and a closing line stating whether any outcome
label was looked at in preparing it. Show the user the **complete** draft as it would be
appended, then stop and wait for explicit approval. Do not edit any file before approval.

## 5. After approval

1. Append the approved text verbatim to the end of `notes/PREREGISTRATION.md` §10.
2. Tell the user: commit it **before the scrape starts** (A9.3 — a league-season scraped
   without a committed amendment is dev data), and update `notes/STATE.md`'s open lead 1 in
   the same commit. Do not commit.
