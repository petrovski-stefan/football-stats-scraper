"""The contract for one goal in `data/raw/goals.csv`.

One row per goal, keyed by `match_id`. A goalless match contributes **no rows at all**,
which is why `data/raw/goals_done.csv` exists separately as the record of what has been
attempted — see `domain/paths.py`.

Row-level validation only. The sequence invariants (scores advancing by exactly one, the
half-time split reconciling against the stored score) span rows and belong to
`qa/goals.py`, which checks them against the corpus's own half-time and full-time scores.
"""

from typing import Literal

from pydantic import BaseModel, Field

# Regulation only. `minute` is the base minute, so 90 is the ceiling and stoppage is
# carried separately -- "90+5'" is minute 90, stoppage 5. Extra time (92', 105', 120')
# does occur, in the cup ties that appear in a team's history, and is dropped by
# `scrapers/goal_parsers.py`: every score this project stores is the 90-minute one.
MAX_MINUTE = 90
MAX_STOPPAGE = 20


class Goal(BaseModel):
    """A single goal, as read from the live page's event list."""

    match_id: str
    league_id: int | None = None

    # 1-based, ordered by (minute, stoppage) within the match.
    goal_index: int = Field(ge=1)

    # The base minute: 45 for both "45'" and "45+3'". `stoppage` carries the added part,
    # so the first half is `minute <= 45` for either. Keeping them apart rather than
    # storing 48 is what makes that test exact.
    minute: int = Field(ge=1, le=MAX_MINUTE)
    stoppage: int = Field(ge=0, le=MAX_STOPPAGE)

    # Which side's running score advanced. Derived from the score, never from the layout.
    side: Literal["home", "away"]

    home_score_after: int = Field(ge=0)
    away_score_after: int = Field(ge=0)

    # The event's own label from the icon's `alt`: "Goal", "Penalty Scored", and so on.
    # Recorded but never used to decide whether a row is a goal — see scrapers/goal_parsers.
    kind: str = ""

    @property
    def is_first_half(self) -> bool:
        """True for "45'" and "45+3'" alike; false from "46'" on."""
        return self.minute <= 45
