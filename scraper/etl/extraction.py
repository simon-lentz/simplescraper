from typing import List
from pydantic import BaseModel

from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController


class Extraction(BaseModel):
    type: str
    selector: str


class ExtractionManager:
    def __init__(self, logger: StructuredLogger, controller: WebController):
        self.logger = logger
        self.controller = controller

    def execute(self, name: str, url: str, extractions: List[Extraction]):
        pass
