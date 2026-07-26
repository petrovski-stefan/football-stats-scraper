import contextlib
import random
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scrapers.constants import (
    AGENTS,
    DETAIL_HOME_RECENT_ROWS,
    DETAIL_ODDS_TABLE_CANDIDATES,
    DETAIL_URL,
    DETAIL_V3_TABLE,
    ODDS_1X2_ITEM,
    ODDS_1X2_LABEL,
    ODDS_LABEL,
    ROUND_SPAN,
    ROUND_SPANS,
    ROW_ODDS_CELLS,
    SCHEDULE_ROWS,
    STANDING_BOX_LABEL,
    STANDING_ROUND_ITEM,
    STANDING_ROWS,
)

DEFAULT_TIMEOUT = 20

# JS click bypasses "element not interactable" for off-screen / overlaid controls.
_CLICK_JS = "arguments[0].click();"


def get_driver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()

    agent = random.choice(AGENTS)

    chrome_options.add_argument(f"--user-agent={agent}")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1600,6000")
    chrome_options.add_argument("log-level=3")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)

    return driver


def find_element_by_css(
    driver: webdriver.Chrome, selector: str, many: bool = False
) -> WebElement | list[WebElement] | None:
    if many:
        return driver.find_elements(By.CSS_SELECTOR, selector)

    return driver.find_element(By.CSS_SELECTOR, selector)


def wait_for_schedule_rows(driver: webdriver.Chrome, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Wait until the schedule rows and the round nav bar are present in the DOM."""
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, SCHEDULE_ROWS))
    )
    WebDriverWait(driver, timeout).until(
        lambda d: len(d.find_elements(By.CSS_SELECTOR, ROUND_SPANS)) > 0
    )


def get_detail_page(
    driver: webdriver.Chrome, match_id: str, timeout: int = DEFAULT_TIMEOUT
) -> None:
    """Load a match detail page and wait for its H2H widgets and odds table.

    The v1/v2/v3 tables lazy-load, so we scroll the page to trigger them and wait
    on the odds table plus the home-recent rows as the readiness signal.
    """
    driver.get(DETAIL_URL.format(match_id=match_id))
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, DETAIL_V3_TABLE))
    )
    _scroll_page(driver)
    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, DETAIL_ODDS_TABLE_CANDIDATES))
    )
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(
            lambda d: len(d.find_elements(By.CSS_SELECTOR, DETAIL_HOME_RECENT_ROWS)) > 0
        )
    time.sleep(0.5)


def _scroll_page(driver: webdriver.Chrome, steps: int = 12) -> None:
    js = f"window.scrollBy(0, document.body.scrollHeight/{steps});"
    for _ in range(steps):
        driver.execute_script(js)  # type: ignore[no-untyped-call]
        time.sleep(0.3)
    time.sleep(1.0)


def wait_for_odds(driver: webdriver.Chrome, timeout: int = 10) -> None:
    """Wait until the current round's odds cells have rendered.

    Clicking a round (especially the first one after switching the odds type)
    swaps the schedule rows before the odds cells are populated; reading
    `page_source` too early yields blank odds. We wait until at least one row has
    a numeric first odds cell, which is when the whole column has rendered.
    Falls back after the timeout so a genuinely odds-less round can't hang.
    """

    def some_row_has_odds(d: webdriver.Chrome) -> bool:
        for row in d.find_elements(By.CSS_SELECTOR, SCHEDULE_ROWS):
            cells = row.find_elements(By.CSS_SELECTOR, ROW_ODDS_CELLS)
            if cells and _is_number(cells[0].text):
                return True
        return False

    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(some_row_has_odds)
    time.sleep(0.3)


def switch_odds_to_1x2(driver: webdriver.Chrome, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Switch the schedule odds column to 1X2 (home / draw / away).

    The choice persists across round clicks, so this only needs calling once per
    page load. Returns quietly if the odds selector isn't present.
    """
    items = driver.find_elements(By.CSS_SELECTOR, ODDS_1X2_ITEM)
    if not items:
        return
    driver.execute_script(_CLICK_JS, items[0])  # type: ignore[no-untyped-call]
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(lambda d: _odds_label(d) == ODDS_1X2_LABEL)
    time.sleep(0.3)


def click_round(
    driver: webdriver.Chrome, round_number: int, timeout: int = DEFAULT_TIMEOUT
) -> None:
    """Click a round button and wait until its schedule list has re-rendered.

    Clicking a round marks its span with the 'on' class and swaps the schedule
    rows; we wait on both to be sure the new round's rows are in place.
    """
    selector = ROUND_SPAN.format(round=round_number)
    span = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )

    prev_first_id = _first_row_match_id(driver)
    driver.execute_script(_CLICK_JS, span)  # type: ignore[no-untyped-call]

    WebDriverWait(driver, timeout).until(
        lambda d: "on" in (d.find_element(By.CSS_SELECTOR, selector).get_attribute("class") or "")
    )
    # Wait for the row list to actually swap (unless the round was already active).
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(
            lambda d: _first_row_match_id(d) != prev_first_id or _first_row_match_id(d) is None
        )
    wait_for_schedule_rows(driver, timeout)
    time.sleep(0.4)  # small settle for trailing DOM updates


def sync_standings_to_round(
    driver: webdriver.Chrome, round_number: int, timeout: int = DEFAULT_TIMEOUT
) -> None:
    """Select the standings dropdown entry for `round_number` and wait for it to apply.

    Returns quietly if the standings section or the round entry is unavailable.
    """
    items = driver.find_elements(By.CSS_SELECTOR, STANDING_ROUND_ITEM.format(round=round_number))
    if not items:
        return

    driver.execute_script(_CLICK_JS, items[0])  # type: ignore[no-untyped-call]
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: _standing_label(d) == f"Round {round_number}"
        )
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, STANDING_ROWS))
        )
    except TimeoutException:
        pass
    time.sleep(0.3)


def _first_row_match_id(driver: webdriver.Chrome) -> str | None:
    rows = driver.find_elements(By.CSS_SELECTOR, SCHEDULE_ROWS)
    return rows[0].get_attribute("matchid") if rows else None


def _standing_label(driver: webdriver.Chrome) -> str:
    elements = driver.find_elements(By.CSS_SELECTOR, STANDING_BOX_LABEL)
    return elements[0].text.strip() if elements else ""


def _odds_label(driver: webdriver.Chrome) -> str:
    elements = driver.find_elements(By.CSS_SELECTOR, ODDS_LABEL)
    return elements[0].text.strip() if elements else ""


def _is_number(text: str) -> bool:
    try:
        float(text.strip())
        return True
    except ValueError:
        return False
