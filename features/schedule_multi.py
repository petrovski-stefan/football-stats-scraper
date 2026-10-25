"""Stage 3 of the schedule: the fields that need the league-season's other rows.

Reads `data/finished/2_row/<country>_<league>_<season>_schedule.csv` and writes the same rows plus
the `s3_` columns to `data/finished/3_multi/` (`notes/FIELDS/SCHEDULE_3_MULTI.md`). The
output is the schedule's analysis input: one row per match.

This is the only schedule stage where another match's result can enter a row, so each
field's row window is stated where it is built:

- the round position and the round offset read other rows' kickoff times, never their results;
- the round so far (the user, 2026-10-13) counts the matches of the same round that kicked off
  at least 2 h 30 min and less than `ROUND_LOOK_BACK` before this one, which of them were a
  comeback, had 7+ goals or both teams scoring, and their average goals and opening O/U line;
- the pre-kickoff table and the half-time / full-time record count a match only if it
  kicked off at least 2 h 30 min before this one, so it had surely finished (the user's
  rule, 2026-10-06);
- what is at stake (the user, 2026-10-12): the matches left read the stage's fixture list,
  never a result; the points gaps read the pre-kickoff table; the rank change compares it
  with the table as it stood `OPEN_LEAD` before kickoff, under the same 2 h 30 min rule.

Run: `uv run python -m features.schedule_multi`
"""

import logging
from collections import Counter
from collections.abc import Iterator
from datetime import timedelta
from itertools import product
from typing import Any, NamedTuple

import numpy as np
import pandas as pd

from domain import paths, stats
from domain.clock import parse_instant
from domain.columns import (
    HTFT_RESULTS,
    SCHEDULE_MULTI_COLUMNS,
    SCHEDULE_RAW_COLUMNS,
    SCHEDULE_ROW_COLUMNS,
    STANDING_VENUES,
    pre_htft_columns,
    pre_kickoff_columns,
    stake_columns,
)
from domain.standings import HalfTimeFullTime, Standings
from features.stage_io import read_stage_csv, write_stage_csv

logger = logging.getLogger(__name__)

# A match counts in another's table only if it kicked off at least this long before. A
# normal match is over about 1 h 55 min after kickoff.
FINISHED_AFTER = timedelta(hours=2, minutes=30)

# A match this many days or more from its round's median kickoff was rescheduled. Measured on
# 2026-10-10 over 82 leagues: 1,155 matches (2.8%) at 5 days, 1,114 at 7, so 5 is where the
# count stops falling; under 5 a long round (Friday to Monday, a split midweek) still counts.
RESCHEDULED_AFTER_DAYS = 5

# The round so far counts only round-mates that kicked off less than this before: the same 5
# days that mark a rescheduled match, so a match played weeks earlier (brought forward, or the
# rest of the round for a postponed one) is not "this round so far". It never reads a later
# kickoff (Claude's choice, 2026-10-13, asked by the user).
ROUND_LOOK_BACK = timedelta(days=RESCHEDULED_AFTER_DAYS)

# The opening odds (Bet365's "Initial") are published about this long before kickoff (the
# user, 2026-10-10: "usually about 7 days", more or fewer by league). A result between then
# and kickoff is news the opening odds cannot hold; `s3_<side>_rank_change_since_open`
# measures how far such results moved the table.
OPEN_LEAD = timedelta(days=7)

_ROUND_KEY = ["s1_stage", "s1_round"]


class _Match(NamedTuple):
    """One finished match of a stage, as the table builders read it."""

    index: Any
    kickoff: Any
    home: int
    away: int
    ft: tuple[int, int]
    ht: tuple[int, int]


