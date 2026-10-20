# Schedule — stage 1, raw

**Group: FIELDS.** One row per field. Never change a field code. The stage-1 docs are frozen after plan step P7.

**Answers: where is each value on the page?** Every field here is read from the league page and
only parsed. The user checks each row on the page (✓).

- Page: the league page, <https://football.nowgoal50.com/league/2025-2026/36> for the reference
  match (round 24).
- Files: `data/finished/1_raw/<country>_<league>_<season>_schedule.csv` (before 2026-10-06:
  `<league>_<season>.csv`, now in `data/archived/raw/`) and `data/finished/1_raw/<country>_<league>_<season>_final_table.csv`
  (new, a check only). `<country>` is the config's country, `<league>` the league's name in the
  page's title (2026-10-08: the title alone can leave the country out). A name that already starts
  with the exact country keeps it once: `brazil_serie_a`, but `england_english_premier_league`.

## A. Match file — one row per finished match

| # | field | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| S1.01 | `s1_season` | season label from the league URL, stored as written: `2025-2026` (cross-year) or `2025` (calendar-year) | text | config URL `/league/<season>/<id>` | 2025-2026 | before | key, input | ✓ | keep |
| S1.02 | `s1_league_id` | nowgoal's league id | int | config URL `/league/<season>/<id>` | 36 | before | key, input | ✓ | keep |
| S1.03 | `s1_league_name` | league name from the page title. **Stored as a slug**; the page shows "English Premier League" | text | page `<title>`, after " - " and the season | english_premier_league | before | key | ✓ | keep |
| S1.04 | `s1_stage` | name of the stage tab; empty when the page has no tabs | text | `div#schedule div.stage span[stage]` (active tab) | (empty) | before | key, input | ✓ | keep |
| S1.05 | `s1_round` | round number inside the stage | int | `div#schedule div.round span[round]` (clicked round) | 24 | before | key, input | ✓ | keep |
| S1.06 | `match_id` | nowgoal's match id; the join key of every file | text | row `div.schedulis`, attribute `matchid` | 2789361 | before | key | ✓ | keep |
| S1.07 | `s1_date` | kickoff date and time, Berlin time with its offset. **The page gives UTC+8 (China time). The files before 2026-10-06 stored it unconverted**: the match was played on Saturday 31 Jan at 17:30 UK time | text | row `span.date`, attribute `data-t` | 2026-01-31 18:30+01:00 (stored before 2026-10-06: 2026-02-01 01:30) | before | key, input, check | ✓ | fixed 2026-10-06: `data-t` is converted from UTC+8 to Berlin time |
| S1.08 | `s1_home_team_id` | nowgoal's id of the home team | int | row `span.home span[onclick]` → `toTeam('<id>')` | 24 | before | key, input | ✓ | keep |
| S1.09 | `s1_away_team_id` | nowgoal's id of the away team | int | row `span.away span[onclick]` | 62 | before | key, input | ✓ | keep |
| S1.10 | `s1_home_team_name` | home team name as shown, with accented letters replaced | text | row `span.home` | Chelsea | before | key | ✓ | keep |
| S1.11 | `s1_away_team_name` | away team name as shown | text | row `span.away` | West Ham United | before | key | ✓ | keep |
| S1.12 | `s1_ht_home_goals` | home goals at half-time | int | row `span.ht` ("0-2"), first number | 0 | after | label, check | ✓ | keep |
| S1.13 | `s1_ht_away_goals` | away goals at half-time | int | row `span.ht`, second number | 2 | after | label, check | ✓ | keep |
| S1.14 | `s1_ft_home_goals` | home goals at full time | int | row attribute `score` ("3 - 2"), else `span.score`; first number | 3 | after | label, check | ✓ | keep |
| S1.15 | `s1_ft_away_goals` | away goals at full time | int | same, second number | 2 | after | label, check | ✓ | keep |
| S1.16 | `s1_odds_1x2_open_home` | opening 1X2 price, home win, decimal | float | row `span.odds > span` [1st], odds header set to 1X2 | 1.40 | before | input | ✓ | keep for now (was `home_win_initial_odds` before 2026-10-06). **Equals D1.03 in 99.7% of EPL rows**: the user reviews duplicates later |
| S1.17 | `s1_odds_1x2_open_draw` | opening 1X2 price, draw | float | row `span.odds > span` [2nd], header 1X2 | 4.75 | before | input | ✓ | keep for now (was `draw_initial_odds` before 2026-10-06); duplicate of D1.04 |
| S1.18 | `s1_odds_1x2_open_away` | opening 1X2 price, away win | float | row `span.odds > span` [3rd], header 1X2 | 7.00 | before | input | ✓ | keep for now (was `away_win_initial_odds` before 2026-10-06); duplicate of D1.05 |
| S1.19 | `s1_odds_ou_open_line` | opening goal line, Asian. A quarter line "3/3.5" is a split bet, half the stake on 3 and half on 3.5, stored as their average 3.25 (`scrapers/parsers.py:parse_line`). Lossless: a .25 or .75 line always splits into the two nearest lines | float | row `span.odds > span` [2nd], header OU | 3.25 | before | input | ✓ | renamed 2026-10-06 (was `ou_line`) |
| S1.20 | `s1_odds_ou_open_over` | opening over price, decimal, as the row shows it (the code converts nothing) | float | row `span.odds > span` [1st], header OU | 1.98 | before | input | ✓ | renamed 2026-10-06 (was `over_odds`) |
| S1.21 | `s1_odds_ou_open_under` | opening under price, decimal | float | row `span.odds > span` [3rd], header OU | 1.88 | before | input | ✓ | renamed 2026-10-06 (was `under_odds`) |
| S1.22 | `s1_odds_ah_open_line` | opening Asian handicap line. A quarter line "1/1.5" is stored as 1.25, the same way as S1.19. nowgoal's sign: positive = the home team gives the handicap (verified 10/10 against the 1X2 favourite); a bookmaker writes the same bet as Chelsea −1.25 | float | row `span.odds > span` [2nd], header AH | 1.25 | before | input | ✓ | renamed 2026-10-06 (was `ah_line`) |
| S1.23 | `s1_odds_ah_open_home` | opening AH price, home, decimal | float | row `span.odds > span` [1st], header AH | 1.83 | before | input | ✓ | renamed 2026-10-06 (was `ah_home_odds`) |
| S1.24 | `s1_odds_ah_open_away` | opening AH price, away, decimal | float | row `span.odds > span` [3rd], header AH | 2.03 | before | input | ✓ | renamed 2026-10-06 (was `ah_away_odds`) |

