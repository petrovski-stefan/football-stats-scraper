"""Checks for the global goal-timing store.

Unlike the other validator modules this one has a *free oracle*. The corpus already holds
an independently scraped half-time and full-time score for every league match, so the goal
rows reconcile against them with no external source:

  - all goals must reproduce the full-time score, and
  - **goals with `minute <= 45` must reproduce the half-time score.**

The second is the one that tests the *minute* rather than the count. A goal at 45+3'
belongs to the first half and one at 46' does not; mishandle stoppage and the half-time
reconciliation fails loudly on every such match. Chelsea 1-0 Fulham, whose only goal is a
penalty at 45+3', is exactly that case.

Matches pulled in only because a fixture's history referenced them -- cup ties, European
games, other leagues -- have no stored score here, so only the internal checks apply to
them. That asymmetry is reported rather than hidden.
"""

import pandas as pd

from qa import universal
from qa.report import Report

MAX_MINUTE = 90  # regulation only; extra time is dropped at parse time
MAX_STOPPAGE = 20
HALF_TIME = 45
# Band for the second-half share of goals, set from an outside corpus that was dropped on
# 2026-10-13. Re-derive it from our own HT and FT scores at plan step P5.
SECOND_HALF_SHARE_MIN = 0.52
SECOND_HALF_SHARE_MAX = 0.59
MIN_GOALS_FOR_SHARE = 500
# Share of matches allowed to disagree on the half-time split alone (full time reconciles,
# the sequence is monotone, one goal sits on the wrong side of 45'). That is nowgoal
# contradicting its own half-time score, not a parse error, and it ran at 0.17% on
# 2026-09-22. The tolerance stays tight on purpose: a stoppage-parsing regression would
# push every `45+N` goal into the second half -- 2-3% of all goals -- and blow straight
# through it. The full-time check has no tolerance at all.
HT_ONLY_TOLERANCE = 0.005


def validate(r: Report, goals: pd.DataFrame, done: pd.DataFrame, truth: pd.DataFrame) -> None:
    """Run every goal-store check.

    `truth` carries match_id plus the ht/ft goal columns for every match whose score is
    known independently — the corpus itself *and* every match referenced by a fixture's
    history, whose score the detail page records. That second source is what makes the
    whole store checkable rather than just the ~20% that are corpus matches.
    """
    universal.check_attempt_log(r, goals, done, "n_goals")
    _check_columns(r, goals)
    _check_sequences(r, goals)
    _check_against_truth(r, goals, done, truth)
    _check_half_split(r, goals)


def _check_columns(r: Report, goals: pd.DataFrame) -> None:
    """Per-row ranges, independent of any match context."""
    if goals.empty:
        return

    bad_minute = goals[(goals["minute"] < 1) | (goals["minute"] > MAX_MINUTE)]
    r.check(bad_minute.empty, f"{len(bad_minute)} goals with a minute outside 1..{MAX_MINUTE}")

    bad_stop = goals[(goals["stoppage"] < 0) | (goals["stoppage"] > MAX_STOPPAGE)]
    r.check(bad_stop.empty, f"{len(bad_stop)} goals with stoppage outside 0..{MAX_STOPPAGE}")

    bad_side = goals[~goals["side"].isin(["home", "away"])]
    r.check(bad_side.empty, f"{len(bad_side)} goals with a side that is neither home nor away")


def _check_sequences(r: Report, goals: pd.DataFrame) -> None:
    """Per-match invariants that hold with or without a stored score."""
    if goals.empty:
        return

    offenders: dict[str, list[str]] = {"order": [], "index": [], "side": []}
    for match_id, group in goals.groupby(goals["match_id"].astype(str)):
        _inspect_match(str(match_id), group, offenders)

    r.check(not offenders["order"], f"{len(offenders['order'])} matches not ordered by minute")
    r.check(not offenders["index"], f"{len(offenders['index'])} matches with a broken goal_index")
    r.check(
        not offenders["side"],
        f"{len(offenders['side'])} matches where `side` disagrees with which score advanced",
    )


def _inspect_match(match_id: str, group: pd.DataFrame, offenders: dict[str, list[str]]) -> None:
    """Order, index, and side/score agreement within one match."""
    ordered = group.sort_values("goal_index")
    minutes = [int(v) for v in ordered["minute"]]
    stoppages = [int(v) for v in ordered["stoppage"]]
    indices = [int(v) for v in ordered["goal_index"]]
    sides = [str(v) for v in ordered["side"]]
    homes = [int(v) for v in ordered["home_score_after"]]
    aways = [int(v) for v in ordered["away_score_after"]]

    keys = list(zip(minutes, stoppages, strict=True))
    if keys != sorted(keys):
        offenders["order"].append(match_id)

    if indices != list(range(1, len(indices) + 1)):
        offenders["index"].append(match_id)

    home = away = 0
    for side, new_home, new_away in zip(sides, homes, aways, strict=True):
        expected = "home" if new_home == home + 1 else "away"
        if side != expected or abs(new_home - home) + abs(new_away - away) != 1:
            offenders["side"].append(match_id)
            return
        home, away = new_home, new_away


