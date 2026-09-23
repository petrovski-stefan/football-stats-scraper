# PLAN — the next direction, captured before it was lost

**Written 2026-09-20. Status: PARKED — nothing scraped, nothing implemented.**
Captured at the end of a session in which the project's direction changed. Three ideas.
Each carries the measurements already made, so none of them has to be re-derived.

Status by idea: **§1 goal timings — scoped, deferred to the next bulk scrape.**
**§2 out-of-round — disambiguated, tested, refuted.** **§3 O/U line — recommended, not
decided.** The one question still open across the whole document is the picks-per-week
number in §3.

Companions: `notes/BEHAVIOURAL_RESULTS.md`, `notes/FILTER_RESULTS.md`, `notes/RESULTS.md`,
`notes/MARKET_LINE_FINDINGS.md`, `notes/PLAN_2026-07-25_environment_filter.md`, and the
user's own `Proprietary_Filter_Explanation_v2.md` (kept outside the repo, on the Desktop;
written ~March 2026, not updated since).

---

## 0. Where the project stands, in one paragraph

Target is still **comeback**, still **pre-match only**. Every articulated feature tested
so far measures at roughly 1.0x lift: six nowgoal families (`RESULTS.md`), the exclusion
filter (`FILTER_RESULTS.md`), the behavioural candidate rule (`BEHAVIOURAL_RESULTS.md`,
0.88x), and four more claims tested today (§4 below, all dead after Holm). The one thing
that has ever beaten the base rate is the **bookmaker's Over/Under 2.5 line**
(`MARKET_LINE_FINDINGS.md`, exploratory), and the pipeline still does not collect it.

---

## 1. Idea 1 — scrape goal timings

**Status: verified scrapeable, not designed, not built.**

### What was verified on 2026-09-20 (read-only, 3 page renders)

Goal minutes are **not** on the h2h detail page the pipeline already scrapes. They are on
a different URL: `https://live10.nowgoal26.com/match/live-<match_id>`.

Rendered event rows, sample (Brighton 0-3 Man Utd, match 2789499):

```
33'  0 - 1  P.Dorgu       (Assist: Fernandes B.)     img 1.png  = goal
44'  0 - 2  Mbeumo B.     (Assist: Diallo A.)
48'  0 - 3  Fernandes B.  (Assist: P.Dorgu)
45+2'       Mainoo K.                                img 3.png  = yellow card
50'         P.Dorgu (Goal awarded)                   img 14.png
```

Structure: minute lives in `b.score` inside a `td`, inside a `tr` of a three-column table
(home cell | minute | away cell). Available per event:

- **minute, including stoppage time** (`45+2'`);
- **the running score** (`0 - 1`, `0 - 2`) — which identifies the scoring side with no
  ambiguity, and is more robust than reading the left/right column position;
- scorer and assist;
- event kind by icon filename: `1.png` goal, `3.png` yellow, `4/5/11.png` substitution,
  `14.png` goal awarded. **Not yet confirmed:** penalty, own goal, red card, VAR
  disallowed.

**Cost: +1 page render per match**, on top of the existing detail render. Re-scraping the
current 2,058-match corpus is roughly another hour at `WORKERS = 4`.

### Proposed storage (not agreed)

A new **long-format** file, one row per goal — *not* new columns on the 501-column detail
CSV:

```
data/raw/<league>_<season>_goals.csv
match_id, minute, stoppage, side, home_score_after, away_score_after, scorer, assist, kind
```

Rationale: a 7-goal match is 7 rows rather than 40 mostly-empty columns; it respects the
`scrapers/` writes raw, `features/` derives split; and it gives `qa/` a real cross-file
check it currently lacks — goals in the file must reconcile to `ft_home_goals` /
`ft_away_goals` in the base CSV.

Derived per-match and rolling as-of-round features would then live in
`features/engine.py` alongside the existing ones.

### Honest prior

Goal timing is **genuinely untested** — it is in no graveyard. football-data.co.uk has no
minutes, so `LEAGUE_STUDY` never saw it, and it was not among the six families in
`RESULTS.md`. `HANDOFF` §9 item 7 listed it as a nice-to-have and nobody ever did it.

But it is the *next* team-trait feature after the one that just died.
`BEHAVIOURAL_RESULTS` used half-splits and scored corr **+0.004** against HT-decisive.
What timing buys that nothing else does: **within-half resolution** (a team that concedes
in minutes 40-45 specifically manufactures half-time deficits) and **lead-survival
hazards**, which `ESOTERIC_MODELS.md` flags as an unused tool. That is a different
construct from "2H goal-difference average", which died as family B.

### Answered by the user, 2026-09-20 (same evening)

