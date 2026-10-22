"""Checks for a staged schedule file
(`data/finished/1_raw/<country>_<league>_<season>_schedule.csv`).

The stage-1 file holds page values only, so these checks test what the page gave us: the
scores, the odds (`qa/odds.py`: plausible prices and lines, whole markets, coverage, and no
round without odds), and the shape of the season. Dataset-agnostic checks come from
`qa/universal.py`; the page's final table against our rebuilt standings is
`qa/final_table.py`; the derived stage files against this one, `qa/stages.py`.

The season-shape checks hold for a league played as a k-fold round robin, which every kept
"League" stage is: each round has floor(teams / 2) matches, no team plays twice in one
round, and every pair of teams meets equally often. A failure is a finding about the data
(`qa/CLAUDE.md` §2): a match the scrape missed, a duplicate, a page whose rounds are only
labels, or a real event such as a team withdrawn mid-season.
"""

from collections import Counter
from datetime import timedelta
from itertools import combinations

import pandas as pd

from domain.clock import parse_instant
from domain.schedule import season_start_year
from qa.odds import OddsColumns, check_all, check_coverage, check_whole_markets
from qa.report import Report

# Where the stage-1 schedule keeps its three markets.
STAGED_ODDS = OddsColumns(
    home="s1_odds_1x2_open_home",
    draw="s1_odds_1x2_open_draw",
    away="s1_odds_1x2_open_away",
    ou_line="s1_odds_ou_open_line",
    over="s1_odds_ou_open_over",
    under="s1_odds_ou_open_under",
    ah_line="s1_odds_ah_open_line",
    ah_home="s1_odds_ah_open_home",
    ah_away="s1_odds_ah_open_away",
)
# No team plays two league matches this close together.
MIN_GAP_BETWEEN_MATCHES = timedelta(hours=24)
# A round of at least this many matches must have odds on one of them. One unpriced match
# is the bookmaker's choice; a whole round without odds is a page that did not show them
# when it was read (England League 2 2024-25, rounds 21 and 28, found 2026-10-10).
BLANK_ROUND_MIN_MATCHES = 2
# Text even when every value looks like a number, or is empty.
_TEXT_COLUMNS = ("match_id", "s1_season", "s1_stage", "season", "stage")


def read_staged(path: str, columns: list[str] | None = None) -> pd.DataFrame:
    """A staged file with its text columns kept as text: an empty stage stays ""."""
    head = pd.read_csv(path, nrows=0).columns
    text = [c for c in _TEXT_COLUMNS if c in head and (columns is None or c in columns)]
    staged_df = pd.read_csv(path, usecols=columns, dtype=dict.fromkeys(text, str))
    return staged_df.fillna(dict.fromkeys(text, ""))


def validate(report: Report, schedule_df: pd.DataFrame) -> None:
    _check_scores(report, schedule_df)
    check_all(report, schedule_df, STAGED_ODDS)
    check_whole_markets(report, schedule_df, STAGED_ODDS)
    check_coverage(report, schedule_df, STAGED_ODDS)
    _check_kickoff_years(report, schedule_df)
    _check_no_team_twice_in_a_day(report, schedule_df)

    for stage, league_stage_df in schedule_df.groupby("s1_stage", sort=False):
        label = f"stage {stage!r}: " if stage else ""
        _check_round_sizes(report, league_stage_df, label)
        _check_team_once_per_round(report, league_stage_df, label)
        _check_pairs_meet_equally(report, league_stage_df, label)
        _check_rounds_have_odds(report, league_stage_df, label)


def _check_scores(report: Report, schedule_df: pd.DataFrame) -> None:
    """Half-time goals never exceed full-time goals, and no score is negative."""
    impossible_df = schedule_df[
        (schedule_df["s1_ht_home_goals"] > schedule_df["s1_ft_home_goals"])
        | (schedule_df["s1_ht_away_goals"] > schedule_df["s1_ft_away_goals"])
        | (schedule_df[["s1_ht_home_goals", "s1_ht_away_goals"]] < 0).any(axis=1)
    ]
    report.check(impossible_df.empty, f"{len(impossible_df)} rows with impossible HT/FT scores")


