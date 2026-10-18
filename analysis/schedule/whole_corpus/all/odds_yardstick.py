"""The odds yardstick on the whole corpus, all matches pooled.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ODDS_YARDSTICK.md`. Prints the corpus line; the
fit; observed against expected goals, comebacks, decisive half-times, completions, 7+ goals,
0-0 and 1-1, for all matches and per season cohort; the same by the favourite's win chance
and by expected goals; where the comeback excess sits; the comebacks by win chance and
expected goals together; and checks of two assumptions of the yardstick: one first-half
share for every match, and Shin's margin removal.

Run: `uv run python -m analysis.schedule.whole_corpus.all.odds_yardstick`
"""

import numpy as np
import pandas as pd

from analysis import corpus, report, stats
from analysis.methods import yardstick

# (observed column, expected column, label): each row of an observed / expected table.
# No row per half: one first-half share, taken from these goals, splits the expected goals,
# so the O/E of each half equals the O/E of all goals by construction.
GOALS = (
    ("goals", "m_goals", "goals per match"),
    ("goals_home", "lam_home", "home goals"),
    ("goals_away", "lam_away", "away goals"),
)
POOR_FIT = 0.05  # a fit error above this is listed
EVENTS = (
    ("is_comeback", "m_cb", "comeback, either side"),
    ("is_comeback_home", "m_cb_home", "comeback, home side"),
    ("is_comeback_away", "m_cb_away", "comeback, away side"),
    ("ht_decisive", "m_ht_decisive", "decisive half-time (link 1)"),
    ("is_comeback", "m_completion", "completion from the HT score (link 2)"),
    ("seven", "m_seven", "7+ goals"),
    ("is00", "m_00", "0-0"),
    ("is11", "m_11", "1-1"),
)
BANDED = (
    ("goals", "m_goals", "goals per match"),
    ("is_comeback", "m_cb", "comeback"),
    ("ht_decisive", "m_ht_decisive", "link 1"),
    ("is_comeback", "m_completion", "link 2"),
    ("seven", "m_seven", "7+ goals"),
    ("goals_1h", "goals", "first-half share (observed / all goals)"),
)
SHARE_SHIFT = 0.02
# The favourite's Shin win chance, and the model's expected goals per match.
FAV_EDGES = (0.0, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70, 1.0)
TOTAL_EDGES = (0.0, 2.2, 2.5, 2.8, 3.1, 3.4, 10.0)


def banded(
    frame: pd.DataFrame,
    column: str,
    edges: tuple[float, ...],
    rows: tuple[tuple[str, str, str], ...],
) -> pd.DataFrame:
    """The same rows inside each band of `column`."""
    bands = pd.cut(frame[column], edges)
    table = [
        {"band": str(band), "quantity": label, **stats.observed_expected(group, o, e)}
        for band, group in frame.groupby(bands, observed=True)
        for o, e, label in rows
    ]
    return pd.DataFrame(table)


def trailer_splits(frame: pd.DataFrame) -> dict[str, "pd.Series[bool]"]:
    """Masks over the decisive half-times: who is behind, by how much, and where."""
    margin = frame["ht_margin"]
    home_behind, away_behind = margin < 0, margin > 0
    fav_behind = (home_behind & frame["fav_is_home"]) | (away_behind & ~frame["fav_is_home"])
    decisive = home_behind | away_behind
    return {
        "favourite behind": decisive & fav_behind,
        "underdog behind": decisive & ~fav_behind,
        "behind by 1": margin.abs() == 1,
        "behind by 2 or more": margin.abs() >= 2,
        "home side behind": home_behind,
        "away side behind": away_behind,
    }


