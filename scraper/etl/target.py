from typing import List

from scraper.config.logging import StructuredLogger
from scraper.config.validator import TargetConfig
from scraper.web.controller import WebController


from .extraction import ExtractionManager
from .interaction import InteractionManager


class TargetManager:
    def __init__(self, logger: StructuredLogger, controller: WebController):
        self.logger = logger
        self.interact = InteractionManager(logger, controller)
        self.extract = ExtractionManager(logger, controller)

    def scrape_target(self, target: TargetConfig):
        # perform startup actions with target domain
        self.interact.start(target.name, target.domain, target.startup)
        # retrieve links, perform interactions
        for link in self._get_target_links(target):
            self.interact.execute(target.name, link, target.interactions)
            self.extract.execute(target.name, link, target.extractions)

    def _get_target_links(self, target: TargetConfig) -> List[str]:  # noqa:501
        input_file = target.input_file
        if input_file.exists():
            try:
                with open(input_file, "r") as file:
                    return [line.strip() for line in file if line.strip()]
            except Exception as e:
                self.logger.error(f"Failed to read links from input file '{input_file}' for '{target.name}': {e}")  # noqa:E501
