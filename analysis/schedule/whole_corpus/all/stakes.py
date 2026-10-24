"""Does the team behind at half-time come back more often when the result matters to it?

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/STAKES.md`. The comparison of the stakes test
frozen on 2026-10-12 (its plan is in the doc's Method), measured again on the corpus of the
day: one row per match with a team behind at half-time, two flags of what is at stake for
that team (S3.11-13), and the Mantel-Haenszel odds ratio of its win, flagged against not,
over strata of league-season x fifth of its opening win chance x deficit. Then the same
flags read against the odds yardstick (`analysis/methods/yardstick.py`). Exploratory: the
frozen test ran once; this is not a second test.

Run: `uv run python -m analysis.schedule.whole_corpus.all.stakes`
"""

from collections.abc import Callable

import numpy as np
import pandas as pd

from analysis import corpus, report, stats
from analysis.methods import yardstick

LATE = 5  # F1: matches left, this one included
CLOSE = 3  # F1: points behind the nearest team above
FELL = 2  # F2: places lost since the odds opened
FIFTHS = (0.2, 0.4, 0.6, 0.8)
ALPHA = 0.05
SIDES = (("home", "away"), ("away", "home"))


def fifth_cuts(matches_df: pd.DataFrame) -> np.ndarray:
    """The cut points of the fifths of the opening win chance: quantiles of the home and away
    chances (S2.17, S2.19) together, over every match with odds. No result is read."""

    priced_df = matches_df.dropna(subset=["s2_mkt_p_home", "s2_mkt_p_away"])
    chances = np.concatenate(
        [priced_df["s2_mkt_p_home"].to_numpy(float), priced_df["s2_mkt_p_away"].to_numpy(float)]
    )
    return np.asarray(np.quantile(chances, FIFTHS))


def trailing_states(matches_df: pd.DataFrame, cuts: np.ndarray) -> pd.DataFrame:
    """One row per match with a team behind at half-time and an opening win chance for it:
    that team's chance, deficit, win, stake fields and stratum, on the match's index."""

    parts = []
    for side, other in SIDES:
        side_trailing_df = matches_df[
            matches_df[f"s1_ht_{side}_goals"] < matches_df[f"s1_ht_{other}_goals"]
        ]
        deficit = side_trailing_df[f"s1_ht_{other}_goals"] - side_trailing_df[f"s1_ht_{side}_goals"]

        parts.append(
            pd.DataFrame(
                {
                    "cluster": side_trailing_df["s1_league_id"].astype(str)
                    + " "
                    + side_trailing_df["s1_season"],
                    "season_cohort": side_trailing_df["season_cohort"],
                    "p_win": side_trailing_df[f"s2_mkt_p_{side}"],
                    "deficit": np.where(deficit >= 2, "2+", "1"),
                    "win": side_trailing_df[f"s2_is_comeback_{side}"].astype(bool),
                    "left": side_trailing_df[f"s3_{side}_pre_matches_left"],
                    "above": side_trailing_df[f"s3_{side}_pre_pts_to_above"],
                    "change": side_trailing_df[f"s3_{side}_rank_change_since_open"],
                },
                index=side_trailing_df.index,
            )
        )

    states_df = pd.concat(parts).sort_index().dropna(subset=["p_win"])
    fifth = np.searchsorted(cuts, states_df["p_win"].to_numpy(float), side="right")
    states_df["stratum"] = (
        states_df["cluster"] + "|" + fifth.astype(str) + "|" + states_df["deficit"]
    )
    return states_df


def late_and_close(states_df: pd.DataFrame) -> pd.DataFrame:
    """F1: `LATE` or fewer matches left and `CLOSE` or fewer points behind the team above.
    A team with no team above is not flagged."""

    return states_df.assign(flag=(states_df["left"] <= LATE) & (states_df["above"] <= CLOSE))


def fell_since_open(states_df: pd.DataFrame) -> pd.DataFrame:
    """F2: `FELL` or more places lost since the odds opened. A row with no rank change (the
    first rounds) is left out."""

    with_change_df = states_df.dropna(subset=["change"])
    return with_change_df.assign(flag=with_change_df["change"] >= FELL)


