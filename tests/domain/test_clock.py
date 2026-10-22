"""`domain/clock.py`: Berlin time with its offset, written and read back."""

from datetime import UTC, datetime, timedelta, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from domain.clock import BERLIN, parse_berlin, parse_instant, to_berlin


@pytest.mark.parametrize(
    ("moment", "text"),
    [
        # Winter: Berlin is UTC+1.
        (datetime(2026, 1, 31, 17, 30, tzinfo=UTC), "2026-01-31 18:30+01:00"),
        # Summer: Berlin is UTC+2.
        (datetime(2025, 8, 15, 19, 0, tzinfo=UTC), "2025-08-15 21:00+02:00"),
        # Another clock in, Berlin out: UTC+8 01:30 is the previous evening in Berlin.
        (
            datetime(2026, 2, 1, 1, 30, tzinfo=timezone(timedelta(hours=8))),
            "2026-01-31 18:30+01:00",
        ),
    ],
)
def test_to_berlin(moment: datetime, text: str) -> None:
    assert to_berlin(moment) == text


@given(
    st.datetimes(datetime(1990, 1, 1), datetime(2100, 1, 1), timezones=st.just(UTC)).map(
        lambda moment: moment.replace(second=0, microsecond=0)
    )
)
def test_any_instant_to_the_minute_survives_writing_and_reading(moment: datetime) -> None:
    # Every clock change from 1990 to 2100 is in range: the written offset keeps the instant.
    assert parse_instant(to_berlin(moment)) == moment


def test_to_berlin_refuses_a_naive_datetime() -> None:
    with pytest.raises(ValueError, match="naive"):
        to_berlin(datetime(2026, 1, 31, 18, 30))


def test_parse_berlin_round_trips() -> None:
    text = "2025-08-15 21:00+02:00"
    moment = parse_berlin(text)
    assert moment.tzinfo == BERLIN
    assert to_berlin(moment) == text


def test_the_autumn_clock_change_keeps_two_instants_apart() -> None:
    # 02:30 happens twice in Berlin on 2025-10-26; the offset says which one.
    first = parse_instant("2025-10-26 02:30+02:00")
    second = parse_instant("2025-10-26 02:30+01:00")
    assert second - first == timedelta(hours=1)


def test_wall_clock_values_must_not_be_compared() -> None:
    # The trap parse_instant exists for: same zone, same wall clock, compared as equal.
    first = parse_berlin("2025-10-26 02:30+02:00")
    second = parse_berlin("2025-10-26 02:30+01:00")
    assert second - first == timedelta(0)


def test_a_gap_across_the_spring_change_is_real_time() -> None:
    # Clocks go forward on 2026-03-29: Saturday 15:00 to Sunday 15:00 is 23 hours.
    saturday = parse_instant("2026-03-28 15:00+01:00")
    sunday = parse_instant("2026-03-29 15:00+02:00")
    assert sunday - saturday == timedelta(hours=23)


@pytest.mark.parametrize("text", ["2026-01-31 18:30", "2026-01-31"])
def test_parse_berlin_refuses_a_value_without_offset(text: str) -> None:
    with pytest.raises(ValueError, match="offset"):
        parse_berlin(text)
