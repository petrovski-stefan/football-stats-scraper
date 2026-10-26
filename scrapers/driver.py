"""The browser: starting Chrome, opening pages under the robots.txt guard, and the waits and
clicks that put the league page, the detail page and the live page on screen.

Every page load goes through `open_page`; the DOM selectors come from `scrapers/constants.py`.
"""

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

# Waits and pauses, in seconds. They came with the early scraper (the page-load limit with the
# first commit, 2025-08-31, the rest on 2026-07-26); no measurement of them is on record.
DEFAULT_TIMEOUT = 20
PAGE_LOAD_TIMEOUT = 60
# How long `wait_for_odds` waits for a round's odds before it returns False.
ODDS_TIMEOUT = 10
# After a wait succeeds, for DOM updates that land just after it.
SETTLE_PAUSE = 0.3
# After a stage or round click, once the new rows are in place.
CLICK_SETTLE_PAUSE = 0.4
# After the detail page's widgets have shown.
DETAIL_SETTLE_PAUSE = 0.5
# The detail page's tables load as the page scrolls: this many steps, a pause after each, and a
# longer pause at the end.
SCROLL_STEPS = 12
SCROLL_STEP_PAUSE = 0.3
SCROLL_END_PAUSE = 1.0

# The headless browser's window, width by height in pixels.
WINDOW_SIZE = "1600,6000"

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
    """A headless Chrome with one desktop-Chrome user agent for its whole life."""

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument(f"--user-agent={_USER_AGENTS.random}")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument(f"--window-size={WINDOW_SIZE}")
    chrome_options.add_argument("log-level=3")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)

    return driver


def robots_refusal(url: str) -> str | None:
    """Why `ROBOTS_DISALLOW` refuses `url`: its host has no recorded rules, or a rule of that
    host disallows its path. None when the URL is allowed."""

    parts = urlparse(url)
    rules = ROBOTS_DISALLOW.get(parts.netloc)
    if rules is None:
        return f"no robots.txt rules recorded for {parts.netloc!r}"

    blocked = next((rule for rule in rules if parts.path.startswith(rule)), None)
    if blocked is not None:
        return f"robots.txt disallows {blocked!r} on {parts.netloc}"

    return None


def open_page(driver: webdriver.Chrome, url: str) -> None:
    """Navigate to `url`: the only place the scrapers call `driver.get`.

    Raises ValueError, before any request, for a host or path `ROBOTS_DISALLOW` refuses, and
    after it when a redirect lands on one (the rules and their reasons: `scrapers/CLAUDE.md`).
    """

    refusal = robots_refusal(url)
    if refusal is not None:
        raise ValueError(f"Refusing {url}: {refusal}")

    driver.get(url)
    landed = driver.current_url

    refusal = robots_refusal(landed)
    if refusal is not None:
        raise ValueError(f"Refusing {url}: it redirected to {landed}, and {refusal}")


