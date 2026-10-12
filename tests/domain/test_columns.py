"""`domain/columns.py`: the declared CSV column orders, checked against the models."""

from domain import columns
from domain.match_detail import MatchDetail
from domain.schedule import FinalTableRow, ScheduleRow


def test_column_lists_have_no_duplicates() -> None:
    for declared in (columns.ORDERED_DF_COLUMNS, columns.DETAIL_ORDERED_COLUMNS):
        assert len(declared) == len(set(declared))


def test_detail_columns_cover_the_detail_model() -> None:
    model = set(MatchDetail.model_fields) | set(MatchDetail.model_computed_fields)
    assert model <= set(columns.DETAIL_ORDERED_COLUMNS)


def test_per_match_columns_naming() -> None:
    names = columns.per_match_columns()
    fields = columns.PER_MATCH_FIELDS
    assert len(names) == len(columns.PER_MATCH_SECTIONS) * columns.MATCHES_PER_SECTION * len(fields)
    first_section = columns.PER_MATCH_SECTIONS[0]
    assert names[: len(fields)] == [f"{first_section}_last1_{field}" for field in fields]
    assert set(names) <= set(columns.DETAIL_ORDERED_COLUMNS)


# --- The staged pipeline ---------------------------------------------------------------

# The columns that identify a row in their own file stay bare (notes/fields/README.md).
_SCHEDULE_KEYS = {"match_id"}
_FINAL_TABLE_KEYS = {"season", "league_id", "stage", "team_id"}


def test_stage_1_columns_match_the_models() -> None:
    assert list(ScheduleRow.model_fields) == columns.SCHEDULE_RAW_COLUMNS
    assert list(FinalTableRow.model_fields) == columns.FINAL_TABLE_COLUMNS


def test_each_stage_names_its_own_columns() -> None:
    by_code = {
        "s1_": columns.SCHEDULE_RAW_COLUMNS,
        "s2_": columns.SCHEDULE_ROW_COLUMNS,
        "s3_": columns.SCHEDULE_MULTI_COLUMNS,
    }
    for code, declared in by_code.items():
        unkeyed = [c for c in declared if c not in _SCHEDULE_KEYS]
        assert all(c.startswith(code) for c in unkeyed), code
    table = [c for c in columns.FINAL_TABLE_COLUMNS if c not in _FINAL_TABLE_KEYS]
    assert all(c.startswith("s1_") for c in table)


def test_a_stage_file_holds_each_column_once() -> None:
    stage_3 = (
        columns.SCHEDULE_RAW_COLUMNS + columns.SCHEDULE_ROW_COLUMNS + columns.SCHEDULE_MULTI_COLUMNS
    )
    assert len(stage_3) == len(set(stage_3))


def test_pre_kickoff_columns_cover_every_combination() -> None:
    names = columns.pre_kickoff_columns()
    expected = (
        len(columns.STANDING_SIDES)
        * len(columns.STANDING_HALVES)
        * len(columns.STANDING_VENUES)
        * len(columns.STANDING_STATS)
    )
    assert len(names) == len(set(names)) == expected
    assert names[0] == "s3_home_pre_ft_total_rank"


def test_stake_columns_cover_both_sides() -> None:
    names = columns.stake_columns()
    assert len(names) == len(set(names)) == len(columns.STANDING_SIDES) * len(columns.STAKE_FIELDS)
    assert set(names) <= set(columns.SCHEDULE_MULTI_COLUMNS)


def test_htft_columns_cover_every_combination() -> None:
    names = columns.pre_htft_columns()
    expected = (
        len(columns.STANDING_SIDES) * len(columns.STANDING_VENUES) * len(columns.HTFT_RESULTS) ** 2
    )
    assert len(names) == len(set(names)) == expected
    assert set(names) <= set(columns.SCHEDULE_MULTI_COLUMNS)
