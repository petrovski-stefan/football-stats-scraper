"""The project's one clock: every stored date and time is Berlin time with its offset.

Decided by the user on 2026-10-05 (`notes/FIELDS/README.md`, "Rules for values"). Berlin
time is the clock in Berlin, UTC+1 in winter and UTC+2 in summer, and the offset is
written into every value: `2026-01-31 18:30+01:00`, `2025-08-15 21:00+02:00`. With the
offset in the text, a value names one instant even across the autumn clock change, when
02:00-03:00 happens twice, so two values compare exactly once parsed.

The pages give other clocks: the league page's kickoff is UTC+8 (China time), the h2h page's
history dates are UTC. The scrapers convert them on the way in; nothing downstream sees
another clock.

On Windows the zone data comes from the `tzdata` package, which pandas requires.
"""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")


def to_berlin(moment: datetime) -> str:
    """Format an aware datetime as Berlin time with its offset, to the minute."""

    if moment.tzinfo is None:
        raise ValueError(f"naive datetime has no clock: {moment!r}")

    return moment.astimezone(BERLIN).isoformat(sep=" ", timespec="minutes")


def parse_berlin(text: str) -> datetime:
    """Read a stored value back as Berlin wall-clock time: for the date and the weekday.

    Never compare or subtract these: same-zone datetimes compare by wall clock, ignoring the
    offset (`domain/CLAUDE.md` §1a). For order and durations, use `parse_instant`.
    """

    return _parse(text).astimezone(BERLIN)


def parse_instant(text: str) -> datetime:
    """Read a stored value back as an instant, in UTC: safe to compare and subtract."""

    return _parse(text).astimezone(UTC)


def _parse(text: str) -> datetime:
    """The stored text as an aware datetime; ValueError when it has no offset."""

    moment = datetime.fromisoformat(text.strip())
    if moment.tzinfo is None:
        raise ValueError(f"stored time has no offset: {text!r}")

    return moment
