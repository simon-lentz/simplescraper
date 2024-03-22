from typing import List
from selenium.webdriver.remote.webdriver import WebDriver

from scraper.config.validator import Extraction
from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController

from .helper import get_element, get_elements, parse_element


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
                if extraction.output_file:
                    extraction_results[str(extraction.output_file)] = {
                        "data": data,
                        "output_type": extraction.output_type
                    }
            except Exception as e:
                self.logger.error(f"Failed to extract '{extraction.type}' for '{name}': {e}", exc_info=True)  # noqa:E501
        return extraction_results

    def _perform_extraction(self, driver: WebDriver, extraction: Extraction) -> List:
        try:
            match extraction.type:
                case "element":
                    if extraction.unique:
                        element = get_element(driver, extraction.locator, extraction.locator_type, extraction.unique)  # noqa:E501
                        return [parse_element(element, exclude_tags=extraction.exclude_tags)]  # noqa:E501
                    else:
                        elements = get_elements(driver, extraction.locator, extraction.locator_type)  # noqa:E501
                        return [parse_element(element, exclude_tags=extraction.exclude_tags) for element in elements]  # noqa:E501
                case "source":
                    return [str(driver.page_source)]
                case _:
                    self.logger.warning(f"Undefined extraction '{extraction.type}'")
            return []
        except Exception as e:
            self.logger.error(f"Failed to perform extraction on '{extraction.type}': {e}", exc_info=True)  # noqa:E501
            return []
