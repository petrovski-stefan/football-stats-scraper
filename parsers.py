from bs4 import Tag

from constants import PORTUGUESE_TO_ENGLISH_LETTERS

from .match import Match


def clean_string(string: str) -> str:
    return "".join([(PORTUGUESE_TO_ENGLISH_LETTERS.get(char, char)) for char in string])


def get_match_metadata(
    *,
    match: Tag,
    i: int,
    matches_len: int,
    odds_company: str,
    league_name: str,
    stage: str,
    year: int | str,
    period: str,
) -> dict:
    match_id = match.get("id", None)

    round_number_td: Tag = match.select_one("td:nth-child(1)")

    round_number_td_text = round_number_td.text.strip()

    round_number = int(round_number_td_text) if round_number_td_text else -1

    home_team_odds_td: Tag = match.select_one("td:nth-child(6)")
    draw_team_odds_td: Tag = match.select_one("td:nth-child(7)")
    away_team_odds_td: Tag = match.select_one("td:nth-child(8)")

    home_team_odds = home_team_odds_td.text
    draw_odds = draw_team_odds_td.text
    away_team_odds = away_team_odds_td.text

    is_first_match_in_round = i == 0
    is_before_last_match_in_round = i == matches_len - 2
    is_last_match_in_round = i == matches_len - 1

    first_team_name_td = match.select_one("td:nth-child(3) > a")
    second_team_name_td = match.select_one("td:nth-child(5) > a")

    first_team_name = first_team_name_td.text
    second_team_name = second_team_name_td.text

    first_team_position_td = match.select_one("td:nth-child(3) > sup")
    second_team_position_td = match.select_one("td:nth-child(5) > sup")

    first_team_position = first_team_position_td.text.lstrip("[").rstrip("]")
    second_team_position = second_team_position_td.text.lstrip("[").rstrip("]")

    date_and_time_td = match.select_one("td:nth-child(3) > a")
    date_and_time = date_and_time_td.text

    match_data = {
        "league_name": league_name,
        "year": year,
        "period": period,
        "stage": stage,
        "round": round_number,
        "id": match_id,
        "date": date_and_time,
        "first_team_name": first_team_name,
        "second_team_name": second_team_name,
        "is_first_match_in_round": is_first_match_in_round,
        "is_before_last_match_in_round": is_before_last_match_in_round,
        "is_last_match_in_round": is_last_match_in_round,
        "odds_company": odds_company,
        "home_team_win_initial_odds": home_team_odds,
        "draw_initial_odds": draw_odds,
        "away_team_win_initial_odds": away_team_odds,
        "first_team_position": first_team_position,
        "second_team_position": second_team_position,
    }

    return match_data
