# Schedule — stage 3, needs other rows

**Answers: which other rows does it read, and are they all before kickoff?** Every field here
needs more than its own row. This is the only place cross-row leakage can enter, so every field
states its **row window**. Claude writes them; the stats-reviewer agent checks them.

- Reads: the schedule file of stage 2 (S3.03 rebuilds the standings from its results).
- File: `data/finished/3_multi/<country>_<league>_<season>_schedule.csv` = the stage-2 file plus these
  columns. This is the schedule's analysis input.
- **Window rule:** a field may use another row's **result** only when that row kicked off before
  this match. S3.01–02, S3.09–10, S3.11 and S3.14 read other rows' **kickoff times** only, never
  their results.

## A. Position in the round

| # | field | formula | row window | type | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| S3.01 | `s3_match_index_in_round` | position of the match in its round by kickoff (1 = earliest); team names break ties. **Do not read 1 as "first match of the round"**: many matches share the earliest kickoff, and the tie-break is alphabetical | kickoff times of the finished rows of the same season, stage and round | int | 4 | before | input | ✓ | keep; formula moves from the scraper to stage 3 |
| S3.02 | `s3_matches_in_round` | number of finished matches in the round | the same rows | int | 10 | before | check | ✓ | keep; **now finished matches only** (plan Q1). A QA check flags a round with fewer than teams ÷ 2 |
| S3.09 | `s3_days_off_round` | this kickoff minus the median kickoff of its stage and round, in days: positive for a match played after its round, negative for one brought forward | kickoff times of the finished rows of the same season, stage and round (never their results) | float | −0.48 (Wolves v Arsenal, round 31, played 18 Feb: −30.95) | before | indicator, read-only for now (the user, 2026-10-10) |  | add (2026-10-10) |
| S3.10 | `s3_is_rescheduled` | abs(S3.09) ≥ `features/schedule_multi.py:RESCHEDULED_AFTER_DAYS` (5) | through S3.09 | bool | False (Wolves v Arsenal: True) | before | indicator, read-only for now (the user, 2026-10-10) |  | add (2026-10-10). Not S3.07 (§C), whose survey wording misfires on a brought-forward match |

The user's ✓ on S3.01–02 was given when they were scrape-derived (2026-10-05). The meaning is the
same; only S3.02 now leaves out matches never played.

**S3.09–10, the rescheduled match** (2026-10-10): the edge-case indicator. On 74 leagues, 1,012 of 36,682
matches (2.8%) are 5 or more days off their round: 768 later, 244 earlier. Such matches lack
Bet365's opening odds about 7 times as often as the rest. Under 5 days a long round (Friday to
Monday, a midweek split) still counts; the count barely changes from 5 to 7 days. A round with
half its matches moved has its median between the two groups: rare, and visible in S3.09.

## A2. The round so far

**Chosen by the user, 2026-10-13:** running counts of the project's two rare events (a comeback,
7+ goals) among the matches of the same round already played, under the 2 h 30 min rule, a match
that was both counting once in S3.17. The 5-day look-back is Claude's choice, which the user
asked for. Later the same day the round's goals joined them (S3.18–20, the user's choice from
Claude's proposal C): how many round-mates ended with both teams scoring, and their average
goals beside their average opening O/U line, so the difference shows how far the round's
finished matches scored above or below their opening lines.

