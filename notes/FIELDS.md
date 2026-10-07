# FIELDS — every field, defined once

> **Superseded 2026-10-05 by `notes/fields/`** (one doc per stage, step P1 of
> `notes/PLAN_2026-10-05_staged_pipeline.md`). Every row, example and check below was carried
> over. This file is no longer updated. It is kept only until the user confirms the split; it was
> never committed, so deleting it cannot be undone.

**Status: draft v0, written by Claude on 2026-10-05. The user's pass started the same day: S1 done.**

**Progress: base fields checked 13 / 90 · page candidates decided 0 / 22 · derived fields classified 0 / 3 sections**

This file is the data dictionary (idea 17). It also holds the naming and format rules (idea 16)
and the inventory of the fields we do not store yet (idea 12b). The refactor (ideas 14b and 2)
is built from it.

## How this file works

- **One row per field.** A field defined here is not defined again anywhere else.
- **Base fields (sections 1–3)** are read from a page. The user goes through them **one by one**
  on match 2789361 and checks the location on the page, the meaning, the value, the timing and the
  role, then ticks ✓. Claude fills every row in first.
- **Derived fields (sections 4–6)** are computed in Python. Claude writes them; the user skims one
  summary per section.
- `?` = not known yet, to settle in the session. **bold** = a problem found while drafting.
- Status: `keep`, `drop`, `rename → new_name`, `add`. A status with `?` is Claude's proposal.

## Rules — to confirm in session S0

1. **Class**
   - `raw`: one value read from one place on the page (or from the config URL), typed.
   - `scrape-derived` (working name): the scraper computes it from the page's context — the
     other rows of the round, the team a history table belongs to, the running score. It stays in
     `data/raw/` with today's calculation.
   - `derived`: Python computes it from stored fields, downstream in `features/`.
2. **Scope:** `base` (every market shares it: all raw and scrape-derived fields, plus the derived
   fields every market needs) or `comebacks` (for now the only market). A field is defined once;
   any number of market lists can name it. Labels of other markets wait for their market.
3. **Timing — the user's rule (2026-10-05): in every row, only the match's own score is after
   kickoff.** That means the HT and FT goals and every field computed from them (results, totals,
   comeback labels). Everything else in the row must be known before kickoff:
   - a field that is not known before kickoff is replaced or dropped. For example, the standings
     become the round X−1 table for a round-X match, not the round X table;
   - the match's own events, statistics and in-play odds never go into its own row. They only
     feed later matches' history, where they are `before`.

   The timing column says `before` or `after` under this rule.
4. **Role — one or more per field** (the user, 2026-10-05; for example `round` is `key, input`):
   - `key`: identifies a row, or links it to rows in another file;
   - `input`: may be used to predict. Only `before` fields can be inputs;
   - `label`: an outcome of this match. It is never an input for its own match;
   - `check` (open for discussion): a data-quality test reads it, for example the score against
     the goal store, or a history row against that match's own row. A field whose only role is
     `check`, like `matches_in_round` or `scraped_at`, is bookkeeping.
