"""The page's final table against the table rebuilt from our own results.

The standings the analysis uses are rebuilt from stored results at each kickoff
(`features/schedule_multi.py`; the user's decision, 2026-10-06), so nothing else holds them
against the site. This is that check: per stage, every team's P, W, D, L, GD and PTS on the
page's final table must equal the table rebuilt from every stored result of the stage.

A difference is a finding about the data, never a reason to loosen the check: a points
deduction (our rebuild cannot know it), a match the scrape missed, or a wrong score. A
deduction confirmed in public reports is declared in `domain/deductions.py` and added to the
rebuilt points before comparing; an undeclared one still fails. Where the page's table applies
less than the official total, the amount it does apply (`deductions.PAGE_TOTALS`) is used. In a
league whose points carry from one stage into the next (Scotland's split, Belgium's halved
points), the later stage differs until that league's carry-over rule exists
(`notes/FIELDS/SCHEDULE_3_MULTI.md` §B), which is the point.

Rank: the page breaks a tie on points by its league's own rule (head-to-head in Spain,
Portugal, Italy and Poland, most wins in Belgium), ours by goal difference and goals for in
every league. So the page's rank only has to fall inside the block of positions the teams
level on points share; P, W, D, L, GD and PTS are still held exactly (the user's decision,
2026-10-07).
"""

from typing import Any

import pandas as pd

from domain import deductions
from domain.standings import Standings
from qa.report import Report

# What the check reads, and the text columns among them (an empty stage stays "").
SCHEDULE_COLUMNS = [
    "s1_stage",
    "s1_home_team_id",
    "s1_away_team_id",
    "s1_ft_home_goals",
    "s1_ft_away_goals",
]
_COUNTS = ("played", "won", "drawn", "lost", "goal_diff", "points")


def _rebuild(matches: pd.DataFrame) -> Standings:
    columns = [matches[c].astype(int).tolist() for c in SCHEDULE_COLUMNS[1:]]
    table = Standings(set(columns[0]) | set(columns[1]))
    for home, away, home_goals, away_goals in zip(*columns, strict=True):
        table.add(home, away, home_goals, away_goals)
    return table


def _check_team(r: Report, label: str, table: Standings, points: dict[int, int], page: Any) -> None:
    """`points`: every team's rebuilt points, declared deductions included."""
    team = int(page.team_id)
    ours = table.line("total", team)
    rebuilt = {name: getattr(ours, name) for name in _COUNTS} | {"points": points[team]}
    differ = {
        name: (int(getattr(page, f"s1_{name}")), rebuilt[name])
        for name in _COUNTS
        if int(getattr(page, f"s1_{name}")) != rebuilt[name]
    }
    r.check(not differ, f"{label}{page.s1_team_name}: (page, rebuilt) {differ}")
    # Teams level on points share a block of positions; the page may order them either way.
    first = 1 + sum(other > points[team] for other in points.values())
    last = first + list(points.values()).count(points[team]) - 1
    r.check(
        first <= int(page.s1_rank) <= last,
        f"{label}{page.s1_team_name}: page rank {page.s1_rank}, rebuilt {first}..{last}",
    )


def check(r: Report, schedule: pd.DataFrame, final_table: pd.DataFrame) -> None:
    """Compare every stage's final table with the table rebuilt from the stage's results."""
    if final_table.empty:
        r.check(False, "no final table: the rebuilt standings are unchecked")
        return
    first_row = final_table.iloc[0]
    league, season = int(first_row["league_id"]), str(first_row["season"])
    for stage, page in final_table.groupby("stage", sort=False):
        label = f"stage {stage!r}: " if stage else ""
        matches = schedule[schedule["s1_stage"] == stage]
        if matches.empty:
            r.check(False, f"{label}a final table but no stored matches")
            continue
        table = _rebuild(matches)
        ranks = table.ranks("total")
        on_page = {int(team) for team in page["team_id"]}
        extra, missing = sorted(on_page - set(ranks)), sorted(set(ranks) - on_page)
        r.check(not extra, f"{label}teams on the page with no stored match: {extra}")
        r.check(not missing, f"{label}teams with matches, missing from the page: {missing}")
        deducted = deductions.on_page(league, season, str(stage))
        points = {team: table.line("total", team).points + deducted.get(team, 0) for team in ranks}
        for row in page[page["team_id"].astype(int).isin(ranks)].itertuples(index=False):
            _check_team(r, label, table, points, row)