| # | field | formula | row window | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|---|
| S3.14 | `s3_round_pre_finished` | how many matches of the same stage and round kicked off at least 2 h 30 min and less than `features/schedule_multi.py:ROUND_LOOK_BACK` (5 days) before this kickoff | the round's rows: kickoff times only | int | before 2789361: 3 (it is the 4th of 10 in its round) | before | input | add (2026-10-13) |
| S3.15 | `s3_round_pre_comebacks` | of S3.14's matches, how many were comebacks (S2.26) | S3.14's matches and their results | int | 0 | before | input | add (2026-10-13) |
| S3.16 | `s3_round_pre_seven_plus` | of S3.14's matches, how many had 7 or more goals (S2.01 ≥ `SEVEN_PLUS_GOALS`) | as S3.15 | int | 0 | before | input | add (2026-10-13) |
| S3.17 | `s3_round_pre_rare_events` | of S3.14's matches, how many were a comeback or had 7 or more goals; a match that was both (a 4-3 comeback) counts once | as S3.15 | int | 0 | before | input | add (2026-10-13) |
| S3.18 | `s3_round_pre_btts` | of S3.14's matches, how many ended with both teams scoring (S1.14 ≥ 1 and S1.15 ≥ 1) | as S3.15 | int | 1 (Brighton 1-1; Leeds 0-4 and Wolves 0-2 did not) | before | input | add (2026-10-13) |
| S3.19 | `s3_round_pre_avg_goals` | the average goals (S2.01) of S3.14's matches that have an opening O/U line (S1.19); empty when none has | as S3.15 | float | 2.67 (2, 4 and 2 goals) | before | input | add (2026-10-13) |
| S3.20 | `s3_round_pre_avg_ou_line` | the average opening O/U line (S1.19) of the same matches as S3.19; empty when S3.19 is | S3.14's matches and their opening lines | float | 2.58 (2.5, 2.5 and 2.75) | before | input | add (2026-10-13) |

- **Zeros:** the first kickoff of a round sees 0 in every count and empty averages, and so does
  any match that kicks off before a round-mate has finished. S3.14 is 0 for 32.9% of matches.
- **S3.19 against S3.20:** the difference is how far the round's finished matches scored above
  or below their opening lines, computed at analysis time (2789361: +0.08). It is not centred
  at 0: the opening line is the market's 50/50 point, not its expected goals, and a match
  scores 0.126 goals above its line on average (+0.22 at a line of 2, +0.01 at 3.5), so a
  round that goes as priced reads about +0.12. Compare rounds with each other, not with 0:
  2789361's round-mates would typically read +0.12, so their +0.08 is slightly below that.
  The average alone mostly repeats the league's goal level, which this match's own odds
  already carry. Both averages cover the same matches, so a round-mate without a line is left
  out of both: 21 rows have a finished round-mate but no line among them. The line ranks
  matches like a goal model fitted to the opening odds (correlation 0.982,
  `notes/runs/2026-10-09_corpus_scan/out_2026-10-09/a3_model.txt`) but sits below it in
  level. Read either average with S3.14: after one finished match it is that match's own
  score.
- **S3.18 and the rare events:** every comeback has both teams scoring (the leader scored
  before half-time, the trailer has to score to win), so S3.15 ≤ S3.18 by definition.
- **The 5-day look-back:** a round-mate played 5 or more days earlier (a match brought forward;
  for a postponed match, the rest of its round) does not count, so a result from weeks before
  is not "this round so far". It reads no later kickoff, unlike S3.10. Measured on kickoff
  times, 2026-10-13: 30 matches played on schedule lose a round-mate played 5 or more days
  earlier, and the look-back changes which round-mates count on 777 rows (2.1%) against
  leaving out S3.10's rescheduled matches instead.
- **Values, 2026-10-13:** S3.17 is 1 or more for 14.7% of matches (S3.15 for 11.1%, S3.16 for
  5.0%); none is above 3 (`notes/runs/2026-10-13_round_so_far/out.txt`). S3.18 is 1 or more
  for 56.1%, and S3.19–20 have a value for 67.0% (`notes/runs/2026-10-13_round_goals/out.txt`).
