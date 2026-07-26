"""One-off migration: add match_index_in_round / matches_in_round to existing league CSVs.

Replaces the three DOM-order booleans (is_first_match_in_round,
is_before_last_match_in_round, is_last_match_in_round) with an explicit kickoff-ordered
index. See notes and CLAUDE.md "Domain notes".

Exact for this corpus because all 216 stored rounds are complete, so "index over every
scheduled match" — what the scraper now computes, with unplayed rows visible — equals
"index over the finished rows present here". It would understate `matches_in_round` for a
partially-played round, which is why it is a migration and not a permanent code path.

Reuses `domain.match.round_sort_key`, the same ordering the scraper applies, so backfilled
and freshly-scraped data cannot disagree.

Run: `uv run python -m scripts.backfill_round_index [--dry-run]`
Delete this file once the corpus is migrated.
"""

import argparse
import glob
import os
from typing import Any, cast

import pandas as pd

from domain.columns import ORDERED_DF_COLUMNS
from domain.match import round_sort_key
from features.engine import round_position
from scrapers.csv_io import write_ordered_csv

DATA_DIR = "data"
DROPPED = ["is_first_match_in_round", "is_before_last_match_in_round", "is_last_match_in_round"]
ROUND_KEY = ["season", "league_id", "stage", "round"]


def _base_csvs() -> list[str]:
    return [
        p
        for p in sorted(glob.glob(os.path.join(DATA_DIR, "*.csv")))
        if not p.endswith("_detail.csv") and not p.endswith("_enriched.csv")
    ]


def backfill(df: pd.DataFrame) -> pd.DataFrame:
    """Assign match_index_in_round / matches_in_round per round, by kickoff order."""
    df = df.copy()
    df["_key"] = list(
        zip(
            df["date"].astype(str),
            df["home_team_name"].astype(str),
            df["away_team_name"].astype(str),
            strict=True,
        )
    )
    df["_sort"] = [round_sort_key(*key) for key in df["_key"]]

    keys = [c for c in ROUND_KEY if c in df.columns]
    index = pd.Series(0, index=df.index, dtype=int)
    for _, group in df.groupby(keys, dropna=False):
        for position, row_index in enumerate(group["_sort"].sort_values().index, 1):
            index.at[row_index] = position

    df["match_index_in_round"] = index
    df["matches_in_round"] = df.groupby(keys, dropna=False)["match_index_in_round"].transform(
        "size"
    )
    return df.drop(columns=["_key", "_sort", *[c for c in DROPPED if c in df.columns]])


def _verify(before: pd.DataFrame, after: pd.DataFrame, path: str) -> list[str]:
    """The pre-change measurement said DOM order was chronological in 216/216 rounds.

    So every row the old booleans flagged must still sit at that extreme of its round.
    Note the check is against `earlier == 0` / `later == 0`, **not** `index == 1` /
    `index == N`: where several matches share the extreme kickoff, the old DOM order and
    the new alphabetical tiebreak pick different ones, and both are equally arbitrary.
    Asserting index equality here would be the very mistake this change exists to prevent
    (it fired on 6 rows across 3 files, all of them legitimate ties).
    """
    problems: list[str] = []
    keys = [c for c in ROUND_KEY if c in after.columns]
    for key, group in after.groupby(keys, dropna=False):
        n = len(group)
        if sorted(group["match_index_in_round"]) != list(range(1, n + 1)):
            problems.append(f"{path} round {key}: index is not exactly 1..{n}")

    if "is_first_match_in_round" not in before.columns:
        return problems

    position = round_position(after)
    joined = after.join(before[DROPPED], rsuffix="_old").join(position)
    first_bad = joined[joined["is_first_match_in_round"] & (joined["earlier"] != 0)]
    last_bad = joined[joined["is_last_match_in_round"] & (joined["later"] != 0)]
    if len(first_bad):
        problems.append(
            f"{path}: {len(first_bad)} old is_first rows are not at the earliest kickoff"
        )
    if len(last_bad):
        problems.append(f"{path}: {len(last_bad)} old is_last rows are not at the latest kickoff")
    return problems


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="verify without writing")
    args = parser.parse_args()

    all_problems: list[str] = []
    for path in _base_csvs():
        before = pd.read_csv(path)
        after = backfill(before)
        problems = _verify(before, after, os.path.basename(path))
        all_problems.extend(problems)

        rounds = after.groupby([c for c in ROUND_KEY if c in after.columns], dropna=False).ngroups
        status = "OK" if not problems else f"{len(problems)} PROBLEM(S)"
        print(f"[{status}] {os.path.basename(path)}: {len(after)} rows, {rounds} rounds")
        for problem in problems:
            print(f"    - {problem}")

        if not args.dry_run and not problems:
            rows = cast(list[dict[str, Any]], after.to_dict("records"))
            write_ordered_csv(rows, path, ORDERED_DF_COLUMNS)

    if all_problems:
        raise SystemExit(1)
    if args.dry_run:
        print("\ndry run — nothing written")


if __name__ == "__main__":
    main()
