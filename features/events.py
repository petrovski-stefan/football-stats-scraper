"""Card and substitution features, derived from `data/archived/raw/events.csv`.

The companion to `features/goals.py`, built the same way: for each fixture, look up the
events of the matches in the home side's recent form, the away side's recent form and the
head-to-head, then aggregate them **from the subject team's point of view**. `features/
history.py` resolves which matches those are, so the two modules cannot disagree about it.

Two kinds of output, as for goals:

  - **Aggregates** (`*_reds_for_rate` and friends) are numeric model inputs. The windows
    they use — 70' for a "late" substitution — are hypotheses, not facts.
  - **Timelines** (`home_last1_sub_timeline` = "26F;53A;63F") are the record: one string
    per history match per kind, lossless down to stoppage time, so a window nobody has
    thought of yet is re-derivable without going back to the store.

**One timeline per kind, not one per match.** Measured 2026-09-23 over 5,993 populated
cells, a combined string averaged 12.1 entries and 62 characters, of which substitutions
were 68.1% and red cards 0.6% — the rare event was buried behind the common one. The kind
is implied by the column now, so an entry carries only the minute and F/A. Nothing is
lost: merging the four strings back into one match view is a sort on minute, and the raw
stores keep `event_index` for the 1.19% of events that share a minute with a goal.

**Why the goal store is a parameter.** An event means almost nothing without the scoreline
it happened at. Measured over 6,840 history slots, the subject team's own events split
37.3% trailing / 26.0% level / 36.7% leading for substitutions and 30.8/35.7/33.4 for
yellows — near-perfect three-way mixtures. A sub at 60' while two up is a closing change;
at 60' while one down it is a reaction, and `first_sub_minute_avg` averages both.

**What that does and does not justify building**, measured by split-half reliability on
the 2025-2026 corpus (each team's 38 matches split odd/even, correlated across 20 teams,
then extrapolated to the six-match depth these features actually have):

  - `yellows_while_leading_avg` — split-half 0.564 against 0.570 for plain yellows, so
    conditioning on the scoreline costs essentially nothing here. Kept.
  - a trailing-conditioned first-substitution minute — split-half **-0.004**. Managers
    have no stable "how fast I react when behind"; the de-confounded feature is noise.
    Deliberately **not** built, and `first_sub_minute_avg` is kept only as the existing
    unconditioned column (it correlates 0.428 with what this docstring used to claim it
    measured). Do not "fix" it by conditioning it — that was measured and it is dead.
  - per-minute exposure denominators — 0.345 against 0.564 per match. Also rejected.

**Honest prior, stated up front.** These are historical team-trait rates, which is the
exact shape of the six nowgoal families in `RESULTS.md` and the behavioural rule in
`BEHAVIOURAL_RESULTS.md` — all of which measured ~1.0x lift. Nothing here has been tested.
They are **claim 15** of `notes/RECORD/RETRY_CANDIDATES_2026-09-23.md`, added by amendment
`PREREGISTRATION.md` A8 before the scrape, and they carry one condition the other claims
do not: claim 15 is evaluated with the `english_premier_league 2025-2026` stratum dropped,
because A8 §4 discloses that holdout-season comeback labels were looked at while this
family was being designed.
"""

from functools import partial
from typing import NamedTuple

import numpy as np
import pandas as pd

from domain.columns import MATCHES_PER_SECTION
from domain.event import RED_CARD, SUBSTITUTION, YELLOW_CARD
from features import history
from features.goals import Goals

# A substitution at or after this minute is "late" — a closing change rather than a
# reaction to how the match is going.
LATE_SUB_MINUTE = 70

# One column block per kind. The kind is implied by the column, so entries carry only the
# minute and whether the event was the subject's (F) or the opponent's (A).
YELLOW_TIMELINE = "yellow_timeline"
RED_TIMELINE = "red_timeline"
SUB_TIMELINE = "sub_timeline"
TIMELINE_FIELDS = (
    (YELLOW_TIMELINE, YELLOW_CARD),
    (RED_TIMELINE, RED_CARD),
    (SUB_TIMELINE, SUBSTITUTION),
)

# A match that was usable and genuinely had none of that kind. Needed because an empty cell
# already means "no usable events", and a clean match is a fact, not a gap.
UNEVENTFUL = "-"

FEATURE_SUFFIXES = (
    "yellows_for_avg",
    "yellows_against_avg",
    "yellows_while_leading_avg",
    "reds_for_rate",
    "reds_against_rate",
    "subs_for_avg",
    "first_sub_minute_avg",
    "late_sub_rate",
    "events_seen",
)


