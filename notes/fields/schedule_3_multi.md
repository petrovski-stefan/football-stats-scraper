# Schedule — stage 3, needs other rows

**Answers: which other rows does it read, and are they all before kickoff?** Every field here
needs more than its own row. This is the only place cross-row leakage can enter, so every field
states its **row window**. Claude writes them; the stats-reviewer agent checks them.

- Reads: the schedule file of stage 2 (S3.03 rebuilds the standings from its results).
- File: `data/finished/3_multi/<country>_<league>_<season>_schedule.csv` = the stage-2 file plus these
  columns. This is the schedule's analysis input.
- **Window rule:** a field may use another row's **result** only when that row kicked off before
  this match. S3.01–02 read other rows' **kickoff times** only, never their results.

## A. Position in the round

| # | field | formula | row window | type | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| S3.01 | `s3_match_index_in_round` | position of the match in its round by kickoff (1 = earliest); team names break ties. **Do not read 1 as "first match of the round"**: many matches share the earliest kickoff, and the tie-break is alphabetical | kickoff times of the finished rows of the same season, stage and round | int | 4 | before | input | ✓ | keep; formula moves from the scraper to stage 3 |
| S3.02 | `s3_matches_in_round` | number of finished matches in the round | the same rows | int | 10 | before | check | ✓ | keep; **now finished matches only** (plan Q1). A QA check flags a round with fewer than teams ÷ 2 |
| S3.09 | `s3_days_off_round` | this kickoff minus the median kickoff of its stage and round, in days: positive for a match played after its round, negative for one brought forward | kickoff times of the finished rows of the same season, stage and round (never their results) | float | −0.48 (Wolves v Arsenal, round 31, played 18 Feb: −30.95) | before | indicator, read-only for now (the user, 2026-10-10) |  | add (2026-10-10) |
| S3.10 | `s3_is_rescheduled` | abs(S3.09) ≥ `features/schedule_multi.py:RESCHEDULED_AFTER_DAYS` (5) | through S3.09 | bool | False (Wolves v Arsenal: True) | before | indicator, read-only for now (the user, 2026-10-10) |  | add (2026-10-10). Not S3.07 (§C), whose survey wording misfires on a brought-forward match |

The user's ✓ on S3.01–02 was given when they were scrape-derived (2026-10-05). The meaning is the
same; only S3.02 now leaves out matches never played.

**S3.09–10, the rescheduled match** (2026-10-10): the edge-case indicator kept; the forfeit and
abandoned flags (S2.30–31) were dropped the same day (the user). On 74 leagues, 1,012 of 36,682
matches (2.8%) are 5 or more days off their round: 768 later, 244 earlier. Such matches lack
Bet365's opening odds about 7 times as often as the rest. Under 5 days a long round (Friday to
Monday, a midweek split) still counts; the count barely changes from 5 to 7 days. A round with
half its matches moved has its median between the two groups: rare, and visible in S3.09.

## B. Pre-kickoff table (rebuilt from our own results)

**Decided by the user, 2026-10-06.** Each match gets the full standings table as it stood at its
own kickoff, rebuilt from the stored results, not scraped. The 2 h 30 min rule: a match counts only
if it kicked off at least 2 h 30 min before this one, so it has surely finished.

- Same table columns as the page: R, P, W, D, L, GD, PTS, plus goals for (GF), which the rank's
  tie-break needs.
- Rank: points, then goal difference, then goals for, in every league. A league that breaks ties
  by head-to-head gets a slightly different rank, only for teams level on points. Measured on the
  54 DEV seasons (2026-10-07): the page uses head-to-head in Spain, Portugal, Italy and Poland and
  most wins in Belgium; the user accepted the difference, since every count stays exact.
- Points: earned on the pitch. Points deductions are not applied (option A, the user, 2026-10-07;
  the 16 known ones are in `notes/POINTS_DEDUCTIONS.md`). Option C, later, applies each one from
  its date.
- One table per stage, as the page shows them. A league whose points carry from one stage into the
  next (Scotland's split, Belgium's halved points) needs the earlier stage added: settled per
  league when one is configured. EPL and the Africa leagues have one stage.
- No leak by design: measured 0 in all 7 stored files. The one assumption: a match finishes within
  2 h 30 min of its listed kickoff (a normal match takes about 1 h 55 min).
- Matches of the same round can see each other's results when one finished before the other's
  kickoff. That is what both teams knew at kickoff. The last round or two usually kick off
  together, so there they share one table.

| # | field | formula | row window | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|---|
| S3.03 | `s3_{side}_pre_{half}_{venue}_{stat}` — side `home` / `away`, half `ft` / `ht`, venue `total` / `home` / `away`, stat `rank`, `played`, `won`, `drawn`, `lost`, `goals_for`, `goal_diff`, `points`. 2 × 2 × 3 × 8 = 96 columns | the side's line in the table built from the window's results: `ft` from FT goals, `ht` from HT goals; `home` / `away` count only the team's home / away matches | matches of the same season and stage that kicked off at least 2 h 30 min before this kickoff | int | before 2789361, FT, Total: Chelsea rank 5, P 23, W 10, D 7, L 6, GF 39, GD 14, PTS 37; West Ham rank 18, P 23, W 5, D 5, L 13, GF 27, GD −18, PTS 20 | before | input | add |
| S3.04 | `s3_pre_rank_gap` | \|`s3_home_pre_ft_total_rank` − `s3_away_pre_ft_total_rank`\| | through S3.03 | int | 13 | before | input | add: replaces `position_gap` |

