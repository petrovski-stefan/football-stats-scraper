"""The card per team: a team in one league, read against its league.

Doc: `notes/ANALYSIS/SCHEDULE/WHOLE_CORPUS/PER_TEAM/RATES.md`. Each match gives two team rows,
one for each team. For each quantity of the team card (`notes/ANALYSIS/CLAUDE.md` §2: the two
roles, each at home and away, and the goals scored and conceded), prints one test of the
teams around their own league, the spread of the shrunk team values against their league,
and the repeat test: does a team's value in one season cohort predict its value in the other,
both against its league? Then, for the two roles, the luck line and the teams most above
their league after shrinkage. No team is tested on its own.

Run: `uv run python -m analysis.schedule.whole_corpus.per_team.rates`
"""

import pandas as pd

from analysis import corpus, report, stats, units

UNIT = "unit"  # a team in one league
LEAGUE = "league"
# (numerator column, denominator column, label, kind): sum(numerator) / sum(denominator) over
# the rows of a team. The two roles: the team comes back (behind at half-time, then wins),
# and the team loses a lead (ahead at half-time, then loses).
QUANTITIES = (
    ("comes_back", "one", "comes back", "event"),
    ("comes_back_home", "home", "comes back at home", "event"),
    ("comes_back_away", "away", "comes back away", "event"),
    ("behind", "one", "behind at half-time", "event"),
    ("comes_back", "behind", "behind, then wins", "event"),
    ("loses_lead", "one", "loses a lead", "event"),
    ("loses_lead_home", "home", "loses a lead at home", "event"),
    ("loses_lead_away", "away", "loses a lead away", "event"),
    ("ahead", "one", "ahead at half-time", "event"),
    ("loses_lead", "ahead", "ahead, then loses", "event"),
    ("goals_for", "one", "goals scored", "count"),
    ("goals_against", "one", "goals conceded", "count"),
)
RANKED = ("comes back", "loses a lead")
TOP = 20


def team_frame(matches: pd.DataFrame) -> pd.DataFrame:
    """Two rows per match, one for each team: its venue, its roles and its goals, its unit
    (the team in its league), the league-season and the cohort."""
    sides = []
    for side, other in (("home", "away"), ("away", "home")):
        ht_for, ht_against = matches[f"s1_ht_{side}_goals"], matches[f"s1_ht_{other}_goals"]
        ft_for, ft_against = matches[f"s1_ft_{side}_goals"], matches[f"s1_ft_{other}_goals"]
        behind, ahead = ht_for < ht_against, ht_for > ht_against
        rows = pd.DataFrame(
            {
                "behind": behind,
                "ahead": ahead,
                "comes_back": behind & (ft_for > ft_against),
                "loses_lead": ahead & (ft_for < ft_against),
                "goals_for": ft_for,
                "goals_against": ft_against,
            },
            index=matches.index,
        ).astype(float)
        rows["home"] = 1.0 if side == "home" else 0.0
        rows["team"] = matches[f"s1_{side}_team_id"]
        rows["team_name"] = matches[f"s1_{side}_team_name"]
        rows[LEAGUE] = matches["s1_league_id"]
        rows["league_name"] = matches["s1_league_name"]
        rows["cluster"] = matches["s1_league_id"].astype(str) + " " + matches["s1_season"]
        rows["season_cohort"] = matches["season_cohort"]
        sides.append(rows)
    frame = pd.concat(sides, ignore_index=True)
    frame["away"] = 1.0 - frame["home"]
    frame["one"] = 1.0
    for role in ("comes_back", "loses_lead"):
        for venue in ("home", "away"):
            frame[f"{role}_{venue}"] = frame[role] * frame[venue]
    frame[UNIT] = frame["team"].astype(str) + " " + frame[LEAGUE].astype(str)
    return frame


def team_summary(
    frame: pd.DataFrame, quantity: tuple[str, str, str, str]
) -> tuple[dict[str, float | str], units.Within]:
    """One quantity: the test of the teams around their league as a row, and its result."""
    numerator, denominator, label, kind = quantity
    result = units.within_tested(frame, LEAGUE, UNIT, numerator, denominator, kind)
    r, n, p = units.repeat_test(frame, UNIT, numerator, denominator, LEAGUE)
    values = result.values
    pooled = float(values["observed"].sum() / values["expected"].sum())
    against = values["shrunk"] - values["owner_mean"]
    keep = result.tau2 / (result.tau2 + values["variance"])
    found = stats.detectable_tau(values["variance"], groups=values["owner"])
    row: dict[str, float | str] = {
        "quantity": label,
        "pooled": pooled,
        "Q": result.q,
        "df": float(result.df),
        "p": f"{result.p:.3g}",
        "tau": result.tau2**0.5,
        "tau/pooled": result.tau2**0.5 / pooled,
        "found 80%": found,
        "found/pooled": found / pooled,
        "keep median": float(keep.median()),
        "shrunk - league min": float(against.min()),
        "shrunk - league max": float(against.max()),
        "repeat r": r,
        "repeat n": float(n),
        "repeat p": f"{p:.3g}",
    }
    return row, result


def luck_row(label: str, result: units.Within) -> dict[str, float | str]:
    """How far the raw team values reach, and how far they would reach by luck alone if
    every team had the value of its league."""
    values = result.values
    low, high = units.luck_line(values["expected"], values["owner_mean"].to_numpy())
    return {
        "quantity": label,
        "events per team, median": float(values["observed"].median()),
        "raw min": float(values["value"].min()),
        "raw max": float(values["value"].max()),
        "luck min": low,
        "luck max": high,
    }


def top_teams(frame: pd.DataFrame, result: units.Within, top: int = TOP) -> pd.DataFrame:
    """The teams most above their league after shrinkage, then by the raw rate, with the
    comebacks in all their matches."""
    names = frame.groupby(UNIT)[["team_name", "league_name"]].first()
    in_matches = frame.groupby(UNIT)[["comes_back", "loses_lead"]].sum().sum(axis=1)
    table = names.join(result.values[["observed", "expected", "value", "owner_mean", "shrunk"]])
    table["shrunk - league"] = table["shrunk"] - table["owner_mean"]
    table["comebacks in its matches"] = in_matches
    table = table.rename(
        columns={
            "observed": "events",
            "expected": "of",
            "value": "rate",
            "owner_mean": "league",
        }
    )
    order = ["shrunk - league", "rate", "team_name"]
    return table.sort_values(order, ascending=[False, False, True]).head(top)


def main() -> None:
    matches = corpus.load()
    print(corpus.corpus_line(matches))
    frame = team_frame(matches)
    in_two = int((frame.groupby("team")[LEAGUE].nunique() > 1).sum())
    print(
        f"{frame[UNIT].nunique():,} team units (a team in one league) in "
        f"{frame[LEAGUE].nunique()} leagues; {len(frame):,} team-matches; "
        f"{in_two} teams in two leagues or more"
    )
    rows, results = [], {}
    for quantity in QUANTITIES:
        row, results[quantity[2]] = team_summary(frame, quantity)
        rows.append(row)
    report.show("One test of the teams around their league, for each quantity", pd.DataFrame(rows))
    report.show(
        "The luck line of the two roles",
        pd.DataFrame([luck_row(label, results[label]) for label in RANKED]),
    )
    for label in RANKED:
        report.show(f"Teams most above their league: {label}", top_teams(frame, results[label]))


if __name__ == "__main__":
    main()
