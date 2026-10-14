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
from typing import Any, NamedTuple

import numpy as np
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
    stake_columns,
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

# A match this many days or more from its round's median kickoff was rescheduled. Measured on
# 2026-10-10 over 82 leagues: 1,155 matches (2.8%) at 5 days, 1,114 at 7, so 5 is where the
# count stops falling; under 5 a long round (Friday to Monday, a split midweek) still counts.
RESCHEDULED_AFTER_DAYS = 5

# The round so far counts only round-mates that kicked off less than this before: the same 5
# days that mark a rescheduled match, so a match played weeks earlier (brought forward, or the
# rest of the round for a postponed one) is not "this round so far". It never reads a later
# kickoff (Claude's choice, 2026-10-13, asked by the user).
ROUND_LOOK_BACK = timedelta(days=RESCHEDULED_AFTER_DAYS)

# The over 6.5 market: a match with at least this many goals.
SEVEN_PLUS_GOALS = 7

# The opening odds (Bet365's "Initial") are published about this long before kickoff (the
# user, 2026-10-10: "usually about 7 days", more or fewer by league). A result between then
# and kickoff is news the opening odds cannot hold; `s3_<side>_rank_change_since_open`
# measures how far such results moved the table.
OPEN_LEAD = timedelta(days=7)

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


def round_offsets(frame: pd.DataFrame) -> pd.DataFrame:
    """`s3_days_off_round` and `s3_is_rescheduled`, from kickoff times only.

    The offset is this kickoff minus the median kickoff of its (stage, round), in days:
    positive for a match played after its round, negative for one brought forward. A match
    `RESCHEDULED_AFTER_DAYS` or more off its round was rescheduled. A read-only indicator for
    now (the user, 2026-10-10). Not `s3_out_of_round` (S3.07), whose survey wording misfires
    on a brought-forward match.
    """
    kickoff = pd.to_datetime(frame["s1_date"].map(parse_instant), utc=True)
    median = kickoff.groupby([frame[key] for key in _ROUND_KEY], dropna=False).transform("median")
    days = (kickoff - median).dt.total_seconds() / 86400
    return pd.DataFrame(
        {"s3_days_off_round": days, "s3_is_rescheduled": days.abs() >= RESCHEDULED_AFTER_DAYS},
        index=frame.index,
    )


def round_so_far(frame: pd.DataFrame) -> pd.DataFrame:
    """The round so far: `s3_round_pre_finished`, `_comebacks`, `_seven_plus`,
    `_rare_events`, `_btts`, `_avg_goals` and `_avg_ou_line`.

    A round-mate counts when it is of the same (stage, round) and kicked off at least
    `FINISHED_AFTER` and less than `ROUND_LOOK_BACK` before this one. The counts say how many
    of those were a comeback, had 7+ goals, either (a match that was both counts once), or
    ended with both teams scoring. The two averages, goals per match and the opening O/U
    line, cover the counted round-mates that have a line, so their difference is how far the
    round scored above or below its opening lines (not centred at 0: the line is the market's
    50/50 point, and a match scores about 0.13 goals above it on average); both are empty when
    there is none. The first kickoff of a round sees 0 in every count.
    """
    keyed = frame.assign(_kickoff=pd.to_datetime(frame["s1_date"].map(parse_instant), utc=True))
    parts = [_round_counts(group) for _, group in keyed.groupby(_ROUND_KEY, sort=False)]
    return pd.concat(parts).reindex(frame.index)


def _round_counts(group: pd.DataFrame) -> pd.DataFrame:
    """`round_so_far` for one (stage, round)."""
    kickoff = group["_kickoff"].to_numpy(dtype="datetime64[ns]")
    # Row: this match; column: a round-mate. True where the round-mate counts.
    gap = kickoff[:, None] - kickoff[None, :]
    counted = (gap >= pd.Timedelta(FINISHED_AFTER).to_timedelta64()) & (
        gap < pd.Timedelta(ROUND_LOOK_BACK).to_timedelta64()
    )
    goals = group["s2_total_goals"].to_numpy(dtype=float)
    comeback = group["s2_is_comeback"].to_numpy(dtype=bool)
    seven_plus = goals >= SEVEN_PLUS_GOALS
    btts = (group["s1_ft_home_goals"].to_numpy() >= 1) & (group["s1_ft_away_goals"].to_numpy() >= 1)
    line = group["s1_odds_ou_open_line"].to_numpy(dtype=float)
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
        index=group.index,
    )


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


def _stage_tables(group: pd.DataFrame) -> Iterator[tuple[Any, dict[str, int | None]]]:
    """Each match of one stage with both teams' lines, HT/FT records and stakes at its
    kickoff."""
    matches = _matches_by_kickoff(group)
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


def pre_kickoff_tables(frame: pd.DataFrame) -> pd.DataFrame:
    """Both teams' standings (96 columns), `s3_pre_rank_gap`, HT/FT records (54) and what is
    at stake (8).

    One table and one record per stage, each counting only the matches that kicked off at
    least `FINISHED_AFTER` before this one; the rank change compares the table with the one
    `OPEN_LEAD` earlier.
    """
    rows: dict[Any, dict[str, int | None]] = {}
    for _, group in frame.groupby("s1_stage", sort=False):
        rows.update(_stage_tables(group))
    tables = pd.DataFrame.from_dict(rows, orient="index").reindex(
        index=frame.index, columns=pre_kickoff_columns() + pre_htft_columns() + stake_columns()
    )
    gap = (tables["s3_home_pre_ft_total_rank"] - tables["s3_away_pre_ft_total_rank"]).abs()
    return tables.assign(s3_pre_rank_gap=gap).astype("Int64")


def derive(frame: pd.DataFrame) -> pd.DataFrame:
    """Every stage-3 column of one league-season's stage-2 rows, in declared order."""
    out = pd.concat(
        [
            round_positions(frame),
            round_offsets(frame),
            round_so_far(frame),
            pre_kickoff_tables(frame),
        ],
        axis=1,
    )
    return out[SCHEDULE_MULTI_COLUMNS]


def build(row_path: str) -> str:
    """Write the stage-3 file for one stage-2 schedule file; return its path."""
    frame = read_stage_csv(row_path)
    out = pd.concat([frame, derive(frame)], axis=1)
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
