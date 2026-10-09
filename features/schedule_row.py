"""Stage 2 of the schedule: the fields computed from one stage-1 row and nothing else.

Reads `data/finished/1_raw/<country>_<league>_<season>_schedule.csv` and writes the same rows plus
the `s2_` columns to `data/finished/2_row/` (`notes/fields/schedule_2_row.md`). `derive`
sees one row at a time, so no field here can carry another match's result into a row.

Run: `uv run python -m features.schedule_row`
"""

import logging
import math
from collections.abc import Mapping
from typing import Any

import pandas as pd

from domain import paths, scope, stats
from domain.clock import parse_berlin
from domain.columns import SCHEDULE_RAW_COLUMNS, SCHEDULE_ROW_COLUMNS
from features.stage_io import read_stage_csv, write_stage_csv

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

MONDAY = 1
MIDWEEK = (2, 3, 4)  # Tuesday to Thursday, ISO weekday numbers


def _number(row: Mapping[str, Any], column: str) -> float | None:
    """A price or line from the row, None when the page showed none."""
    value = row.get(column)
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return float(value)


def _goal_fields(ht: tuple[int, int], ft: tuple[int, int]) -> dict[str, Any]:
    return {
        "s2_total_goals": ft[0] + ft[1],
        "s2_goals_1h": ht[0] + ht[1],
        "s2_goals_2h": ft[0] + ft[1] - ht[0] - ht[1],
        "s2_home_2h_goals": ft[0] - ht[0],
        "s2_away_2h_goals": ft[1] - ht[1],
        "s2_ht_result": stats.one_x_two(*ht),
        "s2_ft_result": stats.one_x_two(*ft),
    }


def _date_fields(kickoff: str) -> dict[str, Any]:
    weekday = parse_berlin(kickoff).isoweekday()
    return {
        "s2_day_of_week": weekday,
        "s2_is_monday": weekday == MONDAY,
        "s2_is_midweek": weekday in MIDWEEK,
    }


def _odds_fields(row: Mapping[str, Any]) -> dict[str, Any]:
    one_x_two = [_number(row, f"s1_odds_1x2_open_{s}") for s in ("home", "draw", "away")]
    over_under = [_number(row, f"s1_odds_ou_open_{s}") for s in ("line", "over", "under")]
    handicap = [_number(row, f"s1_odds_ah_open_{s}") for s in ("line", "home", "away")]
    market = stats.vig_free_1x2(*one_x_two)
    p_home, p_draw, p_away = market if market else (None, None, None)
    return {
        "s2_has_odds": None not in one_x_two,
        "s2_has_ou_odds": None not in over_under,
        "s2_has_ah_odds": None not in handicap,
        "s2_mkt_p_home": p_home,
        "s2_mkt_p_draw": p_draw,
        "s2_mkt_p_away": p_away,
        "s2_mkt_sup": math.log(p_home / p_away) if p_home and p_away else None,
        "s2_mkt_tot": -math.log(p_draw) if p_draw else None,
        "s2_implied_over": stats.two_way_prob(over_under[1], over_under[2]),
        "s2_implied_ah_home": stats.two_way_prob(handicap[1], handicap[2]),
    }


def _comeback_fields(ht: tuple[int, int], ft: tuple[int, int]) -> dict[str, Any]:
    return {
        "s2_is_comeback": stats.is_comeback(*ht, *ft),
        "s2_is_comeback_home": stats.is_comeback_home(*ht, *ft),
        "s2_is_comeback_away": stats.is_comeback_away(*ht, *ft),
        "s2_ht_decisive": ht[0] != ht[1],
    }


def derive(row: Mapping[str, Any]) -> dict[str, Any]:
    """The `s2_` fields of one stage-1 row."""
    ht = (int(row["s1_ht_home_goals"]), int(row["s1_ht_away_goals"]))
    ft = (int(row["s1_ft_home_goals"]), int(row["s1_ft_away_goals"]))
    return {
        **_goal_fields(ht, ft),
        **_date_fields(str(row["s1_date"])),
        **_odds_fields(row),
        "s2_is_abandoned": scope.is_abandoned(row["match_id"]),
        "s2_is_forfeit": scope.is_forfeit(row["match_id"]),
        **_comeback_fields(ht, ft),
    }


def build(raw_path: str) -> str:
    """Write the stage-2 file for one stage-1 schedule file; return its path."""
    raw = read_stage_csv(raw_path)
    records = [{str(k): v for k, v in row.items()} for row in raw.to_dict("records")]
    derived = pd.DataFrame([derive(row) for row in records], index=raw.index)
    out_path = paths.schedule_at_stage(raw_path, 2)
    write_stage_csv(
        pd.concat([raw, derived], axis=1), out_path, SCHEDULE_RAW_COLUMNS + SCHEDULE_ROW_COLUMNS
    )
    logger.info("%s: %d rows -> %s", raw_path, len(raw), out_path)
    return out_path


def build_all() -> None:
    raw_paths = paths.schedule_csvs(1)
    if not raw_paths:
        logger.warning("No stage-1 schedule files in %s", paths.stage_dir(1))
    for raw_path in raw_paths:
        build(raw_path)


def main() -> None:
    build_all()


if __name__ == "__main__":
    main()
