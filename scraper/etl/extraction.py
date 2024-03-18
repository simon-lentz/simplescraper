#  from typing import Optional
#  from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver


def source(driver: WebDriver) -> str:
    """
    Retrieves the page source of the current web page.

    Args:
        driver: The WebDriver instance.

    Returns:
        The page source as a string.
    """
    return driver.page_source