class TimedEvent(NamedTuple):
    """One event, oriented to the subject team and placed in the match's scoreline."""

    minute: int
    stoppage: int
    kind: str
    # "F" when the event was the subject team's, "A" when it was the opponent's.
    tag: str
    # The **subject team's** goal difference immediately before this minute, whichever
    # side the event belongs to. None when that match's goals are missing or fail to
    # reconcile, which is why every state-conditioned aggregate has its own denominator.
    state: int | None


Events = list[TimedEvent]
# What `features/goals.py:load_store` returns; the scoreline is read from it.
GoalStore = dict[str, Goals]


def feature_names() -> list[str]:
    """The numeric aggregate columns, in order."""
    return history.feature_names(FEATURE_SUFFIXES)


def timeline_names(depth: int = MATCHES_PER_SECTION) -> list[str]:
    """The per-history-match timeline columns, in order — one block per event kind."""
    return [name for field, _ in TIMELINE_FIELDS for name in history.timeline_names(field, depth)]


def load_store(events_path: str) -> dict[str, list[tuple[int, int, str, str]]]:
    """match_id -> [(minute, stoppage, kind, side), ...], as stored."""
    frame = pd.read_csv(events_path, usecols=["match_id", "minute", "stoppage", "kind", "side"])
    store: dict[str, list[tuple[int, int, str, str]]] = {}
    for match_id, minute, stoppage, kind, side in zip(
        frame["match_id"].astype(str),
        frame["minute"],
        frame["stoppage"],
        frame["kind"],
        frame["side"],
        strict=True,
    ):
        store.setdefault(match_id, []).append((int(minute), int(stoppage), str(kind), str(side)))
    return store


def build(
    detail: pd.DataFrame,
    store: dict[str, list[tuple[int, int, str, str]]],
    goal_store: GoalStore,
    depth: int = MATCHES_PER_SECTION,
) -> pd.DataFrame:
    """One row per fixture: the aggregates for all three sections, plus every timeline.

    `goal_store` may be empty — the state-conditioned columns then come back NaN and
    everything else is unaffected, so an events scrape without a goals scrape still builds.
    """
    return history.build_frame(
        detail,
        depth,
        FEATURE_SUFFIXES,
        [(field, partial(_timeline, kind=kind)) for field, kind in TIMELINE_FIELDS],
        lambda prefix, row: _usable_events(detail, store, goal_store, prefix, row),
        _rates,
    )


def _usable_events(
    detail: pd.DataFrame,
    store: dict[str, list[tuple[int, int, str, str]]],
    goal_store: GoalStore,
    prefix: str,
    row: int,
) -> Events | None:
    """One history match's events, oriented to the subject team. None when unusable.

    Unusable means not scraped, out of scope, or a match whose venue is unknown — the same
    three tests `features/goals.py` applies. Its fourth test, score reconciliation, is
    applied only to the *scoreline* here rather than to the events themselves: a match
    whose goals do not reconcile still has trustworthy cards, so it keeps its aggregates
    and timelines and loses only its state.
    """
    match_id = history.match_key(detail, prefix, row)
    if match_id is None or match_id not in store:
        return None
    is_home = history.subject_is_home(detail, prefix, row)
    if is_home is None:
        return None
    line = _score_line(detail, goal_store, prefix, row, match_id, is_home)
    return [
        TimedEvent(
            minute,
            stoppage,
            kind,
            "F" if (side == "home") == is_home else "A",
            _state_at(line, minute, stoppage),
        )
        for minute, stoppage, kind, side in store[match_id]
    ]


def _score_line(
    detail: pd.DataFrame,
    goal_store: GoalStore,
    prefix: str,
    row: int,
    match_id: str,
    is_home: bool,
) -> list[tuple[int, int, int]] | None:
    """The subject's running goal difference after each goal. None when unknown.

    None means the match's goals were never scraped, or they do not reproduce the score the
    history block records — the same reconciliation `features/goals.py` applies, and for
    the same reason: a state computed from half the goals is a wrong scoreline rather than
    a missing one, and it would silently flip "leading" to "trailing".
    """
    goals = goal_store.get(match_id)
    if goals is None:
        return None
    counted_home = sum(1 for _, _, side in goals if side == "home")
    if not history.score_matches(detail, prefix, row, counted_home, len(goals) - counted_home):
        return None
    line: list[tuple[int, int, int]] = []
    diff = 0
    for minute, stoppage, side in sorted(goals):
        diff += 1 if (side == "home") == is_home else -1
        line.append((minute, stoppage, diff))
    return line


