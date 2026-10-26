"""Which historical matches are in scope for goal timings.

A fixture's detail page lists each side's recent form and the head-to-head going back
years, across every competition. Not all of it is usable, and the two exclusions here were
established by measurement on 2026-09-22 — every one of the 11 matches whose goal timings
failed to reconcile fell into one of them:

**Friendlies carry no goal timings.** nowgoal serves an empty event list for
"International Club Friendly" fixtures despite recording a decisive score. That is not a
nowgoal quirk; minute data for friendlies is patchy everywhere. 108 of 1,791 referenced
matches (6.0%) are friendlies.

**Pre-2023 pages are unreliable.** Old matches come back with a truncated event list — a
2017 fixture recorded 0-4 returned two goals — and stoppage time is rendered as a raw
minute (`91'`) rather than `90+1'`, which puts it past the regulation cap. 2023 is also
where the corpus itself starts, so nothing earlier feeds a label anyway. 304 of 1,791
(17.0%) predate it.

Together they exclude 404 of 1,791 (22.6%), which is a saving on the scrape as well as a
correctness fix: those pages cost the same to fetch as good ones.

Lives in `domain` because all three of `scrapers`, `features` and `qa` need the same
answer, and `domain` is the only package every layer may import.
"""

import re

# Matched case-insensitively against the competition name on a history row.
FRIENDLY_MARKER = "friendly"
# Earliest year whose pages are trustworthy. Also the first season in the corpus.
HISTORY_FROM_YEAR = 2023

_YEAR_RE = re.compile(r"^\s*(\d{4})")


def is_friendly(league_name: str | None) -> bool:
    """Whether a competition name marks the match as a friendly."""

    return FRIENDLY_MARKER in str(league_name or "").lower()


def match_year(date_text: str | None) -> int | None:
    """The year from a history row's date, or None when it does not start with one."""

    # History dates arrive as "2025-08-09 10:30:00": the leading year is all that is needed, so
    # there is no full datetime parse and no list of formats to cover.
    found = _YEAR_RE.match(str(date_text or ""))

    return int(found.group(1)) if found else None


def in_scope(league_name: str | None, date_text: str | None) -> bool:
    """Whether a referenced history match is worth fetching and using: no friendly, no old page."""

    if is_friendly(league_name):
        return False

    year = match_year(date_text)

    # An unparseable date counts as in scope: dropping it would shrink the corpus for a
    # formatting reason, and `qa/goals.py` catches a match whose timings are really wrong.
    return year is None or year >= HISTORY_FROM_YEAR
