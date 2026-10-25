"""Opening-odds coverage per league, and the likely cause of each gap.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_LEAGUE/ODDS_COVERAGE.md`. Prints which of the
three opening markets each match has, the coverage of each league, league-season and season
cohort, every match without all three markets with its likely cause, and how often the score
of an awarded match comes with odds. Coverage reads no outcome. The cause and the score
pattern read the score, only to find awarded matches: a data-quality check.

Run: `uv run python -m analysis.schedule.whole_corpus.per_league.odds_coverage`
"""

import numpy as np
import pandas as pd

from analysis import corpus, report

# Stage 2's flags: every cell of the market is present (S2.11-13).
MARKETS = {"1X2": "s2_has_odds", "O/U": "s2_has_ou_odds", "AH": "s2_has_ah_odds"}
EDGE_ROUNDS = 2  # rounds 1-2 open a stage; its last round and the 2 before it close it
STAGE_KEYS = ["s1_league_id", "s1_season", "s1_stage"]


def with_markets(matches_df: pd.DataFrame) -> pd.DataFrame:
    """The matches with `all_three` (every market present) and `no_odds` (none present)."""

    market_flags_df = matches_df[list(MARKETS.values())].astype(bool)

    return matches_df.assign(
        all_three=market_flags_df.all(axis=1), no_odds=~market_flags_df.any(axis=1)
    )


def patterns(matches_df: pd.DataFrame) -> pd.DataFrame:
    """How many matches have each combination of markets, e.g. "1X2 O/U AH" or "none"."""

    names = pd.Series("", index=matches_df.index)
    for market, flag in MARKETS.items():
        names = names + np.where(matches_df[flag].astype(bool), f" {market}", "")
    names = names.str.strip().replace("", "none")

    return names.value_counts().rename_axis("markets").reset_index(name="matches")


def coverage(matches_df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Per group: its matches, those with all three markets, and their share."""

    coverage_df = matches_df.groupby(keys).agg(
        matches=("all_three", "size"), all_three=("all_three", "sum")
    )
    coverage_df["share"] = coverage_df["all_three"] / coverage_df["matches"]

    return coverage_df.reset_index()


def three_nil(matches_df: pd.DataFrame) -> "pd.Series[bool]":
    """The matches that end 3-0 or 0-3: the score of an awarded match."""

    home, away = matches_df["s1_ft_home_goals"], matches_df["s1_ft_away_goals"]

    return ((home == 3) & (away == 0)) | ((home == 0) & (away == 3))


def half_time(matches_df: pd.DataFrame) -> tuple["pd.Series[bool]", "pd.Series[bool]"]:
    """Two masks: 0-0 at half-time, and the full-time score already at half-time."""

    ht_home, ht_away = matches_df["s1_ht_home_goals"], matches_df["s1_ht_away_goals"]
    level = (ht_home == 0) & (ht_away == 0)
    final = (ht_home == matches_df["s1_ft_home_goals"]) & (
        ht_away == matches_df["s1_ft_away_goals"]
    )

    return level, final


def causes(matches_df: pd.DataFrame) -> "pd.Series[str]":
    """The likely cause of a match that lacks a market, the first that fits: the awarded pattern
    (no market, 3-0 or 0-3, and 0-0 or that score at half-time), the 1X2 there but the O/U or
    the AH missing, a rescheduled kickoff (S3.10), a stage's first or last rounds, else isolated.
    """

    level, final = half_time(matches_df)
    last = matches_df.groupby(STAGE_KEYS)["s1_round"].transform("max")

    conditions = [
        matches_df["no_odds"] & three_nil(matches_df) & (level | final),
        matches_df["s2_has_odds"].astype(bool),
        matches_df["s3_is_rescheduled"].astype(bool),
        matches_df["s1_round"] <= EDGE_ROUNDS,
        last - matches_df["s1_round"] <= EDGE_ROUNDS,
    ]
    choices = ["awarded pattern", "1X2 only", "rescheduled", "stage start", "stage end"]

    return pd.Series(np.select(conditions, choices, "isolated"), index=matches_df.index)


def gaps(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Every match without all three markets, with its markets and its likely cause."""

    gaps_df = matches_df.assign(cause=causes(matches_df))[~matches_df["all_three"]]
    columns = [
        "s1_league_name",
        "s1_season",
        "s1_round",
        "match_id",
        "s1_date",
        "s1_home_team_name",
        "s1_away_team_name",
        "s1_ht_home_goals",
        "s1_ht_away_goals",
        "s1_ft_home_goals",
        "s1_ft_away_goals",
        *MARKETS.values(),
        "cause",
    ]

    return gaps_df[columns].sort_values(["s1_league_name", "s1_season", "s1_date"])


def award_shapes(matches_df: pd.DataFrame) -> pd.DataFrame:
    """The matches that end 3-0 or 0-3, by their half-time score, and how many lack odds."""

    level, final = half_time(matches_df)
    ends = three_nil(matches_df)

    shapes = {
        "0-0": ends & level,
        "the full-time score": ends & final,
        "other": ends & ~level & ~final,
        "any": ends,
    }

    return pd.DataFrame(
        [
            {
                "half-time score": name,
                "matches": int(mask.sum()),
                "all three markets": int((mask & matches_df["all_three"]).sum()),
                "no odds": int((mask & matches_df["no_odds"]).sum()),
            }
            for name, mask in shapes.items()
        ]
    )


def main() -> None:
    matches_df = with_markets(corpus.load())
    print(corpus.corpus_line(matches_df))
    print(
        f"all three markets: {int(matches_df['all_three'].sum()):,} of {len(matches_df):,}; "
        f"no odds: {int(matches_df['no_odds'].sum()):,}"
    )

    report.show("Markets of each match", patterns(matches_df))
    report.show(
        "By market",
        pd.DataFrame(
            [
                {"market": market, "matches with it": int(matches_df[flag].sum())}
                for market, flag in MARKETS.items()
            ]
        ),
    )

    league_coverage_df = coverage(matches_df, ["s1_league_name"])
    season_coverage_df = coverage(matches_df, ["s1_league_name", "s1_season"])
    print(
        f"\nleagues at 100%: {int((league_coverage_df['share'] == 1).sum())} of "
        f"{len(league_coverage_df)}; "
        f"league-seasons at 100%: {int((season_coverage_df['share'] == 1).sum())} of "
        f"{len(season_coverage_df)}"
    )

    report.show("Season cohorts", coverage(matches_df, ["season_cohort"]))
    report.show("Leagues below 100%", league_coverage_df[league_coverage_df["share"] < 1])
    report.show("League-seasons below 100%", season_coverage_df[season_coverage_df["share"] < 1])
    report.show("Every match without all three markets", gaps(matches_df))
    report.show("Matches that end 3-0 or 0-3, by half-time score", award_shapes(matches_df))
    report.show("Every league", league_coverage_df)


if __name__ == "__main__":
    main()
