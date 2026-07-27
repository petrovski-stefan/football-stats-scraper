"""Feature engine shared by both comeback studies.

Builds, one row per match from `data/processed/*_enriched.csv`:
  - `FAMILIES` — the six nowgoal-exclusive families of the F12 re-test
    (notes/PREREGISTRATION.md), plus the mandatory market and totals controls;
  - `FILTER_FAMILIES` — the goal-focused G1/G2/G3 families of the exclusion-filter
    study (notes/PREREGISTRATION_FILTER.md).

No scraping: rolling team form is derived as-of-round from the base league columns,
and the rest from the detail page's per-match history blocks (match-anchored, see
notes/HANDOFF.md S4).

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

from domain import paths
from domain.columns import MATCHES_PER_SECTION

# Literal season labels, fixed by PREREGISTRATION.md §2. Only cross-year labels appear
# here because the preregistered corpus is 2 European leagues; a calendar-year league
# ("2025") therefore matches neither and is excluded — see `_warn_unassigned`.
TRAIN_SEASONS = ("2023-2024", "2024-2025")
TEST_SEASONS = ("2025-2026",)

# Preregistered: last-6 form window, 5-round burn-in (rounds 1-5 carry no features).
FORM_WINDOW = 6
BURN_IN_ROUNDS = 5
CONGESTION_DAYS = 14
# Friendlies are excluded from the congestion count (PREREGISTRATION.md S4).
FRIENDLY_MARKER = "friendly"

# Rolling as-of-round team quantities: (source column in the long frame, output name).
# The goal *levels* (h1/h2 gf and ga) feed the exclusion filter's scoreline model; the
# differences and rates feed the F12 re-test's families A and B.
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

# --- Exclusion-filter families (notes/PREREGISTRATION_FILTER.md S5) -----------
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


def filter_feature_names() -> list[str]:
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
# `scoreline.py --leak-check` NaNs exactly these and requires identical predictions.
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


def round_position(df: pd.DataFrame) -> pd.DataFrame:
    """Tie-aware position of each match within its round, derived from kickoff time.

    `match_index_in_round` is a strict 1..N ordering with an alphabetical tiebreak, so
    `match_index_in_round == 1` names one arbitrary match among the 15.6% that share
    their round's earliest kickoff. These columns are the ones that carry meaning:

      earlier  matches in the round kicking off strictly before this one (0 = joint first)
      later    matches kicking off strictly after  (0 = joint last)
      slot     which wave of kickoffs this match belongs to, 1..slots
      slots    distinct kickoff times in the round

    Derived rather than stored: they are pure functions of `date`, which is already a
    column. Note they see only the rows present in the frame, so for a partially-played
    round they describe the finished subset — `matches_in_round` is the scrape-time count.

    Deliberately wired into no preregistered family: FAMILIES and FILTER_FAMILIES are
    closed lists (notes/PREREGISTRATION.md S4).
    """
    dates = pd.to_datetime(df["date"], errors="coerce")
    group = dates.groupby([df[c] for c in ROUND_GROUP], dropna=False)
    return pd.DataFrame(
        {
            "earlier": group.rank(method="min").astype("Int64") - 1,
            "later": group.transform("size") - group.rank(method="max").astype("Int64"),
            "slot": group.rank(method="dense").astype("Int64"),
            "slots": group.transform("nunique"),
        },
        index=df.index,
    )


def load_enriched() -> pd.DataFrame:
    """Load every enriched league-season into one frame, tagged with its split."""
    files = paths.enriched_csvs()
    if not files:
        raise FileNotFoundError(
            f"no *_enriched.csv in {paths.PROCESSED_DIR}/ — run `python -m scrapers.schedule`, "
            "then `python -m scrapers.detail`, then `python -m features.enrich`"
        )
    df = pd.concat([pd.read_csv(p) for p in files], ignore_index=True)
    out = df.assign(
        split=np.where(
            df["season"].isin(TRAIN_SEASONS),
            "dev",
            np.where(df["season"].isin(TEST_SEASONS), "holdout", ""),
        ),
        date=pd.to_datetime(df["date"], errors="coerce"),
    )
    _warn_unassigned(out)
    return out


def _warn_unassigned(df: pd.DataFrame) -> None:
    """Announce league-seasons that fall in neither split, instead of dropping them mutely.

    `TRAIN_SEASONS` / `TEST_SEASONS` are literal labels fixed by
    `notes/PREREGISTRATION.md` §2, so a newly scraped league-season — and in particular a
    calendar-year league, whose labels ("2025") can never match a cross-year list —
    correctly lands outside both. That exclusion is the *right* behaviour: the
    preregistered corpus is closed. Silence about it is not, because a whole league can
    then sit in `data/` contributing nothing to any result with no sign it was ignored.
    """
    unassigned = df.loc[df["split"] == "", ["league_name", "season"]].drop_duplicates()
    if unassigned.empty:
        return
    listed = ", ".join(f"{r.league_name} {r.season}" for r in unassigned.itertuples())
    warnings.warn(
        f"{len(unassigned)} league-season(s) match neither TRAIN_SEASONS nor TEST_SEASONS "
        f"and are excluded from dev and holdout: {listed}. This is expected for anything "
        "outside the preregistered corpus (PREREGISTRATION.md §2); widening the splits is "
        "a protocol amendment, not a code change.",
        stacklevel=3,
    )


# --- Rolling as-of-round team form (families A and B) -------------------------


def _team_match_long(df: pd.DataFrame) -> pd.DataFrame:
    """One row per team per match, from that team's own perspective."""
    frames = []
    for side, opp in (("home", "away"), ("away", "home")):
        frames.append(
            pd.DataFrame(
                {
                    "league_name": df["league_name"],
                    "season": df["season"],
                    "round": df["round"],
                    "match_id": df["match_id"],
                    "team_id": df[f"{side}_team_id"],
                    "h1_gf": df[f"ht_{side}_goals"],
                    "h1_ga": df[f"ht_{opp}_goals"],
                    "h2_gf": df[f"{side}_2h_goals"],
                    "h2_ga": df[f"{opp}_2h_goals"],
                    "ft_gf": df[f"ft_{side}_goals"],
                    "ft_ga": df[f"ft_{opp}_goals"],
                }
            )
        )
    long = pd.concat(frames, ignore_index=True)
    long["ht_trail"] = (long["h1_gf"] < long["h1_ga"]).astype(float)
    long["h1_gd"] = long["h1_gf"] - long["h1_ga"]
    long["h2_gd"] = long["h2_gf"] - long["h2_ga"]
    led = long["h1_gf"] > long["h1_ga"]
    won = long["ft_gf"] > long["ft_ga"]
    long["blown_lead"] = (led & ~won).astype(float)
    return long


