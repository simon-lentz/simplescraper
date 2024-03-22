from selenium.webdriver.remote.webdriver import WebDriver

from scraper.config.validator import Startup, Interaction
from scraper.config.logging import StructuredLogger


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
        self.logger.info(f"Performing '{action_type}' startup action with: '{interaction}'")  # noqa:E501
