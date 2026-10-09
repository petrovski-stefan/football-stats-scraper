"""Which matches are usable: stored matches not played to the end, and the historical
matches in scope for goal timings.

**Abandoned matches.** The schedule page lists a match stopped before full time like any
finished one, with the score when play stopped, so its half-time and full-time goals are
not a result. Nothing on the page tells them apart: each one here was found by the
final-table check (`qa/final_table.py`) and confirmed in public reports, and is kept by
hand. Stage 2 flags it (`s2_is_abandoned`), and the analysis leaves it out.

**Forfeits.** A match never played (a team did not turn up, or it was called off and
awarded) is listed with the awarded score, usually 3-0 with 0-0 at half-time. The page
does not mark it either, and the pattern alone is no proof: real 3-0 wins look the same.
Each one here was confirmed in public reports or, for one club's run at the end of a
season, by the club folding. Stage 2 flags it (`s2_is_forfeit`); the standings count it as
the league did, and the goal and comeback analysis leaves it out.

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

# Match id -> what happened. The user decides each entry. Empty since 2026-10-08: both
# matches listed so far left the project with their leagues.
ABANDONED_MATCHES: dict[str, str] = {}

_ZRINSKI = (
    "CRO D2 2024-25, NK Zrinski Jurjevac's end of season: 0-0 at half-time, 3-0 to the "
    "opponent, mostly with no odds; the club folded in 2025 (the user, 2026-10-08)"
)

# Match id -> what happened. The user decides each entry.
FORFEITED_MATCHES = {
    "2634927": "TFF 1. Lig 2024-25, Yeni Malatyaspor v Pendikspor: Yeni Malatyaspor did not "
    "turn up for round 1 and lost 0-3 (the user, 2026-10-08)",
    "2609242": "CYP D1 2024-25, Apollon v AEL: the Limassol derby was called off over crowd "
    "safety; the page shows 3-0 (the user, 2026-10-08)",
    "2753079": _ZRINSKI,
    "2753094": _ZRINSKI,
    "2753102": _ZRINSKI,
    "2753105": _ZRINSKI,
    "2753114": _ZRINSKI,
    "2753116": _ZRINSKI,
}


def is_abandoned(match_id: object) -> bool:
    """Whether a stored match was stopped before full time."""
    return str(match_id) in ABANDONED_MATCHES


def is_forfeit(match_id: object) -> bool:
    """Whether a stored match was never played, its score awarded by the league."""
    return str(match_id) in FORFEITED_MATCHES


def is_friendly(league_name: str | None) -> bool:
    """Whether a competition name marks the match as a friendly."""
    return FRIENDLY_MARKER in str(league_name or "").lower()


def match_year(date_text: str | None) -> int | None:
    """The year from a history row's date, or None when it does not start with one.

    History dates arrive as "2025-08-09 10:30:00"; a leading four-digit year is the only
    part needed, so this avoids a full datetime parse and the formats it would have to
    cover.
    """
    found = _YEAR_RE.match(str(date_text or ""))
    return int(found.group(1)) if found else None


def in_scope(league_name: str | None, date_text: str | None) -> bool:
    """Whether a referenced historical match is worth fetching and using.

    An unparseable date is treated as in scope: dropping a match because its date could
    not be read would silently shrink the corpus for a formatting reason rather than a
    substantive one, and the reconciliation check in `qa/goals.py` catches anything whose
    timings are actually wrong.
    """
    if is_friendly(league_name):
        return False
    year = match_year(date_text)
    return year is None or year >= HISTORY_FROM_YEAR
