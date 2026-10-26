"""A screen of pre-match fields beyond the odds, for a team's comeback.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/PREMATCH_SCREEN.md`. Two rows per match, one for
each team: does this team come back? Each candidate field is added alone to a baseline built
from the odds yardstick (`analysis/methods/yardstick.py`), in a logistic regression whose
intervals are clustered by league-season; Holm over the fields; each season cohort; link 1
and link 2. Then out of sample: fit on one cohort, score the other, the baseline against the
baseline plus every field. Logistic regression only: the boosted trees of the old run are
machine learning (`analysis/CLAUDE.md` §1).

Run: `uv run python -m analysis.schedule.whole_corpus.all.prematch_screen`
"""

from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats as sps

from analysis import card, corpus, report, stats
from analysis.methods import shin, yardstick
from domain.clock import BERLIN

MIN_PLAYED = 5  # both teams have played this many matches of the stage
PRIOR_WEIGHT = 10.0  # pseudo-counts of a shrunk HT/FT record rate
COMPLETION_PRIOR = 0.083  # the old run's prior of a completion and of a blown lead
NOT_WON_PRIOR = 0.26  # the old run's prior of a lead not won
TEAM_PRIOR_WEIGHT = 40.0  # pseudo-matches of a team's comeback rate last season
LATE_SEASON = 0.8  # a dead rubber is this far into the stage or later
MID_TABLE = (0.3, 0.7)  # a dead rubber has both teams' rank shares in this range
MIDWEEK = (1, 2, 3)  # Tuesday to Thursday, Berlin time
TOP_N = (100, 250, 500, 1000)  # the N of `notes/WORKING/PLAN_2026-10-19_ML_TEST.md` step 5
LOGIT_CLIP = 1e-6  # a 0 or 1 field value stays this far inside, so its log odds stay finite
LOGIT_MAX_ITERATIONS = 200  # the most Newton steps the joint logit fit may take

# field -> family
FAMILIES = {
    "mk_margin": "market",
    "mk_ah_resid": "market",
    "mk_ah_tilt": "market",
    "mk_ou_tilt": "market",
    "mk_draw_resid": "market",
    "tb_ppg_diff": "table",
    "tb_gd_diff": "table",
    "tb_goal_env": "table",
    "hp_T_1h_gd": "halves",
    "hp_T_2h_gd": "halves",
    "hp_O_1h_gd": "halves",
    "hp_O_2h_gd": "halves",
    "hp_T_2h_share_for": "halves",
    "hp_O_2h_share_against": "halves",
    "hp_T_2h_gd_venue": "halves",
    "hp_O_2h_gd_venue": "halves",
    "rec_T_trail_rate": "htft record",
    "rec_T_cb_rate": "htft record",
    "rec_T_compl": "htft record",
    "rec_O_lead_rate": "htft record",
    "rec_O_blown": "htft record",
    "rec_O_not_won": "htft record",
    "ss_progress": "season",
    "ss_dead_rubber": "season",
    "cal_midweek": "calendar",
    "cal_last_ko": "calendar",
    "rnd_cb_share": "round so far",
    "rnd_goal_excess": "round so far",
    "prev_T_cb_rate": "last season",
    "prev_O_blown": "last season",
    "prev_league_oe": "last season",
}
BINARY = {"ss_dead_rubber", "cal_midweek", "cal_last_ko"}
LAST_SEASON = {"prev_T_cb_rate", "prev_O_blown", "prev_league_oe"}
# Left out of the joint model: tb_gd_diff is the sum of the four half fields, so the fit
# with all of them has no unique solution.
JOINT_LEFT_OUT = {"tb_gd_diff"}
# target -> (outcome column, yardstick column of the baseline, rows: all, or behind only)
TARGETS = {
    "comeback": ("comes_back", "m_cb", False),
    "link 1": ("behind", "m_trail", False),
    "link 2": ("comes_back", "m_compl", True),
}


def stat(
    matches_df: pd.DataFrame, who: str, half: str, venue: str, name: str
) -> "pd.Series[float]":
    """One stage-3 standings value of a side (S3.03), as floats."""

    return matches_df[f"s3_{who}_pre_{half}_{venue}_{name}"].astype(float)


def htft(matches_df: pd.DataFrame, who: str, ht: str, ft: str) -> "pd.Series[float]":
    """One HT/FT count of a side over its whole season so far (S3.08), as floats."""

    return matches_df[f"s3_{who}_pre_htft_total_{ht}_{ft}"].astype(float)