def _rolling_form(df: pd.DataFrame) -> pd.DataFrame:
    """Last-`FORM_WINDOW` team form, strictly from earlier rounds.

    Each team plays once per round here (asserted), so shifting one row inside a
    team's own chronological sequence is exactly a `round < current` cutoff.
    """
    long = _team_match_long(df)

    per_round = long.groupby(["league_name", "season", "round", "team_id"]).size()
    if int(per_round.max()) != 1:
        raise AssertionError(
            "as-of invariant unsafe: a team plays more than once in a round "
            f"(max={int(per_round.max())}) — shift(1) no longer implies round < current"
        )

    long = long.sort_values(["league_name", "season", "team_id", "round"])
    grouped = long.groupby(["league_name", "season", "team_id"], sort=False)

    out = long[["match_id", "team_id"]].copy()
    for src, dst in ROLLING_SPECS:
        shifted = grouped[src].shift(1)
        out[dst] = shifted.groupby(
            [long["league_name"], long["season"], long["team_id"]], sort=False
        ).transform(lambda s: s.rolling(FORM_WINDOW, min_periods=BURN_IN_ROUNDS).mean())
    return out


def _attach_rolling(df: pd.DataFrame) -> dict[str, Any]:
    form = _rolling_form(df)
    cols = [dst for _, dst in ROLLING_SPECS]
    out: dict[str, Any] = {}
    for side in ("home", "away"):
        merged = df[["match_id", f"{side}_team_id"]].merge(
            form,
            left_on=["match_id", f"{side}_team_id"],
            right_on=["match_id", "team_id"],
            how="left",
        )
        for c in cols:
            out[f"{side}_{c}"] = merged[c].to_numpy()
    return out


