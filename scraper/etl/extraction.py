from typing import List, Optional
from bs4 import BeautifulSoup
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By

from scraper.config.validator import Extraction
from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController


class ExtractionManager:
    def __init__(self, logger: StructuredLogger, controller: WebController):
        self.logger = logger
        self.controller = controller

    def execute(self, name: str, url: str, extractions: List[Extraction]) -> dict:
        connection = self.controller.get_connection(name)
        driver = connection.driver
        self.controller.make_request(name, url)
        extraction_results = {}
        for extraction in extractions:
            try:
                data = self._perform_extraction(driver, extraction)
                self.logger.info(f"Extracted {data}")
                if extraction.output_file:
                    extraction_results[str(extraction.output_file)] = {
                        "data": data,
                        "output_type": extraction.output_type
                    }
            except Exception as e:
                self.logger.error(
                    f"Failed to extract '{extraction.type}' for '{name}': {e}",
                    exc_info=True
                )
        self.logger.info(f"Extraction Results: {extraction_results}")
        return extraction_results

    def element(self, driver: WebDriver, selector: str, selector_strategy: str, unique: bool, exclude_tags: Optional[List[str]] = None) -> List[List[str]]:  # noqa:E501
        by_type = self._parse_selector(selector_strategy)
        if unique:
            element = driver.find_element(by_type, selector)
            return [self.parse_html_element(element, exclude_tags)]
        else:
            elements = driver.find_elements(by_type, selector)
            return [self.parse_html_element(element, exclude_tags) for element in elements]  # noqa:E501

    def parse_html_element(self, element: WebElement, exclude_tags: Optional[List[str]] = None) -> List[str]:  # noqa:E501
        html = element.get_attribute('innerHTML')
        soup = BeautifulSoup(html, 'html.parser')
        if exclude_tags:
            for tag in exclude_tags:
                for match in soup.find_all(tag):
                    match.decompose()  # Remove the matched tags and their content
        text = soup.get_text(separator="&&&", strip=True)
        return [entry.strip() for entry in text.split("&&&") if entry.strip()]

    def _parse_selector(self, selector_strategy: str) -> By:
        formatted_strategy = selector_strategy.strip().replace(" ", "_").upper()
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
                self.logger.error(f"Unsupported Selenium By-type '{formatted_strategy}'")  # noqa:E501

    def _perform_extraction(self, driver: WebDriver, extraction: Extraction) -> List:
        try:
            match extraction.type:
                case "element":
                    return self.element(
                        driver,
                        extraction.selector,
                        extraction.selector_strategy,
                        extraction.unique,
                        exclude_tags=extraction.exclude_tags
                    )
                case "source":
                    return [str(driver.page_source)]
                case _:
                    self.logger.warning(f"Undefined extraction '{extraction.type}'")
            return []  # Return an empty list if the extraction type is not defined
        except Exception as e:
            self.logger.error(f"Failed to perform extraction on '{extraction.type}': {e}", exc_info=True)  # noqa:E501
            return []  # Return an empty list in case of an error
