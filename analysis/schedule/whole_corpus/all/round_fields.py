"""How often each value of the round-so-far fields (S3.14-20) occurs, and how to read S3.19-20.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/ROUND_FIELDS.md`. The fields count the
matches of the same round that finished before a kickoff, and their comebacks, 7+ matches,
rare events and both-teams-scored, and average their goals and opening O/U lines
(`notes/FIELDS/SCHEDULE_3_MULTI.md` §A2). Prints how often each count takes each value, for all
matches and per season cohort; the two averages and their difference; then the goals of a
match against its opening O/U line, and the line against the odds yardstick's expected goals
(`analysis/methods/yardstick.py`), which tell where a round that goes as priced reads.

Run: `uv run python -m analysis.schedule.whole_corpus.all.round_fields`
"""

import pandas as pd

from analysis import corpus, report
from analysis.methods import yardstick

COUNTS = (
    ("s3_round_pre_finished", "S3.14 finished"),
    ("s3_round_pre_comebacks", "S3.15 comebacks"),
    ("s3_round_pre_seven_plus", "S3.16 7+ goals"),
    ("s3_round_pre_rare_events", "S3.17 rare events"),
    ("s3_round_pre_btts", "S3.18 both teams scored"),
)
GOALS = "s3_round_pre_avg_goals"
LINE = "s3_round_pre_avg_ou_line"
OPENING_LINE = "s1_odds_ou_open_line"
LEVELS = (1, 2, 3)  # the shares of "at least this many"
MIN_LINE_MATCHES = 500  # an opening line with fewer matches gets no row of its own


def count_table(matches_df: pd.DataFrame) -> pd.DataFrame:
    """Per count: the share of matches at 0 and at each of `LEVELS` or more, the mean, the
    largest value."""

    rows = []
    for column, label in COUNTS:
        values = matches_df[column]
        row: dict[str, object] = {"field": label, "share 0": float((values == 0).mean())}
        row.update({f"share {n}+": float((values >= n).mean()) for n in LEVELS})
        row.update({"mean": float(values.mean()), "max": int(values.max())})
        rows.append(row)

    return pd.DataFrame(rows)


def average_table(matches_df: pd.DataFrame) -> pd.DataFrame:
    """S3.19, S3.20 and S3.19 - S3.20: the matches with a value and their share, the mean and
    the quartiles."""

    columns = {
        "S3.19 average goals": matches_df[GOALS],
        "S3.20 average O/U line": matches_df[LINE],
        "S3.19 - S3.20": matches_df[GOALS] - matches_df[LINE],
    }

    rows = []
    for label, values in columns.items():
        present = values.dropna()
        rows.append(
            {
                "field": label,
                "with a value": len(present),
                "share with a value": len(present) / len(values),
                "mean": float(present.mean()),
                "p25": float(present.quantile(0.25)),
                "median": float(present.median()),
                "p75": float(present.quantile(0.75)),
            }
        )

    return pd.DataFrame(rows)


def finished_without_line(matches_df: pd.DataFrame) -> int:
    """Rows with a finished round-mate whose averages are empty: no round-mate had a line."""

    return int((matches_df[GOALS].isna() & (matches_df["s3_round_pre_finished"] > 0)).sum())


def goals_over_line(matches_df: pd.DataFrame) -> pd.DataFrame:
    """A match's goals minus its opening O/U line: over all matches with a line, then per
    line with at least `MIN_LINE_MATCHES` matches."""

    with_line_df = matches_df.dropna(subset=[OPENING_LINE])
    excess = with_line_df["s2_total_goals"] - with_line_df[OPENING_LINE]
    by_line_df = excess.groupby(with_line_df[OPENING_LINE]).agg(["size", "mean"])
    common_lines_df = by_line_df[by_line_df["size"] >= MIN_LINE_MATCHES]

    rows = [{"line": "all", "matches": len(with_line_df), "goals minus line": float(excess.mean())}]
    rows += [
        {"line": f"{line:g}", "matches": int(row["size"]), "goals minus line": float(row["mean"])}
        for line, row in common_lines_df.iterrows()
    ]

    return pd.DataFrame(rows)


def line_against_model(yardstick_df: pd.DataFrame) -> dict[str, float]:
    """The opening O/U line against the yardstick's expected goals: their correlation, and
    the mean of the expected goals minus the line."""

    return {
        "matches": float(len(yardstick_df)),
        "correlation": float(yardstick_df["line"].corr(yardstick_df["m_goals"])),
        "expected goals minus line": float((yardstick_df["m_goals"] - yardstick_df["line"]).mean()),
    }


def main() -> None:
    """Entry point: print how often each value of the round-so-far fields occurs."""

    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    report.show("The counts, all matches", count_table(matches_df))
    report.show("The averages, all matches", average_table(matches_df))
    for cohort, cohort_df in matches_df.groupby("season_cohort"):
        size = f"season cohort {cohort} ({len(cohort_df):,} matches)"
        report.show(f"The counts, {size}", count_table(cohort_df))
        report.show(f"The averages, {size}", average_table(cohort_df))

    print(
        f"\nrows with a finished round-mate but empty averages: {finished_without_line(matches_df)}"
    )
    report.show("Goals minus the opening O/U line", goals_over_line(matches_df))

    yardstick_df = yardstick.frame(matches_df, yardstick.build_grid())
    report.show(
        "The opening O/U line against the yardstick's expected goals",
        pd.DataFrame([line_against_model(yardstick_df)]),
    )


if __name__ == "__main__":
    main()
