from typing import List
from pydantic import BaseModel

from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController


class Interaction(BaseModel):
    type: str
    selector: str


class InteractionManager:
    def __init__(self, logger: StructuredLogger, controller: WebController):
        self.logger = logger
        self.controller = controller

    def start(self, name: str, url: str, startup: List[Interaction]):
        pass

    def execute(self, name: str, url: str, interactions: List[Interaction]):
        pass
