# The reliability screen — 2026-09-23

**Status: exploratory, not preregistered.** Everything here was measured while designing the
card/substitution features, on one league-season, after the fact. Nothing in it is a claim
against `notes/PREREGISTRATION.md`, and the outcome-facing numbers in §4 come from roughly
seventeen uncorrected comparisons. What *is* reusable is the screen in §1: it is a pre-test,
not a result, and it costs no outcome data.

> **§4 touched the holdout season and §1 did not.** The league-season measured here is
> English Premier League 2025-2026, which `features/engine.py:TEST_SEASONS` designates as
> the holdout. §1's reliability numbers use **no outcome column** — they are within-team
> stability — and neither does §5's mixture table, so both are clean. §4 conditions
> `is_comeback`, and is therefore a look at holdout labels. Disclosed and bounded in
> `PREREGISTRATION.md` **A8 §4**: claim 15 is evaluated with this stratum excluded. Do not
> quote §4 as support for a result computed on a corpus that includes it.

---

## 1. The screen

**Before testing a history-block feature against any outcome, measure whether it is a stable
property of a team at the depth the feature actually has.** A feature built from six matches
that does not persist across six matches is noise, and no amount of mechanism upstream of it
can fix that.

Method used here:

1. Take every team-match in the corpus (380 matches × 2 sides = 760, 20 teams, ~38 each).
2. Order each team's matches by date and split them odd/even into two disjoint halves.
3. Compute the candidate trait separately on each half.
4. Correlate the two halves across the 20 teams → **split-half r**.
5. Spearman-Brown up to the full 38 matches, invert to a single match, then forward to the
   depth the feature really has: `MATCHES_PER_SECTION = 6`.

Step 5 matters. A trait can look respectable at 19 matches and be worthless at 6, which is
the only depth `features/history.py` ever reads.

The screen needs **no outcome column**, so it spends no Holm budget and cannot be p-hacked.
Run it first; it is the cheapest way to not build something.

## 2. Results

| candidate | split-half r | r @ 38 | **r @ 6 matches** | verdict |
|---|---|---|---|---|
| yellows per match | 0.570 | 0.726 | **0.295** | — (already built) |
| **yellows while leading, per match** | 0.564 | 0.721 | **0.290** | **built** |
| minutes spent trailing | 0.463 | 0.633 | 0.214 | rejected, §3 |
| subs while trailing, per minute | 0.377 | 0.548 | 0.160 | not built |
| yellows while leading, per *minute* | 0.345 | 0.512 | 0.142 | rejected, §3 |
| first sub minute (unconditioned) | 0.283 | 0.441 | 0.111 | kept as-is, §3 |
| **first sub minute when trailing** | **-0.004** | -0.008 | **0.000** | **rejected, §3** |

Read the last column as an upper bound on usefulness: a feature with reliability *r* attenuates
its true correlation with anything by `sqrt(r)`. At 0.29 the best candidate here loses ~46% of
whatever signal exists, and the true correlations in this domain are already tiny
(`BEHAVIOURAL_RESULTS.md` measured +0.004 against HT-decisive).

## 3. Decisions taken

**Built: `yellows_while_leading_avg`** (3 columns, one per history section). Conditioning on
the scoreline costs almost nothing — 0.564 against 0.570 unconditioned — and it has a live
mechanism behind it (§4). It is the only state-conditioned event aggregate in the repo.

**Not built: a trailing-conditioned first-substitution minute.** Split-half **-0.004**. This is
the important negative: it was the obvious fix for a feature we knew was confounded, and it
does not exist as a team trait. Managers have no stable "how fast I react when behind".

Note the shape of it: *subs while trailing per minute* holds 0.377 while the **timing** is zero.
Teams differ in how many changes they make while behind, not in how early.

**`first_sub_minute_avg` stays unconditioned and is not a candidate.** It correlates **0.428**
with the quantity `features/events.py` used to claim it measured, so it is not a noisy version
of that quantity — it is largely a different one. But the honest version is noise, so there is
no version of this feature worth having. Do not "fix" it by conditioning it.

**Rejected: per-minute exposure denominators.** Dividing yellows-while-leading by minutes spent
leading drops reliability 0.564 → 0.345. Normalising by exposure adds noise faster than meaning
at this sample size.

