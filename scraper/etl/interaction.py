from typing import List
from selenium.webdriver.remote.webdriver import WebDriver

from scraper.config.validator import Interaction
from scraper.config.logging import StructuredLogger

from .helper import click, dropdown
from .exceptions import (
    ElementNotFoundException,
    ClickException,
    DropdownSelectionException,
)


class InteractionManager:
    def __init__(self, logger: StructuredLogger, driver: WebDriver):
        self.logger = logger
        self.driver = driver

    def execute(self, name: str, interactions: List[Interaction]):
        for interaction in interactions:
            try:
                self._perform_interaction(interaction)
            except Exception as e:
                self.logger.error(f"Failed to perform interaction '{interaction.type}' for '{name}': {e}", exc_info=True)  # noqa:E501

    def _perform_interaction(self, interaction: Interaction) -> None:
        try:
            match interaction.type:
                case "click":
                    click(self.driver, interaction.locator, interaction.locator_type, interaction.wait_interval)  # noqa:E501
                    self.logger.info(f"Clicked on element: {interaction.locator}")
                case "dropdown":
                    if interaction.option_text is None:
                        raise ValueError("option_text is required for dropdown interactions")  # noqa:E501
                    dropdown(self.driver, interaction.locator, interaction.locator_type, interaction.wait_interval, interaction.option_text)  # noqa:E501
                    self.logger.info(f"Selected '{interaction.option_text}' from dropdown: {interaction.locator}")  # noqa:E501
                case _:
                    self.logger.error(f"Undefined interaction '{interaction.type}'")
        except ElementNotFoundException as e:
            self.logger.error(f"Element not found during interaction '{interaction.type}': {e}", exc_info=True)  # noqa:E501
        except ClickException as e:
            self.logger.error(f"Click failed during interaction '{interaction.type}': {e}", exc_info=True)  # noqa:E501
        except DropdownSelectionException as e:
            self.logger.error(f"Dropdown selection failed during interaction '{interaction.type}': {e}", exc_info=True)  # noqa:E501
        except Exception as e:
            self.logger.error(f"Unexpected error during interaction '{interaction.type}': {e}", exc_info=True)  # noqa:E501
