"""`analysis/schedule/whole_corpus/per_league/odds_coverage.py`: markets, coverage, causes."""

import pandas as pd
import pytest

from analysis.schedule.whole_corpus.per_league import odds_coverage as runner

# (round, match in the round) -> (HT home, HT away, FT home, FT away, 1X2, O/U, AH, rescheduled)
GAPS = {
    (1, 0): (0, 1, 1, 1, False, False, False, False),  # stage start
    (3, 0): (1, 0, 2, 1, False, False, False, False),  # isolated
    (4, 0): (0, 0, 3, 0, False, False, False, False),  # awarded pattern
    (4, 1): (1, 0, 2, 0, True, False, False, False),  # 1X2 only
    (5, 0): (0, 1, 2, 1, False, False, False, True),  # rescheduled
    (7, 0): (0, 0, 1, 0, False, False, False, False),  # stage end
}


@pytest.fixture
def season() -> pd.DataFrame:
    """One league-season of 8 rounds with 3 matches each; six matches lack some markets."""
    rows = []
    for round_number in range(1, 9):
        for match in range(3):
            ht_h, ht_a, ft_h, ft_a, x12, ou, ah, moved = GAPS.get(
                (round_number, match), (1, 1, 2, 1, True, True, True, False)
            )
            kickoff = pd.Timestamp("2024-08-03 18:00+02:00") + pd.Timedelta(
                days=7 * (round_number - 1)
            )
            rows.append(
                {
                    "s1_league_id": 1,
                    "s1_league_name": "a_league",
                    "s1_season": "2024-2025",
                    "season_cohort": 2024,
                    "s1_stage": "",
                    "s1_round": round_number,
                    "match_id": f"m{round_number}{match}",
                    "s1_date": kickoff.isoformat(sep=" ", timespec="minutes"),
                    "s1_home_team_name": f"home {match}",
                    "s1_away_team_name": f"away {match}",
                    "s1_ht_home_goals": ht_h,
                    "s1_ht_away_goals": ht_a,
                    "s1_ft_home_goals": ft_h,
                    "s1_ft_away_goals": ft_a,
                    "s2_has_odds": x12,
                    "s2_has_ou_odds": ou,
                    "s2_has_ah_odds": ah,
                    "s3_is_rescheduled": moved,
                }
            )

    return runner.with_markets(pd.DataFrame(rows))


def test_with_markets_marks_all_or_none(season: pd.DataFrame) -> None:
    assert int(season["all_three"].sum()) == 24 - len(GAPS)
    assert int(season["no_odds"].sum()) == len(GAPS) - 1  # the 1X2-only match has some odds


def test_patterns_name_each_combination(season: pd.DataFrame) -> None:
    table = runner.patterns(season).set_index("markets")["matches"]
    assert table.to_dict() == {"1X2 O/U AH": 18, "none": 5, "1X2": 1}


def test_coverage_counts_each_group(season: pd.DataFrame) -> None:
    table = runner.coverage(season, ["s1_league_name"])
    assert table[["matches", "all_three"]].iloc[0].tolist() == [24, 18]
    assert table["share"].iloc[0] == pytest.approx(18 / 24)


def test_three_nil_is_a_three_goal_shutout() -> None:
    scores = pd.DataFrame({"s1_ft_home_goals": [3, 0, 3, 4], "s1_ft_away_goals": [0, 3, 1, 0]})
    assert runner.three_nil(scores).tolist() == [True, True, False, False]


def test_each_gap_gets_the_first_cause_that_fits(season: pd.DataFrame) -> None:
    table = runner.gaps(season).set_index("match_id")["cause"]

    assert table.to_dict() == {
        "m10": "stage start",
        "m30": "isolated",
        "m40": "awarded pattern",
        "m41": "1X2 only",
        "m50": "rescheduled",
        "m70": "stage end",
    }


def test_award_shapes_split_the_three_nil_results_by_half_time() -> None:
    frame = runner.with_markets(
        pd.DataFrame(
            {
                "s1_ht_home_goals": [0, 0, 3, 1, 0],
                "s1_ht_away_goals": [0, 0, 0, 0, 0],
                "s1_ft_home_goals": [3, 0, 3, 3, 2],
                "s1_ft_away_goals": [0, 3, 0, 0, 0],
                "s2_has_odds": [False, True, True, True, True],
                "s2_has_ou_odds": [False, True, True, True, True],
                "s2_has_ah_odds": [False, True, True, True, True],
            }
        )
    )

    table = runner.award_shapes(frame).set_index("half-time score").to_dict("index")
    columns = ("matches", "all three markets", "no odds")

    assert table["0-0"] == dict(zip(columns, (2, 1, 1), strict=True))
    assert table["the full-time score"] == dict(zip(columns, (1, 1, 0), strict=True))
    assert table["other"] == dict(zip(columns, (1, 1, 0), strict=True))
    assert table["any"] == dict(zip(columns, (4, 3, 1), strict=True))