The first match of a season has an empty table: every count is 0 and the rank is empty.

**History of this decision (2026-10-06).** The page's `Round N` table counts by round number, so a
round X−1 table can hold results played after a round-X match (tested by the user: Arsenal P 27 in
`Round 27`, Man City P 35 in `Round 35`). A guard against that emptied 6–80% of rows. Three rebuild
rules were compared on the 7 files: per round (froze rounds at stale dates when one match was
brought forward), per 3-day piece of a round, and per match with 2 h 30 min. The user chose the
last: it never leaves out a finished result, needs no extra setting, and is right for the final
rounds, where results earlier in the same round change what teams play for. The rebuilt table
equalled the page's round-24 table for Chelsea, Arsenal and Man City.

## B2. Half-time / full-time record (team view)

**Decided by the user, 2026-10-07:** each team's half-time / full-time record before the
match, counted the same way as the pre-kickoff table (same stage, the 2 h 30 min rule), split
Total / Home / Away, stored as counts, from the team's own side ("team view"). It answers: up to
this kickoff, how does this team finish its matches given how it stood at half-time? `l_w` = it
trailed at half-time and won (a comeback), `w_l` = it led and lost (a blown lead).

| # | field | formula | row window | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|---|
| S3.08 | `s3_{side}_pre_htft_{venue}_{ht}_{ft}` — side `home` / `away`, venue `total` / `home` / `away`, ht and ft each `w` / `d` / `l`. 2 × 3 × 9 = 54 columns | how many of the side's matches went `ht` at half-time and `ft` at full time, each read from the side's own goals (`domain/standings.py:HalfTimeFullTime`) | as S3.03: matches of the same season and stage that kicked off at least 2 h 30 min before this kickoff | int | before 2789361, Chelsea, Total: W/W 8, W/D 0, W/L 2, D/W 2, D/D 4, D/L 2, L/W 0, L/D 3, L/L 2 | before | input | add |

- **Why the team view:** Total adds a team's home and away matches. On the betting slip a
  Chelsea comeback is 2/1 at home but 1/2 away, so a slip-view Total would add opposite events
  into one count. In the team view every cell is one event for one team, and Total = Home + Away.
- **Built-in checks** (tests, and 0 failures in 2,280 EPL cells): the 9 counts add up to
  `s3_{side}_pre_ft_{venue}_played`; the half-time sums of a row equal the HT standings' won /
  drawn / lost, and the full-time sums equal the FT standings'.
- **Checked against another stats site by the user, 2026-10-07:** Chelsea's whole 2025-26
  season (the last match's record plus that match) gives W/W 11 / 5 / 6, W/L 2 / 2 / 0 and L/W
  1 / 1 / 0 for Total / Home / Away, as on that site. Its one comeback is the reference match
  itself, which is why the row above shows L/W 0: a match never counts in its own record.
- **Reading it:** the counts are small (Chelsea trailed 5 times in its first 23 matches), so
  one result moves a cell a lot. Related rates (half-time trailing rate, blown-lead rate) died
  as predictors in `notes/RESULTS.md` §1 (Families A and B): testing a claim built on these
  counts needs the candidate protocol first.

## C. The survey's planned flags (`notes/PREREGISTRATION_SURVEY.md` §7.4)

| # | field | formula | row window | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|---|
| S3.05 | `s3_round_state` | at least 1 comeback (S2.26) in the same stage and round, in a match that kicked off 2 h 30 min or more before this one | rows of the same season, stage and round with kickoff ≤ this kickoff − 2 h 30 min | bool | ? | before | input | **deferred** to Phase S step 10, the survey build (claim #3) |
| S3.06 | `s3_{side}_prev_comeback_win` | the side's previous match in this league-season, by kickoff, was a comeback win for it (S2.27 or S2.28, on its side) | the side's rows of the same league-season with kickoff < this kickoff; the latest one | bool | ? | before | input | **deferred** to Phase S step 10 (claim #4) |
| S3.07 | `s3_out_of_round` | a round-X match that kicks off after the first kickoff of any round Y > X of the same stage | kickoff times of the same stage's later rounds that are earlier than this kickoff | bool | ? | before | input | **deferred** to Phase S step 10 (claim #5). **Problem with the definition**, below |

Survey claim #2 (table vs market) is built at analysis time from S3.03 and S2.17–19; it adds no
stored field.

**S3.07's definition, as the survey draft words it, misfires on a brought-forward match** (found
2026-10-06). EPL 2025-26's round 31 started with Wolves v Arsenal on 18 Feb, a month early. By
"kicks off after the first kickoff of any round Y > X", every match of rounds 27–30 (played after
18 Feb) is then out of round. Settle the wording at Phase S step 8 (`notes/IDEAS_2026-10-01.md`,
idea 13's list).

## D. Open points — Claude's, no user decision needed

- A league with stages whose points carry over: settled per league when one is configured (§B).
- Examples marked `?` are filled in P3, from the rebuilt files.
