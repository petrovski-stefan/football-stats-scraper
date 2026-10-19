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


def with_cells(frame: pd.DataFrame, share: float) -> pd.DataFrame:
    """The frame plus the nine expected cells and one observed 0/1 column per cell."""
    cells = yardstick.htft_cells(frame["lam_home"].to_numpy(), frame["lam_away"].to_numpy(), share)
    out = frame.copy()
    out[cells.columns] = cells.to_numpy()
    full_time = (out["goals_home"] - out["goals_away"]).to_numpy()
    happened = (
        pd.Series(yardstick.result_code(out["ht_margin"].to_numpy()), index=out.index)
        + "/"
        + yardstick.result_code(full_time)
    )
    for cell in yardstick.HTFT:
        out[f"o_{cell}"] = (happened == cell).astype(float)
    return out


def cell_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Each HT/FT result: observed and expected counts, O/E with its interval, observed share."""
    rows = tuple((f"o_{cell}", f"m_{cell}", cell) for cell in yardstick.HTFT)
    table = stats.observed_expected_table(frame, rows).rename(columns={"quantity": "HT/FT"})
    table["observed share"] = table["observed"] / len(frame)
    return table


def top_n(frame: pd.DataFrame, observed: str, chance: str) -> pd.DataFrame:
    """The hit rate among the N matches with the highest yardstick chance, for each N.

    Ties at the cut go by match id, so the same N always takes the same matches. The
    interval resamples league-seasons; the lift is against the rate of all matches.
    """
    ranked = frame.sort_values([chance, "match_id"], ascending=[False, True])
    base = float(frame[observed].mean())
    rows = []
    for n in TOP_N:
        top = ranked.head(n)
        rate = float(top[observed].mean())
        low, high = stats.cluster_bootstrap_ci(top[observed], top["cluster"])
        rows.append(
            {
                "top": n,
                "hits": float(top[observed].sum()),
                "rate": rate,
                "low": low,
                "high": high,
                "yardstick": float(top[chance].mean()),
                "lift": rate / base,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    share = yardstick.first_half_share(yardstick.priced(matches))
    frame = with_cells(yardstick.frame(matches, yardstick.build_grid(), share=share), share)
    expected_sum = frame[[f"m_{cell}" for cell in yardstick.HTFT]].sum(axis=1)
    print(f"Priced: {len(frame):,} matches; first-half share {share:.4f}")
    sum_error = float((expected_sum - 1).abs().max())
    cb_error = float((frame["m_2/1"] - frame["m_cb_home"]).abs().max())
    print(f"largest distance of a match's nine chances from a sum of 1: {sum_error:.1e}")
    print(f"largest distance of m_2/1 from m_cb_home: {cb_error:.1e}")

    report.show("HT/FT results, observed against expected, all matches", cell_table(frame))
    for cohort, group in frame.groupby("season_cohort"):
        report.show(f"Season cohort {cohort} ({len(group):,} matches)", cell_table(group))
    for observed, chance, label in TARGETS:
        print(f"\nbase rate of {label}: {frame[observed].mean():.4f}")
        report.show(f"Top N by the yardstick's chance of {label}", top_n(frame, observed, chance))


if __name__ == "__main__":
    main()
