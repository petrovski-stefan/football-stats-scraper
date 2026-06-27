import time

from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver import Chrome
from selenium.webdriver.remote.webelement import WebElement

from constants import STAGE_KEYWORDS
from driver import find_element_by_css, get_driver
from parsers import get_match_metadata


def get_matches_ids_from_league_and_league_name(
    league_link: str,
) -> tuple[list[str], str]:
    # TODO: handle exception
    driver = get_driver()

    driver.get(league_link)
    time.sleep(2)

    league_name: WebElement | None = find_element_by_css(driver, "#titbox")

    if league_name is None:
        raise NoSuchElementException(f"Cannot find the name for league {league_link} .")

    league_name = league_name.text.strip().lower().replace(" ", "_")

    stages: list[WebElement] = find_element_by_css(
        driver, "#SubSelectDiv li.nav_unselected", many=True
    )

    stages_name_id = [
        (
            stage.text,
            stage.get_dom_attribute("onclick")
            .replace("changeSub(", "")
            .replace(")", "")
            .strip(),
        )
        for stage in stages
        if stage.text.strip() in STAGE_KEYWORDS
    ]

    stages_links = [
        f"{league_link}/{stage_id}" for _, stage_id in stages_name_id if stage_id
    ]

    stages_links.insert(0, league_link)
    league_matches = []
    [
        league_matches.extend(process_stage(driver, stage_link))
        for stage_link in stages_links
    ]

    driver.quit()

    print(f"Total league: {len(league_matches)}")

    return league_matches, league_name


def process_stage(driver: Chrome, stage_link: str) -> list[str]:
    driver.get(stage_link)

    time.sleep(2)

    stage: WebElement = find_element_by_css(
        driver, "#Table2 > tbody > tr:nth-child(1) > td:nth-child(1) > div > strong"
    )

    stage_name = stage.text.strip()

    rounds: list[WebElement] = find_element_by_css(driver, "table td.lsm2", many=True)

    stage_matches = []
    [stage_matches.extend(get_matches_metadata_from_round(driver, r)) for r in rounds]
    print(f"Stage: {len(stage_matches)}")

    for match_metadata in stage_matches:
        match_metadata["stage"] = stage_name

    return stage_matches


def get_matches_metadata_from_round(driver: Chrome, round: WebElement) -> list[dict]:
    round.click()

    time.sleep(2)

    round_html = driver.page_source

    bs = BeautifulSoup(round_html, "html.parser")

    rows = bs.select("div.tdsolid table tr")

    matches_rows = [
        row
        for row in rows
        if row.get("id") is not None and len(row.get("id").strip()) == 7
    ]

    matches_metadata = [
        get_match_metadata(match, i, len(matches_rows))
        for i, match in enumerate(matches_rows)
    ]

    return matches_metadata
