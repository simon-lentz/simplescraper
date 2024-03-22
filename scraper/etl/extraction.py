import time
from typing import List
from selenium.webdriver.remote.webdriver import WebDriver

from scraper.config.validator import Extraction
from scraper.config.logging import StructuredLogger

from .helper import get_element, get_elements, parse_element, parse_table, paginate
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
                if not extraction.pagination_locator:
                    data = self._perform_extraction(name, extraction)
                else:
                    data = self._perform_paginated_extraction(name, extraction)
                if extraction.output_file:
                    extraction_results[str(extraction.output_file)] = {
                        "data": data,
                        "output_type": extraction.output_type
                    }
            except Exception as e:
                self.logger.error(f"Failed to extract '{extraction.type}' for '{name}': {e}", exc_info=True)  # noqa:E501
        return extraction_results

    def _perform_extraction(self, name: str, extraction: Extraction) -> List:
        try:
            match extraction.type:
                case "element":
                    if extraction.unique:
                        element = get_element(self.driver, extraction.locator, extraction.locator_type, extraction.wait_interval)  # noqa:E501
                        self.logger.info(f"Extraction for '{name}' complete")
                        return [parse_element(element, exclude_tags=extraction.exclude_tags)]  # noqa:E501
                    else:
                        elements = get_elements(self.driver, extraction.locator, extraction.locator_type, extraction.wait_interval)  # noqa:E501
                        self.logger.info(f"Extraction for '{name}' complete")
                        return [parse_element(element, exclude_tags=extraction.exclude_tags) for element in elements]  # noqa:E501
                case "table":
                    element = get_element(self.driver, extraction.locator, extraction.locator_type, extraction.wait_interval)  # noqa:E501
                    self.logger.info(f"Extraction for '{name}' complete")
                    return parse_table(element, exclude_tags=extraction.exclude_tags)
                case "source":
                    self.logger.info(f"Extraction for '{name}' complete")
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

    def _perform_paginated_extraction(self, name, extraction: Extraction) -> List:  # noqa:E501
        all_data = []
        page_count = 0
        locators = {
            "pagination": extraction.pagination_locator,
            "pagination_type": extraction.pagination_locator_type,
            "last_page": extraction.last_page_locator,
            "last_page_type": extraction.last_page_locator_type,
        }
        while True:
            try:
                match extraction.type:
                    case "element":
                        if extraction.unique:
                            element = get_element(self.driver, extraction.locator, extraction.locator_type, extraction.wait_interval)  # noqa:E501
                            page_data = [parse_element(element, exclude_tags=extraction.exclude_tags)]  # noqa:E501
                        else:
                            elements = get_elements(self.driver, extraction.locator, extraction.locator_type, extraction.wait_interval)  # noqa:E501
                            page_data = [parse_element(element, exclude_tags=extraction.exclude_tags) for element in elements]  # noqa:E501
                    case "table":
                        element = get_element(self.driver, extraction.locator, extraction.locator_type, extraction.wait_interval)  # noqa:E501
                        page_data = parse_table(element, exclude_tags=extraction.exclude_tags)  # noqa:E501
                    case "source":
                        page_data = [str(self.driver.page_source)]
                    case _:
                        self.logger.error(f"Undefined extraction '{extraction.type}'")
                        page_data = []
                all_data.extend(page_data)
                page_count += 1
                self.logger.info(f"Paginating for '{name}', current page: {page_count}")
                more_pages = paginate(self.driver, locators, extraction.wait_interval, page_count)  # noqa:E501
                if not more_pages:
                    break
            except ElementNotFoundException as e:
                self.logger.error(f"Element not found during extraction '{extraction.type}': {e}", exc_info=True)  # noqa:E501
                break
            except ParseElementException as e:
                self.logger.error(f"Failed to parse element during extraction '{extraction.type}': {e}", exc_info=True)  # noqa:E501
                break
            except ParseTableException as e:
                self.logger.error(f"Failed to parse table during extraction '{extraction.type}': {e}", exc_info=True)  # noqa:E501
                break
        self.logger.info(f"Extraction for '{name}' complete")
        return all_data