def odds_columns(yardstick_df: pd.DataFrame, side: str) -> pd.DataFrame:
    """The yardstick's view of the side: its Shin win chance, the two rates, its comeback
    chance, its chance to be behind at half-time, and the completion that follows."""

    mine, theirs = ("lam_home", "lam_away") if side == "home" else ("lam_away", "lam_home")
    odds_df = pd.DataFrame(
        {
            "p_T": yardstick_df[f"shin_p_{side}"],
            "lam_T": yardstick_df[mine],
            "lam_O": yardstick_df[theirs],
            "m_cb": yardstick_df[f"m_cb_{side}"],
            "m_trail": yardstick_df[f"m_{side}_behind"],
        },
        index=yardstick_df.index,
    )

    odds_df["m_compl"] = odds_df["m_cb"] / odds_df["m_trail"]

    return odds_df


def market(matches_df: pd.DataFrame, yardstick_df: pd.DataFrame, side: str) -> pd.DataFrame:
    """The market family: the 1X2 margin, the AH line against the yardstick's goal margin,
    the AH and O/U chances away from 50/50, and the Shin draw chance against the yardstick's."""

    sign = 1.0 if side == "home" else -1.0
    own_odds_df = odds_columns(yardstick_df, side)
    ah_home = matches_df["s2_implied_ah_home"]
    fit_draw = sps.skellam.pmf(0, yardstick_df["lam_home"], yardstick_df["lam_away"])

    return pd.DataFrame(
        {
            "mk_margin": (1.0 / matches_df[shin.ODDS]).sum(axis=1),
            "mk_ah_resid": sign * matches_df[corpus.AH[0]]
            - (own_odds_df["lam_T"] - own_odds_df["lam_O"]),
            "mk_ah_tilt": (ah_home if side == "home" else 1.0 - ah_home) - 0.5,
            "mk_ou_tilt": matches_df["s2_implied_over"] - 0.5,
            "mk_draw_resid": yardstick_df["shin_p_draw"] - fit_draw,
        },
        index=matches_df.index,
    )


