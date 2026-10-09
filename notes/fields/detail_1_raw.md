# Detail — stage 1, raw

**Answers: where is each value on the page?** Every field here is read from the match's h2h
page and only parsed. The user checks each row on the page (✓).

- Page: <https://live11.nowgoal26.com/match/h2h-2789361> for the reference match.
- Files: `data/finished/1_raw/<country>_<league>_<season>_detail.csv` (one row per match) and
  `data/finished/1_raw/<country>_<league>_<season>_history.csv` (new: one row per history row, plan Q3).

## A. Match file — one row per match

| # | field | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| D1.01 | `match_id` | join key, same as S1.06 | text | URL `h2h-<id>` | 2789361 | before | key |  | keep |
| D1.02 | `d1_odds_bookmaker` | bookmaker whose 1X2 rows were read: Bet365 if listed, else the first row | text | odds table `table.team-table-other`, Company column | Bet365 | before | check |  | keep |
| D1.03 | `d1_odds_1x2_open_home` | Bet365 opening 1X2 price, home ("Initial" row) | float | odds table, Initial row, 1X2 cells | 1.40 | before | input |  | rename (today `odds1x2_init_home`) |
| D1.04 | `d1_odds_1x2_open_draw` | same, draw | float | same | 4.75 | before | input |  | rename (today `odds1x2_init_draw`) |
| D1.05 | `d1_odds_1x2_open_away` | same, away | float | same | 7.00 | before | input |  | rename (today `odds1x2_init_away`) |
| D1.06 | `d1_odds_1x2_close_home` | Bet365 "Live" 1X2 price, home. The page has a separate "In-Play" row (1.01 here), so "Live" is the last price before kickoff | float | odds table, Live row, 1X2 cells | 1.61 | before ? (closing) | input |  | rename (today `odds1x2_live_home`) |
| D1.07 | `d1_odds_1x2_close_draw` | same, draw | float | same | 4.33 | before ? | input |  | rename (today `odds1x2_live_draw`) |
| D1.08 | `d1_odds_1x2_close_away` | same, away | float | same | 5.00 | before ? | input |  | rename (today `odds1x2_live_away`) |
| D1.09 | `d1_strength_home` | the page's strength rating, home (home + away = 100) | int | "Strength Comparison" block, `[class*='strength']` | 67 | before ? | input |  | keep |
| D1.10 | `d1_strength_away` | same, away | int | same | 33 | before ? | input |  | keep |
| D1.11 | `d1_h2h_compare_home_pct` | "H2H Comparison" bar, home share in % | float | Strength Comparison block | 84 | before ? | input |  | keep |
| D1.12 | `d1_h2h_compare_away_pct` | same, away | float | same | 16 | before ? | input |  | keep |
| D1.13 | `d1_guess_home_pct` | "Who will win?" crowd vote for the home team, %. **Before kickoff the page shows only the vote count** | float | `div.guessingbox` | 83.6 | **after** ? (hidden before kickoff) | input |  | drop ? (not shown before kickoff) |
| D1.14 | `d1_guess_away_pct` | same, away | float | same | 16.4 | **after** ? | input |  | drop ? |
| D1.15 | `d1_home_next_fixture_days` | days from this match to the home team's next match ("N Days") | int | Fixture table `table.team-table-home`, first countdown | 3 | before | input |  | keep |
| D1.16 | `d1_away_next_fixture_days` | same, away team | int | Fixture table `table.team-table-guest` | 7 | before | input |  | keep |

## B. History file — one row per history row the page shows

The page has three history tables: the home team's recent matches (`tr1_*`), the away team's
(`tr2_*`) and the head-to-head matches (`tr3_*`), up to 20 rows each (2789361 has 20 h2h rows).
**Stage 1 stores every row.** The windows (6 per team; head to head at most 4, none older than 2
years) are applied in stage 3. A row's home and away are the history match's own teams, not this
match's.

Example: the first row of Chelsea's table for 2789361, Napoli 2-3 Chelsea (UEFA Champions
League, 28 Jan 2026).

