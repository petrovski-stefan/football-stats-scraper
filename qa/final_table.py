"""The page's final table against the table rebuilt from our own results.

The standings the analysis uses are rebuilt from stored results at each kickoff
(`features/schedule_multi.py`; the user's decision, 2026-10-06), so nothing else holds them
against the site. This is that check: per stage, every team's P, W, D, L, GD and PTS on the
page's final table must equal the table rebuilt from every stored result of the stage.

A difference is a finding about the data, never a reason to loosen the check: a points
deduction (our rebuild cannot know it), a match the scrape missed, or a wrong score. In a
league whose points carry from one stage into the next (Scotland's split, Belgium's halved
points), the later stage differs until that league's carry-over rule exists
(`notes/fields/schedule_3_multi.md` §B), which is the point.

Rank: our table gives teams level on points, goal difference and goals for one shared rank,
while the page orders them by its own tie-breaks (head-to-head in some leagues). So the
page's rank only has to fall inside the block of positions the tied teams share.
"""

from typing import Any

import pandas as pd

from domain.standings import Line, Standings
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


def read(path: str, columns: list[str] | None = None) -> pd.DataFrame:
    """A stage-1 file with its stage column kept as text."""
    return pd.read_csv(
        path,
        usecols=columns,
        dtype={"s1_stage": str, "stage": str, "season": str},
        keep_default_na=False,
    )


def _rebuild(matches: pd.DataFrame) -> Standings:
    columns = [matches[c].astype(int).tolist() for c in SCHEDULE_COLUMNS[1:]]
    table = Standings(set(columns[0]) | set(columns[1]))
    for home, away, home_goals, away_goals in zip(*columns, strict=True):
        table.add(home, away, home_goals, away_goals)
    return table


def _key(line: Line) -> tuple[int, int, int]:
    return line.points, line.goal_diff, line.goals_for


def _check_team(r: Report, label: str, table: Standings, ranks: dict[int, int], page: Any) -> None:
    team = int(page.team_id)
    ours = table.line("total", team)
    differ = {
        name: (int(getattr(page, f"s1_{name}")), getattr(ours, name))
        for name in _COUNTS
        if int(getattr(page, f"s1_{name}")) != getattr(ours, name)
    }
    r.check(not differ, f"{label}{page.s1_team_name}: (page, rebuilt) {differ}")
    # Teams level on every key share a rank here; the page may order them either way.
    tied = sum(_key(table.line("total", other)) == _key(ours) for other in ranks)
    first, last = ranks[team], ranks[team] + tied - 1
    r.check(
        first <= int(page.s1_rank) <= last,
        f"{label}{page.s1_team_name}: page rank {page.s1_rank}, rebuilt {first}..{last}",
    )


def check(r: Report, schedule: pd.DataFrame, final_table: pd.DataFrame) -> None:
    """Compare every stage's final table with the table rebuilt from the stage's results."""
    if final_table.empty:
        r.check(False, "no final table: the rebuilt standings are unchecked")
        return
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
        for row in page[page["team_id"].astype(int).isin(ranks)].itertuples(index=False):
            _check_team(r, label, table, ranks, row)
