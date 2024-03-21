from typing import List, Optional
from pathlib import Path
from pydantic import ConfigDict, BaseModel

from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController

from .extraction import ExtractionManager, Extraction
from .interaction import InteractionManager, Interaction

# allow empty string for TargetConfig
target_opts = ConfigDict(
    extra="forbid",
    validate_assignment=True,
)


class TargetConfig(BaseModel):
    model_config = target_opts

    name: str
    domain: str
    input_file: Optional[Path] = None
    startup: Optional[List[Interaction]] = None
    interactions: Optional[List[Interaction]] = None
    extractions: Optional[List[Extraction]] = None


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
