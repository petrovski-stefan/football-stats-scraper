# Schedule — stage 2, derived inside one row

**Answers: what formula on this row?** Every field here is computed from stage-1 fields of the
same row, and nothing else. Claude writes the formulas; the user skims.

- Reads: the schedule match file of stage 1 (`schedule_1_raw.md` §A), one row at a time.
- File: `data/finished/2_row/<country>_<league>_<season>_schedule.csv` = the stage-1 file plus these columns.
- **Timing rule:** a field's timing is the latest timing of its inputs.
- Examples are worked on 2789361: HT 0-2, FT 3-2; odds 1.40 / 4.75 / 7.00, O/U 3.25 at 1.98 /
  1.88, AH 1.25 at 1.83 / 2.03.

## A. Base — every market needs these

| # | field | formula | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|
| S2.01 | `s2_total_goals` | S1.14 + S1.15 | int | 5 | after | label | keep |
| S2.02 | `s2_goals_1h` | S1.12 + S1.13 | int | 2 | after | label | keep |
| S2.03 | `s2_goals_2h` | S2.01 − S2.02 | int | 3 | after | label | keep |
| S2.04 | `s2_home_2h_goals` | S1.14 − S1.12 | int | 3 | after | label | keep |
| S2.05 | `s2_away_2h_goals` | S1.15 − S1.13 | int | 0 | after | label | keep |
| S2.06 | `s2_ht_result` | `1` home ahead, `X` level, `2` away ahead, from S1.12–13 | text | 2 | after | label | keep |
| S2.07 | `s2_ft_result` | the same from S1.14–15 | text | 1 | after | label | keep |
| S2.11 | `s2_has_odds` | S1.16–18 all present | bool | True | before | check | keep |
| S2.12 | `s2_has_ou_odds` | S1.19–21 all present | bool | True | before | check | keep |
| S2.13 | `s2_has_ah_odds` | S1.22–24 all present | bool | True | before | check | keep |
| S2.17 | `s2_mkt_p_home` | (1 / S1.16) ÷ (1 / S1.16 + 1 / S1.17 + 1 / S1.18): margin removed, proportionally | float | 0.669 | before | input | built here since P3 (was `features/engine.py:_vig_free`) |
| S2.18 | `s2_mkt_p_draw` | the same for the draw | float | 0.197 | before | input | built here since P3 |
| S2.19 | `s2_mkt_p_away` | the same for the away win | float | 0.134 | before | input | built here since P3 |
| S2.20 | `s2_mkt_sup` | ln(S2.17 ÷ S2.19): the market's supremacy, positive = home favoured | float | 1.609 | before | input | built here since P3 |
| S2.21 | `s2_mkt_tot` | −ln(S2.18): a goal-total proxy from the draw price | float | 1.624 | before | input | built here since P3 |
| S2.24 | `s2_implied_over` | (1 / S1.20) ÷ (1 / S1.20 + 1 / S1.21): two-way, margin removed. Near 0.5 by design; the line S1.19 carries the forecast | float | 0.487 | before | input | keep |
| S2.25 | `s2_implied_ah_home` | (1 / S1.23) ÷ (1 / S1.23 + 1 / S1.24) | float | 0.526 | before | input | keep |

**S2.11, S2.17–21 read S1.16–18.** If the user's later duplicate review drops S1.16–18, these
fields are computed from the detail page's opening prices (D1.03–05) instead and move to
`detail_2_row.md`.

## B. Comebacks

| # | field | formula | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|
| S2.26 | `s2_is_comeback` | the team behind at HT wins at FT (`domain/stats.py`) | bool | True | after | label | keep |
| S2.27 | `s2_is_comeback_home` | the home team is behind at HT and wins | bool | True | after | label | keep |
| S2.28 | `s2_is_comeback_away` | the away team is behind at HT and wins | bool | False | after | label | keep |
| S2.29 | `s2_ht_decisive` | S1.12 ≠ S1.13: someone leads at HT (link 1 of the comeback chain, `notes/MARKET_COMEBACKS.md`) | bool | True | after | label | add |