def wait_for_schedule_rows(driver: webdriver.Chrome, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Wait until the schedule rows and the round nav bar are present in the DOM."""

    WebDriverWait(driver, timeout).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, SCHEDULE_ROWS))
    )
    WebDriverWait(driver, timeout).until(
        lambda browser: len(browser.find_elements(By.CSS_SELECTOR, ROUND_SPANS)) > 0
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

    # The rows are only a readiness signal: a home team without recent matches never shows
    # any, and its page is still parsed.
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(
            lambda browser: len(browser.find_elements(By.CSS_SELECTOR, DETAIL_HOME_RECENT_ROWS)) > 0
        )
    time.sleep(DETAIL_SETTLE_PAUSE)


def get_live_page(driver: webdriver.Chrome, match_id: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Load a match's live page and wait until its event list shows, or the timeout passes."""

    open_page(driver, LIVE_URL.format(match_id=match_id))

    # JavaScript renders the events well after the document is ready, so the wait is on a
    # minute cell: about 3.4 s a page, against 4.5 s with a blind sleep. A goalless, event-free
    # match times out with nothing rendered; `qa/goals.py` tells that apart from a failed load
    # by reconciling against the stored score.
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(_shows_a_minute)


def _scroll_page(driver: webdriver.Chrome) -> None:
    """Scroll down the page in `SCROLL_STEPS` jumps, so that its lazy widgets load."""

    scroll_script = f"window.scrollBy(0, document.body.scrollHeight/{SCROLL_STEPS});"
    for _ in range(SCROLL_STEPS):
        driver.execute_script(scroll_script)  # type: ignore[no-untyped-call]
        time.sleep(SCROLL_STEP_PAUSE)

    time.sleep(SCROLL_END_PAUSE)


def wait_for_odds(driver: webdriver.Chrome, timeout: int = ODDS_TIMEOUT) -> bool:
    """Wait until a row shows a numeric first odds cell; return whether one did in time.

    A clicked round swaps its rows before their odds fill in. False means no odds yet: the
    round may have none or still be loading, which look the same here, so the caller decides.
    """

    def some_row_has_odds(browser: webdriver.Chrome) -> bool:
        """Whether any schedule row's first odds cell holds a number."""

        for row in browser.find_elements(By.CSS_SELECTOR, SCHEDULE_ROWS):
            cells = row.find_elements(By.CSS_SELECTOR, ROW_ODDS_CELLS)
            if cells and _is_number(cells[0].text):
                return True

        return False

    try:
        WebDriverWait(driver, timeout).until(some_row_has_odds)
    except TimeoutException:
        return False

    time.sleep(SETTLE_PAUSE)

    return True


def switch_odds_type(driver: webdriver.Chrome, kind: str, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Switch the schedule odds column to "1x2", "ah" or "ou" (the page opens on AH).

    The choice holds across round clicks. False, with no error, when the type is absent or the
    header never shows its label: a league without that market gets empty columns.
    """

    dom_type, label = ODDS_TYPES[kind]
    if _odds_label(driver) == label:
        return True

    type_items = driver.find_elements(By.CSS_SELECTOR, ODDS_TYPE_ITEM.format(kind=dom_type))
    if not type_items:
        return False

    before = _first_row_odds(driver)
    driver.execute_script(_CLICK_JS, type_items[0])  # type: ignore[no-untyped-call]
    switched = True
    try:
        WebDriverWait(driver, timeout).until(lambda browser: _odds_label(browser) == label)
    except TimeoutException:
        switched = False

    # The header relabels before the column repaints, so the label alone is not a
    # readiness signal: reading here can still return the previous type's numbers.
    # Wait for the cells themselves to change. The middle cell is a draw price under
    # 1X2 and a line under AH/OU, so consecutive types never share it in practice.
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(
            lambda browser: _first_row_odds(browser) not in (before, [])
        )
    time.sleep(SETTLE_PAUSE)

    return switched


def click_stage(driver: webdriver.Chrome, stage_id: str, timeout: int = DEFAULT_TIMEOUT) -> None:
    """Show one stage tab's schedule and wait until its rows replace the previous stage's.

    The click loads the stage's current round. The stage already on screen is not clicked:
    nothing would change, so the row-swap wait would sit out its whole timeout.
    """

    _click_schedule_tab(driver, STAGE_SPAN.format(stage=stage_id), STAGE_ACTIVE_CLASS, timeout)


def sync_standings_to_stage(
    driver: webdriver.Chrome, stage_id: str, timeout: int = DEFAULT_TIMEOUT
) -> bool:
    """Point the standings table at `stage_id`'s sub-table; return whether it shows it.

    The sub-table picker ignores the stage tabs (`scrapers/CLAUDE.md` §2), so on False the
    table on screen is another stage's and the caller must not read it.
    """

    if _standing_sub(driver) == stage_id:
        return True

    return _select_standings(
        driver,
        (By.CSS_SELECTOR, SUB_STANDING_ITEM.format(stage=stage_id)),
        lambda browser: _standing_sub(browser) == stage_id,
        timeout,
    )


def click_round(
    driver: webdriver.Chrome,
    round_number: int,
    stage_id: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> None:
    """Click a round button and wait until its schedule list has re-rendered.

    `stage_id` scopes the button to its stage tab, None on a page without tabs: a multi-stage
    page holds every stage's round buttons, so "round 3" alone matches the first stage's.
    """

    if stage_id is None:
        selector = ROUND_SPAN.format(round=round_number)
    else:
        selector = STAGE_ROUND_SPAN.format(stage=stage_id, round=round_number)

    _click_schedule_tab(driver, selector, ROUND_ACTIVE_CLASS, timeout)


def show_total_standings(driver: webdriver.Chrome, timeout: int = DEFAULT_TIMEOUT) -> bool:
    """Show the standings' `Total` view and return whether it is on screen.

    `Total` is the table now, so the final table of a finished season. A page opens on it and
    picking a sub-table resets to it, so this is usually only a check.
    """

    if _standing_label(driver) == STANDING_TOTAL_LABEL:
        return True

    return _select_standings(
        driver,
        (By.XPATH, STANDING_TOTAL_ITEM),
        lambda browser: _standing_label(browser) == STANDING_TOTAL_LABEL,
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

    first_id_before = _first_row_match_id(driver)
    driver.execute_script(_CLICK_JS, span)  # type: ignore[no-untyped-call]

    WebDriverWait(driver, timeout).until(
        lambda browser: _has_class(browser.find_element(By.CSS_SELECTOR, selector), active_class)
    )

    # Wait for the row list to actually swap.
    with contextlib.suppress(TimeoutException):
        WebDriverWait(driver, timeout).until(
            lambda browser: _rows_swapped(browser, first_id_before)
        )

    wait_for_schedule_rows(driver, timeout)
    time.sleep(CLICK_SETTLE_PAUSE)


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

    entries = driver.find_elements(*item)
    if not entries:
        return False

    driver.execute_script(_CLICK_JS, entries[0])  # type: ignore[no-untyped-call]
    is_applied = True
    try:
        WebDriverWait(driver, timeout).until(applied)
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, STANDING_ROWS))
        )
    except TimeoutException:
        is_applied = False

    time.sleep(SETTLE_PAUSE)

    return is_applied


def _first_row_odds(driver: webdriver.Chrome) -> list[str]:
    """The first schedule row's three odds cells, as text. Repaint detector."""

    rows = driver.find_elements(By.CSS_SELECTOR, SCHEDULE_ROWS)
    if not rows:
        return []

    return [c.text.strip() for c in rows[0].find_elements(By.CSS_SELECTOR, ROW_ODDS_CELLS)]


def _first_row_match_id(driver: webdriver.Chrome) -> str | None:
    """The first schedule row's match id; None when no row is on screen."""

    rows = driver.find_elements(By.CSS_SELECTOR, SCHEDULE_ROWS)

    return rows[0].get_attribute("matchid") if rows else None


def _rows_swapped(driver: webdriver.Chrome, first_id_before: str | None) -> bool:
    """Whether the first schedule row is now another match than `first_id_before`, or no
    row is on screen."""

    first_id = _first_row_match_id(driver)

    return first_id != first_id_before or first_id is None


def _shows_a_minute(driver: webdriver.Chrome) -> bool:
    """Whether a minute cell of the live page's event list shows a match minute."""

    minute_cells = driver.find_elements(By.CSS_SELECTOR, LIVE_EVENT_MINUTE)

    return any(_MINUTE_RE.match(minute_cell.text.strip()) for minute_cell in minute_cells)


def _has_class(element: WebElement, name: str) -> bool:
    """Whether the element's `class` attribute lists `name`."""

    return name in (element.get_attribute("class") or "").split()


def _standing_sub(driver: webdriver.Chrome) -> str | None:
    """Stage id of the standings sub-table on screen; None on pages without stages."""

    boxes = driver.find_elements(By.CSS_SELECTOR, STANDING_BOX)

    return boxes[0].get_attribute("data-st-sub") if boxes else None


def _standing_label(driver: webdriver.Chrome) -> str:
    """The standings dropdown's label, such as "Total"; "" when it is not on screen."""

    elements = driver.find_elements(By.CSS_SELECTOR, STANDING_BOX_LABEL)

    return elements[0].text.strip() if elements else ""


def _odds_label(driver: webdriver.Chrome) -> str:
    """The odds column's header label, such as "1X2"; "" when it is not on screen."""

    elements = driver.find_elements(By.CSS_SELECTOR, ODDS_LABEL)

    return elements[0].text.strip() if elements else ""


def _is_number(text: str) -> bool:
    """Whether the text reads as a number."""

    try:
        float(text.strip())
        return True
    except ValueError:
        return False
