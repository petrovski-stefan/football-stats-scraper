"""The contract for one row of the detail scrape (`scrapers/detail.py`), keyed by `match_id`."""

from pydantic import BaseModel, computed_field

from domain import stats


class MatchDetail(BaseModel):
    """Wide feature row scraped from a match's detail page, joined to the base
    match by `match_id`. Every section field is nullable — a block may be absent
    on a given page (e.g. fixtures/strength for some finished matches).
    """

    match_id: str

    # --- Live Odds Comparison (1X2, preferred bookmaker) ---
    odds_bookmaker: str | None = None
    odds1x2_init_home: float | None = None
    odds1x2_init_draw: float | None = None
    odds1x2_init_away: float | None = None
    odds1x2_live_home: float | None = None
    odds1x2_live_draw: float | None = None
    odds1x2_live_away: float | None = None

    # --- Home team recent form (table_v1) ---
    home_recent_played: int = 0
    home_recent_wins: int | None = None
    home_recent_draws: int | None = None
    home_recent_losses: int | None = None
    home_recent_ppg: float | None = None
    home_recent_gf_avg: float | None = None
    home_recent_ga_avg: float | None = None
    home_recent_over25_rate: float | None = None
    home_recent_btts_rate: float | None = None
    home_recent_form: str | None = None
    home_recent_venue_ppg: float | None = None
    home_recent_venue_over25_rate: float | None = None

    # --- Away team recent form (table_v2) ---
    away_recent_played: int = 0
    away_recent_wins: int | None = None
    away_recent_draws: int | None = None
    away_recent_losses: int | None = None
    away_recent_ppg: float | None = None
    away_recent_gf_avg: float | None = None
    away_recent_ga_avg: float | None = None
    away_recent_over25_rate: float | None = None
    away_recent_btts_rate: float | None = None
    away_recent_form: str | None = None
    away_recent_venue_ppg: float | None = None
    away_recent_venue_over25_rate: float | None = None

    # --- Head to Head (table_v3), oriented to the current home team ---
    h2h_played: int = 0
    h2h_home_team_wins: int | None = None
    h2h_draws: int | None = None
    h2h_away_team_wins: int | None = None
    h2h_over25_rate: float | None = None
    h2h_btts_rate: float | None = None
    h2h_avg_total_goals: float | None = None

    # --- Strength Comparison / crowd prediction ---
    strength_home: int | None = None
    strength_away: int | None = None
    h2h_compare_home_pct: float | None = None
    h2h_compare_away_pct: float | None = None
    guess_home_pct: float | None = None
    guess_away_pct: float | None = None

    # --- Fixture congestion ---
    home_next_fixture_days: int | None = None
    away_next_fixture_days: int | None = None

    # --- Implied probabilities from the bookmaker 1X2 odds ---
    @computed_field
    @property
    def implied_init_home(self) -> float | None:
        """The home win's implied chance from the initial 1X2 price, None without a price."""

        return stats.implied_prob(self.odds1x2_init_home)

    @computed_field
    @property
    def implied_init_away(self) -> float | None:
        """The away win's implied chance from the initial 1X2 price, None without a price."""

        return stats.implied_prob(self.odds1x2_init_away)

    @computed_field
    @property
    def implied_live_home(self) -> float | None:
        """The home win's implied chance from the live 1X2 price, None without a price."""

        return stats.implied_prob(self.odds1x2_live_home)

    @computed_field
    @property
    def implied_live_away(self) -> float | None:
        """The away win's implied chance from the live 1X2 price, None without a price."""

        return stats.implied_prob(self.odds1x2_live_away)
