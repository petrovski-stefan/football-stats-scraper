# STAKES — comebacks when the result matters to the team behind

**Group: Analysis.** Claude writes it from a run. A new run updates its numbers and adds a line to its run log. Each claim is untested until a Record note tests it.

**Written in ASD-STE100 Simplified Technical English.** Short sentences, one idea each. The frozen plan in the Method keeps its own wording.

- **Scope:** `SCHEDULE/WHOLE_CORPUS/ALL`: all matches with a team behind at half-time, divided by two flags of what is at stake for that team.
- **Sources:** schedule stage 3. Inputs: the stake fields S3.11 (matches left), S3.12 (points behind the team above) and S3.13 (rank change since the odds opened), and the opening win chances S2.17 and S2.19. The odds yardstick reads S1.16–19 and S2.24 (`ALL/ODDS_YARDSTICK.md`). Outcomes: the half-time goals (S1.12–13) and the labels S2.27–28. Units: the league-season (S1.02, S1.01), for the strata and the intervals. The season (S1.01) also gives the season cohort.
- **Corpus:** 2026-10-19: 144 league-seasons, 36,238 matches. 21,412 have a team behind at half-time, and each has an opening win chance for it.
- **Code:** `uv run python -m analysis.schedule.whole_corpus.all.stakes`, at the commit that adds this doc.
- **Kind:** empirical.

## Question

Does a team that is behind at half-time come back more often when the result matters to it, beyond what its strength says? The stakes test asked this once, on 2026-10-12, with a frozen plan. This doc measures the same comparison again on the corpus of the day, and adds the odds yardstick. It is not a second test.

## Claims

"MH OR" is the Mantel–Haenszel odds ratio of a win by the team behind, flagged against not flagged, over strata of league-season × fifth of its opening win chance × deficit.

| id | claim | number [95% interval] | n | both seasons | status |
|---|---|---|---|---|---|
| C1 | A team late in the stage and close to the team above (F1) does not come back more often than its strength says | MH OR 1.0958 [0.9291, 1.2923], CMH p = 0.2745. Win rate 0.0894 flagged, 0.0882 not | 21,412 (2,249 flagged) | yes, no difference in either: 1.1209 (p = 0.3395) in 2024, 1.0723 (p = 0.5519) in 2025 | exploratory |
| C2 | A team that fell 2 or more places since the odds opened (F2) does not come back more often than its strength says | MH OR 1.0326 [0.8945, 1.1921], CMH p = 0.6630. Win rate 0.0942 flagged, 0.0882 not | 20,507 (3,056 flagged) | yes, no difference in either: 1.0545 (p = 0.6141) in 2024, 1.0125 (p = 0.9042) in 2025 | exploratory |
| C3 | The bar of the frozen plan is not met on this corpus | Holm p 0.5490 (F1) and 0.6630 (F2). The odds ratios are on the same side of 1 in both cohorts | 2 flags | is the bar | exploratory |
| C4 | Against the odds yardstick, the flagged teams come back about as much more often than expected as the other teams | F1: O/E 1.3089 [1.1336, 1.4868] flagged, 1.2290 [1.1753, 1.2846] not. F2: 1.3009 [1.1577, 1.4549] flagged, 1.2393 [1.1831, 1.2955] not. The intervals overlap | 21,412 and 20,507 | not measured | exploratory |

## The comparison

| flag | states | flagged | wins | rate | not flagged | wins | rate | MH OR [95% interval] | CMH p | strata |
|---|---|---|---|---|---|---|---|---|---|---|
| F1 late and close | 2024 | 1,095 | 101 | 0.0922 | 9,361 | 815 | 0.0871 | 1.1209 [0.8859, 1.4182] | 0.3395 | 278 |
| | 2025 | 1,154 | 100 | 0.0867 | 9,802 | 875 | 0.0893 | 1.0723 [0.8508, 1.3515] | 0.5519 | 297 |
| | pooled | 2,249 | 201 | 0.0894 | 19,163 | 1,690 | 0.0882 | 1.0958 [0.9291, 1.2923] | 0.2745 | 575 |
| F2 fell 2+ places | 2024 | 1,486 | 142 | 0.0956 | 8,515 | 744 | 0.0874 | 1.0545 [0.8582, 1.2957] | 0.6141 | 283 |
| | 2025 | 1,570 | 146 | 0.0930 | 8,936 | 795 | 0.0890 | 1.0125 [0.8286, 1.2371] | 0.9042 | 306 |
| | pooled | 3,056 | 288 | 0.0942 | 17,451 | 1,539 | 0.0882 | 1.0326 [0.8945, 1.1921] | 0.6630 | 589 |

The fifths' cut points of the opening win chance are 0.2342, 0.3211, 0.4 and 0.503. 1,891 of the 21,412 teams behind won (0.0883). F2 leaves out 905 states with no rank change (the first rounds).

## Against the odds

| flag | states | n | wins | expected | O/E [95% interval] |
|---|---|---|---|---|---|
| F1 late and close | flagged | 2,249 | 201 | 153.6 | 1.3089 [1.1336, 1.4868] |
| | not flagged | 19,163 | 1,690 | 1,375.0 | 1.2290 [1.1753, 1.2846] |
| F2 fell 2+ places | flagged | 3,056 | 288 | 221.4 | 1.3009 [1.1577, 1.4549] |
| | not flagged | 17,451 | 1,539 | 1,241.8 | 1.2393 [1.1831, 1.2955] |

