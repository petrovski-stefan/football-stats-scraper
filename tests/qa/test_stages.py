"""`qa/stages.py`: the derived stage files against the stages before them."""

import numpy as np
import pandas as pd
import pytest

from domain import paths
from domain.columns import SCHEDULE_MULTI_COLUMNS, SCHEDULE_RAW_COLUMNS, SCHEDULE_ROW_COLUMNS
from qa.report import Report
from qa.schedule import STAGED_ODDS
from qa.stages import (
    TOLERANCE,
    check_carried,
    check_no_orphans,
    check_odds_fields,
    check_round_fields,
    declared_columns,
    validate,
)

_CARRIED = ["s1_round", "s1_odds_1x2_open_home"]


def test_each_stage_declares_the_earlier_stages_columns_first() -> None:
    assert declared_columns(1) == SCHEDULE_RAW_COLUMNS
    assert declared_columns(2) == SCHEDULE_RAW_COLUMNS + SCHEDULE_ROW_COLUMNS
    assert declared_columns(3) == (
        SCHEDULE_RAW_COLUMNS + SCHEDULE_ROW_COLUMNS + SCHEDULE_MULTI_COLUMNS
    )


def _raw() -> pd.DataFrame:
    return pd.DataFrame(
        {"match_id": ["1", "2"], "s1_round": [1, 1], "s1_odds_1x2_open_home": [1.5, None]}
    )


def _carried_issues(later_df: pd.DataFrame) -> list[str]:
    report = Report("test")
    check_carried(report, _raw(), later_df, _CARRIED, "stage 1")
    return report.issues


def test_the_same_rows_plus_new_columns_pass() -> None:
    assert _carried_issues(_raw().assign(s2_total_goals=[1, 2])) == []


def test_rows_in_another_order_still_pair_up() -> None:
    assert _carried_issues(_raw().iloc[::-1].reset_index(drop=True)) == []


def test_a_changed_value_fails() -> None:
    later_df = _raw()
    later_df.loc[0, "s1_odds_1x2_open_home"] = 1.6
    assert _carried_issues(later_df) == [
        "1 values differ from stage 1 (column: count) {'s1_odds_1x2_open_home': 1} (stale: rebuild)"
    ]


def test_a_value_filled_since_fails() -> None:
    later_df = _raw()
    later_df.loc[1, "s1_odds_1x2_open_home"] = 2.0
    assert len(_carried_issues(later_df)) == 1


def test_a_float_moved_by_rounding_passes() -> None:
    later_df = _raw()
    later_df.loc[0, "s1_odds_1x2_open_home"] = 1.5 * (1 + TOLERANCE / 10)
    assert _carried_issues(later_df) == []


def test_a_missing_and_an_extra_match_fail() -> None:
    later_df = _raw()
    later_df.loc[1, "match_id"] = "3"
    assert _carried_issues(later_df) == [
        "1 matches of stage 1 missing (stale: rebuild)",
        "1 matches not in stage 1 (stale: rebuild)",
    ]


def test_a_repeated_id_is_left_to_the_key_check() -> None:
    assert _carried_issues(pd.concat([_raw(), _raw().iloc[[0]]])) == []


def _stage_two_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        **dict(
            zip(STAGED_ODDS.cells(), [1.5, 4.0, 6.0, 2.75, 1.9, 1.95, 0.75, 1.9, 1.95], strict=True)
        ),
        "s2_has_odds": True,
        "s2_has_ou_odds": True,
        "s2_has_ah_odds": True,
        "s2_mkt_p_home": 0.6,
        "s2_mkt_p_draw": 0.25,
        "s2_mkt_p_away": 0.15,
        "s2_mkt_sup": 1.4,
        "s2_mkt_tot": 1.4,
        "s2_implied_over": 0.5,
        "s2_implied_ah_home": 0.5,
    }

    row.update(overrides)
    return row


def _odds_issues(*rows: dict[str, object]) -> list[str]:
    report = Report("test")
    check_odds_fields(report, pd.DataFrame(list(rows)))
    return report.issues


def _without(market: str) -> dict[str, object]:
    return dict.fromkeys(STAGED_ODDS.markets()[market])


def test_odds_fields_that_agree_pass() -> None:
    no_1x2 = _stage_two_row(
        **_without("1X2"),
        s2_has_odds=False,
        s2_mkt_p_home=None,
        s2_mkt_p_draw=None,
        s2_mkt_p_away=None,
        s2_mkt_sup=None,
        s2_mkt_tot=None,
    )

    assert _odds_issues(_stage_two_row(), no_1x2) == []


