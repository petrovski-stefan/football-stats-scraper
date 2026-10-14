# PLAN — the next direction, captured before it was lost

**Written 2026-09-20. Trimmed 2026-09-23: the goal-timing scrape and the Over/Under line
were both built, so their sections were removed. What remains is what is still open or
still a finding.**

Status: **§1 out-of-round — disambiguated, tested, refuted.** **§2 prospective gut log —
recommended, not decided.** The one question still open across the whole document is the
picks-per-week number in §2.

> **Errata, 2026-10-11** (`notes/IDEAS_2026-10-01.md` idea 13; the text below is not edited):
>
> 1. **§1's refutation does not stand.** Its ordinal flag never checks that the match itself
>    was moved. When one later-round match is brought forward, every match played after it
>    is flagged. Recomputed on the 4 of its 6 seasons still held (kickoffs and rounds only),
>    the flag gives exactly §1's counts (32, 41, 5, 11), and 70 of those 89 matches were
>    played within 5 days of their round's median kickoff: 30 of 32 and 40 of 41 in the EPL,
>    0 of 16 in the Ekstraklasa. So at most 41 of the 111 were rescheduled matches. The claim
>    is reopened (`notes/STATE.md`). `s3_is_rescheduled` (S3.10) flags a match by its own
>    distance from its round's median.
> 2. **§3's T4 most likely did not measure Mondays.** Its script was not kept; survey claim
>    #6, which copies its definition, reads `is_monday` as stored, and the stored flag was
>    computed on the UTC+8 `date`: a stored "Monday" ran from Sunday 16:00 to Monday 16:00
>    UTC. In the 4 seasons still held, 96 of the 103 stored Mondays were Sundays locally, and
>    94 of the 101 real Mondays were stored as Tuesdays. The midweek half was mixed too: 108
>    of 202 stored midweek matches were midweek locally. (The counts alone cannot show which
>    flag T4 read: 103 stored Mondays against 101 real ones.)

Companions: `notes/BEHAVIOURAL_RESULTS.md`, `notes/FILTER_RESULTS.md`, `notes/RESULTS.md`,
`notes/PLAN_2026-07-25_environment_filter.md`,
`notes/RETRY_CANDIDATES_2026-09-23.md`, and the user's own
`Proprietary_Filter_Explanation_v2.md` (kept outside the repo, on the Desktop; written
~March 2026, not updated since).

---

## 0. Where the project stands, in one paragraph

Target is still **comeback**, still **pre-match only**. Every articulated feature tested
so far measures at roughly 1.0x lift: six nowgoal families (`RESULTS.md`), the exclusion
filter (`FILTER_RESULTS.md`), the behavioural candidate rule (`BEHAVIOURAL_RESULTS.md`,
0.88x), and four more claims tested on 2026-09-20 (§3 below, all dead after Holm).

---

## 1. "Match out of round played" — DISAMBIGUATED AND REFUTED

**Status: TESTED 2026-09-20. Dead, and this one was properly powered.**

### The definition, from the user

> Match A was first scheduled in round X. It was rescheduled. Match A is still
> technically from round X, but it kicks off *after* round Y (Y > X) has already started.
> That is an out-of-round match.

This is an **ordinal** definition — "a later round has already begun" — not the
"days away from the round's centre" proxy measured earlier that evening. It is sharper,
and it catches more: 111 matches rather than 41.

The user also supplied a mechanism and a direction:

- **Mechanism: isolation.** The match stands alone, with no other results around it, so it
  carries a different psychological frame.
- **Direction: exclusion.** *"I never seen out of round match go comeback"* — the claim is
  that these matches produce **fewer** comebacks and should be filtered out.

### The measurement

Corpus n = 2,058, base 5.54%. Out-of-round by the definition above: **111 matches (5.39%)**.

| | n | comebacks | rate | lift | 95% CI |
|---|---|---|---|---|---|
| **out of round** | **111** | **6** | **5.41%** | **0.98x** | [2.50%, 11.29%] |
| in round | 1,947 | 108 | 5.55% | 1.00x | [4.62%, 6.65%] |

Expected under the null: 6.1 comebacks. Observed: 6. One-sided p (fewer) = **0.582**.

Per league-season, so the 6 are visible:

| league | season | out-of-round | comebacks |
|---|---|---|---|
| English PL | 2023-2024 | 13 | 1 |
| English PL | 2024-2025 | 32 | 2 |
| English PL | 2025-2026 | 41 | 1 |
| Ekstraklasa | 2023-2024 | 9 | 1 |
| Ekstraklasa | 2024-2025 | 5 | 1 |
| Ekstraklasa | 2025-2026 | 11 | 0 |

**This test had real power, unlike the other four.** If the strong claim were true and
out-of-round matches produced zero comebacks, this corpus would have shown it:
P(0 comebacks | n = 111, base 5.54%) = **0.002**. We did not observe 0. We observed 6,
against 6.1 expected. The strong form is refuted on evidence, not on a shrug.

Secondary cut, pointing the *opposite* way to the claim (not significant): matches with
**two or more** later rounds already started run 3 of 37 = 8.11%, lift 1.46x.

### The stated mechanism also shows nothing

Isolation proxy — other matches in the same league kicking off within +/- 12 hours:

