from typing import Optional
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC


def source(driver: WebDriver) -> str:
    """Returns the page html as a string"""
    return driver.page_source


def parse_source(driver: WebDriver) -> BeautifulSoup:
    """
    Parses a stringified page HTML source and returns a BeautifulSoup object.
    """
    page_source = driver.page_source
    return BeautifulSoup(page_source, 'html.parser')


def parse_element(driver, locator) -> Optional[BeautifulSoup]:
    """
    Returns a parsed web element as soup
    """
    try:
        element = driver.find_element(By.XPATH, locator)
        element_html = element.get_attribute("outerHTML")
        return BeautifulSoup(element_html, "html.parser")
    except Exception:
        try:
            element = WebDriverWait(driver, 1, 0.05).until(
                EC.presence_of_element_located((By.XPATH, locator))
            )
            element_html = element.get_attribute("outerHTML")
            return BeautifulSoup(element_html, "html.parser")
        except Exception as e:
            raise Exception(
                f"Failed to parse element '{locator}': {e}"
            )


def table(driver, locator) -> Optional[str]:
    try:
        table = parse_element(driver, locator)
        return str(table)
    except Exception as e:
        raise e
