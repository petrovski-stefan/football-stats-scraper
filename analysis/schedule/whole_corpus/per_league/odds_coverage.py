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


def with_markets(matches: pd.DataFrame) -> pd.DataFrame:
    """The matches with `all_three` (every market present) and `no_odds` (none present)."""
    flags = matches[list(MARKETS.values())].astype(bool)
    return matches.assign(all_three=flags.all(axis=1), no_odds=~flags.any(axis=1))


def patterns(matches: pd.DataFrame) -> pd.DataFrame:
    """How many matches have each combination of markets, e.g. "1X2 O/U AH" or "none"."""
    names = pd.Series("", index=matches.index)
    for market, flag in MARKETS.items():
        names = names + np.where(matches[flag].astype(bool), f" {market}", "")
    names = names.str.strip().replace("", "none")
    return names.value_counts().rename_axis("markets").reset_index(name="matches")


def coverage(matches: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    """Per group: its matches, those with all three markets, and their share."""
    table = matches.groupby(keys).agg(matches=("all_three", "size"), all_three=("all_three", "sum"))
    table["share"] = table["all_three"] / table["matches"]
    return table.reset_index()


def three_nil(matches: pd.DataFrame) -> "pd.Series[bool]":
    """The matches that end 3-0 or 0-3: the score of an awarded match."""
    home, away = matches["s1_ft_home_goals"], matches["s1_ft_away_goals"]
    return ((home == 3) & (away == 0)) | ((home == 0) & (away == 3))


def half_time(matches: pd.DataFrame) -> tuple["pd.Series[bool]", "pd.Series[bool]"]:
    """Two masks: 0-0 at half-time, and the full-time score already at half-time."""
    ht_home, ht_away = matches["s1_ht_home_goals"], matches["s1_ht_away_goals"]
    level = (ht_home == 0) & (ht_away == 0)
    final = (ht_home == matches["s1_ft_home_goals"]) & (ht_away == matches["s1_ft_away_goals"])
    return level, final


def causes(matches: pd.DataFrame) -> "pd.Series[str]":
    """The likely cause of a match without all three markets, the first that fits.

    The awarded pattern: no market, a 3-0 or 0-3 result, and 0-0 or that result at half-time.
    Then: the 1X2 is there but O/U or AH is not; a rescheduled kickoff (S3.10); the first
    rounds or the last rounds of a stage; else isolated.
    """
    level, final = half_time(matches)
    last = matches.groupby(STAGE_KEYS)["s1_round"].transform("max")
    conditions = [
        matches["no_odds"] & three_nil(matches) & (level | final),
        matches["s2_has_odds"].astype(bool),
        matches["s3_is_rescheduled"].astype(bool),
        matches["s1_round"] <= EDGE_ROUNDS,
        last - matches["s1_round"] <= EDGE_ROUNDS,
    ]
    choices = ["awarded pattern", "1X2 only", "rescheduled", "stage start", "stage end"]
    return pd.Series(np.select(conditions, choices, "isolated"), index=matches.index)


def gaps(matches: pd.DataFrame) -> pd.DataFrame:
    """Every match without all three markets, with its markets and its likely cause."""
    out = matches.assign(cause=causes(matches))[~matches["all_three"]]
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
    return out[columns].sort_values(["s1_league_name", "s1_season", "s1_date"])


def award_shapes(matches: pd.DataFrame) -> pd.DataFrame:
    """The matches that end 3-0 or 0-3, by their half-time score, and how many lack odds."""
    level, final = half_time(matches)
    ends = three_nil(matches)
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
                "all three markets": int((mask & matches["all_three"]).sum()),
                "no odds": int((mask & matches["no_odds"]).sum()),
            }
            for name, mask in shapes.items()
        ]
    )


def main() -> None:
    matches = with_markets(corpus.load())
    print(corpus.corpus_line(matches))
    print(
        f"all three markets: {int(matches['all_three'].sum()):,} of {len(matches):,}; "
        f"no odds: {int(matches['no_odds'].sum()):,}"
    )
    report.show("Markets of each match", patterns(matches))
    report.show(
        "By market",
        pd.DataFrame(
            [
                {"market": market, "matches with it": int(matches[flag].sum())}
                for market, flag in MARKETS.items()
            ]
        ),
    )
    leagues = coverage(matches, ["s1_league_name"])
    seasons = coverage(matches, ["s1_league_name", "s1_season"])
    print(
        f"\nleagues at 100%: {int((leagues['share'] == 1).sum())} of {len(leagues)}; "
        f"league-seasons at 100%: {int((seasons['share'] == 1).sum())} of {len(seasons)}"
    )
    report.show("Season cohorts", coverage(matches, ["season_cohort"]))
    report.show("Leagues below 100%", leagues[leagues["share"] < 1])
    report.show("League-seasons below 100%", seasons[seasons["share"] < 1])
    report.show("Every match without all three markets", gaps(matches))
    report.show("Matches that end 3-0 or 0-3, by half-time score", award_shapes(matches))
    report.show("Every league", leagues)


if __name__ == "__main__":
    main()