| neighbours | n | rate | lift |
|---|---|---|---|
| 0 (alone) | 211 | 6.16% | 1.11x |
| 1-2 | 859 | 4.54% | 0.82x |
| 3+ | 988 | 6.28% | 1.13x |

Non-monotone, and the isolated bucket points *up*, not down. 35 matches are both
out-of-round and alone.

### How the belief formed — and why it was reasonable

"I never seen out of round match go comeback" is entirely consistent with the base rate,
and the arithmetic shows why. At 5.41%:

- you must watch **12.2** out-of-round matches for a coin-flip chance of witnessing one;
- P(seeing zero in 20 such matches) = **0.32**;
- P(seeing zero in 40 such matches) = **0.10**.

Out-of-round matches are ~5% of fixtures, and a manual workflow only inspects its own
picks. Going years without seeing one is the *expected* experience under a plain base
rate. This is the rare-event power trap `HANDOFF` §6 warns about, encountered from the
observer's side rather than the analyst's.

### What survives

Nothing of the exclusion claim. Two notes for later:

1. The **ordinal out-of-round flag is cheap and already derivable** from stored `round`
   and `date` — no new scraping. If the corpus ever reaches the multi-league scale, it
   costs nothing to recompute as a by-product.
2. The `>= 2 later rounds` cut (1.46x, n = 37) is the only cell pointing anywhere. It is
   37 matches and should not be chased on this corpus.

## 2. Still open — the prospective gut log

In progress, and easy to lose. `Proprietary_Filter_Explanation_v2.md` concludes that the
core filter **cannot be encoded**. It lists four things under "What Cannot Be Encoded": the
matchup-combination trigger, the odds pattern, the weight system and the 2-3 second
instant. So **it cannot be backfilled onto historical matches**. The only valid instrument
is a prospective log. This is the same structural problem as the web-search features of
`HANDOFF` §5.4.

Statistically, that is the **cleanest test this project can run**: k = 1, no formula
selection, no winner's curse and zero contamination. It needs 11 hits per 100 picks. The
schema at the end of the user's own document is already the correct one.

**Blocked on one number: picks per week.**

| picks/week | picks per season | verdict |
|---|---|---|
| ~1 (the Mode 2 rate) | ~25 | 1.4 expected hits. Unmeasurable; needs 4+ seasons |
| 4 | ~100 | **one season, fully powered.** Needs 11 hits |
| 8 | ~200 | one season, needs 18. Tighter CI |

The 2026-27 season is live. It was on **round 5** on 2026-09-20. It is a really untouched
holdout, which this project has not had since 2025-26 was opened three times.

---

## 3. Measurements made 2026-09-20, so they are not lost

### Four claims from `Proprietary_Filter_Explanation_v2.md`, tested

> **Dropped, 2026-10-13:** T1, T2 and T3 left the project with the other rerun claims; their
> text is deleted. T4 stays.

Exploratory, one family, Holm-corrected. Corpus n = 2,058, 114 comebacks, base 5.54%.
**All four dead.**

```
T4_monday_midweek    raw p=0.297  Holm p=0.891  dead
```

**T4 — Monday / midweek.** Monday 2.90% (n=138, **4 comebacks**, lift 0.52x); midweek
**5.70%** (lift 1.03x); rest of week 5.73%. The combined claim is half wrong — midweek
shows zero suppression. Calling the Monday effect needs 444 Monday matches; 138 available.

### Why per-league A/B testing was rejected

Proposed: run candidate formulas one at a time on each isolated league, "since every
league is different". This **multiplies** the multiplicity rather than removing it —
k formulas x L leagues tests, each on a smaller, noisier sample.

Best result under a **pure null**, top-100 slate, simulated 200,000 times:

| tests (k x L) | mean best | apparent lift |
|---|---|---|
| 1 (1 x 1) | 5.53 | 1.00x |
| 10 (5 x 2) | 9.27 | 1.67x |
| 50 (5 x 10) | 11.23 | 2.03x |
| **100 (5 x 20)** | **11.98** | **2.16x** |

The significance bar is 11 hits per 100. At 5 formulas across 20 leagues the *expected*
best under pure noise is 12.0 — **selection alone clears the bar every time.**

Hits needed to beat the base rate on a top-100 slate:

| | pool | base | need |
|---|---|---|---|
| pooled | 2,058 | 5.54% | 11 / 100 |
| English PL only | 1,140 | 6.67% | 12 / 100 |
| Ekstraklasa only | 918 | 4.14% | 9 / 100 |

**Agreed alternative: leave-one-league-out**, already mandated by
`PLAN_2026-07-25_environment_filter.md` Phase 2 — choose the formula on leagues 1..L-1,
test on league L, rotate. `RETRY_CANDIDATES_2026-09-23.md` §1 then measured the stratified
version and settled it: league goes in as a **Mantel-Haenszel stratum inside one pooled
test**, not as a per-league split.

---

## 4. What to decide first, when this is picked up

1. **The picks-per-week number.** It is still not answered. The prospective log cannot
   start without it. That log is the only instrument that can read the core of the filter,
   which cannot be encoded.
2. ~~Reading A or B for idea 2~~ — **resolved and closed 2026-09-20.** See §1.
