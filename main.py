import logging
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Callable

from df import save_df_to_csv
from exceptions import SoupNoSuchElementException
from ids import get_matches_ids_from_league_and_league_name
from utils import get_leagues_links

logger = logging.getLogger(__name__)


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
                lambda match_id: print(match_id),
                league_matches_metadata[:1],
            )

        print(f"Scraped total of {len(league_matches_data)} matches from {link} .")

        # save_df_to_csv(league_matches_data, league_name)


if __name__ == "__main__":
    main()
