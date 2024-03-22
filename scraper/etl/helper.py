from typing import List, Optional
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By


def get_element(driver: WebDriver, locator: str, locator_type: str) -> WebElement:  # noqa:E501
    by_type = parse_locator(locator_type)
    element = driver.find_element(by_type, locator)
    return element


def get_elements(driver: WebDriver, locator: str, locator_type: str) -> List[WebElement]:  # noqa:E501
    by_type = parse_locator(locator_type)
    elements = driver.find_elements(by_type, locator)
    return elements


def parse_element(element: WebElement, exclude_tags: Optional[List[str]] = None) -> List[str]:  # noqa:E501
    html = element.get_attribute('innerHTML')
    soup = BeautifulSoup(html, 'html.parser')
    if exclude_tags:
        for tag in exclude_tags:
            for match in soup.find_all(tag):
                match.decompose()  # Remove the matched tags and their content
    text = soup.get_text(separator="&&&", strip=True)
    return [entry.strip() for entry in text.split("&&&") if entry.strip()]


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
            raise ValueError(f"Unsupported Selenium By-type '{formatted_strategy}'")  # noqa:E501
