"""`analysis/schedule/whole_corpus/all/round_fields.py`: the counts, the averages, the line."""

import numpy as np
import pandas as pd
import pytest

from analysis.schedule.whole_corpus.all import round_fields as runner


@pytest.fixture
def matches() -> pd.DataFrame:
    """Four matches of one round in kickoff order: none, one, two and three finished
    round-mates before each. The third of them is a 4-3 comeback without an opening line."""
    frame = pd.DataFrame(
        {
            "s3_round_pre_finished": [0, 1, 2, 3],
            "s3_round_pre_comebacks": [0, 0, 0, 1],
            "s3_round_pre_seven_plus": [0, 0, 0, 1],
            "s3_round_pre_rare_events": [0, 0, 0, 1],
            "s3_round_pre_btts": [0, 1, 2, 3],
            "s3_round_pre_avg_goals": [np.nan, 2.0, 2.5, 2.5],
            "s3_round_pre_avg_ou_line": [np.nan, 2.5, 2.5, 2.5],
            "s1_odds_ou_open_line": [2.5, 2.5, np.nan, 3.0],
            "s2_total_goals": [2, 3, 7, 4],
        }
    )

    return frame


def test_count_table_gives_the_share_at_each_level(matches: pd.DataFrame) -> None:
    table = runner.count_table(matches).set_index("field")
    finished = table.loc["S3.14 finished"]
    assert float(finished["share 0"]) == pytest.approx(1 / 4)
    assert float(finished["share 2+"]) == pytest.approx(2 / 4)
    assert (float(finished["mean"]), int(finished["max"])) == (1.5, 3)
    assert float(table.at["S3.17 rare events", "share 1+"]) == pytest.approx(1 / 4)


def test_average_table_reads_the_rows_with_a_value(matches: pd.DataFrame) -> None:
    table = runner.average_table(matches).set_index("field")
    assert int(table.at["S3.19 average goals", "with a value"]) == 3
    assert float(table.at["S3.19 average goals", "share with a value"]) == pytest.approx(3 / 4)
    assert float(table.at["S3.19 average goals", "mean"]) == pytest.approx(7 / 3)
    assert float(table.at["S3.19 - S3.20", "median"]) == pytest.approx(0.0)
    assert float(table.at["S3.19 - S3.20", "mean"]) == pytest.approx(-0.5 / 3)


def test_finished_without_line_counts_empty_averages_after_a_finished_match(
    matches: pd.DataFrame,
) -> None:
    assert runner.finished_without_line(matches) == 0
    no_line = matches.assign(s3_round_pre_avg_goals=np.nan)
    assert runner.finished_without_line(no_line) == 3


def test_goals_over_line_gives_all_then_the_common_lines(
    matches: pd.DataFrame, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "MIN_LINE_MATCHES", 2)
    table = runner.goals_over_line(matches)
    assert table["line"].tolist() == ["all", "2.5"]
    assert table["matches"].tolist() == [3, 2]
    assert table["goals minus line"].tolist() == pytest.approx([(-0.5 + 0.5 + 1.0) / 3, 0.0])


def test_line_against_model_compares_the_line_with_the_expected_goals() -> None:
    model = pd.DataFrame({"line": [2.0, 2.5, 3.0], "m_goals": [2.2, 2.7, 3.2]})
    result = runner.line_against_model(model)
    assert result["correlation"] == pytest.approx(1.0)
    assert result["expected goals minus line"] == pytest.approx(0.2)
    assert result["matches"] == 3.0
