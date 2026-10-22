"""`analysis/schedule/whole_corpus/all/prematch_screen.py`: the fields, the fits, the scores."""

import numpy as np
import pandas as pd
import pytest
from scipy import stats as sps

from analysis.methods import shin, yardstick
from analysis.schedule.whole_corpus.all import prematch_screen as runner


def standings(rows: int, **values: float) -> pd.DataFrame:
    """Stage-3 standings for both sides: each `<side>_<half>_<venue>_<stat>=value` given,
    every other count 1."""
    columns = {}
    for side in ("home", "away"):
        for half in ("ft", "ht"):
            for venue in ("total", "home", "away"):
                for name in ("rank", "played", "goals_for", "goal_diff", "points"):
                    key = f"{side}_{half}_{venue}_{name}"
                    columns[f"s3_{side}_pre_{half}_{venue}_{name}"] = values.get(key, 1.0)

    return pd.DataFrame(columns, index=range(rows))


def model_frame() -> pd.DataFrame:
    """The yardstick's columns for two matches."""
    return pd.DataFrame(
        {
            "lam_home": [1.5, 1.0],
            "lam_away": [1.0, 1.2],
            "shin_p_home": [0.5, 0.35],
            "shin_p_draw": [0.25, 0.3],
            "shin_p_away": [0.25, 0.35],
            "m_cb_home": [0.03, 0.02],
            "m_cb_away": [0.02, 0.025],
            "m_home_behind": [0.2, 0.3],
            "m_away_behind": [0.3, 0.25],
        }
    )


def test_odds_columns_take_the_side_and_its_completion() -> None:
    away = runner.odds_columns(model_frame(), "away")
    assert away["p_T"].tolist() == [0.25, 0.35]
    assert away["lam_T"].tolist() == [1.0, 1.2]
    assert away["m_compl"].tolist() == pytest.approx([0.02 / 0.3, 0.025 / 0.25])


def test_market_mirrors_the_handicap_for_the_away_side() -> None:
    matches = pd.DataFrame(
        {
            shin.ODDS[0]: [2.0, 2.5],
            shin.ODDS[1]: [4.0, 3.2],
            shin.ODDS[2]: [4.0, 2.8],
            "s1_odds_ah_open_line": [0.5, -0.25],
            "s2_implied_ah_home": [0.55, 0.48],
            "s2_implied_over": [0.52, 0.5],
        }
    )
    model = model_frame()

    home, away = runner.market(matches, model, "home"), runner.market(matches, model, "away")

    assert home["mk_margin"].tolist() == pytest.approx([1.0, 1 / 2.5 + 1 / 3.2 + 1 / 2.8])
    assert home.at[0, "mk_ah_resid"] == pytest.approx(0.5 - 0.5)
    assert away.at[0, "mk_ah_resid"] == pytest.approx(-0.5 + 0.5)
    assert away.at[0, "mk_ah_tilt"] == pytest.approx(0.45 - 0.5)
    draw = float(sps.skellam.pmf(0, 1.5, 1.0))
    assert home.at[0, "mk_draw_resid"] == pytest.approx(0.25 - draw)


def test_table_compares_the_teams_per_match_played() -> None:
    matches = standings(
        1,
        home_ft_total_played=10,
        home_ft_total_points=20,
        home_ft_total_goals_for=15,
        home_ft_total_goal_diff=5,
        away_ft_total_played=5,
        away_ft_total_points=5,
        away_ft_total_goals_for=5,
        away_ft_total_goal_diff=-5,
    )

    table = runner.table(matches, "home", "away").iloc[0]

    assert float(table["tb_ppg_diff"]) == pytest.approx(2.0 - 1.0)
    assert float(table["tb_gd_diff"]) == pytest.approx(0.5 - (-1.0))
    # Goals for and against per match: home (15 + 10) / 10, away (5 + 10) / 5.
    assert float(table["tb_goal_env"]) == pytest.approx((2.5 + 3.0) / 2)


