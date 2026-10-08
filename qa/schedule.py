"""Checks for a staged schedule file (`data/finished/1_raw/<league>_<season>_schedule.csv`).

The stage-1 file holds page values only, so these checks test what the page gave us: the
scores, the odds (`qa/odds.py`), and the shape of the season. Dataset-agnostic checks come
from `qa/universal.py`; the page's final table against our rebuilt standings is
`qa/final_table.py`.

The season-shape checks hold for a league played as a k-fold round robin, which every kept
"League" stage is: each round has floor(teams / 2) matches, and every pair of teams meets
equally often. A failure is a finding about the data (`qa/CLAUDE.md` §2): a match the scrape
missed, a duplicate, or a real event such as a team withdrawn mid-season.
"""

from collections import Counter
from datetime import timedelta
from itertools import combinations

import pandas as pd

from domain.clock import parse_instant
from domain.schedule import season_start_year
from qa.odds import OddsColumns, check_all
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
# Text even when every value looks like a number, or is empty.
_TEXT_COLUMNS = ("match_id", "s1_season", "s1_stage", "season", "stage")


def read_staged(path: str, columns: list[str] | None = None) -> pd.DataFrame:
    """A staged file with its text columns kept as text: an empty stage stays ""."""
    head = pd.read_csv(path, nrows=0).columns
    text = [c for c in _TEXT_COLUMNS if c in head and (columns is None or c in columns)]
    frame = pd.read_csv(path, usecols=columns, dtype=dict.fromkeys(text, str))
    return frame.fillna(dict.fromkeys(text, ""))


def validate(r: Report, df: pd.DataFrame) -> None:
    _check_scores(r, df)
    check_all(r, df, STAGED_ODDS)
    _check_kickoff_years(r, df)
    _check_no_team_twice_in_a_day(r, df)
    for stage, group in df.groupby("s1_stage", sort=False):
        label = f"stage {stage!r}: " if stage else ""
        _check_round_sizes(r, group, label)
        _check_pairs_meet_equally(r, group, label)


def _check_scores(r: Report, df: pd.DataFrame) -> None:
    """Half-time goals never exceed full-time goals, and no score is negative."""
    impossible = df[
        (df["s1_ht_home_goals"] > df["s1_ft_home_goals"])
        | (df["s1_ht_away_goals"] > df["s1_ft_away_goals"])
        | (df[["s1_ht_home_goals", "s1_ht_away_goals"]] < 0).any(axis=1)
    ]
    r.check(impossible.empty, f"{len(impossible)} rows with impossible HT/FT scores")


def _check_kickoff_years(r: Report, df: pd.DataFrame) -> None:
    """Kickoffs fall in the season's start year or the year after (a wrong clock would not)."""
    start = season_start_year(str(df["s1_season"].iloc[0])) if len(df) else None
    if start is None:
        return
    years = df["s1_date"].map(lambda text: parse_instant(text).year)
    outside = df[(years < start) | (years > start + 1)]
    r.check(outside.empty, f"{len(outside)} kickoffs outside {start}-{start + 1}")


def _check_no_team_twice_in_a_day(r: Report, df: pd.DataFrame) -> None:
    """No team has two matches less than `MIN_GAP_BETWEEN_MATCHES` apart."""
    kick = df["s1_date"].map(parse_instant)
    long = pd.concat(
        [
            pd.DataFrame({"team": df["s1_home_team_id"], "kickoff": kick}),
            pd.DataFrame({"team": df["s1_away_team_id"], "kickoff": kick}),
        ]
    )
    clashes = 0
    for _, group in long.groupby("team"):
        gaps = group["kickoff"].sort_values().diff().dropna()
        clashes += int((gaps < MIN_GAP_BETWEEN_MATCHES).sum())
    r.check(clashes == 0, f"{clashes} pairs of matches of one team less than 24 h apart")


def _check_round_sizes(r: Report, group: pd.DataFrame, label: str) -> None:
    """Every round holds floor(teams / 2) matches: none missing, none doubled."""
    teams = set(group["s1_home_team_id"]) | set(group["s1_away_team_id"])
    expected = len(teams) // 2
    sizes = group.groupby("s1_round").size()
    rounds = zip(sizes.index.tolist(), sizes.tolist(), strict=True)
    wrong = {int(rnd): int(n) for rnd, n in rounds if n != expected}
    r.check(
        not wrong, f"{label}{len(wrong)} rounds without {expected} matches (round: count) {wrong}"
    )


def _check_pairs_meet_equally(r: Report, group: pd.DataFrame, label: str) -> None:
    """In a k-fold round robin, every pair of teams meets the same number of times."""
    teams = sorted(set(group["s1_home_team_id"]) | set(group["s1_away_team_id"]))
    met = Counter(
        frozenset(pair)
        for pair in zip(group["s1_home_team_id"], group["s1_away_team_id"], strict=True)
    )
    counts = Counter(met[frozenset(pair)] for pair in combinations(teams, 2))
    r.check(
        len(counts) <= 1, f"{label}pairs of teams meet unequally (meetings: pairs) {dict(counts)}"
    )
