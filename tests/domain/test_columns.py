"""`domain/columns.py`: the declared CSV column orders, checked against the models."""

from domain import columns
from domain.match import Match
from domain.match_detail import MatchDetail


def test_column_lists_have_no_duplicates() -> None:
    for declared in (columns.ORDERED_DF_COLUMNS, columns.DETAIL_ORDERED_COLUMNS):
        assert len(declared) == len(set(declared))


def test_schedule_columns_match_the_match_model() -> None:
    model = set(Match.model_fields) | set(Match.model_computed_fields)
    assert set(columns.ORDERED_DF_COLUMNS) == model


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
