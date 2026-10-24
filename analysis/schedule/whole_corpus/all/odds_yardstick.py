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
# The favourite's Shin win chance. The bands of expected goals are `yardstick.TOTAL_EDGES`.
FAV_EDGES = (0.0, 0.40, 0.45, 0.50, 0.55, 0.60, 0.70, 1.0)


def banded(
    yardstick_df: pd.DataFrame,
    column: str,
    edges: tuple[float, ...],
    rows: tuple[tuple[str, str, str], ...],
) -> pd.DataFrame:
    """The same rows inside each band of `column`."""

    bands = pd.cut(yardstick_df[column], edges)
    table = [
        {
            "band": str(band),
            "quantity": label,
            **stats.observed_expected(band_df, observed_column, expected_column),
        }
        for band, band_df in yardstick_df.groupby(bands, observed=True)
        for observed_column, expected_column, label in rows
    ]
    return pd.DataFrame(table)


def trailer_splits(yardstick_df: pd.DataFrame) -> dict[str, "pd.Series[bool]"]:
    """Masks over the decisive half-times: who is behind, by how much, and where."""

    margin = yardstick_df["ht_margin"]
    home_behind, away_behind = margin < 0, margin > 0
    fav_behind = (home_behind & yardstick_df["fav_is_home"]) | (
        away_behind & ~yardstick_df["fav_is_home"]
    )
    decisive = home_behind | away_behind

    return {
        "favourite behind": decisive & fav_behind,
        "underdog behind": decisive & ~fav_behind,
        "behind by 1": margin.abs() == 1,
        "behind by 2 or more": margin.abs() >= 2,
        "home side behind": home_behind,
        "away side behind": away_behind,
    }


def excess_table(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """Completions observed against expected from the HT score, per trailer split."""

    table = [
        {
            "split": name,
            **stats.observed_expected(yardstick_df[mask], "is_comeback", "m_completion"),
        }
        for name, mask in trailer_splits(yardstick_df).items()
    ]
    return pd.DataFrame(table)


def side_goals(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """The favourite's and the underdog's goals, in each half and in all."""

    home = yardstick_df["fav_is_home"]

    return pd.DataFrame(
        {
            "fav_1h": np.where(home, yardstick_df["goals_home_1h"], yardstick_df["goals_away_1h"]),
            "fav": np.where(home, yardstick_df["goals_home"], yardstick_df["goals_away"]),
            "dog_1h": np.where(home, yardstick_df["goals_away_1h"], yardstick_df["goals_home_1h"]),
            "dog": np.where(home, yardstick_df["goals_away"], yardstick_df["goals_home"]),
            "cluster": yardstick_df["cluster"],
        },
        index=yardstick_df.index,
    )


def pivot(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """Comebacks by the favourite's win chance and the expected goals, both banded."""

    keys = [
        pd.cut(yardstick_df["fav_p"], FAV_EDGES),
        pd.cut(yardstick_df["m_goals"], yardstick.TOTAL_EDGES),
    ]
    grouped = yardstick_df.groupby(keys, observed=True)

    pivot_df = pd.DataFrame(
        {
            "n": grouped.size(),
            "observed": grouped["is_comeback"].sum(),
            "expected": grouped["m_cb"].sum(),
        }
    )

    pivot_df["oe"] = pivot_df["observed"] / pivot_df["expected"]
    return pivot_df.reset_index().rename(
        columns={"fav_p": "win chance", "m_goals": "expected goals"}
    )


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    grid = yardstick.build_grid()
    share = yardstick.first_half_share(yardstick.priced(matches_df))
    yardstick_df = yardstick.frame(matches_df, grid, share=share)
    print(f"Priced: {len(yardstick_df):,} of {len(matches_df):,} matches have both opening markets")

    error = yardstick_df["fit_error"].quantile([0.5, 0.9, 0.99, 1.0])
    print(
        "fit error (probability distance): "
        + ", ".join(f"q{q:g} {v:.4f}" for q, v in error.items())
    )

    poor_fit_df = yardstick_df[yardstick_df["fit_error"] > POOR_FIT].sort_values(
        "fit_error", ascending=False
    )
    print(f"fit error above {POOR_FIT}: {len(poor_fit_df)} matches")
    print(
        poor_fit_df[["match_id", "s1_league_name", "s1_season", "fit_error"]]
        .head(5)
        .to_string(index=False)
    )

    print(f"first-half share of goals: {share:.4f}")
    print(
        f"observed mean goals per match: {yardstick_df['goals'].mean():.4f} (first half "
        f"{yardstick_df['goals_1h'].mean():.4f}, second half {yardstick_df['goals_2h'].mean():.4f})"
    )

    report.show(
        "Goals, observed / expected, all matches",
        stats.observed_expected_table(yardstick_df, GOALS),
    )
    report.show(
        "Events, observed / expected, all matches",
        stats.observed_expected_table(yardstick_df, EVENTS),
    )
    for cohort, cohort_df in yardstick_df.groupby("season_cohort"):
        report.show(
            f"Events, season cohort {cohort} ({len(cohort_df):,} matches)",
            stats.observed_expected_table(cohort_df, EVENTS),
        )
        report.show(
            f"Goals, season cohort {cohort}", stats.observed_expected_table(cohort_df, GOALS[:1])
        )

    report.show(
        "By the favourite's win chance (Shin)", banded(yardstick_df, "fav_p", FAV_EDGES, BANDED)
    )
    report.show(
        "By expected goals per match",
        banded(yardstick_df, "m_goals", yardstick.TOTAL_EDGES, BANDED),
    )
    report.show(
        "Where the comeback excess sits (decisive half-times only)", excess_table(yardstick_df)
    )
    report.show("Comebacks by win chance and expected goals", pivot(yardstick_df))

    side_goals_df = side_goals(yardstick_df)
    report.show(
        "First-half share of each side's goals",
        pd.DataFrame(
            [
                {"side": "favourite", **stats.observed_expected(side_goals_df, "fav_1h", "fav")},
                {"side": "underdog", **stats.observed_expected(side_goals_df, "dog_1h", "dog")},
            ]
        ),
    )
    report.show(
        "First-half share per season cohort",
        pd.DataFrame(
            [
                {"cohort": cohort, **stats.observed_expected(cohort_df, "goals_1h", "goals")}
                for cohort, cohort_df in yardstick_df.groupby("season_cohort")
            ]
        ),
    )

    rows = []
    for shift in (-SHARE_SHIFT, 0.0, SHARE_SHIFT):
        implied_df = yardstick.implied(
            yardstick_df["lam_home"].to_numpy(), yardstick_df["lam_away"].to_numpy(), share + shift
        )

        expected = float(implied_df["m_cb"].sum())
        rows.append(
            {
                "share": share + shift,
                "expected comebacks": expected,
                "oe": yardstick_df["is_comeback"].sum() / expected,
            }
        )

    report.show("Comebacks under other first-half shares", pd.DataFrame(rows))

    proportional_df = yardstick.frame(matches_df, grid, share=share, proportional=True)
    report.show(
        "Proportional margin removal in place of Shin",
        stats.observed_expected_table(proportional_df, EVENTS[:1] + EVENTS[5:6]),
    )


if __name__ == "__main__":
    main()
