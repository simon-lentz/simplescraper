from typing import List
from bs4 import BeautifulSoup
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as EC

from scraper.config.logging import StructuredLogger
from scraper.config.validator import TargetConfig


class ExtractionManager:
    def __init__(self, logger: StructuredLogger):
        self.logger = logger

    def execute(self, driver: WebDriver, target: TargetConfig) -> List[str]:
        extracted_data = []
        extractions = target.extractions
        if extractions:
            for extraction in extractions:
                data = self._do_extraction(driver, **extraction.model_dump())
                extracted_data.append(data)
        else:
            self.logger.info(f"No extractions specified for '{target.name}'")
        return extracted_data

    def _do_extraction(self, driver: WebDriver, type: str, selector: str) -> str:
        match type:
            case "table":
                return self._extract_table(driver, selector)

    def _extract_table(self, driver: WebDriver, locator: str) -> str:
        try:
            element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, locator))
            )
            table_html = element.get_attribute('outerHTML')
            soup = BeautifulSoup(table_html, 'html.parser')
            return str(soup)
        except Exception as e:
            self.logger.error(f"Failed to extract table from '{locator}': {e}", exc_info=True)  # noqa:E501
            return ""
