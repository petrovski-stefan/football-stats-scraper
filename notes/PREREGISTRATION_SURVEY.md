# PREREGISTRATION_SURVEY.md — the multi-country comeback and over-6.5 survey

**Status: DRAFT, written 2026-10-01. Not in force.** It becomes binding when it is committed
together with amendment **A11** (Appendix C) in `notes/PREREGISTRATION.md` §10, **before the
first CONFIRM page is scraped**. Until that commit, any league-season scraped is DEV data
(PREREGISTRATION A9.3).

Ledger audit: **not run** for this draft (the `ledger-auditor` agent runs only when asked or
through `/preregister`). Run it before the commit.

No outcome label of any CONFIRM league-season (Appendix A) was read to write this. The numbers
below come from DEV data (the Africa run of 2026-10-01), the spent EPL 2025-26 file,
theory-only calculations, and the published notes.

---

## 0. What this replaces

One document instead of six. On adoption it governs the multi-country study, and the texts
below stop governing it. None of them is edited; they stay as history.

| was | now |
|---|---|
| A9.2 / A10 confirmatory set (decided by which files exist) | §2 data blocks. As written, A9/A10 admit **41 league-seasons from 21 football-data divisions** (2024-25 and 2025-26; EPL excluded by A9/A10, ENG LCH 2024-25 by A10's history-slot rule). Those are the matches where MARKET_LINE (fit 2023-24, tested 2024-25) and LEAGUE_STUDY F11–F13 (tested 2025-26) were found. |
| RETRY §6 protocol and §7 pass rule (Holm over 15, lift ≥ 1.25×, leave-one-league-out sign) | §6: a fixed testing order, a beyond-baseline estimand, three verdicts, continent robustness |
| PLAN_2026-07-25 Phase 0 deliverable (`PREREGISTRATION_ENVIRONMENT.md`, never written) and its Phase 2 bar | this file; claim C1 |
| MARKET_LINE §4's promotion path for the market-line result | claim C1 |
| LEAGUE_STUDY F1's bar (≥ 8% over ≥ 600 matches + persistence + mechanism) as the survey's league test | claim C2 and §7.3 |
| `modelling/CLAUDE.md` §3 market-orthogonality bars (provisional, DECISIONS D1–D4) | §6.1: the beyond-baseline estimand measures incremental value directly |

**All 15 retry claims carry over. None is added.** Where each one went: §7.5.

## 1. The question

Across ~150 leagues the project has never analysed, using only information available before
kickoff:

1. Does the market's goal environment rank comebacks **within** a league? (C1)
2. Do leagues differ in comeback rate **beyond** what their goal environment explains, and does
   the difference persist from season to season? (C2)
3. Does anything else — the calendar, the table, team history, cards — add beyond the goal
   environment? (the H-family)
4. The first two questions again for over-6.5. (family O)

**The design in one paragraph.** A frozen goal-environment model **B** —
`modelling/scoreline.py` fed only opening market odds — predicts each match's P(comeback). B is
fitted on DEV once and never refitted. C1 tests B's own ranking. Every other claim is tested as
**added value beyond B**: observed outcomes against B's expected outcomes, inside
league-season strata. Claims run in a fixed order (§6.4), once, on CONFIRM. Anything that
passes is re-run once on the 2026-27 seasons (PROSPECTIVE).

**Why B is the baseline.** On DEV, a goal-only Poisson model reproduces Africa's comeback rate,
half-time draw rate and trailing-by-one completion rate from goals per match alone (§12.1).
League differences may be nothing but goal environment, and the market prices goal environment.
A claim that beats B has found something the price does not hold.

## 2. Data blocks — fixed now

### 2.1 DEV — free to analyse, at any time

Every league whose 2023–2026 outcomes the project has already looked at, in any source
(league ids in Appendix B):

- the 22 football-data.co.uk divisions of LEAGUE_STUDY and MARKET_LINE: ENG PR, ENG LCH,
  ENG L1, ENG L2, ENG NL, SCO PR, SCO CH, SCO L1, SCO L2, GER D1, GER D2, ITA D1, ITA D2,
  SPA D1, SPA D2, FRA D1, FRA D2, HOL D1, BEL D1, POR D1, GRE D1, TUR D1;
- POL PR (Ekstraklasa, part of the 2,058-match corpus);
- ALG D1, MAR D1, TUN D1 (scraped 2026-10-01 before any declaration, so DEV under A9.3);
- any other league-season scraped before this file is committed.

Their finished seasons are DEV. Their 2026-27 seasons belong to PROSPECTIVE.

### 2.2 CONFIRM — read once

Every finished league-season (labels `2023-2024`, `2024`, `2024-2025`, `2025`, `2025-2026`) of
every other league in `config/leagues.json` as of 2026-10-01: **153 leagues, 306
league-seasons** — Europe 79 leagues, Asia 44, Americas 30. Listed in **Appendix A**, which is
the A9.3 declaration. Scrape start: after this file and A11 are committed.

Checked 2026-10-01 against A10's history-slot rule (ids and dates only): the only catalogue
leagues referenced by any stored history slot or by the event store are ENG PR (36) and
ENG LCH (37), both DEV. No CONFIRM league-season has a match in `data/raw/` today.

### 2.3 PROSPECTIVE — read once, later

The `2026-2027` and `2026` seasons of every catalogue league, DEV and CONFIRM alike, scraped
after they finish. **One opening, on or after 2027-07-15** (§10).

### 2.4 No-peeking rules — binding

1. **No outcome-derived number is computed or displayed for a CONFIRM league-season before the
   single run**: no comeback rate, goals per match, totals, 7+ count, draw rate, half-time
   state, result or standings. This includes one-off questions such as "what's the comeback
   rate there?" — that question is how the Africa seasons became DEV.
2. Allowed before the run: odds coverage, match and round counts, load errors, kickoff dates,
   `qa.validate` (its checks print mismatch counts only; its two corpus-wide "(info)" lines,
   the second-half goal share and the card rates, inform no claim and are not used for any
   decision), and the reliability screen of §7.4, run on DEV.
3. **No CONFIRM league is dropped after the run, for any reason.**
4. B and all analysis code are frozen before the run: B's artifact hash and the analysis commit
   hash go into amendment A12 (§14.5).
5. The run happens once. Its raw output goes to `notes/runs/<date>_survey_confirm.txt`,
   committed with the results note and the `notes/STATE.md` update. A lost transcript is not
   regenerated (A7).
6. A claim may be added, changed or withdrawn only by a dated amendment committed before the
   run. After the run, nothing in this file changes.

## 3. Inclusion rules — outcome-blind, applied by script before the run

Applied per league. **A league with any failing league-season is dropped whole**, which is the
practice of the 2026-10-01 audit (ALG D2, SAPL and NZNL were dropped whole).

| rule | test | source |
|---|---|---|
| R1 | the schedule scrape finished every kept stage with no load error | audit rule (user, 2026-10-01) |
| R2 | in each single-stage round, the match count equals the league-season's modal round count | audit rule |
| R3 | ≥ 80% of matches carry opening 1X2 **and** O/U odds, in every finished league-season | matches the audit's calls: ALG D2 (75% / 85%) dropped, TUN D1 (81% / 90%) kept |
| R4 | the LEAGUES_INCIDENTS §1 leagues still in the catalogue (TFF 1. Lig, CHA CSL, CHA D1) are excluded now, before any of their data exists | decision D-5 |
| R5 | multi-stage leagues (25 in CONFIRM): a round is keyed on (stage, round); anything ordered in time is ordered by kickoff datetime | closes DECISIONS D7 with its option 1 |

The result — one row per league-season with matches, odds coverage and verdict — is committed
as `notes/runs/<date>_survey_inclusion.txt` before the run. The 15 LEAGUES_INCIDENTS §2
(Australian) leagues stay in and get a sensitivity analysis (§6.3).

## 4. Populations, outcomes, units

- **P_odds** — every match of an included league-season with opening 1X2 **and** O/U odds. The
  population of every test.
- **Matches without odds are reported, never tested.** On DEV (Africa) they ran 1.1% comebacks
  against 3.5% with odds, and 45% of them sat in a season's last 5 rounds. Odds disappear from
  end-of-season games, so these matches are not missing at random.
- Outcomes: `is_comeback` (match level, either side); `is_comeback_home` / `is_comeback_away`
  for the team-level claim; HT-decisive (`ht_home_goals != ht_away_goals`);
  `is_seven_or_more_goals`.
- Stratum: league-season (`league_id` + stored season label). Calendar-year labels are listed
  explicitly in Appendix A (A8.5). Time comparisons use kickoff dates and
  `domain/match.py:season_start_year`, never label strings.
- Continent: Europe, Asia or Americas, from `config/leagues.json`.

## 5. The baseline B

**Definition.** `modelling/scoreline.py:ScorelineModel` — Poisson goal rates per half, the
second half conditioned on the half-time state, a Dixon–Coles correction, full enumeration —
with exactly **four inputs, all in the schedule CSV**:

- `mkt_sup` = log(p_home / p_away) and `mkt_tot` = −log(p_draw), from the opening 1X2 price,
  de-vigged proportionally (`features/engine.py:_vig_free`);
- `ou_line`, the Asian goal line, which is where nowgoal's O/U signal sits
  (`scrapers/CLAUDE.md` §5), and `implied_over`, its tilt.

No Asian-handicap line (claim #10 tests it). No history, detail or standings column.

**Outputs per match:** P(comeback), P(home completes a comeback), P(away completes one),
P(HT-decisive), P(total ≥ 7). All come from the same enumeration.

**Fitting.** On all DEV P_odds matches, once. The free choices (the penalty α, any input
transform) are settled on DEV only, by leave-one-league-out deviance within DEV, and B must pass
`--self-check` and `--leak-check` on DEV. Then B is **frozen**: coefficients, standardisation
statistics, both Dixon–Coles ρ, α and a hash of the DEV training rows go into one artifact,
whose sha256 is recorded in A12 before the run. **B is never refitted on CONFIRM or
PROSPECTIVE.**

**Why market odds only.** RESULTS §3: the price beats a constant on the half-time state by
0.64%, and the six nowgoal feature families add 4% of that. MARKET_LINE §2: the O/U line was
the one input that ranked the comeback environment. The baseline should hold what the market
knows about goals, so that a claim beating it has found something the market does not price.

## 6. Statistical machinery

### 6.1 The beyond-baseline estimand

For a pre-kickoff flag F and a stratum s:

- `O1s`, `O0s` — observed outcomes in the flagged and unflagged matches;
- `E1s`, `E0s` — B's expected outcomes (sums of B's probabilities) in the same two groups;
  `Es = E1s + E0s`.

The **incremental rate ratio** is the Mantel–Haenszel rate ratio with B's expected counts in
the place of person-time:

```
RR = Σs (O1s · E0s / Es)  /  Σs (O0s · E1s / Es)

Var(ln RR) = Σs (E1s · E0s · (O1s + O0s) / Es²)  /  [ Σs (O1s · E0s / Es) · Σs (O0s · E1s / Es) ]
```

(the variance is Greenland–Robins for person-time data). **RR = 1 means the flag adds nothing
beyond B and the league-season.** It is RETRY §1b's Mantel–Haenszel-over-strata default with
one change: B's expectation replaces the match count. So a flag that only picks high-scoring
matches scores RR ≈ 1. That is PLAN_2026-09-20 §3's T2 lesson, where plain BTTS "worked"
because it was the totals dial again.

For a continuous score, the flag is the **top 20% of P_odds matches by score within the
stratum**: rank descending, flag rank ≤ round(0.2 · n_s), ties broken by `match_id` ascending.

For C1 and O1 only (B's own rankings), the expected counts are replaced by match counts: plain
Mantel–Haenszel risk ratio over strata.

### 6.2 Verdicts

- **PASS** — the test rejects RR = 1 in the stated direction at the claim's α (§6.4), and the
  robustness conditions of §6.3 hold. A PASS is labelled *meets SESOI* when the point estimate
  is at or beyond the smallest effect that matters — **SESOI = 1.20×, or 0.83× for a
  suppression claim** (decision D-2) — and *real but small* otherwise.
- **DEAD** — the 90% CI of RR lies inside [0.83, 1.20] (two one-sided tests at α = 0.05). Any
  effect is smaller than matters. The claim leaves the retry list for good.
- **INCONCLUSIVE** — neither. Reported with its CI and the n that would resolve it.

A claim first stated with its own effect size (T1: "essentially impossible"; T4: Monday at
0.52×) is also reported **REFUTED AS STATED** when the 95% CI excludes that size. This is a
reporting rule and spends no α.

### 6.3 Robustness conditions (every PASS)

1. **Leave one continent out.** The estimate stays on the same side of 1 with each of Europe,
   Asia and Americas removed in turn. With ~150 leagues, removing one league barely moves a
   pooled estimate, while a continent is a unit that can carry a result on its own. This
   replaces RETRY §7's leave-one-league-out sign.
2. **Watch list.** The estimate stays on the same side of 1 with the 15 LEAGUES_INCIDENTS §2
   leagues removed.

### 6.4 Testing order and α — family-wise error ≤ 0.05 in each family

Family C (comebacks):

1. **C1 at α = 0.05.** If C1 fails, family C stops. Nothing else in it can PASS. Every other C
   claim is still estimated and reported, labelled exploratory.
2. If C1 passes: **C2 at α = 0.025**, and the **H-family (9 claims) with Holm at α = 0.025**.
3. Recycling: if C2 passes, the H-family is re-evaluated with Holm at α = 0.05. If every H claim
   passes, C2 is re-evaluated at α = 0.05.

This is a graphical multiple-testing procedure (Bretz et al., 2009). It keeps the family-wise
error at or below 0.05 (decision D-3).

Families O and G each have their own α = 0.05. They are separate questions about separate
products, as PREREGISTRATION and PREREGISTRATION_FILTER were.

**What the order changes, compared with Holm over 15 at α = 0.05:** C1 moves from a first-step
threshold of 0.0033 to 0.05, and C2 to 0.025. The H-family's first step moves from 0.0033 to
0.0028, or to 0.0056 if C2 passes. The claims with strong priors get the α they need, and the
others keep about what they had.

## 7. Family C — comebacks

### 7.1 C1 — the market's goal environment ranks comebacks within league (RETRY #9)

- Score: B's P(comeback). Flag: top 20% within stratum (§6.1).
- Estimator: Mantel–Haenszel risk ratio over league-season strata, flagged vs unflagged.
  One-sided, RR > 1.
- Reported, not tested: the **pooled cross-league top-20% slate** — hits, rate, Wilson CI and
  lift, i.e. the candidate-slate number a product would use; the same slate ranked by raw
  `ou_line`; B's calibration overall, by continent and by decile.
- Prior: MARKET_LINE §3 (Europe, pooled, exploratory): top 20% 6.84% against a 5.16% base,
  1.33×, Wilson lower bound 5.68%. Against the rest of the matches that slate is ≈ 1.44×.

### 7.2 C2 — leagues differ beyond goals, persistently (RETRY #1 and #8)

Two tests. Both must reject at C2's α. This is an intersection–union test, so no further
correction is needed.

1. **Dispersion.** `Ol` = league l's comebacks over its finished CONFIRM seasons, `El` = B's
   expectation, `k = ΣO / ΣE`. `X² = Σl (Ol − k·El)² / (k·El)`. p by parametric bootstrap
   (Poisson(k·El), 10,000 draws, seed 0).
2. **Persistence.** Over the leagues with both a 2024-start and a 2025-start season: the
   Pearson r between the two seasons' `log((O + 0.5) / E)`. One-sided (r > 0), p by permutation
   (10,000, seed 0). A league's `2023-2024` season counts in test 1 only.

Reported: the method-of-moments τ (the between-league sd of log O/E beyond B) with a bootstrap
CI; `k` per continent; per league, the split into HT-decisive O/E and completion-given-HT-decisive
O/E (RETRY §2's target); F1's ≥ 8%-over-600 test per league, descriptive only.

DEAD for C2: the upper 95% bound of τ is below 0.10.

### 7.3 Comeback-candidate leagues — replaces F1's bar; runs only if C2 passes

1. Shrink each league's O/E with a gamma–Poisson model whose prior variance is C2's τ²:
   `Ol ~ Poisson(k·El·θl)`, `θl ~ Gamma(1/τ², 1/τ²)`.
2. **Candidate:** posterior 95% lower bound of θl > 1.0 **and** posterior mean ≥ 1.20.
3. **Verified:** the candidate's PROSPECTIVE O/E > 1, one-sided exact Poisson p < 0.05, Holm
   across candidates.

Only a verified league is called a comeback league. The same rule, run downwards, names
comeback-poor leagues; that list is reported, not tested.

### 7.4 The H-family — 9 claims, Holm

Common to every row: population P_odds; stratum league-season; estimator §6.1 (incremental RR
against B); robustness §6.3. **Tier S** needs schedule data only. **Tier D** needs the detail +
live-page scrape of §14.3.

Tier-D scores are history-block traits, so each must first pass the **reliability screen**
(depth-6 Spearman–Brown r₆ ≥ 0.10, `modelling/CLAUDE.md` §3), **measured on DEV**. A claim that
fails it is withdrawn by a dated amendment before the run, and Holm's m shrinks with it.

| RETRY # | claim | flag, known before kickoff | outcome / unit | direction | tier |
|---|---|---|---|---|---|
| 2 | table vs market | the side higher in the **recomputed pre-kickoff table** (§13.1) is the market underdog (lower de-vigged win probability); both sides have played ≥ 5 league matches in this stage | match comeback | two-sided — the earlier 7.11% figure has no recorded definition (§13.1) | S |
| 3 | round state (T3) | ≥ 1 comeback in the same (stage, round), in a match that kicked off ≥ 2 h 30 min before this one | match comeback | more | S |
| 4 | exhaustion (T1) | the team's previous match in this league-season, by kickoff, was a comeback win for it | this team completes a comeback; unit = team-match, expected = B's directional P | fewer | S |
| 5 | out of round | PLAN_2026-09-20 §1's ordinal definition: a round-X match that kicks off after the first kickoff of any round Y > X of the same stage | match comeback | two-sided — the claim said fewer; its only live cell (≥ 2 later rounds started) pointed up | S |
| 6 | Monday (T4) | `is_monday` as stored | match comeback | fewer | S |
| 10 | AH line adds over O/U | top 20% of \|`ah_line`\| within stratum | match comeback | two-sided | S |
| 11 | pre-half-time concession | top 20% within stratum of the mean of `home_conceded_pre_ht_rate` and `away_conceded_pre_ht_rate` (the sides present; a match with neither is excluded) | HT-decisive; expected = B's P(HT-decisive) | more | D |
| 12 | late-goal proneness | top 20% within stratum of the larger of `home_late_goal_rate` and `away_late_goal_rate` (the sides present) | match comeback | more | D |
| 15 | cards as a team trait | top 20% within stratum of the larger of `home_yellows_while_leading_avg` and `away_yellows_while_leading_avg` (the sides present) | match comeback | more | D |

#15 carries A8.4's condition (the EPL 2025-26 stratum is excluded). EPL 2025-26 is DEV here,
so the condition holds by construction.

### 7.5 Where the 15 retry claims went

| RETRY # | home in this file |
|---|---|
| 1, 8 | C2 — one test of league heterogeneity beyond B, with persistence — and §7.3 |
| 9 | C1 |
| 2, 3, 4, 5, 6, 10, 11, 12, 15 | the H-family (§7.4) |
| 7 — structured BTTS ≥ 4/6 | **exploratory** (§7.6). Its flag hit 22 of 2,058 matches (~1%), about 250 matches in a Tier-D subset, so it cannot resolve at any α. |
| 13 — the 36 time buckets | **exploratory**, run only if #11 or #12 passes. Thirty-six features at once is HANDOFF §6's "450-column trap" in small. |
| 14 — over-6.5 | family O (§8) |

Moving #7 and #13 out of the α family is a change made before any data. It frees α for the
claims that can resolve.

### 7.6 Pre-declared exploratory analyses — reported, no α, no claim

- End of season: the last 5 rounds against the rest. DEV (Africa): MH RR 0.45 [0.17, 1.25],
  4 comebacks in 240 matches.
- Matches without odds: count, rate and position in the season (§4).
- #7 and #13 as above.
- B's calibration per continent; the per-league O/E table; F1's bar per league.

## 8. Family O — over-6.5 (RETRY #14)

- **O1** (α = 0.05; the gate): top 20% within stratum by B's P(total ≥ 7) against the rest;
  Mantel–Haenszel risk ratio over strata; one-sided, RR > 1. Prior: F13, top decile 3.66%
  against a 1.87% base.
- **O2** (α = 0.05; only if O1 passes): a league effect on 7+ beyond B — §7.2's two tests with
  7+ as the outcome. Prior: F9 found league structure (χ² p = 9e-9), but it correlated
  r = 0.84 with goals per match, which B carries. Power is low (§11).
- Reported: B's 7+ calibration in its top decile. F13 found 5.6% predicted against 3.7%
  observed there.

## 9. Family G — the prospective gut log (PLAN_2026-09-20 §2)

- One test at α = 0.05, on PROSPECTIVE data only. Each pick is logged with a timestamp before
  kickoff, in a file committed every week. Picks per week and the start and end dates:
  decision D-6.
- **Test:** hits `O` against B's expected `E` over the picked matches (B frozen; the odds come
  from the later schedule scrape), one-sided exact Poisson, O > E. It asks whether the picks
  beat the market's own goal environment, not just the base rate.
- Also reported: the hit rate with its Wilson CI against the picks' league-season base rates.
- Worked bar: at 100 picks with E ≈ 5, a PASS needs ≥ 10 hits (P(X ≥ 10 | 5) = 0.032).

## 10. The PROSPECTIVE block — one opening, on or after 2027-07-15

- Every claim that PASSED on CONFIRM is re-run unchanged, one-sided in its CONFIRM direction,
  with Holm across the re-run claims inside each family. A claim that passes CONFIRM but not
  PROSPECTIVE is reported as *not replicated*.
- §7.3's candidate leagues are verified here.
- Family G is evaluated here.

## 11. Power — theory, no data

Assumptions: P_odds ≈ **60,000** matches (306 league-seasons × ~240 matches × ~85% with odds;
the real count is taken outcome-blind after the scrape), a 4.5% base rate, and a Tier-D subset
of ≈ 25,000 matches. One-sided tests.

| case | SE(ln RR) | DEAD reachable at 1.20×? | power at RR 1.20 (or 0.83): α .05 / Holm-9 at .025 / Holm-9 at .05 | at RR 1.30 (or 0.77) |
|---|---|---|---|---|
| 60k matches, 5% flagged (#5, #6) | 0.088 | yes | 0.72 / 0.30 / 0.38 | 0.95 / 0.71 / 0.79 |
| 60k matches, 20% flagged (C1, #2, #3, #10) | 0.048 | yes | 0.99 / 0.89 / 0.93 | 1.00 / 1.00 / 1.00 |
| 25k Tier-D matches, 20% flagged (#11, #12, #15) | 0.075 | yes | 0.82 / 0.42 / 0.51 | 0.98 / 0.84 / 0.89 |
| #4: 120k team-matches, 2.8% flagged, team base 2.25% | 0.117 | no | 0.42 / 0.09 / 0.13 | 0.63 / 0.22 / 0.29 |

C2, simulated (150 leagues, ~11 expected comebacks per league-season, both tests must reject):

| between-league sd τ beyond B | 0.00 | 0.10 | 0.15 | 0.20 |
|---|---|---|---|---|
| P(C2 rejects) at α = 0.025 | 0.01 | 0.18 | 0.65 | 0.95 |
| at α = 0.05 | 0.02 | 0.26 | 0.74 | 0.98 |

O2 (~4 seven-plus matches per league-season): P(reject) 0.40 at τ = 0.20, 0.89 at τ = 0.30, at
α = 0.05.

What this means:

- C1, O1 and the 20%-prevalence Tier-S claims will be settled either way.
- The 5% flags (#5, #6) resolve effects near 1.3×. Smaller ones end INCONCLUSIVE or DEAD.
- Tier-D claims resolve 1.3×, not 1.2×.
- #4 cannot reach the SESOI, but it will settle T1's own claim ("essentially impossible"): the
  95% CI excludes 0.5 if the true RR is near 1.
- C2 resolves τ = 0.15 — a league 2 sd out has ~35% more comebacks than its goals predict —
  but not τ = 0.10.

## 12. Prior evidence — recorded before the data

1. **Goal environment explains Africa (DEV).** An independent-Poisson goal model (halves split
   45/55, home share 0.56), at Africa's 2.08 goals per match: comebacks 2.96% against 3.3%
   observed [2.5, 4.4]; half-time draws 48.2% against 47.8%; trailing-by-one wins 7.0% against
   7.8% [5.9, 10.2]. At EPL + Ekstraklasa's 2.87 goals per match it gives 4.7% against 5.5%
   observed. Under this model, and allowing for its observed ~15% under-prediction, a league
   needs **≈ 4.0 goals per match** to reach an 8% comeback rate from goals alone.
2. **F1's bar does not scale to this survey.** Under a pure null at 5.15%, ≥ 8% over 600
   matches passes at least one of 150 leagues **26%** of the time (4% at the 22 it was set
   for). If leagues differ only in goals (sd 0.3 goals per match), the figure is **74%**. A
   16-team league plays 240 matches a season, so it has 480 in two finished seasons and can
   never qualify.
3. **The market line.** MARKET_LINE §2–3 as quoted under C1 (Europe, exploratory). On Africa
   (DEV) the above-median-line half ran 3.6% against 3.4% (MH RR 1.01 [0.53, 1.91]), which says
   nothing: the line barely varies there (1.75–2.25 on 91% of matches).
4. **Leagues within Europe.** F1: χ² p = 0.18, between-league true sd ≈ 0.08 pp, persistence
   r = 0.108.
5. **The cost of Holm over 15.** A claim with 80% power on its own has 45% power at Holm's
   first step (α/15).

## 13. Known data defects and leakage rules

### 13.1 Stored standings positions are post-match (measured 2026-10-01)

`home_team_position` and `away_team_position` hold the table **after** the round, including the
match's own result. Measured on DEV and spent files:

- in round 1, the winner is ranked above the loser in **17 of 17** decisive matches (Botola
  2024-25: 4; EPL 2025-26: 7; Algeria 2025-26: 6);
- a team's position change between consecutive rows correlates **0.62** with the result on the
  later row, and −0.09 / −0.14 with the result on the earlier row (EPL 2025-26, Botola 2024-25).

So `home_team_position`, `away_team_position` and `position_gap` are post-match columns. They
join `features/engine.py:POST_MATCH_COLUMNS`. Any table feature (#2) uses a table recomputed
from the league results with an **earlier kickoff** in the same league-season and stage: 3/1/0
points, then goal difference, then goals scored.

HANDOFF §5.2's "as-of-round" invariant holds in the scraper's sense (the dropdown is synced to
the round), but that round's table already contains the round. RETRY #2's 7.11% / 1.29× has no
recorded definition (DECISIONS D6.2), and if it used the stored positions it was exposed to
this leak. It is not used as prior evidence.

### 13.2 Other defects

1. Matches without odds are not missing at random (§4).
2. Multi-stage leagues: §3 R5 (DECISIONS D7).
3. Season labels: never compared as strings across the two conventions (A8.5).
4. `features.engine --self-check` cannot see a feature that reads the target row's own outcome
   (DECISIONS D5). The survey's matrix gets a leak check instead: NaN every post-match column
   (positions included), rebuild, and require identical B predictions and identical flags.

## 14. Build list and order of operations

### 14.1 Before the commit

The decisions of §15 are made, then this file and A11 are committed.

### 14.2 Scrape and include

- CONFIRM schedules: 306 league-seasons × ~5.3 min (measured in the 2026-10-01 audit) ≈ 27 h.
- DEV schedules, for fitting B: ~47 league-seasons ≈ 4 h. DEV can be scraped at any time.
- The inclusion script (§3) → `notes/runs/<date>_survey_inclusion.txt`, committed.

### 14.3 Tier D (decision D-4)

- The subset: per continent, `random.Random(20261001).sample(sorted(codes), k)` with
  k = round(0.4 × that continent's Appendix-A leagues), drawn when this file is committed. A
  drawn league that §3 later drops is not replaced, so the draw stays independent of inclusion.
  That gives ≈ 62 leagues and ≈ 25,000 matches.
- Detail + live-page renders cost ≈ 1.6–2 h per 1,000 matches (PLAN_2026-07-25 Phase 1's
  estimate at 4 workers; the pool is now 3), so ≈ 40–50 h.
- DEV Tier D for the reliability screen and the dry run: ≥ 4 DEV leagues, ≈ 3,000 matches,
  ≈ 5 h.

### 14.4 Code — each piece dry-run on DEV, transcripts in `notes/runs/`

1. A schedule-only matrix: the market inputs from the base CSV. Today
   `features.engine.build_features` needs detail columns.
2. B: a market-only `ScorelineModel`, directional and 7+ outputs, and the freeze artifact.
3. Statistics: §6.1's rate ratio and variance; the risk-ratio MH for C1/O1; TOST; Holm with a
   settable α (`modelling/experiment.py:holm` hard-codes 0.05); §6.4's recycling.
4. C2/O2: the dispersion bootstrap, the persistence permutation, τ, the gamma–Poisson shrinkage.
5. The flags: the recomputed pre-kickoff table, out of round, round state, the team's previous
   result, top 20% within stratum.
6. The leak check of §13.2.

### 14.5 Freeze, then run once

Amendment **A12** records B's artifact sha256, the analysis commit hash and the DEV dry-run
transcript. Then the single CONFIRM run.

### 14.6 After

The results note, the STATE rows and the raw transcript go in one commit. PROSPECTIVE opens on
or after 2027-07-15.

## 15. Decisions for the user

The recommended value is in bold, and this draft assumes it.

| | decision | recommended | alternative |
|---|---|---|---|
| D-1 | DEV boundary | **the 26 leagues of §2.1** | keep A9/A10 as written, which admits 41 football-data league-seasons as confirmatory |
| D-2 | SESOI and DEAD margin | **1.20× (0.83× for suppression)** | 1.25× (RETRY's floor) or 1.15× |
| D-3 | testing order | **C1 gate, then C2 and the H-family at α/2 each, with recycling (§6.4)** | plain Holm over every inferential claim |
| D-4 | Tier-D subset | **40% of leagues per continent, ≈ 25,000 matches, ≈ 40–50 h of scraping** | none (#11, #12, #15 become exploratory), or all of CONFIRM (≈ 100–120 h) |
| D-5 | in-window incident leagues (TFF 1. Lig, CHA CSL, CHA D1) | **exclude now** | include them, with a sensitivity analysis like the Australian one |
| D-6 | the gut log | **keep it; set picks per week and the start date** | drop family G |

Also open, not blocking: FRIENDLY_MARKER (A8.6). It only matters to Tier D's event aggregates.
Recommended: a history match with more than 6 substitutions by one side is left out of the
event aggregates.

## 16. On adoption, also update

- `notes/STATE.md`: open leads 1–3 point here.
- `modelling/CLAUDE.md` §3–4: the candidate protocol's outcome step and the screening bars
  point to §6 here.
- `.claude/skills/preregister/SKILL.md` and `/new-candidate` step d: the pass rule is §6.2,
  not RETRY §7.
- `notes/DECISIONS.md`: close D7 (option 1). D1–D4 no longer bind this study.
- `notes/HANDOFF.md` §5.2: add §13.1.
- `features/engine.py:POST_MATCH_COLUMNS`: add the three position columns.

---

## Appendix A — CONFIRM league-seasons (the A9.3 declaration)

Generated 2026-10-01 from `config/leagues.json` (ids, labels and stages only). The
LEAGUES_INCIDENTS column marks R4's exclusions (§1) and the sensitivity set (§2).

| continent | country | code | id | finished seasons | kept stages (if > 1) | LEAGUES_INCIDENTS |
|---|---|---|---|---|---|---|
| Americas | Argentina | ARG B M | 917 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Argentina | ARG D1 | 2 | 2024, 2025 |  |  |
| Americas | Argentina | ARG D2 | 423 | 2024, 2025 |  |  |
| Americas | Bolivia | BOL D1 | 593 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Brazil | BRA D1 | 4 | 2024, 2025 |  |  |
| Americas | Brazil | BRA D2 | 358 | 2024, 2025 |  |  |
| Americas | Brazil | BRA D3 | 1347 | 2024, 2025 |  |  |
| Americas | Brazil | BRA SP | 178 | 2024, 2025 |  |  |
| Americas | Brazil | BRA SPB | 1373 | 2024, 2025 |  |  |
| Americas | Chile | CHI D1 | 415 | 2024, 2025 |  |  |
| Americas | Chile | CHI D2 | 611 | 2024, 2025 |  |  |
| Americas | Colombia | COL D1 | 250 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Colombia | COL D2 | 1169 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Costa | CRC D1 | 504 | 2024-2025, 2025-2026 | Apertura, Clausura |  |
| Americas | Ecuador | ECU LPSA | 596 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Ecuador | ECU LPSB | 1398 | 2024, 2025 |  |  |
| Americas | El Salvador | SLV D1 | 511 | 2024-2025, 2025-2026 | Apertura, Clausura |  |
| Americas | Guatemala | GUA D1 | 579 | 2024-2025, 2025-2026 | Apertura, Clausura |  |
| Americas | Honduras | HON Lig1 | 577 | 2024-2025, 2025-2026 | Apertura, Clausura |  |
| Americas | Jamaica | JAM D1 | 1409 | 2024-2025, 2025-2026 |  |  |
| Americas | Mexico | MEX D1 | 140 | 2024-2025, 2025-2026 | Apertura, Clausura |  |
| Americas | Mexico | MEX Lig2 | 847 | 2024-2025, 2025-2026 | Apertura, Clausura |  |
| Americas | Nicaragua | NIC LP | 1586 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Panama | LPF | 1494 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Paraguay | PAR D1 | 354 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Paraguay | PAR D2 | 1076 | 2024, 2025 |  |  |
| Americas | Peru | PER L1 | 242 | 2024, 2025 | Apertura, Clausura |  |
| Americas | United States | MLS | 21 | 2024, 2025 |  |  |
| Americas | Uruguay | URU D1 | 240 | 2024, 2025 | Apertura, Clausura |  |
| Americas | Venezuela | VEN D1 | 391 | 2024, 2025 | Apertura, Clausura, Apertura-B |  |
| Asia | Australia | AUS D1 | 273 | 2024-2025, 2025-2026 |  | §2 — sensitivity set |
| Asia | Australia | AUS NSW | 616 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | AUS NSWSL | 1255 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | AUS QSL | 1068 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | AUS SASL | 1029 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | AUS VPL | 436 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | Aus VD1 | 1073 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | FFSA PL | 1072 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | FQPL2 | 2334 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | FQPL3 | 1382 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | NPLCF | 1063 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | NSW-N TPL | 1453 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | QLD D1 | 1868 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | TSA TPL | 1450 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Australia | WAUS D1 | 481 | 2024, 2025 |  | §2 — sensitivity set |
| Asia | Bahrain | BHR D | 896 | 2024-2025, 2025-2026 |  |  |
| Asia | Bahrain | BHR D1 | 318 | 2024-2025, 2025-2026 |  |  |
| Asia | Cambodia | CPL | 1538 | 2024-2025, 2025-2026 |  |  |
| Asia | China | CHA CSL | 60 | 2024, 2025 |  | §1 — excluded by R4 |
| Asia | China | CHA D1 | 61 | 2024, 2025 |  | §1 — excluded by R4 |
| Asia | India | IND D1 | 763 | 2023-2024, 2024-2025, 2025-2026 |  |  |
| Asia | Indonesia | IDN ISL | 1122 | 2024-2025, 2025-2026 |  |  |
| Asia | Iraq | IRQ SL | 1054 | 2024-2025, 2025-2026 |  |  |
| Asia | Japan | JPN D1 | 25 | 2025 |  |  |
| Asia | Japan | JPN D2 | 284 | 2025 |  |  |
| Asia | Japan | JPN D3 | 1346 | 2024, 2025 |  |  |
| Asia | Jordan | JOR D1 | 309 | 2024-2025, 2025-2026 |  |  |
| Asia | Jordan | JOR D2 | 1078 | 2024-2025, 2025-2026 |  |  |
| Asia | Kuwait | KUW D1 | 322 | 2024-2025, 2025-2026 |  |  |
| Asia | Kuwait | KUW D2 | 923 | 2023-2024, 2024-2025, 2025-2026 |  |  |
| Asia | Malaysia | MAS SL | 316 | 2024-2025, 2025-2026 |  |  |
| Asia | Oman | OMA PL | 332 | 2024-2025, 2025-2026 |  |  |
| Asia | Qatar | QAT D1 | 313 | 2024-2025, 2025-2026 |  |  |
| Asia | Saudi Arabia | KSA D1 | 745 | 2024-2025, 2025-2026 |  |  |
| Asia | Saudi Arabia | SPL | 292 | 2024-2025, 2025-2026 |  |  |
| Asia | Singapore | SIN D1 | 194 | 2024-2025, 2025-2026 |  |  |
| Asia | South Korea | KOR D1 | 15 | 2024, 2025 |  |  |
| Asia | South Korea | KOR D2 | 1292 | 2024, 2025 |  |  |
| Asia | Thailand | THA L2 | 1048 | 2024-2025, 2025-2026 |  |  |
| Asia | Thailand | THA PR | 700 | 2024-2025, 2025-2026 |  |  |
| Asia | UAE | UAE LP | 301 | 2024-2025, 2025-2026 |  |  |
| Asia | Uzbekistan | UZB D1 | 772 | 2024, 2025 |  |  |
| Asia | Vietnam | VIE D1 | 766 | 2024-2025, 2025-2026 |  |  |
| Asia | Vietnam | VIE D2 | 1248 | 2024-2025, 2025-2026 |  |  |
| Europe | Albania | ALB D1 | 315 | 2024-2025, 2025-2026 |  |  |
| Europe | Albania | ALB D2 | 348 | 2024-2025, 2025-2026 |  |  |
| Europe | Armenia | ARM D1 | 469 | 2024-2025, 2025-2026 |  |  |
| Europe | Austria | AUT D1 | 3 | 2024-2025, 2025-2026 |  |  |
| Europe | Austria | AUT D2 | 128 | 2024-2025, 2025-2026 |  |  |
| Europe | Belarus | BLR D1 | 230 | 2024, 2025 |  |  |
| Europe | Bosnia | BOS PL | 352 | 2024-2025, 2025-2026 |  |  |
| Europe | Bulgaria | BUL FL | 131 | 2024-2025, 2025-2026 |  |  |
| Europe | Bulgaria | BUL SL | 1262 | 2024-2025, 2025-2026 |  |  |
| Europe | Croatia | CRO D1 | 133 | 2024-2025, 2025-2026 |  |  |
| Europe | Croatia | CRO D2 | 1612 | 2024-2025, 2025-2026 |  |  |
| Europe | Cyprus | CYP D1 | 159 | 2024-2025, 2025-2026 |  |  |
| Europe | Cyprus | CYP D2 | 915 | 2024-2025, 2025-2026 |  |  |
| Europe | Czech Republic | CZE D1 | 137 | 2024-2025, 2025-2026 |  |  |
| Europe | Czech Republic | CZE D2 | 290 | 2024-2025, 2025-2026 |  |  |
| Europe | Denmark | DEN D1 | 127 | 2024-2025, 2025-2026 |  |  |
| Europe | Denmark | DEN D2 | 1427 | 2024-2025, 2025-2026 |  |  |
| Europe | Denmark | DEN SASL | 7 | 2024-2025, 2025-2026 |  |  |
| Europe | England | ENG NLN | 297 | 2024-2025, 2025-2026 |  |  |
| Europe | England | ENG NLS | 298 | 2024-2025, 2025-2026 |  |  |
| Europe | England | ENG RYM | 566 | 2024-2025, 2025-2026 |  |  |
| Europe | England | ENG-N PR | 713 | 2024-2025, 2025-2026 |  |  |
| Europe | England | ENG-S CE | 1956 | 2024-2025, 2025-2026 |  |  |
| Europe | England | ENG-S PR | 336 | 2024-2025, 2025-2026 |  |  |
| Europe | Estonia | EST D1 | 353 | 2024, 2025 |  |  |
| Europe | Estonia | EST D2 | 1043 | 2024, 2025 |  |  |
| Europe | Faroe | FAR D1 | 576 | 2024, 2025 |  |  |
| Europe | Finland | FIN D1 | 13 | 2024, 2025 |  |  |
| Europe | Finland | FIN D2 | 212 | 2024, 2025 |  |  |
| Europe | Finland | FIN D3 A | 1417 | 2024, 2025 | Group A, Group B, Group C, Group D |  |
| Europe | France | FRA D3 | 203 | 2024-2025, 2025-2026 |  |  |
| Europe | France | FRA D4 | 1421 | 2024-2025, 2025-2026 | Group A, Group B, Group C |  |
| Europe | Georgia | GEO D1 | 563 | 2024, 2025 |  |  |
| Europe | Georgia | GEO D2 | 1116 | 2024, 2025 |  |  |
| Europe | Germany | GER D3 | 693 | 2024-2025, 2025-2026 |  |  |
| Europe | Hungary | HUN D1 | 136 | 2024-2025, 2025-2026 |  |  |
| Europe | Hungary | HUN D2E | 703 | 2024-2025, 2025-2026 |  |  |
| Europe | Iceland | ICE D1 | 381 | 2024, 2025 |  |  |
| Europe | Iceland | ICE PR | 166 | 2024, 2025 |  |  |
| Europe | Ireland | IRE D1 | 139 | 2024, 2025 |  |  |
| Europe | Ireland | IRE PR | 1 | 2024, 2025 |  |  |
| Europe | Italy | ITA SC | 142 | 2024-2025, 2025-2026 | Group A, Group B, Group C |  |
| Europe | Kazakhstan | KAZ PR | 466 | 2024, 2025 |  |  |
| Europe | Kosovo | Kos L | 1750 | 2024-2025, 2025-2026 |  |  |
| Europe | Latvia | LAT D1 | 214 | 2024, 2025 |  |  |
| Europe | Latvia | LAT D2 | 1070 | 2024, 2025 |  |  |
| Europe | Lithuania | LIT D2 | 897 | 2024, 2025 |  |  |
| Europe | Lithuania | TOPLYGA | 217 | 2024, 2025 |  |  |
| Europe | Luxembourg | LUX D1 | 514 | 2024-2025, 2025-2026 |  |  |
| Europe | Moldova | MOL D1 | 389 | 2024-2025, 2025-2026 |  |  |
| Europe | Montenegro | MNE D1 | 562 | 2024-2025, 2025-2026 |  |  |
| Europe | Netherlands | HOL D2 | 17 | 2024-2025, 2025-2026 |  |  |
| Europe | North Macedonia | MKD D1 | 392 | 2024-2025, 2025-2026 |  |  |
| Europe | Northern Ireland | NIR CH | 748 | 2024-2025, 2025-2026 |  |  |
| Europe | Northern Ireland | NIR D1 | 165 | 2024-2025, 2025-2026 |  |  |
| Europe | Norway | NOR AL | 123 | 2024, 2025 |  |  |
| Europe | Norway | NOR D1 | 22 | 2024, 2025 |  |  |
| Europe | Norway | NOR D2 | 1428 | 2024, 2025 | Group A, Group B |  |
| Europe | Poland | POL D1 | 221 | 2024-2025, 2025-2026 |  |  |
| Europe | Poland | POL D2 | 1355 | 2024-2025, 2025-2026 |  |  |
| Europe | Portugal | POR D2 | 157 | 2024-2025, 2025-2026 |  |  |
| Europe | Romania | ROM D1 | 124 | 2024-2025, 2025-2026 |  |  |
| Europe | Romania | ROM D2 | 1423 | 2024-2025, 2025-2026 |  |  |
| Europe | Serbia | SER D1 | 129 | 2024-2025, 2025-2026 |  |  |
| Europe | Serbia | SER D2 | 1061 | 2024-2025, 2025-2026 |  |  |
| Europe | Slovakia | SVK D1 | 132 | 2024-2025, 2025-2026 |  |  |
| Europe | Slovenia | SLO D1 | 247 | 2024-2025, 2025-2026 |  |  |
| Europe | Slovenia | SLO D2 | 120 | 2024-2025, 2025-2026 |  |  |
| Europe | Spain | SPA D3 | 2254 | 2024-2025, 2025-2026 | Group A, Group B |  |
| Europe | Spain | SPA D4 | 1413 | 2024-2025, 2025-2026 | Group 1, Group 2, Group 3, Group 4, Group 5 |  |
| Europe | Sweden | SWE D1 | 26 | 2024, 2025 |  |  |
| Europe | Sweden | SWE D1 SN | 218 | 2024, 2025 | North, South |  |
| Europe | Sweden | SWE D2 | 122 | 2024, 2025 |  |  |
| Europe | Switzerland | SUI CL | 121 | 2024-2025, 2025-2026 |  |  |
| Europe | Switzerland | SUI SL | 27 | 2024-2025, 2025-2026 |  |  |
| Europe | Turkey | TFF 1. Lig | 130 | 2024-2025, 2025-2026 |  | §1 — excluded by R4 |
| Europe | Ukraine | UKR D1 | 119 | 2024-2025, 2025-2026 |  |  |
| Europe | Wales | WAL FAWC | 2051 | 2024-2025, 2025-2026 | North, South |  |
| Europe | Wales | Welsh PR | 135 | 2024-2025, 2025-2026 |  |  |

**153 leagues, 306 league-seasons.**

## Appendix B — DEV league ids

The 22 football-data divisions: ENG PR 36, ENG LCH 37, ENG L1 39, ENG L2 35, ENG NL 146,
SCO PR 29, SCO CH 150, SCO L1 151, SCO L2 152, GER D1 8, GER D2 9, ITA D1 34, ITA D2 40,
SPA D1 31, SPA D2 33, FRA D1 11, FRA D2 12, HOL D1 16, BEL D1 5, POR D1 23, GRE D1 32,
TUR D1 30. Plus POL PR 6, and ALG D1, MAR D1 and TUN D1 (the three Africa leagues in
`config/leagues.json`).

## Appendix C — draft A11 for `notes/PREREGISTRATION.md` §10

> **A11 — <commit date>. The multi-country survey is governed by `notes/PREREGISTRATION_SURVEY.md`.**
>
> 1. For the survey it replaces A9.2/A10's confirmatory-set rule, RETRY_CANDIDATES §6–7 and
>    LEAGUE_STUDY F1's league bar. Those texts are not edited.
> 2. The confirmatory set is its Appendix A: 153 leagues, 306 league-seasons, by league id and
>    season label, calendar-year labels included (A8.5). Scrape start: <date>, after this
>    commit.
> 3. DEV adds the 22 football-data divisions and the three Africa leagues to the existing
>    EPL/Ekstraklasa set.
> 4. All 15 retry claims carry over (its §7.5). None is added. #7 and #13 become exploratory.
> 5. No outcome label of any Appendix-A league-season was read in preparing this amendment.
