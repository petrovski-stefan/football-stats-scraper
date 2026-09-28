---
name: new-candidate
description: Walk a proposed comeback/over-6.5 rule or feature through the candidate protocol (graveyard check, reliability screen, market-orthogonality screen, then the outcome test), stopping at the first failure. Use before building or testing any new rule, feature, filter or signal.
argument-hint: "<rule or feature, in one sentence>"
allowed-tools: Read Grep Glob Bash(git log *) Bash(git status *)
---

# /new-candidate — the candidate protocol, gate by gate

Candidate: **$ARGUMENTS**

Sources this skill must agree with — re-read them if they changed since the skill was
written: `notes/STATE.md`, `modelling/CLAUDE.md`, `notes/PREREGISTRATION.md` A8 + A9,
`notes/RETRY_CANDIDATES_2026-09-23.md`, `notes/RELIABILITY_SCREEN_2026-09-23.md`,
`notes/BEHAVIOURAL_RESULTS.md`, `features/CLAUDE.md` §5. If a note disagrees with this
file, the note wins; say so.

## Rules for the whole run

- **Stop at the first failed step.** Print the verdict and nothing after it.
- **Never run `modelling.experiment --holdout`.** 2025-26 is spent (A9.1).
- **No new code without asking.** Reuse what exists. If a step has no existing code, stop,
  describe exactly what would be written (module, function, inputs, output), and ask the
  user before writing any. The known inventory:
  - exists: `modelling/experiment.py:wilson_ci`, `required_n`, `holm`;
    `domain/match.py:season_start_year`; `domain/paths.py` for every file location;
    `features.engine` for the as-of-round matrix (`--self-check` proves no leak).
  - does **not** exist (RELIABILITY §7, RETRY §8, BEHAVIOURAL §6 — all throwaway):
    the reliability screen, the market-orthogonality screen, a precision@top-N slate for
    an arbitrary score, a Mantel–Haenszel estimator over league-season strata.
  - `experiment.py:_slate_report` is private, hard-codes decile/quintile/third fractions
    and is not a top-N tool. Do not import it across modules.
- Steps b and c must not read any outcome column (`is_comeback*`, `ht_*`/`ft_*` goals of
  the match itself, `is_seven_or_more_goals`, anything post-kickoff). If the computation
  needs one, it is not outcome-free and the step is invalid.

## a. Graveyard check

1. Read the ledger in `notes/STATE.md` and `RETRY_CANDIDATES` §3 (Tier 1, "do not retry").
   Find the 1–3 closest rows by **mechanism**, not wording: the quantity measured, the
   side (leader/trailer/team/league), and the time it is known (pre-match vs HT vs in-play).
2. If the closest row is **Dead** (any variant: "Dead", "Dead (priced)", "Dead (reliability
   screen)") or in Tier 1, and the candidate measures the same quantity — including a
   rewording, a re-weighting, a different window, or a conditioning that the note already
   rejected (e.g. RELIABILITY §3 forbids conditioning `first_sub_minute_avg`) — **stop**.
   Cite the row verbatim (claim, status, key number, n, source) and the source section.
3. Otherwise, check the closed retry list (RETRY §4–5 as amended by A8: **15 claims**).
   - On it → record the claim number. Claim 15 carries the A8.4 condition: the
     `english_premier_league 2025-2026` stratum is excluded.
   - Not on it → label the run **EXPLORATORY-ONLY** for every later step. The list is
     closed (`modelling/CLAUDE.md` §4); a 16th claim needs a dated amendment before the
     confirmatory data exists (use `/preregister`).
4. Note any **Live-exploratory** or **Reopened** row it overlaps, so the result is read
   against it.

## b. Reliability screen (outcome-free)