def excess_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Completions observed against expected from the HT score, per trailer split."""
    table = [
        {"split": name, **stats.observed_expected(frame[mask], "is_comeback", "m_completion")}
        for name, mask in trailer_splits(frame).items()
    ]
    return pd.DataFrame(table)


def side_goals(frame: pd.DataFrame) -> pd.DataFrame:
    """The favourite's and the underdog's goals, in each half and in all."""
    home = frame["fav_is_home"]
    return pd.DataFrame(
        {
            "fav_1h": np.where(home, frame["goals_home_1h"], frame["goals_away_1h"]),
            "fav": np.where(home, frame["goals_home"], frame["goals_away"]),
            "dog_1h": np.where(home, frame["goals_away_1h"], frame["goals_home_1h"]),
            "dog": np.where(home, frame["goals_away"], frame["goals_home"]),
            "cluster": frame["cluster"],
        },
        index=frame.index,
    )


def pivot(frame: pd.DataFrame) -> pd.DataFrame:
    """Comebacks by the favourite's win chance and the expected goals, both banded."""
    keys = [pd.cut(frame["fav_p"], FAV_EDGES), pd.cut(frame["m_goals"], TOTAL_EDGES)]
    grouped = frame.groupby(keys, observed=True)
    table = pd.DataFrame(
        {
            "n": grouped.size(),
            "observed": grouped["is_comeback"].sum(),
            "expected": grouped["m_cb"].sum(),
        }
    )
    table["oe"] = table["observed"] / table["expected"]
    return table.reset_index().rename(columns={"fav_p": "win chance", "m_goals": "expected goals"})


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    grid = yardstick.build_grid()
    share = yardstick.first_half_share(yardstick.priced(matches))
    frame = yardstick.frame(matches, grid, share=share)
    print(f"Priced: {len(frame):,} of {len(matches):,} matches have both opening markets")
    error = frame["fit_error"].quantile([0.5, 0.9, 0.99, 1.0])
    print(
        "fit error (probability distance): "
        + ", ".join(f"q{q:g} {v:.4f}" for q, v in error.items())
    )
    poor = frame[frame["fit_error"] > POOR_FIT].sort_values("fit_error", ascending=False)
    print(f"fit error above {POOR_FIT}: {len(poor)} matches")
    print(
        poor[["match_id", "s1_league_name", "s1_season", "fit_error"]]
        .head(5)
        .to_string(index=False)
    )
    print(f"first-half share of goals: {share:.4f}")
    print(
        f"observed mean goals per match: {frame['goals'].mean():.4f} (first half "
        f"{frame['goals_1h'].mean():.4f}, second half {frame['goals_2h'].mean():.4f})"
    )

    report.show(
        "Goals, observed / expected, all matches", stats.observed_expected_table(frame, GOALS)
    )
    report.show(
        "Events, observed / expected, all matches", stats.observed_expected_table(frame, EVENTS)
    )
    for cohort, group in frame.groupby("season_cohort"):
        report.show(
            f"Events, season cohort {cohort} ({len(group):,} matches)",
            stats.observed_expected_table(group, EVENTS),
        )
        report.show(
            f"Goals, season cohort {cohort}", stats.observed_expected_table(group, GOALS[:1])
        )

    report.show("By the favourite's win chance (Shin)", banded(frame, "fav_p", FAV_EDGES, BANDED))
    report.show("By expected goals per match", banded(frame, "m_goals", TOTAL_EDGES, BANDED))
    report.show("Where the comeback excess sits (decisive half-times only)", excess_table(frame))
    report.show("Comebacks by win chance and expected goals", pivot(frame))

    sides = side_goals(frame)
    report.show(
        "First-half share of each side's goals",
        pd.DataFrame(
            [
                {"side": "favourite", **stats.observed_expected(sides, "fav_1h", "fav")},
                {"side": "underdog", **stats.observed_expected(sides, "dog_1h", "dog")},
            ]
        ),
    )
    report.show(
        "First-half share per season cohort",
        pd.DataFrame(
            [
                {"cohort": cohort, **stats.observed_expected(group, "goals_1h", "goals")}
                for cohort, group in frame.groupby("season_cohort")
            ]
        ),
    )
    rows = []
    for shift in (-SHARE_SHIFT, 0.0, SHARE_SHIFT):
        model = yardstick.implied(
            frame["lam_home"].to_numpy(), frame["lam_away"].to_numpy(), share + shift
        )
        expected = float(model["m_cb"].sum())
        rows.append(
            {
                "share": share + shift,
                "expected comebacks": expected,
                "oe": frame["is_comeback"].sum() / expected,
            }
        )
    report.show("Comebacks under other first-half shares", pd.DataFrame(rows))

    flat = yardstick.frame(matches, grid, share=share, proportional=True)
    report.show(
        "Proportional margin removal in place of Shin",
        stats.observed_expected_table(flat, EVENTS[:1] + EVENTS[5:6]),
    )


if __name__ == "__main__":
    main()
