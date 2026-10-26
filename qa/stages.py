"""Checks that the derived schedule files agree with stage 1
(`data/finished/2_row/` and `data/finished/3_multi/`).

Each stage file is the stage before it plus its own columns, rebuilt from stage 1 by
`features/schedule_row.py` and `features/schedule_multi.py`. A stage file that holds other
matches than stage 1, or a value an earlier stage no longer holds, was built before the
earlier file last changed (a re-scrape) and must be rebuilt. Stage 2's odds fields are also
held to the stage-1 cells they come from, and stage 3's round-so-far counts to the rules
between them. Nothing here recomputes a field: the builders' tests do that.
"""

import os
from collections.abc import Collection, Mapping, Sequence
from typing import Any

import numpy as np
import pandas as pd

from domain import paths
from domain.columns import SCHEDULE_MULTI_COLUMNS, SCHEDULE_RAW_COLUMNS, SCHEDULE_ROW_COLUMNS
from qa.report import Report
from qa.schedule import STAGED_ODDS

# The columns each stage adds to the one before it.
_ADDED: dict[int, list[str]] = {
    1: SCHEDULE_RAW_COLUMNS,
    2: SCHEDULE_ROW_COLUMNS,
    3: SCHEDULE_MULTI_COLUMNS,
}
# Slack for floating-point rounding: a CSV round trip may move a long float's last digit,
# and three probabilities may miss a sum of 1 by rounding. Any real change is far larger.
# Measured 2026-10-11: 129 `s2_mkt_sup` / `s2_mkt_tot` cells differ between stages 2 and 3,
# none by more than 1 unit in the last place; an exact comparison would fail them all.
TOLERANCE = 1e-9
# Each market's stage-2 flag, and the stage-2 values computed from its cells
# (`notes/FIELDS/SCHEDULE_2_ROW.md`).
_MARKET_FIELDS: dict[str, tuple[str, tuple[str, ...]]] = {
    "1X2": (
        "s2_has_odds",
        ("s2_mkt_p_home", "s2_mkt_p_draw", "s2_mkt_p_away", "s2_mkt_sup", "s2_mkt_tot"),
    ),
    "OU": ("s2_has_ou_odds", ("s2_implied_over",)),
    "AH": ("s2_has_ah_odds", ("s2_implied_ah_home",)),
}
_PROBABILITIES = ["s2_mkt_p_home", "s2_mkt_p_draw", "s2_mkt_p_away"]
# The round so far (S3.14-20, `notes/FIELDS/SCHEDULE_3_MULTI.md`) and the size of the round.
_ROUND = [
    "s3_matches_in_round",
    "s3_round_pre_finished",
    "s3_round_pre_comebacks",
    "s3_round_pre_seven_plus",
    "s3_round_pre_rare_events",
    "s3_round_pre_btts",
    "s3_round_pre_avg_goals",
    "s3_round_pre_avg_ou_line",
]


def declared_columns(stage: int) -> list[str]:
    """Every column a stage's file must hold: its own and all the earlier stages'."""

    columns: list[str] = []
    for stage_number in range(1, stage + 1):
        columns += _ADDED[stage_number]

    return columns


def validate(
    report: Report, stage_file_df: pd.DataFrame, stage: int, earlier: Mapping[int, pd.DataFrame]
) -> None:
    """One derived stage file: each earlier stage's columns carried over unchanged, the odds
    fields at stage 2 and the round-so-far fields at stage 3. The universal checks (declared
    columns, the key) are `qa/validate.py`'s, as for stage 1.

    Args:
        earlier: each earlier stage mapped to its file.
    """

    for earlier_stage, earlier_df in earlier.items():
        check_carried(
            report, earlier_df, stage_file_df, _ADDED[earlier_stage], f"stage {earlier_stage}"
        )

    if stage == 2:
        check_odds_fields(report, stage_file_df)
    if stage == 3:
        check_round_fields(report, stage_file_df)


def check_carried(
    report: Report,
    earlier_df: pd.DataFrame,
    later_df: pd.DataFrame,
    columns: Sequence[str],
    source: str,
) -> None:
    """`later_df` holds the matches of `earlier_df`, no more and no fewer, with the same value
    in each of `columns`."""

    if not (_pairable(earlier_df) and _pairable(later_df)):
        return

    earlier_by_id_df, later_by_id_df = (
        earlier_df.set_index("match_id"),
        later_df.set_index("match_id"),
    )
    missing = earlier_by_id_df.index.difference(later_by_id_df.index)
    extra = later_by_id_df.index.difference(earlier_by_id_df.index)

    report.check(missing.empty, f"{len(missing)} matches of {source} missing (stale: rebuild)")
    report.check(extra.empty, f"{len(extra)} matches not in {source} (stale: rebuild)")

    shared = earlier_by_id_df.index.intersection(later_by_id_df.index)
    names = [
        column
        for column in columns
        if column in earlier_by_id_df.columns and column in later_by_id_df.columns
    ]
    differ = {
        column: int(
            (~_same(earlier_by_id_df.loc[shared, column], later_by_id_df.loc[shared, column])).sum()
        )
        for column in names
    }
    changed = {column: n for column, n in differ.items() if n}

    report.check(
        not changed,
        f"{sum(changed.values())} values differ from {source} (column: count) "
        f"{dict(list(changed.items())[:5])} (stale: rebuild)",
    )


