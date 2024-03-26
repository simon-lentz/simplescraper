import time

from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException
)

from .exceptions import (
    ElementNotFoundException,
    ClickException,
    DropdownSelectionException,
    ParseElementException,
    ParseTableException,
    LocatorTypeException,
)


def get_element(driver: WebDriver, locator: str, locator_type: str, wait_interval: float) -> WebElement:  # noqa:E501
    by_type = parse_locator(locator_type)
    try:
        return driver.find_element(by_type, locator)
    except NoSuchElementException:
        return retry_get_element(driver, locator, locator_type, wait_interval)


def retry_get_element(driver: WebDriver, locator: str, locator_type: str, wait_interval: float) -> WebElement:  # noqa:E501
    by_type = parse_locator(locator_type)
    try:
        return WebDriverWait(driver, wait_interval).until(
            EC.presence_of_element_located((by_type, locator))
        )
    except TimeoutException as e:
        raise ElementNotFoundException(f"Element not found after retrying: {locator}") from e  # noqa:E501


def get_elements(driver: WebDriver, locator: str, locator_type: str, wait_interval: float) -> List[WebElement]:  # noqa:E501
    by_type = parse_locator(locator_type)
    try:
        _ = get_element(driver, locator, locator_type, wait_interval)
        elements = driver.find_elements(by_type, locator)
        return elements
    except Exception as e:
        raise ElementNotFoundException(f"Elements not found: {locator}") from e


def click(driver: WebDriver, locator: str, locator_type: str, wait_interval: float) -> None:  # noqa:E501
    try:
        element = get_element(driver, locator, locator_type, wait_interval)
        element.click()
    except Exception:
        # If the initial click fails, try again with explicit waits
        retry_click(driver, locator, locator_type, wait_interval)


def retry_click(driver: WebDriver, locator: str, locator_type: str, wait_interval: float) -> None:  # noqa:E501
    by_type = parse_locator(locator_type)
    try:
        # Wait for the element to be clickable
        element = WebDriverWait(driver, wait_interval).until(
            EC.element_to_be_clickable((by_type, locator))
        )
        element.click()
    except Exception as e:
        raise ClickException(f"Failed to click on element: {locator}") from e


def dropdown(driver: WebDriver, locator: str, locator_type: str, wait_interval: float, option_text: str) -> None:  # noqa:E501
    try:
        element = get_element(driver, locator, locator_type, wait_interval)
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


def parse_table(element: WebElement, exclude_tags: Optional[Dict[str, List[str]]] = None) -> List[List[str]]:  # noqa:E501
    try:
        rows_data = []
        html = element.get_attribute('outerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        if exclude_tags:
            for tag, attrs in exclude_tags.items():
                for match in soup.find_all(tag):
                    for attr in attrs:
                        if match.has_attr(attr):
                            match.decompose()
        rows = soup.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            row_data = []
            for cell in cells:
                cell_text = cell.get_text(strip=True)
                row_data.append(cell_text)
                a_tag = cell.find('a', href=True)
                if a_tag:
                    row_data.append(a_tag['href'])
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


def paginate(driver: WebDriver, locator: str, locator_type: str, wait_interval: float) -> bool:  # noqa:E501
    by_type = parse_locator(locator_type)
    try:
        next_button = WebDriverWait(driver, wait_interval, 0.05).until(
            EC.element_to_be_clickable((by_type, locator))
        )
        if "disabled" in next_button.get_attribute("class"):
            return False  # Next button is disabled, indicating the last page
        next_button.click()
        return True
    except Exception:
        return False
