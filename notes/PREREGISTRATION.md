# PREREGISTRATION.md — Can nowgoal-exclusive features overturn F12?

**Written 2026-07-25, before any model was fitted and before the holdout season was
touched.** Everything in this document is fixed. Nothing may be added to the family list,
no bar may be moved, and no split may be redrawn after results are seen. Deviations, if
any prove unavoidable, get appended to §10 with a reason and a date — never edited in
silently.

---

## 1. The claim under test

`notes/LEAGUE_STUDY.md` **F12** concluded that pre-match comeback prediction is refuted:
on 23,127 football-data.co.uk matches the best constructible chained model scored a
held-out Brier of 0.04809 against 0.04812 for a constant "always say 5%" — a tie.

That verdict was reached with football-data's entire feature vocabulary: **closing 1X2
odds, an Asian-handicap line, and an over/under 2.5 price.** It contained no team-level
information of any kind. F12 is therefore a statement about *what a price can predict*,
not about what is predictable.

> **Hypothesis (H1).** Team-level features available only in the nowgoal corpus predict
> the half-time state better than the market price alone, by enough to move a chained
> comeback pricer's held-out Brier past both the constant and the odds-only chain.

The null is F12: no nowgoal feature family adds skill beyond the price.

## 2. Data, fixed

Corpus: `data/*_enriched.csv` as it exists on 2026-07-25 — 2 leagues × 3 seasons,
**2,058 matches, 114 comebacks (5.54%)**. No new scraping is performed for this study; a
corpus expansion decision is deferred until after the result is known, precisely so that
it cannot be made in response to the result.

| split | seasons | matches | comebacks | HT non-draws |
|---|---|---|---|---|
| **dev** | 2023-24, 2024-25 | 1,372 | 78 | 849 |
| **holdout** | 2025-26 | 686 | 36 | 414 |

The holdout is opened **once**, by a single `modelling/experiment.py --holdout` run, after the dev
screen is complete and this document is committed. Leagues are pooled, justified by
LEAGUE_STUDY F1 (leagues do not differ in comeback rate).

## 3. Why the target is decomposed

Measured on the corpus:

| quantity | trials | positives | rate |
|---|---|---|---|
| Someone trails at HT (**factor 1**) | 2,058 | 1,263 | 61.4% |
| Trailer wins (**factor 2**) | 1,263 | 114 | 9.0% |
| Comeback (**the product**) | 2,058 | 114 | 5.5% |

F12 modelled the product. The product is rare; both of its factors are common. So:

```
P(comeback) = Σ_d  P(team X trails by d at HT | features)  ×  F11_completion(X's odds, d, venue)
                   └─ we fit this: 1,372 dev trials ─┘        └─ fixed, imported ─┘
```

**Factor 2 is imported, not fitted.** LEAGUE_STUDY **F11** published a completion model —
logistic on `log(trailer closing odds)` = −1.72, `deficit` = −1.27, `venue` = +0.001 —
trained on 9,195 trailing states and validated walk-forward on 4,526 more, calibrating
decile-by-decile across a 40× range. Those coefficients were estimated on a corpus
disjoint from this study's fitting data, so using them costs **zero degrees of freedom**,
rather than burning 78 positives to re-estimate a curve already measured 120× better.

The baseline uses the **identical** imported completion stage. Any Brier difference between
baseline and candidate is therefore attributable solely to factor 1 — the half-time state —
which is exactly where F12 was blind.

## 4. Feature families — the complete, closed list

Six families, **at most two engineered features each**, defined here before construction.
All are computed with a strict as-of cutoff (`round < current round`, 5-round burn-in) and
`domain/stats.py` is reused for every derived per-match quantity.

| # | family | features (max 2) | targets | exclusive? |
|---|---|---|---|---|
| **A** | HT-state history | rolling rate of trailing at HT; rolling 1H goals for − against | factor 1 | derivable elsewhere, untested by F10 |
| **B** | 2H supremacy — F2's endorsed mechanism replacement | rolling 2H goal difference; blown-lead rate (led at HT, failed to win) | factor 2 | derivable elsewhere, untested by F10 |
| **C** | Pressure vs conversion — F7: comebacks are deserved dominance | last-6 corner share minus goal share | both | **yes** (per-match corners) |
| **D** | Non-market opinion | strength gap residualised on odds; crowd-vs-market disagreement | both | **yes** |
| **E** | True congestion | competitive matches in the last 14 days; days since last match | factor 1 | **yes** (see below) |
| **F** | Venue split & H2H depth | venue-specific PPG gap; H2H non-draw-HT rate | factor 1 | **yes** |

