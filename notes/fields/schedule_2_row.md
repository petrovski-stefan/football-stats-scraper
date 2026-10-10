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
| S2.08 | `s2_day_of_week` | ISO weekday of S1.07 in Berlin time (Monday = 1) | int | 6 (Saturday). **Today's file says 7**: it is computed on UTC+8. Wrong in 41% of EPL 2025-26 rows and 60–63% of the rows of a league removed on 2026-10-10 | before | input | fix: compute on Berlin time |
| S2.09 | `s2_is_monday` | S2.08 = 1 | bool | False | before | input | keep (survey claim #6) |
| S2.10 | `s2_is_midweek` | S2.08 in Tuesday–Thursday | bool | False | before | input | keep |
| S2.11 | `s2_has_odds` | S1.16–18 all present | bool | True | before | check | keep |
| S2.12 | `s2_has_ou_odds` | S1.19–21 all present | bool | True | before | check | keep |
| S2.13 | `s2_has_ah_odds` | S1.22–24 all present | bool | True | before | check | keep |
| S2.14 | `s2_implied_prob_home` | 1 / S1.16; the margin is not removed | float | 0.714 | before | input | **dropped** (Claude, 2026-10-06: no code read it; S2.17–19 replace it) |
| S2.15 | `s2_implied_prob_away` | 1 / S1.18 | float | 0.143 | before | input | **dropped** (Claude, 2026-10-06: no code read it) |
| S2.16 | `s2_favorite` | the name of the team with the lower win price; empty when level | text | Chelsea | before | input | **dropped** (Claude, 2026-10-06: no code read it; S2.20 carries it) |
| S2.17 | `s2_mkt_p_home` | (1 / S1.16) ÷ (1 / S1.16 + 1 / S1.17 + 1 / S1.18): margin removed, proportionally | float | 0.669 | before | input | built here since P3 (was `features/engine.py:_vig_free`) |
| S2.18 | `s2_mkt_p_draw` | the same for the draw | float | 0.197 | before | input | built here since P3 |
| S2.19 | `s2_mkt_p_away` | the same for the away win | float | 0.134 | before | input | built here since P3 |
| S2.20 | `s2_mkt_sup` | ln(S2.17 ÷ S2.19): the market's supremacy, positive = home favoured | float | 1.609 | before | input | built here since P3 |
| S2.21 | `s2_mkt_tot` | −ln(S2.18): a goal-total proxy from the draw price | float | 1.624 | before | input | built here since P3 |
| S2.22 | `s2_favorite_odds` | the lower of S1.16 and S1.18 | float | 1.40 | before | input | **dropped** (Claude, 2026-10-06: no code read it) |
| S2.23 | `s2_underdog_odds` | the higher of S1.16 and S1.18 | float | 7.00 | before | input | **dropped** (Claude, 2026-10-06: no code read it) |
| S2.24 | `s2_implied_over` | (1 / S1.20) ÷ (1 / S1.20 + 1 / S1.21): two-way, margin removed. Near 0.5 by design; the line S1.19 carries the forecast | float | 0.487 | before | input | keep |
| S2.25 | `s2_implied_ah_home` | (1 / S1.23) ÷ (1 / S1.23 + 1 / S1.24) | float | 0.526 | before | input | keep |
| S2.30 | `s2_is_abandoned` | `match_id` is on the hand-kept list `domain/scope.py:ABANDONED_MATCHES`: stopped before full time, so S1.12–15 are the score when play stopped, not a result. The page shows no sign of it | bool | False (no match is listed now: both listed so far left the project with their leagues on 2026-10-08) | after | indicator | **dropped** (the user, 2026-10-10; added 2026-10-07): telling an abandoned match apart is a detail-page question |
| S2.31 | `s2_is_forfeit` | `match_id` is on the hand-kept list `domain/scope.py:FORFEITED_MATCHES`: never played (a team did not turn up, or it was called off and awarded), so S1.12–15 are the awarded score, usually 3–0 with 0–0 at half-time. The page shows no sign of it, and a real 3–0 looks the same, so each entry is confirmed by hand | bool | False (True for 1 match: CYP D1 2609242) | after | indicator | **dropped** (the user, 2026-10-10; added 2026-10-08): a detail-page question, where an awarded match shows no In-Play odds (`detail_1_raw.md` §E) |

**S2.11, S2.14–23 read S1.16–18.** If the user's later duplicate review drops S1.16–18, these
fields are computed from the detail page's opening prices (D1.03–05) instead and move to
`detail_2_row.md`.

## B. Comebacks

| # | field | formula | type | example | timing | role | status |
|---|---|---|---|---|---|---|---|
| S2.26 | `s2_is_comeback` | the team behind at HT wins at FT (`domain/stats.py`) | bool | True | after | label | keep |
| S2.27 | `s2_is_comeback_home` | the home team is behind at HT and wins | bool | True | after | label | keep |
| S2.28 | `s2_is_comeback_away` | the away team is behind at HT and wins | bool | False | after | label | keep |
| S2.29 | `s2_ht_decisive` | S1.12 ≠ S1.13: someone leads at HT (link 1 of the comeback chain, `notes/MARKET_COMEBACKS.md`) | bool | True | after | label | add |

## C. Not in stage 2

- `position_gap` — it was built from the post-round positions, so it was `after`. Dropped. The
  pre-kickoff gap is S3.04.
- Labels of other markets wait for their market: `btts`, `over_25`, `is_seven_or_more_goals`,
  `ht_ft_combo`.
