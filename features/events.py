"""Card and substitution features, derived from `data/raw/events.csv`.

The companion to `features/goals.py`, built the same way: for each fixture, look up the
events of the matches in the home side's recent form, the away side's recent form and the
head-to-head, then aggregate them **from the subject team's point of view**. `features/
history.py` resolves which matches those are, so the two modules cannot disagree about it.

Two kinds of output, as for goals:

  - **Aggregates** (`*_reds_for_rate` and friends) are numeric model inputs. The windows
    they use — 70' for a "late" substitution — are hypotheses, not facts.
  - **Timelines** (`home_last1_event_timeline` = "23YF;45SA;67RF") are the record: one
    string per history match, lossless down to stoppage time, so a window nobody has
    thought of yet is re-derivable without going back to the store.

What this buys that the goal features do not:

  - **`reds_against_rate`** is the one genuinely comeback-shaped signal here. A team that
    plays opponents down to ten men wins matches it was losing; that is a mechanism, not a
    correlation. It is also *rare* — measured at 0.05 red cards per match — so a five-match
    window reads zero far more often than not, and the feature is mostly a sparse flag.
  - **`first_sub_minute_avg`** proxies how early a manager reacts. A side that changes
    things at 46' when trailing behaves differently from one that waits until 70'.

**Honest prior, stated up front.** These are historical team-trait rates, which is the
exact shape of the six nowgoal families in `RESULTS.md` and the behavioural rule in
`BEHAVIOURAL_RESULTS.md` — all of which measured ~1.0x lift. Nothing here has been tested;
these are Tier-3 instruments in `notes/RETRY_CANDIDATES_2026-09-23.md` terms, and they
join the same Holm family as everything else when they are.
"""

import numpy as np
import pandas as pd

from domain.columns import MATCHES_PER_SECTION
from domain.event import RED_CARD, SUBSTITUTION, YELLOW_CARD
from features import history

# A substitution at or after this minute is "late" — a closing change rather than a
# reaction to how the match is going.
LATE_SUB_MINUTE = 70

TIMELINE_FIELD = "event_timeline"
# A match that was usable and genuinely had no cards or substitutions. Needed because an
# empty cell already means "no usable events", and a clean match is a fact, not a gap.
UNEVENTFUL = "-"

# Timeline codes: kind + whether it was the subject's (F) or the opponent's (A).
_CODES = {YELLOW_CARD: "Y", RED_CARD: "R", SUBSTITUTION: "S"}

FEATURE_SUFFIXES = (
    "yellows_for_avg",
    "yellows_against_avg",
    "reds_for_rate",
    "reds_against_rate",
    "subs_for_avg",
    "first_sub_minute_avg",
    "late_sub_rate",
    "events_seen",
)

# (minute, stoppage, kind, side) as stored; oriented to F/A once the subject is known.
Events = list[tuple[int, int, str, str]]


def feature_names() -> list[str]:
    """The numeric aggregate columns, in order."""
    return history.feature_names(FEATURE_SUFFIXES)


def timeline_names(depth: int = MATCHES_PER_SECTION) -> list[str]:
    """The per-history-match timeline columns, in order."""
    return history.timeline_names(TIMELINE_FIELD, depth)


def load_store(events_path: str) -> dict[str, Events]:
    """match_id -> [(minute, stoppage, kind, side), ...]."""
    frame = pd.read_csv(events_path, usecols=["match_id", "minute", "stoppage", "kind", "side"])
    store: dict[str, Events] = {}
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
    store: dict[str, Events],
    depth: int = MATCHES_PER_SECTION,
) -> pd.DataFrame:
    """One row per fixture: the aggregates for all three sections, plus every timeline."""
    return history.build_frame(
        detail,
        depth,
        FEATURE_SUFFIXES,
        TIMELINE_FIELD,
        lambda prefix, row: _usable_events(detail, store, prefix, row),
        _rates,
        _timeline,
    )


def _usable_events(
    detail: pd.DataFrame, store: dict[str, Events], prefix: str, row: int
) -> Events | None:
    """One history match's events, oriented to the subject team. None when unusable.

    Unusable means not scraped, out of scope, or a match whose venue is unknown — the same
    three tests `features/goals.py` applies, minus its score reconciliation, because an
    event store has no score to reconcile against.
    """
    match_id = history.match_key(detail, prefix, row)
    if match_id is None or match_id not in store:
        return None
    is_home = history.subject_is_home(detail, prefix, row)
    if is_home is None:
        return None
    return [
        (minute, stoppage, kind, "F" if (side == "home") == is_home else "A")
        for minute, stoppage, kind, side in store[match_id]
    ]


def _timeline(events: Events | None) -> str:
    """ "23YF;45+2SA;67RF" — lossless, subject-oriented, ordered as they happened.

    Empty when the match had no usable events; `UNEVENTFUL` when it was usable and simply
    had none. Those are different facts and an empty cell cannot carry both.
    """
    if events is None:
        return ""
    if not events:
        return UNEVENTFUL
    parts = []
    for minute, stoppage, kind, tag in events:
        stamp = f"{minute}+{stoppage}" if stoppage else str(minute)
        parts.append(f"{stamp}{_CODES.get(kind, '?')}{tag}")
    return ";".join(parts)


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
    sub_minutes = [m for m, _, k, t in flat if k == SUBSTITUTION and t == "F"]
    return {
        "yellows_for_avg": _count(flat, YELLOW_CARD, "F") / n,
        "yellows_against_avg": _count(flat, YELLOW_CARD, "A") / n,
        "reds_for_rate": _match_share(usable, RED_CARD, "F"),
        "reds_against_rate": _match_share(usable, RED_CARD, "A"),
        "subs_for_avg": len(sub_minutes) / n,
        "first_sub_minute_avg": float(np.mean(first_subs)) if first_subs else float("nan"),
        "late_sub_rate": _share(sub_minutes, LATE_SUB_MINUTE),
        "events_seen": float(len(flat)),
    }


def _first_sub_minutes(usable: list[Events]) -> list[int]:
    """Each match's earliest substitution by the subject team, where it made one."""
    found = []
    for block in usable:
        minutes = [m for m, _, k, t in block if k == SUBSTITUTION and t == "F"]
        if minutes:
            found.append(min(minutes))
    return found


def _share(minutes: list[int], cutoff: int) -> float:
    """Share of `minutes` at or after `cutoff`; NaN when there is nothing to divide by."""
    if not minutes:
        return float("nan")
    return float(sum(1 for m in minutes if m >= cutoff) / len(minutes))


def _count(flat: list[tuple[int, int, str, str]], kind: str, tag: str) -> float:
    return float(sum(1 for _, _, k, t in flat if k == kind and t == tag))


def _match_share(usable: list[Events], kind: str, tag: str) -> float:
    """Share of usable matches containing at least one such event."""
    hits = sum(1 for b in usable if any(k == kind and t == tag for _, _, k, t in b))
    return float(hits / len(usable))
