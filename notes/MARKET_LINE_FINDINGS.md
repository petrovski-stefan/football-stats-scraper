# FINDINGS — the market goal line beats every in-house feature, and clears F12's bar

**Written 2026-07-26, on the football-data.co.uk corpus immediately before that corpus was
retired from the repo (§5 records how to re-fetch it byte-for-byte).**

**Status: EXPLORATORY. Not a preregistered result.** §4 is explicit about what would be
required to promote it. Read §4 before quoting the 1.33× anywhere.

Companions: `notes/LEAGUE_STUDY.md` (the study this corpus was originally built for),
`notes/RESULTS.md` (the six nowgoal families that died), `notes/FILTER_RESULTS.md` (the
exclusion filter that died), `notes/PLAN_2026-07-25_environment_filter.md` (the plan these
measurements re-prioritise).

---

## 1. Why this was measured

`PLAN_2026-07-25` decided to **collect the Over/Under line** and justified a 6–10 hour
25-league scrape on the reasoning in its "Honest expectation". Quoting that document as it
stood on 2026-07-25 (the O/U item was removed from it on 2026-09-23, once the line was
actually being collected):

> Three things could move it, in descending plausibility: **the O/U line** (the market
> prices the goal environment better than our features do), **sample size** (25,000 matches
> resolves an AUC difference 591 cannot), and **league diversity**.

All three were already available in `football-data-co-uk/`, which held 23,127 matches with
the O/U line at **100% coverage** (closing) and 99.8% (opening). The plan proposed scraping
for a column that was already on disk, so it was measured first.

## 2. What the market line predicts

Dev seasons only (2023-24 + 2024-25, 22 divisions, **n = 15,475**). 2025-26 was deliberately
**not** read, preserving it as an untouched holdout. Vig stripped two-way:
`p_over = (1/over) / (1/over + 1/under)`. Bootstrap 95% CIs, 400 resamples.

| target | base | nowgoal features (n=591) | B365 **opening** O/U 2.5 | B365 closing O/U 2.5 |
|---|---|---|---|---|
| HT decisive | 59.4% | 0.522 | 0.562 | 0.561 |
| FT decisive | 73.8% | 0.519 (market draw price 0.544) | 0.560 | 0.559 |
| total ≥ 3 | 52.0% | 0.545 | **0.602** [0.594, 0.611] | 0.610 [0.603, 0.619] |
| environment (all three) | 33.0% | **0.497** | **0.592** [0.583, 0.601] | 0.598 [0.589, 0.606] |
| comeback | 5.3% | 0.496 | **0.552** [0.532, 0.571] | 0.548 [0.527, 0.570] |

Three things this settles:

1. **The plan's first hypothesis was correct.** `PLAN_2026-07-25` §1 measured the
   environment conjunction at AUC 0.497 and concluded "multiplying three weak signals
   yields noise." That was a statement about *our* features, not about the target. A single
   market column reaches 0.592 on the same conjunction.
2. **It is not a closing-line artifact.** The opening price performs within noise of the
   closing price on every target, so the signal is available at the time a pre-match
   prediction would actually be made.
3. **The market's goal forecast beats ours.** `FILTER_RESULTS.md` reached AUC 0.559
   forecasting the goal total in-house; the opening O/U line reaches 0.602.

**Negative control that validates the pipeline:** `|Asian handicap line|` (match mismatch)
predicts comeback at **0.502 [0.483, 0.521]** — dead, CI straddling 0.5. This independently
reconfirms `LEAGUE_STUDY.md` F-series refutation of the balanced-match precondition, on the
same corpus, via a different instrument. The same column *does* predict decisiveness
(HT decisive 0.563, total≥3 0.555), which is the expected direction and confirms the
column is being read correctly.

## 3. The plan's Phase 3 bar, measured out-of-sample

Two features only — opening O/U 2.5 vig-free probability and `|AHh|`. Logistic regression,
**fit on 2023-24, tested on 2024-25**. Test n = 7,675, base rate 5.16%.
Bar (`PLAN_2026-07-25` §2): keep the top 20%; that slate's Wilson 95% lower bound must
exceed the pooled base rate.

| keep top | n | comebacks | rate | lift | Wilson 95% LB | verdict |
|---|---|---|---|---|---|---|
| 5% | 383 | 30 | 7.83% | 1.52× | 5.54% | PASS |
| 10% | 767 | 57 | 7.43% | 1.44× | 5.78% | PASS |
| **20% (the bar)** | **1,535** | **105** | **6.84%** | **1.33×** | **5.68%** | **PASS** |
| 30% | 2,302 | 148 | 6.43% | 1.25× | 5.50% | PASS |
| 40% | 3,070 | 194 | 6.32% | 1.22× | 5.51% | PASS |
| 50% | 3,837 | 239 | 6.23% | 1.21× | 5.51% | PASS |
| 65% | 4,988 | 287 | 5.75% | 1.12× | 5.14% | fail |

