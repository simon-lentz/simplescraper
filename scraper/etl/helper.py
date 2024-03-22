import time

from typing import List, Optional
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException
)

from .exceptions import (
    ElementNotFoundException,
    ClickException,
    DropdownSelectionException,
    ParseElementException,
    ParseTableException,
    LocatorTypeException,
)


def get_element(driver: WebDriver, locator: str, locator_type: str) -> WebElement:
    by_type = parse_locator(locator_type)
    try:
        element = driver.find_element(by_type, locator)
        return element
    except Exception as e:
        raise ElementNotFoundException(f"Element not found: {locator}") from e


def get_elements(driver: WebDriver, locator: str, locator_type: str) -> List[WebElement]:  # noqa:E501
    by_type = parse_locator(locator_type)
    try:
        elements = driver.find_elements(by_type, locator)
        return elements
    except Exception as e:
        raise ElementNotFoundException(f"Elements not found: {locator}") from e


def click(driver: WebDriver, locator: str, locator_type: str, wait_interval: float) -> None:  # noqa:E501
    try:
        element = get_element(driver, locator, locator_type)
        element.click()
        if wait_interval > 0:
            time.sleep(wait_interval)  # Wait for the specified interval
    except Exception as e:
        raise ClickException(f"Failed to click on element: {locator}") from e


def dropdown(driver: WebDriver, locator: str, locator_type: str, wait_interval: float, option_text: str) -> None:  # noqa:E501
    try:
        element = get_element(driver, locator, locator_type)
        select = Select(element)
        select.select_by_visible_text(option_text)
        if wait_interval > 0:
            time.sleep(wait_interval)  # Wait for the specified interval
    except Exception as e:
        raise DropdownSelectionException(f"Failed to select '{option_text}' from dropdown: {locator}") from e  # noqa:E501


def parse_element(element: WebElement, exclude_tags: Optional[List[str]] = None) -> List[str]:  # noqa:E501
    try:
        html = element.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        if exclude_tags:
            for tag in exclude_tags:
                for match in soup.find_all(tag):
                    match.decompose()
        text = soup.get_text(separator="&&&", strip=True)
        return [entry.strip() for entry in text.split("&&&") if entry.strip()]
    except Exception as e:
        raise ParseElementException("Failed to parse element") from e


def parse_table(element: WebElement, exclude_tags: Optional[List[str]] = None) -> List[List[str]]:  # noqa:E501
    try:
        rows_data = []
        html = element.get_attribute('outerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        if exclude_tags:
            for tag in exclude_tags:
                for match in soup.find_all(tag):
                    match.decompose()
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = [cell.get_text(strip=True) for cell in cells]
            rows_data.append(row_data)
        return rows_data
    except Exception as e:
        raise ParseTableException("Failed to parse table") from e


def parse_locator(locator_type: str) -> By:
    formatted_strategy = locator_type.strip().replace(" ", "_").upper()
    match formatted_strategy:
        case "CLASS_NAME":
            return By.CLASS_NAME
        case "CSS_SELECTOR":
            return By.CSS_SELECTOR
        case "ID":
            return By.ID
        case "NAME":
            return By.NAME
        case "LINK_TEXT":
            return By.LINK_TEXT
        case "PARTIAL_LINK_TEXT":
            return By.PARTIAL_LINK_TEXT
        case "TAG_NAME":
            return By.TAG_NAME
        case "XPATH":
            return By.XPATH
        case _:
            raise LocatorTypeException(f"Unsupported Selenium By-type '{formatted_strategy}'")  # noqa:E501


def paginate(driver: WebDriver, locator: str, locator_type: str, wait_interval: float, page_count: int = 0) -> bool:  # noqa:E501
    by_type = parse_locator(locator_type)
    try:
        pagination_element = driver.find_element(by_type, locator)
        pagination_items = pagination_element.find_elements(By.TAG_NAME, "li")
        next_button = pagination_items[-1].find_element(By.TAG_NAME, "a")
        # Assuming the second last item is the last page number
        last_page = pagination_items[-2].find_element(By.TAG_NAME, "a")
        last_page_num = int(last_page.text)
        if next_button.is_enabled() and next_button.is_displayed():
            next_button.click()
            if wait_interval > 0:
                time.sleep(wait_interval)
            if page_count >= last_page_num:
                return False
            return True
    except (NoSuchElementException, ElementNotInteractableException):
        return False  # "Next" button not found or not clickable, assuming last page
