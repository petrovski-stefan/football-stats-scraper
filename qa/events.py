"""Checks for the global card/substitution store.

Unlike `qa/goals.py` this module has **no free oracle**. A goal reconciles against the
half-time and full-time scores the corpus already holds; a yellow card reconciles against
nothing, because no independently scraped column counts cards. So the checks here are of
two weaker kinds, and that limit is stated rather than papered over:

  - **structural** — ranges, allowed kinds, a contiguous per-match index, ordering, and a
    substitution having both of its players. These are exact.
  - **rate bands** — cards and substitutions per match against generous football-wide
    ranges. These cannot prove the data right; they catch the failures that would matter,
    which are wholesale ones: a side-detection regression putting every event on one team,
    a dedupe regression doubling every row, or a parser change dropping a whole kind.

The substitution cap is the sharpest structural check available. Five substitutions per
team is the competition limit in every league in the corpus, so a side showing more than
that in regulation means events are being attributed to the wrong team or counted twice —
exactly the two regressions most likely to be introduced here.
"""

import pandas as pd

from domain.event import EVENT_KINDS, RED_CARD, SUBSTITUTION, YELLOW_CARD
from domain.goal import MAX_MINUTE, MAX_STOPPAGE
from qa import universal
from qa.report import Report

# Five per team is the competition limit across the corpus; six is allowed only with extra
# time, which is dropped at parse time. Seven is a regression, never a fixture.
MAX_SUBS_PER_SIDE = 6

# Generous bands, per match, both teams combined. Deliberately wide: leagues differ a lot
# (northern European leagues book around 3 a match, southern ones closer to 5), so these
# are smoke tests for wholesale breakage, not claims about any particular league.
YELLOW_PER_MATCH = (2.0, 7.0)
RED_PER_MATCH = (0.0, 0.5)
SUBS_PER_MATCH = (4.0, 11.0)
MIN_MATCHES_FOR_RATES = 200

# Every league gives both teams the same substitution allowance, so the home/away split of
# substitutions is 50/50 by construction and does not vary by competition the way card
# rates do. That makes it the sharpest available test that side detection works: measured
# 49.95/50.05 on 8,052 substitutions, where the standard error is 0.56pp. The tolerance is
# ~9 SE — wide enough never to fire on noise, narrow enough that a wholesale side
# regression (which would push it toward 0 or 100) cannot pass.
#
# Cards deliberately get NO such check: away sides are genuinely cautioned more (measured
# +4.01pp on yellows here, a well-documented asymmetry) and the size of that varies by
# league, so a tolerance tight enough to be useful would fire on real football.
SUB_SIDE_TOLERANCE = 0.05
MIN_SUBS_FOR_SIDE_CHECK = 500


def validate(r: Report, events: pd.DataFrame, done: pd.DataFrame) -> None:
    """Run every event-store check."""
    universal.check_attempt_log(r, events, done, "n_events")
    _check_columns(r, events)
    _check_sequences(r, events)
    _check_rates(r, events, done)
    _check_sub_side_balance(r, events)


def _check_columns(r: Report, events: pd.DataFrame) -> None:
    """Per-row ranges, independent of any match context."""
    if events.empty:
        return
    bad_minute = events[(events["minute"] < 1) | (events["minute"] > MAX_MINUTE)]
    r.check(bad_minute.empty, f"{len(bad_minute)} events with a minute outside 1..{MAX_MINUTE}")

    bad_stop = events[(events["stoppage"] < 0) | (events["stoppage"] > MAX_STOPPAGE)]
    r.check(bad_stop.empty, f"{len(bad_stop)} events with stoppage outside 0..{MAX_STOPPAGE}")

    bad_side = events[~events["side"].isin(["home", "away"])]
    r.check(bad_side.empty, f"{len(bad_side)} events with a side that is neither home nor away")

    bad_kind = events[~events["kind"].isin(list(EVENT_KINDS))]
    r.check(bad_kind.empty, f"{len(bad_kind)} events with a kind outside {list(EVENT_KINDS)}")