| # | field | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| D1.17 | `for_match_id` | the match whose page shows this row | text | URL `h2h-<id>` | 2789361 | before | key |  | add |
| D1.18 | `section` | `home` (the home team's table), `away` (the away team's) or `h2h` | text | which table: rows `tr1_*`, `tr2_*`, `tr3_*` | home | before | key |  | add |
| D1.19 | `n` | the row's number in its table, 1 = most recent | int | row id `tr1_<n>` | 1 | before | key |  | add. Today the code numbers the parsed rows in page order; check in P2 that the id agrees |
| D1.20 | `d1_match_id` | the history match's id | int | row attribute `index` | 2861115 | before | key |  | keep |
| D1.21 | `d1_league_id` | its competition id (36 = EPL, 103 = UCL) | int | row attribute `name` | 103 | before | key, input |  | keep |
| D1.22 | `d1_date` | its kickoff, Berlin time with its offset. The page gives UTC | text | `span[name='timeData']`, attribute `data-t` | 2026-01-28 21:00+01:00 (stored today: 2026-01-28 20:00:00) | before | key, input |  | fix: convert from UTC to Berlin time |
| D1.23 | `d1_league` | competition name; the cell shows the short form ("UEFA CL") | text | first cell, `title` attribute, else its text | UEFA Champions League | before | key |  | keep |
| D1.24 | `d1_home_team_id` | the history match's home team | int | first team link, `soccerDbPage.team(<id>)` | ? (Napoli) | before | key, input |  | add. Check in P2 that the ids match S1.08's id space |
| D1.25 | `d1_away_team_id` | its away team | int | second team link | 24 ? (Chelsea, if the id space matches) | before | key, input |  | add |
| D1.26 | `d1_home_team_name` | its home team's name | text | first team link, text | Napoli | before | key |  | add |
| D1.27 | `d1_away_team_name` | its away team's name | text | second team link, text | Chelsea | before | key |  | add |
| D1.28 | `d1_ht_home_goals` | home side's goals at HT | int | `span[class^='hscore']`, shown "(2-1)" | 2 | before | input, check |  | keep |
| D1.29 | `d1_ht_away_goals` | away side's goals at HT | int | same | 1 | before | input, check |  | keep |
| D1.30 | `d1_ft_home_goals` | home side's goals at FT | int | `span[class^='fscore']` | 2 | before | input, check |  | keep |
| D1.31 | `d1_ft_away_goals` | away side's goals at FT | int | same | 3 | before | input, check |  | keep |
| D1.32 | `d1_odds_home` | that match's 1X2 price, home. Bookmaker and snapshot come from the table's own selector (Bet365; Initial or Final?) | float | cells 7–9 | 2.50 | before | input, check |  | keep ? (which snapshot? Settle in P2, then rename to `d1_odds_1x2_open_home` or `d1_odds_1x2_close_home`, rule 3) |
| D1.33 | `d1_odds_draw` | same, draw | float | same | 3.50 | before | input, check |  | keep ? |
| D1.34 | `d1_odds_away` | same, away | float | same | 2.63 | before | input, check |  | keep ? |
| D1.35 | `d1_corners_ft_home` | home side's corners, full match | int | Corner cell "4-1 (3-1)" | 4 | before | input |  | keep |
| D1.36 | `d1_corners_ft_away` | away side's corners, full match | int | same | 1 | before | input |  | keep |
| D1.37 | `d1_corners_ht_home` | home side's corners at HT | int | the part in brackets | 3 | before | input |  | keep; **store as int** (today `3.0`) |
| D1.38 | `d1_corners_ht_away` | away side's corners at HT | int | same | 1 | before | input |  | keep; store as int |

`before` here means the history match was played before this match. Stage 3 checks it: a row
dated at or after this match's kickoff is an error.

## C. Dropped from today's file

- History `ht_score`, `ft_score` — text copies of D1.28–31 (plan rule 1).
- The 7 per-row computed fields → `detail_2_row.md`. `is_home`, `opponent`, `result` →
  `detail_3_multi.md`.
- The 31 form and h2h averages → `detail_3_multi.md`, on the new windows.
- `implied_init_*`, `implied_live_*` → `detail_2_row.md`.
- The 18 wide history blocks (486 columns) → the history file (22 columns).

## D. On the page, not stored — candidates, decided in P2