The expected wins are the yardstick's chance that the team behind wins from that half-time score. All four O/E are above 1: that is the comeback gap of the yardstick (`ALL/ODDS_YARDSTICK.md`, C2–C3), not a stakes effect.

## Method

- **This run** follows the frozen plan below: the same unit, outcome, flags, strata, odds ratio, interval, test and bar. The season cohorts 2024 and 2025 are its seasons 1 and 2. The Mantel–Haenszel odds ratio, its interval and the Holm correction are now in `analysis/stats.py` (`mantel_haenszel`, `holm`). The reading against the odds is new: the observed wins over the yardstick's chances, with a cluster bootstrap over league-seasons (2,000 resamples).
- **The frozen run.** `stakes_test.py` ran once on 2026-10-12, on the corpus of that day. Both flags failed the bar. Its plan, its script and its output are in the backup zip of 2026-10-19 (`Desktop/football-stats-scraper_backups/notes_runs_2026-10-19.zip`, `runs/2026-10-12_stakes/`). The user decided on 2026-10-13 to record no STATE row.
- **The frozen plan, verbatim (`TEST.md`, 2026-10-12).** Its note paths are those of that day: `notes/LEAGUE_STUDY.md` was dropped on 2026-10-13, and `notes/DECISIONS.md`, `notes/fields/schedule_3_multi.md` and `notes/STATE.md` are now `notes/WORKING/DECISIONS.md`, `notes/FIELDS/SCHEDULE_3_MULTI.md` and `notes/WORKING/STATE.md`.

> # Stakes test — frozen 2026-10-12, before the run
>
> Approved by the user ("go", 2026-10-12). **Exploratory:** no dead ledger row measures what a
> result is worth to a side (the closest, `notes/LEAGUE_STUDY.md` F10 "Calendar: month,
> round-of-season", measures time), and the claim is not on the closed retry list. A pass is a
> lead to confirm on new data, not a finding. Market screen: the low bar is waived for these
> fields (`notes/DECISIONS.md` D8).
>
> **Question:** does a team that trails at half-time come back more often when the result
> matters to it, beyond what its strength (the opening odds) says?
>
> **Data:** `data/finished/3_multi/*_schedule.csv`, all 144 league-seasons, as rebuilt on
> 2026-10-12 (208 columns; fields S3.11–13 of `notes/fields/schedule_3_multi.md` §B3). Season 1 =
> `s1_season` 2024 or 2024-2025; season 2 = 2025 or 2025-2026.
>
> **Unit:** a match with a decisive half-time score; T = the side behind at half-time. Matches
> without T's opening 1X2 probability (`s2_mkt_p_<T>`) are left out.
>
> **Outcome:** T wins at full time (`s2_is_comeback_<T>`).
>
> **Flags** (two-sided):
>
> - **F1, late and close:** `s3_<T>_pre_matches_left` ≤ 5 and `s3_<T>_pre_pts_to_above` ≤ 3. An
>   empty `pts_to_above` (no team above) is not flagged.
> - **F2, fell since the odds opened:** `s3_<T>_rank_change_since_open` ≥ 2. Rows with an empty
>   rank change are left out of F2's test.
>
> **Comparison:** Mantel–Haenszel odds ratio of T winning, flagged vs not, over strata =
> league-season × fifth of T's opening win probability × deficit (1 goal / 2 or more). The
> fifths' cut points are the 20/40/60/80% quantiles of `s2_mkt_p_home` and `s2_mkt_p_away`
> pooled over every match with odds (no result read). Cochran–Mantel–Haenszel chi-square test
> (1 df, no continuity correction); 95% CI by Robins–Breslow–Greenland.
>
> **Reported per flag**, for season 1, season 2 and pooled: flagged and unflagged trailing
> states and wins; MH OR [95% CI]; CMH p.
>
> **Bar:** pooled CMH p after Holm over the 2 flags < 0.05, **and** the MH OR on the same side
> of 1 in both seasons.
>
> **Power (planned):** about 1,100 (F1) and 1,600 (F2) trailing states per season; pooled, an
> OR of about 1.3 is detectable at 80%, smaller ones are not.
>
> **Run once:** `stakes_test.py` in this folder; output `out.txt`. A results note and the
> `notes/STATE.md` row follow only with the user's go.

## Caveats

- **Not a second test.** The frozen test ran once and failed. This run sees nearly the same corpus. Since then, only England League 2 was scraped again (2026-10-13, `notes/LOG/MIGRATIONS.md`): the 24 matches of two 2024-25 rounds got their opening odds, and nothing else changed. A new test needs a new holdout (`notes/ANALYSIS/CLAUDE.md` §6).
- **Power:** the frozen plan finds an odds ratio of about 1.3 at 80%. The upper ends of the intervals, 1.2923 (F1) and 1.1921 (F2), leave room for a smaller effect.
- **The flags read the table at kickoff.** S3.12 and S3.13 come from the standings rebuilt from the matches that kicked off at least 2 h 30 min before (`notes/FIELDS/SCHEDULE_3_MULTI.md`). They do not count a match that kicked off less than 2 h 30 min before, even when it ended before this kickoff.
- **The strata take strength from the 1X2 chances only.** The reading against the odds also uses the O/U market, and gives the same answer (C4).
- **Looks:** 2 flags × 3 rows of the comparison, 4 readings against the odds, and the bar.

## Runs

| date | corpus | change |
|---|---|---|
| 2026-10-19 | 144 league-seasons, 36,238 matches | first run in this workflow (the frozen test ran on 2026-10-12) |
