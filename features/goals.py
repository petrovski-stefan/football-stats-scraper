"""Goal-timing features, derived from the global store in `data/archived/raw/goals.csv`.

These are *history-block* features, in the same shape as the existing `*_recent_*` and
`h2h_*` aggregates: for each fixture, look up the goal timings of the matches in the home
team's recent form, the away team's recent form, and the head-to-head, then aggregate them
from the subject team's point of view.

The lookup is by match id, which is why `scrapers/goals.py` fetches each historical match
exactly once however many fixtures reference it. Nothing is copied between rows; the store
is joined on demand.

Two kinds of output, and the distinction matters:

  - **Aggregates** (`*_late_goal_rate` and friends) are numeric model inputs. The windows
    they use -- 75' for "late", 36-45' for the run-up to half-time -- are hypotheses, not
    facts, so they are convenience columns rather than the record.
  - **Timelines** (`home_last1_goal_timeline` = "15GA;18GF;23GF;85GA") are the record: one
    string per history match, lossless down to stoppage time. Any window someone thinks of
    later is re-derivable from them without going back to the store, which is what keeps
    the enriched file self-contained instead of a view over a file it does not carry.

Both come from one usability decision, so a timeline is present exactly when that match
fed the aggregate beside it.

What timing buys that the existing half-split features do not:

  - `conceded_pre_ht_rate` — goals conceded in minutes 36-45, the window that actually
    manufactures the half-time deficit a comeback has to reverse. `BEHAVIOURAL_RESULTS`
    tested whole-half splits and found corr +0.004 against HT-decisive; this is the same
    idea at the resolution where a mechanism could plausibly live.
  - `late_goal_rate` / `late_conceded_rate` — the share arriving after minute 75, which
    `HANDOFF` §9 item 7 proposed as a better "comeback-prone" measure than comeback counts.
"""

from typing import Any

import numpy as np
import pandas as pd

from domain.columns import MATCHES_PER_SECTION
from features import history

# A goal at or after this minute is "late". 75 is HANDOFF S9's proposed cutoff.
LATE_MINUTE = 75
# The run-up to half-time: goals here create the deficit a comeback must overturn.
PRE_HT_FROM, PRE_HT_TO = 36, 45

TIMELINE_FIELD = "goal_timeline"
# A match that was usable and genuinely goalless. Needed because an empty cell already
# means "no usable timings", and a 0-0 is a fact rather than a gap.
GOALLESS = "-"

# Tier-3 time buckets, inclusive on both ends in BASE minutes. A goal at 45+3' is minute
# 45 and lands in 31_45; 90+7' is minute 90 and lands in 76_90. Note `late_goal_rate` uses
# `>= 75` (HANDOFF S9's cutoff) and so straddles 61_75 and 76_90 -- the two are not a
# partition of each other and are not meant to be.
BUCKETS = ((0, 15), (16, 30), (31, 45), (46, 60), (61, 75), (76, 90))

BUCKET_SUFFIXES = tuple(
    f"{direction}_{lo:02d}_{hi}" for direction in ("gf", "ga") for lo, hi in BUCKETS
)

FEATURE_SUFFIXES = (
    "goal_minute_avg",
    "conceded_minute_avg",
    "late_goal_rate",
    "late_conceded_rate",
    "conceded_pre_ht_rate",
    "goals_seen",
    *BUCKET_SUFFIXES,
)

# (minute, stoppage, side) as stored; oriented to "GF"/"GA" once the subject is known.
Goals = list[tuple[int, int, str]]


def feature_names() -> list[str]:
    """The numeric aggregate columns, in order."""

    return history.feature_names(FEATURE_SUFFIXES)


def timeline_names(depth: int = MATCHES_PER_SECTION) -> list[str]:
    """The per-history-match timeline columns, in order."""

    return history.timeline_names(TIMELINE_FIELD, depth)