def _check_kickoff_years(report: Report, schedule_df: pd.DataFrame) -> None:
    """Kickoffs fall in the season's start year or the year after (a wrong clock would not)."""
    start = season_start_year(str(schedule_df["s1_season"].iloc[0])) if len(schedule_df) else None
    if start is None:
        return

    years = schedule_df["s1_date"].map(lambda text: parse_instant(text).year)
    outside_df = schedule_df[(years < start) | (years > start + 1)]
    report.check(outside_df.empty, f"{len(outside_df)} kickoffs outside {start}-{start + 1}")


def _check_no_team_twice_in_a_day(report: Report, schedule_df: pd.DataFrame) -> None:
    """No team has two matches less than `MIN_GAP_BETWEEN_MATCHES` apart."""
    kick = schedule_df["s1_date"].map(parse_instant)
    kickoffs_df = pd.concat(
        [
            pd.DataFrame({"team": schedule_df["s1_home_team_id"], "kickoff": kick}),
            pd.DataFrame({"team": schedule_df["s1_away_team_id"], "kickoff": kick}),
        ]
    )

    clashes = 0
    for _, team_kickoffs_df in kickoffs_df.groupby("team"):
        gaps = team_kickoffs_df["kickoff"].sort_values().diff().dropna()
        clashes += int((gaps < MIN_GAP_BETWEEN_MATCHES).sum())

    report.check(clashes == 0, f"{clashes} pairs of matches of one team less than 24 h apart")


def _check_round_sizes(report: Report, league_stage_df: pd.DataFrame, label: str) -> None:
    """Every round holds floor(teams / 2) matches: none missing, none doubled."""
    teams = set(league_stage_df["s1_home_team_id"]) | set(league_stage_df["s1_away_team_id"])
    expected = len(teams) // 2
    sizes = league_stage_df.groupby("s1_round").size()
    rounds = zip(sizes.index.tolist(), sizes.tolist(), strict=True)
    wrong = {int(rnd): int(n) for rnd, n in rounds if n != expected}

    report.check(
        not wrong, f"{label}{len(wrong)} rounds without {expected} matches (round: count) {wrong}"
    )


def _check_team_once_per_round(report: Report, league_stage_df: pd.DataFrame, label: str) -> None:
    """No team plays twice in one round. A page round that holds a team twice is a label, not
    a round of the round robin, even when its size is right (found 2026-10-08)."""
    slots_df = pd.concat(
        [
            pd.DataFrame(
                {"round": league_stage_df["s1_round"], "team": league_stage_df["s1_home_team_id"]}
            ),
            pd.DataFrame(
                {"round": league_stage_df["s1_round"], "team": league_stage_df["s1_away_team_id"]}
            ),
        ]
    )

    rounds = sorted({int(rnd) for rnd in slots_df.loc[slots_df.duplicated(), "round"]})
    report.check(
        not rounds, f"{label}{len(rounds)} rounds where a team plays twice (rounds) {rounds}"
    )


def _check_pairs_meet_equally(report: Report, league_stage_df: pd.DataFrame, label: str) -> None:
    """In a k-fold round robin, every pair of teams meets the same number of times."""
    teams = sorted(
        set(league_stage_df["s1_home_team_id"]) | set(league_stage_df["s1_away_team_id"])
    )
    met = Counter(
        frozenset(pair)
        for pair in zip(
            league_stage_df["s1_home_team_id"], league_stage_df["s1_away_team_id"], strict=True
        )
    )

    counts = Counter(met[frozenset(pair)] for pair in combinations(teams, 2))
    report.check(
        len(counts) <= 1, f"{label}pairs of teams meet unequally (meetings: pairs) {dict(counts)}"
    )


def _check_rounds_have_odds(report: Report, league_stage_df: pd.DataFrame, label: str) -> None:
    """No round of `BLANK_ROUND_MIN_MATCHES` or more matches lacks odds on every match.
    A table without the odds columns is skipped: `universal.check_required_columns` reports
    them once."""
    cells = STAGED_ODDS.cells()
    if not set(cells) <= set(league_stage_df.columns):
        return

    by_round = league_stage_df[cells].notna().any(axis=1).groupby(league_stage_df["s1_round"])
    sizes, priced = by_round.size(), by_round.any()
    rounds = zip(sizes.index.tolist(), sizes.tolist(), priced.tolist(), strict=True)
    blank = [int(rnd) for rnd, n, odds in rounds if n >= BLANK_ROUND_MIN_MATCHES and not odds]

    report.check(
        not blank, f"{label}{len(blank)} rounds without odds on any match (rounds) {blank}"
    )