5. **Naming rules (idea 16), proposed:**
   - one name per fact: no field stored twice under two names;
   - typed values only: no score strings beside the goal columns;
   - odds as `odds_<market>_<snapshot>_<selection>`, with snapshot `open` (the page's "Initial")
     or `close` (the page's "Live"), stored as decimal odds;
   - no rounding in stored data; round only in reports;
   - a value known only after kickoff never has a name that reads like a pre-match value.
6. **Dates and times are stored in UTC** (decided by the user, 2026-10-05). The league page gives
   UTC+8 and the h2h page gives UTC, so the scraper converts the league page's value.
7. **Reference match:** 2789361, Chelsea v West Ham, English Premier League 2025-26, round 24:
   0-2 at HT, 3-2 at FT, a red card, quarter lines (AH 1.25, O/U 3.25).
   - League page: <https://football.nowgoal26.com/league/2025-2026/36> (round 24)
   - Detail page: <https://live11.nowgoal26.com/match/h2h-2789361>
   - Live page: <https://live11.nowgoal26.com/match/live-2789361>

## 1. League page — `data/raw/<league>_<season>.csv`

All rows below are scope `base`.

### 1a. Session S1 — identity, teams, round

| # | field | class | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `season` | raw (config URL) | season label from the league URL, stored as written: `2025-2026` (cross-year) or `2025` (calendar-year) | text | config URL `/league/<season>/<id>` | 2025-2026 | before | key, input | ✓ | keep |
| 2 | `league_id` | raw (config URL) | nowgoal's league id | int | config URL `/league/<season>/<id>` | 36 | before | key, input | ✓ | keep |
| 3 | `league_name` | raw | league name from the page title. **Stored as a slug**; the page shows "English Premier League" | text | page `<title>`, after " - " and the season | english_premier_league | before | key | ✓ | keep |
| 4 | `stage` | raw | name of the stage tab; empty when the page has no tabs | text | `div#schedule div.stage span[stage]` (active tab) | (empty) | before | key, input | ✓ | keep |
| 5 | `round` | raw | round number inside the stage | int | `div#schedule div.round span[round]` (clicked round) | 24 | before | key, input | ✓ | keep |
| 6 | `match_id` | raw | nowgoal's match id; the join key of every file | text | row `div.schedulis`, attribute `matchid` | 2789361 | before | key | ✓ | keep |
| 7 | `date` | raw | kickoff date and time. **It is UTC+8 (China time), not UTC**: the match was played on Saturday 31 Jan at 17:30 UK time | text | row `span.date`, attribute `data-t` | 2026-02-01 01:30 | before | key, input, check | ✓ | fix: store UTC (`data-t` − 8 h) |
| 8 | `home_team_id` | raw | nowgoal's id of the home team | int | row `span.home span[onclick]` → `toTeam('<id>')` | 24 | before | key, input | ✓ | keep |
| 9 | `away_team_id` | raw | nowgoal's id of the away team | int | row `span.away span[onclick]` | 62 | before | key, input | ✓ | keep |
| 10 | `home_team_name` | raw | home team name as shown, with accented letters replaced | text | row `span.home` | Chelsea | before | key | ✓ | keep |
| 11 | `away_team_name` | raw | away team name as shown | text | row `span.away` | West Ham United | before | key | ✓ | keep |
| 12 | `match_index_in_round` | scrape-derived | position of the match in its round by kickoff (1 = earliest); team names break ties | int | computed from the round's rows | 4 | before | input | ✓ | keep |
| 13 | `matches_in_round` | scrape-derived | number of scheduled matches in the round, played or not | int | count of the round's rows | 10 | before | check | ✓ | keep |

**Checked by the user on 2026-10-05:** all 13 rows as drafted, except #7, which must be stored in
UTC. The user's note on when these fields can be read: before kickoff (but only for the next
round or two, not the whole season ahead), during the match, and after it. Not yet verified;
check it when the upcoming-match scrape (idea 6) is built.

### 1b. Session S2 — scores, odds, standings

| # | field | class | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 14 | `ht_score` | raw | half-time score as text | text | row `span.ht` | 0-2 | after | label |  | drop ? (same facts as 16–17) |
| 15 | `ft_score` | raw | full-time score as text, spaces around the dash | text | row attribute `score`, else `span.score` | 3 - 2 | after | label |  | drop ? (same facts as 18–19) |
| 16 | `ht_home_goals` | raw | home goals at half-time | int | row `span.ht` | 0 | after | label, check |  | keep |
| 17 | `ht_away_goals` | raw | away goals at half-time | int | row `span.ht` | 2 | after | label, check |  | keep |
| 18 | `ft_home_goals` | raw | home goals at full time | int | row attribute `score` | 3 | after | label, check |  | keep |
| 19 | `ft_away_goals` | raw | away goals at full time | int | row attribute `score` | 2 | after | label, check |  | keep |
| 20 | `home_win_initial_odds` | raw | opening 1X2 price, home win, decimal | float | row `span.odds > span` [1st], odds header set to 1X2 | 1.40 | before | input | | drop ? (**equals #33 in 99.7% of EPL rows**) |
| 21 | `draw_initial_odds` | raw | opening 1X2 price, draw | float | row `span.odds > span` [2nd], header 1X2 | 4.75 | before | input | | drop ? (equals #34) |
| 22 | `away_win_initial_odds` | raw | opening 1X2 price, away win | float | row `span.odds > span` [3rd], header 1X2 | 7.00 | before | input | | drop ? (equals #35) |
| 23 | `ou_line` | raw | opening goal line, Asian (3.25 = "3/3.5") | float | row `span.odds > span` [2nd], header OU | 3.25 | before | input | | rename ? → `odds_ou_open_line` |
| 24 | `over_odds` | raw | opening over price, decimal (the page shows Hong Kong odds: 0.98 → 1.98) | float | row `span.odds > span` [1st], header OU | 1.98 | before | input | | rename ? |
| 25 | `under_odds` | raw | opening under price, decimal | float | row `span.odds > span` [3rd], header OU | 1.88 | before | input | | rename ? |
| 26 | `ah_line` | raw | opening Asian handicap line; positive = the home team gives the handicap | float | row `span.odds > span` [2nd], header AH | 1.25 | before | input | | rename ? → `odds_ah_open_line` |
| 27 | `ah_home_odds` | raw | opening AH price, home, decimal | float | row `span.odds > span` [1st], header AH | 1.83 | before | input | | rename ? |
| 28 | `ah_away_odds` | raw | opening AH price, away, decimal | float | row `span.odds > span` [3rd], header AH | 2.03 | before | input | | rename ? |
| 29 | `home_team_position` | raw | home team's rank **after** this round (the table includes this match) | int | `ul#standingList li.standlis span.rank em`, round picked in `#standingBox` | 5 | **after** | check | | replace: the round X−1 table (rule 3, C1) |
| 30 | `away_team_position` | raw | away team's rank **after** this round | int | same | 18 | **after** | check | | replace: the round X−1 table (rule 3, C1) |

Lines 23–28 equal the Bet365 "Initial" row on the detail page for 2789361 (lines and prices), so
the schedule's O/U and AH are **opening** values. Confirm on the page.

### 1c. On the league page, not stored

| C | what the page shows | where | timing | proposal |
|---|---|---|---|---|
| C1 | **the standings per round, with filters** (section 9): a round dropdown (`Total` = now, `Round N` = after round N, listed only once round N is finished), Total / Home / Away, and FT / HT, so 6 tables per finished round. Columns: rank, team, P, W, D, L, GD, PTS. We keep only the FT / Total rank (#29–30) | `#standingBox`, `#standingType`, `#standingHF`, `ul#standingList li.standlis` | Round N: after round N | **add (the user, 2026-10-05): attach the round X−1 tables to every round-X row.** Both teams' lines (rank, P, W, D, L, GD, PTS) for FT and HT × Total / Home / Away; empty in round 1; guard in D11. Reading 6 tables per round adds clicks to the schedule scrape (idea 10 measures the cost) |
| C2 | the row's match state code (`-1` on finished rows) | row attribute `state` | — | skip ? |
| C3 | season tables: team goals, HT/FT results, goal timings, goal differences, correct scores, team stats (shots, possession, corners, fouls, cards) | "Statistics" section | after (season totals as of the scrape) | skip: not usable before kickoff |
| C4 | player stats, odds stats (win %), outright odds | "Tech Stats", "ODDS STATS", "OUTRIGHTS ODDS" | — | skip: not match fields |

The odds header offers AH, 1X2 and OU only. **No HT/FT odds on this page.**

## 2. Detail page — `data/raw/<league>_<season>_detail.csv`

### 2a. Session S3 — odds, strength, crowd vote, next match

| # | field | class | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 31 | `match_id` | raw | join key, same as #6 | text | URL `h2h-<id>` | 2789361 | before | key | | keep |
| 32 | `odds_bookmaker` | raw | bookmaker whose 1X2 row was read: Bet365 if listed, else the first row | text | odds table `table.team-table-other`, Company column | Bet365 | before | check | | keep |
| 33 | `odds1x2_init_home` | raw | Bet365 opening 1X2 price, home ("Initial" row) | float | odds table, Initial row, 1X2 cells | 1.40 | before | input | | rename ? → `odds_1x2_open_home` |
| 34 | `odds1x2_init_draw` | raw | same, draw | float | same | 4.75 | before | input | | rename ? |
| 35 | `odds1x2_init_away` | raw | same, away | float | same | 7.00 | before | input | | rename ? |
| 36 | `odds1x2_live_home` | raw | Bet365 "Live" 1X2 price, home. The page has a separate "In-Play" row (1.01 here), so "Live" is the last price before kickoff | float | odds table, Live row, 1X2 cells | 1.61 | before ? (closing) | input | | rename ? → `odds_1x2_close_home` |
| 37 | `odds1x2_live_draw` | raw | same, draw | float | same | 4.33 | before ? | input | | rename ? |
| 38 | `odds1x2_live_away` | raw | same, away | float | same | 5.00 | before ? | input | | rename ? |
| 39 | `strength_home` | raw | the page's strength rating, home (home + away = 100) | int | "Strength Comparison" block, `[class*='strength']` | 67 | before ? | input | | keep |
| 40 | `strength_away` | raw | same, away | int | same | 33 | before ? | input | | keep |
| 41 | `h2h_compare_home_pct` | raw | "H2H Comparison" bar, home share in % | float | Strength Comparison block | 84 | before ? | input | | keep |
| 42 | `h2h_compare_away_pct` | raw | same, away | float | same | 16 | before ? | input | | keep |
| 43 | `guess_home_pct` | raw | "Who will win?" crowd vote for the home team, %. **Before kickoff the page shows only the vote count** ("See the results after voting"; seen on 2981454) | float | `div.guessingbox` | 83.6 | **after** ? (hidden before kickoff) | input | | drop (rule 3: not shown before kickoff) |
| 44 | `guess_away_pct` | raw | same, away | float | same | 16.4 | **after** ? | input | | drop (rule 3) |
| 45 | `home_next_fixture_days` | raw | days from this match to the home team's next match ("N Days") | int | Fixture table `table.team-table-home`, first Countdown | 3 | before | input | | keep |
| 46 | `away_next_fixture_days` | raw | same, away team | int | Fixture table `table.team-table-guest` | 7 | before | input | | keep |

### 2b. Session S4 — one history row

The detail file stores 18 history rows per match: `{side}_last{n}_<field>`, where `side` is
`home` (the home team's recent matches, `table_v1`), `away` (`table_v2`) or `h2h` (`table_v3`),
and `n` = 1 (most recent) to 6. One row below defines the field for all 18 slots. The row's
home and away are the history match's own teams, not this match's.

Example slot: `home_last1_*` = Chelsea's last match before this one, Napoli 2-3 Chelsea (UEFA
Champions League, 28 Jan 2026), page row `tr#tr1_1`.

| # | field | class | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 47 | `match_id` | raw | the history match's id | int | row attribute `index` | 2861115 | before | key | | keep |
| 48 | `league_id` | raw | its league id (36 = EPL, 103 = UCL) | int | row attribute `name` | 103 | before | key, input |  | keep |
| 49 | `date` | raw | its kickoff. **This one looks like UTC** (20:00 for a UCL match), unlike #7 | text | `span[name='timeData']`, attribute `data-t` | 2026-01-28 20:00:00 | before | key, input |  | keep ? (one timezone for all dates) |
| 50 | `league` | raw | competition name; the page cell shows the short form ("UEFA CL") | text | first cell | UEFA Champions League | before | key |  | keep |
| 51 | `is_home` | scrape-derived | the subject team played at home in that match | bool | the row's team links compared with the subject team | False | before | input | | keep |
| 52 | `opponent` | scrape-derived | the other team's name | text | the team link that is not the subject team | Napoli | before | input | | keep |
| 53 | `result` | scrape-derived | W, D or L for the subject team. The page also shows it in its own cell | text | computed; page cell "W/L" | W | before | input | | keep ? (read the page cell?) |
| 54 | `ht_score` | raw | HT score as text | text | `span[class^='hscore']`, shown "(2-1)" | 2-1 | before | input |  | drop ? (same facts as 56–57) |
| 55 | `ft_score` | raw | FT score as text | text | `span[class^='fscore']` | 2-3 | before | input |  | drop ? (same facts as 58–59) |
| 56 | `ht_home_goals` | raw | home side's goals at HT | int | `span[class^='hscore']` | 2 | before | input, check |  | keep |
| 57 | `ht_away_goals` | raw | away side's goals at HT | int | same | 1 | before | input, check |  | keep |
| 58 | `ft_home_goals` | raw | home side's goals at FT | int | `span[class^='fscore']` | 2 | before | input, check |  | keep |
| 59 | `ft_away_goals` | raw | away side's goals at FT | int | same | 3 | before | input, check |  | keep |
| 60 | `odds_home` | raw | that match's 1X2 price, home. Bookmaker and snapshot come from the table's own selector (Bet365; Initial or Final?) | float | cells 7–9 | 2.50 | before | input, check |  | keep ? (which snapshot?) |
| 61 | `odds_draw` | raw | same, draw | float | same | 3.50 | before | input, check |  | keep ? |
| 62 | `odds_away` | raw | same, away | float | same | 2.63 | before | input, check |  | keep ? |
| 63 | `corners_ft_home` | raw | home side's corners, full match | int | Corner cell "4-1 (3-1)" | 4 | before | input | | keep |
| 64 | `corners_ft_away` | raw | away side's corners, full match | int | same | 1 | before | input | | keep |
| 65 | `corners_ht_home` | raw | home side's corners at HT | int | the part in brackets | 3 | before | input | | keep |
| 66 | `corners_ht_away` | raw | away side's corners at HT | int | same | 1 | before | input | | keep |

### 2c. On the h2h page, not stored

| C | what the page shows | where | timing | proposal |
|---|---|---|---|---|
| C5 | the full odds table: about 17 bookmakers, each with Initial, Live and In-Play rows for AH, 1X2 and O/U. We keep Bet365 1X2 Initial and Live only. Before kickoff a bookmaker has only Initial and Live, and Live keeps moving (2981454 at 5¾ h before kickoff: Bet365 1X2 Initial 1.48 / 4.75 / 6.00, Live 1.36 / 5.25 / 7.50) | "Live Odds Comparison", `table.team-table-other` | Initial and Live before; **In-Play after** | add ? Bet365 AH and O/U Live (closing lines); other bookmakers ? (a market average) |
| C6 | **each team's standings before this match**: FT table (Total / Home / Away / Last 6: played, W, D, L, scored, conceded, points, rank, win %) and an HT table with the same columns. Chelsea shows 23 played before round 24 | `table.team-table-home` / `table.team-table-guest`, headed "[ENG PR-5] Chelsea" | before (verify on more matches) | add ? It could replace the pre-kickoff table we planned to compute. The HT table is first-half form |
| C7 | history-row cells we skip: AH price, line, price; AH result (W/L); O/U result (O/U); the bookmaker and Initial/Final selector; up to 20 rows (we keep 6, while the form averages use 10) | `table_v1` / `table_v2` / `table_v3` | before | add ? AH line and result |
| C8 | **Half Time / Full Time counts per team**, season to date: W/W, W/D, W/L, D/W, D/D, D/L, L/W, L/D, L/L (Chelsea: L/W 0, W/L 2). Filters "H-A" and "Same" | "Half Time / Full Time" | before | add ? comeback-related (L/W = comeback wins, W/L = blown leads) |
| C9 | goals distribution per team, season to date: matches with 0/1/2/3/4+ goals, 1st- and 2nd-half goals, goal timing in 10-minute buckets, first-goal timing | "Goals Distribution" | before | add ? could replace parts of the goal-timing averages that now need the live scrape |
| C10 | full-time / half-time goal difference counts: Win 2+, Win 1, Draw, Lose 1, Lose 2+ | "Full-time/Half-time Goal Difference" | before | ? |
| C11 | odds records over 23 games: AH win/draw/lose %, O/U over/draw/under %; "Historical Matches with Same Odds" | "Odds Statistics" | before | ? |
| C12 | injury and suspension lists: position, shirt number, name | "Injury and Suspension" | ? (the match date or today?) | ? |
| C13 | each team's lineup in its previous match: formation, starting XI, substitutes | "Last Match Lineups" | before ? | ? |
| C14 | the next 3 matches of each team: competition, date, home/away, opponent (we keep only the first countdown) | Fixture tables | before | ? |
| C15 | the crowd vote's counts (46 / 9) and the AH prices shown beside it | "Who will win?" | ? | skip ? |
| C21 | the match header: competition and stage ("UEFA Nations League · League a"), kickoff with weekday, **venue** (Giuseppe Meazza) and **weather** ("Partly sunny, 17℃～18℃") | page header, above the tabs | before | add ? venue and weather |

**No HT/FT odds on this page.**

## 3. Live page — global stores in `data/raw/`

### 3a. Session S5 — goal store, `goals.csv` (one row per goal)

Example: the 5 goals of 2789361. The table shows goal 1 (7', away, 0-1) unless noted.

| # | field | class | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 67 | `match_id` | raw | the match the goal belongs to | int | URL `live-<id>` | 2789361 | — | key | | keep |
| 68 | `league_id` | ? | the match's league id; not on the live page | int | from the work list ? | 36 | — | key | | keep ? |
| 69 | `goal_index` | scrape-derived | order of the goal in the match, from 1 | int | order of the goal rows | 1 | after | key | | keep |
| 70 | `minute` | raw | minute of the goal (45+3 → 45) | int | the event row's minute cell | 7 | after | label, input, check |  | keep |
| 71 | `stoppage` | raw | added minutes (45+3 → 3) | int | same cell | 0 (goal 5: 1) | after | label, input, check |  | keep |
| 72 | `side` | scrape-derived | the team that scored, from the change in the running score (never from the icon) | text | running score | away | after | label, input, check |  | keep |
| 73 | `home_score_after` | raw | home score after the goal | int | running score | 0 | after | label, input, check |  | keep |
| 74 | `away_score_after` | raw | away score after the goal | int | running score | 1 | after | label, input, check |  | keep |
| 75 | `kind` | raw | the event's label from the icon's `alt` text | text | `img[alt]` | Goal | after | label, input, check |  | keep |

### 3b. Session S5 — event store, `events.csv` (one row per card or substitution)

Example: event 1 of 2789361 (26', home substitution) unless noted. The red card is event 15:
90+10', away, Todibo J.

| # | field | class | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 76 | `match_id` | raw | the match the event belongs to | int | URL `live-<id>` | 2789361 | — | key | | keep |
| 77 | `league_id` | ? | the match's league id; not on the live page | int | from the work list ? | 36 | — | key | | keep ? |
| 78 | `event_index` | scrape-derived | order of the event in the match, from 1 | int | order of the event rows | 1 | after | key | | keep |
| 79 | `minute` | raw | minute of the event | int | the event row's minute cell | 26 | after | input, check |  | keep |
| 80 | `stoppage` | raw | added minutes | int | same cell | 0 (red card: 10) | after | input, check |  | keep |
| 81 | `side` | raw | the team of the event: which column the row fills | text | home or away cell of the row | home | after | input, check |  | keep |
| 82 | `kind` | raw | Substitution, Yellow Card or Red Card | text | the row's icon | Substitution | after | input, check |  | keep |
| 83 | `player` | raw | the player; for a substitution, the player who comes on | text | the row's content cell | Neto P. | after | input |  | keep |
| 84 | `player_off` | raw | for a substitution, the player who goes off; empty otherwise | text | the same cell | Bynoe-Gittens J. | after | input |  | keep |

### 3c. Session S5 — attempt logs, `goals_done.csv` and `events_done.csv`

| # | field | class | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|---|
| 85 | `goals_done.match_id` | raw | a match whose live page was read for goals | int | URL | 2789361 | — | key, check |  | keep |
| 86 | `goals_done.scraped_at` | scrape-derived | when it was read, UTC | text | scraper clock | 2026-09-22T10:01:29+00:00 | — | check | | keep |
| 87 | `goals_done.n_goals` | scrape-derived | goals found (0 for a goalless match, which writes no goal row) | int | count | 5 | after | check | | keep |
| 88 | `events_done.match_id` | raw | a match whose live page was read for events | int | URL | 2789361 | — | key, check |  | keep |
| 89 | `events_done.scraped_at` | scrape-derived | when it was read, UTC | text | scraper clock | 2026-09-23T12:30:18+00:00 | — | check | | keep |
| 90 | `events_done.n_events` | scrape-derived | events found | int | count | 15 | after | check | | keep |

### 3d. On the live page, not stored

| C | what the page shows | where | timing | proposal |
|---|---|---|---|---|
| C16 | **match statistics**, about 30 per team, for the full match, the first half and the second half: corners, yellow and red cards, shots, shots on goal, shots off goal, blocked shots, attacks, dangerous attacks, free kicks, possession, passes, pass %, fouls, offsides, aerials, saves, tackles, substitutions, dribbles, throw-ins, hit the post, interceptions, crosses, assists, long passes; also the kick-off team and the first and last card and substitution. Example: shots 14–11, shots on goal 6–6, dangerous attacks 95–33, possession 70%–30% | "Statistics" | after (as history: before) | add ? per-half shots and attacks for history matches. Shots bring back F7 (idea 18) |
| C17 | Bet365 corner over/under odds (Initial 11, Live 11.5) | "Bet365 Corner Odds" | before | skip ? (corners market) |
| C18 | team averages over the last 3 and last 10 matches: goals, conceded, opponent shots, corners, yellow cards, fouls, possession | "Team Statistics" | ? (which date are they counted to?) | ? |
| C19 | rate of goals scored and conceded by 15-minute bucket, last 30 and last 50 matches | "The Rate of Scored / Conceded" | ? | ? |
| C20 | **HT/FT counts over the last 2 seasons, home and away**. Chelsea 61 = 38 (2024-25) + 23 (2025-26 before this match), so league only and before kickoff. HT-L/FT-W = comeback wins (home 1, away 2) | "HT/FT Statistics (Last 2 Seasons)" | before (verify) | add ? comeback-related |
| C22 | **first-half odds**: for Bet365, Sbobet and Crown, the first-half AH, 1X2 and O/U, Initial and Live, beside the full-time row. Example, 2981454 Bet365 first-half 1X2 Initial 1.95 / 2.60 / 5.50, line AH 0.5, O/U 1/1.5. After kickoff the same tables get in-play rows with time and score | "Live Odds Analysis", `table#oddsTable<bookmaker id>`, FT/HT selector | Initial and Live before; in-play rows after | add ? **the market's price for the half-time state**, link 1 of the comeback chain |

**No HT/FT odds on this page.**

## 4. Derived — base (session S6: Claude drafts, the user skims)

| D | field | formula and source | timing | role | proposal |
|---|---|---|---|---|---|
| D1 | `has_odds`, `has_ou_odds`, `has_ah_odds` | all prices of that market present (`domain/match.py`) | before | check | keep |
| D2 | `total_goals`, `goals_1h`, `goals_2h`, `home_2h_goals`, `away_2h_goals` | sums and differences of #16–19 | after | label | keep |
| D3 | `ht_result`, `ft_result` | 1, X or 2 from #16–19 | after | label | keep |
| D4 | `day_of_week`, `is_monday`, `is_midweek` | weekday of #7. **Computed on UTC+8 today**, so a kickoff at or after 16:00 UTC lands on the next day | before | input | fix: compute on UTC once #7 is stored in UTC (survey claim #6 uses `is_monday`) |
| D5 | `position_gap` | \|#29 − #30\|. **After** the round | after | — | rebuild from the round X−1 ranks (D11) |
| D6 | `favorite`, `favorite_odds`, `underdog_odds` | lower and higher opening win price | before | input | keep ? |
| D7 | `implied_prob_home`, `implied_prob_away`, `implied_init_*`, `implied_live_*` | 1 / price; the margin is not removed | before | input | keep ? or replace with D12 |
| D8 | `implied_over`, `implied_ah_home` | two-way price with the margin removed | before | input | keep |
| D9 | `{side}_recent_*` (played, wins, draws, losses, ppg, gf_avg, ga_avg, over25_rate, btts_rate, form, venue_ppg, venue_over25_rate) and `h2h_*` (played, home_team_wins, draws, away_team_wins, over25_rate, btts_rate, avg_total_goals) | `scrapers/detail_parsers.py:aggregate_form`, `aggregate_h2h`, over up to 10 history rows. **Rounded to 3 decimals inside a raw file** | before | input | move to derived; `over25` / `btts` names: keep as inputs ? |
| D10 | `{side}_last{n}_total_goals`, `_ht_result`, `_ft_result`, `_corners_total` | per history row (`_flatten_one`) | before | input | move to derived |
| D11 | pre-kickoff table: rank, P, W, D, L, GD, PTS for each team, FT and HT, Total / Home / Away | **new. Source decided by the user (2026-10-05): the round X−1 table (C1).** Guard: if a match of an earlier round kicked off after this match, this row's table values stay empty, because the round table may already count that later result. Where the detail scrape runs, the h2h page's tables (C6) are a cross-check | before | input | add |
| D12 | margin-free 1X2: `mkt_sup`, `mkt_tot` | `features/engine.py:_vig_free` | before | input | keep |
| D13 | rest days since each team's previous match | **new**: from #7 and #49, both in UTC once #7 is fixed | before | input | add ? |

## 5. Derived — comebacks (session S7: Claude drafts, the user skims)

| K | field | formula and source | timing | role | proposal |
|---|---|---|---|---|---|
| K1 | `is_comeback`, `is_comeback_home`, `is_comeback_away` | the team behind at HT wins at FT (`domain/stats.py`) | after | label | keep |
| K2 | `ht_decisive` | **new**: HT not level (link 1 of the chain, `notes/MARKET_COMEBACKS.md`) | after | label | add |
| K3 | `{side}_last{n}_is_comeback` | the history match was a comeback | before | input | keep |
| K4 | goal-timing averages, `{side}_` + goal_minute_avg, conceded_minute_avg, late_goal_rate, late_conceded_rate, conceded_pre_ht_rate, goals_seen; goals for by bucket gf_00_15, gf_16_30, gf_31_45, gf_46_60, gf_61_75, gf_76_90; goals against ga_00_15, ga_16_30, ga_31_45, ga_46_60, ga_61_75, ga_76_90; and `{side}_last{n}_goal_timeline` | `features/goals.py`, from the goal store | before | input | keep ? |
| K5 | card and substitution averages, `{side}_` + yellows_for_avg, yellows_against_avg, yellows_while_leading_avg, reds_for_rate, reds_against_rate, subs_for_avg, first_sub_minute_avg, late_sub_rate, events_seen; and `{side}_last{n}_yellow_timeline`, `{side}_last{n}_red_timeline`, `{side}_last{n}_sub_timeline` | `features/events.py`, from the event store | before | input | keep ? |
| K6 | `out_of_round`, `round_state`, `prev_match_comeback` | **new**: the survey's planned flags (claims #5, #3, #4) | before | input | add ? |

Labels of other markets wait for their market: `btts`, `over_25`, `is_seven_or_more_goals`,
`ht_ft_combo`, `{side}_last{n}_over_25`, `{side}_last{n}_btts`.

## 6. Engine model features (session S8: Claude drafts, the user skims)

`features/engine.py`, 46 names. Status from `notes/STATE.md`.

| family | features | ledger status |
|---|---|---|
| A_ht_state | home_ht_trail_rate, away_ht_trail_rate, home_h1_gd_avg, away_h1_gd_avg | dead (RESULTS §1) |
| B_2h_supremacy | home_h2_gd_avg, away_h2_gd_avg, home_blown_lead_rate, away_blown_lead_rate | dead |
| C_pressure | home_corner_goal_share_gap, away_corner_goal_share_gap | dead |
| D_non_market | strength_gap, guess_minus_market | dead |
| E_congestion | home_matches_14d, away_matches_14d, home_days_since_last, away_days_since_last | dead |
| F_venue_h2h | venue_ppg_gap, h2h_ht_nondraw_rate | dead |
| G1_recent_goals | home/away × h1_gf_avg, h1_ga_avg, h2_gf_avg, h2_ga_avg, recent_gf_avg, recent_ga_avg, recent_over25_rate | dead (FILTER_RESULTS) |
| G2_h2h_goals | h2h_avg_total_goals, h2h_over25_rate, h2h_ht_goals_avg, h2h_ht_nondraw_rate | dead |
| G3_odds | mkt_sup, mkt_tot, mkt_p_draw, odds_drift_home, odds_drift_away | dead |
| market line | ou_line, implied_over, ah_line, abs_ah_line, implied_ah_home | live-exploratory (MARKET_LINE) |
| controls | mkt_sup, mkt_tot, combined_recent_gf, h2h_avg_total_goals | used in every model |

## 7. Known issues found while drafting

1. **Two timezones.** The league page's `date` (#7) is UTC+8, while the h2h page's history dates
   (#49) are UTC (confirmed in section 8). The weekday flags (D4) are computed on UTC+8.
   **Decided 2026-10-05: store every date in UTC.**
2. **Standings positions (#29–30) are after the round.** The h2h page shows each team's table
   before the match (C6).
3. **Duplicates:** score strings (#14–15, #54–55) repeat the goal columns, and the schedule's
   opening 1X2 (#20–22) equals the detail page's Bet365 Initial (#33–35) in 99.7% of 379 EPL rows.
4. **Odds snapshots:** the schedule's O/U and AH (#23–28) equal Bet365 Initial on 2789361. The
   detail page's "Live" row (#36–38) is separate from "In-Play", so it looks like the closing
   price. The history rows' snapshot (#60–62) is unknown.
5. **Rounding:** the form averages (D9) are rounded to 3 decimals inside a raw file. They count
   up to 10 history rows, while the file keeps 6.
6. **The comeback's own price (HT/FT odds) is on none of the 3 pages.** Another page type would
   need the user's go and a robots.txt check.

## 8. Before-kickoff check — match 2981454

Italy v Turkey, UEFA Nations League (League A), kickoff 2026-10-05 18:45 UTC. The match was
chosen by the user. The h2h and live pages were read at 13:04 UTC, 5 h 40 min before kickoff,
and parsed with the scraper's own code (the `scrape_match_detail` sequence, `parse_goal_events`,
`parse_match_events`). A national-team match has no league page in our config, so #1–30 are not
covered here.

| fields | readable 5 h 40 min before kickoff? | value then |
|---|---|---|
| #32–35 bookmaker and 1X2 Initial | yes | Bet365, 1.48 / 4.75 / 6.00 |
| #36–38 1X2 Live | yes, and it keeps moving | 1.36 / 5.25 / 7.50 |
| #39–42 strength, H2H comparison | yes | 67 / 33, 97 / 3 |
| #43–44 crowd vote % | **no**: hidden, the page shows only "Votes: 6" | None |
| #45–46 days to the next match | yes | 38 / 38 |
| #47–66 history rows | yes: 20 home rows, 20 away, 5 H2H, every slot field filled | `home_last1`: France v Italy, 2026-10-02 18:45 |
| #67–90 goal and event stores | **no**: 0 goal rows, 0 event rows | — |
| C5 odds table | Initial and Live rows only (15 each); **no In-Play row** | — |
| C6 standings | yes, as the group table ("Cup Standings") | Italy 3rd, 4 pts from 3 matches |
| C8 HT/FT counts, C9 goals distribution, C11 odds records | yes | — |
| C10 goal-difference counts | not on this match's page | — |
| C12 injuries, C13 last-match lineups, C14 next matches, C21 venue and weather | yes | Giuseppe Meazza, partly sunny, 17–18 ℃ |
| C16 match statistics | **no**: 0 rows | — |
| C17 corner odds, C18 team averages, C19 scoring by time, C20 HT/FT over 2 seasons | yes | corner line 9.5 |
| C22 first-half odds | yes | Bet365 first-half 1X2 Initial 1.95 / 2.60 / 5.50, Live 1.80 / 2.63 / 7.00 |
| this match's own lineups | not yet posted | — |

The history date `2026-10-02 18:45:00` belongs to a 20:45 CEST kickoff, which confirms that the
h2h page's dates (#49) are UTC.

## 9. Upcoming-match check — EPL 2026-27 league page

Read on 2026-10-05 from the config URL <https://football.nowgoal26.com/league/2026-2027/36>, which the
user sent. That took 2 page loads; everything else was clicks on the page's own controls. Rounds 1–5
were played. Round 6, the round the bar marks `current`, starts on 2026-10-10, 5 days later.

| what | upcoming row (round 6) | played row |
|---|---|---|
| match id, teams, team ids, round, kickoff (`data-t`, UTC+8) | yes | yes |
| odds: 1X2, AH, O/U | yes. Arsenal v Leeds: 1X2 1.25 / 5.50 / 12.00, AH line 1.5/2, O/U line 2.5/3 | yes |
| FT score, HT score | no: `-` and empty | yes |
| row attribute `state` | 0 | -1 |

This matches the user's quick look: before kickoff only the score is missing.

**The standings section:**
- **Round dropdown:** `Total`, plus one entry per finished round (here Round 1–5; Round 6 has no
  entry yet). `Round N` is the table after round N, which the user read the same way and #29–30
  showed. `Total` is the table now. Today it equals Round 5, because no round-6 match has been
  played.
- **Filters:** Total / Home / Away, and FT / HT. They combine with any finished round, so each round
  has 6 tables. Examples:
  - `Round 1 | Total | HT`: Arsenal's goal difference is 2 (FT: 3).
  - `Round 5 | Away | HT`: Bournemouth is first, with 2 away matches and 6 HT points.
- **Columns:** rank, team (id in `toTeam(<id>)`), P, W, D, L, GD, PTS. There are no separate goals
  for and against; GD only.

**Open (the user: "we need to think about this more"):**
1. What does `Total` show while a round is still being played?
2. When a round-N match is postponed and played later, does `Round N` count it, and since when?
   If `Round N` is rebuilt to include it, a table read later can hold results from after a
   round-N+1 kickoff.
3. ~~Which source gives the pre-kickoff table (D11)?~~ **Decided by the user (2026-10-05): the
   round X−1 table**, with the guard in D11. Question 2 now decides only how many rows the guard
   empties, not whether a row can leak.
