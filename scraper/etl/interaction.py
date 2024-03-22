from typing import List

from scraper.config.validator import Interaction
from scraper.config.logging import StructuredLogger
from scraper.web.controller import WebController

from .helper import get_element


class InteractionManager:
    def __init__(self, logger: StructuredLogger, controller: WebController):
        self.logger = logger
        self.controller = controller

    def execute(self, name: str, url: str, interactions: List[Interaction]):
        connection = self.controller.get_connection(name)
        driver = connection.driver
        self.controller.make_request(name, url)
        for interaction in interactions:
            try:
                self._perform_interaction(driver, interaction)
            except Exception as e:
                self.logger.error(f"Failed to perform interaction '{interaction.type}' for '{name}': {e}", exc_info=True)  # noqa:E501
        pass

    def _perform_interaction(self, driver, interaction: Interaction) -> None:
        try:
            match interaction.type:
                case "click":
                    _ = get_element(driver, interaction.locator, interaction.locator_type)  # noqa:E501
                    # click element function
                case _:
                    self.logger.warning(f"Undefined interaction '{interaction.type}'")
        except Exception as e:
            self.logger.error(f"Failed to perform interaction '{interaction.type}': {e}")  # noqa:E501