def load_store(goals_path: str) -> dict[str, Goals]:
    """match_id -> [(minute, stoppage, side), ...].

    Stoppage is carried so the timeline can be written losslessly; the aggregate windows
    ignore it, because a goal at 45+3' is minute 45 for every window here and adding the
    stoppage would push it past a 45 boundary it belongs inside.
    """

    goals_df = pd.read_csv(goals_path, usecols=["match_id", "minute", "stoppage", "side"])
    store: dict[str, Goals] = {}
    for match_id, minute, stoppage, side in zip(
        goals_df["match_id"].astype(str),
        goals_df["minute"],
        goals_df["stoppage"],
        goals_df["side"],
        strict=True,
    ):
        store.setdefault(match_id, []).append((int(minute), int(stoppage), str(side)))

    return store


def build(
    detail_df: pd.DataFrame,
    store: dict[str, Goals],
    depth: int = MATCHES_PER_SECTION,
) -> pd.DataFrame:
    """One row per fixture: the aggregates for all three sections, plus every timeline."""

    return history.build_frame(
        detail_df,
        depth,
        FEATURE_SUFFIXES,
        ((TIMELINE_FIELD, _timeline),),
        lambda prefix, row: _usable_goals(detail_df, store, prefix, row),
        _rates,
    )


def _usable_goals(
    detail_df: pd.DataFrame, store: dict[str, Goals], prefix: str, row: int
) -> Goals | None:
    """One history match's goals, oriented to the subject team. None when unusable.

    Unusable means: not scraped, out of scope (`domain/scope.py` — friendlies carry no
    timings, pre-2023 pages are truncated), the subject's venue is unknown, or the stored
    goals do not reproduce the score the detail page records for that match. Roughly 0.5%
    fail that last test, and including them would be worse than dropping them: a match
    where two of four goals were found reports a late-goal rate computed from half the
    evidence, which is a wrong number rather than a missing one.
    """

    match_id = history.match_key(detail_df, prefix, row)
    if match_id is None or match_id not in store:
        return None
    is_home = history.subject_is_home(detail_df, prefix, row)
    if is_home is None:
        return None

    goals = store[match_id]
    counted_home = sum(1 for _, _, side in goals if side == "home")
    if not history.score_matches(detail_df, prefix, row, counted_home, len(goals) - counted_home):
        return None

    return [
        (minute, stoppage, "GF" if (side == "home") == is_home else "GA")
        for minute, stoppage, side in goals
    ]


def _timeline(goals: Goals | None) -> str:
    """ "15GA;18GF;45+3GF" — lossless, subject-oriented, ordered as scored.

    Empty when the match had no usable timings; `GOALLESS` when it was usable and simply
    had no goals. Those are different facts and an empty cell cannot carry both.
    """

    if goals is None:
        return ""
    if not goals:
        return GOALLESS

    return ";".join(
        f"{minute}+{stoppage}{tag}" if stoppage else f"{minute}{tag}"
        for minute, stoppage, tag in goals
    )


def _rates(blocks: list[Goals | None]) -> dict[str, float]:
    """Fold one fixture's usable history matches into timing rates."""

    scored = [minute for b in blocks if b for minute, _, tag in b if tag == "GF"]
    conceded = [minute for b in blocks if b for minute, _, tag in b if tag == "GA"]

    rates: dict[str, float] = {
        "goal_minute_avg": float(np.mean(scored)) if scored else float("nan"),
        "conceded_minute_avg": float(np.mean(conceded)) if conceded else float("nan"),
        "late_goal_rate": _share(scored, lambda minute: minute >= LATE_MINUTE),
        "late_conceded_rate": _share(conceded, lambda minute: minute >= LATE_MINUTE),
        "conceded_pre_ht_rate": _share(conceded, lambda minute: PRE_HT_FROM <= minute <= PRE_HT_TO),
        "goals_seen": float(len(scored) + len(conceded)),
    }

    for minutes, direction in ((scored, "gf"), (conceded, "ga")):
        for lo, hi in BUCKETS:
            rates[f"{direction}_{lo:02d}_{hi}"] = _share(
                minutes, lambda minute, lo=lo, hi=hi: lo <= minute <= hi
            )

    return rates


def _share(minutes: list[int], predicate: Any) -> float:
    """Share of `minutes` satisfying `predicate`; NaN when there is nothing to divide by.

    NaN rather than 0.0 on an empty list, so "this team conceded no late goals" is not
    confused with "we have no timings for this team".
    """

    if not minutes:
        return float("nan")
    return float(sum(1 for m in minutes if predicate(m)) / len(minutes))