1. **What to capture: minute + which team's score incremented. Nothing else.** Own goals
   are attributed to the team whose score went up, exactly as the running score shows it.
   No scorer, no assist, no event taxonomy. This simplifies the scrape substantially — the
   running-score column alone carries both facts, so parsing reduces to reading the
   `b.score` minute and the `N - M` score text per goal row.
2. **Do NOT re-scrape the existing 2,058 matches — "no for now".** Consistent with the
   2026-09-20 decision on the stale fixture columns (`PREREGISTRATION.md` §9): scraping
   will be re-run in bulk later, and goal timings ride along with it.
3. **Cups and European matches: out of scope — "no for now".** League matches only.

**Consequence that must not be forgotten:** with no re-scrape, goal timings **cannot be
tested until a season of forward collection accumulates**. The feature does not exist for
any historical match. So idea 1 is a *build-now, test-later* item, and it should be
implemented as part of the next bulk scrape rather than as a standalone pass.

Minimal schema follows from answer 1:

```
data/raw/<league>_<season>_goals.csv
match_id, minute, stoppage, side, home_score_after, away_score_after
```

## 2. Idea 2 — "match out of round played" — DISAMBIGUATED AND REFUTED

**Status: TESTED 2026-09-20. Dead, and this one was properly powered.**

### The definition, from the user

> Match A was first scheduled in round X. It was rescheduled. Match A is still
> technically from round X, but it kicks off *after* round Y (Y > X) has already started.
> That is an out-of-round match.

This is an **ordinal** definition — "a later round has already begun" — not the
"days away from the round's centre" proxy measured earlier that evening. It is sharper,
and it catches more: 111 matches rather than 41.

The user also supplied the two things `F1`'s bar requires:

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

## 3. Idea 3 — forgotten. Recommendation in its place

The third idea was lost before it was written down. The recommendation below is **mine,
not the user's**, and is flagged as such.

### Recommended: collect the Over/Under 2.5 line

This is the highest value-per-hour change available and has been since 2026-07-26.

**Why it outranks everything else on this page:** it is the only pre-match variable ever
measured in this project that beats the base rate. `MARKET_LINE_FINDINGS.md` §2, on
15,475 matches:

| target | in-house features | B365 **opening** O/U 2.5 |
|---|---|---|
| comeback environment (HT decisive & FT decisive & 3+ goals) | **0.497** | **0.592** |
| total >= 3 goals | 0.545 | 0.602 |
| comeback | 0.496 | 0.552 |

And §3: a two-column market model cleared the top-20% slate bar out-of-sample at **1.33x**
(Wilson LB 5.68% vs 5.16% base, n = 7,675). Exploratory, not preregistered — §4 of that
document states what promoting it requires.

**Why it is cheap:** the schedule page's odds selector already has an O/U tab that the
pipeline skips. `driver.switch_odds_to_1x2()` clicks `ODDS_1X2_ITEM` (`li[type='O']`);
generalising it to `switch_odds_type(kind)` is a small change. The selection persists
across round clicks, so the cheapest shape is two passes per season — all rounds in 1X2,
switch, all rounds again in O/U — joined on `match_id`. **No detail scrape needed.**

Full design already exists as Phase 1 of `notes/PLAN_2026-07-25_environment_filter.md`,
including the new columns (`ou_line`, `over_odds`, `under_odds`, vig-free `implied_over`)
and which files change.

### Also still open: the prospective gut log

Not an idea from tonight, but in flight and easy to lose. `Proprietary_Filter_Explanation_v2.md`
concludes the core filter **cannot be encoded** — the matchup-combination trigger, the
odds pattern, the weight system and the 2-3 second instant are all listed under "What
Cannot Be Encoded". Consequence: **it cannot be backfilled onto historical matches**, so
the only valid instrument is a prospective log (same structural problem as `HANDOFF` §5.4,
web-search features).

That is statistically the **cleanest test this project can run**: k = 1, no formula
selection, no winner's curse, zero contamination, needs 11 hits per 100 picks. The schema
at the end of the user's own document is already the right one.

**Blocked on one number: picks per week.**

| picks/week | picks per season | verdict |
|---|---|---|
| ~1 (the Mode 2 rate) | ~25 | 1.4 expected hits. Unmeasurable; needs 4+ seasons |
| 4 | ~100 | **one season, fully powered.** Needs 11 hits |
| 8 | ~200 | one season, needs 18. Tighter CI |

The 2026-27 season is live and was on **round 5** on 2026-09-20 — a genuinely untouched
holdout, which this project has not had since 2025-26 was opened three times.

---

## 4. Measurements made 2026-09-20, so they are not lost

### Four claims from `Proprietary_Filter_Explanation_v2.md`, tested