**Family E is genuinely exclusive and is backward-looking only.** The history blocks carry
FA Cup, League Cup, Champions League, Europa League, Conference League, Club World Cup and
friendly fixtures — competitions football-data.co.uk omits entirely, so its "rest days"
(dead at p = 0.77 in F10) measured only *league* gaps and is a different variable from
this one. Friendlies are excluded from the congestion count; competitive matches only.
The forward-looking half is **dropped** — see §9.

**Family G — totals — is a mandatory control in every model, never a discovery.** F10
established implied totals as the one live pre-match dial, so
`combined_recent_gf` and `h2h_avg_total_goals` enter on both sides of every comparison. A
new feature earns its place only *on top of* the totals control.

## 5. Models

| name | description |
|---|---|
| `baseline_constant` | dev-set base rate, applied flat |
| `baseline_chain_odds` | F12's construction: two Poisson regressions on 1H goals from the 1X2 price → Skellam over HT scorelines → × imported F11 completion. **This is the bar.** |
| `candidate_chain` | identical, with families A–G added to the factor-1 regressions. L2-regularised, feature count capped at 1 per 15 dev positives. |
| `factor2_probe` | imported F11 curve plus **one** family-B or family-C adjustment term, as a single-df hypothesis on 1,263 trailing states. Tested separately; never stacked with the above. |

