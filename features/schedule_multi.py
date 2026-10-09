"""Stage 3 of the schedule: the fields that need the league-season's other rows.

Reads `data/finished/2_row/<country>_<league>_<season>_schedule.csv` and writes the same rows plus
the `s3_` columns to `data/finished/3_multi/` (`notes/fields/schedule_3_multi.md`). The
output is the schedule's analysis input: one row per match.

This is the only schedule stage where another match's result can enter a row, so each
field's row window is stated where it is built:

- the round position reads other rows' kickoff times, never their results;
- the pre-kickoff table and the half-time / full-time record count a match only if it
  kicked off at least 2 h 30 min before this one, so it had surely finished (the user's
  rule, 2026-10-06).

Run: `uv run python -m features.schedule_multi`
"""

import logging
from collections.abc import Iterator
from datetime import timedelta
from typing import Any, NamedTuple

import pandas as pd

from domain import paths
from domain.clock import parse_instant
from domain.columns import (
    HTFT_RESULTS,
    SCHEDULE_MULTI_COLUMNS,
    SCHEDULE_RAW_COLUMNS,
    SCHEDULE_ROW_COLUMNS,
    STANDING_VENUES,
    pre_htft_columns,
    pre_kickoff_columns,
)
from domain.standings import HalfTimeFullTime, Standings
from features.stage_io import read_stage_csv, write_stage_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

# A match counts in another's table only if it kicked off at least this long before. A
# normal match is over about 1 h 55 min after kickoff.
FINISHED_AFTER = timedelta(hours=2, minutes=30)

_ROUND_KEY = ["s1_stage", "s1_round"]


class _Match(NamedTuple):
    index: Any
    kickoff: Any
    home: int
    away: int
    ft: tuple[int, int]
    ht: tuple[int, int]


def round_positions(frame: pd.DataFrame) -> pd.DataFrame:
    """`s3_match_index_in_round` and `s3_matches_in_round`, from kickoff times only.

    The position is 1.. by kickoff within (stage, round); team names break ties, which
    makes the order reproducible but carries no meaning. The count is the round's finished
    matches: the finished tree holds no unplayed rows.
    """
    keyed = frame.assign(_kickoff=frame["s1_date"].map(parse_instant))
    ordered = keyed.sort_values([*_ROUND_KEY, "_kickoff", "s1_home_team_name", "s1_away_team_name"])
    groups = ordered.groupby(_ROUND_KEY, sort=False)
    positions = pd.DataFrame(
        {
            "s3_match_index_in_round": groups.cumcount() + 1,
            "s3_matches_in_round": groups["match_id"].transform("size"),
        }
    )
    return positions.reindex(frame.index)


def _matches_by_kickoff(group: pd.DataFrame) -> list[_Match]:
    rows = group.assign(_kickoff=group["s1_date"].map(parse_instant)).sort_values("_kickoff")
    return [
        _Match(
            index,
            row["_kickoff"],
            int(row["s1_home_team_id"]),
            int(row["s1_away_team_id"]),
            (int(row["s1_ft_home_goals"]), int(row["s1_ft_away_goals"])),
            (int(row["s1_ht_home_goals"]), int(row["s1_ht_away_goals"])),
        )
        for index, row in rows.iterrows()
    ]


def _lines(tables: dict[str, Standings], team: int, side: str) -> dict[str, int | None]:
    """One team's stats in the FT and HT tables, as `s3_<side>_pre_<half>_<venue>_<stat>`."""
    out: dict[str, int | None] = {}
    for half, table in tables.items():
        for venue in STANDING_VENUES:
            line = table.line(venue, team)
            prefix = f"s3_{side}_pre_{half}_{venue}_"
            out[prefix + "rank"] = table.ranks(venue).get(team)
            out[prefix + "played"] = line.played
            out[prefix + "won"] = line.won
            out[prefix + "drawn"] = line.drawn
            out[prefix + "lost"] = line.lost
            out[prefix + "goals_for"] = line.goals_for
            out[prefix + "goal_diff"] = line.goal_diff
            out[prefix + "points"] = line.points
    return out


def _htft(record: HalfTimeFullTime, team: int, side: str) -> dict[str, int | None]:
    """One team's HT/FT record, as `s3_<side>_pre_htft_<venue>_<ht>_<ft>` (team view)."""
    return {
        f"s3_{side}_pre_htft_{venue}_{ht}_{ft}": record.count(venue, team, ht.upper(), ft.upper())
        for venue in STANDING_VENUES
        for ht in HTFT_RESULTS
        for ft in HTFT_RESULTS
    }


def _stage_tables(group: pd.DataFrame) -> Iterator[tuple[Any, dict[str, int | None]]]:
    """Each match of one stage with both teams' lines and HT/FT records at its kickoff."""
    matches = _matches_by_kickoff(group)
    teams = {m.home for m in matches} | {m.away for m in matches}
    tables = {"ft": Standings(teams), "ht": Standings(teams)}
    record = HalfTimeFullTime(teams)
    counted = 0
    for match in matches:
        # Sorted by kickoff, so the counted matches are always a prefix of the list.
        while counted < len(matches) and matches[counted].kickoff <= match.kickoff - FINISHED_AFTER:
            done = matches[counted]
            tables["ft"].add(done.home, done.away, *done.ft)
            tables["ht"].add(done.home, done.away, *done.ht)
            record.add(done.home, done.away, done.ht, done.ft)
            counted += 1
        yield (
            match.index,
            {
                **_lines(tables, match.home, "home"),
                **_lines(tables, match.away, "away"),
                **_htft(record, match.home, "home"),
                **_htft(record, match.away, "away"),
            },
        )


def pre_kickoff_tables(frame: pd.DataFrame) -> pd.DataFrame:
    """Both teams' standings (96 columns), `s3_pre_rank_gap` and HT/FT records (54).

    One table and one record per stage, each counting only the matches that kicked off at
    least `FINISHED_AFTER` before this one.
    """
    rows: dict[Any, dict[str, int | None]] = {}
    for _, group in frame.groupby("s1_stage", sort=False):
        rows.update(_stage_tables(group))
    tables = pd.DataFrame.from_dict(rows, orient="index").reindex(
        index=frame.index, columns=pre_kickoff_columns() + pre_htft_columns()
    )
    gap = (tables["s3_home_pre_ft_total_rank"] - tables["s3_away_pre_ft_total_rank"]).abs()
    return tables.assign(s3_pre_rank_gap=gap).astype("Int64")


def build(row_path: str) -> str:
    """Write the stage-3 file for one stage-2 schedule file; return its path."""
    frame = read_stage_csv(row_path)
    out = pd.concat([frame, round_positions(frame), pre_kickoff_tables(frame)], axis=1)
    out_path = paths.schedule_at_stage(row_path, 3)
    columns = SCHEDULE_RAW_COLUMNS + SCHEDULE_ROW_COLUMNS + SCHEDULE_MULTI_COLUMNS
    write_stage_csv(out, out_path, columns)
    logger.info("%s: %d rows -> %s", row_path, len(frame), out_path)
    return out_path


def build_all() -> None:
    row_paths = paths.schedule_csvs(2)
    if not row_paths:
        logger.warning("No stage-2 schedule files in %s", paths.stage_dir(2))
    for row_path in row_paths:
        build(row_path)


def main() -> None:
    build_all()


if __name__ == "__main__":
    main()