def test_halves_split_the_goal_difference_and_read_each_side_at_its_venue() -> None:
    matches = standings(
        1,
        home_ft_total_played=4,
        home_ft_total_goal_diff=6,
        home_ht_total_goal_diff=2,
        home_ft_total_goals_for=8,
        home_ht_total_goals_for=2,
        home_ft_home_played=2,
        home_ft_home_goal_diff=5,
        home_ht_home_goal_diff=1,
        away_ft_away_played=0,
    )

    halves = runner.halves(matches, "home", "away").iloc[0]

    assert float(halves["hp_T_1h_gd"]) == pytest.approx(2 / 4)
    assert float(halves["hp_T_2h_gd"]) == pytest.approx(4 / 4)
    assert float(halves["hp_T_2h_share_for"]) == pytest.approx(6 / 8)
    assert float(halves["hp_T_2h_gd_venue"]) == pytest.approx((5 - 1) / 2)
    assert np.isnan(halves["hp_O_2h_gd_venue"])  # no away match played yet


def test_record_shrinks_the_completion_toward_the_prior() -> None:
    counts = {
        f"s3_{side}_pre_htft_total_{ht}_{ft}": 0.0
        for side in ("home", "away")
        for ht in "wdl"
        for ft in "wdl"
    }
    matches = pd.DataFrame({**counts, **standings(1).iloc[0].to_dict()}, index=[0])
    matches["s3_home_pre_ft_total_played"] = 10.0
    matches["s3_home_pre_htft_total_l_w"] = 2.0
    matches["s3_home_pre_htft_total_l_l"] = 3.0

    record = runner.record(matches, "home", "away").iloc[0]

    assert float(record["rec_T_trail_rate"]) == pytest.approx(5 / 10)
    assert float(record["rec_T_compl"]) == pytest.approx(
        (2 + runner.PRIOR_WEIGHT * runner.COMPLETION_PRIOR) / (5 + runner.PRIOR_WEIGHT)
    )
    assert float(record["rec_O_not_won"]) == pytest.approx(runner.NOT_WON_PRIOR)


def test_season_gives_the_share_played_and_a_dead_rubber() -> None:
    matches = standings(2, home_ft_total_played=16, away_ft_total_played=16)
    matches["s3_home_pre_ft_total_rank"] = [2.0, 1.0]
    matches["s3_away_pre_ft_total_rank"] = [2.0, 1.0]
    matches["s3_home_pre_matches_left"] = [4, 4]
    matches["s1_league_id"], matches["s1_season"], matches["s1_stage"] = 1, "2024", np.nan
    matches["s1_home_team_id"] = [11, 12]  # 2 teams seen: a rank of 1 is a share of 0.5

    season = runner.season(matches, "home", "away")

    assert season["ss_progress"].tolist() == pytest.approx([0.8, 0.8])
    assert season["ss_dead_rubber"].tolist() == [0.0, 1.0]


def test_calendar_reads_the_berlin_weekday_and_the_last_kickoff() -> None:
    matches = pd.DataFrame(
        {
            # Tuesday 23:30 UTC is Wednesday in Berlin; Sunday 23:30 UTC is Monday.
            "s1_date": [
                "2024-08-06 23:30+00:00",
                "2024-08-04 23:30+00:00",
                "2024-08-04 12:00+00:00",
            ],
            "s1_league_id": 1,
            "s1_season": "2024",
            "s1_stage": "League",
            "s1_round": [3, 4, 4],
        }
    )

    calendar = runner.calendar(matches)

    assert calendar["cal_midweek"].tolist() == [1.0, 0.0, 0.0]
    assert calendar["cal_last_ko"].tolist() == [0.0, 1.0, 0.0]  # round 3 has one kickoff


