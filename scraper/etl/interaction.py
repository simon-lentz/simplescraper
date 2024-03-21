from typing import List

from scraper.config.validator import Interaction
from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController


class InteractionManager:
    def __init__(self, logger: StructuredLogger, controller: WebController):
        self.logger = logger
        self.controller = controller

    def start(self, name: str, url: str, startup: List[Interaction]):
        pass

    def execute(self, name: str, url: str, interactions: List[Interaction]):
        pass
