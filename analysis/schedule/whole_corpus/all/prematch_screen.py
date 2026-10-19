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

MIN_PLAYED = 5  # both teams have played this many matches of the stage
PRIOR_WEIGHT = 10.0  # pseudo-counts of a shrunk HT/FT record rate
COMPLETION_PRIOR = 0.083  # the old run's prior of a completion and of a blown lead
NOT_WON_PRIOR = 0.26  # the old run's prior of a lead not won
TEAM_PRIOR_WEIGHT = 40.0  # pseudo-matches of a team's comeback rate last season
LATE_SEASON = 0.8  # a dead rubber is this far into the stage or later
MID_TABLE = (0.3, 0.7)  # a dead rubber has both teams' rank shares in this range
MIDWEEK = (1, 2, 3)  # Tuesday to Thursday, Berlin time
TOP_N = (100, 250, 500, 1000)

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


def stat(matches: pd.DataFrame, who: str, half: str, venue: str, name: str) -> "pd.Series[float]":
    """One stage-3 standings value of a side (S3.03), as floats."""
    return matches[f"s3_{who}_pre_{half}_{venue}_{name}"].astype(float)


def htft(matches: pd.DataFrame, who: str, ht: str, ft: str) -> "pd.Series[float]":
    """One HT/FT count of a side over its whole season so far (S3.08), as floats."""
    return matches[f"s3_{who}_pre_htft_total_{ht}_{ft}"].astype(float)


def odds_columns(model: pd.DataFrame, side: str) -> pd.DataFrame:
    """The yardstick's view of the side: its Shin win chance, the two rates, its comeback
    chance, its chance to be behind at half-time, and the completion that follows."""
    mine, theirs = ("lam_home", "lam_away") if side == "home" else ("lam_away", "lam_home")
    out = pd.DataFrame(
        {
            "p_T": model[f"shin_p_{side}"],
            "lam_T": model[mine],
            "lam_O": model[theirs],
            "m_cb": model[f"m_cb_{side}"],
            "m_trail": model[f"m_{side}_behind"],
        },
        index=model.index,
    )
    out["m_compl"] = out["m_cb"] / out["m_trail"]
    return out


def market(matches: pd.DataFrame, model: pd.DataFrame, side: str) -> pd.DataFrame:
    """The market family: the 1X2 margin, the AH line against the yardstick's goal margin,
    the AH and O/U chances away from 50/50, and the Shin draw chance against the yardstick's."""
    sign = 1.0 if side == "home" else -1.0
    own = odds_columns(model, side)
    ah_home = matches["s2_implied_ah_home"]
    fit_draw = sps.skellam.pmf(0, model["lam_home"], model["lam_away"])
    return pd.DataFrame(
        {
            "mk_margin": (1.0 / matches[shin.ODDS]).sum(axis=1),
            "mk_ah_resid": sign * matches[corpus.AH[0]] - (own["lam_T"] - own["lam_O"]),
            "mk_ah_tilt": (ah_home if side == "home" else 1.0 - ah_home) - 0.5,
            "mk_ou_tilt": matches["s2_implied_over"] - 0.5,
            "mk_draw_resid": model["shin_p_draw"] - fit_draw,
        },
        index=matches.index,
    )