FLAGS: tuple[tuple[str, Callable[[pd.DataFrame], pd.DataFrame]], ...] = (
    (f"F1 late and close (<= {LATE} left, <= {CLOSE} pts behind the team above)", late_and_close),
    (f"F2 fell {FELL}+ places since the odds opened", fell_since_open),
)


def mh_row(label: str, states_df: pd.DataFrame) -> dict[str, object]:
    """The Mantel-Haenszel comparison of one set of flagged states, as a row."""

    result = stats.mantel_haenszel(states_df["flag"], states_df["win"], states_df["stratum"])

    return {
        "states": label,
        "flagged": result.flagged,
        "wins": result.flagged_events,
        "rate": result.flagged_events / result.flagged,
        "rest": result.rest,
        "rest wins": result.rest_events,
        "rest rate": result.rest_events / result.rest,
        "MH OR": result.odds_ratio,
        "low": result.low,
        "high": result.high,
        "CMH p": result.p_value,
        "strata": result.strata,
    }


def mh_table(states_df: pd.DataFrame) -> pd.DataFrame:
    """One row per season cohort, then all states pooled."""

    rows = [
        mh_row(str(cohort), cohort_states_df)
        for cohort, cohort_states_df in states_df.groupby("season_cohort")
    ]
    return pd.DataFrame([*rows, mh_row("pooled", states_df)])


def the_bar(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """The bar of the frozen plan, read on this run: the pooled CMH p after Holm over the
    flags below `ALPHA`, and the odds ratio on the same side of 1 in both cohorts."""

    pooled = [float(mh_table_df["CMH p"].iloc[-1]) for mh_table_df in tables.values()]

    rows = []
    for (name, mh_table_df), adjusted in zip(tables.items(), stats.holm(pooled), strict=True):
        first, second = (float(value) for value in mh_table_df["MH OR"].iloc[:2])
        same_side = (first > 1) == (second > 1)

        rows.append(
            {
                "flag": name,
                "Holm p": adjusted,
                "OR 2024": first,
                "OR 2025": second,
                "same side": same_side,
                "met": adjusted < ALPHA and same_side,
            }
        )

    return pd.DataFrame(rows)


def against_odds(states_df: pd.DataFrame, chance: "pd.Series[float]") -> pd.DataFrame:
    """The wins of the flagged and of the other states against the yardstick's chance that
    the team behind wins from that half-time score (O/E), with intervals over
    league-seasons. The states without a yardstick chance are left out."""

    with_expected_df = states_df.assign(expected=chance).dropna(subset=["expected"])
    with_expected_df = with_expected_df.assign(win=with_expected_df["win"].astype(float))

    rows = []
    for flagged, label in ((True, "flagged"), (False, "rest")):
        ratio = stats.observed_expected(
            with_expected_df[with_expected_df["flag"] == flagged], "win", "expected"
        )
        rows.append({"states": label, **ratio})

    return pd.DataFrame(rows)


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    cuts = fifth_cuts(matches_df)
    states_df = trailing_states(matches_df, cuts)

    trailing = int((matches_df["s1_ht_home_goals"] != matches_df["s1_ht_away_goals"]).sum())
    print(f"fifth cut points (opening win chance): {np.round(cuts, 4).tolist()}")
    print(
        f"trailing states: {len(states_df):,} of {trailing:,} decisive half-times; "
        f"wins {int(states_df['win'].sum()):,} ({states_df['win'].mean():.4f})"
    )

    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid())
    tables = {}
    for name, flag in FLAGS:
        flagged_df = flag(states_df)
        print(
            f"\n{name}: {len(flagged_df):,} states ({len(states_df) - len(flagged_df):,} left out)"
        )

        tables[name] = mh_table(flagged_df)
        report.show(f"{name}: Mantel-Haenszel", tables[name])
        report.show(
            f"{name}: against the odds", against_odds(flagged_df, yardstick_df["m_completion"])
        )

    report.show("The bar of the frozen plan, on this run", the_bar(tables))


if __name__ == "__main__":
    main()
