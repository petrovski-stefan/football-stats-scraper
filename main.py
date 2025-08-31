import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Callable

from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait

from df import save_df_to_csv
from driver import config_driver
from exceptions import SoupNoSuchElementException
from ids import get_matches_ids_from_league_and_league_name
from scrapers import (
    get_current_match_goals,
    get_head_to_head_information,
    get_initial_odds,
    get_team_games_information,
    get_teams_names,
    get_updated_odds,
)
from utils import get_leagues_links

logger = logging.getLogger(__name__)


def process_match(match_id: str) -> dict:
    driver = config_driver()

    driver.get(f"https://www.futebolscore.com/jogos/computador-{match_id}")

    try:
        WebDriverWait(driver, 35).until(
            EC.presence_of_element_located((By.ID, "sp_2_8_1_1"))
        )
        WebDriverWait(driver, 35).until(
            EC.presence_of_element_located((By.ID, "sp_2_8_3_1"))
        )
    except Exception:
        print(f"Couldn't locate the odds for match {match_id} .")
        driver.quit()

    html = driver.page_source
    driver.quit()

    match_data = dict()

    bs = BeautifulSoup(html, "html.parser")

    match_data.update(get_teams_names(bs, match_id))
    match_data.update(get_initial_odds(bs, match_id))
    match_data.update(get_updated_odds(bs, match_id))
    match_data.update(get_current_match_goals(bs, match_id))
    match_data.update(get_head_to_head_information(bs, match_id))
    match_data.update(get_team_games_information(bs, match_id, "home"))
    match_data.update(get_team_games_information(bs, match_id, "away"))

    return match_data


def run(
    process_match: Callable[[str], dict],
    match_metadata: dict,
    lock: Lock,
    league_matches_data: list[dict],
) -> None:
    """
    A wrapper for the process_match function to ensure writing in a synchronized environment.
    """

    try:
        match_data = process_match(match_metadata.get("id"))

        with lock:
            match_data.update(match_metadata)
            league_matches_data.append(match_data)

    except SoupNoSuchElementException:
        print(f"Error element not found in match with id {match_metadata.get('id')} .")
    except Exception:
        print(
            f"Error occured after processing match with id {match_metadata.get('id')} ."
        )


def main() -> None:
    leagues_links = get_leagues_links()

    for link in leagues_links:
        league_matches_metadata, league_name = (
            get_matches_ids_from_league_and_league_name(link)
        )
        print(f"Found total of {len(league_matches_metadata)} matches of {link} .")
        logger.info(
            f"Found total of {len(league_matches_metadata)} matches of {link} ."
        )

        league_matches_data = []
        lock = Lock()
        # TODO: remove [:3] after testing
        with ThreadPoolExecutor(max_workers=5) as executor:
            executor.map(
                lambda match_id: run(
                    process_match, match_id, lock, league_matches_data
                ),
                league_matches_metadata[:1],
            )

        print(f"Scraped total of {len(league_matches_data)} matches from {link} .")

        save_df_to_csv(league_matches_data, league_name)


if __name__ == "__main__":
    main()
