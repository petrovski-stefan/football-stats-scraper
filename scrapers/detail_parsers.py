"""Parsers for the match detail page (`/match/h2h-<id>` on `constants.MATCH_HOST`).

Each parser takes a BeautifulSoup of the rendered page (or a section Tag) and
returns a flat dict of features. List sections (recent form, H2H) are reduced to
per-match mini-records and then aggregated into wide features. Everything is
best-effort and nullable — a section may be missing on a given page.
"""

import re
from collections import Counter
from typing import Any

from bs4 import BeautifulSoup, Tag

from domain import stats
from domain.columns import MATCHES_PER_SECTION, PER_MATCH_FIELDS
from scrapers.constants import (
    DETAIL_FIXTURE_AWAY,
    DETAIL_FIXTURE_HOME,
    DETAIL_GUESS_BOX,
    DETAIL_H2H_COMPARE_BAR,
    DETAIL_ODDS_1X2_CELLS,
    DETAIL_ODDS_TABLE_CANDIDATES,
    DETAIL_STRENGTH_BLOCK,
    HIST_CORNER_TD,
    HIST_DATE,
    HIST_FT_SCORE,
    HIST_HT_SCORE,
    HIST_LEAGUE_ID_ATTR,
    HIST_LEAGUE_TD,
    HIST_MATCH_ID_ATTR,
    HIST_ODDS_TDS,
    HIST_TEAM_LINKS,
    PREFERRED_BOOKMAKER,
)
from scrapers.parsers import attr, parse_float, parse_score, tag_text

_TEAM_ID_RE = re.compile(r"soccerDbPage\.team\((\d+)\)")
_PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_DAYS_RE = re.compile(r"(\d+)\s*Day")


# --- history rows (recent form / H2H) ----------------------------------------
def parse_history_row(row: Tag) -> dict[str, Any] | None:
    """Parse one v1/v2/v3 table row into a mini match-record. None if not a played match."""

    ft_raw = tag_text(row.select_one(HIST_FT_SCORE))
    ht_raw = tag_text(row.select_one(HIST_HT_SCORE)).strip("()")
    ft = parse_score(ft_raw)
    ht = parse_score(ht_raw)
    if ft is None or ht is None:
        return None

    links = row.select(HIST_TEAM_LINKS)
    if len(links) < 2:
        return None
    home_id = _team_id(links[0])
    away_id = _team_id(links[1])
    if home_id is None or away_id is None:
        return None

    cells = row.find_all("td")
    league_td = cells[HIST_LEAGUE_TD] if len(cells) > HIST_LEAGUE_TD else None
    corner_ft, corner_ht = _parse_pair_cell(
        tag_text(cells[HIST_CORNER_TD]) if len(cells) > HIST_CORNER_TD else ""
    )
    odds = [parse_float(tag_text(cells[i])) if len(cells) > i else None for i in HIST_ODDS_TDS]
    date_tag = row.select_one(HIST_DATE)

    return {
        # The referenced match's own id, carried on the row. This is what lets a history
        # row be joined to anything else -- goal timings in particular.
        "match_id": attr(row, HIST_MATCH_ID_ATTR) or "",
        "league_id": _row_league_id(row),
        "home_id": home_id,
        "away_id": away_id,
        "home_name": tag_text(links[0]),
        "away_name": tag_text(links[1]),
        "ft_home": ft[0],
        "ft_away": ft[1],
        "ht_home": ht[0],
        "ht_away": ht[1],
        "ft_score": ft_raw,
        "ht_score": ht_raw,
        "date": attr(date_tag, "data-t") or "",
        "league": (attr(league_td, "title") or tag_text(league_td)) if league_td else "",
        "odds_home": odds[0],
        "odds_draw": odds[1],
        "odds_away": odds[2],
        "corner_ft": corner_ft,
        "corner_ht": corner_ht,
    }


def _row_league_id(row: Tag) -> int | None:
    """The competition id carried on a history row (36 = EPL, 90 = FA Cup)."""

    raw = attr(row, HIST_LEAGUE_ID_ATTR)

    return int(raw) if raw and raw.isdigit() else None


