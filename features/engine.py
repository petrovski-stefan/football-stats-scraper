"""Feature engine shared by both comeback studies.

Builds, one row per match from `data/archived/processed/*_enriched.csv`:
  - `FAMILIES` — the six nowgoal-exclusive families of the F12 re-test
    (notes/RECORD/PREREGISTRATION.md), plus the mandatory market and totals controls;
  - `FILTER_FAMILIES` — the goal-focused G1/G2/G3 families of the exclusion-filter
    study (notes/RECORD/PREREGISTRATION_FILTER.md).

No scraping: rolling team form is derived as-of-round from the base league columns,
and the rest from the detail page's per-match history blocks (match-anchored, see
notes/HISTORY/HANDOFF.md S4).

The as-of invariant: every rolling feature for a match in round R uses only that
team's matches in rounds < R. Each team plays exactly once per round in these
leagues (asserted at build time), so a groupby-shift(1) enforces it.

Run: `uv run python -m features.engine` (summary) or `--self-check` (invariant proof).
"""

import argparse
import warnings
from typing import Any

import numpy as np
import pandas as pd

from domain import paths, scope
from domain.clock import SECONDS_PER_DAY
from domain.columns import MATCHES_PER_SECTION
from features import events as event_features
from features import goals as goal_features

# Literal season labels, fixed by PREREGISTRATION.md §2. Only cross-year labels appear
# here because the preregistered corpus is 2 European leagues; a calendar-year league
# ("2025") therefore matches neither and is excluded — see `_warn_unassigned`.
TRAIN_SEASONS = ("2023-2024", "2024-2025")
TEST_SEASONS = ("2025-2026",)

# Preregistered: last-6 form window, 5-round burn-in (rounds 1-5 carry no features).
FORM_WINDOW = 6
BURN_IN_ROUNDS = 5
CONGESTION_DAYS = 14

# The self-check's two computations agree when they differ by less than float noise.
SELF_CHECK_TOLERANCE = 1e-9

# Rolling as-of-round team quantities: (source column in the long frame, output name).
ROLLING_SPECS: list[tuple[str, str]] = [
    ("ht_trail", "ht_trail_rate"),
    ("h1_gd", "h1_gd_avg"),
    ("h2_gd", "h2_gd_avg"),
    ("blown_lead", "blown_lead_rate"),
    ("h1_gf", "h1_gf_avg"),
    ("h1_ga", "h1_ga_avg"),
    ("h2_gf", "h2_gf_avg"),
    ("h2_ga", "h2_ga_avg"),
]

# The closed family list. Nothing may be added after preregistration.
FAMILIES: dict[str, list[str]] = {
    "A_ht_state": ["home_ht_trail_rate", "away_ht_trail_rate", "home_h1_gd_avg", "away_h1_gd_avg"],
    "B_2h_supremacy": [
        "home_h2_gd_avg",
        "away_h2_gd_avg",
        "home_blown_lead_rate",
        "away_blown_lead_rate",
    ],
    "C_pressure": ["home_corner_goal_share_gap", "away_corner_goal_share_gap"],
    "D_non_market": ["strength_gap", "guess_minus_market"],
    "E_congestion": [
        "home_matches_14d",
        "away_matches_14d",
        "home_days_since_last",
        "away_days_since_last",
    ],
    "F_venue_h2h": ["venue_ppg_gap", "h2h_ht_nondraw_rate"],
}

