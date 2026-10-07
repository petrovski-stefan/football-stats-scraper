# Live page — stage 3, needs other rows (as today)

**Answers: which other rows does it read, and are they all before kickoff?** The goal-timing and
card aggregates. Each one combines the live stores (`live_1_raw.md`) with this match's history
rows, so it needs other rows and other files. **As today, not redesigned yet (plan Q4).**

- Built by `features/goals.py` and `features/events.py`; written today into
  `data/processed/<league>_<season>_enriched.csv` by `features/enrich.py`.
- **Row window today:** the history matches in this match's slots, depth 6, sections `home`,
  `away` and `h2h`. Under the locked windows the `h2h` section becomes at most 4 rows, none older
  than 2 years (`detail_3_multi.md`). A history match is always played before this one; its
  goals and events are `after` for itself and `before` here.
- A history match with no live-page read is skipped as missing, not counted as zero.
  `goals_seen` and `events_seen` count the goals and events the aggregates saw.

| # | fields | source | timing | role | status |
|---|---|---|---|---|---|
| L3.01 | goal timing per section (`home`, `away`, `h2h`), `l3_{section}_` + `goal_minute_avg`, `conceded_minute_avg`, `late_goal_rate`, `late_conceded_rate`, `conceded_pre_ht_rate`, `goals_seen` | `features/goals.py` | before | input | keep ? (survey claims #11, #12 use `conceded_pre_ht_rate` and `late_goal_rate`) |
| L3.02 | goals per 15-minute bucket per section, `l3_{section}_` + `gf_00_15` … `gf_76_90` and `ga_00_15` … `ga_76_90` | `features/goals.py` | before | input | keep ? |
| L3.03 | `l3_{section}_last{n}_goal_timeline` — one history match's goals as text, from the subject's side: `15GA;18GF;23GF;85GA`. The lossless record; every window is re-derivable from it | `features/goals.py` | before | input | keep ? |
| L3.04 | cards and substitutions per section, `l3_{section}_` + `yellows_for_avg`, `yellows_against_avg`, `yellows_while_leading_avg`, `reds_for_rate`, `reds_against_rate`, `subs_for_avg`, `first_sub_minute_avg`, `late_sub_rate`, `events_seen` | `features/events.py` (state-conditioned against the goal store) | before | input | keep ? (survey claim #15 uses `yellows_while_leading_avg`) |
| L3.05 | `l3_{section}_last{n}_yellow_timeline`, `_red_timeline`, `_sub_timeline` | `features/events.py` | before | input | keep ? |

The three-stage redesign of these (one doc per stage, one row per field) comes after schedule and
detail: about 0.5 day.
