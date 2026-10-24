"""`scrapers/detail_parsers.py`: the record-level helpers that need no page.

They turn parsed history rows ("mini-records") into aggregates and per-match column blocks.
Team 1 is the subject team throughout; teams 2-4 are its opponents.
"""

from typing import Any

import pytest

from domain.columns import MATCHES_PER_SECTION, PER_MATCH_FIELDS
from scrapers import detail_parsers


def _record(
    home_id: int,
    away_id: int,
    ft: tuple[int, int],
    ht: tuple[int, int] = (0, 0),
    corner_ft: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """One parsed history row, with every key the helpers read."""
    return {
        "match_id": f"{home_id}-{away_id}",
        "league_id": 1,
        "date": "2026-01-03 15:00:00",
        "league": "Test League",
        "home_id": home_id,
        "away_id": away_id,
        "home_name": f"Team {home_id}",
        "away_name": f"Team {away_id}",
        "ht_score": f"{ht[0]}-{ht[1]}",
        "ft_score": f"{ft[0]}-{ft[1]}",
        "ht_home": ht[0],
        "ht_away": ht[1],
        "ft_home": ft[0],
        "ft_away": ft[1],
        "odds_home": 2.0,
        "odds_draw": 3.0,
        "odds_away": 4.0,
        "corner_ft": corner_ft,
        "corner_ht": None,
    }


# Most recent first: a home win 2-1, an away draw 1-1, a home loss 0-3.
RECORDS = [_record(1, 2, (2, 1)), _record(3, 1, (1, 1)), _record(1, 4, (0, 3))]


def test_subject_team_id_is_the_team_in_most_rows() -> None:
    assert detail_parsers.subject_team_id(RECORDS) == 1
    assert detail_parsers.subject_team_id([]) is None


def test_aggregate_form() -> None:
    form = detail_parsers.aggregate_form(RECORDS, subject_id=1)

    assert form == {
        "played": 3,
        "wins": 1,
        "draws": 1,
        "losses": 1,
        "ppg": round(4 / 3, 3),
        "gf_avg": 1.0,
        "ga_avg": round(5 / 3, 3),
        "over25_rate": round(2 / 3, 3),
        "btts_rate": round(2 / 3, 3),
        "form": "WDL",
    }


def test_aggregate_form_window_keeps_the_most_recent() -> None:
    form = detail_parsers.aggregate_form(RECORDS, subject_id=1, window=2)
    assert (form["played"], form["form"]) == (2, "WD")


@pytest.mark.parametrize(("records", "subject"), [([], 1), (RECORDS, None)])
def test_aggregate_form_without_data_is_all_none(
    records: list[dict[str, Any]], subject: int | None
) -> None:
    form = detail_parsers.aggregate_form(records, subject)
    assert form["played"] == 0
    assert all(value is None for key, value in form.items() if key != "played")


def test_aggregate_recent_adds_the_venue_split() -> None:
    recent = detail_parsers.aggregate_recent(RECORDS, subject_id=1, side="home")
    assert all(key.startswith("home_recent_") for key in recent)
    assert recent["home_recent_played"] == 3
    # Only the two matches team 1 played at home: a win and a loss, both 3 goals.
    assert recent["home_recent_venue_ppg"] == 1.5
    assert recent["home_recent_venue_over25_rate"] == 1.0


def test_aggregate_h2h() -> None:
    h2h = detail_parsers.aggregate_h2h(RECORDS, subject_id=1)

    assert h2h == {
        "h2h_played": 3,
        "h2h_home_team_wins": 1,
        "h2h_draws": 1,
        "h2h_away_team_wins": 1,
        "h2h_over25_rate": round(2 / 3, 3),
        "h2h_btts_rate": round(2 / 3, 3),
        "h2h_avg_total_goals": round(8 / 3, 3),
    }


def test_aggregate_h2h_without_data() -> None:
    h2h = detail_parsers.aggregate_h2h([], subject_id=1)
    assert h2h["h2h_played"] == 0
    assert all(value is None for key, value in h2h.items() if key != "h2h_played")


def test_flatten_history_has_a_fixed_schema() -> None:
    flat = detail_parsers.flatten_history(RECORDS[:2], subject_id=1, section="home")

    assert set(flat) == {
        f"home_last{slot}_{field}"
        for slot in range(1, MATCHES_PER_SECTION + 1)
        for field in PER_MATCH_FIELDS
    }

    # Blocks past the available matches are present but empty.
    assert all(value is None for key, value in flat.items() if key.startswith("home_last3_"))


def test_flatten_history_orients_each_block_to_the_subject() -> None:
    records = [_record(1, 2, (2, 1), corner_ft=(5, 3)), _record(3, 1, (1, 1))]
    flat = detail_parsers.flatten_history(records, subject_id=1, section="away")

    assert flat["away_last1_is_home"] is True
    assert flat["away_last1_opponent"] == "Team 2"
    assert flat["away_last1_result"] == "W"
    assert flat["away_last1_corners_total"] == 8

    assert flat["away_last2_is_home"] is False
    assert flat["away_last2_opponent"] == "Team 3"
    assert flat["away_last2_result"] == "D"
    assert flat["away_last2_corners_total"] is None


def test_flatten_history_without_subject_is_empty() -> None:
    flat = detail_parsers.flatten_history(RECORDS, subject_id=None, section="h2h")
    assert all(value is None for value in flat.values())