**Headroom recovered ≈ 15%** — (6.84 − 5.16) / (16.03 − 5.16), against the 2.89× oracle
ceiling in `PLAN_2026-07-25` §1. That is the same order as `FILTER_RESULTS.md`'s ~15%, so
this is not a large effect; it is a *sufficient* one, because the plan's own bar needed
~1.2× and stated "even a 1.2× lift clears it decisively."

The monotone decay from 1.52× at 5% coverage to 1.12× at 65% is the shape a real ranking
produces. `PLAN_2026-07-25` §1 recorded the opposite for the in-house model: "Ranking by
predicted environment and keeping the top 20% gave a kept set 35.6% environment vs 35.0%
corpus-wide — zero enrichment."

## 4. Why this is not yet a finding

This was **one exploratory fit on a corpus `LEAGUE_STUDY.md` had already mined**, which is
precisely the winner's-curse situation `notes/PREREGISTRATION.md` exists to prevent. To
promote it, the protocol in `PREREGISTRATION.md` requires:

- a **closed feature list** fixed in writing before fitting (candidates: vig-free
  `p_over` opening, `|AHh|`, and the vig-free 1X2 draw price — nothing else);
- **leave-one-league-out** in addition to walk-forward, since the claim is that the ranking
  generalises across leagues — `PLAN_2026-07-25` Phase 2 requires both splits;
- **one opening of the 2025-26 holdout**, which §2 above deliberately preserved;
- Holm correction across whatever family count the preregistration declares.

Until those run, the honest statement is: *a two-column market model plausibly clears F12's
slate bar, measured once, out-of-sample, on 7,675 matches.*

## 5. Re-fetching this corpus

The data was retired from the repo on 2026-07-26 (11 MB, gitignored, single consumer). All
three seasons are **complete** (latest fixture dates 26/05/2024, 25/05/2025, 31/05/2026), so
a re-download reproduces the same files — nothing here depends on a live snapshot.

Source: `https://www.football-data.co.uk/mmz4281/<SEASON>/<DIV>.csv`, where `<SEASON>` is
`2324`, `2425`, `2526` and `<DIV>` is one of the codes below. The on-disk layout was
`football-data-co-uk/<country>/<YYYY-YYYY>/<DIV>.csv`, which is what
`qa/validate.py:FD_SOURCES` expected.

| country | codes | matches (3 seasons) |
|---|---|---|
| belgium | B1 | 935 |
| england | E0, E1, E2, E3 | 6,108 |
| france | F1, F2 | 1,909 |
| germany | D1, D2 | 1,836 |
| greece | G1 | 709 |
| italy | I1, I2 | 2,280 |
| netherlands | N1 | 918 |
| portugal | P1 | 918 |
| scotland | SC0, SC1, SC2, SC3 | 2,304 |
| spain | SP1, SP2 | 2,526 |
| turkey | T1 | 1,028 |
| **total** | **21 divisions** | **21,471** |

One division (1,656 matches over the 3 seasons) was removed from this table on 2026-10-08, at
the user's request. Every result in these notes was measured on all 22 divisions, 23,127 matches.

Columns this study used: `FTHG FTAG HTHG HTAG` (targets), `B365>2.5 B365<2.5` (opening O/U),
`B365C>2.5 B365C<2.5` / `PC>2.5 PC<2.5` (closing O/U, Bet365 and Pinnacle), `AHh` / `AHCh`
(Asian handicap line). Files also carry shots, shots on target, corners, fouls and cards,
none of which were used here.

## 6. What retiring it cost

- `qa/validate.py`'s cross-source check against football-data was **removed** in the same
  change, rather than left to degrade silently to `[SKIP]`. It had only ever covered
  `english_premier_league` (3 of 6 league-seasons) while presenting as general coverage —
  the specific "noise" complaint that prompted the retirement. Internal self-consistency
  checks are unaffected and still run on every league-season.
- **Nothing else in code touched these files.** `features/chain.py`'s F11 completion curve
  is hardcoded published coefficients — `--replicate-f11` validates against F4's published
  octile table and applies the curve to the *nowgoal* corpus, so it still passes with the
  data gone.
- `LEAGUE_STUDY.md`'s 23,127-match measurements are no longer reproducible from the repo
  alone. They remain reproducible via §5.

## 7. Consequence for the plan

`PLAN_2026-07-25` treats the corpus scrape as the prerequisite for testing the environment
hypothesis. §3 above inverts that: the hypothesis has been provisionally validated without
scraping anything, so the scrape's purpose changes.

- **Collecting the O/U line was the first consequence** — needed as a nowgoal capability,
  since the ~30 unsurveyed countries have no football-data equivalent. Built 2026-09-23.
- **The preregistered study should be run per §4 before the scrape**, not after.
  A confirmatory pass needs a re-fetch (§5) and costs hours, not the 6–10 hour scrape.
- **The scrape's remaining unique value is coverage**: whether a market-line ranking that
  works across 22 divisions in 11 countries still works in the unsurveyed ~30, which is the
  project goal and the one question football-data structurally cannot answer.
