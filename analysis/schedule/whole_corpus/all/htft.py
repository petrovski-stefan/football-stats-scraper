"""The nine half-time/full-time results on the whole corpus, all matches pooled.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/ALL/HTFT.md`. Against the odds yardstick
(`ALL/ODDS_YARDSTICK.md`), prints each HT/FT result observed against expected, for all
matches and per season cohort; then the hit rate in the yardstick's own top N for a comeback
and for 7+ goals: the bar that a candidate rule must beat.

Run: `uv run python -m analysis.schedule.whole_corpus.all.htft`
"""

import pandas as pd

from analysis import corpus, report, stats
from analysis.methods import yardstick

TOP_N = (100, 250, 500, 1000, 2000, 5000)
# (observed column, the yardstick's chance, label) for the top-N tables.
TARGETS = (("is_comeback", "m_cb", "comeback"), ("seven", "m_seven", "7+ goals"))


def with_cells(yardstick_df: pd.DataFrame, share: float) -> pd.DataFrame:
    """The frame plus the nine expected cells and one observed 0/1 column per cell."""

    cells_df = yardstick.htft_cells(
        yardstick_df["lam_home"].to_numpy(), yardstick_df["lam_away"].to_numpy(), share
    )
    yardstick_cells_df = yardstick_df.copy()
    yardstick_cells_df[cells_df.columns] = cells_df.to_numpy()

    full_time = (yardstick_cells_df["goals_home"] - yardstick_cells_df["goals_away"]).to_numpy()
    happened = (
        pd.Series(
            yardstick.result_code(yardstick_cells_df["ht_margin"].to_numpy()),
            index=yardstick_cells_df.index,
        )
        + "/"
        + yardstick.result_code(full_time)
    )

    for cell in yardstick.HTFT:
        yardstick_cells_df[f"o_{cell}"] = (happened == cell).astype(float)

    return yardstick_cells_df


def cell_table(yardstick_df: pd.DataFrame) -> pd.DataFrame:
    """Each HT/FT result: observed and expected counts, O/E with its interval, observed share."""

    rows = tuple((f"o_{cell}", f"m_{cell}", cell) for cell in yardstick.HTFT)
    cell_table_df = stats.observed_expected_table(yardstick_df, rows).rename(
        columns={"quantity": "HT/FT"}
    )
    cell_table_df["observed share"] = cell_table_df["observed"] / len(yardstick_df)

    return cell_table_df


def top_n(yardstick_df: pd.DataFrame, observed: str, chance: str) -> pd.DataFrame:
    """The hit rate among the N matches with the highest yardstick chance, for each N.

    Ties at the cut go by match id, so the same N always takes the same matches. The
    interval resamples league-seasons; the lift is against the rate of all matches.
    """

    ranked_df = yardstick_df.sort_values([chance, "match_id"], ascending=[False, True])
    base = float(yardstick_df[observed].mean())

    rows = []
    for top_count in TOP_N:
        top_df = ranked_df.head(top_count)
        rate = float(top_df[observed].mean())
        low, high = stats.cluster_bootstrap_ci(top_df[observed], top_df["cluster"])

        rows.append(
            {
                "top": top_count,
                "hits": float(top_df[observed].sum()),
                "rate": rate,
                "low": low,
                "high": high,
                "yardstick": float(top_df[chance].mean()),
                "lift": rate / base,
            }
        )

    return pd.DataFrame(rows)


def main() -> None:
    """Entry point: print the nine half-time/full-time results against the odds yardstick."""

    matches_df = corpus.load()
    print(corpus.corpus_line(matches_df))

    share = yardstick.first_half_share(yardstick.priced(matches_df))
    yardstick_df = with_cells(
        yardstick.frame(matches_df, yardstick.build_grid(), share=share), share
    )

    expected_sum = yardstick_df[[f"m_{cell}" for cell in yardstick.HTFT]].sum(axis=1)
    print(f"Priced: {len(yardstick_df):,} matches; first-half share {share:.4f}")

    sum_error = float((expected_sum - 1).abs().max())
    cb_error = float((yardstick_df["m_2/1"] - yardstick_df["m_cb_home"]).abs().max())
    print(f"largest distance of a match's nine chances from a sum of 1: {sum_error:.1e}")
    print(f"largest distance of m_2/1 from m_cb_home: {cb_error:.1e}")

    report.show("HT/FT results, observed against expected, all matches", cell_table(yardstick_df))
    for cohort, cohort_df in yardstick_df.groupby("season_cohort"):
        report.show(f"Season cohort {cohort} ({len(cohort_df):,} matches)", cell_table(cohort_df))

    for observed, chance, label in TARGETS:
        print(f"\nbase rate of {label}: {yardstick_df[observed].mean():.4f}")
        report.show(
            f"Top N by the yardstick's chance of {label}", top_n(yardstick_df, observed, chance)
        )


if __name__ == "__main__":
    main()
