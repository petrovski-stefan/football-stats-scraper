"""`qa/schedule.py`: the season-shape and score checks on a staged schedule file."""

from datetime import datetime, timedelta
from itertools import combinations

import pandas as pd

from domain.clock import BERLIN, to_berlin
from qa.report import Report
from qa.schedule import BLANK_ROUND_MIN_MATCHES, STAGED_ODDS, validate

_START = datetime(2025, 8, 9, 15, 0, tzinfo=BERLIN)
# Plausible opening odds, the same on every match: 1X2, then O/U and AH line and prices.
_ODDS = dict(
    zip(STAGED_ODDS.cells(), [1.5, 4.0, 6.0, 2.75, 1.9, 1.95, 0.75, 1.9, 1.95], strict=True)
)


def _rounds(teams: int) -> list[list[tuple[int, int]]]:
    """A single round robin by the circle method: each team plays once per round."""

    ids = list(range(1, teams + 1))
    rounds = []
    for _ in range(teams - 1):
        rounds.append([(ids[i], ids[-1 - i]) for i in range(teams // 2)])
        ids = [ids[0], ids[-1], *ids[1:-1]]

    return rounds


def _season(teams: int = 4, legs: int = 2) -> pd.DataFrame:
    """A clean k-fold round robin: every pair meets `legs` times, one round per week."""

    rows: list[dict[str, object]] = []
    single = _rounds(teams)
    for leg in range(legs):
        for offset, matches in enumerate(single):
            number = leg * len(single) + offset
            for first_team, second_team in matches:
                home, away = (
                    (first_team, second_team) if leg % 2 == 0 else (second_team, first_team)
                )
                rows.append(
                    {
                        "match_id": str(len(rows) + 1),
                        "s1_season": "2025-2026",
                        "s1_stage": "",
                        "s1_round": number + 1,
                        "s1_date": to_berlin(_START + timedelta(days=7 * number)),
                        "s1_home_team_id": home,
                        "s1_away_team_id": away,
                        "s1_ht_home_goals": 0,
                        "s1_ht_away_goals": 0,
                        "s1_ft_home_goals": 1,
                        "s1_ft_away_goals": 0,
                        **_ODDS,
                    }
                )

    return pd.DataFrame(rows)


def test_the_test_season_is_a_real_round_robin() -> None:
    season_df = _season(teams=6, legs=2)

    pairs = combinations(range(1, 7), 2)
    met = dict.fromkeys(pairs, 0)
    for home, away in zip(season_df["s1_home_team_id"], season_df["s1_away_team_id"], strict=True):
        met[(min(home, away), max(home, away))] += 1

    assert set(met.values()) == {2}


def _issues(schedule_df: pd.DataFrame) -> list[str]:
    """The issues the schedule check finds in this table."""

    report = Report("test")
    validate(report, schedule_df)

    return report.issues


def test_a_clean_round_robin_passes() -> None:
    assert _issues(_season()) == []


def test_a_missing_match_fails_two_ways() -> None:
    issues = _issues(_season().iloc[1:])
    assert any("rounds without" in issue for issue in issues)
    assert any("meet unequally" in issue for issue in issues)


def test_a_team_twice_in_one_round_fails_even_when_round_sizes_hold() -> None:
    # Swap the round labels of two matches: every round keeps its size and every pair
    # still meets equally often, but one team now plays twice in a round.
    season_df = _season()
    first = season_df.index[season_df["s1_round"] == 1]
    second = season_df.index[season_df["s1_round"] == 2]
    season_df.loc[first[1], "s1_round"] = 2
    season_df.loc[second[0], "s1_round"] = 1

    issues = _issues(season_df)

    assert any("plays twice" in issue for issue in issues)
    assert not any("rounds without" in issue or "meet unequally" in issue for issue in issues)


def test_half_time_goals_above_full_time_fail() -> None:
    season_df = _season()
    season_df.loc[0, "s1_ht_home_goals"] = 2
    assert any("impossible HT/FT" in issue for issue in _issues(season_df))


def test_a_team_twice_in_one_day_fails() -> None:
    season_df = _season()
    first_kickoff = season_df.loc[0, "s1_date"]
    later = season_df.index[
        (season_df["s1_home_team_id"] == 1) | (season_df["s1_away_team_id"] == 1)
    ][1]
    season_df.loc[later, "s1_date"] = first_kickoff
    assert any("less than 24 h apart" in issue for issue in _issues(season_df))


def test_a_kickoff_in_the_wrong_year_fails() -> None:
    season_df = _season()
    season_df.loc[0, "s1_date"] = "2030-01-01 15:00+01:00"
    assert any("kickoffs outside" in issue for issue in _issues(season_df))


def test_the_year_check_needs_a_season_label_it_can_read() -> None:
    season_df = _season()
    season_df["s1_season"] = "Apertura"
    season_df.loc[0, "s1_date"] = "2030-01-01 15:00+01:00"
    assert not any("kickoffs outside" in issue for issue in _issues(season_df))


def _blank_rounds(issues: list[str]) -> list[str]:
    """The issues about rounds without odds on any match."""

    return [issue for issue in issues if "without odds on any match" in issue]


def test_a_round_without_any_odds_fails() -> None:
    season_df = _season()
    season_df.loc[season_df["s1_round"] == 2, STAGED_ODDS.cells()] = float("nan")
    assert _blank_rounds(_issues(season_df)) == ["1 rounds without odds on any match (rounds) [2]"]


def test_one_priced_match_saves_its_round() -> None:
    season_df = _season()
    unpriced = season_df.index[season_df["s1_round"] == 2][1:]
    season_df.loc[unpriced, STAGED_ODDS.cells()] = float("nan")
    assert _blank_rounds(_issues(season_df)) == []


def test_a_table_without_the_odds_columns_is_not_checked_for_blank_rounds() -> None:
    # `universal.check_required_columns` reports the missing columns, once.
    assert _blank_rounds(_issues(_season().drop(columns=STAGED_ODDS.cells()))) == []


def test_a_round_below_the_minimum_size_is_left_alone() -> None:
    season_df = _season(teams=2 * (BLANK_ROUND_MIN_MATCHES - 1))
    season_df.loc[:, STAGED_ODDS.cells()] = float("nan")
    assert _blank_rounds(_issues(season_df)) == []