# --- Per-match history blocks (families C, E, F) ------------------------------


def _block(df: pd.DataFrame, section: str, n: int, field: str) -> "pd.Series[Any]":
    col = f"{section}_last{n}_{field}"
    if col in df.columns:
        return df[col]
    return pd.Series(np.nan, index=df.index)


def _corner_goal_share_gap(df: pd.DataFrame, section: str) -> "pd.Series[Any]":
    """Last-6 corner share minus goal share, from the subject team's perspective.

    F7 (LEAGUE_STUDY): comeback teams out-shoot even ordinary winners, so a team
    winning the corner count by more than the scoreline is the "deserved dominance
    not yet converted" candidate. Corners are the pressure proxy this corpus has.
    """
    subj_c: pd.Series[Any] = pd.Series(0.0, index=df.index)
    tot_c = pd.Series(0.0, index=df.index)
    subj_g = pd.Series(0.0, index=df.index)
    tot_g = pd.Series(0.0, index=df.index)
    for n in range(1, MATCHES_PER_SECTION + 1):
        is_home = _block(df, section, n, "is_home").astype("boolean")
        ch = _block(df, section, n, "corners_ft_home")
        ca = _block(df, section, n, "corners_ft_away")
        gh = _block(df, section, n, "ft_home_goals")
        ga = _block(df, section, n, "ft_away_goals")
        ok = is_home.notna() & ch.notna() & ca.notna() & gh.notna() & ga.notna()
        mine_c = np.where(is_home.fillna(False), ch, ca)
        mine_g = np.where(is_home.fillna(False), gh, ga)
        subj_c += np.where(ok, mine_c, 0.0)
        tot_c += np.where(ok, ch.fillna(0) + ca.fillna(0), 0.0)
        subj_g += np.where(ok, mine_g, 0.0)
        tot_g += np.where(ok, gh.fillna(0) + ga.fillna(0), 0.0)
    corner_share = np.where(tot_c > 0, subj_c / tot_c, np.nan)
    goal_share = np.where(tot_g > 0, subj_g / tot_g, np.nan)
    gap: pd.Series[Any] = pd.Series(corner_share - goal_share, index=df.index)
    return gap


def _congestion(df: pd.DataFrame, section: str) -> tuple["pd.Series[Any]", "pd.Series[Any]"]:
    """Competitive matches in the last 14 days, and days since the last match.

    Genuinely nowgoal-exclusive: the history blocks carry cup and European
    fixtures that football-data.co.uk omits entirely, so this is a different
    variable from F10's (dead) league-only rest-days.
    """
    played = pd.Series(0, index=df.index, dtype="int64")
    most_recent = pd.Series(pd.NaT, index=df.index, dtype="datetime64[ns]")
    for n in range(1, MATCHES_PER_SECTION + 1):
        when = pd.to_datetime(_block(df, section, n, "date"), errors="coerce")
        league = _block(df, section, n, "league").astype("string").str.lower()
        gap_days = (df["date"] - when).dt.total_seconds() / 86400.0
        competitive = ~league.str.contains(FRIENDLY_MARKER, na=False)
        recent = competitive & gap_days.between(0, CONGESTION_DAYS)
        played += recent.fillna(False).astype("int64")
        most_recent = most_recent.where(most_recent.notna() | when.isna(), when)
    days_since = (df["date"] - most_recent).dt.total_seconds() / 86400.0
    return played.astype(float), days_since


def _h2h_ht_goals_avg(df: pd.DataFrame) -> "pd.Series[Any]":
    """Mean total half-time goals in past meetings of this fixture.

    The exclusion filter needs the fixture's *first-half* goal environment, not just
    its full-time one: a fixture that reliably reaches the break goalless cannot
    build the half-time lead a comeback has to reverse.
    """
    total = pd.Series(0.0, index=df.index)
    seen = pd.Series(0.0, index=df.index)
    for n in range(1, MATCHES_PER_SECTION + 1):
        h = _block(df, "h2h", n, "ht_home_goals")
        a = _block(df, "h2h", n, "ht_away_goals")
        ok = h.notna() & a.notna()
        total += (h.fillna(0) + a.fillna(0)).where(ok, 0.0)
        seen += ok.astype(float)
    avg: pd.Series[Any] = pd.Series(np.where(seen > 0, total / seen, np.nan), index=df.index)
    return avg


