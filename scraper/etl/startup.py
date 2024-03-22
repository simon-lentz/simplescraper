import time
from selenium.webdriver.remote.webdriver import WebDriver

from scraper.config.validator import Startup, Interaction
from scraper.config.logging import StructuredLogger

from .helper import click, dropdown


class StartupManager:
    def __init__(self, logger: StructuredLogger, driver: WebDriver):
        self.logger = logger
        self.driver = driver

    def execute(self, name: str, startup: Startup):
        for action_type, interaction in startup.actions.items():
            try:
                self._perform_startup_action(action_type, interaction)
            except Exception as e:
                self.logger.error(f"Failed to perform startup action '{action_type}' for '{name}': {e}", exc_info=True)  # noqa:E501

    def _perform_startup_action(self, action_type: str, interaction: Interaction) -> None:  # noqa:E501
        max_retries = 2
        for attempt in range(max_retries):
            try:
                match interaction.type:
                    case "click":
                        self._startup_click(action_type, interaction)
                    case "dropdown":
                        self._startup_dropdown(action_type, interaction)
                    case _:
                        self.logger.error(f"Startup action invoked unknown interaction: '{interaction.type}'")  # noqa:E501
                # If action succeeds, break out of the loop
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    self.logger.warning(f"Retrying startup action '{action_type}' (attempt {attempt + 2})")  # noqa:E501
                else:
                    self.logger.error(f"Startup action '{action_type}' failed after {max_retries} attempts")  # noqa:E501
                    raise e
            time.sleep(interaction.wait_interval)

    def _startup_click(self, action_type, interaction: Interaction) -> None:
        click(self.driver, interaction.locator, interaction.locator_type, interaction.wait_interval)  # noqa:E501
        self.logger.info(f"Performed '{action_type}' click")

    def _startup_dropdown(self, action_type, interaction: Interaction) -> None:
        if interaction.option_text is None:
            raise ValueError("option_text is required for dropdown interactions")  # noqa:E501
        dropdown(self.driver, interaction.locator, interaction.locator_type, interaction.wait_interval, interaction.option_text)  # noqa:E501
        self.logger.info(f"Performed '{action_type}' selection")