# --- Exclusion-filter families (notes/RECORD/PREREGISTRATION_FILTER.md S5) -----------
# Closed list, and deliberately goal-focused: the filter's job is to forecast the
# scoreline environment, not to score teams.
FILTER_FAMILIES: dict[str, list[str]] = {
    "G1_recent_goals": [
        "home_h1_gf_avg",
        "home_h1_ga_avg",
        "home_h2_gf_avg",
        "home_h2_ga_avg",
        "away_h1_gf_avg",
        "away_h1_ga_avg",
        "away_h2_gf_avg",
        "away_h2_ga_avg",
        "home_recent_gf_avg",
        "home_recent_ga_avg",
        "away_recent_gf_avg",
        "away_recent_ga_avg",
        "home_recent_over25_rate",
        "away_recent_over25_rate",
    ],
    "G2_h2h_goals": [
        "h2h_avg_total_goals",
        "h2h_over25_rate",
        "h2h_ht_goals_avg",
        "h2h_ht_nondraw_rate",
    ],
    "G3_odds": ["mkt_sup", "mkt_tot", "mkt_p_draw", "odds_drift_home", "odds_drift_away"],
}


# --- Market Asian lines (captured from 2026-09-22) ---------------------------
# Deliberately NOT added to FAMILIES or FILTER_FAMILIES, both of which are closed lists
# fixed by notes/RECORD/PREREGISTRATION.md S4 and notes/RECORD/PREREGISTRATION_FILTER.md S5.
# Widening a preregistered family is a protocol amendment, not a code change, so these live
# in their own set and stay exploratory until a preregistration admits them.
#
# The goal line is Asian and variable: nowgoal moves the line and holds both prices near
# 1.90, so `ou_line` is the market's goal-total forecast and `implied_over` is only the
# sub-quarter tilt around it. A fixed 2.5 line is the opposite split: there the price
# carries everything.
MARKET_LINE_FEATURES = ["ou_line", "implied_over", "ah_line", "abs_ah_line", "implied_ah_home"]

# --- Goal timings (captured from 2026-09-22) ---------------------------------
# Same standing as MARKET_LINE_FEATURES: exploratory, and deliberately NOT added to
# FAMILIES or FILTER_FAMILIES, which notes/RECORD/PREREGISTRATION*.md close. Built by
# features/goals.py from the global store and joined in by features/enrich.py.
# Taken from features/goals.py rather than restated, so the two cannot drift apart when a
# feature is added there. Timelines are deliberately excluded: they are strings for
# analysis, not numeric model inputs.
GOAL_TIMING_FEATURES = goal_features.feature_names()

# --- Cards and substitutions (captured from 2026-09-23) ----------------------
# Same standing again: exploratory, outside the closed families, built by features/
# events.py and joined in by features/enrich.py. `reds_against_rate` is the only one with
# a comeback mechanism behind it (playing ten men wins matches you were losing) and it is
# also the sparsest -- 0.05 red cards per match means a five-match window usually reads
# zero. Timelines excluded here for the same reason as the goal ones: strings, not inputs.
EVENT_FEATURES = event_features.feature_names()


def filter_feature_names() -> list[str]:
    """Every feature of the exclusion-filter families, in family order."""

    return [name for names in FILTER_FAMILIES.values() for name in names]


# Mandatory controls, present in every model on both sides of every comparison.
MARKET_CONTROLS = ["mkt_sup", "mkt_tot"]
TOTALS_CONTROLS = ["combined_recent_gf", "h2h_avg_total_goals"]
CONTROLS = MARKET_CONTROLS + TOTALS_CONTROLS

IDENTITY = ["match_id", "league_name", "season", "round", "date", "split"]
# Everything the models need to build targets and the imported F11 completion stage.
TARGETS = [
    "ht_home_goals",
    "ht_away_goals",
    "ft_home_goals",
    "ft_away_goals",
    "home_2h_goals",
    "away_2h_goals",
    "total_goals",
    "is_comeback",
    "close_odds_home",
    "close_odds_away",
]

# Post-match columns: labels, oracle inputs and scoring only — never model features.
# The deleted `modelling/scoreline.py --leak-check` set exactly these to NaN. Nothing reads
# the list now: it waits for DECISIONS D5, whose option 1 gives this engine the same check.
POST_MATCH_COLUMNS = [
    "ht_home_goals",
    "ht_away_goals",
    "ft_home_goals",
    "ft_away_goals",
    "home_2h_goals",
    "away_2h_goals",
    "total_goals",
    "is_comeback",
]


