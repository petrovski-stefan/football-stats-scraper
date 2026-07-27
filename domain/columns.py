"""CSV output schema: the column order of every file the pipeline writes.

Where those files live is the companion contract in `domain/paths.py`.

Split out of the old flat `constants.py`, whose other half (DOM selectors, user
agents) is scraper-internal and now lives in `scrapers/constants.py`. These names
are a data *contract* — the scrapers write them and the feature layer reads them —
so they sit beside the Pydantic models that define the same rows.
"""

# Base columns that are empty in a *correct* scrape, so the dead-column canary in
# `qa/universal.py` must not read them as parser breakage. This is a statement about
# the contract, not an exemption for known defects: `stage` is the group/stage label,
# which single-table leagues do not have, and `Match.stage` types it as `str` with a
# documented "" default. A CSV cannot distinguish "" from missing, hence the declaration.
OPTIONAL_BASE_COLUMNS = frozenset({"stage"})

ORDERED_DF_COLUMNS = [
    # Match metadata
    "season",
    "league_id",
    "league_name",
    "stage",
    "round",
    "match_id",
    "date",
    # Teams
    "home_team_id",
    "away_team_id",
    "home_team_name",
    "away_team_name",
    # Standings positions (as of this round)
    "home_team_position",
    "away_team_position",
    "position_gap",
    # Position in round: 1..matches_in_round by kickoff time. See domain/match.py for
    # why `match_index_in_round == 1` must not be read as "first match of the round".
    "match_index_in_round",
    "matches_in_round",
    # Date-derived
    "day_of_week",
    "is_monday",
    "is_midweek",
    # Goals (raw score strings + derived integers)
    "ht_score",
    "ft_score",
    "ht_home_goals",
    "ht_away_goals",
    "ft_home_goals",
    "ft_away_goals",
    "home_2h_goals",
    "away_2h_goals",
    "goals_1h",
    "goals_2h",
    "total_goals",
    # Results
    "ht_result",
    "ft_result",
    "ht_ft_combo",
    # 1X2 odds
    "has_odds",
    "home_win_initial_odds",
    "draw_initial_odds",
    "away_win_initial_odds",
    "implied_prob_home",
    "implied_prob_away",
    "favorite",
    "favorite_odds",
    "underdog_odds",
    # Bet markets
    "btts",
    "over_25",
    "is_seven_or_more_goals",
    "is_comeback",
    "is_comeback_home",
    "is_comeback_away",
]

# Detail-scrape output (domain.match_detail.MatchDetail), keyed by match_id.
DETAIL_ORDERED_COLUMNS = [
    "match_id",
    # Odds (1X2, preferred bookmaker) + implied probabilities
    "odds_bookmaker",
    "odds1x2_init_home",
    "odds1x2_init_draw",
    "odds1x2_init_away",
    "odds1x2_live_home",
    "odds1x2_live_draw",
    "odds1x2_live_away",
    "implied_init_home",
    "implied_init_away",
    "implied_live_home",
    "implied_live_away",
    # Home recent form
    "home_recent_played",
    "home_recent_wins",
    "home_recent_draws",
    "home_recent_losses",
    "home_recent_ppg",
    "home_recent_gf_avg",
    "home_recent_ga_avg",
    "home_recent_over25_rate",
    "home_recent_btts_rate",
    "home_recent_form",
    "home_recent_venue_ppg",
    "home_recent_venue_over25_rate",
    # Away recent form
    "away_recent_played",
    "away_recent_wins",
    "away_recent_draws",
    "away_recent_losses",
    "away_recent_ppg",
    "away_recent_gf_avg",
    "away_recent_ga_avg",
    "away_recent_over25_rate",
    "away_recent_btts_rate",
    "away_recent_form",
    "away_recent_venue_ppg",
    "away_recent_venue_over25_rate",
    # Head to head
    "h2h_played",
    "h2h_home_team_wins",
    "h2h_draws",
    "h2h_away_team_wins",
    "h2h_over25_rate",
    "h2h_btts_rate",
    "h2h_avg_total_goals",
    # Strength / prediction
    "strength_home",
    "strength_away",
    "h2h_compare_home_pct",
    "h2h_compare_away_pct",
    "guess_home_pct",
    "guess_away_pct",
    # Fixture congestion
    "home_next_fixture_days",
    "away_next_fixture_days",
]

# --- Per-historical-match columns --------------------------------------------
# Each historical match (H2H + each team's recent games) is flattened into its own
# prefixed column block, e.g. home_last1_*, away_last3_*, h2h_last1_* (last1 = most
# recent). One block per match up to MATCHES_PER_SECTION, padded with None.
PER_MATCH_SECTIONS = ("home", "away", "h2h")
MATCHES_PER_SECTION = 6
PER_MATCH_FIELDS = [
    "date",
    "league",
    "is_home",  # subject team was home in that match
    "opponent",
    "result",  # W / D / L from the subject team's perspective
    "ht_score",
    "ft_score",
    "ht_home_goals",
    "ht_away_goals",
    "ft_home_goals",
    "ft_away_goals",
    "total_goals",
    "ht_result",  # 1 / X / 2
    "ft_result",
    "over_25",
    "btts",
    "is_comeback",
    "odds_home",  # that match's 1X2 odds
    "odds_draw",
    "odds_away",
    "corners_ft_home",
    "corners_ft_away",
    "corners_ht_home",
    "corners_ht_away",
    "corners_total",
]


def per_match_columns() -> list[str]:
    """All flattened per-match column names, in section/index/field order."""
    return [
        f"{section}_last{n}_{field}"
        for section in PER_MATCH_SECTIONS
        for n in range(1, MATCHES_PER_SECTION + 1)
        for field in PER_MATCH_FIELDS
    ]


DETAIL_ORDERED_COLUMNS = DETAIL_ORDERED_COLUMNS + per_match_columns()