def _check_sequences(r: Report, events: pd.DataFrame) -> None:
    """Per-match invariants."""
    if events.empty:
        return
    offenders: dict[str, list[str]] = {"order": [], "index": [], "subs": []}
    for match_id, group in events.groupby(events["match_id"].astype(str)):
        _inspect_match(str(match_id), group, offenders)
    r.check(not offenders["order"], f"{len(offenders['order'])} matches not ordered by minute")
    r.check(not offenders["index"], f"{len(offenders['index'])} matches with a broken event_index")
    r.check(
        not offenders["subs"],
        f"{len(offenders['subs'])} matches where one side made more than "
        f"{MAX_SUBS_PER_SIDE} substitutions — side detection or dedupe has regressed: "
        f"{sorted(offenders['subs'])[:5]}",
    )

    subs = events[events["kind"] == SUBSTITUTION]
    incomplete = subs[subs["player"].isna() | subs["player_off"].isna()]
    r.check(
        incomplete.empty,
        f"{len(incomplete)} substitutions missing the player coming on or off",
    )


def _inspect_match(match_id: str, group: pd.DataFrame, offenders: dict[str, list[str]]) -> None:
    """Order, index contiguity, and the per-side substitution cap within one match."""
    ordered = group.sort_values("event_index")
    keys = list(
        zip(
            [int(v) for v in ordered["minute"]],
            [int(v) for v in ordered["stoppage"]],
            strict=True,
        )
    )
    if keys != sorted(keys):
        offenders["order"].append(match_id)

    indices = [int(v) for v in ordered["event_index"]]
    if indices != list(range(1, len(indices) + 1)):
        offenders["index"].append(match_id)

    subs = ordered[ordered["kind"] == SUBSTITUTION]
    if not subs.empty and int(subs.groupby("side").size().max()) > MAX_SUBS_PER_SIDE:
        offenders["subs"].append(match_id)


def _check_rates(r: Report, events: pd.DataFrame, done: pd.DataFrame) -> None:
    """Corpus-level plausibility. Reports below the threshold rather than judging."""
    matches = len(done)
    if matches == 0:
        return
    rates = {
        YELLOW_CARD: (float((events["kind"] == YELLOW_CARD).sum()) / matches, YELLOW_PER_MATCH),
        RED_CARD: (float((events["kind"] == RED_CARD).sum()) / matches, RED_PER_MATCH),
        SUBSTITUTION: (float((events["kind"] == SUBSTITUTION).sum()) / matches, SUBS_PER_MATCH),
    }
    for kind, (rate, _) in rates.items():
        print(f"    (info) {kind:<14} {rate:.2f} per match")
    if matches < MIN_MATCHES_FOR_RATES:
        print(f"    (info) {matches} matches — too few to judge the rate bands")
        return
    for kind, (rate, (low, high)) in rates.items():
        r.check(
            low <= rate <= high,
            f"{kind} runs {rate:.2f} per match, outside the plausible {low:.2f}-{high:.2f} "
            f"band — a whole kind may be mis-parsed or duplicated",
        )


def _check_sub_side_balance(r: Report, events: pd.DataFrame) -> None:
    """Substitutions must split ~50/50 between home and away — see SUB_SIDE_TOLERANCE."""
    subs = events[events["kind"] == SUBSTITUTION]
    if len(subs) < MIN_SUBS_FOR_SIDE_CHECK:
        return
    away = float(subs["side"].eq("away").mean())
    print(f"    (info) substitution side split {1 - away:.2%} home / {away:.2%} away")
    r.check(
        abs(away - 0.5) <= SUB_SIDE_TOLERANCE,
        f"substitutions split {away:.1%} away, more than {SUB_SIDE_TOLERANCE:.0%} from the "
        f"50/50 every competition's equal allowance guarantees — side detection has broken",
    )
