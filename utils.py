from bs4 import Tag
from selenium.webdriver import Chrome
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from constants import PORTUGUESE_TO_ENGLISH_LETTERS


def get_leagues_links() -> list[str]:

    with open("config/LEAGUES.txt") as f:
        return [line.strip().replace("\n", "") for line in f.readlines()]


def clean_string(string: str) -> str:

    return "".join([(PORTUGUESE_TO_ENGLISH_LETTERS.get(char, char)) for char in string])


def find_element_by_css(
    driver: Chrome, selector: str, many: bool = False
) -> WebElement | list[WebElement] | None:

    if many:
        return driver.find_elements(By.CSS_SELECTOR, selector)

    return driver.find_element(By.CSS_SELECTOR, selector)


def get_match_metadata(match: Tag, i: int, matches_len: int) -> dict:

    match_id = match.get("id", None)

    round_number_td: Tag = match.select_one("td:nth-child(1)")

    round_number_td_text = round_number_td.text.strip()

    round_number = int(round_number_td_text) if round_number_td_text else -1

    home_team_odds_td: Tag = match.select_one("td:nth-child(6)")
    draw_team_odds_td: Tag = match.select_one("td:nth-child(7)")
    away_team_odds_td: Tag = match.select_one("td:nth-child(8)")

    home_team_odds = home_team_odds_td.text.strip()
    draw_team_odds = draw_team_odds_td.text.strip()
    away_team_odds = away_team_odds_td.text.strip()

    has_odds = all([bool(home_team_odds), bool(draw_team_odds), bool(away_team_odds)])

    is_first_match_in_round = i == 0
    is_before_last_match_in_round = i == matches_len - 2
    is_last_match_in_round = i == matches_len - 1

    match_metadata = {
        "id": match_id,
        "round": round_number,
        "has_odds": has_odds,
        "is_first_match_in_round": is_first_match_in_round,
        "is_before_last_match_in_round": is_before_last_match_in_round,
        "is_last_match_in_round": is_last_match_in_round,
    }

    return match_metadata
