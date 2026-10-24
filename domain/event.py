"""The contract for one non-scoring event in `data/archived/raw/events.csv`.

Cards and substitutions, one row per event, keyed by `match_id`. Goals live in their own
store (`domain/goal.py`) because they are identified differently — by the running score
rather than the icon — and because a goal carries a score the event checks reconcile
against, which a card does not.

A match with no cards and no substitutions contributes **no rows at all**, so
`data/archived/raw/events_done.csv` is the record of what has been attempted, exactly as
`goals_done.csv` is for goals. That case is rare but real (an abandoned or unreported
fixture), and deriving "already scraped" from the store would re-fetch it forever.

**Player names are stored, unlike in the goal store.** That is a correctness requirement,
not a nice-to-have: some live pages render the event list twice, and unlike a goal — whose
running score is unique within a match and makes de-duplication exact — two yellow cards
can legitimately share a minute and a side. The players are what tell a genuine pair apart
from a double-render, so `scrapers/event_parsers.py` de-duplicates on them.
"""

from typing import Literal

from pydantic import BaseModel, Field

from domain.goal import MAX_MINUTE, MAX_STOPPAGE

YELLOW_CARD = "Yellow Card"
RED_CARD = "Red Card"
SUBSTITUTION = "Substitution"
# The icon `alt` values this store keeps. Everything else on the page is either a goal
# (handled by domain/goal.py) or an annotation with no state change, such as "VAR".
EVENT_KINDS = (YELLOW_CARD, RED_CARD, SUBSTITUTION)


class Event(BaseModel):
    """A card or a substitution, as read from the live page's event list."""

    match_id: str
    league_id: int | None = None

    # 1-based, ordered by (minute, stoppage) within the match.
    event_index: int = Field(ge=1)

    # Base minute and stoppage kept apart, as for goals: "45+3'" is minute 45, stoppage 3,
    # so `minute <= 45` is an exact first-half test rather than an approximate one.
    minute: int = Field(ge=1, le=MAX_MINUTE)
    stoppage: int = Field(ge=0, le=MAX_STOPPAGE)

    # Which team the event belongs to. Unlike a goal, this comes from the row layout —
    # there is no running score to read it off. See `scrapers/live_rows.py`.
    side: Literal["home", "away"]

    kind: Literal["Yellow Card", "Red Card", "Substitution"]

    # The subject: the booked player, or the player coming ON for a substitution.
    player: str = ""
    # Only for a substitution: the player coming OFF. Empty otherwise.
    player_off: str = ""

    @property
    def is_first_half(self) -> bool:
        """True for "45'" and "45+3'" alike; false from "46'" on."""

        return self.minute <= 45

    @property
    def is_card(self) -> bool:
        return self.kind in (YELLOW_CARD, RED_CARD)
