"""Parse goal events from a match's live page (`/match/live-<id>` on `constants.MATCH_HOST`).

**Goals are identified by the running score, not by the icon.** Measured on live pages
2026-09-22: a penalty carries a different icon from an open-play goal (`7.png`,
alt "Penalty Scored", against `1.png` / "Goal"), so an icon whitelist silently drops every
penalty. Chelsea 1-0 Fulham has *zero* rows with the goal icon — its only goal was a
penalty at 45+3'. Pogon 0-3 Lech shows the score jumping 0-1 to 0-3 for the same reason.

The running score is the reliable marker and is strictly better than the icon:

  - goal and penalty rows both carry it, whatever their icon;
  - VAR rows never do, so "Goal Disallowed" and "Goal awarded" are excluded for free;
  - it identifies the scoring side by which number went up, which is what we actually want
    and which handles own goals without needing to know their icon at all.

The event's own label is still recorded as `kind` (straight from the icon's `alt`), so a
later question like "do penalties behave differently?" does not need a re-scrape.
"""

import re
from typing import Any

from bs4 import BeautifulSoup

from scrapers import live_rows

# The running score after the goal, e.g. "0 - 2".
SCORE_RE = re.compile(r"(\d{1,2})\s*-\s*(\d{1,2})")
# Regulation only. Cup ties in a team's history go to extra time, and nowgoal's event list
# runs through it — but every score this project stores is the 90-minute one, including the
# `ft_home_goals` the history blocks record and the `is_comeback` definition built on it.
# Keeping extra-time goals made 12 matches store more goals than their own full-time score
# (a 2-2 cup tie arriving as 4-3), so they are dropped here rather than filtered by every
# consumer. Note `90+5'` is minute 90 with stoppage 5 and is regulation; 92' is not.
MAX_MINUTE = 90
MAX_STOPPAGE = 20


def parse_goal_events(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Every goal on the page, ordered by when it was scored.

    Returns one dict per goal with `minute`, `stoppage`, `side`, `home_score_after`,
    `away_score_after`, `kind` and a 1-based `goal_index`. An empty list means a goalless
    match *or* a page whose events never rendered — the caller distinguishes those by
    reconciling against the stored score.
    """
    events = _dedupe(_score_rows(soup))

    goals: list[dict[str, Any]] = []
    home, away = 0, 0
    for event in events:
        new_home, new_away = event["home_score_after"], event["away_score_after"]
        side = _side_that_scored(home, away, new_home, new_away)
        if side is None:
            # The score did not advance by exactly one goal for exactly one side. Either
            # the page is inconsistent or a goal is missing; either way the sequence can no
            # longer be trusted, so stop rather than emit a wrong side. qa/goals.py catches
            # the resulting short count against the stored full-time score.
            break

        goals.append(
            {
                "goal_index": len(goals) + 1,
                "minute": event["minute"],
                "stoppage": event["stoppage"],
                "side": side,
                "home_score_after": new_home,
                "away_score_after": new_away,
                "kind": event["kind"],
            }
        )
        home, away = new_home, new_away

    return goals


def _dedupe(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Collapse the same goal reported more than once, then order by when it was scored.

    Some pages render the event list twice — a summary block and a live commentary feed
    both appear in the DOM — so a goal arrives as two distinct `<tr>` elements with
    identical content. Deduplicating by node identity does not catch that.

    The running score is what identifies a goal: it advances by exactly one per goal, so
    no two goals in a match can share it. Collapsing on it is therefore exact, not a
    heuristic. Without this, the second copy looks like a score that failed to advance,
    the fold in `parse_goal_events` stops, and every later goal is silently lost —
    Liverpool 1-1 Brentford (match 2789503) was stored as 1-0 for exactly this reason.
    """
    unique: dict[tuple[int, int], dict[str, Any]] = {}
    for event in sorted(events, key=lambda goal: (goal["minute"], goal["stoppage"])):
        unique.setdefault((event["home_score_after"], event["away_score_after"]), event)

    return sorted(unique.values(), key=lambda goal: (goal["minute"], goal["stoppage"]))


def _score_rows(soup: BeautifulSoup) -> list[dict[str, Any]]:
    """Rows that carry both a minute and a running score — i.e. the goals."""
    out: list[dict[str, Any]] = []
    for row in live_rows.iter_rows(soup):
        score = SCORE_RE.search(row.text)
        if score is None:
            continue  # a card, a substitution, or a VAR annotation
        if row.minute > MAX_MINUTE or row.stoppage > MAX_STOPPAGE:
            continue

        out.append(
            {
                "minute": row.minute,
                "stoppage": row.stoppage,
                "home_score_after": int(score.group(1)),
                "away_score_after": int(score.group(2)),
                "kind": row.kind,
            }
        )

    return out


def _side_that_scored(home: int, away: int, new_home: int, new_away: int) -> str | None:
    """Which side the running score says scored, or None if it did not advance by one."""
    if new_home == home + 1 and new_away == away:
        return "home"
    if new_away == away + 1 and new_home == home:
        return "away"
    return None
