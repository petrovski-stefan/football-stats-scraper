"""One Chrome per worker thread, shared by the per-match scrapers.

Extracted because `scrapers/detail.py` and `scrapers/goals.py` had grown byte-identical
copies of this: the thread-local handle, the registry of live drivers, the lock guarding
it, and the teardown. Two copies of browser lifecycle management is the dangerous kind of
duplication — a leak fixed in one and not the other strands Chrome processes that nothing
will ever close, and the symptom (a machine slowly filling with orphaned browsers) shows
up nowhere near the bug.

A Selenium session is not safe to share across threads, so each worker gets its own and
keeps it for every task it picks up. Starting a browser costs far more than loading a
page, so creating one per match would dominate the run.
"""

import threading

from selenium import webdriver

from scrapers.driver import get_driver


class BrowserPool:
    """Lazily creates one driver per thread and closes every one of them at the end."""

    def __init__(self) -> None:
        self._local = threading.local()
        self._drivers: list[webdriver.Chrome] = []
        self._lock = threading.Lock()

    def driver(self) -> webdriver.Chrome:
        """This thread's browser, started on first use."""

        driver = getattr(self._local, "driver", None)
        if driver is None:
            driver = get_driver()
            self._local.driver = driver
            with self._lock:
                self._drivers.append(driver)

        return driver

    def close_all(self) -> None:
        """Quit every driver this pool started.

        Must run even when the batch raised: a killed run leaves headless Chrome
        processes behind, and they are not obviously attributable to this program.
        """

        with self._lock:
            drivers, self._drivers = self._drivers, []

        for driver in drivers:
            driver.quit()

    def __enter__(self) -> "BrowserPool":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close_all()