**Checked by the user on 2026-10-06 (sitting 1):** S1.12–18, S1.20–21, S1.23–24, all values as stored. The over price shows 1.98 on the row, so the old note "the page shows Hong Kong odds" was wrong. S1.19 and S1.22 were ticked after the quarter-line meaning was explained (same day).

The user's note on S1.01–11 (2026-10-05): these can be read before kickoff (but only for the next
round or two, not the whole season ahead), during the match and after it. Not yet verified; check
it when `data/scheduled/` is built.

## B. Final-table file — one row per team, read once per league-season

**Decided by the user, 2026-10-06:** the standings are **rebuilt from our own results**
(`SCHEDULE_3_MULTI.md` §B), not scraped round by round. This file keeps one table from the page,
the final one, as a check: `qa/final_table.py` (run by `qa.validate`) compares it with our rebuilt
final table, stage by stage. EPL 2025-26 passed on 2026-10-07, 20/20 teams. A difference means a
points deduction, a missing match or a wrong score. It is the `Total` view of the standings, FT,
Total, as the page shows it at scrape time (for a finished season, the final table).

The user checked these columns on 2026-10-06 in the `Round 24` view, which has the same columns:
Chelsea (rank 5, P 24, W 11, D 7, L 6, GD 15, PTS 40), Arsenal (P 24, W 16, D 5, L 3, GD 29, PTS
53) and Man City (2nd, P 24, W 14, D 5, L 5, GD 26, PTS 47) all equalled the table rebuilt from our
own results. The examples below are our rebuilt final table for Chelsea; the page's value is
compared by the code.

| # | field | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| S1.25 | `season` | same as S1.01 | text | config URL | 2025-2026 | — | key | ✓ (as S1.01) | add |
| S1.26 | `league_id` | same as S1.02 | int | config URL | 36 | — | key | ✓ (as S1.02) | add |
| S1.27 | `stage` | the stage the table belongs to; empty without stage tabs. A league with stages has one table per stage | text | the stage the standings are synced to | (empty) | — | key | ✓ (as S1.04) | add |
| S1.31 | `team_id` | the team's id | int | row `toTeam(<id>)`, `ul#standingList li.standlis` | 24 | — | key | ✓ (the user kept it, 2026-10-07; value verified by the QA check: 20/20 ids match S1.08–09) | add |
| S1.32 | `s1_team_name` | the team's name as shown | text | same row | Chelsea | — | key | ✓ | add |
| S1.33 | `s1_rank` | the team's position in the final table | int | `span.rank em` | 10 | after the season | check | ✓ | add |
| S1.34 | `s1_played` | matches played (P) | int | the row, column P | 38 | after the season | check | ✓ | add |
| S1.35 | `s1_won` | W | int | column W | 14 | after the season | check | ✓ | add |
| S1.36 | `s1_drawn` | D | int | column D | 10 | after the season | check | ✓ | add |
| S1.37 | `s1_lost` | L | int | column L | 14 | after the season | check | ✓ | add |
| S1.38 | `s1_goal_diff` | GD. The page has no goals for or against, only GD | int | column GD | 6 | after the season | check | ✓ | add |
| S1.39 | `s1_points` | PTS | int | column PTS | 52 | after the season | check | ✓ | add |