def _pairable(stage_file_df: pd.DataFrame) -> bool:
    """Rows pair up by `match_id`: the column is there and no id repeats. Otherwise the
    file's own key check reports it."""

    return "match_id" in stage_file_df.columns and not stage_file_df["match_id"].duplicated().any()


def _same(old: "pd.Series[Any]", new: "pd.Series[Any]") -> "pd.Series[bool]":
    """Equal, or both empty. Floats compare within `TOLERANCE`."""

    both_empty = old.isna() & new.isna()

    if pd.api.types.is_float_dtype(old) and pd.api.types.is_float_dtype(new):
        close = np.isclose(old.to_numpy(), new.to_numpy(), rtol=TOLERANCE, atol=0.0)
        return pd.Series(close, index=old.index) | both_empty

    return (old == new) | both_empty


def check_odds_fields(report: Report, stage_file_df: pd.DataFrame) -> None:
    """Stage 2's odds fields agree with the row's stage-1 cells: each `s2_has_*` flag is true
    exactly when its market's three cells are filled, each value from a market is there exactly
    when the market is, and the three margin-free 1X2 probabilities sum to 1."""

    markets = STAGED_ODDS.markets()
    for kind, (flag, value_columns) in _MARKET_FIELDS.items():
        cells = markets[kind]
        if not {flag, *cells, *value_columns} <= set(stage_file_df.columns):
            continue

        present = stage_file_df[list(cells)].notna().all(axis=1)
        flags = int((stage_file_df[flag].eq(True) != present).sum())
        report.check(flags == 0, f"{flags} rows where {flag} disagrees with the {kind} cells")

        computed_df = stage_file_df[list(value_columns)].notna()
        stray = int(computed_df.ne(present, axis=0).any(axis=1).sum())
        report.check(
            stray == 0,
            f"{stray} rows with a value computed from {kind} that is there without the "
            f"market, or missing with it",
        )

    if set(_PROBABILITIES) <= set(stage_file_df.columns):
        total = stage_file_df[_PROBABILITIES].sum(axis=1, min_count=len(_PROBABILITIES))
        off = int(((total - 1).abs() > TOLERANCE).sum())
        report.check(off == 0, f"{off} rows whose 1X2 probabilities do not sum to 1")


def check_round_fields(report: Report, stage_file_df: pd.DataFrame) -> None:
    """The round-so-far counts agree in every row: a rare event is a comeback or a 7+ match,
    once if both; fewer round-mates finished than the round holds (a match never counts
    itself); both teams scored in every comeback; the two averages are empty together."""

    if not set(_ROUND) <= set(stage_file_df.columns):
        return

    (size, finished, comebacks, seven, rare, btts, goals, line) = (stage_file_df[c] for c in _ROUND)
    broken = {
        "s3_round_pre_rare_events is above comebacks + seven_plus": rare > comebacks + seven,
        "s3_round_pre_rare_events is below the larger of comebacks and seven_plus": (
            rare < np.maximum(comebacks, seven)
        ),
        "s3_round_pre_finished is not below s3_matches_in_round": finished >= size,
        "s3_round_pre_btts is above s3_round_pre_finished": btts > finished,
        "s3_round_pre_comebacks is above s3_round_pre_btts": comebacks > btts,
        "only one of the two round averages is empty": goals.isna() != line.isna(),
    }

    for rule, rows in broken.items():
        count = int(rows.sum())
        report.check(count == 0, f"{count} rows where {rule}")


def check_no_orphans(
    report: Report, raw_paths: Collection[str], later_paths: Collection[str], stage: int
) -> None:
    """Every stage-`stage` file has its stage-1 file. One without it belongs to a
    league-season no longer in the project, and would still be read with the rest."""

    expected = {
        os.path.normpath(paths.schedule_at_stage(schedule_path, stage))
        for schedule_path in raw_paths
    }
    orphans = sorted(
        os.path.basename(schedule_path)
        for schedule_path in later_paths
        if os.path.normpath(schedule_path) not in expected
    )

    report.check(
        not orphans, f"{len(orphans)} stage-{stage} files without a stage-1 file {orphans[:3]}"
    )