def _state_at(line: list[tuple[int, int, int]] | None, minute: int, stoppage: int) -> int | None:
    """The subject's goal difference immediately *before* (minute, stoppage).

    Strictly before, so a card shown in the same minute as the goal that changed the score
    is attributed to the state that provoked it rather than to the one it produced.
    """
    if line is None:
        return None
    diff = 0
    for goal_minute, goal_stoppage, running in line:
        if (goal_minute, goal_stoppage) >= (minute, stoppage):
            break
        diff = running
    return diff


def _timeline(events: Events | None, kind: str) -> str:
    """ "23F;45+2A;67F" — one kind only, subject-oriented, ordered as it happened.

    Empty when the match had no usable events; `UNEVENTFUL` when it was usable and simply
    had none of this kind. Those are different facts and an empty cell cannot carry both.
    """
    if events is None:
        return ""
    parts = [
        f"{e.minute}+{e.stoppage}{e.tag}" if e.stoppage else f"{e.minute}{e.tag}"
        for e in events
        if e.kind == kind
    ]
    return ";".join(parts) if parts else UNEVENTFUL


def _rates(blocks: list[Events | None]) -> dict[str, float]:
    """Fold one fixture's usable history matches into event rates.

    Counting rules worth stating: the card averages are **per usable match**, not per
    event, so a side with no usable history gets NaN rather than 0; the red-card figures
    are the share of matches containing at least one, which is the quantity a sparse
    event supports; and `first_sub_minute_avg` averages each match's earliest subject
    substitution, skipping matches with none rather than treating them as minute 90.
    """
    usable = [b for b in blocks if b is not None]
    if not usable:
        return dict.fromkeys(FEATURE_SUFFIXES, float("nan"))

    n = len(usable)
    flat = [e for b in usable for e in b]
    first_subs = _first_sub_minutes(usable)
    sub_minutes = [e.minute for e in flat if e.kind == SUBSTITUTION and e.tag == "F"]
    return {
        "yellows_for_avg": _count(flat, YELLOW_CARD, "F") / n,
        "yellows_against_avg": _count(flat, YELLOW_CARD, "A") / n,
        "yellows_while_leading_avg": _while_leading(usable),
        "reds_for_rate": _match_share(usable, RED_CARD, "F"),
        "reds_against_rate": _match_share(usable, RED_CARD, "A"),
        "subs_for_avg": len(sub_minutes) / n,
        "first_sub_minute_avg": float(np.mean(first_subs)) if first_subs else float("nan"),
        "late_sub_rate": _share(sub_minutes, LATE_SUB_MINUTE),
        "events_seen": float(len(flat)),
    }


def _while_leading(usable: list[Events]) -> float:
    """Subject yellows collected while ahead, per match whose scoreline is known.

    The denominator is matches with a usable goal timeline rather than all usable matches:
    a match whose goals are missing cannot say what the scoreline was, and scoring it zero
    would dilute the rate instead of leaving it unmeasured. NaN when none is known.

    Per match, not per minute-leading. The exposure-normalised version was measured at
    split-half 0.345 against 0.564 for this one — dividing by minutes spent ahead adds
    noise faster than it adds meaning.
    """
    known = [b for b in usable if all(e.state is not None for e in b)]
    if not known:
        return float("nan")
    hits = sum(
        1
        for block in known
        for e in block
        if e.kind == YELLOW_CARD and e.tag == "F" and e.state is not None and e.state > 0
    )
    return float(hits / len(known))


def _first_sub_minutes(usable: list[Events]) -> list[int]:
    """Each match's earliest substitution by the subject team, where it made one."""
    found = []
    for block in usable:
        minutes = [e.minute for e in block if e.kind == SUBSTITUTION and e.tag == "F"]
        if minutes:
            found.append(min(minutes))
    return found


def _share(minutes: list[int], cutoff: int) -> float:
    """Share of `minutes` at or after `cutoff`; NaN when there is nothing to divide by."""
    if not minutes:
        return float("nan")
    return float(sum(1 for m in minutes if m >= cutoff) / len(minutes))


def _count(flat: Events, kind: str, tag: str) -> float:
    return float(sum(1 for e in flat if e.kind == kind and e.tag == tag))


def _match_share(usable: list[Events], kind: str, tag: str) -> float:
    """Share of usable matches containing at least one such event."""
    hits = sum(1 for b in usable if any(e.kind == kind and e.tag == tag for e in b))
    return float(hits / len(usable))