def test_round_so_far_needs_a_finished_round_mate() -> None:
    matches = pd.DataFrame(
        {
            "s3_round_pre_finished": [0, 4],
            "s3_round_pre_comebacks": [0, 1],
            "s3_round_pre_avg_goals": [np.nan, 3.0],
            "s3_round_pre_avg_ou_line": [np.nan, 2.5],
        }
    )

    fields = runner.round_so_far(matches)

    assert np.isnan(fields.at[0, "rnd_cb_share"])
    assert fields.at[1, "rnd_cb_share"] == pytest.approx(0.25)
    assert fields.at[1, "rnd_goal_excess"] == pytest.approx(0.5)


def test_last_season_reads_the_earlier_cohort_for_the_later_rows_only() -> None:
    rows = pd.DataFrame(
        {
            "season_cohort": [2024, 2024, 2025, 2025],
            "team": [1, 2, 1, 3],
            "opponent": [2, 1, 3, 1],
            "league": 9,
            "comes_back": [1.0, 0.0, 0.0, 0.0],
            "loses_lead": [0.0, 1.0, 0.0, 0.0],
            "ahead": [0.0, 1.0, 0.0, 0.0],
            "one": 1.0,
            "m_cb": [0.25, 0.25, 0.1, 0.1],
        }
    )

    out = runner.last_season(rows)

    assert out.loc[[0, 1], "prev_T_cb_rate"].isna().all()
    weight = runner.TEAM_PRIOR_WEIGHT
    assert out.at[2, "prev_T_cb_rate"] == pytest.approx((1 + weight * 0.5) / (1 + weight))
    assert np.isnan(out.at[3, "prev_T_cb_rate"])  # team 3 was not there
    assert np.isnan(out.at[2, "prev_O_blown"])  # nor was its opponent
    assert out.at[3, "prev_O_blown"] == pytest.approx(
        runner.PRIOR_WEIGHT * runner.COMPLETION_PRIOR / runner.PRIOR_WEIGHT
    )
    assert out.at[3, "prev_league_oe"] == pytest.approx(1 / 0.5)


def test_last_season_needs_two_cohorts() -> None:
    rows = pd.DataFrame({"season_cohort": [2024], "team": [1]})
    assert runner.last_season(rows)["prev_league_oe"].isna().all()


def synthetic_rows(size: int = 3000, seed: int = 0) -> pd.DataFrame:
    """Team rows in 20 league-seasons and two cohorts, with every field random and the
    comeback driven by `tb_ppg_diff` beyond the yardstick's chance."""
    rng = np.random.default_rng(seed)
    rows = pd.DataFrame({field: rng.standard_normal(size) for field in runner.FAMILIES})
    for field in runner.BINARY:
        rows[field] = (rows[field] > 1).astype(float)

    rows["p_T"] = rng.uniform(0.15, 0.7, size)
    rows["lam_T"], rows["lam_O"] = rng.uniform(0.8, 2.0, size), rng.uniform(0.8, 2.0, size)
    rows["home"] = (np.arange(size) % 2).astype(float)
    rows["m_trail"] = rng.uniform(0.2, 0.5, size)
    rows["m_cb"] = rows["m_trail"] * rng.uniform(0.05, 0.15, size)
    rows["m_compl"] = rows["m_cb"] / rows["m_trail"]

    rows["behind"] = (rng.random(size) < rows["m_trail"]).astype(float)
    chance = 1 / (1 + np.exp(-(-1.5 + 1.0 * rows["tb_ppg_diff"])))
    rows["comes_back"] = rows["behind"] * (rng.random(size) < chance)

    rows["cluster"] = [f"c{i % 20}" for i in range(size)]
    rows["season_cohort"] = np.where(np.arange(size) % 20 < 10, 2024, 2025)
    rows.loc[rows["season_cohort"] == 2024, list(runner.LAST_SEASON)] = np.nan

    return rows


def test_field_test_finds_a_field_that_drives_the_outcome() -> None:
    rows = synthetic_rows()

    strong = runner.field_test(rows, "tb_ppg_diff", "comeback")

    assert strong["OR"] > 1.5
    assert strong["p"] < 1e-6
    assert strong["low"] < strong["OR"] < strong["high"]

    link_2 = runner.field_test(rows, "tb_ppg_diff", "link 2")
    assert link_2["n"] == rows["behind"].sum()