ROUND_GROUP = ["league_name", "season", "stage", "round"]


def round_position(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Tie-aware position of each match in its round, from kickoff (`features/CLAUDE.md` §6).

    In no preregistered family: FAMILIES and FILTER_FAMILIES are closed lists
    (`notes/RECORD/PREREGISTRATION.md` §4).

    Returns:
        `earlier`: the round's matches that kick off strictly before this one (0 = joint first);
        `later`: the same, strictly after (0 = joint last); `slot`: this match's wave of
        kickoffs, 1..`slots`; `slots`: the round's distinct kickoff times.
    """

    # Only the frame's rows count: for a partly played round that is the finished subset,
    # while `matches_in_round` is the count at scrape time.
    dates = pd.to_datetime(matches_df["date"], errors="coerce")
    group = dates.groupby([matches_df[c] for c in ROUND_GROUP], dropna=False)

    return pd.DataFrame(
        {
            "earlier": group.rank(method="min").astype("Int64") - 1,
            "later": group.transform("size") - group.rank(method="max").astype("Int64"),
            "slot": group.rank(method="dense").astype("Int64"),
            "slots": group.transform("nunique"),
        },
        index=matches_df.index,
    )


def load_enriched() -> pd.DataFrame:
    """Load every enriched league-season into one frame, tagged with its split."""

    files = paths.enriched_csvs()
    if not files:
        raise FileNotFoundError(
            f"no *_enriched.csv in {paths.PROCESSED_DIR}/ — run `python -m scrapers.schedule`, "
            "then `python -m scrapers.detail`, then `python -m features.enrich`"
        )

    enriched_df = pd.concat([pd.read_csv(p) for p in files], ignore_index=True)
    matches_df = enriched_df.assign(
        split=np.where(
            enriched_df["season"].isin(TRAIN_SEASONS),
            "dev",
            np.where(enriched_df["season"].isin(TEST_SEASONS), "holdout", ""),
        ),
        date=pd.to_datetime(enriched_df["date"], errors="coerce"),
    )

    _warn_unassigned(matches_df)

    return matches_df


def _warn_unassigned(matches_df: pd.DataFrame) -> None:
    """Warn about league-seasons in neither split, instead of dropping them in silence.

    Their exclusion is right, because the preregistered corpus is closed (`features/CLAUDE.md`
    §7); the silence is not."""

    unassigned_df = matches_df.loc[
        matches_df["split"] == "", ["league_name", "season"]
    ].drop_duplicates()
    if unassigned_df.empty:
        return

    listed = ", ".join(f"{r.league_name} {r.season}" for r in unassigned_df.itertuples())
    warnings.warn(
        f"{len(unassigned_df)} league-season(s) match neither TRAIN_SEASONS nor TEST_SEASONS "
        f"and are excluded from dev and holdout: {listed}. This is expected for anything "
        "outside the preregistered corpus (PREREGISTRATION.md §2); widening the splits is "
        "a protocol amendment, not a code change.",
        stacklevel=3,
    )


# --- Rolling as-of-round team form (families A and B) -------------------------


def _team_match_long(matches_df: pd.DataFrame) -> pd.DataFrame:
    """One row per team per match, from that team's own perspective."""

    frames = []
    for side, opp in (("home", "away"), ("away", "home")):
        frames.append(
            pd.DataFrame(
                {
                    "league_name": matches_df["league_name"],
                    "season": matches_df["season"],
                    "round": matches_df["round"],
                    "match_id": matches_df["match_id"],
                    "team_id": matches_df[f"{side}_team_id"],
                    "h1_gf": matches_df[f"ht_{side}_goals"],
                    "h1_ga": matches_df[f"ht_{opp}_goals"],
                    "h2_gf": matches_df[f"{side}_2h_goals"],
                    "h2_ga": matches_df[f"{opp}_2h_goals"],
                    "ft_gf": matches_df[f"ft_{side}_goals"],
                    "ft_ga": matches_df[f"ft_{opp}_goals"],
                }
            )
        )

    team_matches_df = pd.concat(frames, ignore_index=True)
    team_matches_df["ht_trail"] = (team_matches_df["h1_gf"] < team_matches_df["h1_ga"]).astype(
        float
    )
    team_matches_df["h1_gd"] = team_matches_df["h1_gf"] - team_matches_df["h1_ga"]
    team_matches_df["h2_gd"] = team_matches_df["h2_gf"] - team_matches_df["h2_ga"]

    led = team_matches_df["h1_gf"] > team_matches_df["h1_ga"]
    won = team_matches_df["ft_gf"] > team_matches_df["ft_ga"]
    team_matches_df["blown_lead"] = (led & ~won).astype(float)

    return team_matches_df


def _rolling_form(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Last-`FORM_WINDOW` team form, strictly from earlier rounds.

    Each team plays once per round here (asserted), so shifting one row inside a
    team's own chronological sequence is exactly a `round < current` cutoff.
    """

    team_matches_df = _team_match_long(matches_df)

    per_round = team_matches_df.groupby(["league_name", "season", "round", "team_id"]).size()
    if int(per_round.max()) != 1:
        raise AssertionError(
            "as-of invariant unsafe: a team plays more than once in a round "
            f"(max={int(per_round.max())}) — shift(1) no longer implies round < current"
        )

    team_matches_df = team_matches_df.sort_values(["league_name", "season", "team_id", "round"])
    grouped = team_matches_df.groupby(["league_name", "season", "team_id"], sort=False)

    form_df = team_matches_df[["match_id", "team_id"]].copy()
    for src, dst in ROLLING_SPECS:
        shifted = grouped[src].shift(1)
        form_df[dst] = shifted.groupby(
            [team_matches_df["league_name"], team_matches_df["season"], team_matches_df["team_id"]],
            sort=False,
        ).transform(
            lambda team_values: team_values.rolling(FORM_WINDOW, min_periods=BURN_IN_ROUNDS).mean()
        )

    return form_df


def _attach_rolling(matches_df: pd.DataFrame) -> dict[str, Any]:
    """Each side's rolling form, as `home_<field>` and `away_<field>` arrays in row order."""

    form_df = _rolling_form(matches_df)
    form_columns = [dst for _, dst in ROLLING_SPECS]

    side_columns: dict[str, Any] = {}
    for side in ("home", "away"):
        side_form_df = matches_df[["match_id", f"{side}_team_id"]].merge(
            form_df,
            left_on=["match_id", f"{side}_team_id"],
            right_on=["match_id", "team_id"],
            how="left",
        )

        for column in form_columns:
            side_columns[f"{side}_{column}"] = side_form_df[column].to_numpy()

    return side_columns


# --- Per-match history blocks (families C, E, F) ------------------------------


def _block(matches_df: pd.DataFrame, section: str, slot: int, field: str) -> "pd.Series[Any]":
    """One field of a history slot, all NaN when the matrix has no such column."""

    column = f"{section}_last{slot}_{field}"
    if column in matches_df.columns:
        return matches_df[column]

    return pd.Series(np.nan, index=matches_df.index)


def _corner_goal_share_gap(matches_df: pd.DataFrame, section: str) -> "pd.Series[Any]":
    """Last-6 corner share minus goal share, from the subject team's view (F7 of the old league
    study, dropped 2026-10-13): comeback teams out-shoot even ordinary winners, so more corners
    than goals is dominance not yet converted. Corners are this corpus's pressure proxy."""

    subject_corners: pd.Series[Any] = pd.Series(0.0, index=matches_df.index)
    total_corners = pd.Series(0.0, index=matches_df.index)
    subject_goals = pd.Series(0.0, index=matches_df.index)
    total_goals = pd.Series(0.0, index=matches_df.index)
    for slot in range(1, MATCHES_PER_SECTION + 1):
        is_home = _block(matches_df, section, slot, "is_home").astype("boolean")
        home_corners = _block(matches_df, section, slot, "corners_ft_home")
        away_corners = _block(matches_df, section, slot, "corners_ft_away")
        home_goals = _block(matches_df, section, slot, "ft_home_goals")
        away_goals = _block(matches_df, section, slot, "ft_away_goals")

        is_known = (
            is_home.notna()
            & home_corners.notna()
            & away_corners.notna()
            & home_goals.notna()
            & away_goals.notna()
        )
        own_corners = np.where(is_home.fillna(False), home_corners, away_corners)
        own_goals = np.where(is_home.fillna(False), home_goals, away_goals)

        subject_corners += np.where(is_known, own_corners, 0.0)
        total_corners += np.where(is_known, home_corners.fillna(0) + away_corners.fillna(0), 0.0)
        subject_goals += np.where(is_known, own_goals, 0.0)
        total_goals += np.where(is_known, home_goals.fillna(0) + away_goals.fillna(0), 0.0)

    corner_share = np.where(total_corners > 0, subject_corners / total_corners, np.nan)
    goal_share = np.where(total_goals > 0, subject_goals / total_goals, np.nan)
    gap: pd.Series[Any] = pd.Series(corner_share - goal_share, index=matches_df.index)

    return gap


def _congestion(
    matches_df: pd.DataFrame, section: str
) -> tuple["pd.Series[Any]", "pd.Series[Any]"]:
    """Competitive matches in the last 14 days, and days since the last match.

    Nowgoal-exclusive: the history blocks carry the cup and European fixtures that league-only
    schedules omit, so this differs from league-only rest days."""

    played = pd.Series(0, index=matches_df.index, dtype="int64")
    most_recent = pd.Series(pd.NaT, index=matches_df.index, dtype="datetime64[ns]")
    for slot in range(1, MATCHES_PER_SECTION + 1):
        when = pd.to_datetime(_block(matches_df, section, slot, "date"), errors="coerce")
        league = _block(matches_df, section, slot, "league").astype("string").str.lower()
        gap_days = (matches_df["date"] - when).dt.total_seconds() / SECONDS_PER_DAY
        competitive = ~league.str.contains(scope.FRIENDLY_MARKER, na=False)

        recent = competitive & gap_days.between(0, CONGESTION_DAYS)
        played += recent.fillna(False).astype("int64")
        most_recent = most_recent.where(most_recent.notna() | when.isna(), when)

    days_since = (matches_df["date"] - most_recent).dt.total_seconds() / SECONDS_PER_DAY

    return played.astype(float), days_since


def _h2h_ht_goals_avg(matches_df: pd.DataFrame) -> "pd.Series[Any]":
    """Mean total half-time goals in past meetings of this fixture.

    The exclusion filter needs the first-half goal environment: a fixture that reliably
    reaches the break goalless cannot build the lead a comeback has to reverse."""

    total = pd.Series(0.0, index=matches_df.index)
    seen = pd.Series(0.0, index=matches_df.index)
    for slot in range(1, MATCHES_PER_SECTION + 1):
        home_goals = _block(matches_df, "h2h", slot, "ht_home_goals")
        away_goals = _block(matches_df, "h2h", slot, "ht_away_goals")
        ok = home_goals.notna() & away_goals.notna()

        total += (home_goals.fillna(0) + away_goals.fillna(0)).where(ok, 0.0)
        seen += ok.astype(float)

    avg: pd.Series[Any] = pd.Series(
        np.where(seen > 0, total / seen, np.nan), index=matches_df.index
    )

    return avg


def _h2h_ht_nondraw_rate(matches_df: pd.DataFrame) -> "pd.Series[Any]":
    """Share of past meetings in this fixture that were non-draws at half-time.

    Factor 1 is "does anyone lead at HT" — a fixture that historically produces
    separated half-times is the natural fixture-level predictor of it.
    """

    hits = pd.Series(0.0, index=matches_df.index)
    seen = pd.Series(0.0, index=matches_df.index)
    for slot in range(1, MATCHES_PER_SECTION + 1):
        home_goals = _block(matches_df, "h2h", slot, "ht_home_goals")
        away_goals = _block(matches_df, "h2h", slot, "ht_away_goals")
        ok = home_goals.notna() & away_goals.notna()

        hits += (ok & (home_goals != away_goals)).astype(float)
        seen += ok.astype(float)

    return pd.Series(np.where(seen > 0, hits / seen, np.nan), index=matches_df.index)


# --- Market controls and the imported completion stage's inputs ---------------


def _market_lines(matches_df: pd.DataFrame) -> dict[str, Any]:
    """The schedule page's Asian goal line and handicap, and the handicap's size.

    `abs_ah_line` is the mismatch measure (a positive line favours home). A corpus scraped
    before 2026-09-22 has none of these columns, so they come back NaN."""

    def column_or_nan(name: str) -> "pd.Series[Any]":
        """The column `name`, all NaN when the corpus has none."""

        return (
            matches_df[name]
            if name in matches_df.columns
            else pd.Series(np.nan, index=matches_df.index)
        )

    ah_line = column_or_nan("ah_line")

    return {
        "ou_line": column_or_nan("ou_line"),
        "implied_over": column_or_nan("implied_over"),
        "ah_line": ah_line,
        "abs_ah_line": ah_line.abs(),
        "implied_ah_home": column_or_nan("implied_ah_home"),
    }


def _goal_timings(matches_df: pd.DataFrame) -> dict[str, Any]:
    """Pass the goal-timing and event aggregates through, NaN when they were never built.

    `features/enrich.py` builds them from the global stores, so a corpus enriched before
    `scrapers.goals` ran has none; NaN rather than an error, as in `_market_lines`."""

    return {
        name: matches_df[name]
        if name in matches_df.columns
        else pd.Series(np.nan, index=matches_df.index)
        for name in GOAL_TIMING_FEATURES + EVENT_FEATURES
    }


def _vig_free(matches_df: pd.DataFrame) -> dict[str, Any]:
    """Proportionally de-vigged 1X2 probabilities from the opening price."""

    inv_h = 1.0 / matches_df["home_win_initial_odds"]
    inv_d = 1.0 / matches_df["draw_initial_odds"]
    inv_a = 1.0 / matches_df["away_win_initial_odds"]
    total = inv_h + inv_d + inv_a
    p_home, p_draw, p_away = inv_h / total, inv_d / total, inv_a / total

    return {
        "mkt_p_home": p_home,
        "mkt_p_draw": p_draw,
        "mkt_p_away": p_away,
        # Supremacy and a totals proxy: the two dimensions a 1X2 price carries.
        "mkt_sup": np.log(p_home / p_away),
        "mkt_tot": -np.log(p_draw),
    }


def _closing_odds(matches_df: pd.DataFrame) -> dict[str, Any]:
    """Raw decimal closing odds per side, for the imported F11 completion curve.

    F11 is defined on the trailer's closing price; the detail page's "live" column stands in
    for it (`notes/RECORD/PREREGISTRATION.md` §9), the opening price where it is missing."""

    return {
        f"close_odds_{side}": matches_df[f"odds1x2_live_{side}"].fillna(
            matches_df[f"odds1x2_init_{side}"].fillna(matches_df[f"{side}_win_initial_odds"])
        )
        for side in ("home", "away")
    }


# --- Assembly -----------------------------------------------------------------


def build_features(matches_df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Assemble the full preregistered feature matrix, one row per match."""

    matches_df = load_enriched() if matches_df is None else matches_df.copy()

    built: dict[str, Any] = {}
    built.update(_market_lines(matches_df))
    built.update(_goal_timings(matches_df))
    built.update(_vig_free(matches_df))
    built.update(_closing_odds(matches_df))
    built.update(_attach_rolling(matches_df))

    for side in ("home", "away"):
        built[f"{side}_corner_goal_share_gap"] = _corner_goal_share_gap(matches_df, side)
        played, days_since = _congestion(matches_df, side)
        built[f"{side}_matches_14d"] = played
        built[f"{side}_days_since_last"] = days_since

    built["strength_gap"] = matches_df["strength_home"] - matches_df["strength_away"]
    guess_gap = (matches_df["guess_home_pct"] - matches_df["guess_away_pct"]) / 100.0
    built["guess_minus_market"] = guess_gap - built["mkt_p_home"] + built["mkt_p_away"]

    built["venue_ppg_gap"] = (
        matches_df["home_recent_venue_ppg"] - matches_df["away_recent_venue_ppg"]
    )
    built["h2h_ht_nondraw_rate"] = _h2h_ht_nondraw_rate(matches_df)

    built["combined_recent_gf"] = (
        matches_df["home_recent_gf_avg"] + matches_df["away_recent_gf_avg"]
    )

    # Exclusion-filter additions (G2 / G3).
    built["h2h_ht_goals_avg"] = _h2h_ht_goals_avg(matches_df)
    for side in ("home", "away"):
        built[f"odds_drift_{side}"] = (
            matches_df[f"implied_live_{side}"] - matches_df[f"implied_init_{side}"]
        )

    engineered_df = pd.DataFrame(built, index=matches_df.index)
    wanted = _dedupe(
        IDENTITY
        + TARGETS
        + CONTROLS
        + all_feature_names()
        + filter_feature_names()
        + MARKET_LINE_FEATURES
        + GOAL_TIMING_FEATURES
        + EVENT_FEATURES
    )

    keep_raw = [c for c in wanted if c not in engineered_df.columns]
    matrix_df = pd.concat([matches_df[keep_raw], engineered_df], axis=1)

    return matrix_df[wanted].copy()


def all_feature_names() -> list[str]:
    """Every feature of the closed families, in family order."""

    return [name for names in FAMILIES.values() for name in names]


def _dedupe(names: list[str]) -> list[str]:
    """Order-preserving dedupe — the two studies' family lists overlap."""

    return list(dict.fromkeys(names))


def in_burn_in(matrix_df: pd.DataFrame) -> "pd.Series[Any]":
    """Rounds 1..BURN_IN_ROUNDS, where rolling form does not yet exist.

    Dropped identically for every model so the comparison stays fair.
    """

    return matrix_df["round"] <= BURN_IN_ROUNDS


# --- Verification -------------------------------------------------------------


def self_check(sample: int = 100, seed: int = 0) -> int:
    """Recompute rolling features the slow way and prove the as-of-round cutoff.

    For each sampled match, rebuild each team's last-6 form from scratch using
    *only* that team's matches in strictly earlier rounds, and compare.
    """

    matches_df = load_enriched()
    matrix_df = build_features(matches_df)
    matrix_with_teams_df = matrix_df.merge(
        matches_df[["match_id", "home_team_id", "away_team_id"]], on="match_id", how="left"
    )
    team_matches_df = _team_match_long(matches_df)

    rng = np.random.default_rng(seed)
    candidates_df = matrix_with_teams_df[~in_burn_in(matrix_with_teams_df)]
    chosen = rng.choice(len(candidates_df), size=min(sample, len(candidates_df)), replace=False)
    picks_df = candidates_df.iloc[chosen]

    failures = 0
    checks = 0
    for _, row in picks_df.iterrows():
        for side in ("home", "away"):
            history = team_matches_df[
                (team_matches_df["league_name"] == row["league_name"])
                & (team_matches_df["season"] == row["season"])
                & (team_matches_df["team_id"] == row[f"{side}_team_id"])
                & (team_matches_df["round"] < row["round"])
            ].sort_values("round")

            window = history.tail(FORM_WINDOW)
            if len(window) < BURN_IN_ROUNDS:
                continue

            for src, dst in ROLLING_SPECS:
                checks += 1
                expected = float(window[src].mean())
                actual = row[f"{side}_{dst}"]
                if pd.isna(actual) or abs(float(actual) - expected) > SELF_CHECK_TOLERANCE:
                    failures += 1
                    print(
                        f"  MISMATCH match {row['match_id']} {side} {dst}: "
                        f"vectorised={actual} slow-recompute={expected}"
                    )

    print(f"as-of-round self-check: {checks} comparisons, {failures} mismatches")
    if failures == 0:
        print("  PASS — no rolling feature uses data from the target round or later")

    return failures


def summarise(matrix_df: pd.DataFrame) -> None:
    """Print the matrix's rows and comebacks per split, then the fill rate of each feature."""

    print("=" * 78)
    print("FEATURE MATRIX")
    print("=" * 78)

    usable_df = matrix_df[~in_burn_in(matrix_df)]
    print(f"  rows: {len(matrix_df)} total, {len(usable_df)} after {BURN_IN_ROUNDS}-round burn-in")

    for split in ("dev", "holdout"):
        split_df = usable_df[usable_df["split"] == split]
        if split_df.empty:
            # Normal while the corpus is being rebuilt one league-season at a time:
            # a single 2025-2026 season is all holdout and leaves dev empty.
            print(f"    {split:8s} n=    0  (no league-season in this split)")
            continue

        comebacks = int(split_df["is_comeback"].sum())
        nondraw = int((split_df["ht_home_goals"] != split_df["ht_away_goals"]).sum())
        print(
            f"    {split:8s} n={len(split_df):5d}  "
            f"comebacks={comebacks:4d} ({comebacks / len(split_df):.2%})  "
            f"HT non-draws={nondraw:4d} ({nondraw / len(split_df):.1%})"
        )

    print("\n  fill rate by family (post burn-in):")
    for family, names in FAMILIES.items():
        fills = [f"{name}={usable_df[name].notna().mean():.0%}" for name in names]
        print(f"    {family:16s} {'  '.join(fills)}")

    print("\n  exclusion-filter families (post burn-in):")
    for family, names in FILTER_FAMILIES.items():
        worst = min(usable_df[name].notna().mean() for name in names)
        print(f"    {family:18s} {len(names):2d} features, lowest fill={worst:.0%}")

    print("\n  market Asian lines (exploratory, outside the closed families):")
    for name in MARKET_LINE_FEATURES:
        print(f"    {name:24s} fill={usable_df[name].notna().mean():.0%}")

    print("\n  goal timings (exploratory, outside the closed families):")
    for name in GOAL_TIMING_FEATURES:
        print(f"    {name:26s} fill={usable_df[name].notna().mean():.0%}")

    print("\n  cards and substitutions (exploratory, outside the closed families):")
    for name in EVENT_FEATURES:
        print(f"    {name:26s} fill={usable_df[name].notna().mean():.0%}")

    print("\n  controls:")
    for name in CONTROLS:
        print(f"    {name:24s} fill={usable_df[name].notna().mean():.0%}")


def main() -> None:
    """Entry point: print the feature matrix's summary, or prove the as-of-round invariant."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true", help="prove the as-of-round invariant")
    parser.add_argument("--sample", type=int, default=100, help="matches to verify in --self-check")
    args = parser.parse_args()

    if args.self_check:
        raise SystemExit(1 if self_check(args.sample) else 0)

    summarise(build_features())


if __name__ == "__main__":
    main()