def _check_against_truth(
    r: Report, goals: pd.DataFrame, done: pd.DataFrame, truth: pd.DataFrame
) -> None:
    """The oracle: reconcile the count and the half-time split against known scores."""
    if truth.empty:
        return

    scraped = set(done["match_id"].astype(str))
    truth_ids = truth["match_id"].astype(str)
    known = truth[truth_ids.isin(scraped)]
    unchecked = len(scraped) - len(known)
    r.check(
        unchecked == 0,
        f"{unchecked} scraped matches have no independently known score to check against",
    )

    if known.empty:
        return

    totals = _per_match_totals(goals)
    ids = [str(v) for v in known["match_id"]]
    ft_home = [int(v) for v in known["ft_home_goals"]]
    ft_away = [int(v) for v in known["ft_away_goals"]]
    ht_home = [int(v) for v in known["ht_home_goals"]]
    ht_away = [int(v) for v in known["ht_away_goals"]]

    ft_bad: list[str] = []
    ht_bad: list[str] = []
    for match_id, fh, fa, hh, ha in zip(ids, ft_home, ft_away, ht_home, ht_away, strict=True):
        got = totals.get(match_id, (0, 0, 0, 0))
        if (got[0], got[1]) != (fh, fa):
            ft_bad.append(match_id)
        if (got[2], got[3]) != (hh, ha):
            ht_bad.append(match_id)

    n = len(ids)
    r.check(not ft_bad, f"{len(ft_bad)}/{n} matches where goals do not reproduce the FT score")

    # Half-time disagreements where full time reconciles are the source contradicting
    # itself; the ones where full time ALSO fails are already reported above.
    ht_only = [m for m in ht_bad if m not in set(ft_bad)]
    share = len(ht_only) / n
    r.check(
        share <= HT_ONLY_TOLERANCE,
        f"{len(ht_only)}/{n} ({share:.2%}) matches where full time reconciles but the "
        f"half-time split does not — above the {HT_ONLY_TOLERANCE:.1%} tolerance, which "
        f"means a stoppage-parsing regression, not source noise: {sorted(ht_only)[:5]}",
    )
    print(f"    (info) reconciled {n - len(ft_bad)}/{n} FT, {n - len(ht_bad)}/{n} HT")
    if ht_only:
        print(
            f"    (info) {len(ht_only)} half-time-only disagreements ({share:.2%}, "
            f"tolerance {HT_ONLY_TOLERANCE:.1%}) — nowgoal disagreeing with its own HT score"
        )


def _per_match_totals(goals: pd.DataFrame) -> dict[str, tuple[int, int, int, int]]:
    """match_id -> (ft_home, ft_away, ht_home, ht_away), counted from the goal rows."""
    if goals.empty:
        return {}

    is_home = goals["side"].eq("home")
    first_half = goals["minute"].le(HALF_TIME)
    frame = pd.DataFrame(
        {
            "match_id": goals["match_id"].astype(str),
            "ft_home": is_home.astype(int),
            "ft_away": (~is_home).astype(int),
            "ht_home": (is_home & first_half).astype(int),
            "ht_away": (~is_home & first_half).astype(int),
        }
    )

    summed = frame.groupby("match_id")[["ft_home", "ft_away", "ht_home", "ht_away"]].sum()
    return {
        str(match_id): (int(row[0]), int(row[1]), int(row[2]), int(row[3]))
        for match_id, row in zip(summed.index, summed.to_numpy(), strict=True)
    }


def second_half_share(goals: pd.DataFrame) -> float | None:
    """Share of goals scored after half-time.

    The same quantity is computable from the stored ht/ft columns with no
    minute data at all, so agreement between the two is a real check, not a tautology.
    """
    if goals.empty:
        return None
    return float((~goals["minute"].le(HALF_TIME)).mean())


def _check_half_split(r: Report, goals: pd.DataFrame) -> None:
    """Tier 2: the corpus-level second-half share, against an independent measurement.

    Only meaningful once enough goals have accumulated, so below `MIN_GOALS_FOR_SHARE`
    this reports the figure without judging it — a handful of matches says nothing about
    a population rate.
    """
    share = second_half_share(goals)
    if share is None:
        return
    if len(goals) < MIN_GOALS_FOR_SHARE:
        print(f"    (info) 2H goal share {share:.1%} on {len(goals)} goals (too few to judge)")
        return

    print(f"    (info) second-half goal share {share:.1%}")
    r.check(
        SECOND_HALF_SHARE_MIN <= share <= SECOND_HALF_SHARE_MAX,
        f"second-half goal share {share:.1%} outside the {SECOND_HALF_SHARE_MIN:.1%}-"
        f"{SECOND_HALF_SHARE_MAX:.1%} band — "
        f"minutes may be systematically mis-assigned to a half",
    )