def test_a_flag_against_its_cells_fails() -> None:
    issues = _odds_issues(_stage_two_row(s2_has_ou_odds=False))
    assert issues == ["1 rows where s2_has_ou_odds disagrees with the OU cells"]


def test_a_value_without_its_market_fails() -> None:
    issues = _odds_issues(_stage_two_row(**_without("AH"), s2_has_ah_odds=False))
    assert issues == [
        "1 rows with a value computed from AH that is there without the market, or missing with it"
    ]


def test_a_value_missing_beside_its_market_fails() -> None:
    issues = _odds_issues(_stage_two_row(s2_mkt_sup=None))
    assert any("computed from 1X2" in issue for issue in issues)


def test_probabilities_off_one_fail() -> None:
    issues = _odds_issues(_stage_two_row(s2_mkt_p_home=0.7))
    assert issues == ["1 rows whose 1X2 probabilities do not sum to 1"]


def test_a_stage_file_without_its_stage_one_file_fails() -> None:
    raw = [paths.schedule_path(1, "x_league", "2025")]
    later = [paths.schedule_path(2, "x_league", "2025"), paths.schedule_path(2, "y_league", "2025")]
    report = Report("test")
    check_no_orphans(report, raw, later, 2)
    assert report.issues == [
        "1 stage-2 files without a stage-1 file ['y_league_2025_schedule.csv']"
    ]


def test_stage_three_is_held_to_stage_two_as_well() -> None:
    stage_1_df = _raw()
    stage_2_df = stage_1_df.assign(s2_total_goals=[1, 2])
    stage_3_df = stage_2_df.assign(s2_total_goals=[1, 3])

    report = Report("test")
    validate(report, stage_3_df, 3, {1: stage_1_df, 2: stage_2_df})

    assert any("differ from stage 2" in issue for issue in report.issues)
    assert not any("differ from stage 1" in issue for issue in report.issues)


def test_only_stage_two_gets_the_odds_field_check() -> None:
    stage_2_df = pd.DataFrame([_stage_two_row(match_id="1", s2_has_odds=False)])
    for stage, checked in ((2, True), (3, False)):
        report = Report("test")
        validate(report, stage_2_df, stage, {})
        assert any("s2_has_odds disagrees" in issue for issue in report.issues) is checked


def _round_row(**overrides: object) -> dict[str, object]:
    """One stage-3 row of a 10-match round after 3 finished round-mates: a 4-3 comeback
    (both a comeback and 7+), a 1-1 and a 2-0."""

    row: dict[str, object] = {
        "s3_matches_in_round": 10,
        "s3_round_pre_finished": 3,
        "s3_round_pre_comebacks": 1,
        "s3_round_pre_seven_plus": 1,
        "s3_round_pre_rare_events": 1,
        "s3_round_pre_btts": 2,
        "s3_round_pre_avg_goals": 3.67,
        "s3_round_pre_avg_ou_line": 2.75,
    }

    row.update(overrides)
    return row


def _round_issues(*rows: dict[str, object]) -> list[str]:
    report = Report("test")
    check_round_fields(report, pd.DataFrame(list(rows)))
    return report.issues


def test_round_fields_that_agree_pass() -> None:
    nothing_yet = _round_row(
        s3_round_pre_finished=0,
        s3_round_pre_comebacks=0,
        s3_round_pre_seven_plus=0,
        s3_round_pre_rare_events=0,
        s3_round_pre_btts=0,
        s3_round_pre_avg_goals=np.nan,
        s3_round_pre_avg_ou_line=np.nan,
    )

    assert _round_issues(_round_row(), nothing_yet) == []


@pytest.mark.parametrize(
    ("overrides", "rule"),
    [
        ({"s3_round_pre_rare_events": 3}, "rare_events is above"),
        ({"s3_round_pre_rare_events": 0}, "rare_events is below"),
        ({"s3_matches_in_round": 3}, "finished is not below"),
        ({"s3_round_pre_btts": 4}, "btts is above"),
        ({"s3_round_pre_btts": 0}, "comebacks is above"),
        ({"s3_round_pre_avg_ou_line": np.nan}, "only one of the two round averages"),
    ],
)
def test_each_broken_round_rule_fails(overrides: dict[str, object], rule: str) -> None:
    issues = _round_issues(_round_row(), _round_row(**overrides))
    assert len(issues) == 1
    assert issues[0].startswith("1 rows where ")
    assert rule in issues[0]


def test_only_stage_three_gets_the_round_field_check() -> None:
    stage_2_df = pd.DataFrame([_round_row(match_id="1", s3_round_pre_btts=4)])
    for stage, checked in ((2, False), (3, True)):
        report = Report("test")
        validate(report, stage_2_df, stage, {})
        assert any("btts is above" in issue for issue in report.issues) is checked