def round_positions(schedule_df: pd.DataFrame) -> pd.DataFrame:
    """`s3_match_index_in_round` and `s3_matches_in_round`, from kickoff times only.

    The position is 1.. by kickoff within (stage, round), ties broken by team names: reproducible
    but meaningless. The count is the round's finished matches, the only rows the tree holds.
    """

    with_kickoff_df = schedule_df.assign(_kickoff=schedule_df["s1_date"].map(parse_instant))
    ordered_df = with_kickoff_df.sort_values(
        [*_ROUND_KEY, "_kickoff", "s1_home_team_name", "s1_away_team_name"]
    )
    groups = ordered_df.groupby(_ROUND_KEY, sort=False)

    positions_df = pd.DataFrame(
        {
            "s3_match_index_in_round": groups.cumcount() + 1,
            "s3_matches_in_round": groups["match_id"].transform("size"),
        }
    )

    return positions_df.reindex(schedule_df.index)


def round_offsets(schedule_df: pd.DataFrame) -> pd.DataFrame:
    """`s3_days_off_round` and `s3_is_rescheduled`, from kickoff times only.

    Days from the median kickoff of the match's (stage, round), positive when played after it;
    `RESCHEDULED_AFTER_DAYS` or more either way is rescheduled (S3.09, S3.10).
    """

    kickoff = pd.to_datetime(schedule_df["s1_date"].map(parse_instant), utc=True)
    median = kickoff.groupby([schedule_df[key] for key in _ROUND_KEY], dropna=False).transform(
        "median"
    )
    days = (kickoff - median).dt.total_seconds() / 86400

    return pd.DataFrame(
        {"s3_days_off_round": days, "s3_is_rescheduled": days.abs() >= RESCHEDULED_AFTER_DAYS},
        index=schedule_df.index,
    )


def round_so_far(schedule_df: pd.DataFrame) -> pd.DataFrame:
    """The round so far: the `s3_round_pre_*` fields (`notes/FIELDS/SCHEDULE_3_MULTI.md` §A2).

    Reads the round-mates of the same (stage, round) that kicked off at least `FINISHED_AFTER`
    and less than `ROUND_LOOK_BACK` before this one; the first kickoff of a round sees 0.
    """

    with_kickoff_df = schedule_df.assign(
        _kickoff=pd.to_datetime(schedule_df["s1_date"].map(parse_instant), utc=True)
    )
    parts = [
        _round_counts(round_df) for _, round_df in with_kickoff_df.groupby(_ROUND_KEY, sort=False)
    ]

    return pd.concat(parts).reindex(schedule_df.index)


def _round_counts(round_df: pd.DataFrame) -> pd.DataFrame:
    """`round_so_far` for one (stage, round)."""

    kickoff = round_df["_kickoff"].to_numpy(dtype="datetime64[ns]")

    # Row: this match; column: a round-mate. True where the round-mate counts.
    gap = kickoff[:, None] - kickoff[None, :]
    counted = (gap >= pd.Timedelta(FINISHED_AFTER).to_timedelta64()) & (
        gap < pd.Timedelta(ROUND_LOOK_BACK).to_timedelta64()
    )

    goals = round_df["s2_total_goals"].to_numpy(dtype=float)
    comeback = round_df["s2_is_comeback"].to_numpy(dtype=bool)
    seven_plus = goals >= stats.SEVEN_PLUS_GOALS
    btts = np.array(
        [
            stats.is_btts(home_goals, away_goals)
            for home_goals, away_goals in zip(
                round_df["s1_ft_home_goals"], round_df["s1_ft_away_goals"], strict=True
            )
        ],
        dtype=bool,
    )

    line = round_df["s1_odds_ou_open_line"].to_numpy(dtype=float)
    priced = counted & ~np.isnan(line)
    with np.errstate(invalid="ignore"):
        # 0 / 0 where no counted round-mate has a line: empty, not zero.
        avg_goals = np.where(priced, goals, 0.0).sum(axis=1) / priced.sum(axis=1)
        avg_line = np.where(priced, line, 0.0).sum(axis=1) / priced.sum(axis=1)

    return pd.DataFrame(
        {
            "s3_round_pre_finished": counted.sum(axis=1),
            "s3_round_pre_comebacks": (counted & comeback).sum(axis=1),
            "s3_round_pre_seven_plus": (counted & seven_plus).sum(axis=1),
            "s3_round_pre_rare_events": (counted & (comeback | seven_plus)).sum(axis=1),
            "s3_round_pre_btts": (counted & btts).sum(axis=1),
            "s3_round_pre_avg_goals": avg_goals,
            "s3_round_pre_avg_ou_line": avg_line,
        },
        index=round_df.index,
    )