def _parse_pair_cell(
    text: str,
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """Parse a 'FT (HT)' cell like '5-2 (2-0)' into ((5,2),(2,0))."""

    ft_part = text.split("(")[0]
    ht_part = text[text.find("(") + 1 : text.find(")")] if "(" in text else ""

    return parse_score(ft_part), parse_score(ht_part)


def rows_to_records(rows: list[Tag]) -> list[dict[str, Any]]:
    records = [parse_history_row(r) for r in rows]

    return [r for r in records if r is not None]


def subject_team_id(records: list[dict[str, Any]]) -> int | None:
    """The team common to (most of) the rows — the one whose form the table shows."""

    if not records:
        return None

    counter: Counter[int] = Counter()
    for record in records:
        counter[record["home_id"]] += 1
        counter[record["away_id"]] += 1

    return counter.most_common(1)[0][0]


def aggregate_form(
    records: list[dict[str, Any]], subject_id: int | None, window: int | None = None
) -> dict[str, Any]:
    """Aggregate a subject team's mini-records (most-recent-first) into features."""

    recs = records[:window] if window else records
    played = len(recs)
    if played == 0 or subject_id is None:
        return _empty_form()

    tally: Counter[str] = Counter()
    form_chars: list[str] = []
    gf = ga = over25 = btts = pts = 0
    for record in recs:
        subject_home = record["home_id"] == subject_id
        sgf = record["ft_home"] if subject_home else record["ft_away"]
        sga = record["ft_away"] if subject_home else record["ft_home"]

        gf += sgf
        ga += sga
        pts += stats.points(sgf, sga)
        outcome = stats.team_result(sgf, sga)
        tally[outcome] += 1
        form_chars.append(outcome)

        if stats.is_over(record["ft_home"] + record["ft_away"]):
            over25 += 1
        if stats.is_btts(record["ft_home"], record["ft_away"]):
            btts += 1

    return {
        "played": played,
        "wins": tally["W"],
        "draws": tally["D"],
        "losses": tally["L"],
        "ppg": round(pts / played, 3),
        "gf_avg": round(gf / played, 3),
        "ga_avg": round(ga / played, 3),
        "over25_rate": round(over25 / played, 3),
        "btts_rate": round(btts / played, 3),
        "form": "".join(form_chars[:6]),
    }


def _empty_form() -> dict[str, Any]:
    return {
        "played": 0,
        "wins": None,
        "draws": None,
        "losses": None,
        "ppg": None,
        "gf_avg": None,
        "ga_avg": None,
        "over25_rate": None,
        "btts_rate": None,
        "form": None,
    }


def aggregate_recent(
    records: list[dict[str, Any]], subject_id: int | None, side: str
) -> dict[str, Any]:
    """Recent-form aggregate features for one side ('home'/'away')."""

    venue_is_home = side == "home"
    venue_recs = [r for r in records if (r["home_id"] == subject_id) == venue_is_home]

    agg = aggregate_form(records, subject_id, window=10)
    venue_agg = aggregate_form(venue_recs, subject_id, window=10)
    out = {f"{side}_recent_{k}": v for k, v in agg.items()}
    out[f"{side}_recent_venue_ppg"] = venue_agg["ppg"]
    out[f"{side}_recent_venue_over25_rate"] = venue_agg["over25_rate"]

    return out


def aggregate_h2h(records: list[dict[str, Any]], subject_id: int | None) -> dict[str, Any]:
    """Head-to-head aggregate features, oriented to the current home team."""

    subject = subject_id if subject_id is not None else subject_team_id(records)
    played = len(records)
    if played == 0 or subject is None:
        return {
            "h2h_played": 0,
            "h2h_home_team_wins": None,
            "h2h_draws": None,
            "h2h_away_team_wins": None,
            "h2h_over25_rate": None,
            "h2h_btts_rate": None,
            "h2h_avg_total_goals": None,
        }

    home_wins = draws = away_wins = over25 = btts = total = 0
    for record in records:
        subject_home = record["home_id"] == subject
        sgf = record["ft_home"] if subject_home else record["ft_away"]
        sga = record["ft_away"] if subject_home else record["ft_home"]

        if sgf > sga:
            home_wins += 1
        elif sgf == sga:
            draws += 1
        else:
            away_wins += 1

        total += record["ft_home"] + record["ft_away"]
        over25 += stats.is_over(record["ft_home"] + record["ft_away"])
        btts += stats.is_btts(record["ft_home"], record["ft_away"])

    return {
        "h2h_played": played,
        "h2h_home_team_wins": home_wins,
        "h2h_draws": draws,
        "h2h_away_team_wins": away_wins,
        "h2h_over25_rate": round(over25 / played, 3),
        "h2h_btts_rate": round(btts / played, 3),
        "h2h_avg_total_goals": round(total / played, 3),
    }


# --- per-match flattening (home_lastN_ / away_lastN_ / h2h_lastN_) ------------
def flatten_history(
    records: list[dict[str, Any]], subject_id: int | None, section: str
) -> dict[str, Any]:
    """Flatten each of the first MATCHES_PER_SECTION records into its own column block.

    `section` is one of 'home'/'away'/'h2h'; index 1 = most recent. Missing matches
    (fewer than the fixed count) produce an all-None block for a stable schema.
    """

    out: dict[str, Any] = {}
    for i in range(1, MATCHES_PER_SECTION + 1):
        record = records[i - 1] if i - 1 < len(records) else None
        out.update(_flatten_one(record, subject_id, f"{section}_last{i}_"))

    return out


def _side_of(pair: tuple[int, int] | None, index: int) -> int | None:
    """One side of a parsed `ft (ht)` corner cell, or None when the cell was absent."""

    return pair[index] if pair else None


def _flatten_one(
    record: dict[str, Any] | None, subject_id: int | None, prefix: str
) -> dict[str, Any]:
    if record is None or subject_id is None:
        return {f"{prefix}{field}": None for field in PER_MATCH_FIELDS}

    subject_home = record["home_id"] == subject_id
    sgf = record["ft_home"] if subject_home else record["ft_away"]
    sga = record["ft_away"] if subject_home else record["ft_home"]
    total = record["ft_home"] + record["ft_away"]
    corner_ft = record["corner_ft"]
    result = stats.team_result(sgf, sga)

    values = {
        "match_id": record["match_id"],
        "league_id": record["league_id"],
        "date": record["date"],
        "league": record["league"],
        "is_home": subject_home,
        "opponent": record["away_name"] if subject_home else record["home_name"],
        "result": result,
        "ht_score": record["ht_score"],
        "ft_score": record["ft_score"],
        "ht_home_goals": record["ht_home"],
        "ht_away_goals": record["ht_away"],
        "ft_home_goals": record["ft_home"],
        "ft_away_goals": record["ft_away"],
        "total_goals": total,
        "ht_result": stats.one_x_two(record["ht_home"], record["ht_away"]),
        "ft_result": stats.one_x_two(record["ft_home"], record["ft_away"]),
        "over_25": stats.is_over(total),
        "btts": stats.is_btts(record["ft_home"], record["ft_away"]),
        "is_comeback": stats.is_comeback(
            record["ht_home"], record["ht_away"], record["ft_home"], record["ft_away"]
        ),
        "odds_home": record["odds_home"],
        "odds_draw": record["odds_draw"],
        "odds_away": record["odds_away"],
        "corners_ft_home": _side_of(corner_ft, 0),
        "corners_ft_away": _side_of(corner_ft, 1),
        "corners_ht_home": _side_of(record["corner_ht"], 0),
        "corners_ht_away": _side_of(record["corner_ht"], 1),
        "corners_total": (corner_ft[0] + corner_ft[1]) if corner_ft else None,
    }

    return {f"{prefix}{field}": values[field] for field in PER_MATCH_FIELDS}


# --- odds comparison ----------------------------------------------------------
def parse_odds_1x2(soup: BeautifulSoup) -> dict[str, Any]:
    """1X2 initial + live odds from the preferred bookmaker (else first listed)."""

    table = _find_odds_table(soup)
    empty = {
        "odds_bookmaker": None,
        "odds1x2_init_home": None,
        "odds1x2_init_draw": None,
        "odds1x2_init_away": None,
        "odds1x2_live_home": None,
        "odds1x2_live_draw": None,
        "odds1x2_live_away": None,
    }

    if table is None:
        return empty

    initial_rows = _bookmaker_initial_rows(table)
    if not initial_rows:
        return empty
    init_row = next(
        (r for name, r in initial_rows if name.lower() == PREFERRED_BOOKMAKER.lower()),
        initial_rows[0][1],
    )
    bookmaker = next((name for name, r in initial_rows if r is init_row), None)

    init = _row_1x2(init_row)
    live_row = init_row.find_next_sibling("tr")
    live = _row_1x2(live_row) if isinstance(live_row, Tag) else (None, None, None)

    return {
        "odds_bookmaker": bookmaker,
        "odds1x2_init_home": init[0],
        "odds1x2_init_draw": init[1],
        "odds1x2_init_away": init[2],
        "odds1x2_live_home": live[0],
        "odds1x2_live_draw": live[1],
        "odds1x2_live_away": live[2],
    }


def _find_odds_table(soup: BeautifulSoup) -> Tag | None:
    for table in soup.select(DETAIL_ODDS_TABLE_CANDIDATES):
        text = table.get_text()
        if "1X2" in text and "Company" in text:
            return table

    return None


def _bookmaker_initial_rows(table: Tag) -> list[tuple[str, Tag]]:
    """(company_name, initial_row) for each bookmaker block in the odds table."""

    out: list[tuple[str, Tag]] = []
    for tr in table.select("tr"):
        if not tr.select(DETAIL_ODDS_1X2_CELLS):
            continue

        first = tr.find("td")
        name = tag_text(first if isinstance(first, Tag) else None)
        if name and name not in ("Live", "In-Play"):
            out.append((name, tr))

    return out


def _row_1x2(row: Tag) -> tuple[float | None, float | None, float | None]:
    cells = row.select(DETAIL_ODDS_1X2_CELLS)
    if len(cells) < 3:
        return None, None, None

    vals = [parse_float(attr(c, "data-o") or tag_text(c)) for c in cells[:3]]

    return vals[0], vals[1], vals[2]


# --- analysis blocks (best-effort) -------------------------------------------
def parse_strength(soup: BeautifulSoup) -> dict[str, Any]:
    """Strength split (home vs away) and H2H-comparison percentages."""

    out: dict[str, Any] = {
        "strength_home": None,
        "strength_away": None,
        "h2h_compare_home_pct": None,
        "h2h_compare_away_pct": None,
    }

    block = soup.select_one(DETAIL_STRENGTH_BLOCK)
    if block is not None:
        nums = re.findall(r"\b(\d{1,3})\b", block.get_text())
        # The headline split is the first "NN NN" pair after the team names.
        if len(nums) >= 2:
            out["strength_home"], out["strength_away"] = int(nums[0]), int(nums[1])

    bar = soup.select_one(DETAIL_H2H_COMPARE_BAR)
    if bar is not None:
        pcts = _PCT_RE.findall(bar.get_text())
        if len(pcts) >= 2:
            out["h2h_compare_home_pct"] = float(pcts[0])
            out["h2h_compare_away_pct"] = float(pcts[1])

    return out


def parse_guess(soup: BeautifulSoup) -> dict[str, Any]:
    """Crowd 'Who will win?' percentages (home / away)."""

    out: dict[str, Any] = {"guess_home_pct": None, "guess_away_pct": None}

    box = soup.select_one(DETAIL_GUESS_BOX)
    if box is not None:
        pcts = _PCT_RE.findall(box.get_text())
        if len(pcts) >= 2:
            out["guess_home_pct"] = float(pcts[0])
            out["guess_away_pct"] = float(pcts[-1])

    return out


def parse_fixtures(soup: BeautifulSoup) -> dict[str, Any]:
    """Days until each team's next fixture (congestion/rest), best-effort.

    The "Fixture" widget renders a home table (``table.team-table-home``) and an
    away table (``table.team-table-guest``); rows are ordered soonest-first, so the
    first "N Days" countdown in each table is that team's next match. The home/guest
    classes are reused by other widgets (recent form, standings), so we pick the first
    table of each class that actually carries a "N Days" countdown — that is the
    Fixture widget's. This is orientation-proof: the old positional ``div.team-div``
    approach picked a non-fixture block for home (always None) and mislabeled the home
    team's countdown as the away value.
    """

    out: dict[str, Any] = {"home_next_fixture_days": None, "away_next_fixture_days": None}

    for key, selector in (
        ("home_next_fixture_days", DETAIL_FIXTURE_HOME),
        ("away_next_fixture_days", DETAIL_FIXTURE_AWAY),
    ):
        for table in soup.select(selector):
            found = _DAYS_RE.search(table.get_text())
            if found:
                out[key] = int(found.group(1))
                break

    return out


def _team_id(tag: Tag) -> int | None:
    found = _TEAM_ID_RE.search(attr(tag, "onclick") or "")

    return int(found.group(1)) if found else None
