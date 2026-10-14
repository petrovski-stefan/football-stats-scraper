# Live page — stage 1, raw (unchanged for now)

**Group: FIELDS.** One row per field. Never change a field code. The stage-1 docs are frozen after plan step P7.

**Answers: where is each value on the page?** The goal and event stores, read from the match's
live page. **Unchanged for now (plan Q4):** they already fit stage 1, apart from the exceptions
marked below. Their redesign comes after schedule and detail.

- Page: <https://live11.nowgoal26.com/match/live-2789361> for the reference match.
- Files: today `data/archived/raw/goals.csv`, `events.csv`, `goals_done.csv`, `events_done.csv`. They are
  global stores keyed by match id, because history matches come from many competitions.
- **Names stay as they are** until the redesign: rule 6's codes are not applied here yet.
- **Exception** = a field computed from other rows or another file; kept here for now, as plan Q4
  decided.

## A. Goal store — `goals.csv`, one row per goal

Example: the 5 goals of 2789361. The table shows goal 1 (7', away, 0-1) unless noted.

| # | field | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| L1.01 | `match_id` | the match the goal belongs to | int | URL `live-<id>` | 2789361 | — | key |  | keep |
| L1.02 | `league_id` | the match's league id; **not on the live page**, copied from the schedule or history file | int | from the work list | 36 | — | key |  | exception |
| L1.03 | `goal_index` | order of the goal in the match, from 1 | int | order of the goal rows | 1 | after | key |  | exception (row order) |
| L1.04 | `minute` | minute of the goal (45+3 → 45) | int | the event row's minute cell | 7 | after | label, input, check |  | keep |
| L1.05 | `stoppage` | added minutes (45+3 → 3) | int | same cell | 0 (goal 5: 1) | after | label, input, check |  | keep |
| L1.06 | `side` | the team that scored, from the change in the running score since the previous goal (never from the icon) | text | running score | away | after | label, input, check |  | exception (previous row) |
| L1.07 | `home_score_after` | home score after the goal | int | running score | 0 | after | label, input, check |  | keep |
| L1.08 | `away_score_after` | away score after the goal | int | running score | 1 | after | label, input, check |  | keep |
| L1.09 | `kind` | the event's label from the icon's `alt` text | text | `img[alt]` | Goal | after | label, input, check |  | keep |

## B. Event store — `events.csv`, one row per card or substitution

Example: event 1 of 2789361 (26', home substitution) unless noted. The red card is event 15:
90+10', away, Todibo J.

| # | field | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| L1.10 | `match_id` | the match the event belongs to | int | URL `live-<id>` | 2789361 | — | key |  | keep |
| L1.11 | `league_id` | as L1.02 | int | from the work list | 36 | — | key |  | exception |
| L1.12 | `event_index` | order of the event in the match, from 1 | int | order of the event rows | 1 | after | key |  | exception (row order) |
| L1.13 | `minute` | minute of the event | int | the event row's minute cell | 26 | after | input, check |  | keep |
| L1.14 | `stoppage` | added minutes | int | same cell | 0 (red card: 10) | after | input, check |  | keep |
| L1.15 | `side` | the team of the event: which half of the row is filled | text | home or away cell of the row | home | after | input, check |  | keep |
| L1.16 | `kind` | Substitution, Yellow Card or Red Card | text | the icon beside the minute | Substitution | after | input, check |  | keep |
| L1.17 | `player` | the player; for a substitution, the player who comes on | text | the row's content cell | Neto P. | after | input |  | keep |
| L1.18 | `player_off` | for a substitution, the player who goes off; empty otherwise | text | the same cell | Bynoe-Gittens J. | after | input |  | keep |

## C. Attempt logs — `goals_done.csv`, `events_done.csv`

A goalless match writes no goal row, so the logs record what was read.

| # | field | meaning | type | place on the page | example | timing | role | ✓ | status |
|---|---|---|---|---|---|---|---|---|---|
| L1.19 | `goals_done.match_id` | a match whose live page was read for goals | int | URL | 2789361 | — | key, check |  | keep |
| L1.20 | `goals_done.scraped_at` | when it was read, UTC | text | scraper clock, not the page | 2026-09-22T10:01:29+00:00 | — | check |  | keep (bookkeeping) |
| L1.21 | `goals_done.n_goals` | goals found (0 for a goalless match) | int | count of the goal rows | 5 | after | check |  | exception (count) |
| L1.22 | `events_done.match_id` | a match whose live page was read for events | int | URL | 2789361 | — | key, check |  | keep |
| L1.23 | `events_done.scraped_at` | when it was read, UTC | text | scraper clock | 2026-09-23T12:30:18+00:00 | — | check |  | keep (bookkeeping) |
| L1.24 | `events_done.n_events` | events found | int | count of the event rows | 15 | after | check |  | exception (count) |

**Timing:** a goal or event is `after` for its own match. It is never an input for its own match;
it is an input only for later matches, through their history (`LIVE_3_MULTI.md`).

## D. On the page, not stored — candidates, decided in P2

| C | what the page shows | where | timing | proposal |
|---|---|---|---|---|
| C16 | **match statistics**, about 30 per team, for the full match and each half: corners, cards, shots, shots on goal, attacks, dangerous attacks, possession, passes, fouls, offsides, saves and more. Example: shots 14–11, shots on goal 6–6, possession 70%–30% | "Statistics" | after (as history: before) | add ? per-half shots and attacks for history matches |
| C17 | Bet365 corner over/under odds (Initial 11, Live 11.5) | "Bet365 Corner Odds" | before | skip ? (corners market) |
| C18 | team averages over the last 3 and last 10 matches: goals, conceded, opponent shots, corners, yellow cards, fouls, possession | "Team Statistics" | ? (which date are they counted to?) | ? |
| C19 | rate of goals scored and conceded by 15-minute bucket, last 30 and last 50 matches | "The Rate of Scored / Conceded" | ? | ? |
| C20 | **HT/FT counts over the last 2 seasons, home and away**. Chelsea 61 = 38 (2024-25) + 23 (2025-26 before this match), so league only and before kickoff. HT-L/FT-W = comeback wins (home 1, away 2) | "HT/FT Statistics (Last 2 Seasons)" | before (verify) | ? This season's version is S3.08, rebuilt from our results; the 2-season window would need the previous season's file |
| C22 | **first-half odds**: for Bet365, Sbobet and Crown, the first-half AH, 1X2 and O/U, Initial and Live. Example, 2981454 Bet365 first-half 1X2 Initial 1.95 / 2.60 / 5.50 | "Live Odds Analysis", `table#oddsTable<bookmaker id>`, FT/HT selector | Initial and Live before; in-play rows after | add ? **the market's price for the half-time state**, link 1 of the comeback chain |

**No HT/FT odds on this page.**

**Evidence (2981454, 5 h 40 min before kickoff):** 0 goal rows, 0 event rows and 0 statistics rows,
as expected. C17–C20 and C22 were readable.