def table(matches_df: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The table family, per match played: the points and goal difference against the
    opponent's, and the goals for and against of both teams."""

    team_played = stat(matches_df, side, "ft", "total", "played")
    opponent_played = stat(matches_df, other, "ft", "total", "played")

    def per_game(who: str, name: str, played: "pd.Series[float]") -> "pd.Series[float]":
        """The full-time total `name` of side `who`, per match played."""

        return stat(matches_df, who, "ft", "total", name) / played

    team_goals = 2 * per_game(side, "goals_for", team_played) - per_game(
        side, "goal_diff", team_played
    )
    opponent_goals = 2 * per_game(other, "goals_for", opponent_played) - per_game(
        other, "goal_diff", opponent_played
    )

    return pd.DataFrame(
        {
            "played_T": team_played,
            "played_O": opponent_played,
            "tb_ppg_diff": per_game(side, "points", team_played)
            - per_game(other, "points", opponent_played),
            "tb_gd_diff": per_game(side, "goal_diff", team_played)
            - per_game(other, "goal_diff", opponent_played),
            "tb_goal_env": (team_goals + opponent_goals) / 2,
        },
        index=matches_df.index,
    )


def halves(matches_df: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The halves family: each team's goal difference per match in each half, the second
    half's share of the team's goals for and of the opponent's goals against, and each
    team's second-half goal difference at its venue in this match."""

    halves_df = pd.DataFrame(index=matches_df.index)
    for who, tag in ((side, "T"), (other, "O")):
        played = stat(matches_df, who, "ft", "total", "played")
        ft_goal_diff, ht_goal_diff = (
            stat(matches_df, who, half, "total", "goal_diff") for half in ("ft", "ht")
        )
        halves_df[f"hp_{tag}_1h_gd"] = ht_goal_diff / played
        halves_df[f"hp_{tag}_2h_gd"] = (ft_goal_diff - ht_goal_diff) / played

        # A side's venue in this match is its side: the home team plays at home.
        venue_played = stat(matches_df, who, "ft", who, "played").replace(0, np.nan)
        venue_2h_goal_diff = stat(matches_df, who, "ft", who, "goal_diff") - stat(
            matches_df, who, "ht", who, "goal_diff"
        )
        halves_df[f"hp_{tag}_2h_gd_venue"] = venue_2h_goal_diff / venue_played

    goals_for = stat(matches_df, side, "ft", "total", "goals_for")
    ht_for = stat(matches_df, side, "ht", "total", "goals_for")
    halves_df["hp_T_2h_share_for"] = (goals_for - ht_for) / goals_for.replace(0, np.nan)

    against = stat(matches_df, other, "ft", "total", "goals_for") - stat(
        matches_df, other, "ft", "total", "goal_diff"
    )
    ht_against = stat(matches_df, other, "ht", "total", "goals_for") - stat(
        matches_df, other, "ht", "total", "goal_diff"
    )
    halves_df["hp_O_2h_share_against"] = (against - ht_against) / against.replace(0, np.nan)

    return halves_df


def record(matches_df: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The HT/FT record family: how often the team was behind at half-time and came back,
    its shrunk completion, and how often the opponent led at half-time and did not win."""

    team_played = stat(matches_df, side, "ft", "total", "played")
    opponent_played = stat(matches_df, other, "ft", "total", "played")

    behind = sum(htft(matches_df, side, "l", ft) for ft in "wdl")
    came_back = htft(matches_df, side, "l", "w")
    led = sum(htft(matches_df, other, "w", ft) for ft in "wdl")
    lost, drew = htft(matches_df, other, "w", "l"), htft(matches_df, other, "w", "d")

    return pd.DataFrame(
        {
            "rec_T_trail_rate": behind / team_played,
            "rec_T_cb_rate": came_back / team_played,
            "rec_T_compl": (came_back + PRIOR_WEIGHT * COMPLETION_PRIOR) / (behind + PRIOR_WEIGHT),
            "rec_O_lead_rate": led / opponent_played,
            "rec_O_blown": (lost + PRIOR_WEIGHT * COMPLETION_PRIOR) / (led + PRIOR_WEIGHT),
            "rec_O_not_won": (lost + drew + PRIOR_WEIGHT * NOT_WON_PRIOR) / (led + PRIOR_WEIGHT),
        },
        index=matches_df.index,
    )


def season(matches_df: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The season family: the share of the team's stage played (S3.11 gives the matches
    left), and a dead rubber: late in the stage with both teams in mid-table."""

    played = stat(matches_df, side, "ft", "total", "played")
    progress = played / (played + matches_df[f"s3_{side}_pre_matches_left"].astype(float))

    keys = [matches_df["s1_league_id"], matches_df["s1_season"], matches_df["s1_stage"].fillna("")]
    teams = matches_df["s1_home_team_id"].groupby(keys).transform("nunique").astype(float)

    low, high = MID_TABLE
    in_mid_table = [
        stat(matches_df, who, "ft", "total", "rank").div(teams).between(low, high)
        for who in (side, other)
    ]
    dead = (progress >= LATE_SEASON) & in_mid_table[0] & in_mid_table[1]

    return pd.DataFrame(
        {"ss_progress": progress, "ss_dead_rubber": dead.astype(float)}, index=matches_df.index
    )


def calendar(matches_df: pd.DataFrame) -> pd.DataFrame:
    """The calendar family: a kickoff from Tuesday to Thursday (Berlin time), and the last
    kickoff of a round that has more than one kickoff time."""

    kickoff = pd.to_datetime(matches_df["s1_date"], utc=True).dt.tz_convert(BERLIN)
    keys = [
        matches_df["s1_league_id"],
        matches_df["s1_season"],
        matches_df["s1_stage"].fillna(""),
        matches_df["s1_round"],
    ]

    latest = kickoff.groupby(keys).transform("max")
    earliest = kickoff.groupby(keys).transform("min")

    return pd.DataFrame(
        {
            "cal_midweek": kickoff.dt.weekday.isin(MIDWEEK).astype(float),
            "cal_last_ko": ((kickoff == latest) & (latest > earliest)).astype(float),
        },
        index=matches_df.index,
    )


def round_so_far(matches_df: pd.DataFrame) -> pd.DataFrame:
    """The round-so-far family: the share of the round's finished matches that were
    comebacks (S3.15 / S3.14), and their goals against their opening lines (S3.19 - S3.20)."""

    finished = matches_df["s3_round_pre_finished"].astype(float).replace(0, np.nan)

    return pd.DataFrame(
        {
            "rnd_cb_share": matches_df["s3_round_pre_comebacks"] / finished,
            "rnd_goal_excess": matches_df["s3_round_pre_avg_goals"]
            - matches_df["s3_round_pre_avg_ou_line"],
        },
        index=matches_df.index,
    )


def side_fields(matches_df: pd.DataFrame, yardstick_df: pd.DataFrame, side: str) -> pd.DataFrame:
    """Every column of one side's team row that is known before kickoff."""

    other = "away" if side == "home" else "home"
    parts = [
        odds_columns(yardstick_df, side),
        market(matches_df, yardstick_df, side),
        table(matches_df, side, other),
        halves(matches_df, side, other),
        record(matches_df, side, other),
        season(matches_df, side, other),
        calendar(matches_df),
        round_so_far(matches_df),
    ]

    side_fields_df = pd.concat(parts, axis=1)
    side_fields_df["opponent"] = matches_df[f"s1_{other}_team_id"]

    return side_fields_df.replace([np.inf, -np.inf], np.nan)


def screen_rows(matches_df: pd.DataFrame, yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """Two rows per priced match (`card.team_rows`) with every field, and last season's."""

    priced_df = matches_df.loc[yardstick_df.index]
    home_fields_df, away_fields_df = (
        side_fields(priced_df, yardstick_df, side) for side in ("home", "away")
    )
    extra = {name: (home_fields_df[name], away_fields_df[name]) for name in home_fields_df.columns}

    return last_season(card.team_rows(priced_df, extra))


def last_season(screen_rows_df: pd.DataFrame) -> pd.DataFrame:
    """The last-season family, for the rows of the later cohort only: the team's comeback
    rate and the opponent's blown-lead rate in the earlier cohort, both shrunk, and the
    league's comebacks against the yardstick in the earlier cohort."""

    with_last_season_df = screen_rows_df.copy()
    cohorts = sorted(screen_rows_df["season_cohort"].unique())

    for name in LAST_SEASON:
        with_last_season_df[name] = np.nan

    if len(cohorts) < 2:
        return with_last_season_df

    earlier_cohort_df, later = (
        screen_rows_df[screen_rows_df["season_cohort"] == cohorts[0]],
        screen_rows_df["season_cohort"] == cohorts[1],
    )
    base = earlier_cohort_df["comes_back"].mean()
    team_sums_df = earlier_cohort_df.groupby("team")[
        ["comes_back", "loses_lead", "ahead", "one"]
    ].sum()
    comeback_rate = (team_sums_df["comes_back"] + TEAM_PRIOR_WEIGHT * base) / (
        team_sums_df["one"] + TEAM_PRIOR_WEIGHT
    )
    blown = (team_sums_df["loses_lead"] + PRIOR_WEIGHT * COMPLETION_PRIOR) / (
        team_sums_df["ahead"] + PRIOR_WEIGHT
    )

    league_sums_df = earlier_cohort_df.groupby(card.TEAM_LEAGUE)[["comes_back", "m_cb"]].sum()
    league_observed_over_expected = league_sums_df["comes_back"] / league_sums_df["m_cb"]

    with_last_season_df.loc[later, "prev_T_cb_rate"] = screen_rows_df.loc[later, "team"].map(
        comeback_rate
    )
    with_last_season_df.loc[later, "prev_O_blown"] = screen_rows_df.loc[later, "opponent"].map(
        blown
    )
    with_last_season_df.loc[later, "prev_league_oe"] = screen_rows_df.loc[
        later, card.TEAM_LEAGUE
    ].map(league_observed_over_expected)

    return with_last_season_df


def logit(values: "pd.Series[float] | np.ndarray") -> np.ndarray:
    """The log odds, with the chance kept inside (`LOGIT_CLIP`, 1 - `LOGIT_CLIP`)."""

    clipped = np.clip(np.asarray(values, dtype=float), LOGIT_CLIP, 1 - LOGIT_CLIP)

    return np.asarray(np.log(clipped / (1 - clipped)))


def baseline(screen_rows_df: pd.DataFrame, key: str) -> np.ndarray:
    """The baseline design: a constant, the yardstick's chance of the target (log odds), the
    team's Shin win chance (log odds and its square), the log of the expected goals, and
    the venue."""

    p_win = logit(screen_rows_df["p_T"])

    return np.column_stack(
        [
            np.ones(len(screen_rows_df)),
            logit(screen_rows_df[key]),
            p_win,
            p_win**2,
            np.log(screen_rows_df["lam_T"] + screen_rows_df["lam_O"]).to_numpy(float),
            screen_rows_df["home"].to_numpy(float),
        ]
    )


def standardised(values: "pd.Series[float]", *, is_binary: bool) -> np.ndarray:
    """A field as one column: a 0/1 field as it is, any other in standard deviations."""

    numbers = values.to_numpy(dtype=float)

    return numbers if is_binary else (numbers - numbers.mean()) / numbers.std()


def fit_logit(outcomes: np.ndarray, design: np.ndarray, clusters: "pd.Series[Any]") -> Any:
    """A logistic regression with its covariance clustered by league-season."""

    groups = pd.factorize(clusters)[0]
    model = sm.Logit(outcomes, design)

    return model.fit(disp=0, cov_type="cluster", cov_kwds={"groups": groups})


def field_test(screen_rows_df: pd.DataFrame, field: str, target: str) -> dict[str, float]:
    """One field added alone to the baseline of one target: the odds ratio per standard
    deviation (per 1 for a 0/1 field), its 95% interval and the Wald p, both clustered by
    league-season."""

    outcome, key, behind_only = TARGETS[target]
    field_rows_df = screen_rows_df[screen_rows_df[field].notna()]
    if behind_only:
        field_rows_df = field_rows_df[field_rows_df["behind"] == 1.0]

    design = np.column_stack(
        [
            baseline(field_rows_df, key),
            standardised(field_rows_df[field], is_binary=field in BINARY),
        ]
    )
    outcomes = field_rows_df[outcome].to_numpy(dtype=float)
    fit = fit_logit(outcomes, design, field_rows_df["cluster"])
    coefficient, standard_error = float(fit.params[-1]), float(fit.bse[-1])

    return {
        "n": float(len(field_rows_df)),
        "events": float(outcomes.sum()),
        "OR": float(np.exp(coefficient)),
        "low": float(np.exp(coefficient - stats.Z95 * standard_error)),
        "high": float(np.exp(coefficient + stats.Z95 * standard_error)),
        "p": float(fit.pvalues[-1]),
    }


def eligible(screen_rows_df: pd.DataFrame) -> pd.DataFrame:
    """The rows where both teams have played at least `MIN_PLAYED` matches of the stage."""

    return screen_rows_df[
        (screen_rows_df["played_T"] >= MIN_PLAYED) & (screen_rows_df["played_O"] >= MIN_PLAYED)
    ]


def screen(screen_rows_df: pd.DataFrame) -> pd.DataFrame:
    """Each field alone: the comeback test on all rows (Holm over the fields), in each season
    cohort, and for link 1 and link 2."""

    cohorts = sorted(screen_rows_df["season_cohort"].unique())
    rows = []
    for field, family in FAMILIES.items():
        pooled = field_test(screen_rows_df, field, "comeback")
        row: dict[str, object] = {"field": field, "family": family, **pooled}

        for cohort in cohorts:
            cohort_rows_df = screen_rows_df[screen_rows_df["season_cohort"] == cohort]
            single = (
                field_test(cohort_rows_df, field, "comeback")
                if cohort_rows_df[field].notna().any()
                else None
            )
            row[f"OR {cohort}"] = single["OR"] if single else np.nan
            row[f"p {cohort}"] = single["p"] if single else np.nan

        for target in ("link 1", "link 2"):
            link = field_test(screen_rows_df, field, target)
            row[f"{target} OR"], row[f"{target} p"] = link["OR"], link["p"]

        rows.append(row)

    results_df = pd.DataFrame(rows)
    holm = stats.holm(results_df["p"].tolist())
    results_df.insert(list(results_df.columns).index("p") + 1, "Holm", holm)

    return results_df.sort_values("p").reset_index(drop=True)


def joint_fields() -> list[str]:
    """The fields of the joint model: all but last season's (one cohort only) and
    `JOINT_LEFT_OUT`."""

    return [f for f in FAMILIES if f not in LAST_SEASON and f not in JOINT_LEFT_OUT]


def joint_design(
    screen_rows_df: pd.DataFrame, train_df: pd.DataFrame, fields: list[str]
) -> np.ndarray:
    """The baseline plus the fields, an empty value filled with the training median, each
    field in the training set's standard deviations."""

    field_values_df = screen_rows_df[fields].fillna(train_df[fields].median())
    centre, spread = train_df[fields].mean(), train_df[fields].std()

    return np.column_stack(
        [baseline(screen_rows_df, "m_cb"), ((field_values_df - centre) / spread).to_numpy(float)]
    )


def out_of_sample(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict[str, np.ndarray]:
    """The comeback chance that each model gives the test rows, fitted on the train rows."""

    train_comes_back = train_df["comes_back"].to_numpy(dtype=float)
    fields = joint_fields()
    base = sm.Logit(train_comes_back, baseline(train_df, "m_cb")).fit(disp=0)
    joint = sm.Logit(train_comes_back, joint_design(train_df, train_df, fields)).fit(
        disp=0, maxiter=LOGIT_MAX_ITERATIONS
    )

    return {
        "constant": np.full(len(test_df), train_comes_back.mean()),
        "yardstick": test_df["m_cb"].to_numpy(dtype=float),
        "baseline": np.asarray(base.predict(baseline(test_df, "m_cb"))),
        "baseline + all fields": np.asarray(joint.predict(joint_design(test_df, train_df, fields))),
    }


def log_loss(outcomes: np.ndarray, chances: np.ndarray) -> float:
    """The mean log loss of a chance for a 0/1 outcome."""

    clipped = np.clip(chances, stats.LOG_LOSS_CLIP, 1 - stats.LOG_LOSS_CLIP)

    return float(-np.mean(outcomes * np.log(clipped) + (1 - outcomes) * np.log(1 - clipped)))


def auc(outcomes: np.ndarray, score: np.ndarray) -> float:
    """The area under the ROC curve, as the Mann-Whitney statistic of the scores."""

    ranks = sps.rankdata(score)
    events = outcomes == 1
    n_events, n_rest = int(events.sum()), int((~events).sum())

    return float((ranks[events].sum() - n_events * (n_events + 1) / 2) / (n_events * n_rest))


def top_hits(outcomes: np.ndarray, score: np.ndarray, top_count: int) -> int:
    """The events among the `top_count` rows with the highest scores."""

    order = np.argsort(-score, kind="stable")

    return int(outcomes[order[:top_count]].sum())


def score_table(outcomes: np.ndarray, scores: dict[str, np.ndarray]) -> pd.DataFrame:
    """Per model: the log loss, the AUC, and the events in each top-N set. A model that gives
    every row the same chance has no top set: its row gives the events that chance expects."""

    rows = []
    for name, score in scores.items():
        row: dict[str, object] = {
            "model": name,
            "log loss": log_loss(outcomes, score),
            "AUC": auc(outcomes, score),
        }

        flat = bool(np.ptp(score) == 0)
        row.update(
            {
                f"top {top_count}": top_count * float(outcomes.mean())
                if flat
                else top_hits(outcomes, score, top_count)
                for top_count in TOP_N
            }
        )

        rows.append(row)

    return pd.DataFrame(rows)


def split_rows(
    matches_df: pd.DataFrame, grid: yardstick.Grid, train_cohort: int
) -> tuple[pd.DataFrame, float]:
    """The eligible team rows of one out-of-sample split, and the first-half share that the
    yardstick's chances use: the training cohort's only, so no goal of the test cohort reaches
    the baseline or a field."""

    train_df = matches_df[matches_df["season_cohort"] == train_cohort]
    share = yardstick.first_half_share(yardstick.priced(train_df))
    screen_rows_df = eligible(
        screen_rows(matches_df, yardstick.frame(matches_df, grid, share=share))
    )

    return screen_rows_df, share


def main() -> None:
    """Entry point: print the screen of pre-match fields beyond the odds."""

    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    grid = yardstick.build_grid()
    yardstick_df = yardstick.frame(matches_df, grid)

    screen_rows_df = screen_rows(matches_df, yardstick_df)
    eligible_df = eligible(screen_rows_df)
    print(
        f"team rows: {len(screen_rows_df):,}; both teams with "
        f"{MIN_PLAYED}+ matches played: {len(eligible_df):,}; "
        f"comebacks there: {int(eligible_df['comes_back'].sum()):,}"
    )

    report.show("Each field alone, beyond the odds", screen(eligible_df))

    cohorts = sorted(eligible_df["season_cohort"].unique())
    for first, second in ((cohorts[0], cohorts[1]), (cohorts[1], cohorts[0])):
        split_rows_df, share = split_rows(matches_df, grid, first)
        train_df = split_rows_df[split_rows_df["season_cohort"] == first]
        test_df = split_rows_df[split_rows_df["season_cohort"] == second]

        print(f"\nthe yardstick's first-half share, from the {first} cohort: {share:.4f}")

        test_comes_back = test_df["comes_back"].to_numpy(dtype=float)
        title = (
            f"Fit on {first} ({len(train_df):,} rows, "
            f"{int(train_df['comes_back'].sum())} comebacks), "
            f"scored on {second} ({len(test_df):,} rows, {int(test_comes_back.sum())} comebacks)"
        )

        report.show(title, score_table(test_comes_back, out_of_sample(train_df, test_df)))


if __name__ == "__main__":
    main()
