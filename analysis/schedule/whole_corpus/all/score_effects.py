"""Second-half score effects on the whole corpus, all matches pooled.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/SCORE_EFFECTS.md`. Against the odds yardstick
(`ALL/ODDS_YARDSTICK.md`), prints each team's second-half goals by its half-time state: for
all matches, per season cohort, and for the favourite and the underdog. Then both teams'
second-half goals after each common half-time score, all second-half goals by first-half
goals, and how much of the comeback excess the measured second-half rates explain.

Run: `uv run python -m analysis.schedule.whole_corpus.all.score_effects`
"""

import numpy as np
import pandas as pd

from analysis import corpus, report, stats
from analysis.methods import yardstick

STATES = (
    "behind by 3+",
    "behind by 2",
    "behind by 1",
    "level",
    "ahead by 1",
    "ahead by 2",
    "ahead by 3+",
)
COMMON_SCORES = ((0, 0), (1, 0), (0, 1), (1, 1), (2, 0), (0, 2), (2, 1), (1, 2))
FIRST_HALF_CAP = 4  # first-half goal totals of 4 or more form one group


def state_of(margin: np.ndarray) -> np.ndarray:
    """A team's half-time state, from its own margin: its goals minus the other side's."""
    return np.asarray(np.array(STATES)[np.clip(margin, -3, 3).astype(int) + 3])


def team_halves(yardstick_df: pd.DataFrame, share: float) -> pd.DataFrame:
    """One row per team per match: its half-time state, and its observed and expected
    second-half goals. The two rows of a match share its league-season cluster."""
    sides = []
    for side, sign, favourite in (
        ("home", 1, yardstick_df["fav_is_home"]),
        ("away", -1, ~yardstick_df["fav_is_home"]),
    ):
        margin = sign * yardstick_df["ht_margin"].to_numpy()

        sides.append(
            pd.DataFrame(
                {
                    "state": state_of(margin),
                    "margin": margin,
                    "goals_2h": (
                        yardstick_df[f"goals_{side}"] - yardstick_df[f"goals_{side}_1h"]
                    ).to_numpy(),
                    "expected_2h": (1 - share) * yardstick_df[f"lam_{side}"].to_numpy(),
                    "is_favourite": favourite.to_numpy(),
                    "season_cohort": yardstick_df["season_cohort"].to_numpy(),
                    "cluster": yardstick_df["cluster"].to_numpy(),
                }
            )
        )

    return pd.concat(sides, ignore_index=True)


def by_state(team_halves_df: pd.DataFrame) -> pd.DataFrame:
    """Second-half goals O/E per half-time state, in the order of `STATES`."""
    table = [
        {"state": state, **stats.observed_expected(state_df, "goals_2h", "expected_2h")}
        for state in STATES
        if len(state_df := team_halves_df[team_halves_df["state"] == state])
    ]
    return pd.DataFrame(table)


def by_state_and_side(team_halves_df: pd.DataFrame) -> pd.DataFrame:
    """The same per state, for the favourite and for the underdog."""
    parts = []
    for name, mask in (
        ("favourite", team_halves_df["is_favourite"]),
        ("underdog", ~team_halves_df["is_favourite"]),
    ):
        side_states_df = by_state(team_halves_df[mask])
        side_states_df.insert(0, "side", name)
        parts.append(side_states_df)
    return pd.concat(parts, ignore_index=True)


def by_ht_score(yardstick_df: pd.DataFrame, share: float) -> pd.DataFrame:
    """Each side's second-half goals O/E after each common half-time score that occurred."""
    sides_df = yardstick_df.assign(
        home_2h=yardstick_df["goals_home"] - yardstick_df["goals_home_1h"],
        away_2h=yardstick_df["goals_away"] - yardstick_df["goals_away_1h"],
        e_home_2h=(1 - share) * yardstick_df["lam_home"],
        e_away_2h=(1 - share) * yardstick_df["lam_away"],
    )

    table = []
    for home, away in COMMON_SCORES:
        score_df = sides_df[
            (sides_df["goals_home_1h"] == home) & (sides_df["goals_away_1h"] == away)
        ]
        if score_df.empty:
            continue

        row: dict[str, object] = {"score": f"{home}-{away}", "matches": len(score_df)}
        for side in ("home", "away"):
            result = stats.observed_expected(score_df, f"{side}_2h", f"e_{side}_2h")
            row |= {f"{side} O/E": result["oe"], f"{side} low": result["low"]}
            row |= {f"{side} high": result["high"]}

        table.append(row)

    return pd.DataFrame(table)


def by_first_half_goals(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """All second-half goals O/E, by the goals of the first half (4 or more as one group)."""
    groups = yardstick_df["goals_1h"].clip(upper=FIRST_HALF_CAP)
    table = [
        {
            "first-half goals": int(goals),
            **stats.observed_expected(first_half_df, "goals_2h", "m_goals_2h"),
        }
        for goals, first_half_df in yardstick_df.groupby(groups)
    ]
    return pd.DataFrame(table)


def scaled_completions(
    yardstick_df: pd.DataFrame, share: float, factors: dict[str, float]
) -> float:
    """Expected completions when each side's second-half rate is scaled by its state's factor.

    A state missing from `factors` keeps the basic model's rate (factor 1).
    """
    margin = yardstick_df["ht_margin"].to_numpy()
    home = np.array([factors.get(state, 1.0) for state in state_of(margin)])
    away = np.array([factors.get(state, 1.0) for state in state_of(-margin)])

    completion = yardstick.completion_given_ht(
        yardstick_df["lam_home"].to_numpy(),
        yardstick_df["lam_away"].to_numpy(),
        share,
        margin,
        home,
        away,
    )

    return float(completion.sum())


def gap_table(yardstick_df: pd.DataFrame, share: float, measured: dict[str, float]) -> pd.DataFrame:
    """Expected completions under four sets of factors, against the observed comebacks."""
    trailing = {state: f for state, f in measured.items() if state.startswith("behind")}
    leading = {state: f for state, f in measured.items() if state.startswith("ahead")}

    observed = float(yardstick_df["is_comeback"].sum())
    basic = scaled_completions(yardstick_df, share, {})

    rows = []
    for name, factors in (
        ("basic model", {}),
        ("trailing side scaled", trailing),
        ("leading side scaled", leading),
        ("both scaled", trailing | leading),
    ):
        expected = scaled_completions(yardstick_df, share, factors)

        rows.append(
            {
                "factors": name,
                "expected": expected,
                "observed": observed,
                "oe": observed / expected,
                "gap explained": (expected - basic) / (observed - basic),
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    share = yardstick.first_half_share(yardstick.priced(matches_df))
    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid(), share=share)

    team_halves_df = team_halves(yardstick_df, share)
    print(
        f"Priced: {len(yardstick_df):,} matches; {len(team_halves_df):,} team-halves; "
        f"first-half share {share:.4f}"
    )

    states_df = by_state(team_halves_df)
    report.show("Second-half goals by the team's half-time state", states_df)
    for cohort, cohort_df in team_halves_df.groupby("season_cohort"):
        report.show(f"Season cohort {cohort}", by_state(cohort_df))
    report.show("By half-time state, favourite and underdog", by_state_and_side(team_halves_df))
    report.show("Each side after the common half-time scores", by_ht_score(yardstick_df, share))
    report.show("All second-half goals by first-half goals", by_first_half_goals(yardstick_df))

    measured = dict(zip(states_df["state"], states_df["oe"], strict=True))
    report.show(
        "Comebacks under the measured second-half rates", gap_table(yardstick_df, share, measured)
    )


if __name__ == "__main__":
    main()