Exploratory, one family, Holm-corrected. Corpus n = 2,058, 114 comebacks, base 5.54%.
**All four dead.**

```
T3_round_state       raw p=0.195  Holm p=0.779  dead
T4_monday_midweek    raw p=0.297  Holm p=0.891  dead
T2_structured_btts   raw p=0.590  Holm p=1.000  dead
T1_exhaustion        raw p=0.643  Holm p=1.000  dead
```

**T1 — the consecutive turnaround rule ("energy exhaustion").** Refuted precisely.

| after... | n | comeback wins | rate | lift |
|---|---|---|---|---|
| a comeback WIN | 109 | 3 | 2.75% | 0.99x |
| being the VICTIM | 109 | 2 | 1.83% | 0.66x |
| neither (control) | 3,784 | 107 | 2.83% | 1.02x |

Per-team-match base is 2.77%; observed 3 against 3.0 expected. The claim was "essentially
impossible". The ordering is also **inverted** — the victim shows more suppression than
the winner, the opposite of the model, though not significantly. Power limit: even 0 of
109 would have reached only p = 0.047 uncorrected, so this test could never have strongly
*confirmed* the rule.

**T2 — structured BTTS (one team scores 1H, the other 2H).** Dead, and the control beat it.

| tercile | structured BTTS | raw BTTS (control) |
|---|---|---|
| low | 5.67% | 4.54% |
| mid | 5.69% | 5.48% |
| high | 5.05% (0.91x) | 7.30% (1.32x, p = 0.087) |

The refinement is flat and slightly inverted; plain BTTS rate is monotone. Note raw BTTS
rate is a goal-volume proxy, so this is `LEAGUE_STUDY` F10's known totals dial
reappearing, not a new signal. Lesson: **goal volume carries a little, goal pattern
carries none.** The operator's ">= 4 of 6" threshold hit n = 22 — unusable.

**T3 — round state.** 0 earlier comebacks 5.11% (n=1,390); 1 earlier 7.36% (n=299,
lift 1.33x); 2+ earlier 6.25% (n=48). Non-monotone, CI contains base. Needs 1,422 matches
in the middle bucket.

**T4 — Monday / midweek.** Monday 2.90% (n=138, **4 comebacks**, lift 0.52x); midweek
**5.70%** (lift 1.03x); rest of week 5.73%. The combined claim is half wrong — midweek
shows zero suppression. Calling the Monday effect needs 444 Monday matches; 138 available.

### The two leagues are not interchangeable, but not for the reason it looks

| | n | comebacks | rate | 95% CI |
|---|---|---|---|---|
| English PL | 1,140 | 76 | 6.67% | [5.36%, 8.27%] |
| Ekstraklasa | 918 | 38 | 4.14% | [3.03%, 5.63%] |

chi2 = 5.73, p = **0.017**. But:

- **Half the gap is goal environment.** EPL 2.99 goals/match and 58.8% reach 3+ goals;
  Ekstraklasa 2.73 and 50.1%. Conditional on a comeback being mechanically possible
  (3+ goals and a decisive half-time) the rates converge to 15.77% vs 11.41%,
  **z = 1.76, p = 0.078 — not significant.**
- **Ekstraklasa's season stability is too good to be a league trait.** Observed
  season-to-season sd **0.19pp** against **1.14pp** of binomial noise; EPL 0.85pp against
  1.28pp. Three seasons landing that close happens about 3% of the time.
- `LEAGUE_STUDY` F1 remains the governing measurement: across 22 divisions, p = 0.18,
  between-league true-rate sd 0.08pp, rankings do not persist (r = 0.108). It explicitly
  warns that a two-league comparison (England vs Portugal, z = 2.09) looked significant
  *because those were the extremes of 22 draws*.

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
`PLAN_2026-07-25_environment_filter.md` §3 — choose the formula on leagues 1..L-1, test on
league L, rotate. Plus a **goal-environment covariate** to absorb the real part of the
league difference with one parameter instead of L formulas. If league-specific behaviour
is genuinely believed, that requires *more* leagues to estimate between-league variance
(F1 used 66 league-seasons), not fewer.

---

## 5. What to decide first, when this is picked up

1. **The picks-per-week number.** Still unanswered, and still the gate on the prospective
   log — the only instrument that can read the un-encodable core of the filter.
2. ~~Reading A or B for idea 2~~ — **resolved and closed 2026-09-20.** See §2.
3. **Whether to do the O/U line first** (§3). Independent of everything else, and the only
   measured-positive signal the project has.
4. **When the next bulk scrape happens**, it should carry three things at once: the goal
   timings (§1), the O/U line (§3), and the corrected fixture columns
   (`PREREGISTRATION.md` §9). All three are deferred for the same reason and all three are
   cleared by one pass.