def _matches_by_kickoff(league_stage_df: pd.DataFrame) -> list[_Match]:
    """The stage's matches as `_Match` records, in kickoff order."""

    by_kickoff_df = league_stage_df.assign(
        _kickoff=league_stage_df["s1_date"].map(parse_instant)
    ).sort_values("_kickoff")

    return [
        _Match(
            index,
            row["_kickoff"],
            int(row["s1_home_team_id"]),
            int(row["s1_away_team_id"]),
            (int(row["s1_ft_home_goals"]), int(row["s1_ft_away_goals"])),
            (int(row["s1_ht_home_goals"]), int(row["s1_ht_away_goals"])),
        )
        for index, row in by_kickoff_df.iterrows()
    ]


def _lines(tables: dict[str, Standings], team: int, side: str) -> dict[str, int | None]:
    """One team's stats in the FT and HT tables, as `s3_<side>_pre_<half>_<venue>_<stat>`."""

    team_fields: dict[str, int | None] = {}
    for half, table in tables.items():
        for venue in STANDING_VENUES:
            line = table.line(venue, team)
            prefix = f"s3_{side}_pre_{half}_{venue}_"
            team_fields[prefix + "rank"] = table.ranks(venue).get(team)
            team_fields[prefix + "played"] = line.played
            team_fields[prefix + "won"] = line.won
            team_fields[prefix + "drawn"] = line.drawn
            team_fields[prefix + "lost"] = line.lost
            team_fields[prefix + "goals_for"] = line.goals_for
            team_fields[prefix + "goal_diff"] = line.goal_diff
            team_fields[prefix + "points"] = line.points

    return team_fields


def _htft(record: HalfTimeFullTime, team: int, side: str) -> dict[str, int | None]:
    """One team's HT/FT record, as `s3_<side>_pre_htft_<venue>_<ht>_<ft>` (team view)."""

    return {
        f"s3_{side}_pre_htft_{venue}_{ht_result}_{ft_result}": record.count(
            venue, team, ht_result.upper(), ft_result.upper()
        )
        for venue, ht_result, ft_result in product(STANDING_VENUES, HTFT_RESULTS, HTFT_RESULTS)
    }


def _stakes(
    table: Standings, at_open: Standings, left: Counter[int], team: int, side: str
) -> dict[str, int | None]:
    """What is at stake for one team at kickoff, as `s3_<side>_<field>`: its matches left,
    the points gaps around it, and how far its rank moved after the opening odds."""

    above, below = table.points_gaps("total", team)
    rank, rank_at_open = table.ranks("total").get(team), at_open.ranks("total").get(team)

    return {
        f"s3_{side}_pre_matches_left": left[team],
        f"s3_{side}_pre_pts_to_above": above,
        f"s3_{side}_pre_pts_to_below": below,
        f"s3_{side}_rank_change_since_open": (
            None if rank is None or rank_at_open is None else rank - rank_at_open
        ),
    }


def _finished_by(matches: list[_Match], start: int, instant: Any) -> int:
    """The end of the matches, from `start` on, that kicked off at least `FINISHED_AFTER`
    before `instant`. Sorted by kickoff, so the counted matches are always a prefix."""

    end = start
    while end < len(matches) and matches[end].kickoff <= instant - FINISHED_AFTER:
        end += 1

    return end