| C | what the page shows | where | timing | proposal |
|---|---|---|---|---|
| C5 | the full odds table: about 17 bookmakers, each with Initial, Live and In-Play rows for AH, 1X2 and O/U. We keep Bet365 1X2 Initial and Live only. Before kickoff a bookmaker has only Initial and Live, and Live keeps moving | "Live Odds Comparison", `table.team-table-other` | Initial and Live before; **In-Play after** | add ? Bet365 AH and O/U Live (closing lines); other bookmakers ? (a market average) |
| C6 | **each team's standings before this match**: FT table (Total / Home / Away / Last 6: played, W, D, L, scored, conceded, points, rank, win %) and an HT table with the same columns. Chelsea shows 23 played before round 24 | `table.team-table-home` / `table.team-table-guest`, headed "[ENG PR-5] Chelsea" | before (verify on more matches) | add ? a cross-check for S3.03. It has goals for and against, which the league page lacks |
| C7 | history-row cells we skip: AH price, line, price; AH result (W/L); O/U result (O/U); the bookmaker and Initial/Final selector | `tr1_*` / `tr2_*` / `tr3_*` rows | before | add ? AH line and result |
| C8 | **Half Time / Full Time counts per team**, season to date: W/W, W/D, W/L, D/W, D/D, D/L, L/W, L/D, L/L (Chelsea: L/W 0, W/L 2). Filters "H-A" and "Same" | "Half Time / Full Time" | before | **skip** (2026-10-07): rebuilt from our own results as S3.08 (`schedule_3_multi.md` §B2), which matches this table for Chelsea (L/W 0, W/L 2) |
| C9 | goals distribution per team, season to date: matches with 0/1/2/3/4+ goals, 1st- and 2nd-half goals, goal timing in 10-minute buckets, first-goal timing | "Goals Distribution" | before | add ? could replace parts of the goal-timing averages that now need the live scrape |
| C10 | full-time / half-time goal difference counts: Win 2+, Win 1, Draw, Lose 1, Lose 2+ | "Full-time/Half-time Goal Difference" | before | ? |
| C11 | odds records over 23 games: AH win/draw/lose %, O/U over/draw/under %; "Historical Matches with Same Odds" | "Odds Statistics" | before | ? |
| C12 | injury and suspension lists: position, shirt number, name | "Injury and Suspension" | ? (the match date or today?) | ? |
| C13 | each team's lineup in its previous match: formation, starting XI, substitutes | "Last Match Lineups" | before ? | ? |
| C14 | the next 3 matches of each team: competition, date, home/away, opponent (we keep only the first countdown) | Fixture tables | before | ? |
| C15 | the crowd vote's counts (46 / 9) and the AH prices shown beside it | "Who will win?" | ? | skip ? |
| C21 | the match header: competition and stage, kickoff with weekday, **venue** and **weather** ("Partly sunny, 17℃～18℃") | page header, above the tabs | before | add ? venue and weather |

**No HT/FT odds on this page.**

## E. Evidence — read 5 h 40 min before kickoff (match 2981454, 2026-10-05)

| fields | readable before kickoff? | value then |
|---|---|---|
| D1.02–05 bookmaker and 1X2 Initial | yes | Bet365, 1.48 / 4.75 / 6.00 |
| D1.06–08 1X2 Live | yes, and it keeps moving | 1.36 / 5.25 / 7.50 |
| D1.09–12 strength, H2H comparison | yes | 67 / 33, 97 / 3 |
| D1.13–14 crowd vote % | **no**: hidden, the page shows only "Votes: 6" | None |
| D1.15–16 days to the next match | yes | 38 / 38 |
| history rows | yes: 20 home rows, 20 away, 5 H2H, every field filled | `home_last1`: France v Italy, 2026-10-02 18:45 |
| C5 odds table | Initial and Live rows only; **no In-Play row** | — |
| C6, C8, C9, C11–C14, C21 | yes | Giuseppe Meazza, partly sunny, 17–18 ℃ |
| C10 | not on this match's page | — |
| this match's own lineups | not yet posted | — |

The history date `2026-10-02 18:45:00` belongs to a 20:45 CEST kickoff, which confirms that the
page gives D1.22 in UTC.
