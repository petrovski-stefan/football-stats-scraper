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
    # Over/Under — the goal line is Asian and variable, so `ou_line` is the market's
    # goal-total forecast and `implied_over` is only the sub-quarter tilt around it.
    "has_ou_odds",
    "ou_line",
    "over_odds",
    "under_odds",
    "implied_over",
    # Asian Handicap — positive `ah_line` means the HOME side is favoured (opposite of
    # football-data.co.uk's AHh convention).
    "has_ah_odds",
    "ah_line",
    "ah_home_odds",
    "ah_away_odds",
    "implied_ah_home",
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
    # The referenced match's own ids, read from the history row's `index` / `name`
    # attributes. Without these a history row is an orphan: it cannot be joined to goal
    # timings, or to anything else. Added 2026-09-22; detail files scraped before that
    # date do not carry them.
    "match_id",
    "league_id",
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


# --- Goal timings (data/raw/goals.csv, data/raw/goals_done.csv) ---------------
# A GLOBAL store keyed by match id, not a per-league-season file: the matches referenced by
# a fixture's history come from cups, European competition and other leagues, so they
# belong to no single league-season, and the whole point of keying on the id is that the
# dedupe works across all of them. `league_id` keeps the provenance.
GOALS_ORDERED_COLUMNS = [
    "match_id",
    "league_id",
    "goal_index",
    "minute",
    "stoppage",
    "side",
    "home_score_after",
    "away_score_after",
    "kind",
]

# The attempt log. A goalless match yields no rows in goals.csv, so "has this been
# scraped?" cannot be answered from that file alone — without this, every 0-0 would be
# re-scraped on every run, forever.
GOALS_DONE_COLUMNS = ["match_id", "scraped_at", "n_goals"]


# --- Cards and substitutions (data/raw/events.csv, data/raw/events_done.csv) --
# Global and keyed by match id for the same reason the goal store is: the events wanted
# are those of the matches in a fixture's history, which span competitions. `player` and
# `player_off` are stored because they are what makes de-duplication exact when a page
# renders its event list twice -- see domain/event.py.
EVENTS_ORDERED_COLUMNS = [
    "match_id",
    "league_id",
    "event_index",
    "minute",
    "stoppage",
    "side",
    "kind",
    "player",
    "player_off",
]

# The attempt log. A match with no cards and no substitutions yields no rows, so the same
# argument that gives goals a separate log applies here.
EVENTS_DONE_COLUMNS = ["match_id", "scraped_at", "n_events"]