def _h2h_ht_nondraw_rate(df: pd.DataFrame) -> "pd.Series[Any]":
    """Share of past meetings in this fixture that were non-draws at half-time.

    Factor 1 is "does anyone lead at HT" — a fixture that historically produces
    separated half-times is the natural fixture-level predictor of it.
    """
    hits = pd.Series(0.0, index=df.index)
    seen = pd.Series(0.0, index=df.index)
    for n in range(1, MATCHES_PER_SECTION + 1):
        h = _block(df, "h2h", n, "ht_home_goals")
        a = _block(df, "h2h", n, "ht_away_goals")
        ok = h.notna() & a.notna()
        hits += (ok & (h != a)).astype(float)
        seen += ok.astype(float)
    return pd.Series(np.where(seen > 0, hits / seen, np.nan), index=df.index)


# --- Market controls and the imported completion stage's inputs ---------------


def _vig_free(df: pd.DataFrame) -> dict[str, Any]:
    """Proportionally de-vigged 1X2 probabilities from the opening price."""
    inv_h = 1.0 / df["home_win_initial_odds"]
    inv_d = 1.0 / df["draw_initial_odds"]
    inv_a = 1.0 / df["away_win_initial_odds"]
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


def _closing_odds(df: pd.DataFrame) -> dict[str, Any]:
    """Raw decimal closing odds per side, for the imported F11 completion curve.

    F11's coefficients are defined on the trailing team's *closing* price. The
    detail page's "live" column is cleared for this use in PREREGISTRATION.md S9
    (it behaves as a pre-kickoff drift, not a settled price); the opening price is
    the fallback where it is missing.
    """
    return {
        f"close_odds_{side}": df[f"odds1x2_live_{side}"].fillna(
            df[f"odds1x2_init_{side}"].fillna(df[f"{side}_win_initial_odds"])
        )
        for side in ("home", "away")
    }


# --- Assembly -----------------------------------------------------------------


def build_features(df: pd.DataFrame | None = None) -> pd.DataFrame:
    """Assemble the full preregistered feature matrix, one row per match."""
    df = load_enriched() if df is None else df.copy()

    built: dict[str, Any] = {}
    built.update(_vig_free(df))
    built.update(_closing_odds(df))
    built.update(_attach_rolling(df))

    for side in ("home", "away"):
        built[f"{side}_corner_goal_share_gap"] = _corner_goal_share_gap(df, side)
        played, days_since = _congestion(df, side)
        built[f"{side}_matches_14d"] = played
        built[f"{side}_days_since_last"] = days_since

    built["strength_gap"] = df["strength_home"] - df["strength_away"]
    guess_gap = (df["guess_home_pct"] - df["guess_away_pct"]) / 100.0
    built["guess_minus_market"] = guess_gap - built["mkt_p_home"] + built["mkt_p_away"]

    built["venue_ppg_gap"] = df["home_recent_venue_ppg"] - df["away_recent_venue_ppg"]
    built["h2h_ht_nondraw_rate"] = _h2h_ht_nondraw_rate(df)

    built["combined_recent_gf"] = df["home_recent_gf_avg"] + df["away_recent_gf_avg"]

    # Exclusion-filter additions (G2 / G3).
    built["h2h_ht_goals_avg"] = _h2h_ht_goals_avg(df)
    for side in ("home", "away"):
        built[f"odds_drift_{side}"] = df[f"implied_live_{side}"] - df[f"implied_init_{side}"]

    engineered = pd.DataFrame(built, index=df.index)
    wanted = _dedupe(IDENTITY + TARGETS + CONTROLS + all_feature_names() + filter_feature_names())
    keep_raw = [c for c in wanted if c not in engineered.columns]
    full = pd.concat([df[keep_raw], engineered], axis=1)
    return full[wanted].copy()


