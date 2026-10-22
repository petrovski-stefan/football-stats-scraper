"""Parse cards and substitutions from a match's live page.

The companion to `scrapers/goal_parsers.py`: same page, same rows, opposite selection.
That parser keeps the rows carrying a running score; this one keeps the rows that do not
and whose icon names a card or a substitution.

**Side comes from the row layout here, not from a score.** A card has no score to read,
so `scrapers/live_rows.py` resolves it from which half of the five-cell row is populated.
That is safe for cards and substitutions precisely because they are not goals: the own-goal
case, where the rendered side and the credited side disagree, cannot arise.

**A substitution is one row, not two.** The icon beside the minute is `11.png`
"Substitution"; the content cell holds `4.png` "Sub in" and `5.png` "Sub out" beside two
player links. Reading the first image in the row instead would name the same event
"Sub in" on one side and "Substitution" on the other — see `live_rows`.

Extra time is dropped, as it is for goals: every score and every state this project stores
is the 90-minute one, so a 105' booking would describe a period nothing else covers.
"""

from typing import Any

from bs4 import BeautifulSoup, Tag

from domain.event import EVENT_KINDS, SUBSTITUTION
from domain.goal import MAX_MINUTE, MAX_STOPPAGE
from scrapers import live_rows
from scrapers.constants import LIVE_EVENT_ICON

SUB_IN_ALT = "Sub in"
SUB_OUT_ALT = "Sub out"


def parse_match_events(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Every card and substitution on the page, ordered by when it happened.

    Returns one dict per event with `event_index`, `minute`, `stoppage`, `side`, `kind`,
    `player` and `player_off`. An empty list means a match with no cards or substitutions
    *or* a page whose events never rendered; the caller distinguishes those the same way
    the goal scrape does, by whether anything at all came back for the match.
    """
    found: list[dict[str, Any]] = []
    for row in live_rows.iter_rows(soup):
        if row.kind not in EVENT_KINDS or row.side is None:
            continue
        if row.minute > MAX_MINUTE or row.stoppage > MAX_STOPPAGE:
            continue

        player, player_off = _players(row)
        found.append(
            {
                "minute": row.minute,
                "stoppage": row.stoppage,
                "side": row.side,
                "kind": row.kind,
                "player": player,
                "player_off": player_off,
            }
        )

    ordered = _dedupe(found)
    for index, event in enumerate(ordered, 1):
        event["event_index"] = index

    return ordered


def _dedupe(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse the same event reported twice, then order by when it happened.

    Some live pages render the event list twice — a summary block and a commentary feed
    both sit in the DOM — so one booking arrives as two `<tr>` elements with identical
    content, which de-duplicating by node identity cannot catch.

    Goals collapse on their running score, which is unique within a match. Cards have no
    such key: two players on the same side can be booked in the same minute, and
    collapsing on (minute, side, kind) alone would silently merge them into one. Including
    the players makes the key exact — a genuine pair differs in the name, a double-render
    does not.
    """
    unique: dict[tuple[Any, ...], dict[str, Any]] = {}
    for event in sorted(events, key=_when):
        key = (
            event["minute"],
            event["stoppage"],
            event["side"],
            event["kind"],
            event["player"],
            event["player_off"],
        )
        unique.setdefault(key, event)

    return sorted(unique.values(), key=_when)


def _when(event: dict[str, Any]) -> tuple[int, int]:
    return (event["minute"], event["stoppage"])


def _players(row: live_rows.LiveRow) -> tuple[str, str]:
    """(subject, player_off). For a card the subject is the booked player.

    For a substitution the content cell interleaves markers and links as
    `4.png` "Sub in", <a>on</a>, `5.png` "Sub out", <a>off</a>, so each link is attributed
    to whichever marker most recently preceded it rather than to its position. Pages that
    omit a marker fall back to document order, which is in/out on every page observed.
    """
    cell = row.content_cell()
    if cell is None:
        return "", ""

    names = [a.get_text(strip=True) for a in cell.find_all("a") if a.get_text(strip=True)]
    if row.kind != SUBSTITUTION:
        return (names[0] if names else ""), ""

    on, off = _by_marker(cell)
    if on or off:
        return on, off
    return (names[0] if names else ""), (names[1] if len(names) > 1 else "")


def _by_marker(cell: Tag) -> tuple[str, str]:
    """Walk the cell in order, attributing each player link to the last marker seen."""
    on = off = ""
    marker = ""
    for node in cell.find_all([LIVE_EVENT_ICON, "a"]):
        if node.name == LIVE_EVENT_ICON:
            alt = node.get("alt")
            if isinstance(alt, str) and alt.strip() in (SUB_IN_ALT, SUB_OUT_ALT):
                marker = alt.strip()
            continue

        name = node.get_text(strip=True)
        if not name:
            continue
        if marker == SUB_IN_ALT and not on:
            on = name
        elif marker == SUB_OUT_ALT and not off:
            off = name

    return on, off
