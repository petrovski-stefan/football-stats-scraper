# Detail — stage 2, derived inside one row

**Group: FIELDS.** One row per field. Never change a field code. The stage-1 docs are frozen after plan step P7.

**Answers: what formula on this row?** Every field here is computed from stage-1 fields of the
same row, and nothing else. Claude writes the formulas; the user skims.

- Reads: the two detail files of stage 1 (`DETAIL_1_RAW.md` §A and §B), one row at a time.
- Files: `data/finished/2_row/<country>_<league>_<season>_detail.csv` and `..._history.csv` = the stage-1
  files plus these columns.
- **Timing rule:** a field's timing is the latest timing of its inputs. Every history row is a
  match played before this one, so every history field is `before`.

## A. Match file

Example: 2789361, Bet365 1X2 Initial 1.40 / 4.75 / 7.00, Live 1.61 / 4.33 / 5.00.

| # | field | formula | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|
| D2.01 | `d2_implied_1x2_open_home` | 1 / D1.03; the margin is not removed | float | 0.714 | before | input | keep ? (today `implied_init_home`; read by `features/engine.py` for `odds_drift_*`) |
| D2.02 | `d2_implied_1x2_open_away` | 1 / D1.05 | float | 0.143 | before | input | keep ? (today `implied_init_away`) |
| D2.03 | `d2_implied_1x2_close_home` | 1 / D1.06 | float | 0.621 | before ? (closing) | input | keep ? (today `implied_live_home`) |
| D2.04 | `d2_implied_1x2_close_away` | 1 / D1.08 | float | 0.200 | before ? | input | keep ? (today `implied_live_away`) |

If the user's later duplicate review drops the schedule's opening prices (S1.16–18), the
margin-free fields S2.11, S2.17–21 are computed here from D1.03–05 instead.

## B. History file — per history row

Example: Napoli 2-3 Chelsea, HT 2-1, corners 4-1.

| # | field | formula | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|
| D2.05 | `d2_total_goals` | D1.30 + D1.31 | int | 5 | before | input | keep |
| D2.06 | `d2_ht_result` | `1` / `X` / `2` from D1.28–29 | text | 1 | before | input | keep |
| D2.07 | `d2_ft_result` | `1` / `X` / `2` from D1.30–31 | text | 2 | before | input | keep |
| D2.08 | `d2_corners_total` | D1.35 + D1.36 | int | 5 | before | input | keep |
| D2.09 | `d2_is_comeback` | the team behind at HT wins at FT (`domain/stats.py`). Comebacks | bool | True | before | input | keep |

## C. Not in stage 2

- `is_home`, `opponent`, `result` need this match's teams, which are in the schedule file:
  `DETAIL_3_MULTI.md` §A.
- `over_25` and `btts` per history row are labels of other markets and wait for them. The
  averages named after them (`*_over25_rate`, `*_btts_rate`) are an open point in
  `DETAIL_3_MULTI.md`.