**Rejected: `minutes spent trailing` as a feature.** r = **-0.925** with points per game
(R² = 0.86). It is team strength wearing a hat, and the corpus already carries strength columns.

## 4. Mechanism evidence (exploratory, uncorrected)

Measured on 1,397 matches with known HT and FT scores — the corpus plus every match its history
blocks reference, scored via `qa/validate.py:_goal_truth`. Base rates: comeback 6.30%,
HT-decisive 62.85%, completion given HT-decisive 10.02%.

**Yellows to the half-time leader in the second half, against completion rate:**

| 2H yellows to HT-leader | completion | 95% CI |
|---|---|---|
| 0 | 6.39% | [4.03, 10.00] |
| 1 | 9.64% | [6.71, 13.67] |
| 2+ | 13.25% | [10.02, 17.32] |

2×3 χ² p = 0.020. Two controls, both null, which is what makes it interesting:

- **chaser's** 2H yellows (busy-match control): p = 0.357
- HT-leader's **1st-half** yellows (team/referee trait control): p = 0.575

The effect is specific to *leader* × *second half*. It reads as a siege thermometer rather than
a discipline trait. **p = 0.020 does not survive Holm over ~17 comparisons** (0.34); the pattern
of one hit plus two clean controls is the persuasive part, not the p-value.

**Red cards — a reverse-causation trap, kept here as a warning.** Standalone the effect looks
enormous:

```
completion | HT-leader sent off in 2H    39.13%  (9/23)   vs  9.24%   -> 4.2x
```

Joining it to the goal timeline dissolves most of it. Of the 8 completions, **5 had the red
card arrive *after* the equaliser** — the comeback caused the red, not the reverse. Restricted
to properly ordered cases: **17.65%, CI [6.19, 41.03], n = 17**, overlapping the baseline.

**Any event-based claim in this project needs an ordering check against the goal timeline.**
Events are downstream of the scoreline as often as they are upstream of it.

**Substitutions — a well-powered null.** The chasing side's first second-half substitution:
57.1' when the comeback landed, 57.6' when it did not, n = 876, and flat across buckets
(10.83% / 8.60% / 10.32% for 46-59' / 60-69' / 70-120'). The mechanism is absent even with
perfect in-play knowledge, which is the prior that made the §3 rejection unsurprising.

## 5. Why the event timelines were split

Measured over 5,993 populated combined-timeline cells: 12.1 entries and 62 characters each,
of which substitutions were 68.1% of entries, yellows 31.3% and red cards **0.6%**. The rarest
and most mechanically interesting event was buried behind the most common one.

Split into `yellow_timeline` / `red_timeline` / `sub_timeline`, with the kind implied by the
column. Lossless: all 6,840 cells were re-derived from the old combined strings with zero
mismatches. The two reasons not to go further and merge goals in as well:

- **5.0% of history slots** have a usable event timeline but no usable goal timeline (goals
  must reconcile against the block's own score; cards have nothing to reconcile against), so
  one string would force a wrong usability rule on one slot in twenty.
- the goals would be stored four times over.

**1.19% of events** share an exact minute and stoppage with a goal, so re-merging by minute is
ambiguous for those; the raw stores keep `event_index` if the order is ever needed.

## 6. Caveats

- **n = 20 teams.** The CI on r = 0.57 is roughly [0.17, 0.81]. These are wide.
- One league-season, one competition, one country. The multi-country scrape in
  `notes/RETRY_CANDIDATES_2026-09-23.md` would tighten every number here.
- "-0.004" means *indistinguishable from zero and certainly not large*, not exactly zero.
- §4 is in-play and descriptive. It says a mechanism exists; it does not say a pre-match team
  trait built from it will work. Those remain Tier-3 instruments under the closed 14-claim list.

## 7. Reproduction

The §1 screen and the §4 measurements were run as throwaway scripts against
`data/raw/goals.csv`, `data/raw/events.csv`, `data/raw/events_done.csv` and the base league
CSVs, using `qa/validate.py:_goal_truth` for the scores and
`modelling/experiment.py:wilson_ci` for the intervals. They are not committed — the screen is
cheap to re-derive and pinning it as a module would imply a stability the n = 20 does not have.
The §5 split verification is reproducible at any time by rebuilding with `features.enrich` and
re-deriving the three kind timelines from a saved combined one.
