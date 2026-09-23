# PLAN — the comeback-environment filter, tested at corpus scale

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
- The corpus serves the project goal regardless, and yields F1's league-bar survey free.

## 2. Decisions taken 2026-07-25

| question | decision |
|---|---|
| league selection | **neutral criteria, list proposed for approval** before scraping |
| success bar | **top 20% slate, Wilson 95% lower bound above the pooled base rate** |

---

## Phase 0 — League list and preregistration (before any scraping)

Criteria, fixed in writing and unrelated to comeback rate — any comeback-based selection
self-invalidates via F1's winner's curse:

1. nowgoal data completeness — standings dropdown present, 1X2 and O/U odds populated;
2. ≥ 240 matches per season (power per league-season);
3. country and tier spread, weighted toward the ~30 countries **not** in
   football-data.co.uk's catalog, so F1's bar applies to genuinely unsurveyed leagues;
4. 3–5 already-surveyed leagues retained as cross-source validation controls.

Needs a **league-id discovery step** — `config/LEAGUES.txt` is a handful of hand-written
URLs today. Read nowgoal's league index via Selenium DOM; never its API.

Deliverable: `notes/PREREGISTRATION_ENVIRONMENT.md` — league list, criteria, closed
feature list, the Phase 2 bar, the evaluation protocol, and §1's figures recorded as prior
evidence. Committed before the first page is scraped. The *claim* half of that
preregistration already exists as `notes/RETRY_CANDIDATES_2026-09-23.md`; the league list
is the missing half.

## Phase 1 — Scrape the corpus

~25 leagues × 3 seasons ≈ 75 league-seasons.

**Cost note added 2026-09-23.** This phase originally read "schedule-only, do not run
`scrapers/detail.py`" at 6–10 hours. That is no longer available: `features/goals.py`
reads `{section}_last{n}_match_id`, which exists only in the detail file, so the
goal-timing features cannot be built without the detail scrape. Extrapolating from a
measured ~2,000 renders/hour at `WORKERS = 4`:

| stage | renders | rough time |
|---|---|---|
| schedule (2 odds passes per season) | — | 6–10h |
| detail (~27,750) | 1 per corpus match | ~14h |
| goals (~60,000 after dedupe) | 2–3× corpus | ~30h |
| **total** | | **~50–55h** |

That estimate rests on one throughput measurement — treat it as an order of magnitude, and
re-measure on the first league before committing to the rest.

Per-league smoke test — one season, then `qa/validate.py` — before committing to a country.
Split/playoff formats will violate the one-match-per-team-per-round invariant asserted in
`features/engine.py:_rolling_form`; that assertion is the guard. Fix or drop, and record which.

## Phase 2 — The preregistered study

**Bar:** keep the **top 20%** of fixtures by model score; that slate's comeback rate must
have a **Wilson 95% lower bound above the pooled base rate**, on leagues and seasons not
used to build the rule. At ~25,000 matches a 20% slate is ~5,000 fixtures, so even a 1.2×
lift (5.5% → 6.6%) clears it decisively.

**Two independent splits, both required:**

- *walk-forward in time* — expanding window, reuse `modelling/experiment.py:walk_forward`;
- *leave-one-league-out* — the claim is that the filter generalises, and league-holdout is
  the only test of that. It also substitutes for the clean holdout the project no longer
  has (2025-26 was opened three times).

**Models:** the existing generative `modelling/scoreline.py`, plus a direct classifier on
P(HT decisive ∧ FT decisive ∧ ≥3 goals).

**Always reported:** the retained-rate curve (keep top 5%–65%) with CIs; the oracle ceiling
recomputed on the new corpus; **headroom recovered** = (achieved − base) / (ceiling − base),
the headline number either way; per-component AUC, which is what diagnosed the failure
this time; and the **F1 league-bar survey** by-product — every league's comeback rate with
CIs against the ≥8%-over-≥600-matches bar, plus the persistence test.

## Files

| file | change |
|---|---|
| `notes/PREREGISTRATION_ENVIRONMENT.md` | new — list, criteria, bar, protocol, prior evidence |
| `config/LEAGUES.txt` | expanded to the approved list |
| `features/engine.py` | make G2 (H2H) optional when no detail exists |
| `modelling/filter_study.py` | keep-top-slate view + headroom-recovered metric, beside the existing exclusion curve |
| `qa/validate.py` | per-league round-count checks |
| `notes/ENVIRONMENT_RESULTS.md` | verdict either way |

Reuse, don't rebuild: `features/engine.py`'s rolling as-of-round engine and `--self-check`;
`modelling/scoreline.py`'s generative model with its `--self-check` / `--leak-check` gates;
`modelling/filter_study.py:_exclude`; `modelling/experiment.py:wilson_ci` and `walk_forward`.

## Verification

- `uv run ruff check && uv run ruff format --check && uv run mypy .` clean.
- `uv run python -m qa.validate` — every new league-season passes.
- `uv run python -m features.engine --self-check` — as-of-round invariant on the full corpus.
- `uv run python -m modelling.scoreline --self-check --leak-check` — recalibrated; mass, zero-floor,
  parity and no-post-match-column gates still pass.
- `uv run python -m modelling.filter_study --curve` then `--bar` — curve, recomputed ceiling, and the
  preregistered pass/fail under both splits.

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
