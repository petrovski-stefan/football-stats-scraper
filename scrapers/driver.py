import contextlib
import re
import time
from collections.abc import Callable
from urllib.parse import urlparse

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from scrapers.constants import (
    DETAIL_HOME_RECENT_ROWS,
    DETAIL_ODDS_TABLE_CANDIDATES,
    DETAIL_URL,
    DETAIL_V3_TABLE,
    LIVE_EVENT_MINUTE,
    LIVE_URL,
    ODDS_LABEL,
    ODDS_TYPE_ITEM,
    ODDS_TYPES,
    ROBOTS_DISALLOW,
    ROUND_ACTIVE_CLASS,
    ROUND_SPAN,
    ROUND_SPANS,
    ROW_ODDS_CELLS,
    SCHEDULE_ROWS,
    STAGE_ACTIVE_CLASS,
    STAGE_ROUND_SPAN,
    STAGE_SPAN,
    STANDING_BOX,
    STANDING_BOX_LABEL,
    STANDING_ROWS,
    STANDING_TOTAL_ITEM,
    STANDING_TOTAL_LABEL,
    SUB_STANDING_ITEM,
)

DEFAULT_TIMEOUT = 20

# JS click bypasses "element not interactable" for off-screen / overlaid controls.
_CLICK_JS = "arguments[0].click();"

# A rendered event minute: "33'", "45+3'", "90+8'". Used only as a readiness signal here;
# scrapers/goal_parsers.py owns the real parse.
_MINUTE_RE = re.compile(r"^\d{1,3}(?:\+\d{1,2})?'$")

# One fake-useragent string per driver, kept for every page that driver opens. Chrome desktop
# only: the real browser is Chrome, and a Safari, Firefox or mobile string can make the site
# serve a layout the parsers do not know. The library reads a data file bundled with it and
# makes no network calls.
_USER_AGENTS = UserAgent(browsers=["Chrome"], platforms=["desktop"])


def get_driver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"--user-agent={_USER_AGENTS.random}")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--window-size=1600,6000")
    chrome_options.add_argument("log-level=3")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(60)

    return driver


def open_page(driver: webdriver.Chrome, url: str) -> None:
    """Navigate to `url`. The only place the scrapers call `driver.get`.

    Refuses, before any request is made, a URL on a host with no recorded robots.txt rules and
    a path that host's robots.txt disallows (`ROBOTS_DISALLOW`). Resources the page loads by
    itself while rendering are not checked: the rule covers the pages the scraper chooses to
    open (decided 2026-10-02).
    """
    parts = urlparse(url)
    rules = ROBOTS_DISALLOW.get(parts.netloc)
    if rules is None:
        raise ValueError(f"Refusing {url}: no robots.txt rules recorded for {parts.netloc!r}")
    blocked = next((rule for rule in rules if parts.path.startswith(rule)), None)
    if blocked is not None:
        raise ValueError(f"Refusing {url}: robots.txt disallows {blocked!r} on {parts.netloc}")
    driver.get(url)


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
    open_page(driver, DETAIL_URL.format(match_id=match_id))
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