Role `check` only: this table is never an input. Pre-kickoff standings come from S3.03.

## D. On the page, not stored — candidates, decided in P2

| C | what the page shows | where | timing | proposal |
|---|---|---|---|---|
| C1 | the standings per round, 6 tables | `#standingBox` | after round N | **decided 2026-10-06: not scraped**; rebuilt in S3.03, the final table read as a check (§B) |
| C2 | the row's match state code (`-1` on finished rows, `0` on upcoming ones) | row attribute `state` | — | **skip** (the user, 2026-10-06); revisit with `data/scheduled/` |
| C3 | season tables: team goals, HT/FT results, goal timings, goal differences, correct scores, team stats (shots, possession, corners, fouls, cards) | "Statistics" section | after (season totals as of the scrape) | **skip** (the user, 2026-10-06): season totals, never usable before kickoff; its useful parts are rebuilt from our own per-match data |
| C4 | player stats, odds stats (win %), outright odds | "Tech Stats", "ODDS STATS", "OUTRIGHTS ODDS" | — | **skip** (the user, 2026-10-06): not match fields |

The odds header offers AH, 1X2 and OU only. **No HT/FT odds on this page.**

## E. Evidence

- **Opening odds:** S1.19–24 equal the Bet365 "Initial" row on the detail page for 2789361, lines
  and prices. Confirm on the page in P2.
- **Missing odds mean Bet365 did not price the match** (the user, 2026-10-10, on the h2h pages of
  one match without schedule odds and one with): the schedule shows Bet365's prices only. The h2h
  page's odds table also lists 18Bet, Ladbrokes, Vcbet, Interwetten, Sbobet, M88, 12Bet, Crown,
  Easybet and Macauslot, which can price a match Bet365 left out. So `s2_has_odds` False means
  "no Bet365 odds", not "no market". The h2h page agrees: for 2604629 (played 228 days after its
  round) Bet365's row is empty in every snapshot and market, and one other bookmaker priced only
  1X2 and O/U (the user, 2026-10-10). So the detail page cannot fill a schedule gap from Bet365.
- **Duplicates:** S1.16–18 equal D1.03–05 in 99.7% of 379 EPL 2025-26 rows.
- **A market the match does not carry** (found 2026-10-08): its odds cells keep the previous
  market's numbers when the header switches, so 97 rows stored their 1X2 prices as S1.19–24 and
  one stored its AH as S1.16–18. The scraper now leaves such a market empty
  (`scrapers/schedule.py:drop_stale_odds`); files scraped before then keep the rows until re-scraped.
- **The standings section** (EPL 2026-27 page, read 2026-10-05): the round dropdown lists `Total`
  plus one entry per finished round. `Round N` is the table after round N; `Total` is the table
  now. The FT / HT and Total / Home / Away filters combine with any finished round. Columns: rank,
  team, P, W, D, L, GD, PTS.
- **Answered: "Round N" counts by round number** (tested by the user, 2026-10-06: Arsenal P 27 in
  `Round 27`, Man City P 35 in `Round 35`). The table holds every match of rounds 1–N, whenever it
  was played, as seen today. The question (the user: "we really have to double check how the
  round X dropdown works"). Two EPL 2025-26 matches were played out of round order, and one number
  each settles it:
  - brought forward: Wolves v Arsenal (round 31) was played on 18 Feb, between rounds 26 and 27.
    Arsenal's P in the `Round 27` table: **27** = the table counts by round number; **28** = it
    counts everything played by the end of round 27;
  - postponed: Man City v Crystal Palace (round 31) was played on 13 May, after round 35. Man
    City's P in the `Round 35` table: **35** = by round number; **34** = by date.
  By round number, the round X−1 table can count a result played after this match's kickoff; the
  guard in `SCHEDULE_3_MULTI.md` §B empties those rows. By date, a brought-forward result is in
  the table and a postponed one is not.
- **Upcoming rows** (same read, for `data/scheduled/` later): an upcoming row has the ids, teams,
  round, kickoff and the three odds markets; the FT and HT scores are `-` and empty; `state` is 0.
