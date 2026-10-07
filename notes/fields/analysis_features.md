# Analysis features — `features/engine.py` (not a stage)

**Answers: which model features exist, and are they alive?** These are not stored fields. The
engine builds them in memory from the joined analysis input (schedule stage 3 + detail stage 3 +
the live aggregates), as of each round. Carried over from the old `notes/FIELDS.md` §6; their
redesign waits for the stage files to exist (plan P5).

46 names. Ledger status from `notes/STATE.md`.

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

Several of these move into the stage files as plain fields: `mkt_sup`, `mkt_tot`, `mkt_p_*`
(S2.17–21), the days since the last match (D3.24). `guess_minus_market` needs the crowd vote
(D1.13–14), which P2 may drop as not shown before kickoff.