def get_live_page(driver: webdriver.Chrome, match_id: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Load a match's live page and wait for its event list to be injected.

    Events are rendered by JavaScript well after the document is ready, so the readiness
    signal is an actual minute cell, not the page load. Waiting on that instead of sleeping
    blindly takes the page from ~4.5s to ~3.4s.

    A goalless, event-free match simply times out with nothing rendered and the caller sees
    zero goals — the right answer for a 0-0. Telling "no events" apart from "failed to
    load" is done by reconciling against the stored score in `qa/goals.py`, not here.
    """
    open_page(driver, LIVE_URL.format(match_id=match_id))
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(
            lambda d: any(
                _MINUTE_RE.match(e.text.strip())
                for e in d.find_elements(By.CSS_SELECTOR, LIVE_EVENT_MINUTE)
            )
        )


def _scroll_page(driver: webdriver.Chrome, steps: int = 12) -> None:
    js = f"window.scrollBy(0, document.body.scrollHeight/{steps});"
    for _ in range(steps):
        driver.execute_script(js)  # type: ignore[no-untyped-call]
        time.sleep(0.3)
    time.sleep(1.0)


def wait_for_odds(driver: webdriver.Chrome, timeout: int = 10) -> bool:
    """Wait until the current round's odds cells have rendered; return whether they did.

    Clicking a round (especially the first one after switching the odds type)
    swaps the schedule rows before the odds cells are populated; reading
    `page_source` too early yields blank odds. We wait until at least one row has
    a numeric first odds cell, which is when the whole column has rendered.
    Gives up after the timeout so a genuinely odds-less round can't hang. False then
    means no odds yet: the round may have none, or they may still be loading, and the
    two look the same here, so the caller decides.
    """

    def some_row_has_odds(d: webdriver.Chrome) -> bool:
        for row in d.find_elements(By.CSS_SELECTOR, SCHEDULE_ROWS):
            cells = row.find_elements(By.CSS_SELECTOR, ROW_ODDS_CELLS)
            if cells and _is_number(cells[0].text):
                return True
        return False

    try:
        WebDriverWait(driver, timeout).until(some_row_has_odds)
    except TimeoutException:
        return False
    time.sleep(0.3)
    return True


def switch_odds_type(driver: webdriver.Chrome, kind: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Switch the schedule odds column to "1x2", "ah" or "ou".

    The page defaults to AH. The choice persists across round clicks, so switching once
    is enough for a whole pass; switching per round is also safe. Returns False (quietly)
    when the selector is absent or the header never adopts the new label, so a league
    that does not carry a given odds type degrades to empty columns rather than raising.
    """
    dom_type, label = ODDS_TYPES[kind]
    if _odds_label(driver) == label:
        return True
    items = driver.find_elements(By.CSS_SELECTOR, ODDS_TYPE_ITEM.format(kind=dom_type))
    if not items:
        return False

    before = _first_row_odds(driver)
    driver.execute_script(_CLICK_JS, items[0])  # type: ignore[no-untyped-call]
    switched = True
    try:
        WebDriverWait(driver, timeout).until(lambda d: _odds_label(d) == label)
    except TimeoutException:
        switched = False
    # The header relabels before the column repaints, so the label alone is not a
    # readiness signal: reading here can still return the previous type's numbers.
    # Wait for the cells themselves to change. The middle cell is a draw price under
    # 1X2 and a line under AH/OU, so consecutive types never share it in practice.
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(lambda d: _first_row_odds(d) not in (before, []))
    time.sleep(0.3)
    return switched


def click_stage(driver: webdriver.Chrome, stage_id: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Show one stage tab's schedule and wait until its rows replace the previous stage's.

    Clicking a tab marks it 'on', unhides that stage's round buttons and loads the
    stage's current round. The stage already on screen is left alone: re-clicking it
    changes nothing, so the row-swap wait would sit out its whole timeout.
    """
    _click_schedule_tab(driver, STAGE_SPAN.format(stage=stage_id), STAGE_ACTIVE_CLASS, timeout)


def sync_standings_to_stage(
    driver: webdriver.Chrome, stage_id: str, timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """Point the standings table at `stage_id`'s sub-table; return whether it shows it.

    The sub-table picker ignores the stage tabs and opens on the latest sub-table: a
    Liga MX page shows the Apertura schedule beside the Clausura table, a Scottish
    Premiership page the regular season beside the 6-team Championship Group. Ranks read
    without this sync belong to another table, so on False the caller must drop them.
    """
    if _standing_sub(driver) == stage_id:
        return True
    return _select_standings(
        driver,
        (By.CSS_SELECTOR, SUB_STANDING_ITEM.format(stage=stage_id)),
        lambda d: _standing_sub(d) == stage_id,
        timeout,
    )


def click_round(
    driver: webdriver.Chrome,
    round_number: int,
    stage_id: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> None:
    """Click a round button and wait until its schedule list has re-rendered.

    `stage_id` scopes the button to one stage tab: a multi-stage page holds every
    stage's round buttons at once, so "round 3" alone would match the first stage's.
    None on pages without stage tabs.
    """
    if stage_id is None:
        selector = ROUND_SPAN.format(round=round_number)
    else:
        selector = STAGE_ROUND_SPAN.format(stage=stage_id, round=round_number)
    _click_schedule_tab(driver, selector, ROUND_ACTIVE_CLASS, timeout)


def show_total_standings(driver: webdriver.Chrome, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Show the standings' `Total` view and return whether it is on screen.

    `Total` is the table as it stands now, so for a finished season the final table. The
    dropdown lists it beside one entry per finished round; a page opens on it, and picking
    a sub-table resets to it, so this is usually only a check.
    """
    if _standing_label(driver) == STANDING_TOTAL_LABEL:
        return True
    return _select_standings(
        driver,
        (By.XPATH, STANDING_TOTAL_ITEM),
        lambda d: _standing_label(d) == STANDING_TOTAL_LABEL,
        timeout,
    )


def _click_schedule_tab(
    driver: webdriver.Chrome, selector: str, active_class: str, timeout: int
) -> None:
    """Click a stage or round button and wait until the schedule rows have re-rendered.

    The click marks the button with `active_class` and swaps the schedule rows; we wait
    on both to be sure the new rows are in place. A button already active is not clicked.
    """
    span = WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
    )
    if _has_class(span, active_class):
        return

    prev_first_id = _first_row_match_id(driver)
    driver.execute_script(_CLICK_JS, span)  # type: ignore[no-untyped-call]

    WebDriverWait(driver, timeout).until(
        lambda d: _has_class(d.find_element(By.CSS_SELECTOR, selector), active_class)
    )
    # Wait for the row list to actually swap (unless the button was already active).
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(
            lambda d: _first_row_match_id(d) != prev_first_id or _first_row_match_id(d) is None
        )
    wait_for_schedule_rows(driver, timeout)
    time.sleep(0.4)  # small settle for trailing DOM updates


def _select_standings(
    driver: webdriver.Chrome,
    item: tuple[str, str],
    applied: Callable[[webdriver.Chrome], bool],
    timeout: int,
) -> bool:
    """Click a standings picker entry, found by `(By.<kind>, locator)`, and wait for the
    table to apply it.

    False when the entry is absent or the table never shows it applied.
    """
    items = driver.find_elements(*item)
    if not items:
        return False

    driver.execute_script(_CLICK_JS, items[0])  # type: ignore[no-untyped-call]
    ok = True
    try:
        WebDriverWait(driver, timeout).until(applied)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, STANDING_ROWS))
        )
    except TimeoutException:
        ok = False
    time.sleep(0.3)
    return ok


def _first_row_odds(driver: webdriver.Chrome) -> list[str]:
    """The first schedule row's three odds cells, as text. Repaint detector."""
    rows = driver.find_elements(By.CSS_SELECTOR, SCHEDULE_ROWS)
    if not rows:
        return []
    return [c.text.strip() for c in rows[0].find_elements(By.CSS_SELECTOR, ROW_ODDS_CELLS)]


def _first_row_match_id(driver: webdriver.Chrome) -> str | None:
    rows = driver.find_elements(By.CSS_SELECTOR, SCHEDULE_ROWS)
    return rows[0].get_attribute("matchid") if rows else None


def _has_class(element: WebElement, name: str) -> bool:
    return name in (element.get_attribute("class") or "").split()


def _standing_sub(driver: webdriver.Chrome) -> str | None:
    """Stage id of the standings sub-table on screen; None on pages without stages."""
    boxes = driver.find_elements(By.CSS_SELECTOR, STANDING_BOX)
    return boxes[0].get_attribute("data-st-sub") if boxes else None


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
