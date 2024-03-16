from typing import Optional
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver


def page_source(driver: WebDriver) -> str:
    """
    Retrieves the page source of the current web page.

    Args:
        driver: The WebDriver instance.

    Returns:
        The page source as a string.
    """
    return driver.page_source


def parse_page_source(source: str) -> BeautifulSoup:
    """
    Parses the page source using BeautifulSoup.

    Args:
        page_source: The page source as a string.

    Returns:
        A BeautifulSoup object representing the parsed page source.
    """
    return BeautifulSoup(source, "html.parser")


def extract_table(soup: BeautifulSoup, table_selector: str) -> Optional[str]:
    """
    Extracts a table from the parsed page source.

    Args:
        soup: The BeautifulSoup object representing the parsed page source.
        table_selector: The CSS selector for the desired table.

    Returns:
        The extracted table as a string, or None if the table is not found.
    """
    table = soup.select_one(table_selector)
    if table:
        return str(table)
    return None


def extract_image_urls(soup: BeautifulSoup, image_selector: str) -> list[str]:
    """
    Extracts image URLs from the parsed page source.

    Args:
        soup: The BeautifulSoup object representing the parsed page source.
        image_selector: The CSS selector for the desired images.

    Returns:
        A list of image URLs.
    """
    image_tags = soup.select(image_selector)
    return [img["src"] for img in image_tags if img.get("src")]


def extract_data(driver: WebDriver, table_selector: str, image_selector: str) -> dict:
    """
    Extracts data from the web page using BeautifulSoup.

    Args:
        driver: The WebDriver instance.
        table_selector: The CSS selector for the desired table.
        image_selector: The CSS selector for the desired images.

    Returns:
        A dictionary containing the extracted data.
    """
    source = page_source(driver)
    soup = parse_page_source(source)

    extracted_data = {
        "table": extract_table(soup, table_selector),
        "image_urls": extract_image_urls(soup, image_selector),
    }

    return extracted_data