Vig removal is proportional normalisation. Shin's method
(`notes/ESOTERIC_MODELS.md` #1) is a stretch item, not part of the preregistered test.

## 6. Evaluation protocol

- **Dev screening**: expanding-window round-wise walk-forward (train rounds ≤ k, predict
  round k+1, pooled across leagues). All tuning, family selection and hyperparameters are
  settled here.
- **Multiplicity**: six families ⇒ Holm correction at the family level on the dev screen.
  The number of tests run is reported alongside the results.
- **Metrics are reported at all three levels**, because their power differs by an order of
  magnitude: factor 1 (686 holdout trials at 61%), factor 2 (414 trials / 36 positives),
  product (686 / 36).

## 7. Success bars — both reported, separately and honestly

**Bar 1 — scientific (Brier).** The held-out *product* Brier must beat **both**
`baseline_constant` and `baseline_chain_odds`, with a paired bootstrap 95% CI on the
difference excluding zero, and decile calibration holding.

**Bar 2 — practical (slate lift).** Rank the holdout by predicted P(comeback). The slate's
observed comeback rate must have a Wilson 95% lower bound above the holdout base rate of
5.25%. Minimum detectable on this holdout:

| slate | n | comebacks needed | rate | lift | expected under null |
|---|---|---|---|---|---|
| top decile | 68 | ≥ 8 | 11.8% | 2.2× | 3.6 |
| **top quintile (primary)** | **137** | **≥ 13** | **9.5%** | **1.8×** | **7.2** |
| top third | 226 | ≥ 19 | 8.4% | 1.6× | 11.9 |

The two bars may disagree. Both outcomes are reported; neither is suppressed in favour of
the other.

## 8. Power statement — read this before interpreting any null

With **36 holdout comebacks**, the product-level test can detect only a *large* effect. A
null at the product level is **not** evidence of absence and must not be written up as a
replication of F12 — it is the expected outcome of a small holdout regardless of whether
signal exists.

The **factor-1 test is the well-powered one** (686 trials at a 61% rate) and is where a
real result can actually be demonstrated on this corpus. Three outcomes are anticipated,
and all three are publishable:

1. Factor 1 improves **and** the product clears Bar 1 → H1 supported; F12 overturned
   within this corpus, pending confirmation on more data.
2. Factor 1 improves, product CI inconclusive → "nowgoal features predict the half-time
   state better than the market does, but the gain is diluted by the completion stage."
   The honest next step is corpus expansion — a decision deliberately deferred to *after*
   this result.
3. Factor 1 does not improve → the price already contains the team-level information, and
   F12's verdict extends to the nowgoal feature set. A clean, well-powered negative.

## 9. Known data defects and quarantines

Established 2026-07-25, before modelling:

- **`home_next_fixture_days` is 100% empty; `away_next_fixture_days` is mislabelled.** The
  detail CSVs were scraped 2026-07-20 against a fixture parser that picked a non-fixture
  block for home and recorded *the home team's* countdown in the away column. The parser
  was rewritten 2026-07-22 and verified working against live pages on 2026-07-25, but the
  stored data predates the fix. **Both columns were quarantined**; Family E therefore ships
  backward-looking only. Re-deriving them costs a full ~2,058-page re-scrape and is not
  worth it for this study.

  **Update 2026-07-26:** the quarantine *mechanism* was removed from `qa/validate.py` —
  the validator no longer carries per-column exemptions, so it reports what is actually
  in the data. The modelling decision above is unchanged and remains the record of what
  Family E used. The consequence is that `uv run python -m qa.validate` now **exits 1 on
  the stored corpus**, failing all six league-seasons on this one column. That is the
  known defect described here, not new breakage; it clears when the detail files are
  re-scraped with the corrected parser.

  **Update 2026-09-20 — the re-scrape is now known to be sufficient, and was not before.**
  The 2026-07-25 entry recorded that the parser had been "verified working against live
  pages", but never established what the widget means on a *past* match, which is the
  case a re-scrape of 2023-26 actually depends on. Measured directly, three read-only
  detail renders:

  - current season (EPL 2026-27, round 4): `home_next_fixture_days=5`,
    `away_next_fixture_days=3` — both columns populate, and the away column is no longer
    carrying the home team's countdown;
  - **the widget is match-anchored, not today-anchored**: an EPL 2025-26 round-10 match
    (2025-11-01), re-rendered in September 2026, still reports 5 / 7 days, and its
    `last1` dates precede its own kickoff. This is the same anchoring property HANDOFF §4
    established for the history blocks, now confirmed for the fixture block;
  - a season-final match correctly reports `None` for both, which is the true value and
    stays far below the 95%-empty canary threshold.

  Consequence: a detail re-scrape restores both columns as **valid pre-match features**,
  clears the standing `qa.validate` exit-1, and un-quarantines the forward-looking half of
  Family E. "Not worth it for this study" stands for *this* study — the F12 re-test is
  closed and its record is fixed either way. It no longer applies to future work.

  **Decision 2026-09-20 (user): do not re-scrape now. Leave the defect standing.** The
  reasoning is that the fault is in the stored data only, the code is correct, and a
  wider re-scrape is certain to happen anyway — so an hour of renders spent on this
  corpus today buys nothing that the next scrape does not deliver for free. Until then:

  - `uv run python -m qa.validate` **exits 1 by design**, on this one column, on all six
    league-seasons. That is the expected state, not new breakage. Do not "fix" it in
    `qa/` — the canary is working correctly and must keep failing until the data changes.
  - `home_next_fixture_days` and `away_next_fixture_days` stay **unusable as features**.
    Family E remains backward-looking only, exactly as this section already specifies.
  - The defect clears on the next detail scrape with no code change. Re-verify by
    running `qa.validate` afterwards and confirming a clean exit 0.
- **`odds1x2_live_*` is cleared for use.** HANDOFF §5.1 warned these could be post-match
  in-play prices. Diagnostic over 2,058 matches: home-win Brier 0.2199 (initial) vs 0.2176
  (live), corr 0.963, mean implied shift 3.4pp — the signature of an ordinary pre-kickoff
  drift, not of a settled price. A post-match price would have driven Brier toward ~0.05.
  Re-verified per league in `modelling/experiment.py` as a standing regression test.
- All other `qa/validate.py` checks pass. At the time of writing this included
  cross-source reconciliation of every Premier League season against football-data.co.uk
  (scores, comeback counts, 7+ counts); that check was retired with the corpus on
  2026-07-26 — see `notes/MARKET_LINE_FINDINGS.md` §6.

## 10. Amendments

**A1 — 2026-07-25, before any model was fitted and before the holdout was opened.**
The §2 split sizes and the §7 slate table were computed on the raw corpus, but §4 also
preregisters a 5-round burn-in (rolling form does not exist in rounds 1–5). Applying the
burn-in that §4 already mandates removes 285 matches, so the *evaluation* sets are smaller
than the §2 table states. Corrected figures, and the slate thresholds recomputed against
them:

| split | matches | comebacks | base rate | HT non-draws |
|---|---|---|---|---|
| dev | 1,182 | 65 | 5.50% | 729 (61.7%) |
| holdout | 591 | 33 | 5.58% | 361 (61.1%) |

| slate | n | comebacks needed | rate | lift | expected under null |
|---|---|---|---|---|---|
| top decile | 59 | ≥ 7 | 11.9% | 2.1× | 3.3 |
| **top quintile (primary)** | **118** | **≥ 12** | **10.2%** | **1.8×** | **6.6** |
| top third | 195 | ≥ 18 | 9.2% | 1.7× | 10.9 |

Bar 2's Wilson lower bound is now measured against **5.58%**. Bar 1 is unchanged. The
burn-in is applied identically to every model including both baselines, so the comparison
is unaffected. This amendment is a mechanical consequence of a rule already preregistered
in §4, not a change of bar — and §8's power warning applies more strongly, not less: the
product-level test now rests on 33 holdout comebacks.

**A2 — 2026-07-25, before any model was fitted and before the holdout was opened.**
§5 caps `candidate_chain` at "1 feature per 15 dev positives" (⇒ 4 features). That cap was
written as if the model were fitted on comebacks, but the architecture §3 preregisters
fits factor 1 on **first-half goals** — 1,182 dev match observations, not 65 comebacks.
The 65 positives constrain nothing in factor 1, because no comeback label enters it; they
constrain only the final evaluation. Applying a comeback-sized cap to a goals-sized
regression is a straightforward specification error in this document.

Restated cap: **≥ 50 fitted observations per regressor.** The full candidate (16 family
features + 4 controls = 20 regressors on 1,182 observations ⇒ 59 per regressor) satisfies
it. To keep the original intent visible, a **restricted variant** limited to the
dev-screen's surviving families is reported alongside the full candidate as a sensitivity
analysis. L2 strength is tuned by walk-forward on dev only.

**A3 — 2026-07-25.** F11 publishes slopes but not its intercept, so factor 2 as specified
in §3 is under-determined. The intercept is recovered by n-weighted least squares against
**F4's published eight-octile table** — published numbers only, no data from this corpus.
Recovered value 0.9591 reproduces F4's octiles to a maximum error of 2.1pp and implies an
overall trail−1 completion rate of 11.0% against F11's published 11.1%. The "zero degrees
of freedom" claim in §3 therefore stands. Validated by `features/chain.py --replicate-f11`, which
is a hard gate: applied to this corpus's 1,090 trailing states the imported curve is
monotone across quartiles (0.4% → 6.6% → 12.0% → 17.5%) and predicts 8.8% against 9.0%
observed.

**A4 — 2026-07-26. Documentation-only: module paths, no statistical content.** The flat
top-level modules were reorganised into layered packages (`domain` → `scrapers` →
`features` → `modelling`, plus `qa`; a `core` package created in this change was collapsed
into `domain` later the same day); `constants.py` split into `scrapers/constants.py`
(DOM selectors) and `domain/columns.py` (CSV column order); `df.py` → `scrapers/csv_io.py`;
`features.py` → `features/engine.py`; `validate.py` → `qa/validate.py`. Every path
reference in this file and in the other `notes/` documents was updated to match. **No
feature definition, family list, bar, split, or measurement changed** — the refactor was a
file move plus import rewrite, and the CSV output schema was verified column-identical
(49 base columns, 501 detail columns, `Match.model_dump()` keys unchanged). Re-run after
the move, all four offline gates reproduce their previously recorded numbers exactly:
`qa.validate` all league-seasons PASS incl. cross-source; `features.engine --self-check`
1,600 comparisons / 0 mismatches; `modelling.scoreline --self-check --leak-check` PASS with
predictions bit-identical; `features.chain --replicate-f11` max absolute error 2.1%, 8.8%
predicted vs 9.0% observed. The holdout was **not** opened by this work.

**A5 — 2026-07-27. Data locations only: no statistical content.** The flat `data/`
directory was split by provenance — `data/raw/` holds scraper output
(`<league>_<season>.csv`, `_detail.csv`), `data/processed/` holds derived files
(`_enriched.csv`) — and directory/sibling-path construction was consolidated into the new
`domain/paths.py`, which is now the only module that names a data directory; five modules
had each carried their own `DATA_DIR = "data"`. The base+detail
join moved from `scrapers/detail.py:_write_enriched` to the new `features/enrich.py`, run as
a third pipeline step, so no scraper writes a derived file. `scripts/backfill_round_index.py`
was deleted, its A4-era migration having been applied.

**No feature definition, family list, bar, split, or measurement changed.** The join is
byte-identical: an enriched file was copied aside before the move and `diff` against the
rebuild by `features/enrich.py` reported no difference. All four offline gates reproduce
their recorded numbers: `qa.validate` — 12/12 base+joins subjects PASS across the two
directories, the 6 detail subjects still FAIL on the known-stale `home_next_fixture_days`
canary (§9) and the run still exits 1; `features.engine --self-check` 1,600 comparisons /
0 mismatches; `modelling.scoreline --self-check --leak-check` PASS with predictions
bit-identical; `features.chain --replicate-f11` 8.8% predicted vs 9.0% observed. Earlier
`notes/` documents naming a CSV directly under `data/` (e.g. §2's corpus,
`data/*_enriched.csv`) refer to the same file one level deeper — `data/processed/` for
enriched, `data/raw/` otherwise; the findings are unaffected. The holdout was **not**
opened by this work.

**A6 — 2026-09-20. Code hygiene: no statistical content.** `modelling/analysis.py` was
deleted (self-marked SUPERSEDED on 2026-07-25, committed in `6643b1f`; its `wilson_ci`
and `required_n` already live in `modelling/experiment.py`). Three functions over the
cognitive-complexity threshold were refactored with no change of behaviour:
`ScorelineModel.predict` (35) split into `_second_half_joint` and a `_Totals`
accumulator with the grid geometry hoisted to module scope; `qa/league.py`'s
`_check_round_index` (20) split into the four assertions its own docstring already
enumerated; and `detail_parsers.py`'s `aggregate_form` / `_flatten_one` (16 each) now
share one `_outcome` helper instead of two copies of the same W/D/L branch.

**No feature definition, family list, bar, split, or measurement changed.** The scoreline
model's predictions are **bit-identical** across the refactor, verified by hashing the
seven output columns over all 1,773 post-burn-in matches before and after
(sha256 `a154deb6c3e82798b03909191068adee20c4e55b15e230e2d91a7263a4751e6a`, unchanged).
All offline gates reproduce their recorded numbers: `qa.validate` 12/12 base+joins PASS,
the 6 detail subjects still FAIL on the §9 canary and the run still exits 1;
`features.engine --self-check` 1,600 comparisons / 0 mismatches;
`modelling.scoreline --self-check --leak-check` PASS; `features.chain --replicate-f11`
max absolute error 2.1%, 8.8% predicted vs 9.0% observed. The holdout was **not** opened
by this work.

**A7 — 2026-09-20. Provenance: the holdout raw transcript is lost.**
`modelling/experiment.py` writes its holdout transcript to
`notes/results_holdout_raw.txt`, and `notes/RESULTS.md` §2 quotes it. That file is not in
the repo and is not recoverable — the filter study's equivalent
(`notes/filter_study_raw.txt`) survives, this one does not.

**It must not be regenerated.** `--holdout` re-opens the 2025-26 season, and §2 permits
exactly one opening; re-running it to recover a transcript would spend the protocol's
scarcest resource on a bookkeeping repair. The figures quoted in `RESULTS.md` §2 stand as
the record of that single run. Anyone re-deriving them is running a *second* opening and
must say so.