def _stage_tables(league_stage_df: pd.DataFrame) -> Iterator[tuple[Any, dict[str, int | None]]]:
    """Each match of one stage with both teams' lines, HT/FT records and stakes at its
    kickoff."""

    matches = _matches_by_kickoff(league_stage_df)
    teams = {m.home for m in matches} | {m.away for m in matches}
    tables = {"ft": Standings(teams), "ht": Standings(teams)}
    record = HalfTimeFullTime(teams)
    at_open = Standings(teams)

    # Each team's matches from this one on, this one included: the fixture list, no result.
    left = Counter([m.home for m in matches] + [m.away for m in matches])

    counted = opened = 0
    for match in matches:
        end = _finished_by(matches, counted, match.kickoff)
        for done in matches[counted:end]:
            tables["ft"].add(done.home, done.away, *done.ft)
            tables["ht"].add(done.home, done.away, *done.ht)
            record.add(done.home, done.away, done.ht, done.ft)
        counted = end

        end = _finished_by(matches, opened, match.kickoff - OPEN_LEAD)
        for done in matches[opened:end]:
            at_open.add(done.home, done.away, *done.ft)
        opened = end

        yield (
            match.index,
            {
                **_lines(tables, match.home, "home"),
                **_lines(tables, match.away, "away"),
                **_htft(record, match.home, "home"),
                **_htft(record, match.away, "away"),
                **_stakes(tables["ft"], at_open, left, match.home, "home"),
                **_stakes(tables["ft"], at_open, left, match.away, "away"),
            },
        )

        left[match.home] -= 1
        left[match.away] -= 1


def pre_kickoff_tables(schedule_df: pd.DataFrame) -> pd.DataFrame:
    """Both teams' standings (96 columns), `s3_pre_rank_gap`, HT/FT records (54) and stakes (8).

    One table and one record per stage, counting the matches that kicked off at least
    `FINISHED_AFTER` before this one; the rank change compares with the table `OPEN_LEAD` earlier.
    """

    rows: dict[Any, dict[str, int | None]] = {}
    for _, league_stage_df in schedule_df.groupby("s1_stage", sort=False):
        rows.update(_stage_tables(league_stage_df))

    pre_kickoff_df = pd.DataFrame.from_dict(rows, orient="index").reindex(
        index=schedule_df.index,
        columns=pre_kickoff_columns() + pre_htft_columns() + stake_columns(),
    )

    gap = (
        pre_kickoff_df["s3_home_pre_ft_total_rank"] - pre_kickoff_df["s3_away_pre_ft_total_rank"]
    ).abs()

    return pre_kickoff_df.assign(s3_pre_rank_gap=gap).astype("Int64")


def derive(schedule_df: pd.DataFrame) -> pd.DataFrame:
    """Every stage-3 column of one league-season's stage-2 rows, in declared order."""

    derived_df = pd.concat(
        [
            round_positions(schedule_df),
            round_offsets(schedule_df),
            round_so_far(schedule_df),
            pre_kickoff_tables(schedule_df),
        ],
        axis=1,
    )

    return derived_df[SCHEDULE_MULTI_COLUMNS]


def build(row_path: str) -> str:
    """Write the stage-3 file for one stage-2 schedule file; return its path."""

    stage_2_df = read_stage_csv(row_path)
    stage_3_df = pd.concat([stage_2_df, derive(stage_2_df)], axis=1)

    stage_3_path = paths.schedule_at_stage(row_path, 3)
    columns = SCHEDULE_RAW_COLUMNS + SCHEDULE_ROW_COLUMNS + SCHEDULE_MULTI_COLUMNS
    write_stage_csv(stage_3_df, stage_3_path, columns)

    logger.info("%s: %d rows -> %s", row_path, len(stage_2_df), stage_3_path)

    return stage_3_path


def build_all() -> None:
    """Build the stage-3 file of every stage-2 schedule file."""

    row_paths = paths.schedule_csvs(2)
    if not row_paths:
        logger.warning("No stage-2 schedule files in %s", paths.stage_dir(2))

    for row_path in row_paths:
        build(row_path)


def main() -> None:
    """Entry point: build every stage-3 schedule file."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )

    build_all()


if __name__ == "__main__":
    main()
