import time
from typing import List
from selenium.webdriver.remote.webdriver import WebDriver

from scraper.config.validator import Extraction
from scraper.config.logging import StructuredLogger

from .helper import get_element, get_elements, parse_element, parse_table
from .exceptions import (
    ElementNotFoundException,
    ParseElementException,
    ParseTableException,
)


class ExtractionManager:
    def __init__(self, logger: StructuredLogger, driver: WebDriver):
        self.logger = logger
        self.driver = driver

    def execute(self, name: str, extractions: List[Extraction]) -> dict:
        extraction_results = {}
        for extraction in extractions:
            try:
                if extraction.wait_interval > 0:
                    time.sleep(extraction.wait_interval)
                data = self._perform_extraction(extraction)
                if extraction.output_file:
                    extraction_results[str(extraction.output_file)] = {
                        "data": data,
                        "output_type": extraction.output_type
                    }
            except Exception as e:
                self.logger.error(f"Failed to extract '{extraction.type}' for '{name}': {e}", exc_info=True)  # noqa:E501
        return extraction_results

    def _perform_extraction(self, extraction: Extraction) -> List:
        try:
            match extraction.type:
                case "element":
                    if extraction.unique:
                        element = get_element(self.driver, extraction.locator, extraction.locator_type)  # noqa:E501
                        return [parse_element(element, exclude_tags=extraction.exclude_tags)]  # noqa:E501
                    else:
                        elements = get_elements(self.driver, extraction.locator, extraction.locator_type)  # noqa:E501
                        return [parse_element(element, exclude_tags=extraction.exclude_tags) for element in elements]  # noqa:E501
                case "table":
                    element = get_element(self.driver, extraction.locator, extraction.locator_type)  # noqa:E501
                    return parse_table(element, exclude_tags=extraction.exclude_tags)
                case "source":
                    return [str(self.driver.page_source)]
                case _:
                    self.logger.error(f"Undefined extraction '{extraction.type}'")
            return []
        except ElementNotFoundException as e:
            self.logger.error(f"Element not found during extraction '{extraction.type}': {e}", exc_info=True)  # noqa:E501
            return []
        except ParseElementException as e:
            self.logger.error(f"Failed to parse element during extraction '{extraction.type}': {e}", exc_info=True)  # noqa:E501
            return []
        except ParseTableException as e:
            self.logger.error(f"Failed to parse table during extraction '{extraction.type}': {e}", exc_info=True)  # noqa:E501
            return []
