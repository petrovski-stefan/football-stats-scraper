"""The ML test on the schedule fields: is there comeback information beyond the odds?

Doc: `notes/ML/SCHEDULE/WHOLE_CORPUS/ALL/BEYOND_ODDS.md`; plan:
`notes/WORKING/PLAN_2026-10-19_ML_TEST.md`. One row per side of a priced match: is this team
behind at half-time, and does it win (`ml/rows.py`)? Model A reads the odds only; model B
reads the odds and every other pre-match field of the schedule; "B without league" leaves
out the league. Each is tuned and fitted on one season cohort (`ml/boosting.py`) and scored
on the other, both ways: the comebacks in the top N against model A, the log loss, the
calibration (`ml/score.py`). The odds yardstick, scaled to the training cohort, is one more
ranking, and the training base rate one more chance for the log loss. Then the SHAP values
of both B models show which fields they read. In each split, the yardstick's chances (fields
of both models) use the first-half share of the training cohort only (`split_rows`).

Run: `uv run python -m ml.schedule.whole_corpus.all.beyond_odds`
"""

import numpy as np
import pandas as pd

from analysis import corpus, report
from analysis.methods import yardstick
from ml import boosting, rows, score

SPLITS = ((2024, 2025), (2025, 2024))  # (training cohort, test cohort)
TOP_N = (100, 250, 500, 1000)
SHAP_TOP = 25
YARDSTICK = "m_comes_back"  # the yardstick's comeback chance of the side


NO_LEAGUE = "B without league"


def models(fields_b: list[str]) -> dict[str, list[str]]:
    """The fields of each model: A the odds; B the odds and every other field; B without the
    league, which shows what the other fields add on their own."""
    return {
        "A": list(rows.ODDS),
        "B": fields_b,
        NO_LEAGUE: [field for field in fields_b if field != rows.LEAGUE],
    }


def yardstick_chance(train: pd.DataFrame, test: pd.DataFrame) -> np.ndarray:
    """The yardstick's chance in the test rows, times its O/E in the training rows, so that
    it is calibrated as a whole, like the two models."""
    scale = train[rows.TARGET].sum() / train[YARDSTICK].sum()
    return np.asarray(test[YARDSTICK].to_numpy(dtype=float) * scale)


def importance(contributions: pd.DataFrame) -> pd.DataFrame:
    """Each field's mean absolute SHAP value, its share of the total, and whether it is an
    odds field (model A reads it) or not, largest first."""
    mean_abs = contributions.abs().mean()
    table = pd.DataFrame(
        {
            "field": mean_abs.index,
            "mean |SHAP|": mean_abs.to_numpy(),
            "share": (mean_abs / mean_abs.sum()).to_numpy(),
            "odds": [field in rows.ODDS for field in mean_abs.index],
        }
    )

    return table.sort_values("mean |SHAP|", ascending=False, ignore_index=True)


def tuning_table(tuned: dict[str, boosting.Tuned]) -> pd.DataFrame:
    """The chosen setting of each model, with its trees and its cross-validated log loss."""
    return pd.DataFrame(
        [
            {
                "model": name,
                **{key: result.params[key] for key in boosting.GRID[0]},
                "trees": result.trees,
                "cv loss": result.cv_loss,
            }
            for name, result in tuned.items()
        ]
    )


def run_split(
    side_rows: pd.DataFrame, fields_b: list[str], train_cohort: int, test_cohort: int
) -> None:
    """Tune, fit and score both models on one split, and print its tables."""
    train = side_rows[side_rows["season_cohort"] == train_cohort]
    test = side_rows[side_rows["season_cohort"] == test_cohort]
    comes_back = test[rows.TARGET].to_numpy(dtype=float)
    title = f"fit on {train_cohort}, scored on {test_cohort}"
    print(
        f"\n#### {title}: {len(train):,} training rows ({train[rows.TARGET].sum():.0f} "
        f"comebacks), {len(test):,} test rows ({comes_back.sum():.0f})"
    )

    chances = {"yardstick": yardstick_chance(train, test)}
    tuned, boosters = {}, {}
    for name, fields in models(fields_b).items():
        tuned[name] = boosting.tune(train, fields, rows.TARGET, train["cluster"])
        boosters[name] = boosting.fit(train, fields, rows.TARGET, tuned[name])
        chances[name] = boosting.predict(boosters[name], test, fields)

    report.show(f"{title}: the chosen settings", tuning_table(tuned))
    for name, result in tuned.items():
        report.show(f"{title}: every setting of model {name}", result.table)

    base_rate = np.full(len(test), train[rows.TARGET].mean())
    report.show(
        f"{title}: log loss",
        score.loss_table(comes_back, {"base rate": base_rate, **chances}, test["cluster"], "A"),
    )
    report.show(
        f"{title}: comebacks in the top N",
        score.top_n_table(comes_back, chances, test["cluster"], TOP_N, "A"),
    )

    for name in ("A", "B"):
        report.show(
            f"{title}: calibration of {name}", score.calibration_table(comes_back, chances[name])
        )

    model_fields = models(fields_b)
    for name in ("B", NO_LEAGUE):
        shap = importance(boosting.contributions(boosters[name], test, model_fields[name]))
        print(
            f"\n{title}: share of the |SHAP| of {name} in fields that are not odds fields: "
            f"{shap.loc[~shap['odds'], 'share'].sum():.4f}"
        )
        report.show(
            f"{title}: the fields of {name} by mean |SHAP| (top {SHAP_TOP})", shap.head(SHAP_TOP)
        )


def split_rows(
    matches: pd.DataFrame, grid: yardstick.Grid, train_cohort: int
) -> tuple[pd.DataFrame, list[str], float]:
    """The side rows of every priced match for one split, and model B's fields. The
    yardstick's chances use the first-half share of the training cohort only, so no goal of
    the test cohort reaches a field. Also that share."""
    train = matches[matches["season_cohort"] == train_cohort]
    share = yardstick.first_half_share(yardstick.priced(train))
    side_rows, fields_b = rows.side_rows(matches, yardstick.frame(matches, grid, share=share))

    return side_rows, fields_b, share


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    print(f"each interval: {score.DRAWS} resamples of whole league-seasons of the test cohort")

    grid = yardstick.build_grid()
    for train_cohort, test_cohort in SPLITS:
        side_rows, fields_b, share = split_rows(matches, grid, train_cohort)
        report.show("The rows", pd.DataFrame([rows.summary(side_rows, fields_b)]))
        print(f"the yardstick's first-half share, from the {train_cohort} cohort: {share:.4f}")
        run_split(side_rows, fields_b, train_cohort, test_cohort)


if __name__ == "__main__":
    main()