def all_feature_names() -> list[str]:
    return [name for names in FAMILIES.values() for name in names]


def _dedupe(names: list[str]) -> list[str]:
    """Order-preserving dedupe — the two studies' family lists overlap."""
    return list(dict.fromkeys(names))


def in_burn_in(df: pd.DataFrame) -> "pd.Series[Any]":
    """Rounds 1..BURN_IN_ROUNDS, where rolling form does not yet exist.

    Dropped identically for every model so the comparison stays fair.
    """
    return df["round"] <= BURN_IN_ROUNDS


# --- Verification -------------------------------------------------------------


def self_check(sample: int = 100, seed: int = 0) -> int:
    """Recompute rolling features the slow way and prove the as-of-round cutoff.

    For each sampled match, rebuild each team's last-6 form from scratch using
    *only* that team's matches in strictly earlier rounds, and compare.
    """
    raw = load_enriched()
    feats = build_features(raw)
    merged = feats.merge(
        raw[["match_id", "home_team_id", "away_team_id"]], on="match_id", how="left"
    )
    long = _team_match_long(raw)

    rng = np.random.default_rng(seed)
    candidates = merged[~in_burn_in(merged)]
    chosen = rng.choice(len(candidates), size=min(sample, len(candidates)), replace=False)
    picks = candidates.iloc[chosen]

    failures = 0
    checks = 0
    for _, row in picks.iterrows():
        for side in ("home", "away"):
            history = long[
                (long["league_name"] == row["league_name"])
                & (long["season"] == row["season"])
                & (long["team_id"] == row[f"{side}_team_id"])
                & (long["round"] < row["round"])
            ].sort_values("round")
            window = history.tail(FORM_WINDOW)
            if len(window) < BURN_IN_ROUNDS:
                continue
            for src, dst in ROLLING_SPECS:
                checks += 1
                expected = float(window[src].mean())
                actual = row[f"{side}_{dst}"]
                if pd.isna(actual) or abs(float(actual) - expected) > 1e-9:
                    failures += 1
                    print(
                        f"  MISMATCH match {row['match_id']} {side} {dst}: "
                        f"vectorised={actual} slow-recompute={expected}"
                    )

    print(f"as-of-round self-check: {checks} comparisons, {failures} mismatches")
    if failures == 0:
        print("  PASS — no rolling feature uses data from the target round or later")
    return failures


def summarize(df: pd.DataFrame) -> None:
    print("=" * 78)
    print("FEATURE MATRIX")
    print("=" * 78)
    usable = df[~in_burn_in(df)]
    print(f"  rows: {len(df)} total, {len(usable)} after {BURN_IN_ROUNDS}-round burn-in")
    for split in ("dev", "holdout"):
        sub = usable[usable["split"] == split]
        cb = int(sub["is_comeback"].sum())
        nondraw = int((sub["ht_home_goals"] != sub["ht_away_goals"]).sum())
        print(
            f"    {split:8s} n={len(sub):5d}  comebacks={cb:4d} ({cb / len(sub):.2%})  "
            f"HT non-draws={nondraw:4d} ({nondraw / len(sub):.1%})"
        )
    print("\n  fill rate by family (post burn-in):")
    for family, names in FAMILIES.items():
        fills = [f"{name}={usable[name].notna().mean():.0%}" for name in names]
        print(f"    {family:16s} {'  '.join(fills)}")
    print("\n  exclusion-filter families (post burn-in):")
    for family, names in FILTER_FAMILIES.items():
        worst = min(usable[name].notna().mean() for name in names)
        print(f"    {family:18s} {len(names):2d} features, lowest fill={worst:.0%}")

    print("\n  controls:")
    for name in CONTROLS:
        print(f"    {name:24s} fill={usable[name].notna().mean():.0%}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-check", action="store_true", help="prove the as-of-round invariant")
    parser.add_argument("--sample", type=int, default=100, help="matches to verify in --self-check")
    args = parser.parse_args()

    if args.self_check:
        raise SystemExit(1 if self_check(args.sample) else 0)
    summarize(build_features())


if __name__ == "__main__":
    main()
