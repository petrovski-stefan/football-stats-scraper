"""Reading the live page's event table, shared by the goal and event parsers.

Both parsers walk the same `<tr>` elements on the live page (`/match/live-<id>` on
`constants.MATCH_HOST`), so the row-finding, minute-parsing and side-detection live here once
rather than being written twice and drifting apart.

**The row is five cells, and the minute sits in the middle.** Measured on live pages
2026-09-23:

    td[0]  home content      (player links, and for a goal the running score)
    td[1]  home event icon
    td[2]  <b class="score">78'</b>      <- the minute, always the middle cell
    td[3]  away event icon
    td[4]  away content

Two consequences that are easy to get wrong:

  - **Side comes from which half of the row is populated**, not from the order names
    appear in the row's text. A home event reads "Chukwueze S. 4 - 5 78'" and an away one
    reads "90+4' Cherki R." — the minute moves because the content moved, not the event.
  - **The event's own icon is the one in the cell beside the minute**, not the first
    `<img>` in the row. A substitution's icon cell holds `11.png` "Substitution" while its
    *content* cell holds `4.png` "Sub in" and `5.png` "Sub out" beside the two players.
    Taking the first image in document order therefore labels home substitutions "Sub in"
    and away substitutions "Substitution" — the same event under two names, purely
    because the content cell precedes the icon cell on one side and follows it on the
    other.

Side is *not* how goals are attributed. A goal is attributed by which running score
advanced (see `scrapers/goal_parsers.py`), and an own goal is exactly the case where the
two disagree: it is rendered on the player's own side but credited to the opponent.
"""

import re
from collections.abc import Iterator
from dataclasses import dataclass

from bs4 import BeautifulSoup, Tag

from scrapers.constants import LIVE_EVENT_ICON, LIVE_EVENT_MINUTE, LIVE_EVENT_ROW

# "33'", "45+3'", "90+8'" -> (base minute, stoppage)
MINUTE_RE = re.compile(r"^\s*(\d{1,3})(?:\+(\d{1,2}))?'\s*$")


@dataclass(frozen=True)
class LiveRow:
    """One event row, with the parts every consumer needs already resolved."""

    row: Tag
    minute: int
    stoppage: int
    # None when neither half of the row carries content, or when both do — either way the
    # row cannot be attributed and the caller decides whether that matters.
    side: str | None
    # The `alt` of the icon beside the minute: "Goal", "Yellow Card", "Substitution"...
    kind: str

    @property
    def text(self) -> str:
        return self.row.get_text(" ", strip=True)

    def content_cell(self) -> Tag | None:
        """The populated half of the row — where player links live."""

        cells = self.row.find_all("td", recursive=False)
        index = _minute_index(cells)
        if index is None or self.side is None:
            return None

        cell = cells[0] if self.side == "home" else cells[-1]

        return cell if isinstance(cell, Tag) else None


def iter_rows(soup: BeautifulSoup) -> Iterator[LiveRow]:
    """Every event row on the page, in document order, de-duplicated by node identity."""

    seen: set[int] = set()
    for cell in soup.select(LIVE_EVENT_MINUTE):
        parsed = MINUTE_RE.match(cell.get_text(strip=True))
        if parsed is None:
            continue

        row = cell.find_parent(LIVE_EVENT_ROW)
        if row is None or id(row) in seen:
            continue
        seen.add(id(row))

        cells = row.find_all("td", recursive=False)
        side = _side_of(cells)
        yield LiveRow(
            row=row,
            minute=int(parsed.group(1)),
            stoppage=int(parsed.group(2) or 0),
            side=side,
            kind=_kind(cells, side),
        )


def _minute_index(cells: list[Tag]) -> int | None:
    """Index of the cell holding the minute, which splits the row into home and away."""

    for i, cell in enumerate(cells):
        if cell.select_one(LIVE_EVENT_MINUTE) is not None:
            return i

    return None


def _side_of(cells: list[Tag]) -> str | None:
    """Which half of the row carries the event."""

    index = _minute_index(cells)
    if index is None:
        return None

    home = _populated(cells[:index])
    away = _populated(cells[index + 1 :])
    if home == away:  # neither side, or both — not attributable
        return None

    return "home" if home else "away"


def _populated(cells: list[Tag]) -> bool:
    return any(cell.get_text(strip=True) or cell.select_one(LIVE_EVENT_ICON) for cell in cells)


def _kind(cells: list[Tag], side: str | None) -> str:
    """The `alt` of the icon in the cell beside the minute — see the module docstring."""

    index = _minute_index(cells)
    if index is None or side is None:
        return ""

    icon_index = index - 1 if side == "home" else index + 1
    if not 0 <= icon_index < len(cells):
        return ""

    for icon in cells[icon_index].select(LIVE_EVENT_ICON):
        alt = icon.get("alt")
        if isinstance(alt, str) and alt.strip():
            return alt.strip()

    return ""
