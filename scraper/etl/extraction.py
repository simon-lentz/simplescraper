from typing import List

from scraper.config.validator import Extraction
from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController


class ExtractionManager:
    def __init__(self, logger: StructuredLogger, controller: WebController):
        self.logger = logger
        self.controller = controller

    def execute(self, name: str, url: str, extractions: List[Extraction]):
        connection = self.controller.get_connection(name)
        driver = connection.driver
        self.controller.make_request(name, url)
        source = driver.page_source
        self.logger.info(f"Retrieved page source for target '{name}': '{str(source)}'")