- **Checked 2026-10-13:** a recount with plain loops gave the same values on all 36,238 rows,
  for S3.14–17 and for S3.18–20; scrambling the results and lines of every match outside the
  window (the match's own included) moved none of 150 sampled matches' values, in each run.
  Run records: `notes/runs/2026-10-13_round_so_far/` (`verify_round.py`, `out.txt`) for
  S3.14–17 and `notes/runs/2026-10-13_round_goals/` (`verify_round_goals.py`, `out.txt`) for
  S3.18–20, on disk only: `notes/runs/` is gitignored.

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

## B3. What is at stake

**Chosen by the user, 2026-10-12,** from Claude's brainstorm of that day. The hypothesis they
are built for (untested, `notes/MARKET_COMEBACKS.md` §5 Q15, still open): how hard a side
chases a deficit or protects a lead depends on what the result is worth to it, beyond what the
opening 1X2 price carries. All three read the FT Total table of §B or the stage's fixture
list. None needs the zone sizes (promotion, play-off and relegation places), which no file
holds.

| # | field | formula | row window | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|---|
| S3.11 | `s3_{side}_pre_matches_left` | the side's matches in this stage from this one on, this one included: 1 = its last match of the stage | the side's rows of the same season and stage: that they exist and their kickoff times (the fixture list), never their results | int | before 2789361: Chelsea 15, West Ham 15 | before | input | add (2026-10-12) |
| S3.12 | `s3_{side}_pre_pts_to_{dir}` — dir `above` / `below` | `above`: how many points the side trails the nearest team with more points by; `below`: how many it leads the nearest team with fewer points by, in the FT Total table of S3.03 (`domain/standings.py:Standings.points_gaps`). Empty when no team has more (fewer) points | as S3.03 | int | Chelsea 1 / 1, West Ham 5 / 5 | before | input | add (2026-10-12) |
| S3.13 | `s3_{side}_rank_change_since_open` | the side's FT Total rank (S3.03) minus its rank `features/schedule_multi.py:OPEN_LEAD` (7 days) before kickoff, when the opening odds were published: positive = it fell, negative = it climbed. Empty when either rank is | as S3.03, at two instants: matches that kicked off at least 2 h 30 min before this kickoff, and at least 2 h 30 min before this kickoff minus 7 days | int | Chelsea −1, West Ham 0 | before | input | add (2026-10-12) |

- **S3.11 reads later rows, but only that they exist.** The fixture list is known before the
  season, and every kept stage is a k-fold round robin (`qa/schedule.py`), so the count is the
  format's: in all 144 league-seasons every team of a stage has the same total.
- **S3.12 reads points only.** A team level on points is neither above nor below, whatever the
  tie-break, so a league that breaks ties by head-to-head (§B) gets the same gaps.
- **S3.13's one assumption:** the opening price is published about 7 days before kickoff (the
  user, 2026-10-10, `notes/fields/README.md`); it varies by league. A result between the two
  instants is news the opening odds cannot hold, the side's own included (a midweek match).
  Measured on the rebuilt files, 2026-10-12: the rank changed for 51.3% of the 69,380
  team-matches with a rank at both instants, by 3 or more places for 10.4%; over the last 3
  days alone, 24.9% and 2.3%. Moves of 10 or more places come almost all from the first rounds,
  when the table is thin.
- **Checked 2026-10-12:** both tables rebuilt from scratch for every match of three
  league-seasons (EPL 2025-26, Liga MX 2025-26, Venezuela 2025 with its four-team Apertura-B)
  gave the same S3.12–13 values; scrambling every result that kicked off less than 2 h 30 min
  before kickoff, or later, moved none of 120 sampled matches' S3.11–13 values (a scratch
  script, not a repo command); S3.11 counts down to 1 for every team.
- **Reading it:** these are building blocks of "what is at stake", not a test of it. A
  zone-based version (points to the promotion, play-off and relegation lines, a "nothing left
  to play for" flag) needs a zone table per league-season first.

## C. Planned flag

| # | field | formula | row window | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|---|
| S3.07 | `s3_out_of_round` | a round-X match that kicks off after the first kickoff of any round Y > X of the same stage | kickoff times of the same stage's later rounds that are earlier than this kickoff | bool | ? | before | input | **deferred** until IDEAS idea 13 settles the out-of-round definition. **Problem with the definition**, below |

**S3.07's definition misfires on a brought-forward match** (found
2026-10-06). EPL 2025-26's round 31 started with Wolves v Arsenal on 18 Feb, a month early. By
"kicks off after the first kickoff of any round Y > X", every match of rounds 27–30 (played after
18 Feb) is then out of round. Settle the wording in `notes/IDEAS_2026-10-01.md` idea 13.

## D. Open points — Claude's, no user decision needed

- A league with stages whose points carry over: settled per league when one is configured (§B).
- Examples marked `?` are filled in P3, from the rebuilt files.
