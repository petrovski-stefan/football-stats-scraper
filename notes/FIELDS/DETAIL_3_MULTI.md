# Detail — stage 3, needs other rows

**Group: FIELDS.** One row per field. Never change a field code. The stage-1 docs are frozen after plan step P7.

**Answers: which other rows does it read, and are they all before kickoff?** Every field here
needs more than its own row. Every field states its **row window**. Claude writes them; the
stats-reviewer agent checks them.

- Reads: the detail files of stage 2, plus this match's `date`, `home_team_id` and `away_team_id`
  from the schedule (S1.07–09).
- Files: `data/finished/3_multi/<country>_<league>_<season>_history.csv` (§A; a helper, still one row per
  history row) and `data/finished/3_multi/<country>_<league>_<season>_detail.csv` (§B–E; one row per
  match). The detail file is the analysis input, joined to the schedule's stage 3 by
  `match_id`.
- No rounding: values are stored at full precision (today's averages are rounded to 3 decimals
  inside a raw file).

## The windows — locked by the user, 2026-10-05

- **Team tables** (`home`, `away`): the 6 most recent rows (`n` = 1–6).
- **Head to head:** at most 4 rows, the most recent, each played on or after this kickoff date
  minus 2 calendar years (2026-01-31 → 2024-01-31). Fewer qualifying rows → fewer rows; none →
  the h2h fields are empty, not zero.
- All competitions, as the page lists them.
- **Every row read must be dated before this match's kickoff.** A row dated at or after it is a
  scrape error, reported by QA, never used.

Today's stored averages use up to 10 rows, so their values change.

## A. Per history row, once this match's teams are known

The subject team is this match's home team for the `home` and `h2h` sections, and its away team
for `away`. Today the scraper guesses it by majority vote over the table
(`scrapers/detail_parsers.py:subject_team_id`); the join replaces the guess.

| # | field | formula | row window | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|---|
| D3.01 | `d3_is_home` | the subject team was the history match's home team (D1.24 = subject) | one history row + this match's S1.08–09 | bool | False | before | input | keep |
| D3.02 | `d3_opponent` | the other team's name (D1.26 or D1.27) | the same | text | Napoli | before | input | keep |
| D3.03 | `d3_result` | W, D or L for the subject team, from D1.30–31 | the same | text | W | before | input | keep |

## B. Form averages per side — side = `home`, `away`

Over the team window (6 rows). Examples are `?`: they are computed in P4, and today's stored values
used 10 rows.

| # | field | formula | type | timing | role | status |
|---|---|---|---|---|---|---|
| D3.04 | `d3_{side}_recent_played` | rows used (0–6) | int | before | input, check | keep |
| D3.05 | `d3_{side}_recent_wins` | rows with D3.03 = W | int | before | input | keep |
| D3.06 | `d3_{side}_recent_draws` | rows with D | int | before | input | keep |
| D3.07 | `d3_{side}_recent_losses` | rows with L | int | before | input | keep |
| D3.08 | `d3_{side}_recent_ppg` | points (3 / 1 / 0) ÷ D3.04 | float | before | input | keep |
| D3.09 | `d3_{side}_recent_gf_avg` | the subject's FT goals ÷ D3.04 | float | before | input | keep |
| D3.10 | `d3_{side}_recent_ga_avg` | goals against ÷ D3.04 | float | before | input | keep |
| D3.11 | `d3_{side}_recent_form` | D3.03 of the rows, most recent first, e.g. `WLDWWL` | text | before | input | keep |
| D3.12 | `d3_{side}_recent_venue_ppg` | D3.08 over the rows at the same venue as this match (home rows for `home`, away rows for `away`) | float | before | input | keep. Claude's default: the venue rows **inside** the 6 (today: the 10 most recent venue rows of all 20) |
| D3.13 | `d3_{side}_recent_over25_rate` | rows with more than 2.5 goals ÷ D3.04 | float | before | input | ? named after another market: keep as an input or drop (P2) |
| D3.14 | `d3_{side}_recent_btts_rate` | rows where both sides scored ÷ D3.04 | float | before | input | ? the same |
| D3.15 | `d3_{side}_recent_venue_over25_rate` | D3.13 over the venue rows of D3.12 | float | before | input | ? the same |

## C. Head to head

Over the h2h window (at most 4 rows, none older than 2 years). Oriented to this match's home team.

| # | field | formula | type | timing | role | status |
|---|---|---|---|---|---|---|
| D3.16 | `d3_h2h_played` | rows used (0–4) | int | before | input, check | keep |
| D3.17 | `d3_h2h_home_team_wins` | rows this match's home team won | int | before | input | keep |
| D3.18 | `d3_h2h_draws` | drawn rows | int | before | input | keep |
| D3.19 | `d3_h2h_away_team_wins` | rows this match's away team won | int | before | input | keep |
| D3.20 | `d3_h2h_avg_total_goals` | the sum of D2.05 ÷ D3.16 | float | before | input | keep |
| D3.21 | `d3_h2h_over25_rate` | rows with more than 2.5 goals ÷ D3.16 | float | before | input | ? named after another market (P2) |
| D3.22 | `d3_h2h_btts_rate` | rows where both sides scored ÷ D3.16 | float | before | input | ? the same |

## D. History slots back to one row per match

| # | field | formula | type | timing | role | status |
|---|---|---|---|---|---|---|
| D3.23 | `d3_{section}_last{n}_<field>` | one history row's fields, pivoted wide: section `home` / `away` / `h2h`, n inside the window. Example: `d3_home_last1_is_comeback` = True | as the field | before | input | which sections, slots and fields: set in P4 by what `features/` and `modelling/` read. Only those are written |

## E. New, from the old `notes/FIELDS.md`

| # | field | formula | row window | type | timing | role | status |
|---|---|---|---|---|---|---|---|
| D3.24 | `d3_{side}_days_since_last` | days from the side's most recent history row to this kickoff, from the two timestamps with their offsets (rest days). Today `features/engine.py` mixes UTC+8 (this match) with UTC (history), so its value can be a day off | row `n` = 1 of the side's section | int | before | input | add ? (`features/engine.py` builds the same from today's slots) |
