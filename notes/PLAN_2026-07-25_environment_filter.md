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

The criteria are fixed in writing, and they have no relation to the comeback rate. A
selection by comeback rate makes itself invalid, through the winner's curse:

1. nowgoal data completeness — 1X2, O/U and AH opening odds populated. Since 2026-10-10, a
   league stays only if every match without odds is a proven forfeit (`notes/MIGRATIONS.md`).
   The standings dropdown is no longer a criterion: the per-round standings scrape was removed
   on 2026-10-06;
2. ≥ 240 matches per season (power per league-season);
3. country and tier spread.

Deliverable: `notes/PREREGISTRATION_ENVIRONMENT.md`. It holds the league list, the
criteria, the closed feature list, the Phase 2 bar, the evaluation protocol, and §1's
figures as prior evidence. Commit it before the first page is scraped. The *claim* half of
that preregistration already exists as `notes/RETRY_CANDIDATES_2026-09-23.md`. The league
list is the missing half.

## Phase 1 — Scrape the corpus

The plan was ~25 leagues × 3 seasons ≈ 75 league-seasons. The corpus has 73 leagues and 144
finished league-seasons (`notes/MIGRATIONS.md`, 2026-10-10). The schedules are scraped (every finished season in
`config/leagues.json`, `notes/MIGRATIONS.md` 2026-10-09). The detail and goal stages remain.

**Cost note added 2026-09-23.** At first, this phase said "schedule-only, do not run
`scrapers/detail.py`", at 6–10 hours. That option no longer exists. `features/goals.py`
reads `{section}_last{n}_match_id`, and only the detail file has it. So the goal-timing
features need the detail scrape. An extrapolation from a measured ~2,000 renders/hour at
`WORKERS = 4`:

| stage | renders | rough time |
|---|---|---|
| detail (~27,750) | 1 per corpus match | ~14h |
| goals (~60,000 after dedupe) | 2–3× corpus | ~30h |
| **total** | | **~44h** |

That estimate comes from one throughput measurement. Use it only as an order of magnitude.
Measure again on the first league, before you start the others.

Do a smoke test per league before you scrape a full country: one season, then
`qa/validate.py`. Split and play-off formats will break the one-match-per-team-per-round
invariant that `features/engine.py:_rolling_form` asserts. That assertion is the guard. Fix
the league or drop it, and record which.

## Phase 2 — The preregistered study

**Bar:** keep the **top 20%** of fixtures by model score. The comeback rate of that slate
must have a **Wilson 95% lower bound above the pooled base rate**, on leagues and seasons
that were not used to build the rule. At ~25,000 matches, a 20% slate is ~5,000 fixtures.
So even a 1.2× lift (5.5% → 6.6%) passes it clearly.

**Two independent splits, both required:**

- *walk-forward in time*: an expanding window. Use `modelling/experiment.py:walk_forward`
  again;
- *leave-one-league-out*: the claim is that the filter works in other leagues, and a league
  holdout is the only test of that. It also takes the place of the clean holdout that the
  project no longer has (2025-26 was opened three times).

**Models:** the existing generative `modelling/scoreline.py`, plus a direct classifier on
P(HT decisive ∧ FT decisive ∧ ≥3 goals).

**Always reported:**

- the retained-rate curve (keep the top 5%–65%), with CIs;
- the oracle ceiling, calculated again on the new corpus;
- **headroom recovered** = (achieved − base) / (ceiling − base). It is the main number,
  whatever the result;
- the AUC per component. That AUC found the cause of the failure this time.

## Files

| file | change |
|---|---|
| `notes/PREREGISTRATION_ENVIRONMENT.md` | new — list, criteria, bar, protocol, prior evidence |
| `features/engine.py` | make G2 (H2H) optional when no detail exists |
| `modelling/filter_study.py` | keep-top-slate view + headroom-recovered metric, beside the existing exclusion curve |
| `notes/ENVIRONMENT_RESULTS.md` | verdict either way |

Use the existing code again. Do not build it again:

- the rolling as-of-round engine of `features/engine.py`, and its `--self-check`;
- the generative model of `modelling/scoreline.py`, with its `--self-check` /
  `--leak-check` gates;
- `modelling/filter_study.py:_exclude`;
- `modelling/experiment.py:wilson_ci` and `walk_forward`.

## Verification

- The seven quality gates of root `CLAUDE.md` are clean: ruff check, ruff format, mypy,
  complexipy, pyscn, deptry and pytest.
- `uv run python -m qa.validate` — every new league-season passes.
- `uv run python -m features.engine --self-check` — as-of-round invariant on the full corpus.
- `uv run python -m modelling.scoreline --self-check --leak-check` — recalibrated. The mass,
  zero-floor, parity and no-post-match-column gates still pass.
- `uv run python -m modelling.filter_study --curve` then `--bar` — the curve, the ceiling
  calculated again, and the preregistered pass/fail under both splits.

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