def test_screen_gives_each_field_once_sorted_by_p_with_holm() -> None:
    table = runner.screen(synthetic_rows())

    assert sorted(table["field"]) == sorted(runner.FAMILIES)
    assert table.at[0, "field"] == "tb_ppg_diff"
    assert (table["Holm"] >= table["p"]).all()
    assert table["p"].is_monotonic_increasing

    last_season = table[table["field"].isin(runner.LAST_SEASON)]
    assert last_season["OR 2024"].isna().all()


def test_joint_fields_leave_out_last_season_and_the_sum_of_the_halves() -> None:
    fields = runner.joint_fields()
    assert not set(fields) & (runner.LAST_SEASON | runner.JOINT_LEFT_OUT)
    assert len(fields) == len(runner.FAMILIES) - 4


def test_joint_design_fills_and_scales_with_the_training_rows() -> None:
    train = synthetic_rows(size=200)
    test = train.head(3).copy()
    test.loc[0, "tb_goal_env"] = np.nan

    design = runner.joint_design(test, train, ["tb_goal_env"])

    expected = (train["tb_goal_env"].median() - train["tb_goal_env"].mean()) / train[
        "tb_goal_env"
    ].std()
    assert design.shape == (3, 7)
    assert design[0, -1] == pytest.approx(expected)


def test_out_of_sample_scores_every_test_row() -> None:
    rows = synthetic_rows()
    train, test = rows[rows["season_cohort"] == 2024], rows[rows["season_cohort"] == 2025]
    scores = runner.out_of_sample(train, test)
    assert list(scores) == ["constant", "yardstick", "baseline", "baseline + all fields"]
    assert all(len(score) == len(test) for score in scores.values())
    assert scores["constant"][0] == pytest.approx(train["comes_back"].mean())


def test_auc_log_loss_and_top_hits() -> None:
    y = np.array([0.0, 0.0, 1.0, 1.0])
    assert runner.auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == 1.0
    assert runner.auc(y, np.array([0.9, 0.8, 0.2, 0.1])) == 0.0
    assert runner.auc(y, np.full(4, 0.5)) == 0.5
    assert runner.log_loss(y, np.full(4, 0.5)) == pytest.approx(np.log(2))
    assert runner.top_hits(y, np.array([0.1, 0.9, 0.8, 0.2]), 2) == 1


def test_score_table_gives_chance_hits_for_a_flat_score(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(runner, "TOP_N", (2,))
    y = np.array([0.0, 0.0, 1.0, 1.0])
    table = runner.score_table(
        y, {"flat": np.full(4, 0.5), "sharp": np.array([0.1, 0.2, 0.8, 0.9])}
    )
    assert table["top 2"].tolist() == [1.0, 2]


def test_split_rows_take_the_share_of_the_training_cohort(
    monkeypatch: pytest.MonkeyPatch, toy_priced_matches: pd.DataFrame
) -> None:
    seen: dict[str, float | None] = {}

    def frame(matches: pd.DataFrame, grid: object, share: float | None = None) -> pd.DataFrame:
        seen["share"] = share
        return matches

    monkeypatch.setattr(yardstick, "frame", frame)
    monkeypatch.setattr(runner, "screen_rows", lambda matches, model: model)
    monkeypatch.setattr(runner, "eligible", lambda rows: rows)

    rows, share = runner.split_rows(toy_priced_matches, None, 2024)  # type: ignore[arg-type]

    train = toy_priced_matches[toy_priced_matches["season_cohort"] == 2024]
    expected = yardstick.first_half_share(yardstick.priced(train))
    assert share == pytest.approx(expected)
    assert seen["share"] == pytest.approx(expected)
    assert len(rows) == len(toy_priced_matches)