def table(matches: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The table family, per match played: the points and goal difference against the
    opponent's, and the goals for and against of both teams."""
    played_t = stat(matches, side, "ft", "total", "played")
    played_o = stat(matches, other, "ft", "total", "played")

    def per_game(who: str, name: str, played: "pd.Series[float]") -> "pd.Series[float]":
        return stat(matches, who, "ft", "total", name) / played

    goals_t = 2 * per_game(side, "goals_for", played_t) - per_game(side, "goal_diff", played_t)
    goals_o = 2 * per_game(other, "goals_for", played_o) - per_game(other, "goal_diff", played_o)
    return pd.DataFrame(
        {
            "played_T": played_t,
            "played_O": played_o,
            "tb_ppg_diff": per_game(side, "points", played_t) - per_game(other, "points", played_o),
            "tb_gd_diff": per_game(side, "goal_diff", played_t)
            - per_game(other, "goal_diff", played_o),
            "tb_goal_env": (goals_t + goals_o) / 2,
        },
        index=matches.index,
    )


def halves(matches: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The halves family: each team's goal difference per match in each half, the second
    half's share of the team's goals for and of the opponent's goals against, and each
    team's second-half goal difference at its venue in this match."""
    out = pd.DataFrame(index=matches.index)
    for who, tag in ((side, "T"), (other, "O")):
        played = stat(matches, who, "ft", "total", "played")
        ft_gd, ht_gd = (stat(matches, who, h, "total", "goal_diff") for h in ("ft", "ht"))
        out[f"hp_{tag}_1h_gd"] = ht_gd / played
        out[f"hp_{tag}_2h_gd"] = (ft_gd - ht_gd) / played
        # A side's venue in this match is its side: the home team plays at home.
        venue_played = stat(matches, who, "ft", who, "played").replace(0, np.nan)
        venue_2h = stat(matches, who, "ft", who, "goal_diff") - stat(
            matches, who, "ht", who, "goal_diff"
        )
        out[f"hp_{tag}_2h_gd_venue"] = venue_2h / venue_played
    goals_for = stat(matches, side, "ft", "total", "goals_for")
    ht_for = stat(matches, side, "ht", "total", "goals_for")
    out["hp_T_2h_share_for"] = (goals_for - ht_for) / goals_for.replace(0, np.nan)
    against = stat(matches, other, "ft", "total", "goals_for") - stat(
        matches, other, "ft", "total", "goal_diff"
    )
    ht_against = stat(matches, other, "ht", "total", "goals_for") - stat(
        matches, other, "ht", "total", "goal_diff"
    )
    out["hp_O_2h_share_against"] = (against - ht_against) / against.replace(0, np.nan)
    return out


def record(matches: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The HT/FT record family: how often the team was behind at half-time and came back,
    its shrunk completion, and how often the opponent led at half-time and did not win."""
    played_t = stat(matches, side, "ft", "total", "played")
    played_o = stat(matches, other, "ft", "total", "played")
    behind = sum(htft(matches, side, "l", ft) for ft in "wdl")
    came_back = htft(matches, side, "l", "w")
    led = sum(htft(matches, other, "w", ft) for ft in "wdl")
    lost, drew = htft(matches, other, "w", "l"), htft(matches, other, "w", "d")
    return pd.DataFrame(
        {
            "rec_T_trail_rate": behind / played_t,
            "rec_T_cb_rate": came_back / played_t,
            "rec_T_compl": (came_back + PRIOR_WEIGHT * COMPLETION_PRIOR) / (behind + PRIOR_WEIGHT),
            "rec_O_lead_rate": led / played_o,
            "rec_O_blown": (lost + PRIOR_WEIGHT * COMPLETION_PRIOR) / (led + PRIOR_WEIGHT),
            "rec_O_not_won": (lost + drew + PRIOR_WEIGHT * NOT_WON_PRIOR) / (led + PRIOR_WEIGHT),
        },
        index=matches.index,
    )


def season(matches: pd.DataFrame, side: str, other: str) -> pd.DataFrame:
    """The season family: the share of the team's stage played (S3.11 gives the matches
    left), and a dead rubber: late in the stage with both teams in mid-table."""
    played = stat(matches, side, "ft", "total", "played")
    progress = played / (played + matches[f"s3_{side}_pre_matches_left"].astype(float))
    keys = [matches["s1_league_id"], matches["s1_season"], matches["s1_stage"].fillna("")]
    teams = matches["s1_home_team_id"].groupby(keys).transform("nunique").astype(float)
    low, high = MID_TABLE
    mid = [
        stat(matches, who, "ft", "total", "rank").div(teams).between(low, high)
        for who in (side, other)
    ]
    dead = (progress >= LATE_SEASON) & mid[0] & mid[1]
    return pd.DataFrame(
        {"ss_progress": progress, "ss_dead_rubber": dead.astype(float)}, index=matches.index
    )


def calendar(matches: pd.DataFrame) -> pd.DataFrame:
    """The calendar family: a kickoff from Tuesday to Thursday (Berlin time), and the last
    kickoff of a round that has more than one kickoff time."""
    kickoff = pd.to_datetime(matches["s1_date"], utc=True).dt.tz_convert("Europe/Berlin")
    keys = [
        matches["s1_league_id"],
        matches["s1_season"],
        matches["s1_stage"].fillna(""),
        matches["s1_round"],
    ]
    latest = kickoff.groupby(keys).transform("max")
    earliest = kickoff.groupby(keys).transform("min")
    return pd.DataFrame(
        {
            "cal_midweek": kickoff.dt.weekday.isin(MIDWEEK).astype(float),
            "cal_last_ko": ((kickoff == latest) & (latest > earliest)).astype(float),
        },
        index=matches.index,
    )


def round_so_far(matches: pd.DataFrame) -> pd.DataFrame:
    """The round-so-far family: the share of the round's finished matches that were
    comebacks (S3.15 / S3.14), and their goals against their opening lines (S3.19 - S3.20)."""
    finished = matches["s3_round_pre_finished"].astype(float).replace(0, np.nan)
    return pd.DataFrame(
        {
            "rnd_cb_share": matches["s3_round_pre_comebacks"] / finished,
            "rnd_goal_excess": matches["s3_round_pre_avg_goals"]
            - matches["s3_round_pre_avg_ou_line"],
        },
        index=matches.index,
    )


def side_fields(matches: pd.DataFrame, model: pd.DataFrame, side: str) -> pd.DataFrame:
    """Every column of one side's team row that is known before kickoff."""
    other = "away" if side == "home" else "home"
    parts = [
        odds_columns(model, side),
        market(matches, model, side),
        table(matches, side, other),
        halves(matches, side, other),
        record(matches, side, other),
        season(matches, side, other),
        calendar(matches),
        round_so_far(matches),
    ]
    out = pd.concat(parts, axis=1)
    out["opponent"] = matches[f"s1_{other}_team_id"]
    return out.replace([np.inf, -np.inf], np.nan)


def screen_rows(matches: pd.DataFrame, model: pd.DataFrame) -> pd.DataFrame:
    """Two rows per priced match (`card.team_rows`) with every field, and last season's."""
    priced = matches.loc[model.index]
    home, away = (side_fields(priced, model, side) for side in ("home", "away"))
    extra = {name: (home[name], away[name]) for name in home.columns}
    return last_season(card.team_rows(priced, extra))


def last_season(rows: pd.DataFrame) -> pd.DataFrame:
    """The last-season family, for the rows of the later cohort only: the team's comeback
    rate and the opponent's blown-lead rate in the earlier cohort, both shrunk, and the
    league's comebacks against the yardstick in the earlier cohort."""
    out = rows.copy()
    cohorts = sorted(rows["season_cohort"].unique())
    for name in LAST_SEASON:
        out[name] = np.nan
    if len(cohorts) < 2:
        return out
    before, later = rows[rows["season_cohort"] == cohorts[0]], rows["season_cohort"] == cohorts[1]
    base = before["comes_back"].mean()
    team = before.groupby("team")[["comes_back", "loses_lead", "ahead", "one"]].sum()
    cb_rate = (team["comes_back"] + TEAM_PRIOR_WEIGHT * base) / (team["one"] + TEAM_PRIOR_WEIGHT)
    blown = (team["loses_lead"] + PRIOR_WEIGHT * COMPLETION_PRIOR) / (team["ahead"] + PRIOR_WEIGHT)
    league = before.groupby(card.TEAM_LEAGUE)[["comes_back", "m_cb"]].sum()
    league_oe = league["comes_back"] / league["m_cb"]
    out.loc[later, "prev_T_cb_rate"] = rows.loc[later, "team"].map(cb_rate)
    out.loc[later, "prev_O_blown"] = rows.loc[later, "opponent"].map(blown)
    out.loc[later, "prev_league_oe"] = rows.loc[later, card.TEAM_LEAGUE].map(league_oe)
    return out


def logit(values: "pd.Series[float] | np.ndarray") -> np.ndarray:
    """The log odds, with the chance kept inside (1e-6, 1 - 1e-6)."""
    p = np.clip(np.asarray(values, dtype=float), 1e-6, 1 - 1e-6)
    return np.asarray(np.log(p / (1 - p)))


def baseline(rows: pd.DataFrame, key: str) -> np.ndarray:
    """The baseline design: a constant, the yardstick's chance of the target (log odds), the
    team's Shin win chance (log odds and its square), the log of the expected goals, and
    the venue."""
    p_win = logit(rows["p_T"])
    return np.column_stack(
        [
            np.ones(len(rows)),
            logit(rows[key]),
            p_win,
            p_win**2,
            np.log(rows["lam_T"] + rows["lam_O"]).to_numpy(float),
            rows["home"].to_numpy(float),
        ]
    )


def standardised(values: "pd.Series[float]", binary: bool) -> np.ndarray:
    """A field as one column: a 0/1 field as it is, any other in standard deviations."""
    x = values.to_numpy(dtype=float)
    return x if binary else (x - x.mean()) / x.std()


def fit_logit(y: np.ndarray, design: np.ndarray, clusters: "pd.Series[Any]") -> Any:
    """A logistic regression with its covariance clustered by league-season."""
    groups = pd.factorize(clusters)[0]
    model = sm.Logit(y, design)
    return model.fit(disp=0, cov_type="cluster", cov_kwds={"groups": groups})


def field_test(rows: pd.DataFrame, field: str, target: str) -> dict[str, float]:
    """One field added alone to the baseline of one target: the odds ratio per standard
    deviation (per 1 for a 0/1 field), its 95% interval and the Wald p, both clustered by
    league-season."""
    outcome, key, behind_only = TARGETS[target]
    part = rows[rows[field].notna()]
    if behind_only:
        part = part[part["behind"] == 1.0]
    design = np.column_stack([baseline(part, key), standardised(part[field], field in BINARY)])
    y = part[outcome].to_numpy(dtype=float)
    result = fit_logit(y, design, part["cluster"])
    beta, se = float(result.params[-1]), float(result.bse[-1])
    return {
        "n": float(len(part)),
        "events": float(y.sum()),
        "OR": float(np.exp(beta)),
        "low": float(np.exp(beta - stats.Z95 * se)),
        "high": float(np.exp(beta + stats.Z95 * se)),
        "p": float(result.pvalues[-1]),
    }


def eligible(rows: pd.DataFrame) -> pd.DataFrame:
    """The rows where both teams have played at least `MIN_PLAYED` matches of the stage."""
    return rows[(rows["played_T"] >= MIN_PLAYED) & (rows["played_O"] >= MIN_PLAYED)]


def screen(rows: pd.DataFrame) -> pd.DataFrame:
    """Each field alone: the comeback test on all rows (Holm over the fields), in each season
    cohort, and for link 1 and link 2."""
    cohorts = sorted(rows["season_cohort"].unique())
    out = []
    for field, family in FAMILIES.items():
        pooled = field_test(rows, field, "comeback")
        row: dict[str, object] = {"field": field, "family": family, **pooled}
        for cohort in cohorts:
            part = rows[rows["season_cohort"] == cohort]
            single = field_test(part, field, "comeback") if part[field].notna().any() else None
            row[f"OR {cohort}"] = single["OR"] if single else np.nan
            row[f"p {cohort}"] = single["p"] if single else np.nan
        for target in ("link 1", "link 2"):
            link = field_test(rows, field, target)
            row[f"{target} OR"], row[f"{target} p"] = link["OR"], link["p"]
        out.append(row)
    table = pd.DataFrame(out)
    holm = stats.holm(table["p"].tolist())
    table.insert(list(table.columns).index("p") + 1, "Holm", holm)
    return table.sort_values("p").reset_index(drop=True)


def joint_fields() -> list[str]:
    """The fields of the joint model: all but last season's (one cohort only) and
    `JOINT_LEFT_OUT`."""
    return [f for f in FAMILIES if f not in LAST_SEASON and f not in JOINT_LEFT_OUT]


def joint_design(rows: pd.DataFrame, train: pd.DataFrame, fields: list[str]) -> np.ndarray:
    """The baseline plus the fields, an empty value filled with the training median, each
    field in the training set's standard deviations."""
    values = rows[fields].fillna(train[fields].median())
    centre, spread = train[fields].mean(), train[fields].std()
    return np.column_stack([baseline(rows, "m_cb"), ((values - centre) / spread).to_numpy(float)])


def out_of_sample(train: pd.DataFrame, test: pd.DataFrame) -> dict[str, np.ndarray]:
    """The comeback chance that each model gives the test rows, fitted on the train rows."""
    y = train["comes_back"].to_numpy(dtype=float)
    fields = joint_fields()
    base = sm.Logit(y, baseline(train, "m_cb")).fit(disp=0)
    joint = sm.Logit(y, joint_design(train, train, fields)).fit(disp=0, maxiter=200)
    return {
        "constant": np.full(len(test), y.mean()),
        "yardstick": test["m_cb"].to_numpy(dtype=float),
        "baseline": np.asarray(base.predict(baseline(test, "m_cb"))),
        "baseline + all fields": np.asarray(joint.predict(joint_design(test, train, fields))),
    }


def log_loss(y: np.ndarray, p: np.ndarray) -> float:
    """The mean log loss of a chance for a 0/1 outcome."""
    q = np.clip(p, 1e-12, 1 - 1e-12)
    return float(-np.mean(y * np.log(q) + (1 - y) * np.log(1 - q)))


def auc(y: np.ndarray, score: np.ndarray) -> float:
    """The area under the ROC curve, as the Mann-Whitney statistic of the scores."""
    ranks = sps.rankdata(score)
    events = y == 1
    n_events, n_rest = int(events.sum()), int((~events).sum())
    return float((ranks[events].sum() - n_events * (n_events + 1) / 2) / (n_events * n_rest))


def top_hits(y: np.ndarray, score: np.ndarray, n: int) -> int:
    """The events among the `n` rows with the highest scores."""
    order = np.argsort(-score, kind="stable")
    return int(y[order[:n]].sum())


def score_table(y: np.ndarray, scores: dict[str, np.ndarray]) -> pd.DataFrame:
    """Per model: the log loss, the AUC, and the events in each top-N set. A model that gives
    every row the same chance has no top set: its row gives the events that chance expects."""
    rows = []
    for name, score in scores.items():
        row: dict[str, object] = {
            "model": name,
            "log loss": log_loss(y, score),
            "AUC": auc(y, score),
        }
        flat = bool(np.ptp(score) == 0)
        row.update(
            {f"top {n}": n * float(y.mean()) if flat else top_hits(y, score, n) for n in TOP_N}
        )
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    model = yardstick.frame(matches, yardstick.build_grid())
    rows = screen_rows(matches, model)
    used = eligible(rows)
    print(
        f"team rows: {len(rows):,}; both teams with {MIN_PLAYED}+ matches played: {len(used):,}; "
        f"comebacks there: {int(used['comes_back'].sum()):,}"
    )
    report.show("Each field alone, beyond the odds", screen(used))
    cohorts = sorted(used["season_cohort"].unique())
    for first, second in ((cohorts[0], cohorts[1]), (cohorts[1], cohorts[0])):
        train, test = used[used["season_cohort"] == first], used[used["season_cohort"] == second]
        y = test["comes_back"].to_numpy(dtype=float)
        title = (
            f"Fit on {first} ({len(train):,} rows, {int(train['comes_back'].sum())} comebacks), "
            f"scored on {second} ({len(test):,} rows, {int(y.sum())} comebacks)"
        )
        report.show(title, score_table(y, out_of_sample(train, test)))


if __name__ == "__main__":
    main()
