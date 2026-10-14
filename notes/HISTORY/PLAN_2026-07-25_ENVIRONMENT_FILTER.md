# PLAN — the comeback-environment filter, tested at corpus scale

**Group: History.** Read it for context only. Do not edit it. Its facts can be out of date.

**Written 2026-07-25. Trimmed 2026-09-23: the completed Over/Under capture work was
removed, leaving only what is still outstanding.**
Pick this up by reading §0 (what's decided) and §1 (what's already measured), then
starting at Phase 0. Companions: `notes/PREREGISTRATION.md`, `notes/RESULTS.md`,
`notes/PREREGISTRATION_FILTER.md`, `notes/FILTER_RESULTS.md`,
`notes/RETRY_CANDIDATES_2026-09-23.md`.

---

## 0. The project goal, now strictly defined (decided 2026-07-25)

> **Pre-match comeback prediction. Comebacks only. No in-play. Not for money — a
> research-grade result held to a professional bar. Corpus: 20–30 handpicked leagues ×
> last 3 seasons.**

Over-6.5 is an **input feature, not a target**. Open items the user has not yet settled:
whether the HANDOFF §7 LLM matchup-card engine is still the deliverable (§4 of the goal
questions), and the stopping rule for the whole thesis (§5) — though the bar in Phase 2
below supplies one for this hypothesis.

**The hypothesis under test (the user's):** exact comeback prediction is hard, but a
*comeback environment* may be identifiable — filter out fixtures that cannot produce a
comeback and the surviving slate's rate rises well above the 5–8% base.

## 1. What is already measured

### The ceiling is real, and higher than earlier notes implied

> **Erratum, 2026-10-11** (`notes/IDEAS_2026-10-01.md` idea 13; the text below is not
> edited): the ceiling is an oracle. That a filter on these three conditions loses no
> comebacks is true by definition, not a measurement (`notes/MARKET_COMEBACKS.md` §1, "The
> comeback environment" and "Filters that remove impossible matches"). Only the share of
> matches inside the environment (34.5% here) is data.

A comeback requires three necessary conditions. A perfect filter on their conjunction
keeps 34.5% of matches, loses **zero** comebacks, and lifts 5.54% → **16.03%, i.e. 2.89×**:

| environment definition | keeps | retained rate | lift |
|---|---|---|---|
| total goals ≥ 3 | 54.9% | 10.09% | 1.82× |
| HT decisive & total ≥ 3 | 39.6% | 13.99% | 2.53× |
| **HT decisive & FT decisive & total ≥ 3** | **34.5%** | **16.03%** | **2.89×** |

(`FILTER_RESULTS.md` quoted 1.79× — that was the goals-only oracle and understates the
idea. The conjunction is the right envelope.)

### But the conjunction is currently unpredictable — less so than its own parts

Held-out AUC, train 2023-25 → test 2025-26, n=591:

| target | base | AUC |
|---|---|---|
| HT decisive | 61.1% | 0.522 |
| FT decisive | 72.3% | 0.519 — *market draw price alone: **0.544*** |
| total ≥ 3 | 54.1% | 0.545 |
| **environment (all three)** | 35.0% | **0.497** |
| comeback | 5.6% | 0.496 |

Multiplying three weak signals yields noise. Ranking by predicted environment and keeping
the top 20% gave a kept set 35.6% environment vs 35.0% corpus-wide — **zero enrichment**.
Ranking by model P(comeback) reached 1.20× at 30% coverage, CI [4.87%, 9.47%], which
contains the base rate. Headroom recovered: ~11%.

### Why it is still worth running

- At n=591 the standard error on AUC is ≈0.03, so a true 0.55 sits inside the interval.
  **591 matches cannot resolve this; 25,000 can.**
- The corpus serves the project goal regardless.

## 2. Decisions taken 2026-07-25

| question | decision |
|---|---|
| league selection | **neutral criteria, list proposed for approval** before scraping |
| success bar | **top 20% slate, Wilson 95% lower bound above the pooled base rate** |

---

## Phase 0 — League list and preregistration (before any scraping)

Moved to `notes/IDEAS_2026-10-01.md` idea 4 on 2026-10-14.

## Phase 1 — Scrape the corpus

Moved to `notes/IDEAS_2026-10-01.md` idea 4 on 2026-10-14.

## Phase 2 — The preregistered study

Moved to `notes/IDEAS_2026-10-01.md` idea 4 on 2026-10-14.

## Files

Moved to `notes/IDEAS_2026-10-01.md` idea 4 on 2026-10-14.

## Verification

Moved to `notes/IDEAS_2026-10-01.md` idea 4 on 2026-10-14.

## Honest expectation

The point estimate says null: AUC 0.497 on the conjunction, zero measured enrichment.
Two things could move it, in descending plausibility: **sample size** (25,000 matches
resolves an AUC difference 591 cannot), and **league diversity** (all evidence so far is
England and Poland).

The bar needs ~1.2× and the ceiling is 2.89×, so there is genuine room — but "5–8% goes up
so much" is bounded at **16% even with perfect foresight**, and the realistic target is
6.5–7%. A clean, well-powered null across 25 leagues is publishable and closes the
question; a validated 1.2× slate is the project's first real positive. Both justify the
scrape, which is why the corpus is worth building either way.
