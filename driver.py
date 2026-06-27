import random

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from constants import AGENTS


def get_driver() -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()

    agent = AGENTS[random.randint(0, len(AGENTS) - 1)]  # TODO: use agent lib

    chrome_options.add_argument(f"--user-agent={agent}")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])
    chrome_options.add_argument("--headless")
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
