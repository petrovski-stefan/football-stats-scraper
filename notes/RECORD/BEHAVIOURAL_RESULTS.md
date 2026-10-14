# RESULTS — the behavioural-profile candidate rule

**Group: Record.** Do not edit it. Add a dated erratum. Only the user can decide an edit.

**Run 2026-08-29.** The first test conducted under the *candidate* protocol rather than
the global-metric one, and the only study in this repo whose rule was **hand-weighted and
frozen** rather than fitted.

**Provenance caveat, stated up front.** This document was written on **2026-09-20** from
session records, not from a preserved transcript — no raw output file survives (the same
gap `notes/PREREGISTRATION.md` A7 records for the F12 holdout). The figures below are the
ones that were reported at the time. Treat them as a faithful record of a measurement
that was made, not as a reproducible artefact: no code for this rule is in the repo, so
re-deriving it means re-implementing it from §2.

Companions: `notes/RESULTS.md`, `notes/FILTER_RESULTS.md`.

---

## Verdict

**Failed, and not narrowly. The bar was statistically excluded at every slate size ≥ 50.**

| slate | n | hits | rate | lift | Wilson 95% CI |
|---|---|---|---|---|---|
| **top 100 (primary)** | 100 | **5** | **4.90%** | **0.88×** | [2.11%, 10.97%] |

Corpus: all **2,058** matches (EPL + Ekstraklasa, 2023-24 → 2025-26), 114 comebacks,
base rate **5.54%**. The preregistered bar was a **15%** absolute hit rate.

(The reported 4.90% against 5 hits implies the slate ran to ~102 rather than exactly 100,
which is what a top-N cut does when scores tie. The transcript that would settle it is
gone; the conclusion is unaffected at any n in that range.)

## 1. Why this was tested differently from everything before it

Every earlier study in this repo judged a comeback model by a **global** metric — Brier,
log-loss, AUC over the whole corpus. On 2026-08-29 that was identified as the wrong
instrument for the actual goal, which is **finding a small set of candidates**:

> A rule firing on 35 matches at a 20% hit rate — a 3.6× lift and a genuinely strong
> product — scores **AUC 0.527**. That sits inside the 0.496–0.545 band every buried
> result in `notes/RESULTS.md` occupies, and next to `modelling/scoreline.py`'s own
> out-of-sample 0.5266.

So the graveyard in `RESULTS.md` never tested the candidate hypothesis; it was
structurally unable to see it. The finest slate ever measured there was §2's top decile
at n = 59, 1 hit, CI [0.30%, 9.00%] — an interval wide enough to contain almost any
claim. This study exists to test the candidate hypothesis on its own terms.

**Protocol, fixed before the rule was scored:**

- candidates identified **strictly pre-kickoff**;
- a hit is a **match-level comeback, either side** (direction deferred to production);
- the candidate set is **top-N by score, with N named in advance**;
- the bar is an **absolute hit rate named before computing**, reported with lift and a
  Wilson CI beside it;
- scoring weights are **hand-set by rarity and frozen — never fitted**.

A frozen unfitted rule estimates no parameters, so it needs no train/test split: it was
evaluated on the full corpus with no burn-in. Power on 2,058 matches: a 50-match slate
needs 6 hits (12%), 100 needs 11 (11%), 300 needs 25 (8.3%) to put the Wilson lower bound
above the 5.54% base.

## 2. The rule

For each side, score its **last 5 matches in all competitions** plus the **3 most recent
H2H meetings**, counting these signals:

| signal | weight |
|---|---|
| trailed at HT, then drew or won | 3.5 |
| led at HT, then drew or lost | 3.6 |
| scored only in the second half | 1.8 |
| scored only in the first half | 2.3 |
| over 6.5 goals | 5.1 |

Weights are `-log2(per-game rate)` — rarer signals count for more — applied to raw counts.
A match's score is `max(home profile, away profile)`.

The idea is sound on its face and is the natural formalisation of the manual Mode 2
"turnaround registry" (HANDOFF §3, §8): a comeback needs a **recoverer** and a
**collapser**, so profile both sides for recovery and fragility and take the stronger case.

## 3. Ruled out as explanations for the failure

The null was interrogated before being accepted:

- **Not weight dominance.** Per-signal variance contributions were balanced
  (sd 1.79–2.19), so no single rare signal was driving the ranking.
- **Not the aggregation.** The strict-AND conjunction the rule was first described as
  gives lift **1.00× exactly** (n = 234) — precisely the base rate.
- **Not one bad signal masking a good one.** All five signals were tested individually
  across both sides: **12 comparisons, zero above 1.96 SE.** The nominally strongest —
  "home team has recovered recently" — pointed the *wrong way*, at −1.92%.

## 4. Why it failed — the root cause worth keeping

**The score is orthogonal to the mechanism.** Correlations with the things a comeback is
actually made of:

| against | corr |
|---|---|
| HT decisive (someone leads at the break) | **+0.004** |
| total goals | **+0.006** |
| the market price | +0.05 |

A comeback requires `HT-decisive AND total ≥ 3`. Team behavioural history forecasts
neither. This is the same wall `RESULTS.md` §3 hit from the other direction — there, a
bookmaker's full information beat a constant on the half-time state by 0.64%; here, a
team's own recovery and collapse history correlates with it at 0.004.

It also closes a loop with **F2** of the old league study (dropped 2026-10-13), which killed comeback-proneness built
from *comeback counts* and recommended building it from *mechanisms* instead. This rule
did exactly that — HT-state transitions, half-splits, goal volume — and the mechanism
version dies too, on this corpus.

## 5. What survives

1. **The candidate framing is correct and is retained.** The reason to report
   precision@top-N with a Wilson CI and lift, never AUC or Brier, is established by §1 and
   is not affected by this rule's failure.
2. **One cheap screen, learned here:** before testing any new candidate rule against
   outcomes, first screen it **outcome-free for correlation with the market price**. A
   rule orthogonal to the market is orthogonal to the best known signal, and §4 shows that
   this is detectable without spending a test.
3. **The negative is scoped to these two leagues.** Re-testing behavioural profiles
   belongs to the unsurveyed-league extension survey, not to EPL and Ekstraklasa.

## 6. Limits

- Two leagues, three seasons, 2,058 matches, 114 comebacks — the same corpus, and the same
  ceiling on power, as `notes/RESULTS.md`.
- One rule, one slate size as primary. A different weighting of the same five signals was
  not tested, and §3's variance check is the only evidence that it would not matter.
- No code in the repo implements this. Reproducing it means rebuilding it from §2.