Applies to features built from history blocks (the six-match `home_last*`, `away_last*`,
`h2h_last*` slots, or anything aggregated over a team's past matches). If the candidate is
not a team trait from history — e.g. a market price, a league label, a calendar fact —
write "b: not applicable (<why>)" and go to c.

Method (RELIABILITY §1, `features/CLAUDE.md` §5):
1. Every team-match, ordered by date per team, split odd/even into two halves.
2. Compute the trait per team on each half; correlate across teams → split-half r.
3. Spearman–Brown: `r_full = 2r/(1+r)`; to one match `r1 = r_full/(k-(k-1)·r_full)` with
   k = matches per team; to depth 6 `r6 = 6·r1/(1+5·r1)`, floored at 0.
4. **Judge on r6, not the raw split-half** (A9.4 erratum).

Verdict — the bar in `modelling/CLAUDE.md` "Screening bars (set 2026-09-28, before use)",
applied mechanically, no judgement branch:
- **r6 < 0.10 → KILLED at step b.**
- **r6 ≥ 0.10 → pass.** Report r6 against the reference table in `features/CLAUDE.md` §5
  (plain yellows 0.295, `yellows_while_leading` 0.290, per-minute 0.142, first-sub minute
  0.111, trailing-conditioned first-sub 0.000).

Also report, for information only (not a kill criterion), |r| between the trait and points
per game — `minutes trailing` was team strength in disguise at −0.925.

No code exists for this screen → stop and ask before writing it (see Rules).

## c. Market-orthogonality screen (outcome-free)

BEHAVIOURAL §5.2 / RETRY §6.5: correlate the candidate's score with the market price
before any outcome test. Use the pre-kickoff market columns in the detail/enriched files
(`implied_init_*`, `implied_live_*`; the O/U line if the corpus carries it — MARKET_LINE
found it the one live ranker). Report Pearson r per market column, with n and a 95% CI.

If the candidate **is** a market price or line (e.g. retry claims #9, #10), correlating it
with the market is meaningless: write "c: not applicable (candidate is a market price)"
and go to d.

Verdict — the bar in `modelling/CLAUDE.md` "Screening bars (set 2026-09-28, before use)",
applied mechanically to **max |r| across the market columns**, no judgement branch. It is
an effect-size bar; the CI is information only and decides nothing:
- **max |r| < 0.05 → KILLED at step c (no signal).**
- **max |r| > 0.80 → KILLED at step c (redundant: the market already carries it).**
- **0.05 ≤ max |r| ≤ 0.80 → pass.**

No code exists for this screen → stop and ask before writing it.

## d. Outcome test (reads labels)

Only after a–c pass.

1. **Fix N and the bar before computing anything** and print them first: slate size N
   (top-N by score), the power line from `required_n` / the Wilson lower bound needed to
   clear the base rate at that N.
2. Data: the enriched corpus via `domain/paths.py:enriched_csvs()`. Candidates identified
   strictly pre-kickoff; features as-of-round (`features.engine`). Event-based claims need
   the ordering check against the goal timeline (RELIABILITY §4: the red-card trap).
3. Metric: precision@top-N — hits, rate, **Wilson 95% CI** (`wilson_ci`), **lift vs base
   rate** — pooled with **Mantel–Haenszel over league-season strata**. Never report a
   per-league test as a result (STATE: "Per-league testing" is Dead). Never AUC/Brier as
   the verdict.
4. **Label: EXPLORATORY**, always, on the current corpus. Every league-season in
   `data/raw/` today is EPL 2025-26, which is spent (A9.1); dev seasons are parked. A
   confirmatory test runs only on the A9.2 confirmatory set, only after `/preregister`
   has an amendment committed before that set is scraped.
5. If the claim is #15, drop the EPL 2025-26 stratum (A8.4). On today's corpus that leaves
   **no data**: say so and stop with "not testable on the current corpus".
6. Report RETRY §7's four pass criteria for reference (Holm p < 0.05 within the family,
   Wilson LB > base, lift ≥ 1.25× at the pre-fixed N, same sign leave-one-league-out),
   with LOLO marked "n/a" when the corpus has one league.

The slate and MH code do not exist → stop and ask before writing them.

## e. Save the raw output

Write the complete stdout of step d, unedited, to `notes/runs/<YYYY-MM-DD>_<slug>.txt`
(create `notes/runs/`). Then tell the user: commit it **in the same commit as the note that
reports the result**, and update `notes/STATE.md` in that commit (`modelling/CLAUDE.md` §2;
STATE maintenance rule). Do not commit.

## Verdict — exactly one of

- `KILLED at step <a|b|c|d> — <reason, with the cited row / number>`
- `EXPLORATORY RESULT — N=<n>, hits=<k>, rate=<r>, Wilson [<lo>, <hi>], lift=<x>, base=<b>, strata=<s>; raw: notes/runs/<file>`
- `ELIGIBLE FOR PREREGISTRATION — passed a–c<, and d at LB > base with lift ≥ 1.25×>; next: /preregister`

Also print the state line: which steps ran, which were skipped, and whether any stop-and-ask
is pending.
